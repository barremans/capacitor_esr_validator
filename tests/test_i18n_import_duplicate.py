"""
================================================================================
Module:     tests/test_i18n_import_duplicate.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.2
Datum:      2026-10-07
Auteur:     Bart Bossuyt

Doel:       Controleert dat alle keys onder documentatie.import.duplicate.*
            in beide locales (nl_NL en en_US) aanwezig zijn en dat de
            waarden niet leeg zijn.

Wijzigingen:
  v1.0.0 (2026-10-07)  Eerste versie.
  v1.0.1 (2026-10-07)  test_nl_en_en_verschillen_waar_verwacht: check op
                        status_concept verwijderd ("Concept" is gelijk in
                        NL en EN). status_gearchiveerd toegevoegd.
  v1.0.2 (2026-10-07)  Radio-labels ingekort (cosmetische fix 5D'.2a):
                        optie_behouden, optie_nieuwe_versie en
                        optie_overschrijven zijn nu korte labels. De
                        !=-checks blijven werken; alleen de waarden zijn
                        korter. Geen testinhoud gewijzigd.
================================================================================
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCALES = {
    "nl_NL": PROJECT_ROOT / "i18n" / "locales" / "nl_NL" / "documentation.json",
    "en_US": PROJECT_ROOT / "i18n" / "locales" / "en_US" / "documentation.json",
}

VERWACHTE_KEYS = (
    "titel",
    "match_type_label",
    "match_type_bestand",
    "match_type_url",
    "bestaande_titel",
    "bestaande_status",
    "bestaande_datum",
    "bestaande_url",
    "bestaande_bestand",
    "status_concept",
    "status_actief",
    "status_gearchiveerd",
    "optie_behouden",
    "optie_nieuwe_versie",
    "optie_overschrijven",
    "detail_behouden",
    "detail_nieuwe_versie",
    "detail_overschrijven",
    "doorgaan",
    "annuleren",
)


def _laad(taal: str) -> dict:
    pad = LOCALES[taal]
    with pad.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.mark.parametrize("taal", list(LOCALES.keys()))
def test_duplicate_blok_aanwezig(taal):
    data = _laad(taal)
    assert "documentatie" in data
    assert "import" in data["documentatie"]
    assert "duplicate" in data["documentatie"]["import"]


@pytest.mark.parametrize("taal", list(LOCALES.keys()))
@pytest.mark.parametrize("key", VERWACHTE_KEYS)
def test_duplicate_key_aanwezig_en_niet_leeg(taal, key):
    data = _laad(taal)
    blok = data["documentatie"]["import"]["duplicate"]
    assert key in blok, f"key '{key}' ontbreekt in {taal}"
    waarde = blok[key]
    assert isinstance(waarde, str) and waarde.strip(), (
        f"key '{key}' in {taal} is leeg of geen string"
    )


def test_nl_en_en_verschillen_waar_verwacht():
    """Controleer dat een paar duidelijke sleutels echt vertaald zijn.

    Let op: 'Concept' is in het Nederlands en het Engels hetzelfde woord
    (leenwoord, gangbaar in softwarecontexten). Daarom wordt die key hier
    NIET als verschil-check gebruikt. status_actief (NL: Actief, EN:
    Active) is wel een echt verschil.
    """
    nl = _laad("nl_NL")["documentatie"]["import"]["duplicate"]
    en = _laad("en_US")["documentatie"]["import"]["duplicate"]

    # Titel
    assert nl["titel"] != en["titel"]
    # Knoppen
    assert nl["doorgaan"] != en["doorgaan"]
    assert nl["annuleren"] != en["annuleren"]
    # Statuslabels — status_actief is een echt vertaalverschil
    assert nl["status_actief"] != en["status_actief"]
    # Statuslabels — status_gearchiveerd is ook een echt verschil
    assert nl["status_gearchiveerd"] != en["status_gearchiveerd"]
    # Radio-labels — kort, maar nog steeds vertaald
    assert nl["optie_behouden"] != en["optie_behouden"]
    assert nl["optie_nieuwe_versie"] != en["optie_nieuwe_versie"]
    assert nl["optie_overschrijven"] != en["optie_overschrijven"]


def test_match_type_url_is_gelijk_in_beide_talen():
    """URL is een technische term en blijft gelijk in NL en EN."""
    nl = _laad("nl_NL")["documentatie"]["import"]["duplicate"]
    en = _laad("en_US")["documentatie"]["import"]["duplicate"]
    assert nl["match_type_url"] == en["match_type_url"] == "URL"


def test_status_concept_is_gelijk_in_beide_talen():
    """Concept is een leenwoord en is bewust gelijk in NL en EN."""
    nl = _laad("nl_NL")["documentatie"]["import"]["duplicate"]
    en = _laad("en_US")["documentatie"]["import"]["duplicate"]
    assert nl["status_concept"] == en["status_concept"] == "Concept"


def test_radio_labels_zijn_kort():
    """Bewijs dat de radio-labels kort zijn (geen lange uitleg meer)."""
    nl = _laad("nl_NL")["documentatie"]["import"]["duplicate"]
    en = _laad("en_US")["documentatie"]["import"]["duplicate"]

    # De labels mogen geen opsommingsteken of "—" meer bevatten.
    for taal, blok in (("nl_NL", nl), ("en_US", en)):
        for key in ("optie_behouden", "optie_nieuwe_versie", "optie_overschrijven"):
            waarde = blok[key]
            assert "—" not in waarde, (
                f"{taal}.{key} bevat nog een '—': {waarde!r}"
            )
            assert " - " not in waarde, (
                f"{taal}.{key} bevat nog een ' - ' scheiding: {waarde!r}"
            )
            # Kort: max 30 tekens
            assert len(waarde) <= 30, (
                f"{taal}.{key} is te lang ({len(waarde)} tekens): {waarde!r}"
            )