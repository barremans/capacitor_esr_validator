"""
================================================================================
Module:     tests/test_documentation_models.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-02
Auteur:     Bart Bossuyt

Doel:       Regressietests voor vaste documentcategorieën en immutable metadata.

Wijzigingen:
  v1.0.0 (2026-10-02)  Eerste tests voor documentatiemodellen.
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
