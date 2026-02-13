"""
routes_api.py

It defines the API routes for the PhySioLog Flask application.

Author: Jose Guzman, sjm.guzman<at>gmail.com
"""

from datetime import datetime

from flask import Blueprint, Response, jsonify, request
from sqlalchemy.exc import IntegrityError

from .extensions import db
from .models import HealthEntry
from .services import compute_stats

api_bp = Blueprint("api", __name__, url_prefix="/api")


# =========================================================================
# API Routes
# =========================================================================
@api_bp.route("/entries", methods=["GET", "POST"])
def entries() -> Response | tuple[Response, int]:
    """
    Handle health entry retrieval and creation.

    GET
    ---
    Returns all health entries ordered by date (descending).

    Response:
        200 OK
        JSON list[dict]: Serialized HealthEntry objects.

    POST
    ----
    Creates a new health entry from JSON payload.

    Expected JSON fields:
        - date (str, required): Format YYYY-MM-DD
        - weight (float, optional)
        - body_fat (float, optional)
        - calories (int, optional)
        - steps (int, optional)
        - sleep_total (float, optional)
        - sleep_quality (str, optional)
        - observations (str, optional)

    Responses:
        201 Created:
            Entry successfully created.
        400 Bad Request:
            Invalid JSON, missing fields, or invalid date format.
        409 Conflict:
            Entry for the provided date already exists.

    Returns:
        flask.Response or (flask.Response, int):
            JSON response containing success status and data or error message.
    """
    if request.method == "POST":
        if not request.is_json:
            return jsonify(
                {"success": False, "error": "Content-Type must be application/json"}
            ), 400

        data = request.json
        if data is None:
            return jsonify({"success": False, "error": "Invalid JSON data"}), 400

        date_str = (data.get("date") or "").strip()
        if not date_str:
            return jsonify({"success": False, "error": "Date is required"}), 400

        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"success": False, "error": "Invalid date format"}), 400

        entry = HealthEntry(
            date=parsed_date,
            weight=data.get("weight"),
            body_fat=data.get("body_fat"),
            calories=data.get("calories"),
            steps=data.get("steps"),
            sleep_total=data.get("sleep_total"),
            sleep_quality=data.get("sleep_quality"),
            observations=data.get("observations"),
        )

        db.session.add(entry)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({"success": False, "error": "Date already exists"}), 409
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 400

        return jsonify({"success": True, "entry": entry.to_dict()}), 201

    all_entries = HealthEntry.query.order_by(HealthEntry.date.desc()).all()
    return jsonify([entry.to_dict() for entry in all_entries])


@api_bp.route("/stats")
def stats() -> Response | tuple[Response, int]:
    """Calculate statistics"""
    entries = HealthEntry.query.all()

    if not entries:
        return jsonify({"error": "No data available"}), 404

    return jsonify(compute_stats(entries))
