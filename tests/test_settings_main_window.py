"""
================================================================================
Module:     tests/test_settings_main_window.py
Project:    Electronics Diagnostic Tool Hub / ESR Validator (Windows)
Versie:     1.0.1
Datum:      2026-09-27
Auteur:     Ontwikkelaar

Doel:       Regressietests voor de koppeling tussen ToolHubWindow en Settings.
Wijzigingen:
  v1.0.1 (2026-09-27)  Correcte hoofdvensterklasse ToolHubWindow gebruikt.
================================================================================
"""

from dataclasses import replace

from PySide6.QtWidgets import QApplication

import app.gui.main_window as main_window_module
from app.gui.main_window import ToolHubWindow


def _app():
    return QApplication.instance() or QApplication([])


def test_taalwissel_behoudt_overige_instellingen(monkeypatch):
    _app()
    opgeslagen = []
    monkeypatch.setattr(main_window_module, "sla_instellingen_op", opgeslagen.append)

    window = ToolHubWindow()
    basis = window.instellingen
    aangepast_esr = replace(
        basis.esr_condensator,
        temperatuur_c=27.0,
        bevestig_wissen=False,
    )
    window.instellingen = replace(basis, esr_condensator=aangepast_esr)

    window._set_language("en_US")

    assert window.instellingen.taal == "en_US"
    assert window.instellingen.esr_condensator == aangepast_esr
    assert opgeslagen[-1] == window.instellingen


def test_apply_settings_bewaart_volledig_object(monkeypatch):
    _app()
    opgeslagen = []
    monkeypatch.setattr(main_window_module, "sla_instellingen_op", opgeslagen.append)

    window = ToolHubWindow()
    nieuw = replace(
        window.instellingen,
        rapportage=replace(
            window.instellingen.rapportage,
            werkplaats_bedrijf="Werkplaats",
        ),
    )

    window._apply_settings(nieuw)

    assert window.instellingen == nieuw
    assert opgeslagen == [nieuw]


def test_show_settings_opent_settingsdialog(monkeypatch):
    _app()
    geopend = []

    class FakeSignal:
        def connect(self, callback):
            self.callback = callback

    class FakeDialog:
        def __init__(self, instellingen, taal, parent):
            geopend.append((instellingen, taal, parent))
            self.settings_applied = FakeSignal()

        def exec(self):
            return 0

    monkeypatch.setattr(main_window_module, "SettingsDialog", FakeDialog)

    window = ToolHubWindow()
    window._show_settings()

    assert len(geopend) == 1
    assert geopend[0][0] == window.instellingen
    assert geopend[0][1] == window.taal
    assert geopend[0][2] is window
