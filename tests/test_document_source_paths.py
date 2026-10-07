"""
================================================================================
Module:     tests/test_document_source_paths.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-07
Auteur:     Bart Bossuyt

Doel:       Regressietests voor document_source_paths: source_kind,
            resolve_local_path en resolve_builtin_path.

Wijzigingen:
  v1.0.0 (2026-10-07)  Eerste versie (fase 5D'.4).
================================================================================
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.documentation.models import (
    DocumentCategory,
    DocumentMetadata,
    DocumentSourceType,
)
from app.helpers.document_source_paths import (
    resolve_builtin_path,
    resolve_local_path,
    source_kind,
)


def _doc(
    *,
    source_type: DocumentSourceType = DocumentSourceType.FILE,
    source_path: str | None = "sources/abc.pdf",
    source_url: str | None = None,
    document_id: str = "abc",
) -> DocumentMetadata:
    return DocumentMetadata(
        document_id=document_id,
        title="Test",
        category=DocumentCategory.DATASHEET,
        source_type=source_type,
        source_path=source_path,
        source_url=source_url,
        tool_key=None,
        manufacturer=None,
        series=None,
        part_number=None,
        document_version=None,
        document_date=None,
        notes=None,
    )


# ============================================================================
# source_kind
# ============================================================================

@pytest.mark.parametrize(
    "path, verwacht",
    [
        ("sources/abc.pdf", "pdf"),
        ("sources/abc.PDF", "pdf"),
        ("sources/abc.docx", "word"),
        ("sources/abc.doc", "word"),
        ("sources/abc.xlsx", "excel"),
        ("sources/abc.xls", "excel"),
        ("internal/nl_NL/foo.md", "markdown"),
        ("internal/nl_NL/foo.txt", "markdown"),
        ("internal/nl_NL/foo.MD", "markdown"),
        ("sources/abc.unknown", "onbekend"),
    ],
)
def test_source_kind_file(path, verwacht):
    document = _doc(source_path=path)
    assert source_kind(document) == verwacht


def test_source_kind_url():
    document = _doc(
        source_type=DocumentSourceType.URL,
        source_path=None,
        source_url="https://example.com",
    )
    assert source_kind(document) == "url"


def test_source_kind_zonder_path_is_onbekend():
    document = _doc(source_path=None)
    assert source_kind(document) == "onbekend"


# ============================================================================
# resolve_local_path
# ============================================================================

def test_resolve_local_path_pdf_bestaat(tmp_path):
    sources_root = tmp_path / "sources"
    sources_root.mkdir()
    (sources_root / "abc.pdf").write_bytes(b"%PDF-1.4 fake")

    document = _doc(source_path="sources/abc.pdf")
    pad = resolve_local_path(document, sources_root=sources_root)

    assert pad is not None
    assert pad == sources_root / "abc.pdf"


def test_resolve_local_path_pdf_bestaat_niet(tmp_path):
    sources_root = tmp_path / "sources"
    sources_root.mkdir()

    document = _doc(source_path="sources/abc.pdf")
    assert resolve_local_path(document, sources_root=sources_root) is None


def test_resolve_local_path_zonder_sources_root():
    document = _doc(source_path="sources/abc.pdf")
    assert resolve_local_path(document, sources_root=None) is None


def test_resolve_local_path_url_snapshot_bestaat(tmp_path):
    snapshots_root = tmp_path / "snapshots"
    snapshots_root.mkdir()
    (snapshots_root / "abc.html").write_text("<html></html>", encoding="utf-8")

    document = _doc(
        source_type=DocumentSourceType.URL,
        source_path=None,
        source_url="https://example.com",
        document_id="abc",
    )
    pad = resolve_local_path(document, snapshots_root=snapshots_root)

    assert pad is not None
    assert pad == snapshots_root / "abc.html"


def test_resolve_local_path_url_zonder_snapshot(tmp_path):
    snapshots_root = tmp_path / "snapshots"
    snapshots_root.mkdir()

    document = _doc(
        source_type=DocumentSourceType.URL,
        source_path=None,
        source_url="https://example.com",
        document_id="abc",
    )
    assert resolve_local_path(document, snapshots_root=snapshots_root) is None


def test_resolve_local_path_markdown_geeft_none():
    """Markdown wordt niet via resolve_local_path gevonden."""
    document = _doc(source_path="internal/nl_NL/foo.md")
    assert resolve_local_path(document) is None


# ============================================================================
# resolve_builtin_path
# ============================================================================

def test_resolve_builtin_path_bestaat(tmp_path):
    catalog_root = tmp_path / "catalog"
    (catalog_root / "internal" / "nl_NL").mkdir(parents=True)
    (catalog_root / "internal" / "nl_NL" / "foo.md").write_text(
        "# Foo", encoding="utf-8"
    )

    document = _doc(source_path="internal/nl_NL/foo.md")
    pad = resolve_builtin_path(document, catalog_root=catalog_root)

    assert pad is not None
    assert pad.name == "foo.md"


def test_resolve_builtin_path_bestaat_niet(tmp_path):
    catalog_root = tmp_path / "catalog"
    catalog_root.mkdir()

    document = _doc(source_path="internal/nl_NL/foo.md")
    assert resolve_builtin_path(document, catalog_root=catalog_root) is None


def test_resolve_builtin_path_zonder_catalog_root():
    document = _doc(source_path="internal/nl_NL/foo.md")
    assert resolve_builtin_path(document, catalog_root=None) is None


def test_resolve_builtin_path_absoluut_pad_wordt_geweigerd(tmp_path):
    catalog_root = tmp_path / "catalog"
    catalog_root.mkdir()
    document = _doc(source_path=str(tmp_path / "elders" / "foo.md"))
    assert resolve_builtin_path(document, catalog_root=catalog_root) is None


def test_resolve_builtin_path_traversal_wordt_geweigerd(tmp_path):
    catalog_root = tmp_path / "catalog"
    catalog_root.mkdir()
    document = _doc(source_path="../buiten/foo.md")
    assert resolve_builtin_path(document, catalog_root=catalog_root) is None