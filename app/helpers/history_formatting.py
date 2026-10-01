"""
================================================================================
Module:     app/helpers/history_formatting.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Kleine, GUI-onafhankelijke formatters voor historiek en de
            read-only detailweergave.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste formatters voor datum/tijd, capaciteit, ESR en
                        componentidentiteit.
  v1.1.0 (2026-10-01)  Helpers toegevoegd voor booleans, optionele getallen
                        en opgeslagen JSON-lijsten in detailweergave.
================================================================================
"""

from __future__ import annotations

from datetime import datetime
import json
from typing import Any


def format_local_datetime(epoch_ms: int | None) -> str:
    if epoch_ms is None:
        return "—"
    return datetime.fromtimestamp(epoch_ms / 1000.0).strftime("%Y-%m-%d %H:%M:%S")


def format_capacitance_f(value_f: float | None) -> str:
    if value_f is None:
        return "—"
    absolute = abs(value_f)
    if absolute >= 1e-3:
        return f"{value_f * 1e3:.4g} mF"
    if absolute >= 1e-6:
        return f"{value_f * 1e6:.4g} µF"
    if absolute >= 1e-9:
        return f"{value_f * 1e9:.4g} nF"
    return f"{value_f * 1e12:.4g} pF"


def format_esr_ohm(value_ohm: float | None) -> str:
    if value_ohm is None:
        return "—"
    if abs(value_ohm) < 1.0:
        return f"{value_ohm * 1000:.4g} mΩ"
    return f"{value_ohm:.4g} Ω"


def component_label(row: dict[str, Any]) -> str:
    parts = [row.get("manufacturer"), row.get("series"), row.get("part_number")]
    text = " ".join(str(part).strip() for part in parts if part and str(part).strip())
    return text or "—"


def format_optional_number(value: float | int | None, *, suffix: str = "") -> str:
    if value is None:
        return "—"
    number = f"{float(value):.6g}"
    return f"{number}{suffix}"


def format_bool(value: bool | None, yes: str = "Ja", no: str = "Nee") -> str:
    if value is None:
        return "—"
    return yes if value else no


def decode_json_list(value: str | None) -> tuple[str, ...]:
    """Decodeert alleen een opgeslagen JSON-lijst; corrupte data wordt zichtbaar gehouden."""
    if not value:
        return ()
    try:
        decoded = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return (str(value),)
    if not isinstance(decoded, list):
        return (str(value),)
    return tuple(str(item) for item in decoded)
