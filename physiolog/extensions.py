"""
extensions.py

It contains the SQLAlchemy extension instance for the PhySioLog Flask application.

Author: Jose Guzman, sjm.guzman<at>gmail.com
Created: Sun Jan 25 09:23:24 CET 2026
"""

from flask_sqlalchemy import SQLAlchemy

# database as global to be imported in other modules without circular imports
db = SQLAlchemy()
