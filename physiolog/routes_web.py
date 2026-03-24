"""
routes_web.py

It defines the web routes for the PhySioLog Flask application.

Author: Jose Guzman, sjm.guzman<at>gmail.com
"""

from pathlib import Path
from urllib.parse import urlparse

import markdown2
from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func, or_

from .extensions import db
from .models import AdminClientAssignment, HealthEntry, User

web_bp = Blueprint("web", __name__)
DOCS_DIR = Path("docs").resolve()
MARKDOWN_EXTRAS = ["fenced-code-blocks", "tables", "break-on-newline"]
DOCS_PER_PAGE_OPTIONS = ["5", "10", "20", "all"]


def build_docs_tree() -> dict[str, list[dict[str, str]]]:
    tree: dict[str, list[dict[str, str]]] = {}
    if not DOCS_DIR.exists():
        return tree

    for file in sorted(DOCS_DIR.rglob("*.md")):
        rel = file.relative_to(DOCS_DIR)
        section = rel.parent.as_posix() if rel.parent.as_posix() != "." else "general"
        text = file.read_text(encoding="utf-8")
        h1_title = None
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                h1_title = stripped[2:].strip()
                break
        tree.setdefault(section, []).append(
            {
                "name": rel.stem.replace("_", " "),
                "title": h1_title or rel.stem.replace("_", " "),
                "doc_path": rel.with_suffix("").as_posix(),
            }
        )

    for pages in tree.values():
        pages.sort(key=lambda page: page["name"].lower())

    return dict(sorted(tree.items(), key=lambda item: item[0].lower()))


@web_bp.app_context_processor
def inject_docs_sections():
    tree = build_docs_tree()
    return {
        "docs_sections": list(tree.keys()),
        "selected_client": get_selected_client(),
    }


def get_selected_client():
    """Return the selected client for template rendering, if any."""
    if not current_user.is_authenticated or not current_user.is_admin:
        return None

    selected_user_id = session.get("selected_user_id")
    if selected_user_id is None:
        return None

    return (
        db.session.query(User)
        .join(
            AdminClientAssignment,
            AdminClientAssignment.client_user_id == User.id,
        )
        .filter(
            AdminClientAssignment.admin_user_id == current_user.id,
            User.id == selected_user_id,
        )
        .first()
    )


def _resolve_doc_file(doc_path: str) -> Path | None:
    candidate = (DOCS_DIR / f"{doc_path}.md").resolve()
    if DOCS_DIR not in candidate.parents:
        return None
    if not candidate.exists() or not candidate.is_file():
        return None
    return candidate


def _section_from_doc_path(doc_path: str) -> str:
    parent = Path(doc_path).parent.as_posix()
    return parent if parent != "." else "general"


def _normalize_markdown_whitespace(text: str) -> str:
    # Ensure lines containing only spaces/tabs are treated as blank separators.
    lines = ["" if not line.strip() else line.rstrip() for line in text.splitlines()]
    return "\n".join(lines)


def _render_docs_markdown_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current_lines: list[str] = []

    for line in text.splitlines():
        if line.strip() == "---":
            block = _normalize_markdown_whitespace("\n".join(current_lines)).strip()
            if block:
                blocks.append(markdown2.markdown(block, extras=MARKDOWN_EXTRAS))
            current_lines = []
            continue
        current_lines.append(line)

    block = _normalize_markdown_whitespace("\n".join(current_lines)).strip()
    if block:
        blocks.append(markdown2.markdown(block, extras=MARKDOWN_EXTRAS))

    return blocks


def _filter_section_pages(
    section_pages: list[dict[str, str]],
    docs_query: str,
) -> list[dict[str, str]]:
    query = docs_query.strip().lower()
    if not query:
        return section_pages
    return [
        page
        for page in section_pages
        if query in page["name"].lower() or query in page["title"].lower()
    ]


def _parse_docs_pagination_args() -> tuple[int, int | str]:
    per_page_raw = request.args.get("per_page", "10").strip().lower()
    if per_page_raw not in {"5", "10", "20", "all"}:
        per_page_raw = "10"
    per_page: int | str = per_page_raw if per_page_raw == "all" else int(per_page_raw)

    page_raw = request.args.get("page", "1").strip()
    try:
        page = int(page_raw)
    except ValueError:
        page = 1
    if page < 1:
        page = 1
    return page, per_page


def _paginate_docs(
    section_pages: list[dict[str, str]],
    page: int,
    per_page: int | str,
) -> tuple[list[dict[str, str]], int, int]:
    total_docs = len(section_pages)
    total_pages = (
        1 if per_page == "all" else max(1, (total_docs + per_page - 1) // per_page)
    )
    if page > total_pages:
        page = total_pages

    if per_page == "all":
        return section_pages, page, total_pages

    start = (page - 1) * per_page
    end = start + per_page
    return section_pages[start:end], page, total_pages


@web_bp.route("/")
def index():
    """Redirect to overview if logged in, otherwise to login page"""
    if current_user.is_authenticated:
        return redirect(url_for("web.metabolism"))
    return redirect(url_for("web.login"))


@web_bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for("web.metabolism"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            nxt = request.args.get("next")
            # prevent open redirect by only allowing relative local targets
            if nxt:
                parsed_url = urlparse(nxt)
                if parsed_url.scheme or parsed_url.netloc:
                    nxt = None
            return redirect(nxt or url_for("web.metabolism"))
        flash("Invalid email or password", "error")
    return render_template("login.html")


@web_bp.route("/register", methods=["GET", "POST"])
def register():
    """Register page"""
    if current_user.is_authenticated:
        return redirect(url_for("web.metabolism"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Name, email and password are required", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return render_template("register.html")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered", "error")
            return render_template("register.html")

        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Account created. You can now sign in.", "success")
        return redirect(url_for("web.login"))

    return render_template("register.html")


# =========================================================================
# Protected routes (require login)
# =========================================================================
@web_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """Logout goes to loging page"""
    logout_user()
    db.session.remove()
    return redirect(url_for("web.login"))


@web_bp.route("/metabolism")
@login_required
def metabolism():
    """Metabolism page with metabolism stats and input entry form"""
    return render_template("metabolism.html")


@web_bp.route("/overview")
@login_required
def overview():
    """Backward-compatible redirect from overview to metabolism."""
    return redirect(url_for("web.metabolism"))


@web_bp.route("/trends")
@login_required
def trends():
    """Visualizations page with trends charts"""
    return render_template("trends.html")


@web_bp.route("/entry")
@login_required
def entry():
    """Data entry page with form to add new health metrics"""
    return render_template("entry.html")


@web_bp.route("/user")
@login_required
def user_settings():
    """User settings page."""
    return render_template("user.html")


@web_bp.route("/coach")
@login_required
def coach():
    """Connection to the coach page with personalized recommendations based on user data"""
    return render_template("coach.html")


@web_bp.route("/docs")
@login_required
def docs_index():
    tree = build_docs_tree()
    docs_query = request.args.get("q", "").strip()
    page, per_page = _parse_docs_pagination_args()
    current_section = next(iter(tree), None)
    section_pages = tree.get(current_section, []) if current_section else []
    section_pages = _filter_section_pages(section_pages, docs_query)
    section_pages, page, total_pages = _paginate_docs(section_pages, page, per_page)
    return render_template(
        "docs_layout.html",
        tree=tree,
        current=None,
        current_section=current_section,
        section_pages=section_pages,
        docs_query=docs_query,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        per_page_options=DOCS_PER_PAGE_OPTIONS,
        content_blocks=None,
    )


@web_bp.route("/docs/<path:doc_path>")
@login_required
def docs_page(doc_path: str):
    tree = build_docs_tree()
    docs_query = request.args.get("q", "").strip()
    page, per_page = _parse_docs_pagination_args()
    doc_file = _resolve_doc_file(doc_path)

    if doc_file is None:
        section_pages = tree.get(doc_path)
        if section_pages is None:
            abort(404)
        section_pages = _filter_section_pages(section_pages, docs_query)
        section_pages, page, total_pages = _paginate_docs(section_pages, page, per_page)
        return render_template(
            "docs_layout.html",
            tree=tree,
            current=None,
            current_section=doc_path,
            section_pages=section_pages,
            docs_query=docs_query,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            per_page_options=DOCS_PER_PAGE_OPTIONS,
            content_blocks=None,
        )

    text = doc_file.read_text(encoding="utf-8")
    content_blocks = _render_docs_markdown_blocks(text)
    current = doc_file.relative_to(DOCS_DIR).with_suffix("").as_posix()
    current_section = _section_from_doc_path(current)

    section_pages = _filter_section_pages(tree.get(current_section, []), docs_query)
    section_pages, page, total_pages = _paginate_docs(section_pages, page, per_page)

    return render_template(
        "docs_layout.html",
        tree=tree,
        current=current,
        current_section=current_section,
        section_pages=section_pages,
        docs_query=docs_query,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        per_page_options=DOCS_PER_PAGE_OPTIONS,
        content_blocks=content_blocks,
    )


@web_bp.route("/admin")
@web_bp.route("/clients")
# @web_bp.route("/users")
@login_required
def clients():
    """Admin clients page with list of clients and subscription status."""
    if not current_user.is_admin:
        abort(403)

    email_query = request.args.get("email", "").strip().lower()
    per_page_raw = request.args.get("per_page", "10").strip().lower()
    page_raw = request.args.get("page", "1").strip()

    allowed_per_page = {"5", "10", "20", "all"}
    if per_page_raw not in allowed_per_page:
        per_page_raw = "10"

    per_page = per_page_raw if per_page_raw == "all" else int(per_page_raw)

    try:
        page = int(page_raw)
    except ValueError:
        page = 1
    if page < 1:
        page = 1

    query = db.session.query(
        User,
        func.max(HealthEntry.date).label("last_entry_date"),
    ).join(
        AdminClientAssignment,
        AdminClientAssignment.client_user_id == User.id,
    ).outerjoin(
        HealthEntry, HealthEntry.user_id == User.id
    ).filter(
        AdminClientAssignment.admin_user_id == current_user.id
    )

    if email_query:
        query = query.filter(
            or_(
                User.email.ilike(f"%{email_query}%"),
                User.name.ilike(f"%{email_query}%"),
            )
        )

    query = query.group_by(User.id)

    total_clients = query.count()
    total_pages = (
        1 if per_page == "all" else max(1, (total_clients + per_page - 1) // per_page)
    )
    if page > total_pages:
        page = total_pages

    paginated_query = query.order_by(User.name.asc(), User.email.asc())
    if per_page != "all":
        paginated_query = paginated_query.offset((page - 1) * per_page).limit(per_page)

    users_with_last_entry = paginated_query.all()
    selected_user_id = session.get("selected_user_id")
    return render_template(
        "clients.html",
        users_with_last_entry=users_with_last_entry,
        selected_user_id=selected_user_id,
        email_query=email_query,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        per_page_options=["5", "10", "20", "all"],
    )


@web_bp.route("/admin/clients/<int:user_id>/subscription", methods=["POST"])
@web_bp.route("/admin/users/<int:user_id>/subscription", methods=["POST"])
@login_required
def update_client_subscription(user_id: int):
    """Admin-only subscription status update."""
    if not current_user.is_admin:
        abort(403)

    user = (
        db.session.query(User)
        .join(
            AdminClientAssignment,
            AdminClientAssignment.client_user_id == User.id,
        )
        .filter(
            AdminClientAssignment.admin_user_id == current_user.id,
            User.id == user_id,
        )
        .first()
    )
    if user is None:
        abort(404)
    next_status = request.form.get("status", "").strip().lower()
    email_query = request.form.get("email", "").strip().lower()
    per_page = request.form.get("per_page", "10").strip()
    page = request.form.get("page", "1").strip()

    if next_status not in {"active", "inactive"}:
        abort(400)

    user.has_subscription = next_status == "active"
    db.session.commit()

    return redirect(
        url_for("web.clients", email=email_query, per_page=per_page, page=page)
    )


@web_bp.route("/admin/clients/<int:user_id>/select", methods=["POST"])
@login_required
def select_client(user_id: int):
    """Set the currently selected client for the logged-in admin session."""
    if not current_user.is_admin:
        abort(403)

    user = (
        db.session.query(User)
        .join(
            AdminClientAssignment,
            AdminClientAssignment.client_user_id == User.id,
        )
        .filter(
            AdminClientAssignment.admin_user_id == current_user.id,
            User.id == user_id,
        )
        .first()
    )
    if user is None:
        abort(404)

    session["selected_user_id"] = user.id

    return redirect(
        url_for(
            "web.clients",
            email=request.form.get("email", "").strip().lower(),
            per_page=request.form.get("per_page", "10").strip(),
            page=request.form.get("page", "1").strip(),
        )
    )


# test route
@web_bp.route("/test")
def test():
    """To test html rendering and API connectivity"""
    return render_template("test.html")
