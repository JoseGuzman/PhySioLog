"""
extensions.py

It contains the SQLAlchemy extension instance for the PhySioLog Flask application.
That's basically the database connection and Object Relational Mapping
(ORM) layer for the app.

Author: Jose Guzman, sjm.guzman<at>gmail.com
Created: Sun Jan 25 09:23:24 CET 2026
"""

from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

# database as global to be imported in other modules without circular imports
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = str("web.login")  # Redirect to login page if not authenticated
login_manager.login_message_category = "warning"  # Flash category for login messages.
