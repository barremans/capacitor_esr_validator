"""
================================================================================
Module:     tests/test_help_paths.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-15
Auteur:     Bart Bossuyt

Doel:       Regressietests voor GUI-onafhankelijke help-padresolutie
            (Fase 4H). Dekt de fallback-keten, meertaligheid en
            foutmelding wanneer niets bestaat.

            Sinds v1.1.0 ook voor changelog_pad_voor_taal() — dezelfde
            fallback-keten, maar met docs/changelog/ als submap en
            docs/changelog.md als legacy (fase 9H-afronding).

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie.
  v1.1.0 (2026-10-15)  Fase 9H-afronding: tests voor changelog-resolutie
                        via dezelfde resolver.
================================================================================
"""

from pathlib import Path

import pytest

from app.helpers.help_paths import (
    STANDAARD_FALLBACK_TAAL,
    changelog_pad_bestaat_voor_taal,
    changelog_pad_voor_taal,
    help_pad_bestaat_voor_taal,
    help_pad_voor_taal,
)


def _maak_docs(tmp_path: Path) -> Path:
    """Mini docs/-structuur voor tests."""
    docs = tmp_path / "docs"
    (docs / "help").mkdir(parents=True)
    return docs


# ============================================================================
# Help-resolutie (v1.0.0)
# ============================================================================

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


# ============================================================================
# v1.1.0 — changelog-resolutie (fase 9H-afronding)
# ============================================================================

def _maak_docs_met_changelog(tmp_path: Path) -> Path:
    docs = tmp_path / "docs"
    (docs / "changelog").mkdir(parents=True)
    return docs


def test_changelog_kies_taalbestand_wanneer_aanwezig(tmp_path):
    docs = _maak_docs_met_changelog(tmp_path)
    (docs / "changelog" / "en_US.md").write_text("# EN", encoding="utf-8")
    (docs / "changelog" / "nl_NL.md").write_text("# NL", encoding="utf-8")

    pad = changelog_pad_voor_taal("en_US", docs_root=docs)
    assert pad == docs / "changelog" / "en_US.md"
    assert pad.read_text(encoding="utf-8") == "# EN"


def test_changelog_valt_terug_op_nl(tmp_path):
    docs = _maak_docs_met_changelog(tmp_path)
    (docs / "changelog" / "nl_NL.md").write_text("# NL", encoding="utf-8")

    pad = changelog_pad_voor_taal("de_DE", docs_root=docs)
    assert pad == docs / "changelog" / "nl_NL.md"


def test_changelog_valt_terug_op_legacy(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "changelog.md").write_text("# Legacy", encoding="utf-8")

    pad = changelog_pad_voor_taal("fr_FR", docs_root=docs)
    assert pad == docs / "changelog.md"


def test_changelog_gooit_file_not_found_wanneer_niets_bestaat(tmp_path):
    docs = _maak_docs_met_changelog(tmp_path)

    with pytest.raises(FileNotFoundError):
        changelog_pad_voor_taal("en_US", docs_root=docs)


def test_changelog_bestaat_voor_taal_true_en_false(tmp_path):
    docs = _maak_docs_met_changelog(tmp_path)
    (docs / "changelog" / "en_US.md").write_text("# EN", encoding="utf-8")

    assert changelog_pad_bestaat_voor_taal("en_US", docs_root=docs) is True
    assert changelog_pad_bestaat_voor_taal("nl_NL", docs_root=docs) is False


def test_changelog_en_help_gebruiken_aparte_submappen(tmp_path):
    """De changelog-resolver mag nooit per ongeluk de help-submap pakken."""
    docs = tmp_path / "docs"
    (docs / "help").mkdir(parents=True)
    (docs / "changelog").mkdir(parents=True)
    (docs / "help" / "nl_NL.md").write_text("# Help NL", encoding="utf-8")
    (docs / "changelog" / "nl_NL.md").write_text(
        "# Changelog NL", encoding="utf-8"
    )

    help_pad = help_pad_voor_taal("nl_NL", docs_root=docs)
    changelog_pad = changelog_pad_voor_taal("nl_NL", docs_root=docs)

    assert help_pad == docs / "help" / "nl_NL.md"
    assert changelog_pad == docs / "changelog" / "nl_NL.md"


def test_echte_projectchangelog_bevat_nl_en_en():
    """Bewaakt dat de productie-changelog voor NL en EN effectief bestaat."""
    from app.helpers.help_paths import _docs_root_default

    docs = _docs_root_default()
    nl = changelog_pad_voor_taal("nl_NL", docs_root=docs)
    en = changelog_pad_voor_taal("en_US", docs_root=docs)

    assert nl.is_file(), f"Ontbreekt: {nl}"
    assert en.is_file(), f"Ontbreekt: {en}"