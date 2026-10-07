"""
================================================================================
Module:     app/helpers/document_source_paths.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-07
Auteur:     Bart Bossuyt

Doel:       GUI-onafhankelijke helper om het type en het pad van een
            documentbron te bepalen. Wordt gebruikt door de documentatie-
            viewer (fase 5D'.4) om te beslissen of een document intern
            wordt getoond (Markdown/tekst) of extern wordt geopend
            (PDF, Word, Excel, URL-snapshot).

            Geen Qt, geen netwerk. Alleen pathlib/os. De aanroeper geeft
            de roots mee zodat deze helper geen import-cycles veroorzaakt
            en eenvoudig testbaar blijft.

Wijzigingen:
  v1.0.0 (2026-10-07)  Eerste versie: source_kind, resolve_local_path,
                       resolve_builtin_path.
================================================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.documentation.models import DocumentMetadata, DocumentSourceType


# Extensies die de interne viewer kan tonen.
_MARKDOWN_EXTENSIONS = frozenset({".md", ".txt"})
_PDF_EXTENSIONS = frozenset({".pdf"})
_WORD_EXTENSIONS = frozenset({".docx", ".doc"})
_EXCEL_EXTENSIONS = frozenset({".xlsx", ".xls"})


def source_kind(document: DocumentMetadata) -> str:
    """Bepaal het type bron voor de viewer.

    Retourneert één van:
      - "markdown"  : .md of .txt — interne viewer
      - "pdf"       : .pdf — extern openen
      - "word"      : .docx of .doc — extern openen
      - "excel"     : .xlsx of .xls — extern openen
      - "url"       : URL-bron zonder lokaal bestand — snapshot of live URL
      - "onbekend"  : geen herkenbaar type
    """

    if document.source_type is DocumentSourceType.URL:
        return "url"

    path_str = document.source_path
    if not path_str:
        # FILE of FILE_AND_URL zonder source_path: niets om te openen.
        return "onbekend"

    suffix = Path(path_str).suffix.lower()
    if suffix in _MARKDOWN_EXTENSIONS:
        return "markdown"
    if suffix in _PDF_EXTENSIONS:
        return "pdf"
    if suffix in _WORD_EXTENSIONS:
        return "word"
    if suffix in _EXCEL_EXTENSIONS:
        return "excel"
    return "onbekend"


def _resolve_bronbestand(
    document: DocumentMetadata,
    *,
    sources_root: Optional[Path],
) -> Optional[Path]:
    """Bepaal het absolute pad van een bronbestand in sources/.

    Alleen voor paden met vorm ``sources/<bestandsnaam>``. Retourneert
    None als sources_root ontbreekt of het bestand niet bestaat.
    """
    if sources_root is None or not document.source_path:
        return None

    source_path = Path(document.source_path)
    if source_path.parts[:1] != ("sources",):
        return None

    bestand = Path(sources_root) / source_path.name
    if not bestand.is_file():
        return None
    return bestand


def _resolve_snapshot(
    document: DocumentMetadata,
    *,
    snapshots_root: Optional[Path],
) -> Optional[Path]:
    """Bepaal het absolute pad van een URL-snapshot.

    Alleen voor URL-bronnen. Retourneert None als snapshots_root ontbreekt
    of de snapshot niet bestaat.
    """
    if snapshots_root is None:
        return None
    if document.source_type is not DocumentSourceType.URL:
        return None

    snapshot = Path(snapshots_root) / f"{document.document_id}.html"
    if not snapshot.is_file():
        return None
    return snapshot


def resolve_local_path(
    document: DocumentMetadata,
    *,
    sources_root: Optional[Path] = None,
    snapshots_root: Optional[Path] = None,
) -> Optional[Path]:
    """Bepaal het absolute pad van een geïmporteerde bron.

    Voor PDF/Word/Excel: bestand onder sources_root.
    Voor URL: snapshot onder snapshots_root als die bestaat.
    Voor interne Markdown (.md/.txt): None — gebruik
        resolve_builtin_path() voor die gevallen.

    Retourneert None als geen lokaal bestand gevonden is.
    """

    kind = source_kind(document)
    if kind in ("pdf", "word", "excel"):
        return _resolve_bronbestand(document, sources_root=sources_root)
    if kind == "url":
        return _resolve_snapshot(document, snapshots_root=snapshots_root)
    return None


def resolve_builtin_path(
    document: DocumentMetadata,
    *,
    catalog_root: Optional[Path],
) -> Optional[Path]:
    """Bepaal het absolute pad van een ingebouwde Markdown/tekst-bron.

    Alleen voor relatieve paden onder de ingebouwde catalogus-root.
    Retourneert None als catalog_root ontbreekt, het pad absoluut is,
    of het bestand niet bestaat.
    """

    if catalog_root is None or not document.source_path:
        return None

    source_path = Path(document.source_path)
    if source_path.is_absolute():
        return None

    try:
        kandidaat = (Path(catalog_root) / source_path).resolve()
    except (OSError, ValueError):
        return None

    try:
        kandidaat.relative_to(Path(catalog_root).resolve())
    except ValueError:
        return None

    if not kandidaat.is_file():
        return None
    return kandidaat