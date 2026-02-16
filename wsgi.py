"""
wsgi.py

Author: Jose Guzman, sjm.guzman<at>gmail.com

WSGI entrypoint for production servers (Gunicorn).

Usage:
>>> gunicorn wsgi:app -w 4 -b 0.0.0:8000
"""

from physiolog import create_app

app = create_app()
