"""
================================================================================
Module:     tests/test_settings_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Validator (Windows)
Versie:     1.3.0
Datum:      2026-10-14
Auteur:     Bart Bossuyt

Doel:       GUI-regressietests voor de Settings-dialoog.

Wijzigingen:
  v1.1.0 (2026-10-02)  Algemene bestandsvoorkeuren en Browse-gedrag getest.
  v1.2.0 (2026-10-11)  Fase 8D: Auteur-veld en Rapportmap-veld getest.
  v1.3.0 (2026-10-14)  Fase 9H: checkbox "Bij opstarten controleren op
                       updates" getest, inclusief default True en
                       roundtrip via Toepassen.
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


# ============================================================================
# v1.2.0 — Auteur-veld en Rapportmap-veld (fase 8D)
# ============================================================================

def test_auteur_veld_leeg_default():
    _app()
    dialog = SettingsDialog(AppInstellingen(), taal="nl_NL")
    assert dialog.auteur_edit.text() == ""


def test_rapportmap_veld_leeg_default():
    _app()
    dialog = SettingsDialog(AppInstellingen(), taal="nl_NL")
    assert dialog.rapportmap_edit.text() == ""


def test_auteur_wordt_opgenomen_in_nieuw_settingsobject():
    _app()
    dialog = SettingsDialog(AppInstellingen(), taal="nl_NL")
    dialog.auteur_edit.setText("Bart Bossuyt")
    dialog._toepassen()

    assert dialog.toegepaste_instellingen.rapportage.auteur == "Bart Bossuyt"


def test_rapportmap_wordt_opgenomen_in_laatste_rapportmap():
    _app()
    dialog = SettingsDialog(AppInstellingen(), taal="nl_NL")
    dialog.rapportmap_edit.setText(r"C:\Rapporten")
    dialog._toepassen()

    assert (
        dialog.toegepaste_instellingen.algemeen.laatste_rapportmap
        == r"C:\Rapporten"
    )


def test_bestaande_laatste_exportmap_blijft_behouden_bij_toepassen():
    """Belangrijk: Toepassen mag laatste_exportmap niet per ongeluk wissen."""
    _app()
    basis = AppInstellingen()
    basis = type(basis)(
        taal=basis.taal,
        algemeen=type(basis.algemeen)(
            thema=basis.algemeen.thema,
            tooltips_ingeschakeld=basis.algemeen.tooltips_ingeschakeld,
            standaard_exportmap=basis.algemeen.standaard_exportmap,
            standaard_importmap=basis.algemeen.standaard_importmap,
            laatste_exportmap=r"C:\CSV",
            laatste_importmap=r"C:\PDFs",
            laatste_rapportmap="",
            exportmap_openen_na_export=basis.algemeen.exportmap_openen_na_export,
        ),
        esr_condensator=basis.esr_condensator,
        rapportage=basis.rapportage,
        beoordeling=basis.beoordeling,
    )
    dialog = SettingsDialog(basis, taal="nl_NL")
    dialog._toepassen()

    algemeen = dialog.toegepaste_instellingen.algemeen
    assert algemeen.laatste_exportmap == r"C:\CSV"
    assert algemeen.laatste_importmap == r"C:\PDFs"


def test_bladeren_voor_rapportmap_vult_veld(monkeypatch):
    _app()
    dialog = SettingsDialog(AppInstellingen(), taal="nl_NL")

    monkeypatch.setattr(
        "app.gui.dialogs.settings_dialog.QFileDialog.getExistingDirectory",
        lambda *args, **kwargs: r"C:\GekozenRapportmap",
    )

    dialog._kies_rapportmap()

    assert dialog.rapportmap_edit.text() == r"C:\GekozenRapportmap"


# ============================================================================
# v1.3.0 — update-check bij opstarten (fase 9H)
# ============================================================================

def test_controleer_updates_checkbox_default_aan():
    _app()
    dialog = SettingsDialog(AppInstellingen(), taal="nl_NL")
    assert dialog.controleer_updates_check.isChecked() is True


def test_controleer_updates_checkbox_neemt_waarde_over():
    _app()
    basis = AppInstellingen()
    basis = type(basis)(
        taal=basis.taal,
        algemeen=type(basis.algemeen)(
            thema=basis.algemeen.thema,
            tooltips_ingeschakeld=basis.algemeen.tooltips_ingeschakeld,
            standaard_exportmap=basis.algemeen.standaard_exportmap,
            standaard_importmap=basis.algemeen.standaard_importmap,
            laatste_exportmap=basis.algemeen.laatste_exportmap,
            laatste_importmap=basis.algemeen.laatste_importmap,
            laatste_rapportmap=basis.algemeen.laatste_rapportmap,
            exportmap_openen_na_export=basis.algemeen.exportmap_openen_na_export,
            controleer_updates_bij_opstarten=False,
        ),
        esr_condensator=basis.esr_condensator,
        rapportage=basis.rapportage,
        beoordeling=basis.beoordeling,
    )
    dialog = SettingsDialog(basis, taal="nl_NL")
    assert dialog.controleer_updates_check.isChecked() is False


def test_controleer_updates_uit_wordt_opgenomen():
    _app()
    dialog = SettingsDialog(AppInstellingen(), taal="nl_NL")
    dialog.controleer_updates_check.setChecked(False)
    dialog._toepassen()

    assert (
        dialog.toegepaste_instellingen.algemeen.controleer_updates_bij_opstarten
        is False
    )


def test_controleer_updates_aan_blijft_aan_bij_toepassen():
    _app()
    dialog = SettingsDialog(AppInstellingen(), taal="nl_NL")
    dialog._toepassen()

    assert (
        dialog.toegepaste_instellingen.algemeen.controleer_updates_bij_opstarten
        is True
    )


def test_andere_instellingen_blijven_behouden_bij_update_checkbox_wijziging():
    """De nieuwe checkbox mag niets anders beïnvloeden."""
    _app()
    basis = AppInstellingen()
    dialog = SettingsDialog(basis, taal="nl_NL")
    dialog.temperatuur_spin.setValue(30.0)
    dialog.controleer_updates_check.setChecked(False)
    dialog._toepassen()

    esr = dialog.toegepaste_instellingen.esr_condensator
    assert esr.temperatuur_c == 30.0
    assert (
        dialog.toegepaste_instellingen.algemeen.controleer_updates_bij_opstarten
        is False
    )