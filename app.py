"""
App.py

PhySioLog: Health Tracker is a multi-view Flask application that serves as a health tracker.
It allows users to log daily health metrics such as weight, body fat percentage,
calories consumed, steps taken, sleep duration, and quality.
The application provides an API to create new entries and retrieve statistics based on
the logged data.

Author: Jose Guzman, sjm.guzman<at>gmail.com
Created: Sun Jan 25 09:23:24 CET 2026

Legacy dev runner (kept for compatibility).
Prefer running: uv run python main.py
"""

from physiolog import create_app

app = create_app()

if __name__ == "__main__":
    # when running locally with uv run python app.py,
    # the app will be available at http://localhost:5000
    print("\n🏃‍♂️ Physiolog Starting...")
    print("📊 Visit: http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000)
