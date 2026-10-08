"""
================================================================================
Module:     tests/test_documentation_edit_metadata_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-07
Auteur:     Bart Bossuyt

Doel:       Regressietests voor ImportService.update_metadata (fase 5D'.2c).

            update_metadata wijzigt uitsluitend metadata (titel, categorie,
            fabrikant, serie, partnummer, documentversie, documentdatum,
            notities). Het bronbestand (file_hash, original_filename,
            source_url), de status en imported_at blijven ongewijzigd.

Wijzigingen:
  v1.0.0 (2026-10-07)  Eerste versie.
================================================================================
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.documentation.import_models import (
    ImportSourceType,
    ImportStatus,
    ImportValidationError,
)
from app.documentation.import_service import ImportService


@pytest.fixture()
def service(tmp_path):
    return ImportService(catalog_path=tmp_path / "imported_catalog.json")


def _registreer_pdf(service, **overrides):
    basis = dict(
        title="OUD",
        original_filename="oud.pdf",
        file_hash="hash_abc",
        category="DATASHEET",
        manufacturer="PANASONIC",
        series="FR",
        part_number="FR-123",
        document_version="1.0",
        document_date="2024-01-01",
        notes="oude notitie",
    )
    basis.update(overrides)
    return service.register_pdf(**basis)


# ============================================================================
# Basis: wijzigen van metadata
# ============================================================================

def test_update_metadata_wijzigt_titel(service):
    r = _registreer_pdf(service)
    result = service.update_metadata(r.source.source_id, title="NIEUW")
    assert result.source.title == "NIEUW"


def test_update_metadata_wijzigt_meerdere_velden(service):
    r = _registreer_pdf(service)
    result = service.update_metadata(
        r.source.source_id,
        title="NIEUW",
        category="MANUAL",
        manufacturer="TDK",
        series="C-SERIES",
        part_number="C-456",
        document_version="2.0",
        document_date="2023-06-15",
        notes="nieuwe notitie",
    )
    s = result.source
    assert s.title == "NIEUW"
    assert s.category == "MANUAL"
    assert s.manufacturer == "TDK"
    assert s.series == "C-SERIES"
    assert s.part_number == "C-456"
    assert s.document_version == "2.0"
    assert s.document_date == "2023-06-15"
    assert s.notes == "nieuwe notitie"


# ============================================================================
# Behoud van niet-metadata velden
# ============================================================================

def test_update_metadata_behoudt_source_id(service):
    r = _registreer_pdf(service)
    result = service.update_metadata(r.source.source_id, title="NIEUW")
    assert result.source.source_id == r.source.source_id


def test_update_metadata_behoudt_source_type(service):
    r = _registreer_pdf(service)
    result = service.update_metadata(r.source.source_id, title="NIEUW")
    assert result.source.source_type is ImportSourceType.PDF


def test_update_metadata_behoudt_file_hash(service):
    r = _registreer_pdf(service)
    result = service.update_metadata(r.source.source_id, title="NIEUW")
    assert result.source.file_hash == "hash_abc"


def test_update_metadata_behoudt_original_filename(service):
    r = _registreer_pdf(service)
    result = service.update_metadata(r.source.source_id, title="NIEUW")
    assert result.source.original_filename == "oud.pdf"


def test_update_metadata_behoudt_imported_at(service):
    r = _registreer_pdf(service)
    result = service.update_metadata(r.source.source_id, title="NIEUW")
    assert result.source.imported_at == r.source.imported_at


def test_update_metadata_behoudt_imported_by(service):
    r = _registreer_pdf(service)
    result = service.update_metadata(r.source.source_id, title="NIEUW")
    assert result.source.imported_by == r.source.imported_by


def test_update_metadata_behoudt_status(service):
    r = _registreer_pdf(service)
    service.set_status(r.source.source_id, ImportStatus.ACTIEF)
    result = service.update_metadata(r.source.source_id, title="NIEUW")
    assert result.source.status is ImportStatus.ACTIEF


def test_update_metadata_behoudt_status_gearchiveerd(service):
    r = _registreer_pdf(service)
    service.archive(r.source.source_id)
    result = service.update_metadata(r.source.source_id, title="NIEUW")
    assert result.source.status is ImportStatus.GEARCHIVEERD


def test_update_metadata_behoudt_source_url_bij_url_bron(service):
    r = service.register_url(
        title="OUD", source_url="https://example.com"
    )
    result = service.update_metadata(r.source.source_id, title="NIEUW")
    assert result.source.source_url == "https://example.com"


# ============================================================================
# Sentinel-semantiek
# ============================================================================

def test_update_metadata_niet_meegegeven_behoudt_bestaande(service):
    r = _registreer_pdf(service)
    result = service.update_metadata(r.source.source_id, title="NIEUW")
    assert result.source.category == "DATASHEET"
    assert result.source.manufacturer == "PANASONIC"
    assert result.source.series == "FR"
    assert result.source.part_number == "FR-123"
    assert result.source.document_version == "1.0"
    assert result.source.document_date == "2024-01-01"
    assert result.source.notes == "oude notitie"


def test_update_metadata_expliciet_none_maakt_leeg(service):
    r = _registreer_pdf(service)
    result = service.update_metadata(
        r.source.source_id,
        category=None,
        manufacturer=None,
        series=None,
        part_number=None,
        document_version=None,
        document_date=None,
        notes=None,
    )
    s = result.source
    assert s.category is None
    assert s.manufacturer is None
    assert s.series is None
    assert s.part_number is None
    assert s.document_version is None
    assert s.document_date is None
    assert s.notes is None


def test_update_metadata_lege_string_wordt_none(service):
    r = _registreer_pdf(service)
    result = service.update_metadata(
        r.source.source_id,
        manufacturer="",
        series="   ",
    )
    assert result.source.manufacturer is None
    assert result.source.series is None


def test_update_metadata_titel_none_behoudt_bestaande(service):
    """Titel mag niet leeg zijn; None of lege string behoudt de bestaande titel."""
    r = _registreer_pdf(service)
    result = service.update_metadata(r.source.source_id, title=None)
    assert result.source.title == "OUD"


def test_update_metadata_titel_lege_string_behoudt_bestaande(service):
    r = _registreer_pdf(service)
    result = service.update_metadata(r.source.source_id, title="   ")
    assert result.source.title == "OUD"


# ============================================================================
# Foutpaden
# ============================================================================

def test_update_metadata_onbekende_id_faalt(service):
    with pytest.raises(ImportValidationError):
        service.update_metadata("bestaat-niet", title="X")


# ============================================================================
# Persistentie
# ============================================================================

def test_update_metadata_persisteert_naar_disk(service):
    r = _registreer_pdf(service)
    service.update_metadata(
        r.source.source_id, title="NIEUW", manufacturer="TDK"
    )
    service2 = ImportService(catalog_path=service.catalog_path)
    terug = service2.get(r.source.source_id)
    assert terug.title == "NIEUW"
    assert terug.manufacturer == "TDK"


def test_update_metadata_wijzigt_niets_aan_andere_bronnen(service):
    a = _registreer_pdf(service, title="A", original_filename="a.pdf")
    b = _registreer_pdf(service, title="B", original_filename="b.pdf")
    service.update_metadata(a.source.source_id, title="A-NIEUW")
    a_terug = service.get(a.source.source_id)
    b_terug = service.get(b.source.source_id)
    assert a_terug.title == "A-NIEUW"
    assert b_terug.title == "B"


def test_update_metadata_meerdere_keren(service):
    r = _registreer_pdf(service)
    service.update_metadata(r.source.source_id, title="STAP1")
    service.update_metadata(r.source.source_id, title="STAP2")
    service.update_metadata(r.source.source_id, title="STAP3")
    terug = service.get(r.source.source_id)
    assert terug.title == "STAP3"