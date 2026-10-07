"""
================================================================================
Module:     tests/test_documentation_import_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.1
Datum:      2026-10-07
Auteur:     Bart Bossuyt

Doel:       Regressietests voor ImportService: registratie, statusmachine,
            JSON-persistentie, corrupte catalogus, schema_version,
            atomair schrijven, duplicate-detectie, replace_source en de
            beste-match-prioriteit (ACTIEF > CONCEPT > GEARCHIVEERD).

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie.
  v1.0.1 (2026-10-06)  Qt-onafhankelijkheid niet meer via sys.modules-
                        manipulatie. Vervangen door statische broncheck.
  v1.1.0 (2026-10-07)  Tests voor find_by_file_hash, find_by_source_url en
                        replace_source (fase 5D'.2a).
  v1.1.1 (2026-10-07)  Tests voor beste-match-prioriteit: ACTIEF >
                        CONCEPT > GEARCHIVEERD, dan meest recente. Lost
                        bug op waarbij Overschrijven de gearchiveerde bron
                        koos in plaats van de actieve/concept-bron.
================================================================================
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.documentation.import_models import (
    ImportSourceType,
    ImportStatus,
    ImportValidationError,
)
from app.documentation.import_service import (
    CATALOG_SCHEMA_VERSION,
    ImportService,
)


@pytest.fixture()
def service(tmp_path):
    return ImportService(catalog_path=tmp_path / "imported_catalog.json")


def _lees_catalogus(pad):
    return json.loads(pad.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- registratie

def test_register_pdf_maakt_concept(service):
    result = service.register_pdf(
        title="FR-serie", original_filename="fr.pdf"
    )
    assert result.changed is True
    assert result.source.source_type is ImportSourceType.PDF
    assert result.source.status is ImportStatus.CONCEPT
    assert result.source.original_filename == "fr.pdf"


def test_register_url_maakt_concept(service):
    result = service.register_url(
        title="Fabrikant", source_url="https://example.com"
    )
    assert result.source.source_type is ImportSourceType.URL
    assert result.source.status is ImportStatus.CONCEPT
    assert result.source.source_url == "https://example.com"


def test_register_pdf_zonder_titel_faalt(service):
    with pytest.raises(ImportValidationError):
        service.register_pdf(title="", original_filename="x.pdf")


def test_register_url_zonder_url_faalt(service):
    with pytest.raises(ImportValidationError):
        service.register_url(title="x", source_url="")


# ---------------------------------------------------------------- persistentie

def test_catalogus_wordt_aangemaakt_met_schema_version(tmp_path):
    pad = tmp_path / "imported_catalog.json"
    service = ImportService(catalog_path=pad)
    service.register_pdf(title="A", original_filename="a.pdf")
    data = _lees_catalogus(pad)
    assert data["schema_version"] == CATALOG_SCHEMA_VERSION
    assert isinstance(data["sources"], list)
    assert len(data["sources"]) == 1


def test_meerdere_registraties_blijven_bewaard(tmp_path):
    pad = tmp_path / "imported_catalog.json"
    service = ImportService(catalog_path=pad)
    service.register_pdf(title="A", original_filename="a.pdf")
    service.register_url(title="B", source_url="https://example.com")
    items = service.list_sources()
    assert len(items) == 2
    assert {i.source_type for i in items} == {
        ImportSourceType.PDF,
        ImportSourceType.URL,
    }


def test_ontbrekend_bestand_geeft_lege_lijst(tmp_path):
    service = ImportService(catalog_path=tmp_path / "bestaat_niet.json")
    assert service.list_sources() == []


def test_corrupte_json_faalt_zonder_reset(tmp_path):
    pad = tmp_path / "imported_catalog.json"
    pad.write_text("{ dit is geen geldige json", encoding="utf-8")
    service = ImportService(catalog_path=pad)
    with pytest.raises(ImportValidationError):
        service.list_sources()
    # Bestand mag niet stil zijn gereset
    assert pad.read_text(encoding="utf-8").startswith("{ dit is geen geldige")


def test_verkeerde_schema_version_faalt(tmp_path):
    pad = tmp_path / "imported_catalog.json"
    pad.write_text(
        json.dumps({"schema_version": 999, "sources": []}),
        encoding="utf-8",
    )
    service = ImportService(catalog_path=pad)
    with pytest.raises(ImportValidationError):
        service.list_sources()


def test_sources_moet_lijst_zijn(tmp_path):
    pad = tmp_path / "imported_catalog.json"
    pad.write_text(
        json.dumps({"schema_version": CATALOG_SCHEMA_VERSION, "sources": {}}),
        encoding="utf-8",
    )
    service = ImportService(catalog_path=pad)
    with pytest.raises(ImportValidationError):
        service.list_sources()


# ---------------------------------------------------------------- get

def test_get_onbekende_id_faalt(service):
    with pytest.raises(ImportValidationError):
        service.get("bestaat-niet")


def test_get_bestaande_id(service):
    result = service.register_pdf(title="A", original_filename="a.pdf")
    hersteld = service.get(result.source.source_id)
    assert hersteld == result.source


# ---------------------------------------------------------------- statusmachine

def test_status_concept_naar_actief(service):
    result = service.register_pdf(title="A", original_filename="a.pdf")
    updated = service.set_status(result.source.source_id, ImportStatus.ACTIEF)
    assert updated.source.status is ImportStatus.ACTIEF


def test_status_ongeldige_overgang_faalt(service):
    result = service.register_pdf(title="A", original_filename="a.pdf")
    service.set_status(result.source.source_id, ImportStatus.GEARCHIVEERD)
    with pytest.raises(ImportValidationError):
        service.set_status(result.source.source_id, ImportStatus.ACTIEF)


def test_revoke_gaat_terug_naar_concept_en_behoudt_bron(service):
    result = service.register_pdf(title="A", original_filename="a.pdf")
    service.set_status(result.source.source_id, ImportStatus.ACTIEF)
    terug = service.revoke(result.source.source_id)
    assert terug.source.status is ImportStatus.CONCEPT
    # Bron blijft bestaan
    assert service.get(result.source.source_id).status is ImportStatus.CONCEPT


def test_archive_behoudt_bron(service):
    result = service.register_pdf(title="A", original_filename="a.pdf")
    gearchiveerd = service.archive(result.source.source_id)
    assert gearchiveerd.source.status is ImportStatus.GEARCHIVEERD
    # Nog steeds opvraagbaar
    assert service.get(result.source.source_id).status is ImportStatus.GEARCHIVEERD


def test_set_status_onbekende_id_faalt(service):
    with pytest.raises(ImportValidationError):
        service.set_status("bestaat-niet", ImportStatus.ACTIEF)


# ---------------------------------------------------------------- opnieuw importeren

def test_opnieuw_importeren_geeft_nieuwe_id_en_behoudt_oude(service):
    eerste = service.register_pdf(title="A", original_filename="a.pdf")
    tweede = service.register_pdf(title="A", original_filename="a.pdf")
    assert eerste.source.source_id != tweede.source.source_id
    items = service.list_sources()
    assert len(items) == 2


# ---------------------------------------------------------------- list filter

def test_list_sources_filter_op_status(service):
    a = service.register_pdf(title="A", original_filename="a.pdf")
    b = service.register_pdf(title="B", original_filename="b.pdf")
    service.set_status(b.source.source_id, ImportStatus.ACTIEF)

    concepten = service.list_sources(status=ImportStatus.CONCEPT)
    actief = service.list_sources(status=ImportStatus.ACTIEF)
    assert [s.source_id for s in concepten] == [a.source.source_id]
    assert [s.source_id for s in actief] == [b.source.source_id]


def test_list_sources_ongeldige_status_faalt(service):
    with pytest.raises(ImportValidationError):
        service.list_sources(status="concept")  # type: ignore[arg-type]


# ---------------------------------------------------------------- geen Qt

def test_import_service_en_models_bevatten_geen_qt_import():
    """Bewijs dat de import-laag GUI-onafhankelijk is."""
    project_root = Path(__file__).resolve().parents[1]
    te_controleren = [
        project_root / "app" / "documentation" / "import_service.py",
        project_root / "app" / "documentation" / "import_models.py",
    ]
    verboden = ("PySide6", "PyQt5", "PyQt6", "PyQt")
    for pad in te_controleren:
        tekst = pad.read_text(encoding="utf-8")
        for token in verboden:
            assert token not in tekst, (
                f"{pad.name} bevat verboden Qt-import: {token}"
            )


# ============================================================================
# v1.1.0 — find_by_file_hash, find_by_source_url, replace_source
# ============================================================================

# ---------------------------------------------------------------- find_by_file_hash

def test_find_by_file_hash_geen_match(service):
    service.register_pdf(
        title="A", original_filename="a.pdf", file_hash="abc123"
    )
    assert service.find_by_file_hash("def456") is None


def test_find_by_file_hash_match(service):
    r = service.register_pdf(
        title="A", original_filename="a.pdf", file_hash="abc123"
    )
    gevonden = service.find_by_file_hash("abc123")
    assert gevonden is not None
    assert gevonden.source_id == r.source.source_id


def test_find_by_file_hash_case_insensitive(service):
    service.register_pdf(
        title="A", original_filename="a.pdf", file_hash="ABC123"
    )
    assert service.find_by_file_hash("abc123") is not None
    assert service.find_by_file_hash("ABC123") is not None


def test_find_by_file_hash_strip_whitespace(service):
    service.register_pdf(
        title="A", original_filename="a.pdf", file_hash="abc123"
    )
    assert service.find_by_file_hash("  abc123  ") is not None


def test_find_by_file_hash_lege_hash_geeft_none(service):
    service.register_pdf(
        title="A", original_filename="a.pdf", file_hash="abc123"
    )
    assert service.find_by_file_hash("") is None
    assert service.find_by_file_hash("   ") is None


def test_find_by_file_hash_gearchiveerd_match(service):
    r = service.register_pdf(
        title="A", original_filename="a.pdf", file_hash="abc123"
    )
    service.archive(r.source.source_id)
    gevonden = service.find_by_file_hash("abc123")
    assert gevonden is not None
    assert gevonden.status is ImportStatus.GEARCHIVEERD


# ---------------------------------------------------------------- find_by_source_url

def test_find_by_source_url_geen_match(service):
    service.register_url(title="A", source_url="https://example.com")
    assert service.find_by_source_url("https://other.com") is None


def test_find_by_source_url_match(service):
    r = service.register_url(title="A", source_url="https://example.com")
    gevonden = service.find_by_source_url("https://example.com")
    assert gevonden is not None
    assert gevonden.source_id == r.source.source_id


def test_find_by_source_url_trailing_slash_genegeerd(service):
    service.register_url(title="A", source_url="https://example.com")
    assert service.find_by_source_url("https://example.com/") is not None


def test_find_by_source_url_lege_url_geeft_none(service):
    service.register_url(title="A", source_url="https://example.com")
    assert service.find_by_source_url("") is None
    assert service.find_by_source_url("   ") is None


def test_find_by_source_url_gearchiveerd_match(service):
    r = service.register_url(title="A", source_url="https://example.com")
    service.archive(r.source.source_id)
    gevonden = service.find_by_source_url("https://example.com")
    assert gevonden is not None
    assert gevonden.status is ImportStatus.GEARCHIVEERD


# ---------------------------------------------------------------- replace_source

def test_replace_source_wijzigt_velden(service):
    r = service.register_pdf(
        title="Oud", original_filename="oud.pdf", file_hash="hash_oud"
    )
    result = service.replace_source(
        r.source.source_id,
        title="Nieuw",
        file_hash="hash_nieuw",
        original_filename="nieuw.pdf",
        notes="nieuwe notitie",
    )
    assert result.changed is True
    assert result.source.source_id == r.source.source_id
    assert result.source.title == "Nieuw"
    assert result.source.file_hash == "hash_nieuw"
    assert result.source.original_filename == "nieuw.pdf"
    assert result.source.notes == "nieuwe notitie"
    assert result.source.imported_at == r.source.imported_at


def test_replace_source_behoudt_source_id_en_type(service):
    r = service.register_pdf(
        title="Oud", original_filename="oud.pdf", file_hash="hash_oud"
    )
    result = service.replace_source(
        r.source.source_id,
        title="Nieuw",
        file_hash="hash_nieuw",
        original_filename="nieuw.pdf",
        notes=None,
    )
    assert result.source.source_id == r.source.source_id
    assert result.source.source_type is ImportSourceType.PDF
    assert result.source.imported_by == r.source.imported_by


def test_replace_source_status_overschrijven_naar_concept(service):
    r = service.register_pdf(
        title="Oud", original_filename="oud.pdf", file_hash="hash_oud"
    )
    service.set_status(r.source.source_id, ImportStatus.ACTIEF)
    result = service.replace_source(
        r.source.source_id,
        title="Nieuw",
        file_hash="hash_nieuw",
        original_filename="nieuw.pdf",
        notes=None,
        status=ImportStatus.CONCEPT,
    )
    assert result.source.status is ImportStatus.CONCEPT


def test_replace_source_zonder_status_behoudt_bestaande(service):
    r = service.register_pdf(
        title="Oud", original_filename="oud.pdf", file_hash="hash_oud"
    )
    service.set_status(r.source.source_id, ImportStatus.ACTIEF)
    result = service.replace_source(
        r.source.source_id,
        title="Nieuw",
        file_hash="hash_nieuw",
        original_filename="nieuw.pdf",
        notes=None,
    )
    assert result.source.status is ImportStatus.ACTIEF


def test_replace_source_custom_imported_at(service):
    r = service.register_pdf(
        title="Oud", original_filename="oud.pdf", file_hash="hash_oud"
    )
    nieuw_ts = r.source.imported_at + 5000
    result = service.replace_source(
        r.source.source_id,
        title="Nieuw",
        file_hash="hash_nieuw",
        original_filename="nieuw.pdf",
        notes=None,
        imported_at=nieuw_ts,
    )
    assert result.source.imported_at == nieuw_ts


def test_replace_source_onbekende_id_faalt(service):
    with pytest.raises(ImportValidationError):
        service.replace_source(
            "bestaat-niet",
            title="X",
            file_hash="y",
            original_filename="z.pdf",
            notes=None,
        )


def test_replace_source_persisteert_naar_disk(service, tmp_path):
    r = service.register_pdf(
        title="Oud", original_filename="oud.pdf", file_hash="hash_oud"
    )
    service.replace_source(
        r.source.source_id,
        title="Nieuw",
        file_hash="hash_nieuw",
        original_filename="nieuw.pdf",
        notes=None,
    )
    service2 = ImportService(catalog_path=service.catalog_path)
    terug = service2.get(r.source.source_id)
    assert terug.title == "Nieuw"
    assert terug.file_hash == "hash_nieuw"


def test_replace_source_url_behoudt_source_url(service):
    r = service.register_url(title="Oud", source_url="https://example.com")
    result = service.replace_source(
        r.source.source_id,
        title="Nieuw",
        file_hash=None,
        original_filename=None,
        notes="nieuw",
    )
    assert result.source.source_url == "https://example.com"


# ============================================================================
# v1.1.1 — beste match bij duplicate-detectie
# ============================================================================

def test_find_by_file_hash_kiest_actief_boven_gearchiveerd(service):
    """Bij meerdere matches met dezelfde hash: Actief wint van Gearchiveerd."""
    oud = service.register_pdf(
        title="Oud", original_filename="oud.pdf", file_hash="abc123"
    )
    service.archive(oud.source.source_id)

    nieuw = service.register_pdf(
        title="Nieuw", original_filename="nieuw.pdf", file_hash="abc123"
    )
    service.set_status(nieuw.source.source_id, ImportStatus.ACTIEF)

    gevonden = service.find_by_file_hash("abc123")
    assert gevonden is not None
    assert gevonden.source_id == nieuw.source.source_id
    assert gevonden.status is ImportStatus.ACTIEF


def test_find_by_file_hash_kiest_concept_boven_gearchiveerd(service):
    """Concept wint van Gearchiveerd."""
    oud = service.register_pdf(
        title="Oud", original_filename="oud.pdf", file_hash="abc123"
    )
    service.archive(oud.source.source_id)

    nieuw = service.register_pdf(
        title="Nieuw", original_filename="nieuw.pdf", file_hash="abc123"
    )

    gevonden = service.find_by_file_hash("abc123")
    assert gevonden is not None
    assert gevonden.source_id == nieuw.source.source_id
    assert gevonden.status is ImportStatus.CONCEPT


def test_find_by_file_hash_kiest_actief_boven_concept(service):
    """Actief wint van Concept."""
    eerste = service.register_pdf(
        title="Eerste", original_filename="eerste.pdf", file_hash="abc123"
    )
    service.set_status(eerste.source.source_id, ImportStatus.ACTIEF)

    service.register_pdf(
        title="Tweede", original_filename="tweede.pdf", file_hash="abc123"
    )

    gevonden = service.find_by_file_hash("abc123")
    assert gevonden is not None
    assert gevonden.source_id == eerste.source.source_id
    assert gevonden.status is ImportStatus.ACTIEF


def test_find_by_file_hash_gelijke_status_kiest_recentste(service):
    """Bij gelijke status: hoogste imported_at (meest recente)."""
    service.register_pdf(
        title="Eerste", original_filename="eerste.pdf", file_hash="abc123"
    )
    tweede = service.register_pdf(
        title="Tweede", original_filename="tweede.pdf", file_hash="abc123"
    )

    gevonden = service.find_by_file_hash("abc123")
    assert gevonden is not None
    assert gevonden.source_id == tweede.source.source_id


def test_find_by_source_url_kiest_actief_boven_gearchiveerd(service):
    """Bij meerdere URL-matches: Actief wint van Gearchiveerd."""
    oud = service.register_url(title="Oud", source_url="https://example.com")
    service.archive(oud.source.source_id)

    nieuw = service.register_url(
        title="Nieuw", source_url="https://example.com"
    )
    service.set_status(nieuw.source.source_id, ImportStatus.ACTIEF)

    gevonden = service.find_by_source_url("https://example.com")
    assert gevonden is not None
    assert gevonden.source_id == nieuw.source.source_id
    assert gevonden.status is ImportStatus.ACTIEF


def test_find_by_source_url_gelijke_status_kiest_recentste(service):
    """Bij gelijke status: hoogste imported_at."""
    service.register_url(title="Eerste", source_url="https://example.com")
    tweede = service.register_url(
        title="Tweede", source_url="https://example.com"
    )

    gevonden = service.find_by_source_url("https://example.com")
    assert gevonden is not None
    assert gevonden.source_id == tweede.source.source_id