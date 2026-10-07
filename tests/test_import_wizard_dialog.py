"""
================================================================================
Module:     tests/test_import_wizard_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.2.1
Datum:      2026-10-07
Auteur:     Bart Bossuyt

Doel:       GUI-regressietests voor de import-wizard. Netwerk, PDF-parsing
            en ImportService worden gemockt of in tmp_path geïsoleerd.
            Geen echte HTTP-verzoeken. Sinds v1.1.0 ook tests voor de
            duplicate-popup-flow (fase 5D'.2a). Sinds v1.2.0 startmap-
            logica (fase 5D'.3). Sinds v1.2.1 titelveld-gedrag.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie.
  v1.0.1 (2026-10-06)  isVisible() vervangen door isHidden().
  v1.0.2 (2026-10-07)  Titel-voorstel bij PDF is nu bestandsnaam.
  v1.1.0 (2026-10-07)  Tests voor duplicate-popup.
  v1.2.0 (2026-10-07)  Tests voor startmap en laatste_importmap.
  v1.2.1 (2026-10-07)  Tests voor titelveld-gedrag bij meerdere PDF-keuzes.
================================================================================
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import app.gui.dialogs.import_wizard_dialog as wizard_module
from app.config.settings import AppInstellingen
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


# ============================================================================
# Basis
# ============================================================================

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


# ============================================================================
# PDF kiezen
# ============================================================================

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
    monkeypatch.setattr(wizard_module, "sla_instellingen_op", lambda _: None)

    dialog._pick_pdf()

    assert dialog._pdf_pad == pdf_pad
    assert dialog._pdf_meta_titel == "Mijn PDF"
    assert dialog.title_edit.text() == "doc"
    assert dialog.import_btn.isEnabled() is True
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
    monkeypatch.setattr(wizard_module, "sla_instellingen_op", lambda _: None)

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
    monkeypatch.setattr(wizard_module, "sla_instellingen_op", lambda _: None)
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


# ============================================================================
# URL
# ============================================================================

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


# ============================================================================
# Importeren
# ============================================================================

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
    monkeypatch.setattr(wizard_module, "sla_instellingen_op", lambda _: None)
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
    monkeypatch.setattr(wizard_module, "sla_instellingen_op", lambda _: None)
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


# ============================================================================
# Taalwissel
# ============================================================================

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
# v1.1.0 — duplicate-popup-flow
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
    monkeypatch.setattr(wizard_module, "sla_instellingen_op", lambda _: None)
    dialog._pick_pdf()

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
    monkeypatch.setattr(wizard_module, "sla_instellingen_op", lambda _: None)
    dialog._pick_pdf()

    from app.documentation.pdf_import import import_pdf
    eerste = import_pdf(
        pdf_pad,
        import_service=service,
        sources_dir=tmp_path / "sources",
    )
    aantal_voor = len(service.list_sources())

    from app.gui.dialogs import duplicate_source_dialog as dup_module
    monkeypatch.setattr(
        dup_module.DuplicateSourceDialog,
        "vraag_actie",
        staticmethod(lambda **kw: DuplicateAction.KEEP),
    )

    dialog._perform_import()

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
    monkeypatch.setattr(wizard_module, "sla_instellingen_op", lambda _: None)
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
    monkeypatch.setattr(wizard_module, "sla_instellingen_op", lambda _: None)
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


# ============================================================================
# v1.2.0 — startmap-logica (fase 5D'.3)
# ============================================================================

def test_start_map_gebruikt_laatste_importmap_indien_geldig(
    tmp_path, monkeypatch
):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    dialog = ImportWizardDialog(taal="nl_NL", import_service=service)

    laatste_map = tmp_path / "laatste"
    laatste_map.mkdir()

    basis = AppInstellingen()
    from dataclasses import replace as dc_replace

    instellingen = dc_replace(
        basis,
        algemeen=dc_replace(
            basis.algemeen,
            laatste_importmap=str(laatste_map),
            standaard_importmap=str(tmp_path / "standaard"),
        ),
    )

    start = dialog._start_map_voor_pdf(instellingen)
    assert start == str(laatste_map)


def test_start_map_valt_terug_op_standaardmap_bij_ongeldige_laatste(
    tmp_path, monkeypatch
):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    dialog = ImportWizardDialog(taal="nl_NL", import_service=service)

    standaard_map = tmp_path / "standaard"
    standaard_map.mkdir()

    basis = AppInstellingen()
    from dataclasses import replace as dc_replace

    instellingen = dc_replace(
        basis,
        algemeen=dc_replace(
            basis.algemeen,
            laatste_importmap=str(tmp_path / "bestaat-niet"),
            standaard_importmap=str(standaard_map),
        ),
    )

    start = dialog._start_map_voor_pdf(instellingen)
    assert start == str(standaard_map)


def test_start_map_valt_terug_op_leeg_bij_geen_geldige_mappen(
    tmp_path
):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    dialog = ImportWizardDialog(taal="nl_NL", import_service=service)

    basis = AppInstellingen()
    from dataclasses import replace as dc_replace

    instellingen = dc_replace(
        basis,
        algemeen=dc_replace(
            basis.algemeen,
            laatste_importmap=str(tmp_path / "bestaat-niet-1"),
            standaard_importmap=str(tmp_path / "bestaat-niet-2"),
        ),
    )

    start = dialog._start_map_voor_pdf(instellingen)
    assert start == ""


def test_pick_pdf_start_in_laatste_importmap(tmp_path, monkeypatch):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    dialog = ImportWizardDialog(taal="nl_NL", import_service=service)

    laatste_map = tmp_path / "laatste"
    laatste_map.mkdir()
    pdf_pad = _maak_eenvoudige_pdf(laatste_map / "doc.pdf")

    basis = AppInstellingen()
    from dataclasses import replace as dc_replace

    instellingen = dc_replace(
        basis,
        algemeen=dc_replace(
            basis.algemeen,
            laatste_importmap=str(laatste_map),
        ),
    )
    monkeypatch.setattr(
        wizard_module, "laad_instellingen", lambda: instellingen
    )
    monkeypatch.setattr(wizard_module, "sla_instellingen_op", lambda _: None)

    ontvangen_start = {"pad": None}

    from PySide6.QtWidgets import QFileDialog

    def _fake_get_open(parent, titel, start, filter_):
        ontvangen_start["pad"] = start
        return (str(pdf_pad), "PDF (*.pdf)")

    monkeypatch.setattr(
        QFileDialog, "getOpenFileName", staticmethod(_fake_get_open)
    )

    dialog._pick_pdf()

    assert ontvangen_start["pad"] == str(laatste_map)


def test_pick_pdf_onthoudt_nieuwe_map(tmp_path, monkeypatch):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    dialog = ImportWizardDialog(taal="nl_NL", import_service=service)

    andere_map = tmp_path / "andere"
    andere_map.mkdir()
    pdf_pad = _maak_eenvoudige_pdf(andere_map / "doc.pdf")

    basis = AppInstellingen()
    monkeypatch.setattr(
        wizard_module, "laad_instellingen", lambda: basis
    )

    opgeslagen = {"instellingen": None}

    def _fake_opslaan(inst):
        opgeslagen["instellingen"] = inst

    monkeypatch.setattr(wizard_module, "sla_instellingen_op", _fake_opslaan)

    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        staticmethod(lambda *a, **kw: (str(pdf_pad), "PDF (*.pdf)")),
    )

    dialog._pick_pdf()

    assert opgeslagen["instellingen"] is not None
    assert (
        opgeslagen["instellingen"].algemeen.laatste_importmap
        == str(andere_map)
    )


def test_pick_pdf_annuleren_wijzigt_niets(tmp_path, monkeypatch):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    dialog = ImportWizardDialog(taal="nl_NL", import_service=service)

    basis = AppInstellingen()
    monkeypatch.setattr(
        wizard_module, "laad_instellingen", lambda: basis
    )

    opgeslagen = {"count": 0}

    def _fake_opslaan(inst):
        opgeslagen["count"] += 1

    monkeypatch.setattr(wizard_module, "sla_instellingen_op", _fake_opslaan)

    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        staticmethod(lambda *a, **kw: ("", "")),
    )

    dialog._pick_pdf()

    assert opgeslagen["count"] == 0
    assert dialog._pdf_pad is None


def test_pick_pdf_zelfde_map_slaat_niet_opnieuw_op(tmp_path, monkeypatch):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    dialog = ImportWizardDialog(taal="nl_NL", import_service=service)

    pdf_pad = _maak_eenvoudige_pdf(tmp_path / "doc.pdf")

    basis = AppInstellingen()
    from dataclasses import replace as dc_replace

    instellingen = dc_replace(
        basis,
        algemeen=dc_replace(
            basis.algemeen,
            laatste_importmap=str(tmp_path),
        ),
    )
    monkeypatch.setattr(
        wizard_module, "laad_instellingen", lambda: instellingen
    )

    opgeslagen = {"count": 0}

    def _fake_opslaan(inst):
        opgeslagen["count"] += 1

    monkeypatch.setattr(wizard_module, "sla_instellingen_op", _fake_opslaan)

    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        staticmethod(lambda *a, **kw: (str(pdf_pad), "PDF (*.pdf)")),
    )

    dialog._pick_pdf()

    assert opgeslagen["count"] == 0


# ============================================================================
# v1.2.1 — titelveld-gedrag bij meerdere PDF-keuzes
# ============================================================================

def test_titel_wisselt_bij_nieuwe_pdf_als_automatisch(tmp_path, monkeypatch):
    """Twee PDF-keuzes na elkaar: titel volgt de tweede keuze."""
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    dialog = ImportWizardDialog(taal="nl_NL", import_service=service)

    pdf_a = _maak_eenvoudige_pdf(tmp_path / "eerste.pdf")
    pdf_b = _maak_eenvoudige_pdf(tmp_path / "tweede.pdf")

    monkeypatch.setattr(wizard_module, "sla_instellingen_op", lambda _: None)

    from PySide6.QtWidgets import QFileDialog

    # Eerste keuze
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        staticmethod(lambda *a, **kw: (str(pdf_a), "PDF (*.pdf)")),
    )
    dialog._pick_pdf()
    assert dialog.title_edit.text() == "eerste"
    assert dialog._titel_automatisch is True

    # Tweede keuze: titel moet mee veranderen
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        staticmethod(lambda *a, **kw: (str(pdf_b), "PDF (*.pdf)")),
    )
    dialog._pick_pdf()
    assert dialog.title_edit.text() == "tweede"


def test_titel_blijft_staan_bij_nieuwe_pdf_na_handmatige_bewerking(
    tmp_path, monkeypatch
):
    """Als de gebruiker de titel handmatig typt, blijft die staan."""
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    dialog = ImportWizardDialog(taal="nl_NL", import_service=service)

    pdf_a = _maak_eenvoudige_pdf(tmp_path / "eerste.pdf")
    pdf_b = _maak_eenvoudige_pdf(tmp_path / "tweede.pdf")

    monkeypatch.setattr(wizard_module, "sla_instellingen_op", lambda _: None)

    from PySide6.QtWidgets import QFileDialog

    # Eerste keuze: automatisch
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        staticmethod(lambda *a, **kw: (str(pdf_a), "PDF (*.pdf)")),
    )
    dialog._pick_pdf()
    assert dialog.title_edit.text() == "eerste"

    # Handmatige bewerking simuleren: textEdited-signaal.
    dialog._on_titel_handmatig_bewerkt("Mijn eigen titel")
    dialog.title_edit.setText("Mijn eigen titel")
    assert dialog._titel_automatisch is False

    # Tweede keuze: titel mag NIET worden overschreven
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        staticmethod(lambda *a, **kw: (str(pdf_b), "PDF (*.pdf)")),
    )
    dialog._pick_pdf()
    assert dialog.title_edit.text() == "Mijn eigen titel"


def test_samenvatting_wisselt_bij_nieuwe_pdf(tmp_path, monkeypatch):
    """Samenvatting toont altijd de laatste PDF, ongeacht titel-state."""
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    dialog = ImportWizardDialog(taal="nl_NL", import_service=service)

    pdf_a = _maak_eenvoudige_pdf(tmp_path / "eerste.pdf")
    pdf_b = _maak_eenvoudige_pdf(tmp_path / "tweede.pdf")

    monkeypatch.setattr(wizard_module, "sla_instellingen_op", lambda _: None)

    from PySide6.QtWidgets import QFileDialog

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        staticmethod(lambda *a, **kw: (str(pdf_a), "PDF (*.pdf)")),
    )
    dialog._pick_pdf()
    html_a = dialog.summary_browser.toHtml()
    assert "eerste.pdf" in html_a

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        staticmethod(lambda *a, **kw: (str(pdf_b), "PDF (*.pdf)")),
    )
    dialog._pick_pdf()
    html_b = dialog.summary_browser.toHtml()
    assert "tweede.pdf" in html_b
    assert "eerste.pdf" not in html_b