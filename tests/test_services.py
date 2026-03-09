"""
test_services.py

Used to test the compute_stats function in services.py

Author: Jose Guzman, sjm.guzman<at>gmail.com

Usage:
------
# requires uv sync --extra dev to install pytest in the virtual environment)
>>>  uv run pytest tests/test_services.py
"""

from __future__ import annotations

from dataclasses import dataclass

from physiolog.services import compute_stats


@dataclass
class FakeEntry:
    weight_kg: float | None = None
    body_fat_percent: float | None = None
    calories_kcal: int | None = None
    protein_g: int | None = None
    steps_count: int | None = None
    sleep_hours: float | None = None


def test_compute_stats_basic() -> None:
    entries = [
        FakeEntry(
            weight_kg=70.0,
            body_fat_percent=20.0,
            calories_kcal=2000,
            protein_g=160.0,
            steps_count=8000,
            sleep_hours=7.0,
        ),
        FakeEntry(
            weight_kg=72.0,
            body_fat_percent=None,
            calories_kcal=2200,
            protein_g=180.0,
            steps_count=None,
            sleep_hours=8.0,
        ),
        FakeEntry(
            weight_kg=None,
            body_fat_percent=18.0,
            calories_kcal=None,
            protein_g=None,
            steps_count=6000,
            sleep_hours=None,
        ),
    ]

    stats = compute_stats(entries)  # type: ignore[arg-type]

    assert stats["avg_weight"] == 71.0  # (70 + 72) / 2
    assert stats["avg_body_fat"] == 19.0  # (20 + 18) / 2
    assert stats["avg_calories"] == 2100.0  # (2000 + 2200) / 2
    assert stats["avg_protein"] == 170.0  # (160 + 180) / 2
    assert stats["avg_steps"] == 7000.0  # (8000 + 6000) / 2
    assert stats["avg_sleep"] == 7.5  # (7 + 8) / 2
    assert stats["total_entries"] == 3


def test_compute_stats_all_none() -> None:
    entries = [FakeEntry(), FakeEntry()]

    stats = compute_stats(entries)  # type: ignore[arg-type]

    assert stats["avg_weight"] is None
    assert stats["avg_body_fat"] is None
    assert stats["avg_calories"] is None
    assert stats["avg_protein"] is None
    assert stats["avg_steps"] is None
    assert stats["avg_sleep"] is None
    assert stats["total_entries"] == 2
