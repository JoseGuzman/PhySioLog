"""
services.py

A helper module to provide common services and utilities for the

PhySioLog Flask application.
Author: Jose Guzman, sjm.guzman<at>gmail.com
"""

from __future__ import annotations

from typing import Iterable

from .models import HealthEntry


def safe_avg(values: Iterable[float | int | None]) -> float | None:
    """Return the mean of non-None values rounded to 2 decimals, or None if empty."""
    filtered = [v for v in values if v is not None]
    return round(sum(filtered) / len(filtered), 2) if filtered else None


def compute_stats(entries: list[HealthEntry]) -> dict[str, float | int | None]:
    """
    Compute aggregate statistics for a list of HealthEntry rows.

    Returns:
        dict with averages (float|None) and total_entries (int).
    """
    return {
        "avg_weight": safe_avg([e.weight for e in entries]),
        "avg_body_fat": safe_avg([e.body_fat for e in entries]),
        "avg_calories": safe_avg([e.calories for e in entries]),
        "avg_steps": safe_avg([e.steps for e in entries]),
        "avg_sleep": safe_avg([e.sleep_total for e in entries]),
        "total_entries": len(entries),
    }
