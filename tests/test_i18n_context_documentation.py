"""
================================================================================
Module:     tests/test_i18n_context_documentation.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-03
Auteur:     Bart Bossuyt
================================================================================
"""

from app.helpers.i18n import vertaal, wis_cache


def test_context_documentation_button_translations():
    wis_cache()
    assert vertaal("knop.meetinstructies", taal="nl_NL") == "Meetinstructies"
    assert vertaal("knop.meetinstructies", taal="en_US") == "Measurement instructions"
    assert vertaal("knop.aanbevolen_instructie", taal="nl_NL", titel="X") == "Aanbevolen: X"
    assert vertaal("knop.aanbevolen_instructie", taal="en_US", titel="X") == "Recommended: X"
