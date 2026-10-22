"""
================================================================================
Module:     tests/test_documentation_extraction_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-22
Auteur:     Bart Bossuyt

Doel:       Regressietests voor app/documentation/extraction_service.py
            (fase 12A.2). Geen netwerk: URL-tests werken met een
            HTML-string of een tijdelijke snapshot. Geen Qt.

Wijzigingen:
  v1.0.0 (2026-10-22)  Eerste versie.
================================================================================
"""

from __future__ import annotations

from pathlib import Path

import pytest
from docx import Document
from openpyxl import Workbook

from app.documentation.extraction_models import (
    ExtractionError,
    ExtractionResult,
    ExtractionSourceKind,
)
from app.documentation.extraction_service import (
    extract_for_path,
    extract_for_source,
    extract_for_url,
)
from app.documentation.import_models import (
    ImportSource,
    ImportSourceType,
    ImportStatus,
)


# ------------------------------------------------------------------ hulpfuncties

def _maak_pdf(pad: Path, *, met_tekst: bool = True) -> Path:
    """Minimale PDF. Met tekst als pypdf een string kan insluiten."""
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.add_metadata({"/Title": "Test-PDF", "/Author": "Tester"})
    with pad.open("wb") as handle:
        writer.write(handle)
    return pad


def _maak_docx(pad: Path) -> Path:
    document = Document()
    document.add_paragraph("Eerste paragraaf.")
    document.add_paragraph("Tweede paragraaf.")
    document.core_properties.title = "Test-DOCX"
    document.core_properties.author = "Tester"
    document.save(str(pad))
    return pad


def _maak_xlsx(pad: Path) -> Path:
    wb = Workbook()
    eerste = wb.active
    eerste.title = "Blad1"
    eerste["A1"] = "Waarde 1"
    eerste["B1"] = 42
    wb.properties.title = "Test-XLSX"
    wb.properties.creator = "Tester"
    wb.save(str(pad))
    return pad


def _maak_source(
    *,
    source_id: str,
    source_type: ImportSourceType,
    source_url: str | None = None,
    original_filename: str | None = None,
) -> ImportSource:
    return ImportSource(
        source_id=source_id,
        source_type=source_type,
        title="Testbron",
        imported_at=1,
        imported_by="tester",
        status=ImportStatus.CONCEPT,
        original_filename=original_filename,
        source_url=source_url,
    )


# ------------------------------------------------------------------ PDF

def test_pdf_gelukkig_pad(tmp_path):
    pad = _maak_pdf(tmp_path / "doc.pdf")

    result = extract_for_path(
        pad, source_kind=ExtractionSourceKind.PDF
    )

    assert isinstance(result, ExtractionResult)
    assert result.source_kind is ExtractionSourceKind.PDF
    assert result.metadata["title"] == "Test-PDF"
    assert result.metadata["author"] == "Tester"
    assert result.metadata["page_count"] == 1
    # Een blanco pagina levert lege tekst, dus een waarschuwing.
    assert result.is_empty is True
    assert any("ingescand" in w for w in result.warnings)
    # Paginascheiding: één pagina.
    assert len(result.pages) == 1


def test_pdf_ontbrekend_faalt(tmp_path):
    with pytest.raises(ExtractionError):
        extract_for_path(
            tmp_path / "bestaat-niet.pdf",
            source_kind=ExtractionSourceKind.PDF,
        )


# ------------------------------------------------------------------ DOCX

def test_docx_gelukkig_pad(tmp_path):
    pad = _maak_docx(tmp_path / "doc.docx")

    result = extract_for_path(
        pad, source_kind=ExtractionSourceKind.DOCX
    )

    assert result.source_kind is ExtractionSourceKind.DOCX
    assert "Eerste paragraaf." in result.text
    assert "Tweede paragraaf." in result.text
    assert result.metadata["title"] == "Test-DOCX"
    assert result.metadata["paragraph_count"] == 2
    assert result.pages == ()
    assert result.is_empty is False


def test_docx_ontbrekend_faalt(tmp_path):
    with pytest.raises(ExtractionError):
        extract_for_path(
            tmp_path / "bestaat-niet.docx",
            source_kind=ExtractionSourceKind.DOCX,
        )


# ------------------------------------------------------------------ XLSX

def test_xlsx_gelukkig_pad(tmp_path):
    pad = _maak_xlsx(tmp_path / "doc.xlsx")

    result = extract_for_path(
        pad, source_kind=ExtractionSourceKind.XLSX
    )

    assert result.source_kind is ExtractionSourceKind.XLSX
    assert "Waarde 1" in result.text
    assert "42" in result.text
    assert "# Blad1" in result.text
    assert result.metadata["sheet_names"] == ["Blad1"]
    assert result.metadata["sheet_count"] == 1
    assert result.pages == ()
    assert result.is_empty is False


def test_xlsx_ontbrekend_faalt(tmp_path):
    with pytest.raises(ExtractionError):
        extract_for_path(
            tmp_path / "bestaat-niet.xlsx",
            source_kind=ExtractionSourceKind.XLSX,
        )


# ------------------------------------------------------------------ URL

def test_url_met_html_string():
    html = (
        "<html lang='nl'><head><title>Paginatitel</title></head>"
        "<body><h1>Kop</h1><p>Eerste alinea.</p><p>Tweede alinea.</p>"
        "</body></html>"
    )

    result = extract_for_url(url="https://example.com/p", html=html)

    assert result.source_kind is ExtractionSourceKind.URL
    assert "Kop" in result.text
    assert "Eerste alinea." in result.text
    assert "Tweede alinea." in result.text
    assert result.metadata["title"] == "Paginatitel"
    assert result.metadata["language"] == "nl"
    assert result.metadata["url"] == "https://example.com/p"
    assert result.pages == ()


def test_url_met_snapshot_pad(tmp_path):
    snapshots = tmp_path / "snaps"
    snapshots.mkdir()
    snapshot = snapshots / "src-1.html"
    snapshot.write_text(
        "<html><body><p>Uit snapshot.</p></body></html>",
        encoding="utf-8",
    )

    result = extract_for_url(
        url="https://example.com/x",
        snapshot_pad=snapshot,
        source_id="src-1",
    )

    assert "Uit snapshot." in result.text
    assert result.source_id == "src-1"


def test_url_snapshot_ontbreekt_faalt(tmp_path):
    with pytest.raises(ExtractionError):
        extract_for_url(
            url="https://example.com/x",
            snapshot_pad=tmp_path / "bestaat-niet.html",
        )


def test_url_lege_html_geeft_waarschuwing():
    result = extract_for_url(
        url="https://example.com/leeg",
        html="<html><body></body></html>",
    )

    assert result.is_empty is True
    assert any("geen herkenbare tekst" in w for w in result.warnings)


def test_url_script_en_style_worden_verwijderd():
    html = (
        "<html><body>"
        "<script>var x = 1;</script>"
        "<style>.a { color: red; }</style>"
        "<p>Zichtbaar</p>"
        "</body></html>"
    )
    result = extract_for_url(url="https://example.com/p", html=html)

    assert "Zichtbaar" in result.text
    assert "var x" not in result.text
    assert "color: red" not in result.text


def test_url_zowel_html_als_snapshot_faalt(tmp_path):
    snapshot = tmp_path / "snap.html"
    snapshot.write_text("<html></html>", encoding="utf-8")

    with pytest.raises(ExtractionError):
        extract_for_url(
            url="https://example.com/x",
            html="<html></html>",
            snapshot_pad=snapshot,
        )


def test_url_zonder_html_en_zonder_snapshot_faalt():
    with pytest.raises(ExtractionError):
        extract_for_url(url="https://example.com/x")


def test_url_lege_url_faalt():
    with pytest.raises(ExtractionError):
        extract_for_url(url="", html="<html></html>")


# ------------------------------------------------------------------ extract_for_path validatie

def test_extract_for_path_url_faalt():
    with pytest.raises(ExtractionError):
        extract_for_path(
            Path("x.pdf"), source_kind=ExtractionSourceKind.URL
        )


# ------------------------------------------------------------------ extract_for_source

def test_source_pdf_leest_uit_sources_dir(tmp_path):
    sources = tmp_path / "sources"
    sources.mkdir()
    bron = _maak_pdf(sources / "src-1.pdf")

    source = _maak_source(
        source_id="src-1",
        source_type=ImportSourceType.PDF,
        original_filename=bron.name,
    )

    result = extract_for_source(source, sources_dir=sources)

    assert result.source_kind is ExtractionSourceKind.PDF
    assert result.source_id == "src-1"
    assert result.metadata["title"] == "Test-PDF"


def test_source_docx_leest_uit_sources_dir(tmp_path):
    sources = tmp_path / "sources"
    sources.mkdir()
    bron = _maak_docx(sources / "src-2.docx")

    source = _maak_source(
        source_id="src-2",
        source_type=ImportSourceType.DOCX,
        original_filename=bron.name,
    )

    result = extract_for_source(source, sources_dir=sources)

    assert result.source_kind is ExtractionSourceKind.DOCX
    assert "Eerste paragraaf." in result.text


def test_source_xlsx_leest_uit_sources_dir(tmp_path):
    sources = tmp_path / "sources"
    sources.mkdir()
    bron = _maak_xlsx(sources / "src-3.xlsx")

    source = _maak_source(
        source_id="src-3",
        source_type=ImportSourceType.XLSX,
        original_filename=bron.name,
    )

    result = extract_for_source(source, sources_dir=sources)

    assert result.source_kind is ExtractionSourceKind.XLSX
    assert "Waarde 1" in result.text


def test_source_url_leest_snapshot(tmp_path):
    snapshots = tmp_path / "snaps"
    snapshots.mkdir()
    (snapshots / "src-4.html").write_text(
        "<html><body><p>Snapshot-tekst.</p></body></html>",
        encoding="utf-8",
    )

    source = _maak_source(
        source_id="src-4",
        source_type=ImportSourceType.URL,
        source_url="https://example.com/p",
    )

    result = extract_for_source(source, snapshots_dir=snapshots)

    assert result.source_kind is ExtractionSourceKind.URL
    assert "Snapshot-tekst." in result.text
    assert result.source_id == "src-4"


def test_source_pdf_ontbrekend_faalt(tmp_path):
    sources = tmp_path / "sources"
    sources.mkdir()
    source = _maak_source(
        source_id="src-x",
        source_type=ImportSourceType.PDF,
        original_filename="doc.pdf",
    )

    with pytest.raises(ExtractionError):
        extract_for_source(source, sources_dir=sources)


def test_source_url_zonder_source_url_faalt(tmp_path):
    # ImportSource staat geen URL-bron zonder source_url toe; we bouwen
    # het object daarom via __post_init__-omzeiling en controleren dat
    # extract_for_source alsnog weigert.
    source = _maak_source(
        source_id="src-x",
        source_type=ImportSourceType.PDF,
        original_filename="doc.pdf",
    )
    # We kunnen geen geldige URL-bron zonder source_url maken; dat is
    # precies de bedoeling van de ImportSource-validatie. Deze test
    # documenteert dat extract_for_source daar niet omheen werkt.
    object.__setattr__(source, "source_type", ImportSourceType.URL)
    object.__setattr__(source, "original_filename", None)

    with pytest.raises(ExtractionError):
        extract_for_source(source)


def test_source_ongeldig_type_faalt():
    with pytest.raises(ExtractionError):
        extract_for_source("geen-importsource")  # type: ignore[arg-type]