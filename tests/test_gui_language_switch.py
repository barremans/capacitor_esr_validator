"""
================================================================================
Module:     tests/test_gui_language_switch.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Regressietests voor live taalwissel in Hoofdmenu/Diagnose, ESR en
            Historiek. Bewijst dat zichtbare statische GUI-teksten vernieuwen
            zonder meetinvoer of actieve filterwaarden te wissen.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste regressietests voor de taalwissel-UX-fix.
================================================================================
"""

from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

import app.gui.esr_test_screen as esr_module
import app.gui.history_screen as history_module
import app.gui.main_window as main_window_module
from app.gui.esr_test_screen import EsrTestScreen
from app.gui.history_screen import HistoryScreen
from app.gui.main_window import ToolHubWindow


@pytest.fixture(scope="module", autouse=True)
def qapplication():
    app = QApplication.instance() or QApplication([])
    yield app


def _fake_translate(key: str, taal: str = "nl_NL", **kwargs) -> str:
    return f"{taal}:{key}"


def _fake_esr_settings():
    instrument_code = next(iter(esr_module.INSTRUMENT_PROFIELEN))
    profile = esr_module.get_instrument_profiel(instrument_code)
    frequency = profile.standaard_frequentie_hz or profile.frequenties_hz[0]
    test_voltage = (
        profile.standaard_testspanning_vrms
        if profile.standaard_testspanning_vrms is not None
        else profile.testspanningen_vrms[0]
    )
    return SimpleNamespace(
        esr_condensator=SimpleNamespace(
            capaciteitseenheid="µF",
            tolerantie_percent=20.0,
            werkspanning_v=None,
            condensatortype=esr_module.CONDENSATORTYPES[0],
            fabrikant="",
            meetmethode="EX_SITU",
            instrument_code=instrument_code,
            meetfrequentie_hz=frequency,
            testspanning_vrms=test_voltage,
            temperatuur_c=20.0,
            esr_eenheid="mΩ",
            bevestig_wissen=False,
        )
    )


class _EmptyHistoryService:
    def list_measurements(self, filters=None, *, limit=100, offset=0):
        return []

    def get_measurement_detail(self, measurement_id):
        return None


def test_esr_language_switch_preserves_user_input(monkeypatch):
    monkeypatch.setattr(esr_module, "vertaal", _fake_translate)
    monkeypatch.setattr(esr_module, "laad_instellingen", _fake_esr_settings)

    screen = EsrTestScreen(taal="nl_NL")
    screen.nom_cap_input.setText("470")
    screen.meas_cap_input.setText("465")
    screen.meas_esr_input.setText("200")
    screen.safety_check.setChecked(True)
    screen.out_of_range_check.setChecked(True)
    screen.method_combo.setCurrentIndex(1)
    selected_method = screen.method_combo.currentData()

    screen.apply_language("en_US")

    assert screen.title_label.text() == "en_US:scherm.esr_test"
    assert screen.component_group.title() == "en_US:scherm.condensator"
    assert screen.context_group.title() == "en_US:scherm.meetcontext"
    assert screen.measurement_group.title() == "en_US:scherm.meetwaarden"
    assert screen.back_btn.text() == "en_US:knop.terug"
    assert screen.assess_btn.text() == "en_US:knop.beoordeel"
    assert screen.method_combo.currentData() == selected_method
    assert screen.nom_cap_input.text() == "470"
    assert screen.meas_cap_input.text() == "465"
    assert screen.meas_esr_input.text() == "200"
    assert screen.safety_check.isChecked() is True
    assert screen.out_of_range_check.isChecked() is True


def test_history_language_switch_updates_filter_labels_and_keeps_values(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)

    screen = HistoryScreen(
        taal="nl_NL",
        history_service=_EmptyHistoryService(),
    )
    screen.filter_manufacturer.setText("Panasonic")
    screen.filter_series.setText("FM")
    screen.filter_method.setCurrentIndex(2)
    selected_method = screen.filter_method.currentData()

    screen.apply_language("en_US")

    assert screen.filter_tool_label.text() == "en_US:historiek.filter.tool"
    assert screen.filter_manufacturer_label.text() == "en_US:historiek.filter.fabrikant"
    assert screen.filter_series_label.text() == "en_US:historiek.filter.serie"
    assert screen.filter_method_label.text() == "en_US:historiek.filter.meetmethode"
    assert screen.filter_instrument_label.text() == "en_US:historiek.filter.instrument"
    assert screen.filter_frequency_label.text() == "en_US:historiek.filter.frequentie"
    assert screen.filter_status_label.text() == "en_US:historiek.filter.status"
    assert screen.filter_reliability_label.text() == "en_US:historiek.filter.betrouwbaarheid"
    assert screen.filter_manufacturer.text() == "Panasonic"
    assert screen.filter_series.text() == "FM"
    assert screen.filter_method.currentData() == selected_method


def test_main_window_language_switch_updates_current_page_title(monkeypatch):
    monkeypatch.setattr(main_window_module, "vertaal", _fake_translate)
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    monkeypatch.setattr(esr_module, "vertaal", _fake_translate)
    monkeypatch.setattr(esr_module, "laad_instellingen", _fake_esr_settings)
    monkeypatch.setattr(
        main_window_module,
        "laad_instellingen",
        lambda: SimpleNamespace(taal="nl_NL"),
    )

    window = ToolHubWindow()
    window.stack.setCurrentWidget(window.diagnose_page)
    window.taal = "en_US"

    window._apply_language()

    assert window.hub_title_label.text() == "en_US:app.titel"
    assert window.hub_subtitle_label.text() == "en_US:scherm.hoofdmenu"
    assert window.diagnose_back_btn.text() == "en_US:knop.terug"
    assert window.diagnose_title_label.text() == "en_US:scherm.diagnose"
    assert window.esr_page.title_label.text() == "en_US:scherm.esr_test"
    assert window.windowTitle() == "en_US:app.titel — en_US:scherm.diagnose"
