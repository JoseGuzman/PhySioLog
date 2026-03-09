"""
stats.py

Utility functions and business-logic services for the PhySioLog application.

This module intentionally avoids dependencies on Flask or SQLAlchemy so that
its functions can be reused in scripts, tests, background tasks, or notebooks.

Use cases
---------
1. API layer:
    Compute summary statistics for health entries returned by the database.

    >>> entries = HealthEntry.query.all()
    >>> compute_stats(entries)

2. Streaming / large datasets:
    Process entries lazily without loading everything into memory.

    >>> compute_stats(HealthEntry.query.yield_per(100))

3. Unit testing:
    Use lightweight mock objects or dataclasses without requiring a database.

    >>> from dataclasses import dataclass
    >>> @dataclass
    ... class FakeEntry:
    ...     weight_kg: float | None = 70.0
    ...     body_fat_percent: float | None = 20.0
    ...     calories_kcal: int | None = 2000
    ...     steps_count: int | None = 8000
    ...     sleep_hours: float | None = 7.5
    >>> compute_stats([FakeEntry()])
"""

from __future__ import annotations

from typing import Iterable, Protocol

# from .models import HealthEntry
# Map output statistic keys -> HealthEntry attribute names
METRICS: dict[str, str] = {
    "avg_weight": "weight_kg",
    "avg_body_fat": "body_fat_percent",
    "avg_calories": "calories_kcal",
    "avg_protein": "protein_g",
    "avg_steps": "steps_count",
    "avg_sleep": "sleep_hours",
}


class HasHealthMetrics(Protocol):
    """
    Structural typing protocol for objects containing health metric fields.

    This protocol defines the minimal set of attributes required by
    statistics functions in this module (e.g., ``compute_stats``).

    Any object that exposes these attributes — such as SQLAlchemy models,
    dataclasses, or lightweight test doubles — satisfies this protocol
    without explicit inheritance.

    Purpose:
        - Decouple business logic from the database layer.
        - Allow unit testing with simple mock objects.
        - Enable reuse of statistical functions outside Flask or SQLAlchemy.

    Required attributes:
        weight_kg (float | None):
            Body weight in kilograms.
        body_fat_percent (float | None):
            Body fat percentage.
        calories_kcal (int | None):
            Daily caloric intake.
        protein_g (float | None):
            Daily protein intake in grams.
        steps_count (int | None):
            Number of steps recorded.
        sleep_hours (float | None):
            Total sleep duration in hours.
    """

    weight_kg: float | None
    body_fat_percent: float | None
    calories_kcal: int | None
    protein_g: float | None
    steps_count: int | None
    sleep_hours: float | None


def compute_stats(entries: Iterable[HasHealthMetrics]) -> dict[str, float | int | None]:
    """
    Compute aggregate statistics from an iterable of health-metric objects.

    The function processes entries in a single pass, making it memory-efficient
    for large datasets or streaming database queries.

    Args:
        entries:
            Any iterable of objects matching the ``HasHealthMetrics`` protocol.

    Returns:
        dict[str, float | int | None]:
            Dictionary containing averaged metrics and total entry count.
            Keys are defined by ``METRICS`` plus ``total_entries``.
    """
    sums: dict[str, float] = {stat_key: 0.0 for stat_key in METRICS}
    counts: dict[str, int] = {stat_key: 0 for stat_key in METRICS}
    total_entries = 0

    for e in entries:
        total_entries += 1
        for stat_key, attr_name in METRICS.items():
            value = getattr(e, attr_name)
            if value is not None:
                sums[stat_key] += float(value)
                counts[stat_key] += 1

    def avg(stat_key: str) -> float | None:
        if counts[stat_key] == 0:
            return None
        return round(sums[stat_key] / counts[stat_key], 2)

    result: dict[str, float | int | None] = {k: avg(k) for k in METRICS}
    result["total_entries"] = total_entries
    return result
