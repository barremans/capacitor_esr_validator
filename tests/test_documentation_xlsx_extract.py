"""
================================================================================
Module:     tests/test_documentation_xlsx_extract.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.1
Datum:      2026-10-09
Auteur:     Bart Bossuyt

Doel:       Regressietests voor xlsx_extract: metadata, celinhoud,
            hashing, kopiëren naar sources/ en de .oud-rollback-helpers.

Wijzigingen:
  v1.0.0 (2026-10-09)  Eerste versie (fase 6A).
  v1.0.1 (2026-10-09)  Fix testhelper _maak_xlsx: Workbook-object
                       ondersteunt geen __setitem__; cellen moeten via
                       wb.active (of een specifiek werkblad) worden gezet.
================================================================================
"""

from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import Workbook

from app.documentation.xlsx_extract import (
    XlsxExtractError,
    XlsxMetadata,
    compute_file_hash,
    copy_xlsx_to_sources,
    extract_xlsx_metadata,
    extract_xlsx_text,
    rename_existing_xlsx_to_old,
    restore_old_xlsx,
)


def _maak_xlsx(
    pad: Path,
    *,
    titel: str = "Testwerkmap",
    auteur: str = "Tester",
    bladen: tuple[str, ...] = ("Blad1",),
) -> Path:
    wb = Workbook()
    # Eerste blad hernoemen naar bladen[0]
    eerste_blad = wb.active
    eerste_blad.title = bladen[0]
    # Cellen op het eerste blad zetten (Workbook-object zelf
    # ondersteunt geen __setitem__).
    eerste_blad["A1"] = "Waarde 1"
    eerste_blad["B1"] = 42

    for extra in bladen[1:]:
        wb.create_sheet(extra)

    wb.properties.title = titel
    wb.properties.creator = auteur
    wb.save(str(pad))
    return pad


# ---------------------------------------------------------------- metadata

def test_extract_metadata_gelukkig(tmp_path):
    pad = _maak_xlsx(tmp_path / "doc.xlsx")
    meta = extract_xlsx_metadata(pad)

    assert isinstance(meta, XlsxMetadata)
    assert meta.sheet_count == 1
    assert meta.sheet_names == ("Blad1",)
    assert meta.title == "Testwerkmap"
    assert meta.author == "Tester"


def test_extract_metadata_meerdere_bladen(tmp_path):
    pad = _maak_xlsx(tmp_path / "doc.xlsx", bladen=("A", "B", "C"))
    meta = extract_xlsx_metadata(pad)
    assert meta.sheet_count == 3
    assert meta.sheet_names == ("A", "B", "C")


def test_extract_metadata_ontbrekend_bestand(tmp_path):
    with pytest.raises(XlsxExtractError):
        extract_xlsx_metadata(tmp_path / "bestaat-niet.xlsx")


def test_extract_metadata_geen_bestand(tmp_path):
    map_pad = tmp_path / "map"
    map_pad.mkdir()
    with pytest.raises(XlsxExtractError):
        extract_xlsx_metadata(map_pad)


def test_extract_metadata_corrupt_bestand(tmp_path):
    ongeldig = tmp_path / "kapot.xlsx"
    ongeldig.write_text("geen xlsx", encoding="utf-8")
    with pytest.raises(XlsxExtractError):
        extract_xlsx_metadata(ongeldig)


# ---------------------------------------------------------------- tekst

def test_extract_text_gelukkig(tmp_path):
    pad = _maak_xlsx(tmp_path / "doc.xlsx")
    tekst = extract_xlsx_text(pad)
    assert "Waarde 1" in tekst
    assert "42" in tekst
    assert "# Blad1" in tekst


def test_extract_text_meerdere_bladen(tmp_path):
    pad = _maak_xlsx(tmp_path / "doc.xlsx", bladen=("A", "B"))
    tekst = extract_xlsx_text(pad)
    assert "# A" in tekst
    assert "# B" in tekst


def test_extract_text_ontbrekend_bestand(tmp_path):
    with pytest.raises(XlsxExtractError):
        extract_xlsx_text(tmp_path / "bestaat-niet.xlsx")


# ---------------------------------------------------------------- hash

def test_compute_hash_deterministisch(tmp_path):
    pad = _maak_xlsx(tmp_path / "doc.xlsx")
    h1 = compute_file_hash(pad)
    h2 = compute_file_hash(pad)
    assert h1 == h2
    assert len(h1) == 64


# ---------------------------------------------------------------- kopiëren

def test_copy_naar_sources(tmp_path):
    pad = _maak_xlsx(tmp_path / "doc.xlsx")
    sources = tmp_path / "sources"

    doel = copy_xlsx_to_sources(pad, "source-1", sources_dir=sources)
    assert doel.exists()
    assert doel.name == "source-1.xlsx"


def test_copy_weigert_bestaand_doel(tmp_path):
    pad = _maak_xlsx(tmp_path / "doc.xlsx")
    sources = tmp_path / "sources"
    sources.mkdir()
    (sources / "source-1.xlsx").write_text("bezet", encoding="utf-8")

    with pytest.raises(XlsxExtractError):
        copy_xlsx_to_sources(pad, "source-1", sources_dir=sources)


# ---------------------------------------------------------------- rollback

def test_rename_naar_oud(tmp_path):
    pad = _maak_xlsx(tmp_path / "doc.xlsx")
    oud = rename_existing_xlsx_to_old(pad, timestamp="20261009")
    assert oud is not None
    assert oud.exists()
    assert not pad.exists()


def test_restore_old(tmp_path):
    pad = _maak_xlsx(tmp_path / "doc.xlsx")
    oud = rename_existing_xlsx_to_old(pad, timestamp="20261009")
    assert oud is not None

    restore_old_xlsx(oud, pad)
    assert pad.exists()
    assert not oud.exists()