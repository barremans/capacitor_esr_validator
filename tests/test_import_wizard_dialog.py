"""
================================================================================
Module:     tests/test_import_wizard_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.2
Datum:      2026-10-07
Auteur:     Bart Bossuyt

Doel:       GUI-regressietests voor de import-wizard. Netwerk, PDF-parsing
            en ImportService worden gemockt of in tmp_path geïsoleerd.
            Geen echte HTTP-verzoeken.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie.
  v1.0.1 (2026-10-06)  isVisible() vervangen door isHidden() voor het
                        controleren van paneelzichtbaarheid.
  v1.0.2 (2026-10-07)  Titel-voorstel bij PDF is nu bestandsnaam, niet
                        PDF-metadata /Title. Tests aangepast en één test
                        toegevoegd die expliciet bewijst dat metadata-titel
                        niet meer de initiële titel is.
================================================================================
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import app.gui.dialogs.import_wizard_dialog as wizard_module
from app.documentation.import_models import (
    ImportResult,
    ImportSource,
    ImportSourceType,
    ImportStatus,
)
from app.documentation.import_service import ImportService
from app.gui.dialogs.import_wizard_dialog import ImportWizardDialog


def _app():
    return QApplication.instance() or QApplication([])


def _maak_eenvoudige_pdf(pad: Path, *, titel: str = "Testdocument") -> Path:
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.add_metadata({"/Title": titel})
    with pad.open("wb") as handle:
        writer.write(handle)
    return pad


# ------------------------------------------------------------------ basis

def test_dialoog_opent_met_pdf_geselecteerd(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    dialog = ImportWizardDialog(taal="nl_NL", import_service=service)

    assert dialog.radio_pdf.isChecked() is True
    assert dialog.radio_url.isChecked() is False
    assert dialog.pdf_panel.isHidden() is False
    assert dialog.url_panel.isHidden() is True
    assert dialog.import_btn.isEnabled() is False


def test_type_wissel_toont_url_paneel(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    dialog = ImportWizardDialog(taal="nl_NL", import_service=service)

    dialog.radio_url.setChecked(True)

    assert dialog.url_panel.isHidden() is False
    assert dialog.pdf_panel.isHidden() is True


# ------------------------------------------------------------------ PDF kiezen

def test_kies_pdf_vult_samenvatting(tmp_path, monkeypatch):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    dialog = ImportWizardDialog(taal="nl_NL", import_service=service)

    pdf_pad = _maak_eenvoudige_pdf(tmp_path / "doc.pdf", titel="Mijn PDF")

    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        staticmethod(lambda *a, **kw: (str(pdf_pad), "PDF (*.pdf)")),
    )

    dialog._pick_pdf()

    assert dialog._pdf_pad == pdf_pad
    assert dialog._pdf_meta_titel == "Mijn PDF"
    # Nieuwe logica (v1.0.2): titel-voorstel is de bestandsnaam, niet de
    # PDF-metadata /Title. Metadata blijft zichtbaar in de samenvatting.
    assert dialog.title_edit.text() == "doc"
    assert dialog.import_btn.isEnabled() is True


def test_pdf_titel_komt_uit_bestandsnaam_niet_uit_metadata(
    tmp_path, monkeypatch
):
    """Bewijs dat PDF-metadata /Title niet meer de initiële titel is.

    Scenario: een PDF met een rommelige /Title, zoals Word die vaak
    achterlaat ("Microsoft Word - ...doc"). Het titelveld moet de
    bestandsnaam tonen, niet de metadata.
    """
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    dialog = ImportWizardDialog(taal="nl_NL", import_service=service)

    pdf_pad = _maak_eenvoudige_pdf(
        tmp_path / "CHONGCD11XSERIES.pdf",
        titel="Microsoft Word - CD11X n3-4 105.doc",
    )

    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        staticmethod(lambda *a, **kw: (str(pdf_pad), "PDF (*.pdf)")),
    )

    dialog._pick_pdf()

    assert dialog.title_edit.text() == "CHONGCD11XSERIES"
    # Metadata-titel blijft beschikbaar voor weergave in de samenvatting.
    assert dialog._pdf_meta_titel == "Microsoft Word - CD11X n3-4 105.doc"


def test_kies_ongeldige_pdf_toont_fout(tmp_path, monkeypatch):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    dialog = ImportWizardDialog(taal="nl_NL", import_service=service)

    ongeldig = tmp_path / "geen.pdf"
    ongeldig.write_text("geen pdf", encoding="utf-8")

    from PySide6.QtWidgets import QFileDialog, QMessageBox
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        staticmethod(lambda *a, **kw: (str(ongeldig), "PDF (*.pdf)")),
    )
    gewaarschuwd = {"count": 0}
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        staticmethod(
            lambda *a, **kw: gewaarschuwd.__setitem__(
                "count", gewaarschuwd["count"] + 1
            )
        ),
    )

    dialog._pick_pdf()

    assert gewaarschuwd["count"] == 1
    assert dialog._pdf_pad is None
    assert dialog.import_btn.isEnabled() is False


# ------------------------------------------------------------------ URL

def test_url_metadata_ophalen_vult_titel(tmp_path, monkeypatch):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    dialog = ImportWizardDialog(taal="nl_NL", import_service=service)
    dialog.radio_url.setChecked(True)

    from app.documentation.url_fetch import UrlMetadata
    nep_meta = UrlMetadata(
        url="https://example.com",
        fetched_at=1,
        http_status=200,
        title="Paginatitel",
        og_title=None,
    )
    monkeypatch.setattr(
        wizard_module, "fetch_url_metadata", lambda url: nep_meta
    )

    dialog.url_edit.setText("https://example.com")
    dialog._fetch_url_metadata()

    assert dialog._url == "https://example.com"
    assert dialog._url_meta is nep_meta
    assert dialog.title_edit.text() == "Paginatitel"
    assert dialog.import_btn.isEnabled() is True


def test_url_metadata_fout_toont_waarschuwing(tmp_path, monkeypatch):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    dialog = ImportWizardDialog(taal="nl_NL", import_service=service)
    dialog.radio_url.setChecked(True)
    dialog.url_edit.setText("https://example.com")

    from app.documentation.url_fetch import UrlFetchError

    def _faal(url):
        raise UrlFetchError("timeout")

    monkeypatch.setattr(wizard_module, "fetch_url_metadata", _faal)

    from PySide6.QtWidgets import QMessageBox
    gewaarschuwd = {"count": 0}
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        staticmethod(
            lambda *a, **kw: gewaarschuwd.__setitem__(
                "count", gewaarschuwd["count"] + 1
            )
        ),
    )

    dialog._fetch_url_metadata()

    assert gewaarschuwd["count"] == 1
    assert dialog._url_meta is None
    assert dialog.import_btn.isEnabled() is False


# ------------------------------------------------------------------ importeren

def test_importeren_pdf_emit_signal(tmp_path, monkeypatch):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    dialog = ImportWizardDialog(taal="nl_NL", import_service=service)

    pdf_pad = _maak_eenvoudige_pdf(tmp_path / "doc.pdf", titel="Mijn PDF")

    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        staticmethod(lambda *a, **kw: (str(pdf_pad), "PDF (*.pdf)")),
    )
    dialog._pick_pdf()

    ontvangen = {"source_id": None}
    dialog.import_completed.connect(
        lambda sid: ontvangen.__setitem__("source_id", sid)
    )

    dialog._perform_import()

    assert ontvangen["source_id"] is not None
    assert len(service.list_sources()) == 1


def test_importeren_fout_toont_waarschuwing(tmp_path, monkeypatch):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    dialog = ImportWizardDialog(taal="nl_NL", import_service=service)

    pdf_pad = _maak_eenvoudige_pdf(tmp_path / "doc.pdf")
    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        staticmethod(lambda *a, **kw: (str(pdf_pad), "PDF (*.pdf)")),
    )
    dialog._pick_pdf()

    from app.documentation.pdf_extract import PdfExtractError

    def _faal(*a, **kw):
        raise PdfExtractError("test-fout")

    monkeypatch.setattr(wizard_module, "import_pdf", _faal)

    from PySide6.QtWidgets import QMessageBox
    gewaarschuwd = {"count": 0}
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        staticmethod(
            lambda *a, **kw: gewaarschuwd.__setitem__(
                "count", gewaarschuwd["count"] + 1
            )
        ),
    )

    dialog._perform_import()

    assert gewaarschuwd["count"] == 1
    assert len(service.list_sources()) == 0


# ------------------------------------------------------------------ taalwissel

def test_titels_komen_uit_i18n(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    dialog_nl = ImportWizardDialog(taal="nl_NL", import_service=service)
    dialog_en = ImportWizardDialog(taal="en_US", import_service=service)

    assert dialog_nl.radio_pdf.text() == "PDF-bestand"
    assert dialog_en.radio_pdf.text() == "PDF file"
    assert dialog_nl.cancel_btn.text() == "Annuleren"
    assert dialog_en.cancel_btn.text() == "Cancel"