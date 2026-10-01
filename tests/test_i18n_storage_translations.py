"""
================================================================================
Module:     tests/test_i18n_storage_translations.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.0.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de NL/EN GUI-vertalingen van de lokale
            opslagactie 'Meting opslaan'.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste versie.
================================================================================
"""

from app.helpers.i18n import vertaal, wis_cache


def test_nederlandse_opslagvertalingen() -> None:
    wis_cache()
    assert vertaal("knop.meting_opslaan", taal="nl_NL") == "Meting opslaan"
    assert vertaal("opslag.meting_opgeslagen_titel", taal="nl_NL") == "Meting opgeslagen"
    assert (
        vertaal("opslag.meting_opgeslagen_tekst", taal="nl_NL", measurement_id=42)
        == "Meting 42 is opgeslagen in de lokale historiek."
    )


def test_engelse_opslagvertalingen() -> None:
    wis_cache()
    assert vertaal("knop.meting_opslaan", taal="en_US") == "Save measurement"
    assert vertaal("opslag.meting_opgeslagen_titel", taal="en_US") == "Measurement saved"
    assert (
        vertaal("opslag.meting_opgeslagen_tekst", taal="en_US", measurement_id=42)
        == "Measurement 42 was saved to local history."
    )


def test_opslagfoutteksten_worden_geinterpoleerd() -> None:
    wis_cache()
    assert (
        vertaal("opslag.meting_opslaan_fout_tekst", taal="nl_NL", bericht="test")
        == "De meting kon niet worden opgeslagen: test"
    )
    assert (
        vertaal("opslag.meting_opslaan_fout_tekst", taal="en_US", bericht="test")
        == "The measurement could not be saved: test"
    )
