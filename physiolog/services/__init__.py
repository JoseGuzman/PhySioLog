"""
# physiolog/services/__init__.py

Serves as the entry point for the services package in the PhysioLog project. 
It imports and exposes service functions to use within the application.
"""

from .openai import run_smoke_test
from .stats import compute_stats
from .entries import (
    build_entry_fields,
    parse_entry_date_required,
    parse_optional_sleep_total_hhmm,
)
