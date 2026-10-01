"""
================================================================================
Module:     app/helpers/history_formatting.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.2.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Kleine, GUI-onafhankelijke formatters voor centrale historiek en
            read-only detailweergave. Tool-specifieke meetwaarden worden via
            een expliciete formatter-registry tot één compacte samenvatting
            opgebouwd zodat de tabel zelf multitool-neutraal blijft.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste formatters voor datum/tijd, capaciteit, ESR en
                        componentidentiteit.
  v1.1.0 (2026-10-01)  Helpers toegevoegd voor booleans, optionele getallen
                        en opgeslagen JSON-lijsten in detailweergave.
  v1.2.0 (2026-10-01)  Multitool meetwaardesamenvatting en één centrale
                        meetmethode-vertaalsleutelmapping toegevoegd.
================================================================================
"""

from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Callable


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


def measurement_method_translation_key(value: Any) -> str:
    """Geeft overal dezelfde publieke i18n-sleutel voor een meetmethode terug."""
    raw = getattr(value, "value", value)
    mapping = {
        "EX_SITU": "meetmethode.ex_situ",
        "ONE_LEG": "meetmethode.one_leg",
        "IN_CIRCUIT": "meetmethode.in_circuit",
    }
    return mapping.get(str(raw), f"settings.meetmethode.{raw}")


def _field(record: Any, name: str) -> Any:
    if isinstance(record, dict):
        return record.get(name)
    return getattr(record, name, None)


def _format_esr_capacitor_values(measurement: Any) -> str:
    values: list[str] = []
    capacitance_f = _field(measurement, "capacitance_f")
    esr_ohm = _field(measurement, "esr_ohm")
    if capacitance_f is not None:
        values.append(format_capacitance_f(capacitance_f))
    if esr_ohm is not None:
        values.append(format_esr_ohm(esr_ohm))
    return " · ".join(values) or "—"


MeasurementValuesFormatter = Callable[[Any], str]
_TOOL_VALUE_FORMATTERS: dict[str, MeasurementValuesFormatter] = {
    "ESR_CAPACITOR": _format_esr_capacitor_values,
}


def format_measurement_values(tool_key: str | None, measurement: Any) -> str:
    """Formatteert de compacte meetwaarde-kolom voor het opgegeven tooltype.

    Nieuwe tools voegen hier later één formatter toe zonder de tabelstructuur te
    wijzigen. Onbekende tooltypes tonen bewust geen verzonnen meetwaarden.
    """
    if not tool_key:
        return "—"
    formatter = _TOOL_VALUE_FORMATTERS.get(str(tool_key))
    return formatter(measurement) if formatter is not None else "—"
