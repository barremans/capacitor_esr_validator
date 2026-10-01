"""
================================================================================
Module:     tests/test_history_formatting.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Regressietests voor compacte historiekweergave van C, ESR en
            componentidentiteit.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste formatteringstests.
  v1.1.0 (2026-10-01)  Detailhelpers voor JSON, booleans en getallen getest.
================================================================================
"""

from app.helpers.history_formatting import (
    component_label,
    format_capacitance_f,
    format_esr_ohm,
    decode_json_list,
    format_bool,
    format_optional_number,
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
