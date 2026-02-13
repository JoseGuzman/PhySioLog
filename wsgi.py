"""
wsgi.py

WSGI entrypoint for production servers (Gunicorn).
"""

from physiolog import create_app

app = create_app()
