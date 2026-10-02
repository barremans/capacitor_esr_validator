"""
================================================================================
Module:     tests/test_settings_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Validator (Windows)
Versie:     1.1.0
Datum:      2026-09-27
Auteur:     Ontwikkelaar

Doel:       GUI-regressietests voor de Settings-dialoog.

Wijzigingen:
  v1.1.0 (2026-10-02)  Algemene bestandsvoorkeuren en Browse-gedrag getest.
================================================================================
"""

from PySide6.QtWidgets import QApplication

from app.config.settings import AppInstellingen
from app.gui.dialogs.settings_dialog import SettingsDialog


def _app():
    return QApplication.instance() or QApplication([])


def test_settings_dialog_heeft_drie_tabs():
    _app()
    dialog = SettingsDialog(AppInstellingen(), taal="nl_NL")
    assert dialog.tabs.count() == 3
    assert dialog.tabs.tabText(0) == "Algemeen"
    assert dialog.tabs.tabText(1) == "ESR / Condensator"
    assert dialog.tabs.tabText(2) == "Rapportage"


def test_annuleren_verandert_toegepaste_instellingen_niet():
    _app()
    basis = AppInstellingen()
    dialog = SettingsDialog(basis, taal="nl_NL")
    dialog.temperatuur_spin.setValue(35.0)
    dialog.reject()
    assert dialog.toegepaste_instellingen == basis


def test_toepassen_levert_nieuw_object_en_behoudt_beoordeling():
    _app()
    basis = AppInstellingen()
    dialog = SettingsDialog(basis, taal="nl_NL")
    dialog.temperatuur_spin.setValue(25.0)
    dialog._toepassen()
    assert dialog.toegepaste_instellingen.esr_condensator.temperatuur_c == 25.0
    assert dialog.toegepaste_instellingen.beoordeling == basis.beoordeling


def test_english_tab_labels():
    _app()
    dialog = SettingsDialog(AppInstellingen(taal="en_US"), taal="en_US")
    assert dialog.tabs.tabText(0) == "General"
    assert dialog.tabs.tabText(1) == "ESR / Capacitor"
    assert dialog.tabs.tabText(2) == "Reporting"


def test_bestandsvoorkeuren_worden_in_nieuw_settingsobject_opgenomen():
    _app()
    basis = AppInstellingen()
    dialog = SettingsDialog(basis, taal="nl_NL")

    dialog.exportmap_edit.setText(r"C:\Exports")
    dialog.importmap_edit.setText(r"C:\Imports")
    dialog.exportmap_openen_check.setChecked(True)
    dialog._toepassen()

    algemeen = dialog.toegepaste_instellingen.algemeen
    assert algemeen.standaard_exportmap == r"C:\Exports"
    assert algemeen.standaard_importmap == r"C:\Imports"
    assert algemeen.exportmap_openen_na_export is True


def test_bladeren_voor_exportmap_vult_veld(monkeypatch):
    _app()
    dialog = SettingsDialog(AppInstellingen(), taal="nl_NL")

    monkeypatch.setattr(
        "app.gui.dialogs.settings_dialog.QFileDialog.getExistingDirectory",
        lambda *args, **kwargs: r"C:\GekozenExport",
    )

    dialog._kies_exportmap()

    assert dialog.exportmap_edit.text() == r"C:\GekozenExport"


def test_condensatortypes_komen_uit_centrale_settingsconstante():
    _app()
    from app.config.settings import CONDENSATORTYPES

    dialog = SettingsDialog(AppInstellingen(), taal="nl_NL")
    waarden = [dialog.type_combo.itemText(i) for i in range(dialog.type_combo.count())]

    assert tuple(waarden) == CONDENSATORTYPES
