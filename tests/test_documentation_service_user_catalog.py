"""
================================================================================
Module:     tests/test_documentation_service_user_catalog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-08
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de tweede cataloguslaag in
            DocumentationService: imports uit imported_catalog.json
            worden samengevoegd met de ingebouwde catalogus.

Wijzigingen:
  v1.0.0 (2026-10-07)  Eerste versie: basisintegratie, dubbele
                       document_id, bronresolutie.
  v1.0.1 (2026-10-07)  Regressietests voor de metadata die sinds
                       5D'.2c wordt doorgegeven aan DocumentMetadata.
  v1.1.0 (2026-10-08)  Fase 5D'.2e: tests voor include_archived-
                       parameter en voor het doorgeven van import_status
                       aan DocumentMetadata.
================================================================================
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.documentation.models import DocumentCategory
from app.documentation.service import DocumentationService


# ============================================================================
# Hulp: maak een minimale ingebouwde catalogus in tmp_path
# ============================================================================

def _maak_ingebouwde_catalogus(pad: Path) -> Path:
    pad.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "data_version": "test-1",
                "documents": [
                    {
                        "document_id": "builtin-1",
                        "title": "Ingebouwd document",
                        "category": "DATASHEET",
                        "source_type": "URL",
                        "source_url": "https://example.com/builtin",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return pad


def _schrijf_gebruikerscatalogus(pad: Path, sources: list[dict]) -> Path:
    pad.write_text(
        json.dumps(
            {"schema_version": 1, "sources": sources},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return pad


def _basis_source(
    *,
    source_id: str = "import-1",
    status: str = "concept",
    **extra,
) -> dict:
    bron = {
        "source_id": source_id,
        "source_type": "pdf",
        "title": "Eigen import",
        "imported_at": 1_700_000_000_000,
        "imported_by": "tester",
        "status": status,
        "original_filename": "eigen.pdf",
        "file_hash": "hash_x",
    }
    bron.update(extra)
    return bron


# ============================================================================
# Basisintegratie
# ============================================================================

def test_gebruikerscatalogus_wordt_samengevoegd(tmp_path):
    ingebouwd = _maak_ingebouwde_catalogus(tmp_path / "catalog.json")
    gebruikers = _schrijf_gebruikerscatalogus(
        tmp_path / "imported.json",
        [_basis_source()],
    )

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )

    docs = service.load_documents()
    ids = {d.document_id for d in docs}
    assert ids == {"builtin-1", "import-1"}


def test_gebruikerscatalogus_wint_bij_dubbele_document_id(tmp_path):
    ingebouwd = _maak_ingebouwde_catalogus(tmp_path / "catalog.json")
    gebruikers = _schrijf_gebruikerscatalogus(
        tmp_path / "imported.json",
        [_basis_source(source_id="builtin-1")],
    )

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )

    docs = service.load_documents()
    assert len(docs) == 1
    assert docs[0].title == "Eigen import"


# ============================================================================
# Metadata sinds 5D'.2c
# ============================================================================

def test_metadata_wordt_doorgegeven_aan_documentmetadata(tmp_path):
    ingebouwd = _maak_ingebouwde_catalogus(tmp_path / "catalog.json")
    gebruikers = _schrijf_gebruikerscatalogus(
        tmp_path / "imported.json",
        [
            _basis_source(
                category="MANUAL",
                manufacturer="CHONG",
                series="CDX",
                part_number="CDX-1",
                document_version="V1.1",
                document_date="2026-10-08",
                notes="Testnotitie",
            )
        ],
    )

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )

    doc = service.get_document("import-1")
    assert doc.category is DocumentCategory.MANUAL
    assert doc.manufacturer == "CHONG"
    assert doc.series == "CDX"
    assert doc.part_number == "CDX-1"
    assert doc.document_version == "V1.1"
    assert doc.document_date == "2026-10-08"
    assert doc.notes == "Testnotitie"
    assert doc.is_user_import is True


def test_lege_categorie_valt_terug_op_datasheet(tmp_path):
    ingebouwd = _maak_ingebouwde_catalogus(tmp_path / "catalog.json")
    gebruikers = _schrijf_gebruikerscatalogus(
        tmp_path / "imported.json",
        [_basis_source()],
    )

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )

    doc = service.get_document("import-1")
    assert doc.category is DocumentCategory.DATASHEET


# ============================================================================
# include_archived — sinds 5D'.2e
# ============================================================================

def test_default_verbergt_gearchiveerde_imports(tmp_path):
    ingebouwd = _maak_ingebouwde_catalogus(tmp_path / "catalog.json")
    gebruikers = _schrijf_gebruikerscatalogus(
        tmp_path / "imported.json",
        [_basis_source(status="gearchiveerd")],
    )

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )

    docs = service.load_documents()
    ids = {d.document_id for d in docs}
    assert ids == {"builtin-1"}


def test_include_archived_toont_gearchiveerde_imports(tmp_path):
    ingebouwd = _maak_ingebouwde_catalogus(tmp_path / "catalog.json")
    gebruikers = _schrijf_gebruikerscatalogus(
        tmp_path / "imported.json",
        [_basis_source(status="gearchiveerd")],
    )

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )

    docs = service.load_documents(include_archived=True)
    ids = {d.document_id for d in docs}
    assert ids == {"builtin-1", "import-1"}


def test_ingebouwde_catalogus_negeert_include_archived(tmp_path):
    ingebouwd = _maak_ingebouwde_catalogus(tmp_path / "catalog.json")
    gebruikers = _schrijf_gebruikerscatalogus(
        tmp_path / "imported.json",
        [],
    )

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )

    docs_zonder = service.load_documents(include_archived=False)
    docs_met = service.load_documents(include_archived=True)
    assert {d.document_id for d in docs_zonder} == {"builtin-1"}
    assert {d.document_id for d in docs_met} == {"builtin-1"}


def test_combinatie_met_search_text(tmp_path):
    ingebouwd = _maak_ingebouwde_catalogus(tmp_path / "catalog.json")
    gebruikers = _schrijf_gebruikerscatalogus(
        tmp_path / "imported.json",
        [
            _basis_source(
                source_id="import-a",
                status="gearchiveerd",
                manufacturer="CHONG",
            ),
            _basis_source(
                source_id="import-b",
                status="concept",
                manufacturer="PANASONIC",
            ),
        ],
    )

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )

    result = service.list_documents(
        search_text="PANASONIC",
        include_archived=True,
    )
    assert {d.document_id for d in result} == {"import-b"}


def test_combinatie_met_category(tmp_path):
    ingebouwd = _maak_ingebouwde_catalogus(tmp_path / "catalog.json")
    gebruikers = _schrijf_gebruikerscatalogus(
        tmp_path / "imported.json",
        [
            _basis_source(
                source_id="import-a",
                status="gearchiveerd",
                category="MANUAL",
            ),
            _basis_source(
                source_id="import-b",
                status="gearchiveerd",
                category="DATASHEET",
            ),
        ],
    )

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )

    result = service.list_documents(
        category="MANUAL",
        include_archived=True,
    )
    assert {d.document_id for d in result} == {"import-a"}


def test_import_status_wordt_doorgegeven_aan_documentmetadata(tmp_path):
    ingebouwd = _maak_ingebouwde_catalogus(tmp_path / "catalog.json")
    gebruikers = _schrijf_gebruikerscatalogus(
        tmp_path / "imported.json",
        [
            _basis_source(source_id="import-a", status="actief"),
            _basis_source(source_id="import-b", status="gearchiveerd"),
        ],
    )

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )

    doc_a = service.get_document("import-a")
    assert doc_a.import_status == "actief"

    doc_b = service.get_document("import-b")
    assert doc_b.import_status == "gearchiveerd"