#!/usr/bin/env python3
"""
Create a full PostgreSQL backup using pg_dump.
Requires pg_dump to be installed and accessible in the system PATH.
and the SQLALCHEMY_DATABASE_URI environment variable to be set

Usage:
    uv run python scripts/backup_postgres.py
    uv run python scripts/backup_postgres.py --output /tmp/physiolog.dump

Environment:
    SQLALCHEMY_DATABASE_URI=postgresql+psycopg://user:password@host:5432/dbname
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


def normalize_postgres_uri(uri: str) -> str:
    if uri.startswith("postgresql+psycopg://"):
        return "postgresql://" + uri[len("postgresql+psycopg://") :]
    if uri.startswith("postgresql://"):
        return uri
    raise ValueError("SQLALCHEMY_DATABASE_URI must be a PostgreSQL URI")


def default_output_path(db_name: str) -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return Path.cwd() / f"{db_name}_{timestamp}.dump"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a full PostgreSQL database backup with pg_dump."
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output dump file path. Defaults to ./<dbname>_<timestamp>.dump",
    )
    args = parser.parse_args()

    db_uri = os.environ.get("SQLALCHEMY_DATABASE_URI")
    if not db_uri:
        print("Error: SQLALCHEMY_DATABASE_URI is not set", file=sys.stderr)
        return 1

    try:
        postgres_uri = normalize_postgres_uri(db_uri)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    parsed = urlparse(postgres_uri)
    db_name = parsed.path.lstrip("/")
    if not db_name:
        print(
            "Error: database name is missing in SQLALCHEMY_DATABASE_URI",
            file=sys.stderr,
        )
        return 1

    output_path = args.output or default_output_path(db_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "pg_dump",
        "-Fc",
        "-f",
        str(output_path),
        postgres_uri,
    ]

    try:
        subprocess.run(command, check=True)
    except FileNotFoundError:
        print("Error: pg_dump is not installed or not on PATH", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"Error: pg_dump failed with exit code {exc.returncode}", file=sys.stderr)
        return exc.returncode

    print(f"Backup created: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
