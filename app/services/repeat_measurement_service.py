"""
================================================================================
Module:     app/services/repeat_measurement_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Zet één opgeslagen meetdetail om naar een veilige preset voor
            "Herhaal meting".

            Alleen bekende component- en meetcontext wordt hergebruikt.
            Oude meetwaarden, veiligheidsbevestiging, assessmentresultaten en
            referentie-snapshots worden bewust NIET als nieuwe waarheid
            overgenomen.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste immutable repeat-preset en mapping vanuit
                        StorageService.get_measurement_detail().
  v1.1.0 (2026-10-01)  Herhalen expliciet beperkt tot ESR_CAPACITOR;
                        toekomstige tools krijgen eigen repeat-mapping.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RepeatMeasurementPreset:
    """Veilige voorafinvulling voor een nieuwe, onafhankelijke meetrun."""

    source_measurement_id: int

    nominal_capacitance_value: float | None
    nominal_capacitance_unit: str | None
    tolerance_percent: float | None
    rated_voltage_v: float | None
    technology: str | None
    manufacturer: str | None
    series: str | None

    measurement_method: str | None
    instrument_key: str | None
    frequency_hz: float | None
    test_voltage_vrms: float | None
    temperature_c: float | None


def build_repeat_measurement_preset(detail: dict[str, Any]) -> RepeatMeasurementPreset:
    """Bouw een repeat-preset zonder historische meetuitkomst te kopiëren."""
    model = detail["component_model"]
    measurement = detail["measurement"]
    if getattr(measurement, "tool_key", "ESR_CAPACITOR") != "ESR_CAPACITOR":
        raise ValueError(
            "Herhaal meting is voor dit tooltype nog niet geïmplementeerd."
        )

    return RepeatMeasurementPreset(
        source_measurement_id=int(measurement.id),
        nominal_capacitance_value=model.nominal_capacitance_value,
        nominal_capacitance_unit=model.nominal_capacitance_unit,
        tolerance_percent=_symmetric_tolerance_percent(
            model.tolerance_lower_pct,
            model.tolerance_upper_pct,
        ),
        rated_voltage_v=model.rated_voltage_v,
        technology=model.technology,
        manufacturer=model.manufacturer,
        series=model.series,
        measurement_method=_enum_value(measurement.measurement_method),
        instrument_key=measurement.instrument_key,
        frequency_hz=measurement.frequency_hz,
        test_voltage_vrms=measurement.test_voltage_vrms,
        temperature_c=measurement.temperature_c,
    )


def _symmetric_tolerance_percent(
    lower_pct: float | None,
    upper_pct: float | None,
) -> float | None:
    """Geef ±tolerantie terug alleen wanneer storage werkelijk symmetrisch is."""
    if lower_pct is None or upper_pct is None:
        return None
    lower = float(lower_pct)
    upper = float(upper_pct)
    if lower > 0 or upper < 0:
        return None
    if abs(abs(lower) - abs(upper)) > 1e-12:
        return None
    return abs(upper)


def _enum_value(value: Any) -> str | None:
    if value is None:
        return None
    return str(getattr(value, "value", value))
