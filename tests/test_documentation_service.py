"""
================================================================================
Module:     tests/test_documentation_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-02
Auteur:     Bart Bossuyt

Doel:       Regressietests voor read-only catalogusladen, validatie, zoeken en
            filteren van de documentatiebibliotheek.

Wijzigingen:
  v1.0.0 (2026-10-02)  Eerste DocumentationService-tests.
================================================================================
"""

import json

import pytest

from app.documentation.models import DocumentCategory
from app.documentation.service import (
    DocumentationService,
    DocumentationValidationError,
)


def _write_catalog(path, documents):
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "data_version": "test-1",
                "documents": documents,
            }
        ),
        encoding="utf-8",
    )


def _documents():
    return [
        {
            "document_id": "panasonic-fm",
            "title": "FM Series Datasheet",
            "category": "DATASHEET",
            "source_type": "FILE_AND_URL",
            "source_path": "docs/FM.pdf",
            "source_url": "https://example.invalid/fm",
            "tool_key": "ESR_CAPACITOR",
            "manufacturer": "Panasonic",
            "series": "FM",
            "part_number": None,
            "document_version": "Rev. 3",
            "document_date": "2026-01",
            "notes": "Low ESR",
        },
        {
            "document_id": "safety-discharge",
            "title": "Capacitor discharge",
            "category": "SAFETY",
            "source_type": "FILE",
            "source_path": "docs/discharge.pdf",
            "source_url": None,
            "tool_key": None,
            "manufacturer": None,
            "series": None,
            "part_number": None,
            "document_version": None,
            "document_date": None,
            "notes": "General safety",
        },
    ]


def test_load_documents_preserves_source_metadata(tmp_path):
    path = tmp_path / "catalog.json"
    _write_catalog(path, _documents())

    documents = DocumentationService(path).load_documents()

    assert len(documents) == 2
    assert documents[0].source_path == "docs/FM.pdf"
    assert documents[0].source_url == "https://example.invalid/fm"
    assert documents[0].tool_key == "ESR_CAPACITOR"


def test_search_is_case_insensitive_and_searches_metadata(tmp_path):
    path = tmp_path / "catalog.json"
    _write_catalog(path, _documents())
    service = DocumentationService(path)

    assert [d.document_id for d in service.list_documents(search_text="panasonic")] == [
        "panasonic-fm"
    ]
    assert [d.document_id for d in service.list_documents(search_text="LOW esr")] == [
        "panasonic-fm"
    ]


def test_category_and_tool_filter_work_together(tmp_path):
    path = tmp_path / "catalog.json"
    _write_catalog(path, _documents())
    service = DocumentationService(path)

    documents = service.list_documents(
        category=DocumentCategory.DATASHEET,
        tool_key="esr_capacitor",
    )

    assert [d.document_id for d in documents] == ["panasonic-fm"]


def test_invalid_category_is_rejected(tmp_path):
    path = tmp_path / "catalog.json"
    documents = _documents()
    documents[0]["category"] = "NOT_A_CATEGORY"
    _write_catalog(path, documents)

    with pytest.raises(DocumentationValidationError):
        DocumentationService(path).load_documents()


def test_duplicate_document_id_is_rejected(tmp_path):
    path = tmp_path / "catalog.json"
    documents = _documents()
    documents.append(dict(documents[0]))
    _write_catalog(path, documents)

    with pytest.raises(DocumentationValidationError, match="Dubbele document_id"):
        DocumentationService(path).load_documents()


def test_service_exposes_no_write_or_delete_api():
    assert not hasattr(DocumentationService, "save_document")
    assert not hasattr(DocumentationService, "update_document")
    assert not hasattr(DocumentationService, "delete_document")
