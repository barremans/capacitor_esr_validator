"""
================================================================================
Module:     tests/test_i18n_repeat_measurement_translations.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Controleert NL/EN vertalingen voor "Herhaal meting".

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste vertaalcontract voor knop, foutmelding en banner.
================================================================================
"""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "i18n" / "locales"


def _load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def test_repeat_measurement_translations_exist_in_both_languages() -> None:
    nl = _load("nl_NL.json")
    en = _load("en_US.json")

    for data in (nl, en):
        assert data["knop"]["herhaal_meting"]
        assert "{bericht}" in data["historiek"]["herhalen_fout"]
        assert "{measurement_id}" in data["herhalen"]["banner"]


def test_repeat_measurement_labels_are_language_specific() -> None:
    nl = _load("nl_NL.json")
    en = _load("en_US.json")

    assert nl["knop"]["herhaal_meting"] == "Herhaal meting"
    assert en["knop"]["herhaal_meting"] == "Repeat measurement"
