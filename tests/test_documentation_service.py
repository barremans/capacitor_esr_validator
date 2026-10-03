"""
================================================================================
Module:     tests/test_documentation_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.4.0
Datum:      2026-10-03
Auteur:     Bart Bossuyt

Doel:       Regressietests voor read-only catalogusladen, validatie, zoeken en
            filteren van de documentatiebibliotheek.

Wijzigingen:
  v1.0.0 (2026-10-02)  Eerste DocumentationService-tests.
  v1.1.0 (2026-10-02)  Lookup, veilig tekstlezen en padbeveiliging getest.
  v1.2.0 (2026-10-02)  Gestructureerde provenance parsing en validatie getest.
  v1.3.0 (2026-10-03)  title_key wordt optioneel geladen zonder officiële titel te vervangen.
  v1.4.0 (2026-10-03)  Meertalige interne Markdown-resolutie en fallback naar
                        nl_NL getest, inclusief backward compatibility.
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



def test_get_document_and_read_document_text(tmp_path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "guide.md").write_text("# Guide\nVeilige inhoud.\n", encoding="utf-8")

    path = tmp_path / "catalog.json"
    documents = [
        {
            "document_id": "guide",
            "title": "Guide",
            "category": "MEASUREMENT_TECHNIQUE",
            "source_type": "FILE",
            "source_path": "content/guide.md",
            "source_url": None,
            "tool_key": "ESR_CAPACITOR",
            "manufacturer": None,
            "series": None,
            "part_number": None,
            "document_version": "1",
            "document_date": "2026-10-02",
            "notes": None,
        }
    ]
    _write_catalog(path, documents)

    service = DocumentationService(path)

    assert service.get_document("guide").title == "Guide"
    assert service.read_document_text("guide") == "# Guide\nVeilige inhoud.\n"


def test_read_document_text_rejects_path_escape(tmp_path):
    outside = tmp_path.parent / "outside.md"
    outside.write_text("niet lezen", encoding="utf-8")

    path = tmp_path / "catalog.json"
    documents = [
        {
            "document_id": "escape",
            "title": "Escape",
            "category": "MEASUREMENT_TECHNIQUE",
            "source_type": "FILE",
            "source_path": "../outside.md",
            "source_url": None,
            "tool_key": "ESR_CAPACITOR",
            "manufacturer": None,
            "series": None,
            "part_number": None,
            "document_version": "1",
            "document_date": "2026-10-02",
            "notes": None,
        }
    ]
    _write_catalog(path, documents)

    with pytest.raises(DocumentationValidationError, match="buiten de documentatiemap"):
        DocumentationService(path).read_document_text("escape")


def test_read_document_text_rejects_non_text_source(tmp_path):
    (tmp_path / "guide.pdf").write_bytes(b"%PDF-test")
    path = tmp_path / "catalog.json"
    documents = [
        {
            "document_id": "pdf",
            "title": "PDF",
            "category": "MANUAL",
            "source_type": "FILE",
            "source_path": "guide.pdf",
            "source_url": None,
            "tool_key": "ESR_CAPACITOR",
            "manufacturer": None,
            "series": None,
            "part_number": None,
            "document_version": "1",
            "document_date": "2026-10-02",
            "notes": None,
        }
    ]
    _write_catalog(path, documents)

    from app.documentation.service import DocumentationError

    with pytest.raises(DocumentationError, match="geen leesbare tekstbron"):
        DocumentationService(path).read_document_text("pdf")



def test_structured_provenance_is_loaded(tmp_path):
    path = tmp_path / "catalog.json"
    documents = _documents()
    documents[0]["provenance"] = [
        {
            "source_id": "master_02",
            "source_title": "Technical reference",
            "source_kind": "FILE",
            "source_path": "MASTER_02.md",
            "source_url": None,
            "locator": "Chapter 6",
            "supports": ["parallel_paths", "frequency"],
            "note": "Project source",
        }
    ]
    _write_catalog(path, documents)

    document = DocumentationService(path).get_document("panasonic-fm")

    assert len(document.provenance) == 1
    ref = document.provenance[0]
    assert ref.source_id == "master_02"
    assert ref.locator == "Chapter 6"
    assert ref.supports == ("parallel_paths", "frequency")


def test_invalid_provenance_supports_is_rejected(tmp_path):
    path = tmp_path / "catalog.json"
    documents = _documents()
    documents[0]["provenance"] = [
        {
            "source_id": "bad",
            "source_title": "Bad",
            "source_kind": "FILE",
            "source_path": "bad.md",
            "source_url": None,
            "locator": None,
            "supports": "not-a-list",
            "note": None,
        }
    ]
    _write_catalog(path, documents)

    with pytest.raises(DocumentationValidationError, match="supports"):
        DocumentationService(path).load_documents()



def test_title_key_is_optional_and_preserves_official_title(tmp_path):
    path = tmp_path / "catalog.json"
    documents = _documents()
    documents[0]["title_key"] = "documentatie.document_titels.panasonic_fm"
    _write_catalog(path, documents)

    document = DocumentationService(path).get_document("panasonic-fm")

    assert document.title == "FM Series Datasheet"
    assert document.title_key == "documentatie.document_titels.panasonic_fm"


def test_multilingual_internal_document_prefers_requested_language(tmp_path):
    nl_dir = tmp_path / "internal" / "nl_NL"
    en_dir = tmp_path / "internal" / "en_US"
    nl_dir.mkdir(parents=True)
    en_dir.mkdir(parents=True)
    (nl_dir / "guide.md").write_text("# Nederlands\n", encoding="utf-8")
    (en_dir / "guide.md").write_text("# English\n", encoding="utf-8")

    path = tmp_path / "catalog.json"
    documents = [
        {
            "document_id": "guide",
            "title": "Guide",
            "category": "MEASUREMENT_TECHNIQUE",
            "source_type": "FILE",
            "source_path": "internal/nl_NL/guide.md",
            "source_url": None,
            "tool_key": "ESR_CAPACITOR",
            "manufacturer": None,
            "series": None,
            "part_number": None,
            "document_version": "1",
            "document_date": "2026-10-03",
            "notes": None,
        }
    ]
    _write_catalog(path, documents)

    service = DocumentationService(path)

    assert service.read_document_text("guide", language="en_US") == "# English\n"
    assert service.read_document_text("guide", language="nl_NL") == "# Nederlands\n"


def test_multilingual_internal_document_falls_back_to_dutch(tmp_path):
    nl_dir = tmp_path / "internal" / "nl_NL"
    nl_dir.mkdir(parents=True)
    (nl_dir / "guide.md").write_text("# Nederlands\n", encoding="utf-8")

    path = tmp_path / "catalog.json"
    documents = [
        {
            "document_id": "guide",
            "title": "Guide",
            "category": "MEASUREMENT_TECHNIQUE",
            "source_type": "FILE",
            "source_path": "internal/nl_NL/guide.md",
            "source_url": None,
            "tool_key": "ESR_CAPACITOR",
            "manufacturer": None,
            "series": None,
            "part_number": None,
            "document_version": "1",
            "document_date": "2026-10-03",
            "notes": None,
        }
    ]
    _write_catalog(path, documents)

    service = DocumentationService(path)

    assert service.read_document_text("guide", language="de_DE") == "# Nederlands\n"


def test_legacy_text_source_path_remains_backward_compatible(tmp_path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "guide.md").write_text("# Legacy\n", encoding="utf-8")

    path = tmp_path / "catalog.json"
    documents = [
        {
            "document_id": "guide",
            "title": "Guide",
            "category": "MEASUREMENT_TECHNIQUE",
            "source_type": "FILE",
            "source_path": "content/guide.md",
            "source_url": None,
            "tool_key": "ESR_CAPACITOR",
            "manufacturer": None,
            "series": None,
            "part_number": None,
            "document_version": "1",
            "document_date": "2026-10-03",
            "notes": None,
        }
    ]
    _write_catalog(path, documents)

    assert DocumentationService(path).read_document_text(
        "guide", language="en_US"
    ) == "# Legacy\n"
