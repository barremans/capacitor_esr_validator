"""
================================================================================
Module:     app/helpers/history_filters.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.2.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       GUI-onafhankelijke opbouw van read-only historiekfilters.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste filterbuilder.
  v1.1.0 (2026-10-01)  tool_key toegevoegd voor centrale multitool-historiek.
  v1.2.0 (2026-10-01)  Optionele lokale datumgrenzen toegevoegd voor de bestaande
                        measured_from_ms/measured_to_ms historiekfilters.
================================================================================
"""
from __future__ import annotations
from datetime import date, datetime, timedelta
from typing import Any


def build_history_filters(
    *,
    tool_key: str | None = None,
    manufacturer: str | None = None,
    series: str | None = None,
    measurement_method: str | None = None,
    instrument_key: str | None = None,
    frequency_hz: float | int | None = None,
    final_status: str | None = None,
    reliability_level: str | None = None,
    measured_from_ms: int | None = None,
    measured_to_ms: int | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in (
        ("tool_key", tool_key),
        ("manufacturer", manufacturer),
        ("series", series),
        ("measurement_method", measurement_method),
        ("instrument_key", instrument_key),
        ("final_status", final_status),
        ("reliability_level", reliability_level),
    ):
        if isinstance(value, str):
            value = value.strip()
        if value not in (None, ""):
            result[key] = value
    if frequency_hz is not None:
        result["frequency_hz"] = float(frequency_hz)
    if measured_from_ms is not None:
        result["measured_from_ms"] = int(measured_from_ms)
    if measured_to_ms is not None:
        result["measured_to_ms"] = int(measured_to_ms)
    return result


def parse_local_date_start_ms(text: str) -> int | None:
    """Parse YYYY-MM-DD als start van die lokale kalenderdag in epoch-ms."""
    parsed = _parse_optional_iso_date(text)
    if parsed is None:
        return None
    start = datetime.combine(parsed, datetime.min.time())
    return int(start.timestamp() * 1000)


def parse_local_date_end_ms(text: str) -> int | None:
    """Parse YYYY-MM-DD als inclusieve grens van de volledige lokale dag."""
    parsed = _parse_optional_iso_date(text)
    if parsed is None:
        return None
    next_day = datetime.combine(parsed + timedelta(days=1), datetime.min.time())
    return int(next_day.timestamp() * 1000) - 1


def _parse_optional_iso_date(text: str) -> date | None:
    cleaned = (text or "").strip()
    if not cleaned:
        return None
    return date.fromisoformat(cleaned)
