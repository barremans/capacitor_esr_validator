"""
================================================================================
Module:     tests/test_documentation_pdf_extract.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-06
Auteur:     Bart Bossuyt

Doel:       Regressietests voor pdf_extract: metadata, tekstextractie,
            SHA-256, kopiëren naar bronmap, foutpaden.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie.
================================================================================
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from app.documentation.pdf_extract import (
    PdfExtractError,
    PdfMetadata,
    compute_file_hash,
    copy_pdf_to_sources,
    extract_pdf_metadata,
    extract_pdf_text,
)


# ------------------------------------------------------------------ test-PDF's

def _maak_eenvoudige_pdf(pad: Path, *, tekst: str = "Hallo ESR-wereld") -> Path:
    """Maak een minimale geldige PDF met pypdf's eigen writer."""
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    # Voeg metadata toe
    writer.add_metadata({
        "/Title": "Testdocument",
        "/Author": "Testauteur",
        "/Subject": "Testonderwerp",
    })
    # pypdf kan geen tekst toevoegen aan een blanco pagina; voor de
    # tekstextractietest gebruiken we daarom een tweede PDF hieronder.
    with pad.open("wb") as handle:
        writer.write(handle)
    return pad


def _maak_pdf_met_tekst(pad: Path, *, tekst: str = "Hallo ESR-wereld") -> Path:
    """Maak een PDF met echte tekst door een minimale PDF-bytes op te bouwen.

    Gebruikt reportlab niet (niet in requirements); bouwt de PDF handmatig
    op met eenvoudige content-stream. pypdf kan dit lezen en de tekst
    terugvinden.
    """
    inhoud_stream = f"BT /F1 24 Tf 50 100 Td ({tekst}) Tj ET".encode("latin-1")
    lengte = len(inhoud_stream)

    objecten = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(lengte).encode() + b" >>\nstream\n"
        + inhoud_stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objecten, start=1):
        offsets.append(len(output))
        output += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"

    xref_offset = len(output)
    output += f"xref\n0 {len(objecten) + 1}\n".encode()
    output += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        output += f"{off:010d} 00000 n \n".encode()
    output += (
        f"trailer\n<< /Size {len(objecten) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode()

    pad.write_bytes(bytes(output))
    return pad


# ------------------------------------------------------------------ metadata

def test_metadata_van_geldige_pdf(tmp_path):
    pad = _maak_eenvoudige_pdf(tmp_path / "test.pdf")
    meta = extract_pdf_metadata(pad)
    assert isinstance(meta, PdfMetadata)
    assert meta.page_count == 1
    assert meta.title == "Testdocument"
    assert meta.author == "Testauteur"
    assert meta.subject == "Testonderwerp"
    assert meta.is_encrypted is False


def test_metadata_van_ontbrekend_bestand_faalt(tmp_path):
    with pytest.raises(PdfExtractError):
        extract_pdf_metadata(tmp_path / "bestaat-niet.pdf")


def test_metadata_van_map_faalt(tmp_path):
    map_pad = tmp_path / "map"
    map_pad.mkdir()
    with pytest.raises(PdfExtractError):
        extract_pdf_metadata(map_pad)


def test_metadata_van_geen_pdf_faalt(tmp_path):
    pad = tmp_path / "geen.pdf"
    pad.write_text("dit is geen pdf", encoding="utf-8")
    with pytest.raises(PdfExtractError):
        extract_pdf_metadata(pad)


# ------------------------------------------------------------------ tekst

def test_tekstextractie_van_pdf_met_tekst(tmp_path):
    pad = _maak_pdf_met_tekst(tmp_path / "tekst.pdf", tekst="Hallo ESR")
    tekst = extract_pdf_text(pad)
    assert "Hallo ESR" in tekst


def test_tekstextractie_van_lege_pdf_geeft_lege_string(tmp_path):
    pad = _maak_eenvoudige_pdf(tmp_path / "leeg.pdf")
    tekst = extract_pdf_text(pad)
    # Blanco pagina → tekst is leeg of alleen whitespace
    assert tekst.strip() == ""


def test_tekstextractie_van_ontbrekend_bestand_faalt(tmp_path):
    with pytest.raises(PdfExtractError):
        extract_pdf_text(tmp_path / "bestaat-niet.pdf")


def test_tekstextractie_van_onleesbare_pdf_faalt(tmp_path):
    pad = tmp_path / "kapot.pdf"
    pad.write_bytes(b"%PDF-1.4\nniet echt een pdf")
    with pytest.raises(PdfExtractError):
        extract_pdf_text(pad)


# ------------------------------------------------------------------ hash

def test_hash_is_sha256_van_inhoud(tmp_path):
    pad = tmp_path / "x.pdf"
    inhoud = b"hallo wereld"
    pad.write_bytes(inhoud)
    verwacht = hashlib.sha256(inhoud).hexdigest()
    assert compute_file_hash(pad) == verwacht


def test_hash_stabiel_bij_herberekenen(tmp_path):
    pad = tmp_path / "x.pdf"
    pad.write_bytes(b"abc" * 1000)
    assert compute_file_hash(pad) == compute_file_hash(pad)


def test_hash_van_ontbrekend_bestand_faalt(tmp_path):
    with pytest.raises(PdfExtractError):
        compute_file_hash(tmp_path / "bestaat-niet.pdf")


# ------------------------------------------------------------------ kopiëren

def test_kopieer_naar_sources_map(tmp_path):
    bron = _maak_eenvoudige_pdf(tmp_path / "bron.pdf")
    sources = tmp_path / "sources"

    doel = copy_pdf_to_sources(bron, "src-abc", sources_dir=sources)

    assert doel.exists()
    assert doel.name == "src-abc.pdf"
    assert doel.read_bytes() == bron.read_bytes()


def test_kopieer_weigert_bestaand_doel(tmp_path):
    bron = _maak_eenvoudige_pdf(tmp_path / "bron.pdf")
    sources = tmp_path / "sources"

    copy_pdf_to_sources(bron, "src-abc", sources_dir=sources)
    with pytest.raises(PdfExtractError):
        copy_pdf_to_sources(bron, "src-abc", sources_dir=sources)


def test_kopieer_van_ontbrekend_bestand_faalt(tmp_path):
    with pytest.raises(PdfExtractError):
        copy_pdf_to_sources(
            tmp_path / "bestaat-niet.pdf",
            "src-abc",
            sources_dir=tmp_path / "sources",
        )


def test_kopieer_met_lege_source_id_faalt(tmp_path):
    bron = _maak_eenvoudige_pdf(tmp_path / "bron.pdf")
    with pytest.raises(PdfExtractError):
        copy_pdf_to_sources(bron, "", sources_dir=tmp_path / "sources")


def test_kopieer_maakt_sources_map_aan(tmp_path):
    bron = _maak_eenvoudige_pdf(tmp_path / "bron.pdf")
    sources = tmp_path / "diep" / "genest" / "sources"
    assert not sources.exists()
    copy_pdf_to_sources(bron, "src-1", sources_dir=sources)
    assert sources.exists()