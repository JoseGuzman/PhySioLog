"""
Config.py
Set Flask Config variables.

This file records environmental variables (e.g., in a file called .env) to set the Flask
environment in stagging, production or debug mode (by default).
It also sets the database URI for SQLAlchemy.
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
PROJECT_ROOT = BASEDIR.parent

# set APP_ENV (e.g.., export=APP_ENV=production)
APP_ENV = environ.get("APP_ENV", "development").strip().lower()
# Prefer .env.<env>; fallback to .env. Never override already-exported vars
ENV_FILE = PROJECT_ROOT / f".env.{APP_ENV}"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE, override=False)
else:
    load_dotenv(PROJECT_ROOT / ".env", override=False)


class BaseConfig:
    """Base configuration (shared by all environments)."""

    SECRET_KEY = environ.get("SECRET_KEY")

    # SQLite database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # default location instance/physiolog.db
    default_db_path = PROJECT_ROOT / "instance" / "physiolog.db"
    SQLALCHEMY_DATABASE_URI = environ.get(
        "SQLALCHEMY_DATABASE_URI", f"sqlite:///{default_db_path}"
    )

    # Automatic creation of initial user at app start
    AUTH_BOOTSTRAP_USER = environ.get("AUTH_BOOTSTRAP_USER", "").strip().lower()
    AUTH_BOOTSTRAP_PASSWORD = environ.get("AUTH_BOOTSTRAP_PASSWORD", "")
    AUTH_BOOTSTRAP_USER_ENABLED = (
        environ.get("AUTH_BOOTSTRAP_USER_ENABLED", "False").lower() == "true"
    )


class DevConfig(BaseConfig):
    """Development config (default)."""

    FLASK_ENV = "development"
    DEBUG = True
    # if not present, use a default
    SECRET_KEY = environ.get("SECRET_KEY", "dev-fallback-key")
    # AUTO_CREATE_DB=False
    AUTO_CREATE_DB = environ.get("AUTO_CREATE_DB", "True").lower() == "true"


class StagingConfig(BaseConfig):
    """Staging config.
    A pre-production environment for testing with production-like settings.
    It will use PostgreSQL
    """

    FLASK_ENV = "staging"
    DEBUG = False
    # AUTO_CREATE_DB=False
    AUTO_CREATE_DB = environ.get("AUTO_CREATE_DB", "False").lower() == "true"

    # Staging requires a SECRET_KEY
    SECRET_KEY = environ.get("SECRET_KEY") or None


class ProdConfig(BaseConfig):
    """Production config. The following settings should be set in the environment
    SECRET_KEY = environ["SECRET_KEY"]
    SQLALCHEMY_DATABASE_URI = environ["SQLALCHEMY_DATABASE_URI"]  # e.g., postgresql://user:password@host:port/dbname
    """

    FLASK_ENV = "production"
    DEBUG = False
    # AUTO_CREATE_DB=False
    AUTO_CREATE_DB = environ.get("AUTO_CREATE_DB", "False").lower() == "true"
    SECRET_KEY = environ.get("SECRET_KEY")  # must be set in environment for production
    SQLALCHEMY_DATABASE_URI = environ.get("SQLALCHEMY_DATABASE_URI")


def get_config_class():
    """Get the appropriate config class based on the APP_ENV."""
    if APP_ENV == "production":
        return ProdConfig
    elif APP_ENV == "staging":
        return StagingConfig
    else:
        return DevConfig
