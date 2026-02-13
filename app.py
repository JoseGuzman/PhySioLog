"""
App.py
PhySioLog: Health Tracker - Simple Flask Application

This is a multi-view Flask application that serves as a health tracker.
It allows users to log daily health metrics such as weight, body fat percentage,
calories consumed, steps taken, sleep duration, and quality.
The application provides an API to create new entries and retrieve statistics based on
the logged data.

Author: Jose Guzman, sjm.guzman<at>gmail.com
Created: Sun Jan 25 09:23:24 CET 2026
"""

from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy

from config import Config

BASE_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    static_folder=str(BASE_DIR / "static"),
    template_folder=str(BASE_DIR / "templates"),
    static_url_path="/static",
)

app.config.from_object(Config)

db = SQLAlchemy(app)


# =========================================================================
# Database Model
# =========================================================================
class HealthEntry(db.Model):
    """This is the registry of the database
    Args:
        db (_type_): _description_

    Returns:
        _type_: _description_
    """

    __tablename__ = "health_entries"  # set name of resulting table

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    weight = db.Column(db.Float)
    body_fat = db.Column(db.Float)
    calories = db.Column(db.Integer)
    steps = db.Column(db.Integer)
    sleep_total = db.Column(db.Float)
    sleep_quality = db.Column(db.String(20))
    observations = db.Column(db.Text)

    def to_dict(self) -> dict:
        """
        Converts the HealthEntry object to a dictionary for easy JSON serialization.
        Returns:
            dict: _description_
        """
        return {
            "id": self.id,
            "date": self.date.strftime("%Y-%m-%d"),
            "weight": self.weight,
            "body_fat": self.body_fat,
            "calories": self.calories,
            "steps": self.steps,
            "sleep_total": self.sleep_total,
            "sleep_quality": self.sleep_quality,
            "observations": self.observations,
        }


# =========================================================================
# Main App Routes (protected)
# =========================================================================
#
@app.route("/")
def index():
    """Redirect to overview if logged in, otherwise to login page"""
    return render_template("overview.html")


@app.route("/overview")
def overview():
    """Overview page with metabolism stats and input entry form"""
    return render_template("overview.html")


@app.route("/trends")
def trends():
    """Visualizations page with trends charts"""
    return render_template("trends.html")


@app.route("/entry")
def entry():
    """Data entry page with form to add new health metrics"""
    return render_template("entry.html")


@app.route("/coach")
def coach():
    """Connection to the coach page with personalized recommendations based on user data"""
    return render_template("coach.html")


@app.route("/test")
def test():
    """To test html rendering and API connectivity"""
    return render_template("test.html")


# =========================================================================
# Authentication routes
# =========================================================================


# =========================================================================
# API Routes (Protected)
# =========================================================================
@app.route("/api/entries", methods=["GET", "POST"])
def entries():
    if request.method == "POST":
        data = request.json
        try:
            entry = HealthEntry(
                date=datetime.strptime(data["date"], "%Y-%m-%d").date(),
                weight=data.get("weight"),
                body_fat=data.get("body_fat"),
                calories=data.get("calories"),
                steps=data.get("steps"),
                sleep_total=data.get("sleep_total"),
                sleep_quality=data.get("sleep_quality"),
                observations=data.get("observations"),
            )
            db.session.add(entry)
            db.session.commit()
            return jsonify({"success": True, "entry": entry.to_dict()}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 400

    # GET - return all entries
    entries = HealthEntry.query.order_by(HealthEntry.date.desc()).all()
    return jsonify([entry.to_dict() for entry in entries])


@app.route("/api/stats")
def stats():
    """Calculate statistics"""
    entries = HealthEntry.query.all()

    if not entries:
        return jsonify({"error": "No data available"}), 404

    def safe_avg(values):
        filtered = [v for v in values if v is not None]
        return round(sum(filtered) / len(filtered), 2) if filtered else None

    stats_data = {
        "avg_weight": safe_avg([e.weight for e in entries]),
        "avg_body_fat": safe_avg([e.body_fat for e in entries]),
        "avg_calories": safe_avg([e.calories for e in entries]),
        "avg_steps": safe_avg([e.steps for e in entries]),
        "avg_sleep": safe_avg([e.sleep_total for e in entries]),
        "total_entries": len(entries),
    }

    return jsonify(stats_data)


# Initialize database
with app.app_context():
    db.create_all()
    print("✓ Database initialized")

if __name__ == "__main__":
    # when running locally with uv run python app.py, 
    # the app will be available at http://localhost:5000
    print("\n🏃‍♂️ Physiolog Starting...")
    print("📊 Visit: http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000)
