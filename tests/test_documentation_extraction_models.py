"""
================================================================================
Module:     tests/test_documentation_extraction_models.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-22
Auteur:     Bart Bossuyt

Doel:       Regressietests voor app/documentation/extraction_models.py
            (fase 12A.1). Puur, geen Qt, geen netwerk.

Wijzigingen:
  v1.0.0 (2026-10-22)  Eerste versie.
================================================================================
"""

from __future__ import annotations

import pytest

from app.documentation.extraction_models import (
    ExtractionError,
    ExtractionResult,
    ExtractionSourceKind,
)


# ---------------------------------------------------------------- enum

def test_source_kind_heeft_vier_waarden():
    waarden = {kind.value for kind in ExtractionSourceKind}
    assert waarden == {"pdf", "docx", "xlsx", "url"}


def test_source_kind_is_str_enum():
    assert ExtractionSourceKind.PDF == "pdf"
    assert ExtractionSourceKind("docx") is ExtractionSourceKind.DOCX


# ---------------------------------------------------------------- gelukkig pad

def test_extraction_result_gelukkig_pad():
    result = ExtractionResult(
        source_kind=ExtractionSourceKind.PDF,
        source_id="src-1",
        text="Hallo wereld",
        pages=("Hallo", "wereld"),
        metadata={"page_count": 2},
        origin="C:/bron.pdf",
    )

    assert result.source_kind is ExtractionSourceKind.PDF
    assert result.source_id == "src-1"
    assert result.text == "Hallo wereld"
    assert result.pages == ("Hallo", "wereld")
    assert result.metadata == {"page_count": 2}
    assert result.origin == "C:/bron.pdf"
    assert result.is_empty is False


def test_extraction_result_minimaal():
    result = ExtractionResult(
        source_kind=ExtractionSourceKind.URL,
        source_id=None,
        text="",
    )

    assert result.pages == ()
    assert result.metadata == {}
    assert result.warnings == ()
    assert result.origin is None
    assert result.is_empty is True


# ---------------------------------------------------------------- normalisatie

def test_source_id_whitespace_wordt_none():
    result = ExtractionResult(
        source_kind=ExtractionSourceKind.PDF,
        source_id="   ",
        text="x",
    )
    assert result.source_id is None


def test_origin_whitespace_wordt_none():
    result = ExtractionResult(
        source_kind=ExtractionSourceKind.PDF,
        source_id=None,
        text="x",
        origin="   ",
    )
    assert result.origin is None


def test_metadata_wordt_gekopieerd():
    """De metadata-dict mag achteraf niet muteerbaar zijn."""
    bron_metadata = {"title": "Test"}
    result = ExtractionResult(
        source_kind=ExtractionSourceKind.PDF,
        source_id=None,
        text="x",
        metadata=bron_metadata,
    )
    bron_metadata["title"] = "Gewijzigd"
    assert result.metadata == {"title": "Test"}


# ---------------------------------------------------------------- validatie

def test_ongeldige_source_kind_faalt():
    with pytest.raises(ExtractionError):
        ExtractionResult(
            source_kind="pdf",  # type: ignore[arg-type]
            source_id=None,
            text="x",
        )


def test_text_moet_string_zijn():
    with pytest.raises(ExtractionError):
        ExtractionResult(
            source_kind=ExtractionSourceKind.PDF,
            source_id=None,
            text=123,  # type: ignore[arg-type]
        )


def test_pages_moet_tuple_zijn():
    with pytest.raises(ExtractionError):
        ExtractionResult(
            source_kind=ExtractionSourceKind.PDF,
            source_id=None,
            text="x",
            pages=["a", "b"],  # type: ignore[arg-type]
        )


def test_pages_inhoud_moet_string_zijn():
    with pytest.raises(ExtractionError):
        ExtractionResult(
            source_kind=ExtractionSourceKind.PDF,
            source_id=None,
            text="x",
            pages=("a", 2),  # type: ignore[arg-type]
        )


def test_metadata_moet_dict_zijn():
    with pytest.raises(ExtractionError):
        ExtractionResult(
            source_kind=ExtractionSourceKind.PDF,
            source_id=None,
            text="x",
            metadata=[("a", 1)],  # type: ignore[arg-type]
        )


def test_warnings_moet_tuple_zijn():
    with pytest.raises(ExtractionError):
        ExtractionResult(
            source_kind=ExtractionSourceKind.PDF,
            source_id=None,
            text="x",
            warnings=["waarschuwing"],  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------- to_dict

def test_to_dict_bevat_alle_velden():
    result = ExtractionResult(
        source_kind=ExtractionSourceKind.XLSX,
        source_id="src-2",
        text="ABC",
        pages=(),
        metadata={"sheet_count": 1},
        warnings=("leeg blad",),
        origin="C:/bron.xlsx",
    )

    data = result.to_dict()
    assert data == {
        "source_kind": "xlsx",
        "source_id": "src-2",
        "text": "ABC",
        "pages": [],
        "metadata": {"sheet_count": 1},
        "warnings": ["leeg blad"],
        "origin": "C:/bron.xlsx",
    }


def test_to_dict_is_herhaalbaar():
    """Twee to_dict-aanroepen geven onafhankelijke dicts."""
    result = ExtractionResult(
        source_kind=ExtractionSourceKind.PDF,
        source_id=None,
        text="x",
        metadata={"title": "T"},
    )
    a = result.to_dict()
    b = result.to_dict()
    a["metadata"]["title"] = "gewijzigd"
    assert b["metadata"]["title"] == "T"