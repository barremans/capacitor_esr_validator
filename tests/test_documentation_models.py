"""
================================================================================
Module:     tests/test_documentation_models.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.2.0
Datum:      2026-10-02
Auteur:     Bart Bossuyt

Doel:       Regressietests voor vaste documentcategorieën en immutable metadata.

Wijzigingen:
  v1.0.0 (2026-10-02)  Eerste tests voor documentatiemodellen.
  v1.1.0 (2026-10-03)  Backward-compatible tool_keys metadata getest.
  v1.2.0 (2026-10-03)  Overige optionele multi-context tuples getest.
================================================================================
"""

from dataclasses import FrozenInstanceError

import pytest

from app.documentation.models import (
    DocumentCategory,
    DocumentMetadata,
    DocumentSourceType,
)


def test_document_categories_match_approved_foundation_set():
    assert {item.value for item in DocumentCategory} == {
        "DATASHEET",
        "APPLICATION_NOTE",
        "MEASUREMENT_TECHNIQUE",
        "MANUAL",
        "SAFETY",
        "REFERENCE_TABLE",
        "INTERNAL_INSTRUCTION",
    }


def test_document_metadata_is_immutable():
    document = DocumentMetadata(
        document_id="doc-1",
        title="Test",
        category=DocumentCategory.DATASHEET,
        source_type=DocumentSourceType.FILE,
        source_path="docs/test.pdf",
        source_url=None,
        tool_key="ESR_CAPACITOR",
        manufacturer="Maker",
        series="Series",
        part_number="Part",
        document_version="1",
        document_date="2026-10-02",
        notes=None,
    )

    with pytest.raises(FrozenInstanceError):
        document.title = "Changed"


def test_document_metadata_tool_keys_defaults_to_empty_tuple():
    document = DocumentMetadata(
        document_id="doc-2",
        title="General",
        category=DocumentCategory.SAFETY,
        source_type=DocumentSourceType.FILE,
        source_path="docs/general.md",
        source_url=None,
        tool_key=None,
        manufacturer=None,
        series=None,
        part_number=None,
        document_version=None,
        document_date=None,
        notes=None,
    )

    assert document.tool_keys == ()


def test_document_metadata_accepts_multiple_tool_keys():
    document = DocumentMetadata(
        document_id="doc-3",
        title="Shared",
        category=DocumentCategory.MEASUREMENT_TECHNIQUE,
        source_type=DocumentSourceType.FILE,
        source_path="docs/shared.md",
        source_url=None,
        tool_key="ESR_CAPACITOR",
        manufacturer=None,
        series=None,
        part_number=None,
        document_version="1",
        document_date=None,
        notes=None,
        tool_keys=("ESR_CAPACITOR", "RESISTOR"),
    )

    assert document.tool_keys == ("ESR_CAPACITOR", "RESISTOR")


def test_document_metadata_multicontext_fields_default_to_empty_tuples():
    document = DocumentMetadata(
        document_id="doc-4",
        title="Shared context",
        category=DocumentCategory.INTERNAL_INSTRUCTION,
        source_type=DocumentSourceType.FILE,
        source_path="docs/shared.md",
        source_url=None,
        tool_key=None,
        manufacturer=None,
        series=None,
        part_number=None,
        document_version=None,
        document_date=None,
        notes=None,
    )

    assert document.component_types == ()
    assert document.test_keys == ()
    assert document.measurement_methods == ()
    assert document.instrument_keys == ()
    assert document.topics == ()


def test_document_metadata_accepts_multicontext_tuples():
    document = DocumentMetadata(
        document_id="doc-5",
        title="Context",
        category=DocumentCategory.MEASUREMENT_TECHNIQUE,
        source_type=DocumentSourceType.FILE,
        source_path="docs/context.md",
        source_url=None,
        tool_key="ESR_CAPACITOR",
        manufacturer=None,
        series=None,
        part_number=None,
        document_version="1",
        document_date=None,
        notes=None,
        component_types=("CAPACITOR",),
        test_keys=("ESR", "CAPACITANCE"),
        measurement_methods=("EX_SITU", "ONE_LEG"),
        instrument_keys=("ESR70", "LCR_ST1"),
        topics=("frequency", "in-circuit"),
    )

    assert document.component_types == ("CAPACITOR",)
    assert document.measurement_methods == ("EX_SITU", "ONE_LEG")
    assert document.topics == ("frequency", "in-circuit")
