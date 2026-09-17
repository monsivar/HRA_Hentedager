"""Small dependency-free tests for the HRA date logic."""

from datetime import date

from custom_components.hra_renovasjon.coordinator import days_until, parse_collection_date


def test_parse_iso_datetime() -> None:
    assert parse_collection_date("2026-09-18T00:00:00") == date(2026, 9, 18)


def test_parse_iso_date() -> None:
    assert parse_collection_date("2026-09-18") == date(2026, 9, 18)


def test_days_until() -> None:
    assert days_until(date(2026, 9, 20), date(2026, 9, 17)) == 3
