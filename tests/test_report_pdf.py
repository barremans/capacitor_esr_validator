"""
================================================================================
Module:     tests/test_report_pdf.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-10
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de Qt-specifieke PDF-export.

Wijzigingen:
  v1.0.0 (2026-10-10)  Eerste versie: bestand wordt aangemaakt, is niet
                        leeg, en bevat een PDF-header.
================================================================================
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from app.helpers.report_pdf import write_html_to_pdf


@pytest.fixture(scope="module", autouse=True)
def qapplication():
    app = QApplication.instance() or QApplication([])
    yield app


def _minimale_html() -> str:
    return (
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\">"
        "<title>Test</title></head><body>"
        "<h1>Meetrapport</h1><p>Testinhoud.</p>"
        "</body></html>"
    )


def test_write_html_to_pdf_maakt_bestand(tmp_path):
    doel = tmp_path / "rapport.pdf"
    resultaat = write_html_to_pdf(_minimale_html(), doel, titel="Testrapport")

    assert resultaat == doel
    assert doel.exists()
    assert doel.stat().st_size > 0


def test_write_html_to_pdf_heeft_pdf_header(tmp_path):
    doel = tmp_path / "rapport.pdf"
    write_html_to_pdf(_minimale_html(), doel, titel="Testrapport")

    with doel.open("rb") as f:
        header = f.read(5)

    assert header == b"%PDF-"


def test_write_html_to_pdf_redelijke_grootte(tmp_path):
    doel = tmp_path / "rapport.pdf"
    write_html_to_pdf(_minimale_html(), doel, titel="Testrapport")

    # Een minimale A4-pagina is typisch 1-10 kB.
    assert 500 < doel.stat().st_size < 100_000


def test_write_html_to_pdf_weigert_lege_html(tmp_path):
    doel = tmp_path / "rapport.pdf"

    with pytest.raises(ValueError):
        write_html_to_pdf("", doel)


def test_write_html_to_pdf_weigert_lege_string(tmp_path):
    doel = tmp_path / "rapport.pdf"

    with pytest.raises(ValueError):
        write_html_to_pdf("   ", doel)


def test_write_html_to_pdf_weigert_leeg_pad():
    with pytest.raises(ValueError):
        write_html_to_pdf(_minimale_html(), "")


def test_write_html_to_pdf_accepteert_path_object(tmp_path):
    doel = tmp_path / "rapport.pdf"
    resultaat = write_html_to_pdf(_minimale_html(), doel)

    assert isinstance(resultaat, type(doel))
    assert resultaat.exists()