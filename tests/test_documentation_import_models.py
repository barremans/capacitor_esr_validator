"""
================================================================================
Module:     tests/test_documentation_import_models.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.3.0
Datum:      2026-10-09
Auteur:     Bart Bossuyt

Doel:       Regressietests voor import_models: enums, frozen-gedrag,
            statusovergangen, serialisatie en de metadata-uitbreiding
            uit fase 5D'.2b (category, manufacturer, series, part_number,
            document_version, document_date). Sinds v1.3.0 ook de
            DOCX- en XLSX-brontypes uit fase 6A.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie.
  v1.1.0 (2026-10-07)  DuplicateAction en DuplicateMatch.
  v1.2.0 (2026-10-07)  Metadata-velden (5D'.2b): defaults, normalisatie
                       van lege strings naar None, to_dict/from_dict
                       round-trip, backward-compat met oude catalogi.
  v1.3.0 (2026-10-09)  Fase 6A: ImportSourceType.DOCX en .XLSX,
                       validatie van local-file-types, round-trip.
================================================================================
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.documentation.import_models import (
    DuplicateAction,
    DuplicateMatch,
    ImportResult,
    ImportSource,
    ImportSourceType,
    ImportStatus,
    ImportValidationError,
    is_allowed_transition,
)


# ---------------------------------------------------------------- helpers

def _pdf_source(**overrides) -> ImportSource:
    basis = dict(
        source_id="src-1",
        source_type=ImportSourceType.PDF,
        title="Titel",
        imported_at=1_700_000_000_000,
        imported_by="tester",
        status=ImportStatus.CONCEPT,
        original_filename="doc.pdf",
        file_hash="abc123",
    )
    basis.update(overrides)
    return ImportSource(**basis)


def _url_source(**overrides) -> ImportSource:
    basis = dict(
        source_id="src-2",
        source_type=ImportSourceType.URL,
        title="Titel",
        imported_at=1_700_000_000_000,
        imported_by="tester",
        status=ImportStatus.CONCEPT,
        source_url="https://example.com",
    )
    basis.update(overrides)
    return ImportSource(**basis)


def _docx_source(**overrides) -> ImportSource:
    basis = dict(
        source_id="src-3",
        source_type=ImportSourceType.DOCX,
        title="Titel",
        imported_at=1_700_000_000_000,
        imported_by="tester",
        status=ImportStatus.CONCEPT,
        original_filename="doc.docx",
        file_hash="abc123",
    )
    basis.update(overrides)
    return ImportSource(**basis)


def _xlsx_source(**overrides) -> ImportSource:
    basis = dict(
        source_id="src-4",
        source_type=ImportSourceType.XLSX,
        title="Titel",
        imported_at=1_700_000_000_000,
        imported_by="tester",
        status=ImportStatus.CONCEPT,
        original_filename="doc.xlsx",
        file_hash="abc123",
    )
    basis.update(overrides)
    return ImportSource(**basis)


# ============================================================================
# Enums
# ============================================================================

def test_import_source_type_waarden():
    assert ImportSourceType.PDF.value == "pdf"
    assert ImportSourceType.URL.value == "url"
    assert ImportSourceType.DOCX.value == "docx"
    assert ImportSourceType.XLSX.value == "xlsx"


def test_import_status_waarden():
    assert ImportStatus.CONCEPT.value == "concept"
    assert ImportStatus.ACTIEF.value == "actief"
    assert ImportStatus.GEARCHIVEERD.value == "gearchiveerd"


def test_duplicate_action_waarden():
    assert DuplicateAction.KEEP.value == "keep"
    assert DuplicateAction.NEW_VERSION.value == "new_version"
    assert DuplicateAction.OVERWRITE.value == "overwrite"


# ============================================================================
# Statusovergangen
# ============================================================================

@pytest.mark.parametrize(
    "huidige,nieuwe,verwacht",
    [
        (ImportStatus.CONCEPT, ImportStatus.ACTIEF, True),
        (ImportStatus.CONCEPT, ImportStatus.GEARCHIVEERD, True),
        (ImportStatus.ACTIEF, ImportStatus.CONCEPT, True),
        (ImportStatus.ACTIEF, ImportStatus.GEARCHIVEERD, True),
        (ImportStatus.GEARCHIVEERD, ImportStatus.CONCEPT, True),
        (ImportStatus.GEARCHIVEERD, ImportStatus.ACTIEF, False),
        (ImportStatus.CONCEPT, ImportStatus.CONCEPT, False),
        (ImportStatus.ACTIEF, ImportStatus.ACTIEF, False),
        (ImportStatus.GEARCHIVEERD, ImportStatus.GEARCHIVEERD, False),
    ],
)
def test_is_allowed_transition(huidige, nieuwe, verwacht):
    assert is_allowed_transition(huidige, nieuwe) is verwacht


def test_is_allowed_transition_ongeldig_type_faalt():
    with pytest.raises(ImportValidationError):
        is_allowed_transition("concept", ImportStatus.ACTIEF)  # type: ignore[arg-type]
    with pytest.raises(ImportValidationError):
        is_allowed_transition(ImportStatus.CONCEPT, "actief")  # type: ignore[arg-type]


# ============================================================================
# ImportSource — basisvalidatie
# ============================================================================

def test_pdf_source_geldig():
    s = _pdf_source()
    assert s.source_type is ImportSourceType.PDF
    assert s.original_filename == "doc.pdf"
    assert s.source_url is None


def test_url_source_geldig():
    s = _url_source()
    assert s.source_type is ImportSourceType.URL
    assert s.source_url == "https://example.com"
    assert s.original_filename is None


def test_pdf_zonder_original_filename_faalt():
    with pytest.raises(ImportValidationError):
        _pdf_source(original_filename=None)


def test_pdf_met_source_url_faalt():
    with pytest.raises(ImportValidationError):
        _pdf_source(source_url="https://example.com")


def test_url_zonder_source_url_faalt():
    with pytest.raises(ImportValidationError):
        _url_source(source_url=None)


def test_url_met_original_filename_faalt():
    with pytest.raises(ImportValidationError):
        _url_source(original_filename="doc.pdf")


def test_source_id_leeg_faalt():
    with pytest.raises(ImportValidationError):
        _pdf_source(source_id="")


def test_title_leeg_faalt():
    with pytest.raises(ImportValidationError):
        _pdf_source(title="")
    with pytest.raises(ImportValidationError):
        _pdf_source(title="   ")


def test_imported_at_negatief_faalt():
    with pytest.raises(ImportValidationError):
        _pdf_source(imported_at=0)
    with pytest.raises(ImportValidationError):
        _pdf_source(imported_at=-1)


def test_imported_by_leeg_faalt():
    with pytest.raises(ImportValidationError):
        _pdf_source(imported_by="")


def test_source_type_verkeerd_type_faalt():
    with pytest.raises(ImportValidationError):
        _pdf_source(source_type="pdf")  # type: ignore[arg-type]


def test_status_verkeerd_type_faalt():
    with pytest.raises(ImportValidationError):
        _pdf_source(status="concept")  # type: ignore[arg-type]


# ============================================================================
# ImportSource — frozen-gedrag
# ============================================================================

def test_import_source_is_frozen():
    s = _pdf_source()
    with pytest.raises(FrozenInstanceError):
        s.title = "Anders"  # type: ignore[misc]


# ============================================================================
# ImportSource — serialisatie (basisvelden)
# ============================================================================

def test_to_dict_bevat_alle_velden():
    s = _pdf_source(notes="noot")
    data = s.to_dict()
    for sleutel in (
        "source_id",
        "source_type",
        "title",
        "imported_at",
        "imported_by",
        "status",
        "original_filename",
        "source_url",
        "file_hash",
        "notes",
        "category",
        "manufacturer",
        "series",
        "part_number",
        "document_version",
        "document_date",
    ):
        assert sleutel in data
    assert data["source_type"] == "pdf"
    assert data["status"] == "concept"


def test_round_trip_pdf_zonder_metadata():
    s = _pdf_source()
    hersteld = ImportSource.from_dict(s.to_dict())
    assert hersteld == s


def test_round_trip_url_met_metadata():
    s = _url_source(
        category="DATASHEET",
        manufacturer="Panasonic",
        series="FR",
        part_number="FR-123",
        document_version="1.2",
        document_date="2024-01",
        notes="noot",
    )
    hersteld = ImportSource.from_dict(s.to_dict())
    assert hersteld == s


# ============================================================================
# v1.2.0 — metadata-velden (5D'.2b)
# ============================================================================

def test_metadata_defaults_zijn_none():
    s = _pdf_source()
    assert s.category is None
    assert s.manufacturer is None
    assert s.series is None
    assert s.part_number is None
    assert s.document_version is None
    assert s.document_date is None


def test_metadata_lege_string_wordt_none():
    s = _pdf_source(
        category="",
        manufacturer="   ",
        series="",
        part_number="\t",
        document_version="",
        document_date="  ",
    )
    assert s.category is None
    assert s.manufacturer is None
    assert s.series is None
    assert s.part_number is None
    assert s.document_version is None
    assert s.document_date is None


def test_metadata_wordt_gestript():
    s = _pdf_source(
        category="  DATASHEET  ",
        manufacturer="  Panasonic  ",
        series="  FR  ",
        part_number="  FR-123  ",
        document_version="  1.2  ",
        document_date="  2024-01  ",
    )
    assert s.category == "DATASHEET"
    assert s.manufacturer == "Panasonic"
    assert s.series == "FR"
    assert s.part_number == "FR-123"
    assert s.document_version == "1.2"
    assert s.document_date == "2024-01"


def test_notes_lege_string_wordt_none():
    s = _pdf_source(notes="   ")
    assert s.notes is None


def test_metadata_verkeerd_type_faalt():
    with pytest.raises(ImportValidationError):
        _pdf_source(category=123)  # type: ignore[arg-type]
    with pytest.raises(ImportValidationError):
        _pdf_source(manufacturer=[])  # type: ignore[arg-type]


def test_from_dict_zonder_metadata_geeft_none():
    """Backward-compat: catalogus van vóór 5D'.2b blijft geldig."""
    data = {
        "source_id": "src-1",
        "source_type": "pdf",
        "title": "Titel",
        "imported_at": 1_700_000_000_000,
        "imported_by": "tester",
        "status": "concept",
        "original_filename": "doc.pdf",
        "source_url": None,
        "file_hash": "abc123",
        "notes": None,
    }
    s = ImportSource.from_dict(data)
    assert s.category is None
    assert s.manufacturer is None
    assert s.series is None
    assert s.part_number is None
    assert s.document_version is None
    assert s.document_date is None


def test_from_dict_met_metadata():
    data = {
        "source_id": "src-1",
        "source_type": "pdf",
        "title": "Titel",
        "imported_at": 1_700_000_000_000,
        "imported_by": "tester",
        "status": "concept",
        "original_filename": "doc.pdf",
        "source_url": None,
        "file_hash": "abc123",
        "notes": None,
        "category": "DATASHEET",
        "manufacturer": "Panasonic",
        "series": "FR",
        "part_number": "FR-123",
        "document_version": "1.2",
        "document_date": "2024-01",
    }
    s = ImportSource.from_dict(data)
    assert s.category == "DATASHEET"
    assert s.manufacturer == "Panasonic"
    assert s.series == "FR"
    assert s.part_number == "FR-123"
    assert s.document_version == "1.2"
    assert s.document_date == "2024-01"


def test_from_dict_lege_metadata_wordt_none():
    data = {
        "source_id": "src-1",
        "source_type": "pdf",
        "title": "Titel",
        "imported_at": 1_700_000_000_000,
        "imported_by": "tester",
        "status": "concept",
        "original_filename": "doc.pdf",
        "source_url": None,
        "file_hash": "abc123",
        "notes": None,
        "category": "",
        "manufacturer": "  ",
        "series": None,
        "part_number": None,
        "document_version": None,
        "document_date": None,
    }
    s = ImportSource.from_dict(data)
    assert s.category is None
    assert s.manufacturer is None


# ============================================================================
# ImportResult
# ============================================================================

def test_import_result_defaults():
    s = _pdf_source()
    r = ImportResult(source=s)
    assert r.source is s
    assert r.changed is True
    assert r.message is None


def test_import_result_frozen():
    s = _pdf_source()
    r = ImportResult(source=s, changed=False, message="niets")
    with pytest.raises(FrozenInstanceError):
        r.changed = True  # type: ignore[misc]


# ============================================================================
# DuplicateMatch
# ============================================================================

def test_duplicate_match_geldig():
    s = _pdf_source()
    m = DuplicateMatch(bestaande=s, match_type="file_hash")
    assert m.bestaande is s
    assert m.match_type == "file_hash"


def test_duplicate_match_ongeldig_type_faalt():
    s = _pdf_source()
    with pytest.raises(ImportValidationError):
        DuplicateMatch(bestaande=s, match_type="titel")  # type: ignore[arg-type]


def test_duplicate_match_bestaande_verkeerd_type_faalt():
    with pytest.raises(ImportValidationError):
        DuplicateMatch(bestaande="geen-source", match_type="file_hash")  # type: ignore[arg-type]


# ============================================================================
# v1.3.0 — ImportSourceType DOCX en XLSX (fase 6A)
# ============================================================================

def test_docx_source_geldig():
    s = _docx_source()
    assert s.source_type is ImportSourceType.DOCX
    assert s.original_filename == "doc.docx"
    assert s.source_url is None


def test_xlsx_source_geldig():
    s = _xlsx_source()
    assert s.source_type is ImportSourceType.XLSX
    assert s.original_filename == "doc.xlsx"
    assert s.source_url is None


def test_docx_zonder_original_filename_faalt():
    with pytest.raises(ImportValidationError):
        _docx_source(original_filename=None)


def test_docx_met_source_url_faalt():
    with pytest.raises(ImportValidationError):
        _docx_source(source_url="https://example.com")


def test_xlsx_zonder_original_filename_faalt():
    with pytest.raises(ImportValidationError):
        _xlsx_source(original_filename=None)


def test_xlsx_met_source_url_faalt():
    with pytest.raises(ImportValidationError):
        _xlsx_source(source_url="https://example.com")


def test_round_trip_docx_zonder_metadata():
    s = _docx_source()
    hersteld = ImportSource.from_dict(s.to_dict())
    assert hersteld == s


def test_round_trip_xlsx_zonder_metadata():
    s = _xlsx_source()
    hersteld = ImportSource.from_dict(s.to_dict())
    assert hersteld == s


def test_round_trip_docx_met_metadata():
    s = _docx_source(
        category="MANUAL",
        manufacturer="CHONG",
        series="CDX",
        part_number="CDX-1",
        document_version="V1.1",
        document_date="2026-10-09",
        notes="noot",
    )
    hersteld = ImportSource.from_dict(s.to_dict())
    assert hersteld == s


def test_round_trip_xlsx_met_metadata():
    s = _xlsx_source(
        category="REFERENCE_TABLE",
        manufacturer="TDK",
        notes="noot",
    )
    hersteld = ImportSource.from_dict(s.to_dict())
    assert hersteld == s


def test_docx_to_dict_heeft_docx_source_type():
    s = _docx_source()
    assert s.to_dict()["source_type"] == "docx"


def test_xlsx_to_dict_heeft_xlsx_source_type():
    s = _xlsx_source()
    assert s.to_dict()["source_type"] == "xlsx"


def test_from_dict_docx():
    data = {
        "source_id": "src-3",
        "source_type": "docx",
        "title": "Titel",
        "imported_at": 1_700_000_000_000,
        "imported_by": "tester",
        "status": "concept",
        "original_filename": "doc.docx",
        "source_url": None,
        "file_hash": "abc123",
        "notes": None,
    }
    s = ImportSource.from_dict(data)
    assert s.source_type is ImportSourceType.DOCX


def test_from_dict_xlsx():
    data = {
        "source_id": "src-4",
        "source_type": "xlsx",
        "title": "Titel",
        "imported_at": 1_700_000_000_000,
        "imported_by": "tester",
        "status": "concept",
        "original_filename": "doc.xlsx",
        "source_url": None,
        "file_hash": "abc123",
        "notes": None,
    }
    s = ImportSource.from_dict(data)
    assert s.source_type is ImportSourceType.XLSX


def test_from_dict_onbekende_source_type_faalt():
    data = {
        "source_id": "src-x",
        "source_type": "pptx",  # niet ondersteund
        "title": "Titel",
        "imported_at": 1_700_000_000_000,
        "imported_by": "tester",
        "status": "concept",
        "original_filename": "doc.pptx",
    }
    with pytest.raises(ImportValidationError):
        ImportSource.from_dict(data)