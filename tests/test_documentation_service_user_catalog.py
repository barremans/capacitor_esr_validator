"""
================================================================================
Module:     tests/test_documentation_service_user_catalog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.1
Datum:      2026-10-07
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de tweede cataloguslaag in
            DocumentationService: geïmporteerde bronnen worden samengevoegd
            met de ingebouwde catalogus.

Wijzigingen:
  v1.0.0 (2026-10-07)  Eerste versie.
  v1.0.1 (2026-10-07)  Test test_user_catalog_path_none_gebruikt_standaardpad
                        was fout: die riep DocumentationService aan MET een
                        expliciete catalog_path en verwachtte toen dat de
                        gebruikerscatalogus alsnog werd meegeladen. Dat is
                        precies het gedrag dat v1.8.1 bewust uitschakelt.
                        Opgesplitst in twee correcte tests: default-
                        constructor en expliciete catalog_path.
================================================================================
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.documentation.models import (
    DocumentCategory,
    DocumentSourceType,
)
from app.documentation.service import (
    DocumentationError,
    DocumentationService,
    DocumentationValidationError,
    IMPORTED_CATALOG_SCHEMA_VERSION,
)


def _schrijf_ingebouwde_catalogus(pad: Path, documenten: list[dict]) -> None:
    pad.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "data_version": "test-1",
                "documents": documenten,
            }
        ),
        encoding="utf-8",
    )


def _schrijf_gebruikerscatalogus(pad: Path, sources: list[dict]) -> None:
    pad.write_text(
        json.dumps(
            {
                "schema_version": IMPORTED_CATALOG_SCHEMA_VERSION,
                "sources": sources,
            }
        ),
        encoding="utf-8",
    )


def _ingebouwd_doc(document_id: str = "doc-1", titel: str = "Ingebouwd") -> dict:
    return {
        "document_id": document_id,
        "title": titel,
        "category": "DATASHEET",
        "source_type": "URL",
        "source_url": "https://example.com/builtin",
    }


def _import_source(
    source_id: str = "src-1",
    *,
    titel: str = "Geïmporteerd",
    source_type: str = "pdf",
    status: str = "concept",
) -> dict:
    basis = {
        "source_id": source_id,
        "source_type": source_type,
        "title": titel,
        "imported_at": 1_700_000_000_000,
        "imported_by": "tester",
        "status": status,
        "original_filename": None,
        "source_url": None,
        "file_hash": None,
        "notes": None,
    }
    if source_type == "pdf":
        basis["original_filename"] = "doc.pdf"
    else:
        basis["source_url"] = "https://example.com/imported"
    return basis


def test_gebruikerscatalogus_wordt_samengevoegd(tmp_path):
    ingebouwd = tmp_path / "catalog.json"
    gebruikers = tmp_path / "imported_catalog.json"

    _schrijf_ingebouwde_catalogus(ingebouwd, [_ingebouwd_doc("doc-1", "Ingebouwd")])
    _schrijf_gebruikerscatalogus(gebruikers, [_import_source("src-1", titel="Geïmporteerd")])

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )
    docs = service.load_documents()

    assert len(docs) == 2
    ids = {d.document_id for d in docs}
    assert ids == {"doc-1", "src-1"}


def test_ontbrekende_gebruikerscatalogus_is_geen_fout(tmp_path):
    ingebouwd = tmp_path / "catalog.json"
    _schrijf_ingebouwde_catalogus(ingebouwd, [_ingebouwd_doc()])

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=tmp_path / "bestaat-niet.json",
    )
    docs = service.load_documents()
    assert len(docs) == 1


def test_lege_gebruikerscatalogus_is_geen_fout(tmp_path):
    ingebouwd = tmp_path / "catalog.json"
    gebruikers = tmp_path / "imported_catalog.json"
    _schrijf_ingebouwde_catalogus(ingebouwd, [_ingebouwd_doc()])
    gebruikers.write_text("", encoding="utf-8")

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )
    docs = service.load_documents()
    assert len(docs) == 1


def test_gebruikerscatalogus_wint_bij_dubbele_id(tmp_path):
    ingebouwd = tmp_path / "catalog.json"
    gebruikers = tmp_path / "imported_catalog.json"

    _schrijf_ingebouwde_catalogus(ingebouwd, [_ingebouwd_doc("doc-1", "Ingebouwd")])
    _schrijf_gebruikerscatalogus(gebruikers, [_import_source("doc-1", titel="Import wint")])

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )
    docs = service.load_documents()

    assert len(docs) == 1
    assert docs[0].title == "Import wint"


def test_gearchiveerde_bron_wordt_niet_getoond(tmp_path):
    ingebouwd = tmp_path / "catalog.json"
    gebruikers = tmp_path / "imported_catalog.json"

    _schrijf_ingebouwde_catalogus(ingebouwd, [_ingebouwd_doc()])
    _schrijf_gebruikerscatalogus(
        gebruikers,
        [
            _import_source("src-actief", titel="Actief", status="actief"),
            _import_source("src-archief", titel="Gearchiveerd", status="gearchiveerd"),
        ],
    )

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )
    docs = service.load_documents()

    ids = {d.document_id for d in docs}
    assert "src-actief" in ids
    assert "src-archief" not in ids


def test_pdf_import_krijgt_file_source_type(tmp_path):
    ingebouwd = tmp_path / "catalog.json"
    gebruikers = tmp_path / "imported_catalog.json"

    _schrijf_ingebouwde_catalogus(ingebouwd, [])
    _schrijf_gebruikerscatalogus(
        gebruikers,
        [_import_source("src-1", source_type="pdf")],
    )

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )
    docs = service.load_documents()

    assert len(docs) == 1
    assert docs[0].source_type is DocumentSourceType.FILE
    assert docs[0].source_path == "sources/src-1.pdf"
    assert docs[0].category is DocumentCategory.DATASHEET


def test_url_import_krijgt_url_source_type(tmp_path):
    ingebouwd = tmp_path / "catalog.json"
    gebruikers = tmp_path / "imported_catalog.json"

    _schrijf_ingebouwde_catalogus(ingebouwd, [])
    _schrijf_gebruikerscatalogus(
        gebruikers,
        [_import_source("src-1", source_type="url")],
    )

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )
    docs = service.load_documents()

    assert len(docs) == 1
    assert docs[0].source_type is DocumentSourceType.URL
    assert docs[0].source_url == "https://example.com/imported"
    assert docs[0].source_path is None


def test_default_constructor_gebruikt_standaardpad():
    """DocumentationService() zonder argumenten leest de gebruikerscatalogus
    op het standaardpad onder %LOCALAPPDATA%."""
    service = DocumentationService()
    assert service.user_catalog_path is not None
    assert "ElectronicsDiagnosticToolHub" in str(service.user_catalog_path)
    assert str(service.user_catalog_path).endswith("imported_catalog.json")


def test_expliciete_catalog_path_schakelt_gebruikerscatalogus_uit(tmp_path):
    """DocumentationService(catalog_path=X) zonder user_catalog_path leest
    uitsluitend X. Dit isoleert tests en bestaande code die expliciet
    één catalogus opgeeft."""
    ingebouwd = tmp_path / "catalog.json"
    _schrijf_ingebouwde_catalogus(ingebouwd, [_ingebouwd_doc()])

    service = DocumentationService(catalog_path=ingebouwd)
    assert service.user_catalog_path is None


def test_user_catalog_path_lege_string_schakelt_uit(tmp_path):
    ingebouwd = tmp_path / "catalog.json"
    _schrijf_ingebouwde_catalogus(ingebouwd, [_ingebouwd_doc()])

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path="",
    )
    assert service.user_catalog_path is None
    assert len(service.load_documents()) == 1


def test_get_document_vindt_geimporteerde_bron(tmp_path):
    ingebouwd = tmp_path / "catalog.json"
    gebruikers = tmp_path / "imported_catalog.json"

    _schrijf_ingebouwde_catalogus(ingebouwd, [])
    _schrijf_gebruikerscatalogus(gebruikers, [_import_source("src-abc")])

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )
    doc = service.get_document("src-abc")
    assert doc.document_id == "src-abc"


def test_corrupte_gebruikerscatalogus_faalt(tmp_path):
    ingebouwd = tmp_path / "catalog.json"
    gebruikers = tmp_path / "imported_catalog.json"

    _schrijf_ingebouwde_catalogus(ingebouwd, [_ingebouwd_doc()])
    gebruikers.write_text("{ geen geldige json", encoding="utf-8")

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )
    with pytest.raises(DocumentationValidationError):
        service.load_documents()


def test_verkeerde_schema_version_in_gebruikerscatalogus_faalt(tmp_path):
    ingebouwd = tmp_path / "catalog.json"
    gebruikers = tmp_path / "imported_catalog.json"

    _schrijf_ingebouwde_catalogus(ingebouwd, [_ingebouwd_doc()])
    gebruikers.write_text(
        json.dumps({"schema_version": 999, "sources": []}),
        encoding="utf-8",
    )

    service = DocumentationService(
        catalog_path=ingebouwd,
        user_catalog_path=gebruikers,
    )
    with pytest.raises(DocumentationValidationError):
        service.load_documents()