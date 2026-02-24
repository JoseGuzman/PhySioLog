"""
Entry-related parsing and mapping helpers.
"""

from __future__ import annotations

from datetime import date, datetime
import re
from typing import Any, Mapping

SLEEP_HHMM_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def parse_entry_date_required(data: Mapping[str, Any]) -> date:
    """Parse required entry date in YYYY-MM-DD format."""
    date_str = str(data.get("date") or "").strip()
    if not date_str:
        raise ValueError("Date is required")

    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("Invalid date format") from exc


def parse_optional_sleep_total_hhmm(value: Any) -> float | None:
    """Parse optional sleep_total in HH:MM format and return decimal hours."""
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValueError("sleep_total must be in HH:MM format")

    sleep_match = SLEEP_HHMM_RE.match(value.strip())
    if not sleep_match:
        raise ValueError("sleep_total must be in HH:MM format")

    hours = int(sleep_match.group(1))
    minutes = int(sleep_match.group(2))
    return hours + (minutes / 60.0)


def build_entry_fields(
    data: Mapping[str, Any], sleep_decimal: float | None
) -> dict[str, Any]:
    """Build the shared field mapping for create/update entry flows."""
    return {
        "weight": data.get("weight"),
        "body_fat": data.get("body_fat"),
        "calories": data.get("calories"),
        "training_volume": data.get("training_volume"),
        "steps": data.get("steps"),
        "sleep_total": sleep_decimal,
        "sleep_quality": data.get("sleep_quality"),
        "observations": data.get("observations"),
    }
