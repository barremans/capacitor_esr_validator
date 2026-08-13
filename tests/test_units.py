"""
Modulepad: tests/test_units.py
Doel: Tests voor app/helpers/units.py — decimaalparsing en
      eenheidsconversie (capaciteit, ESR).
Referentie: PROJECT_CONTEXT_capacitor_ESR_validator.md §22,
            testgevallen 1 (470 µF vs 0,47 mF), 2 (mΩ/Ω) en 3
            (komma/punt).
"""

import pytest

from app.helpers.units import converteer_capaciteit, converteer_esr, parse_decimaal


# ---------------------------------------------------------------------------
# parse_decimaal — testgeval 3
# ---------------------------------------------------------------------------
def test_parse_decimaal_met_punt():
    assert parse_decimaal("4.7") == pytest.approx(4.7)


def test_parse_decimaal_met_komma():
    assert parse_decimaal("4,7") == pytest.approx(4.7)


def test_parse_decimaal_met_spaties_rondom():
    assert parse_decimaal("  4,7  ") == pytest.approx(4.7)


def test_parse_decimaal_lege_tekst_geeft_foutmelding():
    with pytest.raises(ValueError):
        parse_decimaal("")


def test_parse_decimaal_none_geeft_foutmelding():
    with pytest.raises(ValueError):
        parse_decimaal(None)


def test_parse_decimaal_ongeldige_tekst_geeft_foutmelding():
    with pytest.raises(ValueError):
        parse_decimaal("abc")


# ---------------------------------------------------------------------------
# converteer_capaciteit — testgeval 1: 470 µF ingevoerd als 0,47 mF
# ---------------------------------------------------------------------------
def test_470_microfarad_gelijk_aan_0_47_millifarad():
    resultaat = converteer_capaciteit(0.47, "mF", "µF")
    assert resultaat == pytest.approx(470.0)


def test_converteer_capaciteit_zelfde_eenheid_is_identiek():
    assert converteer_capaciteit(100.0, "µF", "µF") == pytest.approx(100.0)


def test_converteer_capaciteit_pf_naar_nf():
    assert converteer_capaciteit(1000.0, "pF", "nF") == pytest.approx(1.0)


def test_converteer_capaciteit_onbekende_eenheid_geeft_foutmelding():
    with pytest.raises(ValueError):
        converteer_capaciteit(1.0, "F", "µF")


# ---------------------------------------------------------------------------
# converteer_esr — testgeval 2: ESR in mΩ en Ω
# ---------------------------------------------------------------------------
def test_converteer_esr_milliohm_naar_ohm():
    assert converteer_esr(500.0, "mΩ", "Ω") == pytest.approx(0.5)


def test_converteer_esr_ohm_naar_milliohm():
    assert converteer_esr(0.5, "Ω", "mΩ") == pytest.approx(500.0)


def test_converteer_esr_onbekende_eenheid_geeft_foutmelding():
    with pytest.raises(ValueError):
        converteer_esr(1.0, "kΩ", "Ω")
