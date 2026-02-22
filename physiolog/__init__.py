"""
__init__.py

Main Flask Application Factory with Blueprints.

PhySioLog: Health Tracker is a multi-view Flask application that serves as a health tracker.
It allows users to log daily health metrics such as weight, body fat percentage,
calories consumed, steps taken, sleep duration, and quality.
The application provides an API to create new entries and retrieve statistics based on
the logged data.

Author: Jose Guzman, sjm.guzman<at>gmail.com
Created: Sun Jan 25 09:23:24 CET 2026

Usage:
------
Shell context (only available in development):
(see here: https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iv-database)
Typing flask shell will permit access to the app and database. Note that
we need a .flaskenv file with FLASK_ENV=physiology:create_app:
>>> uv run flask shell
Python 3.12.12 (main, Jan 27 2026, 23:31:45) [Clang 21.1.4 ] on darwin
App: physiolog
Instance: /path/to/repo/instance
>>> app
>>> <Flask 'physiolog'>
>>> db
>>> <SQLAlchemy sqlite:////path/to/repo/instance/physiolog_users.db>
>>> User
>>> User <class 'physiolog.models.User'>
>>> myuser = User.query.filter_by(username='jose').first()
>>> myuser = User.query.filter(User.email == 'jose.guzman@example.com').first()
>>> db.session.commit()
"""

from pathlib import Path

from flask import Flask

from physiolog.config import Config

from .extensions import db

# physiolog/ is a subfolder, target templates and static folders in the parent directory
BASE_DIR = Path(__file__).resolve().parent.parent


def create_app(config_class=None) -> Flask:
    """Creates Flask app objects and returns it

    Args:
        config_class (_type_, optional): _description_. Defaults to None.

    Returns:
        Flask: A Flask app object
    """
    # Create Flask app with custom static and template folders
    app = Flask(
        __name__,
        static_folder=str(BASE_DIR / "static"),
        template_folder=str(BASE_DIR / "templates"),
        static_url_path="/static",
    )
    if config_class is None:
        config_class = Config  # default to Config class in config.py if not provided
    app.config.from_object(config_class)  # check config.py

    db.init_app(app)
    from . import models  # import models to create tables with db.create_all()

    # provide shell context for development
    @app.shell_context_processor
    def make_shell_context():
        """Shell context for flask shell command in development

        Returns:
            dict: A dictionary of app and db objects for flask shell
        """
        return {"app": app, "db": db}

    # Import and register modular blueprints
    from .routes_api import api_bp  # API routes
    from .routes_web import web_bp  # web routes

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)

    # The app context is needed to register blueprints and initialize the database
    with app.app_context():
        # Create database tables if they don't exist
        # database creation only if AUTO_CREATE_DB = true
        create_db = app.config.get("AUTO_CREATE_DB", False)
        debug = app.config.get("DEBUG", False)
        if create_db or debug:
            db.create_all()

    return app
