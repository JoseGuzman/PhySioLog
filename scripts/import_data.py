#!/usr/bin/env python3
"""
Import health data from CSV/TSV file

Author: Jose Guzman
Created: Thu Feb  5 09:29:27 CET 2026

Usage:
>>>  uv run python scripts/import_data.py data/health_data.csv
"""

import argparse
import os
import sys
from datetime import date as Date
from datetime import datetime
from getpass import getpass
from pathlib import Path

import pandas as pd

# Ensure project root is importable BEFORE importing app modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from physiolog import create_app
from physiolog.extensions import db
from physiolog.models import HealthEntry, User


def parse_time(time_str: str) -> float | None:
    """
    Parse a time string in 'h:mm[:ss]' format and return total hours in decimal format.
    Returns None for empty, NaN, or placeholder values ('--').
    """
    if time_str is None or pd.isna(time_str):
        return None

    if not isinstance(time_str, str):
        raise TypeError(f"Expected string, got {type(time_str).__name__}")

    time_str = time_str.strip()
    if time_str in ("", "--"):
        return None

    parts = time_str.split(":")
    if len(parts) < 2:
        raise ValueError(f"Invalid time format: {time_str!r}. Expected 'h:mm[:ss]'")

    try:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2]) if len(parts) == 3 else 0
    except ValueError as exc:
        raise ValueError(
            f"Invalid time format: {time_str!r}. Expected 'h:mm[:ss]'"
        ) from exc

    # Proper range checks
    if hours < 0 or hours > 24:
        raise ValueError(
            f"Invalid time format: {time_str!r}. Hours must be between 0 and 24"
        )
    if minutes < 0 or minutes >= 60:
        raise ValueError(
            f"Invalid time format: {time_str!r}. Minutes must be between 0 and 59"
        )
    if seconds < 0 or seconds >= 60:
        raise ValueError(
            f"Invalid time format: {time_str!r}. Seconds must be between 0 and 59"
        )

    return round(hours + minutes / 60 + seconds / 3600, 2)


def parse_number(value) -> float | None:
    """
    Parse number with comma as decimal separator.
    Returns None for empty/NaN/'--'.
    """
    if value is None or pd.isna(value) or value == "--" or value == "":
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError as exc:
        msg = f"{value!r} invalid argument; expected number"
        raise ValueError(msg) from exc


def parse_date(date_str) -> Date | None:
    """
    Parse a date string in common formats and return a `date`.

    Accepts formats:
    - dd/mm/YYYY
    - YYYY-mm-dd
    - mm/dd/YYYY
    - dd-mm-YYYY

    Returns None for NaN/empty/placeholder values or if parsing fails.
    """
    if date_str is None or pd.isna(date_str) or date_str == "--" or date_str == "":
        return None

    formats = ["%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y"]
    s = str(date_str).strip()
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def import_data(app, filepath: str, demo_password: str | None = None) -> None:
    """
    Imports health data from a CSV or TSV file into the database.
    """
    print(f"\n📊 Importing data from {filepath}...")

    sep = "\t" if filepath.endswith(".tsv") else ","
    df = pd.read_csv(filepath, sep=sep, encoding="utf-8")

    print(f"\n📋 Found columns: {list(df.columns)}\n")

    column_map: dict[str, str] = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        if "date" in col_lower:
            column_map["date"] = col
        elif "weight" in col_lower and "kg" in col_lower:
            column_map["weight"] = col
        elif "body" in col_lower and "fat" in col_lower:
            column_map["body_fat"] = col
        elif "calorie" in col_lower:
            column_map["calories"] = col
        elif (
            "training" in col_lower and "volume" in col_lower
        ) or "volumen" in col_lower:
            column_map["training_volume"] = col
        elif "step" in col_lower:
            column_map["steps"] = col
        elif "sleep total" in col_lower or (
            ("sleep" in col_lower) and ("total" in col_lower)
        ):
            column_map["sleep_total"] = col
        elif "sleep quality" in col_lower or (
            ("sleep" in col_lower) and ("quality" in col_lower)
        ):
            column_map["sleep_quality"] = col
        elif "observation" in col_lower or "notes" in col_lower:
            column_map["observations"] = col

    print(f"📌 Mapped columns: {column_map}\n")

    if "date" not in column_map:
        print("❌ Error: Could not find a 'Date' column!")
        print(f"Available columns: {list(df.columns)}")
        sys.exit(1)

    added = 0
    updated = 0
    skipped = 0
    errors = 0

    with app.app_context():
        db.create_all()

        demo_email = "demo@physiolog.com"
        demo_user = User.query.filter_by(email=demo_email).first()
        if not demo_user:
            demo_user = User(
                name="Demo User",
                email=demo_email,
                age=49,
                height_cm=168,
                weight_kg=70,
            )
            if demo_password is None:
                demo_password = os.environ.get("DEMO_USER_PASSWORD")
                print(
                    f"Using DEMO_USER_PASSWORD from environment: {demo_password is not None}"
                )
            if demo_password is None:
                demo_password = getpass(
                    "Enter password for demo@physiolog.com: "
                ).strip()
            if not demo_password:
                print("Error: Password cannot be empty")
                sys.exit(1)
            demo_user.set_password(demo_password)
            db.session.add(demo_user)
            db.session.commit()
            print(f"✓ Demo user created: {demo_email}")

        for idx, row in df.iterrows():
            try:
                entry_date = parse_date(row[column_map["date"]])
                if not entry_date:
                    errors += 1
                    continue

                training_volume_val = (
                    parse_number(row.get(column_map.get("training_volume")))
                    if "training_volume" in column_map
                    else None
                )

                existing = HealthEntry.query.filter_by(
                    user_id=demo_user.id, date=entry_date
                ).first()
                if existing:
                    if (
                        training_volume_val is not None
                        and existing.training_volume != training_volume_val
                    ):
                        existing.training_volume = training_volume_val
                        updated += 1
                    else:
                        skipped += 1
                    continue

                calories_val = (
                    parse_number(row.get(column_map.get("calories")))
                    if "calories" in column_map
                    else None
                )
                steps_val = (
                    parse_number(row.get(column_map.get("steps")))
                    if "steps" in column_map
                    else None
                )

                entry = HealthEntry(
                    user_id=demo_user.id,
                    date=entry_date,
                    weight=parse_number(row.get(column_map.get("weight")))
                    if "weight" in column_map
                    else None,
                    body_fat=parse_number(row.get(column_map.get("body_fat")))
                    if "body_fat" in column_map
                    else None,
                    calories=int(calories_val) if calories_val is not None else None,
                    training_volume=training_volume_val,
                    steps=int(steps_val) if steps_val is not None else None,
                    sleep_total=parse_time(row.get(column_map.get("sleep_total")))
                    if "sleep_total" in column_map
                    else None,
                    sleep_quality=row.get(column_map.get("sleep_quality"))
                    if "sleep_quality" in column_map
                    and pd.notna(row.get(column_map.get("sleep_quality")))
                    and row.get(column_map.get("sleep_quality")) != "--"
                    else None,
                    observations=row.get(column_map.get("observations"))
                    if "observations" in column_map
                    and pd.notna(row.get(column_map.get("observations")))
                    else None,
                )

                db.session.add(entry)
                added += 1

            except Exception as e:
                errors += 1
                print(f"⚠️  Error on row {idx + 1}: {e}")
                continue

        db.session.commit()
        total = HealthEntry.query.count()

    print("✓ Import complete!")
    print(f"  • Added: {added} entries")
    print(f"  • Updated: {updated} entries (existing dates)")
    print(f"  • Skipped: {skipped} entries (already exist)")
    print(f"  • Errors: {errors} entries (invalid data)")
    print(f"  • Total in database: {total}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import health data from CSV/TSV")
    parser.add_argument(
        "filepath",
        nargs="?",
        default="data/health_data.csv",
        help="Path to CSV/TSV file (default: data/health_data.csv)",
    )
    parser.add_argument(
        "--password",
        dest="demo_password",
        help="Demo user password (if omitted, prompt interactively)",
    )
    args = parser.parse_args()
    myfilepath = args.filepath
    if args.filepath == "data/health_data.csv" and len(sys.argv) == 1:
        print("No file argument provided. Using default: data/health_data.csv")
    if not Path(myfilepath).exists():
        print(f"Error: File '{myfilepath}' not found")
        sys.exit(1)

    app = create_app()
    import_data(app=app, filepath=myfilepath, demo_password=args.demo_password)
