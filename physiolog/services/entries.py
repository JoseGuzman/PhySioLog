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
    def pick_value(new_key: str, old_key: str) -> Any:
        if new_key in data:
            return data.get(new_key)
        return data.get(old_key)

    return {
        "weight_kg": pick_value("weight_kg", "weight"),
        "body_fat_percent": pick_value("body_fat_percent", "body_fat"),
        "calories_kcal": pick_value("calories_kcal", "calories"),
        "protein_g": pick_value("protein_g", "protein"),
        "training_volume_kg": pick_value("training_volume_kg", "training_volume"),
        "steps_count": pick_value("steps_count", "steps"),
        "sleep_hours": sleep_decimal,
        "sleep_quality": data.get("sleep_quality"),
        "observations": data.get("observations"),
    }
