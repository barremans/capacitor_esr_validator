"""
================================================================================
Module:     tests/test_instrument_profiles.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.0.0
Datum:      2026-09-26
Auteur:     Ontwikkelaar

Doel:       Test de toestelprofielen en toegelaten frequenties/testspanningen.

Wijzigingen:
  v1.0.0 (2026-09-26)  Eerste versie met LCR-ST1.
================================================================================
"""

import pytest

from app.config.instrument_profiles import get_instrument_profiel


def test_lcr_st1_frequenties():
    profiel = get_instrument_profiel("LCR_ST1")
    assert profiel.frequenties_hz == (100, 1_000, 10_000)


@pytest.mark.parametrize("voltage", [0.3, 0.6])
def test_lcr_st1_testspanningen(voltage):
    profiel = get_instrument_profiel("LCR_ST1")
    assert voltage in profiel.testspanningen_vrms


def test_onbekend_profiel_geeft_fout():
    with pytest.raises(ValueError):
        get_instrument_profiel("BESTAAT_NIET")
