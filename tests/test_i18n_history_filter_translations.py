"""
================================================================================
Module:     tests/test_i18n_history_filter_translations.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Bewaakt de NL/EN vertalingen voor de historiekfilterbalk.
Wijzigingen:
  v1.1.0 (2026-10-01)  NL/EN sleutels voor Tool/Testtype toegevoegd.
================================================================================
"""

import json
from pathlib import Path


def _load(language: str) -> dict:
    path = Path(__file__).parents[1] / "i18n" / "locales" / f"{language}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_history_filter_translations_exist_in_both_languages() -> None:
    for language in ("nl_NL", "en_US"):
        section = _load(language)["historiek"]["filter"]
        for key in (
            "titel", "fabrikant", "serie", "meetmethode", "instrument",
            "frequentie", "status", "betrouwbaarheid", "alle", "toepassen",
            "wissen", "exact_placeholder",
        ):
            assert section[key]


def test_multitool_history_translation_keys_exist() -> None:
    for language in ("nl_NL", "en_US"):
        data = _load(language)
        assert data["historiek"]["filter"]["tool"]
        assert data["historiek"]["kolom"]["tool"]
        assert data["historiek"]["detail"]["tool"]
        assert data["tool_type"]["ESR_CAPACITOR"]
