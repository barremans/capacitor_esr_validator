"""
================================================================================
Module:     tests/test_history_formatting.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.2.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Regressietests voor centrale historiekformattering, inclusief
            tool-specifieke meetwaardesamenvatting en uniforme meetmethode.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste formatteringstests.
  v1.1.0 (2026-10-01)  Detailhelpers voor JSON, booleans en getallen getest.
  v1.2.0 (2026-10-01)  Multitool meetwaardesamenvatting en uniforme
                        meetmethode-vertaalsleutels getest.
================================================================================
"""

from types import SimpleNamespace

from app.helpers.history_formatting import (
    component_label,
    format_capacitance_f,
    format_esr_ohm,
    decode_json_list,
    format_bool,
    format_optional_number,
    format_measurement_values,
    measurement_method_translation_key,
)


def test_capacitance_history_formatting() -> None:
    assert format_capacitance_f(None) == "—"
    assert format_capacitance_f(470e-6) == "470 µF"
    assert format_capacitance_f(2.2e-9) == "2.2 nF"


def test_esr_history_formatting() -> None:
    assert format_esr_ohm(None) == "—"
    assert format_esr_ohm(0.047) == "47 mΩ"
    assert format_esr_ohm(2.5) == "2.5 Ω"


def test_component_label_uses_available_identity_fields() -> None:
    assert component_label(
        {"manufacturer": "AIC", "series": "HU", "part_number": "HU2W680"}
    ) == "AIC HU HU2W680"
    assert component_label(
        {"manufacturer": None, "series": "", "part_number": None}
    ) == "—"


def test_detail_formatting_helpers() -> None:
    assert format_bool(True, "Ja", "Nee") == "Ja"
    assert format_bool(False, "Ja", "Nee") == "Nee"
    assert format_bool(None, "Ja", "Nee") == "—"
    assert format_optional_number(1000.0, suffix=" Hz") == "1000 Hz"
    assert format_optional_number(None, suffix=" Hz") == "—"
    assert decode_json_list('["een","twee"]') == ("een", "twee")
    assert decode_json_list(None) == ()
    assert decode_json_list('{broken') == ('{broken',)


def test_esr_capacitor_values_are_combined_in_one_multitool_column() -> None:
    measurement = SimpleNamespace(capacitance_f=465e-6, esr_ohm=0.2)
    assert format_measurement_values("ESR_CAPACITOR", measurement) == "465 µF · 200 mΩ"

    out_of_range = SimpleNamespace(capacitance_f=None, esr_ohm=None)
    assert format_measurement_values("ESR_CAPACITOR", out_of_range) == "—"
    assert format_measurement_values("RESISTOR", measurement) == "—"


def test_measurement_method_labels_use_one_public_translation_set() -> None:
    assert measurement_method_translation_key("EX_SITU") == "meetmethode.ex_situ"
    assert measurement_method_translation_key("ONE_LEG") == "meetmethode.one_leg"
    assert measurement_method_translation_key("IN_CIRCUIT") == "meetmethode.in_circuit"
