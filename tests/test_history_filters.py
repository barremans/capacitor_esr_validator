"""
================================================================================
Module:     tests/test_history_filters.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de GUI-onafhankelijke historiekfilterbuilder.
Wijzigingen:
  v1.1.0 (2026-10-01)  tool_key-filtertest toegevoegd voor multitool-historiek.
================================================================================
"""

from app.helpers.history_filters import build_history_filters


def test_empty_filter_inputs_produce_no_filters() -> None:
    assert build_history_filters() == {}


def test_text_filters_are_trimmed_and_choices_preserved() -> None:
    assert build_history_filters(
        manufacturer="  Panasonic ",
        series=" FR ",
        measurement_method="EX_SITU",
        instrument_key=" LCR-ST1 ",
        frequency_hz=1000,
        final_status="waarschijnlijk_goed",
        reliability_level="hoog",
    ) == {
        "manufacturer": "Panasonic",
        "series": "FR",
        "measurement_method": "EX_SITU",
        "instrument_key": "LCR-ST1",
        "frequency_hz": 1000.0,
        "final_status": "waarschijnlijk_goed",
        "reliability_level": "hoog",
    }


def test_blank_text_does_not_create_exact_match_filter() -> None:
    assert build_history_filters(
        manufacturer="   ",
        series="",
        instrument_key="  ",
        measurement_method="ONE_LEG",
    ) == {"measurement_method": "ONE_LEG"}


def test_tool_filter_is_preserved() -> None:
    assert build_history_filters(tool_key=" ESR_CAPACITOR ") == {
        "tool_key": "ESR_CAPACITOR"
    }
