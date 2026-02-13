"""
main.py

Development runner for the PhySioLog Flask app. It is only development runner,
not for production. In production, you we use  a WSGI server (Gunicorn)

Author: Jose Guzman, sjm.guzman<at>gmail.com

Run:
>>>  uv run python main.py
"""

from physiolog import create_app

app = create_app()

if __name__ == "__main__":
    print("\n🏃‍♂️ Physiolog Starting (dev)...")
    print("📊 Visit: http://localhost:5000\n")
    # in development we run the Flask built-in server, not suitable for production
    app.run(host="0.0.0.0", port=5000)
