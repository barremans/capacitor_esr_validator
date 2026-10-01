"""
================================================================================
Module:     tests/test_repeat_measurement_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Regressietests voor veilige voorbereiding van "Herhaal meting".

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste tests: alleen component/meetcontext wordt
                        overgenomen; symmetrische tolerantie wordt veilig hersteld.
================================================================================
"""

from types import SimpleNamespace

from app.services.repeat_measurement_service import build_repeat_measurement_preset


def _detail(*, lower=-20.0, upper=20.0):
    return {
        "component_model": SimpleNamespace(
            nominal_capacitance_value=470.0,
            nominal_capacitance_unit="µF",
            tolerance_lower_pct=lower,
            tolerance_upper_pct=upper,
            rated_voltage_v=25.0,
            technology="Aluminium elektrolytisch",
            manufacturer="AIC",
            series="HU",
        ),
        "measurement": SimpleNamespace(
            id=42,
            measurement_method=SimpleNamespace(value="EX_SITU"),
            instrument_key="LCR-ST1",
            frequency_hz=1000.0,
            test_voltage_vrms=0.6,
            temperature_c=20.0,
            capacitance_f=0.000465,
            esr_ohm=0.12,
            dissipation_factor_d=0.08,
            out_of_range=False,
        ),
        "assessment_snapshots": [SimpleNamespace(final_status="waarschijnlijk_goed")],
        "reference_snapshots_by_assessment_id": {1: [SimpleNamespace(source_name="datasheet")]},
    }


def test_repeat_preset_contains_only_component_and_measurement_context() -> None:
    preset = build_repeat_measurement_preset(_detail())

    assert preset.source_measurement_id == 42
    assert preset.nominal_capacitance_value == 470.0
    assert preset.nominal_capacitance_unit == "µF"
    assert preset.tolerance_percent == 20.0
    assert preset.rated_voltage_v == 25.0
    assert preset.technology == "Aluminium elektrolytisch"
    assert preset.manufacturer == "AIC"
    assert preset.series == "HU"
    assert preset.measurement_method == "EX_SITU"
    assert preset.instrument_key == "LCR-ST1"
    assert preset.frequency_hz == 1000.0
    assert preset.test_voltage_vrms == 0.6
    assert preset.temperature_c == 20.0

    # De DTO heeft bewust geen velden voor oude meetwaarden of assessment.
    assert not hasattr(preset, "capacitance_f")
    assert not hasattr(preset, "esr_ohm")
    assert not hasattr(preset, "final_status")
    assert not hasattr(preset, "reference")
    assert not hasattr(preset, "safety_confirmed")


def test_asymmetric_tolerance_is_not_silently_rewritten_as_symmetric() -> None:
    preset = build_repeat_measurement_preset(_detail(lower=-10.0, upper=30.0))
    assert preset.tolerance_percent is None


def test_missing_tolerance_remains_unknown() -> None:
    preset = build_repeat_measurement_preset(_detail(lower=None, upper=None))
    assert preset.tolerance_percent is None
