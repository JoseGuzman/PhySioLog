"""
routes_web.py

It defines the web routes for the PhySioLog Flask application.

Author: Jose Guzman, sjm.guzman<at>gmail.com
"""

from urllib.parse import urlparse
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func, or_

from .extensions import db
from .models import HealthEntry, User

web_bp = Blueprint("web", __name__)


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


@web_bp.route("/admin")
@web_bp.route("/clients")
#@web_bp.route("/users")
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

    query = (
        db.session.query(
            User,
            func.max(HealthEntry.date).label("last_entry_date"),
        )
        .outerjoin(HealthEntry, HealthEntry.user_id == User.id)
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
    total_pages = 1 if per_page == "all" else max(1, (total_clients + per_page - 1) // per_page)
    if page > total_pages:
        page = total_pages

    paginated_query = query.order_by(User.name.asc(), User.email.asc())
    if per_page != "all":
        paginated_query = paginated_query.offset((page - 1) * per_page).limit(per_page)

    users_with_last_entry = paginated_query.all()
    return render_template(
        "clients.html",
        users_with_last_entry=users_with_last_entry,
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

    user = User.query.get_or_404(user_id)
    next_status = request.form.get("status", "").strip().lower()
    email_query = request.form.get("email", "").strip().lower()
    per_page = request.form.get("per_page", "10").strip()
    page = request.form.get("page", "1").strip()

    if next_status not in {"active", "inactive"}:
        abort(400)

    user.has_subscription = next_status == "active"
    db.session.commit()

    return redirect(url_for("web.clients", email=email_query, per_page=per_page, page=page))


# test route
@web_bp.route("/test")
def test():
    """To test html rendering and API connectivity"""
    return render_template("test.html")
