"""
routes_api.py

It defines the API routes for the PhySioLog Flask application.

Author: Jose Guzman, sjm.guzman<at>gmail.com
"""

from datetime import date, datetime, timedelta

from flask import Blueprint, Response, jsonify, request
from sqlalchemy.exc import IntegrityError

from .extensions import db
from .models import HealthEntry
from .services import (
    build_entry_fields,
    compute_stats,
    parse_entry_date_required,
    parse_optional_sleep_total_hhmm,
    run_smoke_test,
)

api_bp = Blueprint("api", __name__, url_prefix="/api")


def window_to_days(window_str: str) -> int | None:
    """Convert window strings like 7d/3m/1y to day counts."""
    s = window_str.strip().lower()
    if not s:
        return None
    if s.endswith("d"):
        return int(s[:-1])
    if s.endswith("m"):
        return int(s[:-1]) * 30
    if s.endswith("y"):
        return int(s[:-1]) * 365
    raise ValueError("Invalid window format")


# =========================================================================
# API Routes
# =========================================================================
@api_bp.route("/llm-smoke", methods=["GET"])
def llm_smoke() -> Response | tuple[Response, int]:
    """
    OpenAI API smoke test route to verify connectivity and basic functionality.

    Response:
        200 OK
        JSON object with test results or error message.
    """
    try:
        result = run_smoke_test()
        return jsonify(result), 200
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@api_bp.route("/entries", methods=["GET", "POST", "PUT"])
def entries() -> Response | tuple[Response, int]:
    """
        Handle health entry retrieval and creation.

    Retrieve health entries.

    Query parameters:
        - date (str, optional): Format YYYY-MM-DD
            If provided, returns a single entry for that date.
            If omitted, returns all entries ordered by date (descending).

    Response:
        200 OK
        JSON list[dict]: Serialized HealthEntry objects.
        200 OK:
        - Without `date`: JSON list[dict] of serialized HealthEntry objects.
        - With `date`: JSON object:
        {
            "success": true,
            "entry": { ... serialized HealthEntry ... }
        }
        400 Bad Request:
            Invalid `date` format.
        404 Not Found:
            No entry exists for the requested date.

        POST
        ----
        Creates a new health entry from JSON payload.

        Expected JSON fields:
            - date (str, required): Format YYYY-MM-DD
            - weight (float, optional)
            - body_fat (float, optional)
            - calories (int, optional)
            - steps (int, optional)
            - sleep_total (str, optional): Format HH:MM
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
    if request.method in {"POST", "PUT"}:
        if not request.is_json:
            return jsonify(
                {"success": False, "error": "Content-Type must be application/json"}
            ), 400

        data = request.json
        if data is None or not isinstance(data, dict):
            return jsonify({"success": False, "error": "Invalid JSON data"}), 400

        try:
            parsed_date = parse_entry_date_required(data)
            sleep_decimal = parse_optional_sleep_total_hhmm(data.get("sleep_total"))
        except ValueError as exc:
            return jsonify({"success": False, "error": str(exc)}), 400

        entry_fields = build_entry_fields(data, sleep_decimal)

        if request.method == "PUT":
            entry = HealthEntry.query.filter_by(date=parsed_date).first()
            if not entry:
                return jsonify(
                    {"success": False, "error": "Entry not found for the given date"}
                ), 404

            for field_name, field_value in entry_fields.items():
                setattr(entry, field_name, field_value)

            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                return jsonify({"success": False, "error": str(e)}), 400

            return jsonify({"success": True, "entry": entry.to_dict()}), 200

        entry = HealthEntry(
            date=parsed_date,
            **entry_fields,
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

    # GET request:
    date_str = request.args.get("date", type=str)
    if date_str:
        date_str = date_str.strip()
        try:
            query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify(
                {"success": False, "error": "Invalid date format, expected YYYY-MM-DD"}
            ), 400
        # If date is provided, return only that entry
        entry = HealthEntry.query.filter_by(date=query_date).first()
        if not entry:
            return jsonify(
                {"success": False, "error": "Entry not found for the given date"}
            ), 404
        return jsonify({"success": True, "entry": entry.to_dict()})

    window = request.args.get("window", default="", type=str).lower().strip()
    days_param = request.args.get("days", type=int)

    query = HealthEntry.query.order_by(HealthEntry.date.desc())
    days = None
    if days_param is not None:
        if days_param <= 0:
            return jsonify({"success": False, "error": "days must be a positive integer"}), 400
        days = days_param
    elif window:
        try:
            days = window_to_days(window)
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "format is 7d,30d,3m,1y"}), 400

    if days is not None:
        start_date = date.today() - timedelta(days=days - 1)
        query = query.filter(HealthEntry.date >= start_date)

    all_entries = query.all()
    serialized_entries = [entry.to_dict() for entry in all_entries]
    return jsonify({"success": True, "entries": serialized_entries})


@api_bp.route("/stats")  # GET only (default when no methods specified)
def stats() -> Response | tuple[Response, int]:
    """
    Return aggregated statitistics for health entries.

    Optional query parameters:
        days (int): if provided, restrict to the last N days of entries (default: all)
        Example: /api/stats?days=7 or /api/stats?window=7d 30d 3m 1y

    Response:
    Example response for /api/stats?days=7:
    {
        "window": "7d",
        "window_days": 7,
        "start_date": "2026-02-07",
        "end_date": "2026-02-13",
        "stats": {
            "avg_weight": 72.14,
            "avg_body_fat": 18.63,
            "avg_calories": 2132.5,
            "avg_steps": 8045.8,
            "avg_sleep": 7.36,
            "total_entries": 6
            }
        }
    """
    # recognize days=7
    days_param = request.args.get("days", type=int)
    # window can be: "", "7d", "30d", "3m", "1y", or omitted
    window = request.args.get("window", default="", type=str).lower().strip()

    # Decide days
    days = None
    if days_param is not None:
        if days_param <= 0:
            return jsonify({"success": False, "error": "days must be a positive integer"}), 400
        days = days_param
    elif window:  # window provided and not empty
        try:
            days = window_to_days(window)
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "format is 7d,30d,3m,1y"}), 400
    else:
        days = None  # all time

    query = HealthEntry.query.order_by(HealthEntry.date.desc())

    start_date = None
    end_date = date.today()

    if days is not None:
        start_date = end_date - timedelta(days=days - 1)
        query = query.filter(HealthEntry.date >= start_date)

    entries = query.all()
    if not entries:
        return jsonify({"success": False, "error": "No data available"}), 404

    # For all-time, expose an actual date span so the UI can show day count.
    if days is None:
        latest_entry_date = entries[0].date
        oldest_entry_date = entries[-1].date
        start_date = oldest_entry_date
        end_date = latest_entry_date
        window_days = (end_date - start_date).days + 1
    else:
        window_days = days

    return jsonify(
        {
            "success": True,
            "window": window or "all",
            "window_days": window_days,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat(),
            "stats": compute_stats(entries),
        }
    )
