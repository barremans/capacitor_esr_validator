"""
================================================================================
Module:     tests/test_import_wizard_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-07
Auteur:     Bart Bossuyt

Doel:       GUI-regressietests voor de import-wizard. Netwerk, PDF-parsing
            en ImportService worden gemockt of in tmp_path geïsoleerd.
            Geen echte HTTP-verzoeken. Sinds v1.1.0 ook tests voor de
            duplicate-popup-flow (fase 5D'.2a).

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie.
  v1.0.1 (2026-10-06)  isVisible() vervangen door isHidden().
  v1.0.2 (2026-10-07)  Titel-voorstel bij PDF is nu bestandsnaam.
  v1.1.0 (2026-10-07)  Tests voor duplicate-popup: match gevonden,
                        KEEP/OVERWRITE-keuze, annuleren.
================================================================================
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import app.gui.dialogs.import_wizard_dialog as wizard_module
from app.documentation.import_models import (
    DuplicateAction,
    DuplicateMatch,
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
    assert dialog.title_edit.text() == "doc"
    assert dialog.import_btn.isEnabled() is True
    # Hash wordt nu ook berekend bij PDF-keuze
    assert dialog._pdf_hash is not None


def test_pdf_titel_komt_uit_bestandsnaam_niet_uit_metadata(
    tmp_path, monkeypatch
):
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


# ============================================================================
# NIEUW IN v1.1.0 — duplicate-popup-flow
# ============================================================================

def _maak_match(
    *,
    source_type: ImportSourceType = ImportSourceType.PDF,
    match_type: str = "file_hash",
) -> DuplicateMatch:
    if source_type is ImportSourceType.PDF:
        bestaande = ImportSource(
            source_id="abc-123",
            source_type=ImportSourceType.PDF,
            title="Bestaand document",
            imported_at=1_700_000_000_000,
            imported_by="tester",
            status=ImportStatus.CONCEPT,
            original_filename="oud.pdf",
            file_hash="deadbeef",
        )
    else:
        bestaande = ImportSource(
            source_id="abc-456",
            source_type=ImportSourceType.URL,
            title="Bestaande URL",
            imported_at=1_700_000_000_000,
            imported_by="tester",
            status=ImportStatus.CONCEPT,
            source_url="https://example.com",
        )
    return DuplicateMatch(bestaande=bestaande, match_type=match_type)


def test_duplicate_check_geen_match_voor_pdf_zonder_keuze(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    dialog = ImportWizardDialog(taal="nl_NL", import_service=service)
    assert dialog._check_duplicate() is None


def test_duplicate_check_vindt_bestaande_pdf(tmp_path, monkeypatch):
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

    # Registreer dezelfde PDF eerst in de service.
    from app.documentation.pdf_import import import_pdf
    import_pdf(
        pdf_pad,
        import_service=service,
        sources_dir=tmp_path / "sources",
    )

    match = dialog._check_duplicate()
    assert match is not None
    assert match.match_type == "file_hash"


def test_wizard_keep_bij_match_doet_niets(tmp_path, monkeypatch):
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

    from app.documentation.pdf_import import import_pdf
    eerste = import_pdf(
        pdf_pad,
        import_service=service,
        sources_dir=tmp_path / "sources",
    )
    aantal_voor = len(service.list_sources())

    # Simuleer KEEP-keuze in de popup.
    from app.gui.dialogs import duplicate_source_dialog as dup_module
    monkeypatch.setattr(
        dup_module.DuplicateSourceDialog,
        "vraag_actie",
        staticmethod(lambda **kw: DuplicateAction.KEEP),
    )

    dialog._perform_import()

    # Niets gewijzigd
    assert len(service.list_sources()) == aantal_voor
    assert service.get(eerste.source.source_id).status is ImportStatus.CONCEPT


def test_wizard_annuleren_in_popup_doet_niets(tmp_path, monkeypatch):
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

    from app.documentation.pdf_import import import_pdf
    import_pdf(
        pdf_pad,
        import_service=service,
        sources_dir=tmp_path / "sources",
    )
    aantal_voor = len(service.list_sources())

    from app.gui.dialogs import duplicate_source_dialog as dup_module
    monkeypatch.setattr(
        dup_module.DuplicateSourceDialog,
        "vraag_actie",
        staticmethod(lambda **kw: None),
    )

    dialog._perform_import()

    assert len(service.list_sources()) == aantal_voor


def test_wizard_overwrite_bij_match(tmp_path, monkeypatch):
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

    from app.documentation.pdf_import import import_pdf
    eerste = import_pdf(
        pdf_pad,
        import_service=service,
        sources_dir=tmp_path / "sources",
    )

    from app.gui.dialogs import duplicate_source_dialog as dup_module
    monkeypatch.setattr(
        dup_module.DuplicateSourceDialog,
        "vraag_actie",
        staticmethod(lambda **kw: DuplicateAction.OVERWRITE),
    )

    ontvangen = {"source_id": None}
    dialog.import_completed.connect(
        lambda sid: ontvangen.__setitem__("source_id", sid)
    )

    dialog._perform_import()

    assert ontvangen["source_id"] == eerste.source.source_id
    assert len(service.list_sources()) == 1