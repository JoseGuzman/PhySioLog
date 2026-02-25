from __future__ import annotations

from datetime import date

import pytest

from physiolog.services import (
    parse_entry_date_required,
    parse_optional_sleep_total_hhmm,
)


def test_parse_entry_date_required_accepts_yyyy_mm_dd() -> None:
    parsed = parse_entry_date_required({"date": "2026-02-15"})
    assert parsed == date(2026, 2, 15)


@pytest.mark.parametrize("payload", [{}, {"date": ""}, {"date": "2026/02/15"}])
def test_parse_entry_date_required_rejects_missing_or_invalid(payload: dict) -> None:
    with pytest.raises(ValueError):
        parse_entry_date_required(payload)


def test_parse_optional_sleep_total_hhmm_accepts_hh_mm() -> None:
    parsed = parse_optional_sleep_total_hhmm("07:30")
    assert parsed == 7.5


@pytest.mark.parametrize("value", [7.5, "24:00", "7:3", "abc"])
def test_parse_optional_sleep_total_hhmm_rejects_non_string_or_bad_format(
    value: object,
) -> None:
    with pytest.raises(ValueError):
        parse_optional_sleep_total_hhmm(value)
