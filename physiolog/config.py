"""
Config.py
Set Flask Config variables.

This file records environmental variables in a file called .env to set the Flask
environment in production or debug mode. It also sets the database URI for SQLAlchemy.
In production, you would typically set the database URI to a more robust database
like PostgreSQL, while in development you can use SQLite for simplicity.

Check here: https://hackersandslackers.com/configure-flask-applications/
Check here to use S3 for static content:
https://abhishekm47.medium.com/serve-static-assets-on-s3-bucket-a-complete-flask-guide-fbe128d97e71

Author: Jose Guzman, sjm.guzman<at>gmail.com
Created: Fri Feb 13 07:48:57 CET 2026
"""

from os import environ
from pathlib import Path

from dotenv import load_dotenv

BASEDIR = Path(__file__).resolve().parent


# Load .env file from project root (above physiolog/ folder)
load_dotenv(BASEDIR.parent / ".env")


class Config:
    """Base configuration (shared by all environments)."""

    SECRET_KEY = environ.get("SECRET_KEY", "dev-fallback-key")

    SQLALCHEMY_DATABASE_URI = environ.get(
        "SQLALCHEMY_DATABASE_URI", "sqlite:///physiolog.db"
    )

    AUTO_CREATE_DB = environ.get("AUTO_CREATE_DB", "True").lower() == "true"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Convert string to boolean safely
    DEBUG = environ.get("FLASK_DEBUG", "False").lower() == "true"
