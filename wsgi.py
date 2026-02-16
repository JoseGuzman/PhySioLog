"""
wsgi.py

Author: Jose Guzman, sjm.guzman<at>gmail.com

WSGI entrypoint for production servers (Gunicorn).

Usage:
To run the Flask locally
>>> uv run gunicorn -w 2 -b 0.0.0.0:8000 wsgi:app --access-logfile - --error-logfile - --timeout 60
"""

from physiolog import create_app

app = create_app()
