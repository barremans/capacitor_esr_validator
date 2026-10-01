"""
================================================================================
Module:     app/helpers/history_filters.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       GUI-onafhankelijke opbouw van read-only historiekfilters.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste filterbuilder.
  v1.1.0 (2026-10-01)  tool_key toegevoegd voor centrale multitool-historiek.
================================================================================
"""
from __future__ import annotations
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
    return result
