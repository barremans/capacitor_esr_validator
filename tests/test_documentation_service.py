"""
================================================================================
Module:     tests/test_documentation_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.7.0
Datum:      2026-10-04
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
  v1.5.0 (2026-10-03)  tool_key/tool_keys normalisatie, filtering en validatie getest.
  v1.6.0 (2026-10-03)  Multi-contextvelden, filters, zoeken en validatie getest.
  v1.6.1 (2026-10-03)  Zoektest gebruikt unieke metadatawaarden zodat bestaande
                        documenttitels geen vals-positieve match veroorzaken.
  v1.7.0 (2026-10-04)  Vrije zoektekst gebruikt de nieuwe zoektaal en matcht
                        alleen nog op document-eigen metadata. Tool-, context-
                        en provenance-velden zijn uitsluitend via de bestaande
                        filters bereikbaar. Twee voormalige zoek-tests zijn
                        herschreven om dit expliciet te bewijzen.
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


def test_legacy_tool_key_is_exposed_as_normalized_tool_keys(tmp_path):
    path = tmp_path / "catalog.json"
    _write_catalog(path, _documents())

    document = DocumentationService(path).get_document("panasonic-fm")

    assert document.tool_key == "ESR_CAPACITOR"
    assert document.tool_keys == ("ESR_CAPACITOR",)


def test_tool_keys_only_is_backward_compatible_with_tool_key_alias(tmp_path):
    path = tmp_path / "catalog.json"
    documents = _documents()
    documents[0].pop("tool_key")
    documents[0]["tool_keys"] = ["esr_capacitor", "resistor"]
    _write_catalog(path, documents)

    document = DocumentationService(path).get_document("panasonic-fm")

    assert document.tool_key == "ESR_CAPACITOR"
    assert document.tool_keys == ("ESR_CAPACITOR", "RESISTOR")


def test_tool_key_and_tool_keys_are_merged_without_duplicates(tmp_path):
    path = tmp_path / "catalog.json"
    documents = _documents()
    documents[0]["tool_keys"] = ["esr_capacitor", "RESISTOR", "resistor"]
    _write_catalog(path, documents)

    document = DocumentationService(path).get_document("panasonic-fm")

    assert document.tool_key == "ESR_CAPACITOR"
    assert document.tool_keys == ("ESR_CAPACITOR", "RESISTOR")


def test_tool_filter_matches_any_tool_key(tmp_path):
    path = tmp_path / "catalog.json"
    documents = _documents()
    documents[0]["tool_keys"] = ["RESISTOR"]
    _write_catalog(path, documents)

    service = DocumentationService(path)

    assert [d.document_id for d in service.list_documents(tool_key="ESR_CAPACITOR")] == [
        "panasonic-fm"
    ]
    assert [d.document_id for d in service.list_documents(tool_key="resistor")] == [
        "panasonic-fm"
    ]


@pytest.mark.parametrize(
    "bad_value",
    [
        "ESR_CAPACITOR",
        [None],
        [""],
        ["BAD-KEY"],
    ],
)
def test_invalid_tool_keys_is_rejected(tmp_path, bad_value):
    path = tmp_path / "catalog.json"
    documents = _documents()
    documents[0]["tool_keys"] = bad_value
    _write_catalog(path, documents)

    with pytest.raises(DocumentationValidationError, match="tool_keys|tool_key"):
        DocumentationService(path).load_documents()


def test_search_does_not_match_tool_keys_via_search_field(tmp_path):
    """Zoeken op tool_keys werkt uitsluitend via de filter, niet via zoekveld."""
    path = tmp_path / "catalog.json"
    documents = _documents()
    documents[0]["tool_keys"] = ["RESISTOR"]
    _write_catalog(path, documents)

    service = DocumentationService(path)

    # Vrije zoektekst matcht NIET meer op tool_keys
    assert service.list_documents(search_text="resistor") == []

    # De filter werkt nog wel
    assert [d.document_id for d in service.list_documents(tool_key="resistor")] == [
        "panasonic-fm"
    ]


def test_multicontext_fields_are_normalized_and_deduplicated(tmp_path):
    path = tmp_path / "catalog.json"
    documents = _documents()
    documents[0]["component_types"] = ["capacitor", "CAPACITOR"]
    documents[0]["test_keys"] = ["esr", "capacitance"]
    documents[0]["measurement_methods"] = ["ex_situ", "one_leg"]
    documents[0]["instrument_keys"] = ["esr70", "LCR_ST1"]
    documents[0]["topics"] = ["Frequency", "in-circuit", "frequency"]
    _write_catalog(path, documents)

    document = DocumentationService(path).get_document("panasonic-fm")

    assert document.component_types == ("CAPACITOR",)
    assert document.test_keys == ("ESR", "CAPACITANCE")
    assert document.measurement_methods == ("EX_SITU", "ONE_LEG")
    assert document.instrument_keys == ("ESR70", "LCR_ST1")
    assert document.topics == ("frequency", "in-circuit")


def test_multicontext_filters_match_independently_and_together(tmp_path):
    path = tmp_path / "catalog.json"
    documents = _documents()
    documents[0]["component_types"] = ["CAPACITOR"]
    documents[0]["test_keys"] = ["ESR"]
    documents[0]["measurement_methods"] = ["IN_CIRCUIT"]
    documents[0]["instrument_keys"] = ["ESR70"]
    documents[0]["topics"] = ["parallel-paths"]
    _write_catalog(path, documents)

    service = DocumentationService(path)

    assert [d.document_id for d in service.list_documents(component_type="capacitor")] == [
        "panasonic-fm"
    ]
    assert [d.document_id for d in service.list_documents(test_key="esr")] == [
        "panasonic-fm"
    ]
    assert [d.document_id for d in service.list_documents(measurement_method="in_circuit")] == [
        "panasonic-fm"
    ]
    assert [d.document_id for d in service.list_documents(instrument_key="esr70")] == [
        "panasonic-fm"
    ]
    assert [d.document_id for d in service.list_documents(topic="PARALLEL-PATHS")] == [
        "panasonic-fm"
    ]

    combined = service.list_documents(
        tool_key="esr_capacitor",
        component_type="capacitor",
        test_key="esr",
        measurement_method="in_circuit",
        instrument_key="esr70",
        topic="parallel-paths",
    )
    assert [d.document_id for d in combined] == ["panasonic-fm"]


def test_multicontext_filter_excludes_non_matching_document(tmp_path):
    path = tmp_path / "catalog.json"
    documents = _documents()
    documents[0]["component_types"] = ["CAPACITOR"]
    _write_catalog(path, documents)

    assert DocumentationService(path).list_documents(component_type="RESISTOR") == []


def test_search_does_not_match_multicontext_via_search_field(tmp_path):
    """Vrije zoektekst matcht niet meer op component/test/methode/instrument/topic."""
    path = tmp_path / "catalog.json"
    documents = _documents()
    documents[0]["component_types"] = ["ALUMINUM_CAPACITOR"]
    documents[0]["test_keys"] = ["ESR_DIAGNOSTIC"]
    documents[0]["measurement_methods"] = ["ONE_LEG"]
    documents[0]["instrument_keys"] = ["LCR_ST1"]
    documents[0]["topics"] = ["frequency-context"]
    _write_catalog(path, documents)

    service = DocumentationService(path)

    for needle in (
        "aluminum_capacitor",
        "esr_diagnostic",
        "one_leg",
        "lcr_st1",
        "frequency-context",
    ):
        assert service.list_documents(search_text=needle) == [], needle

    # Maar de filters werken wel
    assert [d.document_id for d in service.list_documents(component_type="ALUMINUM_CAPACITOR")] == [
        "panasonic-fm"
    ]
    assert [d.document_id for d in service.list_documents(test_key="ESR_DIAGNOSTIC")] == [
        "panasonic-fm"
    ]
    assert [d.document_id for d in service.list_documents(measurement_method="ONE_LEG")] == [
        "panasonic-fm"
    ]
    assert [d.document_id for d in service.list_documents(instrument_key="LCR_ST1")] == [
        "panasonic-fm"
    ]
    assert [d.document_id for d in service.list_documents(topic="frequency-context")] == [
        "panasonic-fm"
    ]


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    [
        ("component_types", "CAPACITOR"),
        ("component_types", ["BAD TYPE"]),
        ("test_keys", [None]),
        ("measurement_methods", [""]),
        ("instrument_keys", ["LCR-ST1"]),
        ("topics", "frequency"),
        ("topics", ["bad topic"]),
        ("topics", [None]),
    ],
)
def test_invalid_multicontext_fields_are_rejected(tmp_path, field_name, bad_value):
    path = tmp_path / "catalog.json"
    documents = _documents()
    documents[0][field_name] = bad_value
    _write_catalog(path, documents)

    with pytest.raises(DocumentationValidationError):
        DocumentationService(path).load_documents()


def test_legacy_catalog_without_multicontext_fields_remains_valid(tmp_path):
    path = tmp_path / "catalog.json"
    _write_catalog(path, _documents())

    document = DocumentationService(path).get_document("panasonic-fm")

    assert document.component_types == ()
    assert document.test_keys == ()
    assert document.measurement_methods == ()
    assert document.instrument_keys == ()
    assert document.topics == ()


# ---------------------------------------------------------------------------
# Nieuwe zoektaal-tests (v1.7.0)
# ---------------------------------------------------------------------------


def test_search_supports_or_operator(tmp_path):
    path = tmp_path / "catalog.json"
    _write_catalog(path, _documents())
    service = DocumentationService(path)

    ids = {d.document_id for d in service.list_documents(search_text="panasonic|discharge")}
    assert ids == {"panasonic-fm", "safety-discharge"}


def test_search_supports_exclusion(tmp_path):
    path = tmp_path / "catalog.json"
    _write_catalog(path, _documents())
    service = DocumentationService(path)

    ids = {d.document_id for d in service.list_documents(search_text="!panasonic")}
    assert ids == {"safety-discharge"}


def test_search_supports_exact_word(tmp_path):
    path = tmp_path / "catalog.json"
    _write_catalog(path, _documents())
    service = DocumentationService(path)

    # "FM" is een los woord in de titel van panasonic-fm.
    ids = {d.document_id for d in service.list_documents(search_text="-FM")}
    assert ids == {"panasonic-fm"}


def test_search_supports_wildcard(tmp_path):
    path = tmp_path / "catalog.json"
    _write_catalog(path, _documents())
    service = DocumentationService(path)

    # %discharge matcht aan het einde van "Capacitor discharge"
    ids = {d.document_id for d in service.list_documents(search_text="%discharge")}
    assert ids == {"safety-discharge"}


def test_search_combines_and_or_and_exclusion(tmp_path):
    path = tmp_path / "catalog.json"
    _write_catalog(path, _documents())
    service = DocumentationService(path)

    # (panasonic OR discharge) AND NOT datasheet
    ids = {
        d.document_id
        for d in service.list_documents(search_text="panasonic|discharge !datasheet")
    }
    assert ids == {"safety-discharge"}