"""
================================================================================
Module:     tests/test_i18n_history_translations.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Controleert dat de nieuwe historiekteksten in beide locale-bestanden
            aanwezig zijn.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste NL/EN historiek-i18n regressietest.
  v1.1.0 (2026-10-01)  Nieuwe detailteksten in NL en EN afgedekt.
================================================================================
"""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load(language: str) -> dict:
    path = ROOT / "i18n" / "locales" / f"{language}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_history_translations_exist_in_dutch_and_english() -> None:
    for language in ("nl_NL", "en_US"):
        data = _load(language)
        assert data["scherm"]["historiek"]
        assert data["knop"]["verversen"]
        assert data["tool"]["historiek"]
        assert data["tool"]["historiek_omschrijving"]
        assert data["historiek"]["leeg"]
        assert data["historiek"]["aantal"]
        assert data["historiek"]["fout"]
        assert set(data["historiek"]["kolom"]) == {
            "datum_tijd",
            "component",
            "meetmethode",
            "instrument",
            "capaciteit",
            "esr",
            "status",
            "betrouwbaarheid",
        }


def test_history_detail_translations_exist_in_dutch_and_english() -> None:
    required_detail_keys = {
        "fabrikant", "serie", "part_number", "technologie",
        "nominale_capaciteit", "nominale_spanning", "tolerantie",
        "sample_state", "datum_tijd", "meetmethode", "instrument",
        "frequentie", "testspanning", "temperatuur", "spanningsloos",
        "ontladen", "sessie_start", "sessie_einde", "capaciteit",
        "esr", "d", "out_of_range", "open_suspected",
        "short_suspected", "assessed_at", "engine_version",
        "capacitance_status", "capacitance_deviation", "esr_status",
        "esr_factor", "consistency_status", "reliability",
        "final_status", "redenen", "waarschuwingen", "advies",
        "reference_role", "reference_level", "reference_type",
        "reference_value", "reference_frequency",
        "reference_temperature", "value_kind", "source_name",
        "source_document",
    }
    for language in ("nl_NL", "en_US"):
        data = _load(language)
        history = data["historiek"]
        assert history["detail_titel"]
        assert history["detail_kop"]
        assert history["detail_fout"]
        assert history["detail_niet_gevonden"]
        assert history["detail_opmerking_opgeslagen_waarden"]
        assert set(history["detail"]) == required_detail_keys
        assert set(history["sectie"]) == {
            "component", "meetcontext", "meetwaarden",
            "assessment", "referenties", "referentie",
        }
        assert data["algemeen"]["ja"]
        assert data["algemeen"]["nee"]
