"""
routes_web.py

It defines the web routes for the PhySioLog Flask application.

Author: Jose Guzman, sjm.guzman<at>gmail.com
"""

from flask import Blueprint, render_template

web_bp = Blueprint("web", __name__)


# =========================================================================
# Main App Routes (protected)
# =========================================================================
#
@web_bp.route("/")
def index():
    """Redirect to overview if logged in, otherwise to login page"""
    return render_template("overview.html")


@web_bp.route("/overview")
def overview():
    """Overview page with metabolism stats and input entry form"""
    return render_template("overview.html")


@web_bp.route("/trends")
def trends():
    """Visualizations page with trends charts"""
    return render_template("trends.html")


@web_bp.route("/entry")
def entry():
    """Data entry page with form to add new health metrics"""
    return render_template("entry.html")


@web_bp.route("/coach")
def coach():
    """Connection to the coach page with personalized recommendations based on user data"""
    return render_template("coach.html")


@web_bp.route("/test")
def test():
    """To test html rendering and API connectivity"""
    return render_template("test.html")
