"""
routes_web.py

It defines the web routes for the PhySioLog Flask application.

Author: Jose Guzman, sjm.guzman<at>gmail.com
"""

from urllib.parse import urlparse
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from .extensions import db
from .models import User

web_bp = Blueprint("web", __name__)


@web_bp.route("/")
def index():
    """Redirect to overview if logged in, otherwise to login page"""
    if current_user.is_authenticated:
        return redirect(url_for("web.overview"))
    return redirect(url_for("web.login"))


@web_bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for("web.overview"))
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
            return redirect(nxt or url_for("web.overview"))
        flash("Invalid email or password", "error")
    return render_template("login.html")


@web_bp.route("/register", methods=["GET", "POST"])
def register():
    """Register page"""
    if current_user.is_authenticated:
        return redirect(url_for("web.overview"))

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


@web_bp.route("/overview")
@login_required
def overview():
    """Overview page with metabolism stats and input entry form"""
    return render_template("overview.html")


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


@web_bp.route("/coach")
@login_required
def coach():
    """Connection to the coach page with personalized recommendations based on user data"""
    return render_template("coach.html")


# test route
@web_bp.route("/test")
def test():
    """To test html rendering and API connectivity"""
    return render_template("test.html")
