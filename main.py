"""
main.py

Development runner for the PhySioLog Flask app. It is only development runner,
not for production. In production, you we use  a WSGI server (Gunicorn).
Check wsig.py for the production entry point.

Author: Jose Guzman, sjm.guzman<at>gmail.com

Run:
>>>  uv run python main.py
"""

from physiolog import create_app

app = create_app()

if __name__ == "__main__":
    print("\n🏃‍♂️ PhysioLog Starting (dev)...")
    print("📊 Visit: http://localhost:5001\n")
    # in development we run the Flask built-in server, not suitable for production
    app.run(host="0.0.0.0", port=5001)
