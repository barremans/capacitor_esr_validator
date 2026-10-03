"""
================================================================================
Module:     tests/test_i18n_dynamic_language_ui.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-03
Auteur:     Bart Bossuyt

Doel:       Bewijst dat Settings en hoofdmenu talen dynamisch uit i18n-metadata
            opbouwen in plaats van uit vaste NL/EN-code.

Wijzigingen:
  v1.0.0 (2026-10-03)  Eerste dynamische taalkeuzetests.
================================================================================
"""

from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import app.gui.dialogs.settings_dialog as settings_dialog_module
import app.gui.main_window as main_window_module
from app.config.settings import AppInstellingen
from app.gui.dialogs.settings_dialog import SettingsDialog
from app.helpers.i18n import TaalInfo


def _app():
    return QApplication.instance() or QApplication([])


def _fake_languages():
    return [
        TaalInfo("nl_NL", "Dutch", "Nederlands", True, 10),
        TaalInfo("en_US", "English", "English", True, 20),
        TaalInfo("de_DE", "German", "Deutsch", True, 30),
    ]


def test_settings_taalkeuze_wordt_dynamisch_opgebouwd(monkeypatch):
    _app()
    monkeypatch.setattr(
        settings_dialog_module,
        "beschikbare_taalinfos",
        _fake_languages,
    )

    dialog = SettingsDialog(AppInstellingen(), taal="nl_NL")

    assert dialog.taal_combo.count() == 3
    assert [dialog.taal_combo.itemData(i) for i in range(3)] == [
        "nl_NL",
        "en_US",
        "de_DE",
    ]
    assert [dialog.taal_combo.itemText(i) for i in range(3)] == [
        "Nederlands",
        "English",
        "Deutsch",
    ]


def test_hoofdmenu_talenactie_wordt_dynamisch_opgebouwd(monkeypatch):
    _app()
    monkeypatch.setattr(main_window_module, "beschikbare_taalinfos", _fake_languages)

    # Gebruik de echte instellingenstructuur maar voorkom schijfwijziging.
    basis = AppInstellingen(taal="nl_NL")
    monkeypatch.setattr(main_window_module, "laad_instellingen", lambda: basis)
    monkeypatch.setattr(main_window_module, "sla_instellingen_op", lambda instellingen: None)

    window = main_window_module.ToolHubWindow()

    assert set(window.language_actions) == {"nl_NL", "en_US", "de_DE"}
    assert window.language_actions["de_DE"].text() == "Deutsch"
    assert window.language_actions["nl_NL"].isChecked() is True
