"""
================================================================================
Module:     tests/test_edit_metadata_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-20
Auteur:     Bart Bossuyt

Doel:       GUI-regressietests voor de metadata-editor (fase 5D'.2c).
            Geen echte ImportService met %LOCALAPPDATA%; de service wordt
            in tmp_path geïsoleerd.

Wijzigingen:
  v1.0.0 (2026-10-07)  Eerste versie.
  v1.1.0 (2026-10-20)  Fase 11F.4: tests voor de uitgebreide
                        datum-parsing. _parse_datum_naar_qdate accepteert
                        nu ook yyyy/MM/dd, dd-MM-yyyy, yyyy-MM (dag 1)
                        en yyyy (1 januari).
================================================================================
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QApplication

from app.documentation.import_models import (
    ImportSource,
    ImportSourceType,
    ImportStatus,
)
from app.documentation.import_service import ImportService
from app.gui.dialogs.edit_metadata_dialog import EditMetadataDialog


def _app():
    return QApplication.instance() or QApplication([])


def _maak_pdf_source(**overrides) -> ImportSource:
    basis = dict(
        source_id="abc-123",
        source_type=ImportSourceType.PDF,
        title="OUD",
        imported_at=1_700_000_000_000,
        imported_by="tester",
        status=ImportStatus.CONCEPT,
        original_filename="oud.pdf",
        file_hash="hash_abc",
        category="DATASHEET",
        manufacturer="PANASONIC",
        series="FR",
        part_number="FR-123",
        document_version="1.0",
        document_date="2024-01-01",
        notes="oude notitie",
    )
    basis.update(overrides)
    return ImportSource(**basis)


# ============================================================================
# Initialisatie
# ============================================================================

def test_dialoog_toont_bestaande_metadata(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_pdf_source()
    dialog = EditMetadataDialog(bron=bron, taal="nl_NL", import_service=service)

    assert dialog.title_edit.text() == "OUD"
    assert dialog.fabrikant_edit.text() == "PANASONIC"
    assert dialog.serie_edit.text() == "FR"
    assert dialog.partnummer_edit.text() == "FR-123"
    assert dialog.documentversie_edit.text() == "1.0"
    assert dialog.notities_edit.text() == "oude notitie"


def test_dialoog_toont_bestaande_categorie(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_pdf_source(category="MANUAL")
    dialog = EditMetadataDialog(bron=bron, taal="nl_NL", import_service=service)

    assert dialog._huidige_categorie() == "MANUAL"
    assert dialog.categorie_combo.currentText() == "Handleiding"


def test_dialoog_toont_bestaande_datum(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_pdf_source(document_date="2024-01-31")
    dialog = EditMetadataDialog(bron=bron, taal="nl_NL", import_service=service)

    assert dialog.documentdatum_edit.date() == QDate(2024, 1, 31)
    assert dialog.datum_onbekend_checkbox.isChecked() is False
    assert dialog.documentdatum_edit.isEnabled() is True


def test_dialoog_zonder_datum_zet_onbekend(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_pdf_source(document_date=None)
    dialog = EditMetadataDialog(bron=bron, taal="nl_NL", import_service=service)

    assert dialog.datum_onbekend_checkbox.isChecked() is True
    assert dialog.documentdatum_edit.isEnabled() is False


def test_dialoog_met_onbekende_datum_zet_onbekend(tmp_path):
    """Een onparseerbare datum valt terug op 'Datum onbekend'."""
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_pdf_source(document_date="geen-datum")
    dialog = EditMetadataDialog(bron=bron, taal="nl_NL", import_service=service)

    assert dialog.datum_onbekend_checkbox.isChecked() is True
    assert dialog.documentdatum_edit.isEnabled() is False


def test_dialoog_behoudt_bron_source_id(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_pdf_source()
    dialog = EditMetadataDialog(bron=bron, taal="nl_NL", import_service=service)

    assert dialog.bron.source_id == "abc-123"


# ============================================================================
# Datum-parsing (fase 11F.4)
# ============================================================================

def test_parse_iso_datum():
    _app()
    assert EditMetadataDialog._parse_datum_naar_qdate("2024-01-31") == QDate(2024, 1, 31)


def test_parse_slash_datum():
    _app()
    assert EditMetadataDialog._parse_datum_naar_qdate("2024/01/31") == QDate(2024, 1, 31)


def test_parse_nl_datum():
    _app()
    assert EditMetadataDialog._parse_datum_naar_qdate("31-01-2024") == QDate(2024, 1, 31)


def test_parse_maand_only_geeft_dag_1():
    _app()
    assert EditMetadataDialog._parse_datum_naar_qdate("2024-01") == QDate(2024, 1, 1)


def test_parse_jaar_only_geeft_1_januari():
    _app()
    assert EditMetadataDialog._parse_datum_naar_qdate("2024") == QDate(2024, 1, 1)


def test_parse_lege_string_geeft_ongeldig():
    _app()
    qdate = EditMetadataDialog._parse_datum_naar_qdate("")
    assert qdate.isValid() is False


def test_parse_whitespace_geeft_ongeldig():
    _app()
    qdate = EditMetadataDialog._parse_datum_naar_qdate("   ")
    assert qdate.isValid() is False


def test_parse_onbekend_formaat_geeft_ongeldig():
    _app()
    qdate = EditMetadataDialog._parse_datum_naar_qdate("geen-datum")
    assert qdate.isValid() is False


def test_parse_ongeldige_maand_geeft_ongeldig():
    _app()
    qdate = EditMetadataDialog._parse_datum_naar_qdate("2024-13")
    assert qdate.isValid() is False


def test_parse_ongeldige_maand_nul_geeft_ongeldig():
    _app()
    qdate = EditMetadataDialog._parse_datum_naar_qdate("2024-00")
    assert qdate.isValid() is False


def test_dialoog_met_slash_datum(tmp_path):
    """yyyy/MM/dd wordt geaccepteerd als bestaande document_date."""
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_pdf_source(document_date="2024/01/31")
    dialog = EditMetadataDialog(bron=bron, taal="nl_NL", import_service=service)

    assert dialog.documentdatum_edit.date() == QDate(2024, 1, 31)
    assert dialog.datum_onbekend_checkbox.isChecked() is False


def test_dialoog_met_nl_datum(tmp_path):
    """dd-MM-yyyy wordt geaccepteerd als bestaande document_date."""
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_pdf_source(document_date="31-01-2024")
    dialog = EditMetadataDialog(bron=bron, taal="nl_NL", import_service=service)

    assert dialog.documentdatum_edit.date() == QDate(2024, 1, 31)
    assert dialog.datum_onbekend_checkbox.isChecked() is False


def test_dialoog_met_maand_only(tmp_path):
    """yyyy-MM wordt geaccepteerd; dag wordt 1."""
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_pdf_source(document_date="2024-01")
    dialog = EditMetadataDialog(bron=bron, taal="nl_NL", import_service=service)

    assert dialog.documentdatum_edit.date() == QDate(2024, 1, 1)
    assert dialog.datum_onbekend_checkbox.isChecked() is False
    assert dialog.documentdatum_edit.isEnabled() is True


def test_dialoog_met_jaar_only(tmp_path):
    """yyyy wordt geaccepteerd; datum wordt 1 januari."""
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_pdf_source(document_date="2024")
    dialog = EditMetadataDialog(bron=bron, taal="nl_NL", import_service=service)

    assert dialog.documentdatum_edit.date() == QDate(2024, 1, 1)
    assert dialog.datum_onbekend_checkbox.isChecked() is False
    assert dialog.documentdatum_edit.isEnabled() is True


# ============================================================================
# Opslaan-knop state
# ============================================================================

def test_save_btn_actief_met_titel(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_pdf_source()
    dialog = EditMetadataDialog(bron=bron, taal="nl_NL", import_service=service)

    assert dialog.save_btn.isEnabled() is True


def test_save_btn_disabled_bij_lege_titel(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_pdf_source(title="OUD")
    dialog = EditMetadataDialog(bron=bron, taal="nl_NL", import_service=service)

    dialog.title_edit.setText("")
    dialog._update_save_state()
    assert dialog.save_btn.isEnabled() is False


def test_save_btn_weer_actief_na_titel(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_pdf_source()
    dialog = EditMetadataDialog(bron=bron, taal="nl_NL", import_service=service)

    dialog.title_edit.setText("")
    dialog._update_save_state()
    assert dialog.save_btn.isEnabled() is False

    dialog.title_edit.setText("NIEUW")
    dialog._update_save_state()
    assert dialog.save_btn.isEnabled() is True


# ============================================================================
# Opslaan
# ============================================================================

def _registreer_bron(service, **overrides):
    """Registreer de bron in de service zodat update_metadata kan werken."""
    basis = dict(
        title="OUD",
        original_filename="oud.pdf",
        file_hash="hash_abc",
        category="DATASHEET",
        manufacturer="PANASONIC",
        series="FR",
        part_number="FR-123",
        document_version="1.0",
        document_date="2024-01-01",
        notes="oude notitie",
    )
    basis.update(overrides)
    return service.register_pdf(**basis)


def test_save_roept_update_metadata_aan(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    r = _registreer_bron(service)
    dialog = EditMetadataDialog(
        bron=r.source, taal="nl_NL", import_service=service
    )

    dialog.title_edit.setText("NIEUW")
    dialog.fabrikant_edit.setText("TDK")

    ontvangen = {"source_id": None}
    dialog.metadata_saved.connect(
        lambda sid: ontvangen.__setitem__("source_id", sid)
    )

    dialog._save()

    assert ontvangen["source_id"] == r.source.source_id
    terug = service.get(r.source.source_id)
    assert terug.title == "NIEUW"
    assert terug.manufacturer == "TDK"


def test_save_lege_titel_doet_niets(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    r = _registreer_bron(service)
    dialog = EditMetadataDialog(
        bron=r.source, taal="nl_NL", import_service=service
    )

    dialog.title_edit.setText("")
    ontvangen = {"source_id": None}
    dialog.metadata_saved.connect(
        lambda sid: ontvangen.__setitem__("source_id", sid)
    )

    dialog._save()

    assert ontvangen["source_id"] is None
    terug = service.get(r.source.source_id)
    assert terug.title == "OUD"


def test_save_datum_onbekend_maakt_leeg(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    r = _registreer_bron(service)
    dialog = EditMetadataDialog(
        bron=r.source, taal="nl_NL", import_service=service
    )

    dialog.datum_onbekend_checkbox.setChecked(True)
    dialog._save()

    terug = service.get(r.source.source_id)
    assert terug.document_date is None


def test_save_lege_metadata_wordt_none(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    r = _registreer_bron(service)
    dialog = EditMetadataDialog(
        bron=r.source, taal="nl_NL", import_service=service
    )

    dialog.fabrikant_edit.setText("")
    dialog.serie_edit.setText("")
    dialog.notities_edit.setText("")
    dialog._save()

    terug = service.get(r.source.source_id)
    assert terug.manufacturer is None
    assert terug.series is None
    assert terug.notes is None


# ============================================================================
# Datum-interacties
# ============================================================================

def test_datum_onbekend_disablet_veld(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_pdf_source(document_date="2024-01-01")
    dialog = EditMetadataDialog(bron=bron, taal="nl_NL", import_service=service)

    dialog.datum_onbekend_checkbox.setChecked(True)
    assert dialog.documentdatum_edit.isEnabled() is False
    dialog.datum_onbekend_checkbox.setChecked(False)
    assert dialog.documentdatum_edit.isEnabled() is True


def test_ctrl_d_zet_vandaag(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_pdf_source(document_date="2024-01-01")
    dialog = EditMetadataDialog(bron=bron, taal="nl_NL", import_service=service)

    dialog._zet_datum_op_vandaag()
    assert dialog.documentdatum_edit.date() == QDate.currentDate()


def test_ctrl_d_negeert_onbekend(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_pdf_source(document_date="2024-01-01")
    dialog = EditMetadataDialog(bron=bron, taal="nl_NL", import_service=service)

    dialog.datum_onbekend_checkbox.setChecked(True)
    dialog._zet_datum_op_vandaag()
    assert dialog.documentdatum_edit.date() == QDate(2024, 1, 1)


# ============================================================================
# Taalwissel
# ============================================================================

def test_labels_nl(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_pdf_source()
    dialog = EditMetadataDialog(bron=bron, taal="nl_NL", import_service=service)

    assert dialog.header_label.text() == "Metadata bewerken"
    assert dialog.save_btn.text() == "Opslaan"
    assert dialog.cancel_btn.text() == "Annuleren"
    assert dialog.categorie_combo.currentText() == "Fabrikantdatasheet"


def test_labels_en(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_pdf_source()
    dialog = EditMetadataDialog(bron=bron, taal="en_US", import_service=service)

    assert dialog.header_label.text() == "Edit metadata"
    assert dialog.save_btn.text() == "Save"
    assert dialog.cancel_btn.text() == "Cancel"
    assert dialog.categorie_combo.currentText() == "Manufacturer datasheet"


def test_taalwissel_behoudt_categorie(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_pdf_source(category="MANUAL")
    dialog = EditMetadataDialog(bron=bron, taal="nl_NL", import_service=service)

    assert dialog._huidige_categorie() == "MANUAL"
    dialog.taal = "en_US"
    dialog._apply_language()
    assert dialog._huidige_categorie() == "MANUAL"
    assert dialog.categorie_combo.currentText() == "Manual"


# ============================================================================
# Uppercase op identificatievelden
# ============================================================================

def test_fabrikant_uppercase(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_pdf_source()
    dialog = EditMetadataDialog(bron=bron, taal="nl_NL", import_service=service)

    from app.gui.dialogs._metadata_form_helpers import naar_uppercase

    dialog.fabrikant_edit.setText("tdk")
    naar_uppercase(dialog.fabrikant_edit)
    assert dialog.fabrikant_edit.text() == "TDK"


def test_titel_blijft_gemengd(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_pdf_source(title="OUD")
    dialog = EditMetadataDialog(bron=bron, taal="nl_NL", import_service=service)

    dialog.title_edit.setText("Measure ESR with an ESR meter")
    assert dialog.title_edit.text() == "Measure ESR with an ESR meter"


def test_notities_blijft_gemengd(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_pdf_source()
    dialog = EditMetadataDialog(bron=bron, taal="nl_NL", import_service=service)

    dialog.notities_edit.setText("Test notitie met Gemengde Case")
    assert dialog.notities_edit.text() == "Test notitie met Gemengde Case"