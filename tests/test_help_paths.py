"""
================================================================================
Module:     tests/test_help_paths.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-06
Auteur:     Bart Bossuyt

Doel:       Regressietests voor GUI-onafhankelijke help-padresolutie
            (Fase 4H). Dekt de fallback-keten, meertaligheid en
            foutmelding wanneer niets bestaat.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie.
================================================================================
"""

from pathlib import Path

import pytest

from app.helpers.help_paths import (
    STANDAARD_FALLBACK_TAAL,
    help_pad_bestaat_voor_taal,
    help_pad_voor_taal,
)


def _maak_docs(tmp_path: Path) -> Path:
    """Mini docs/-structuur voor tests."""
    docs = tmp_path / "docs"
    (docs / "help").mkdir(parents=True)
    return docs


def test_kies_taalbestand_wanneer_aanwezig(tmp_path):
    docs = _maak_docs(tmp_path)
    (docs / "help" / "en_US.md").write_text("# EN", encoding="utf-8")
    (docs / "help" / "nl_NL.md").write_text("# NL", encoding="utf-8")

    pad = help_pad_voor_taal("en_US", docs_root=docs)
    assert pad == docs / "help" / "en_US.md"
    assert pad.read_text(encoding="utf-8") == "# EN"


def test_valt_terug_op_nl_wanneer_taal_ontbreekt(tmp_path):
    docs = _maak_docs(tmp_path)
    (docs / "help" / "nl_NL.md").write_text("# NL", encoding="utf-8")

    pad = help_pad_voor_taal("de_DE", docs_root=docs)
    assert pad == docs / "help" / "nl_NL.md"


def test_valt_terug_op_legacy_help_md(tmp_path):
    docs = _maak_docs(tmp_path)
    (docs / "help.md").write_text("# Legacy", encoding="utf-8")

    pad = help_pad_voor_taal("fr_FR", docs_root=docs)
    assert pad == docs / "help.md"


def test_gooit_file_not_found_wanneer_niets_bestaat(tmp_path):
    docs = _maak_docs(tmp_path)

    with pytest.raises(FileNotFoundError) as excinfo:
        help_pad_voor_taal("en_US", docs_root=docs)

    boodschap = str(excinfo.value)
    assert "en_US" in boodschap
    assert "nl_NL" in boodschap
    assert "help.md" in boodschap


def test_bestaat_voor_taal_true_en_false(tmp_path):
    docs = _maak_docs(tmp_path)
    (docs / "help" / "en_US.md").write_text("# EN", encoding="utf-8")

    assert help_pad_bestaat_voor_taal("en_US", docs_root=docs) is True
    # nl_NL ontbreekt, maar legacy ontbreekt ook => False
    assert help_pad_bestaat_voor_taal("nl_NL", docs_root=docs) is False


def test_taalonafhankelijk_extra_taal_toevoegen(tmp_path):
    """Een nieuwe taal werkt zonder codewijziging."""
    docs = _maak_docs(tmp_path)
    (docs / "help" / "fr_FR.md").write_text("# FR", encoding="utf-8")
    (docs / "help" / "nl_NL.md").write_text("# NL", encoding="utf-8")

    pad = help_pad_voor_taal("fr_FR", docs_root=docs)
    assert pad.name == "fr_FR.md"


def test_lege_taalcode_gebruikt_fallback(tmp_path):
    docs = _maak_docs(tmp_path)
    (docs / "help" / "nl_NL.md").write_text("# NL", encoding="utf-8")

    pad = help_pad_voor_taal("", docs_root=docs)
    assert pad == docs / "help" / "nl_NL.md"


def test_standaard_fallback_taal_is_nl():
    assert STANDAARD_FALLBACK_TAAL == "nl_NL"


def test_custom_fallback_taal(tmp_path):
    docs = _maak_docs(tmp_path)
    (docs / "help" / "en_US.md").write_text("# EN", encoding="utf-8")

    pad = help_pad_voor_taal("de_DE", docs_root=docs, fallback_taal="en_US")
    assert pad == docs / "help" / "en_US.md"


def test_echte_projectdocs_bevatten_nl_en_en():
    """Bewaakt dat de productie-help voor NL en EN effectief bestaat."""
    from app.helpers.help_paths import _docs_root_default

    docs = _docs_root_default()
    nl = docs / "help" / "nl_NL.md"
    en = docs / "help" / "en_US.md"

    assert nl.is_file(), f"Ontbreekt: {nl}"
    assert en.is_file(), f"Ontbreekt: {en}"