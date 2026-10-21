"""
================================================================================
Module:     tests/test_main_window_report_menu.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.4.1
Datum:      2026-10-20
Auteur:     Bart Bossuyt

Doel:       Regressietests voor het menu-item "Rapport maken…".

Wijzigingen:
  v1.0.0 (2026-10-10)  Eerste versie.
  v1.0.1 (2026-10-10)  Fix: _vind_actie gebruikte addMenu("x").
  v1.0.2 (2026-10-10)  Fix: _vind_actie gebruikt menubar.actions().
  v1.0.3 (2026-10-10)  Fix: __init__ respecteert parameter taal.
  v1.0.4 (2026-10-10)  Fix: deleteLater() verwerken via processEvents().
  v1.1.0 (2026-10-16)  Fase 11A.1: menu-item disabled zonder selectie.
  v1.2.0 (2026-10-16)  Fase 11A.2: menu-item wordt ook enabled op Analyse
                        met een checkbox-selectie.
  v1.3.0 (2026-10-16)  Fase 11B: menu-item heeft een tooltip die vertaalt mee.
  v1.4.0 (2026-10-16)  Fase 11C: menu-item heeft een icoon. De nieuwe test
                        test_rapport_action_heeft_icoon gebruikt geen
                        niet-bestaande _app-fixture meer; de QApplication
                        wordt lokaal opgehaald via de bestaande
                        qapplication-fixture of QApplication.instance().
  v1.4.1 (2026-10-20)  Fase 11G.5-fix: _AnalysisStub heeft nu de
                        measurement_ids-parameter (keyword-only, default
                        None) op alle methodes. Sinds AnalysisService
                        v1.1.0 roept AnalysisScreen deze methodes aan met
                        measurement_ids=..., en zonder die parameter
                        faalde de stub met "unexpected keyword argument
                        'measurement_ids'". Daardoor bleef de
                        selectietabel leeg en faalde
                        test_rapport_action_enabled_op_analyse_met_selectie
                        met AttributeError op selection_table.item(0,0).
================================================================================
"""

from __future__ import annotations

import os
from enum import Enum
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication

from app.gui.main_window import ToolHubWindow


@pytest.fixture(scope="module", autouse=True)
def qapplication():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def window():
    w = ToolHubWindow(taal="nl_NL", check_on_startup=False)
    QApplication.processEvents()
    yield w
    w.close()
    QApplication.processEvents()


class _EnumValue(str, Enum):
    VALUE = "VALUE"


def _measurement(measurement_id: int):
    return SimpleNamespace(
        id=measurement_id,
        measurement_session_id=10,
        measured_at_ms=1_700_000_000_000 + measurement_id,
        tool_key="ESR_CAPACITOR",
        measurement_method=_EnumValue.VALUE,
        instrument_key="LCR_ST1",
        instrument_name="LCR-ST1",
        instrument_profile_version=None,
        frequency_hz=1000.0,
        test_voltage_vrms=0.6,
        temperature_c=20.0,
        power_off_confirmed=True,
        discharged_confirmed=True,
        residual_voltage_before_v=None,
        residual_voltage_after_v=None,
        capacitance_f=465e-6,
        esr_ohm=0.2,
        dissipation_factor_d=None,
        quality_factor_q=None,
        impedance_z_ohm=None,
        reactance_x_ohm=None,
        out_of_range=False,
        open_suspected=False,
        short_suspected=False,
        unstable_reading=False,
        parallel_components_notes=None,
        mechanical_condition_notes=None,
        notes=None,
        record_status=None,
        supersedes_measurement_id=None,
        invalid_reason=None,
    )


def _overview_row(measurement_id: int):
    return {
        "measurement": _measurement(measurement_id),
        "manufacturer": "TEST",
        "series": "SYN",
        "part_number": None,
        "final_status": "aandachtspunt",
        "reliability_level": "laag",
    }


class _HistoryStub:
    def __init__(self, total=3):
        self.rows = [_overview_row(i + 1) for i in range(total)]

    def list_measurements(self, filters=None, *, limit=100, offset=0):
        return self.rows[offset: offset + limit]

    def get_measurement_detail(self, measurement_id):
        return None


class _AnalysisStub:
    """Stub voor AnalysisService.

    Sinds AnalysisService v1.1.0 accepteren alle methodes een
    keyword-only measurement_ids-parameter. De stub negeert die; de
    tests richten zich op het menu-item, niet op de scope-selectie.
    """

    def __init__(self, rows):
        self.rows = rows

    def load_rows(self, filters=None, *, measurement_ids=None):
        return list(self.rows)

    def esr_series(self, filters=None, *, aggregation="raw", measurement_ids=None):
        return []

    def capacitance_series(self, filters=None, *, aggregation="raw", measurement_ids=None):
        return []

    def dissipation_series(self, filters=None, *, aggregation="raw", measurement_ids=None):
        return []

    def scatter_esr_vs_capacitance(self, filters=None, *, measurement_ids=None):
        return []


def _alle_menu_acties(window):
    resultaat = []
    menubar = window.menuBar()
    for menu_actie in menubar.actions():
        try:
            menu = menu_actie.menu()
        except RuntimeError:
            continue
        if menu is None:
            continue
        for actie in menu.actions():
            try:
                tekst = actie.text()
            except RuntimeError:
                continue
            resultaat.append((tekst, actie))
    return resultaat


def _vind_actie(window, tekst: str):
    for act_tekst, actie in _alle_menu_acties(window):
        if act_tekst == tekst:
            return actie
    return None


def _beschikbare_teksten(window):
    return [tekst for tekst, _ in _alle_menu_acties(window)]


def test_menu_dump_bij_fout(window):
    teksten = _beschikbare_teksten(window)
    assert len(teksten) > 0


def test_menu_item_rapport_bestaat(window):
    actie = _vind_actie(window, "Rapport maken…")
    assert actie is not None, (
        "Menu-item 'Rapport maken…' niet gevonden. "
        f"Beschikbare items: {_beschikbare_teksten(window)}"
    )


def test_menu_item_rapport_heeft_sneltoets(window):
    actie = _vind_actie(window, "Rapport maken…")
    assert actie is not None
    assert actie.shortcut() == QKeySequence("Ctrl+P")


def test_menu_item_rapport_vertaalt_mee_naar_engels(window):
    window.taal = "en_US"
    window._apply_language()
    QApplication.processEvents()

    actie = _vind_actie(window, "Create report…")
    assert actie is not None, (
        "Menu-item 'Create report…' niet gevonden na taalwissel. "
        f"Beschikbare items: {_beschikbare_teksten(window)}"
    )


# ---------------------------------------------------------------------------
# 11A.1 + 11A.2 — enabled-state op basis van de actieve pagina
# ---------------------------------------------------------------------------

def _activeer_history_met_selectie(window):
    stub = _HistoryStub(total=3)
    window.history_page._history_service = stub
    window._show_history()
    window.history_page.table.setCurrentCell(0, 1)
    QApplication.processEvents()


def _activeer_analysis_met_selectie(window):
    stub = _AnalysisStub([_overview_row(i + 1) for i in range(3)])
    window.analysis_page._analysis_service = stub
    window._show_analysis()
    QApplication.processEvents()
    window.analysis_page.selection_table.item(0, 0).setCheckState(
        __import__("PySide6.QtCore", fromlist=["Qt"]).Qt.CheckState.Checked
    )
    QApplication.processEvents()


def test_rapport_action_disabled_op_hub(window):
    window._show_hub()
    QApplication.processEvents()
    assert window.rapport_action is not None
    assert window.rapport_action.isEnabled() is False


def test_rapport_action_disabled_op_diagnose(window):
    window._show_diagnose()
    QApplication.processEvents()
    assert window.rapport_action.isEnabled() is False


def test_rapport_action_disabled_op_historiek_zonder_selectie(window):
    stub = _HistoryStub(total=3)
    window.history_page._history_service = stub
    window._show_history()
    QApplication.processEvents()
    assert window.rapport_action.isEnabled() is False


def test_rapport_action_enabled_op_historiek_met_selectie(window):
    _activeer_history_met_selectie(window)
    assert window.rapport_action.isEnabled() is True


def test_rapport_action_disabled_op_analyse_zonder_selectie(window):
    stub = _AnalysisStub([_overview_row(i + 1) for i in range(3)])
    window.analysis_page._analysis_service = stub
    window._show_analysis()
    QApplication.processEvents()
    assert window.rapport_action.isEnabled() is False


def test_rapport_action_enabled_op_analyse_met_selectie(window):
    _activeer_analysis_met_selectie(window)
    assert window.rapport_action.isEnabled() is True


def test_rapport_action_heeft_tooltip_nl(window):
    window._apply_language()
    QApplication.processEvents()
    assert window.rapport_action.toolTip() == (
        "Selecteer eerst een meting in de historiek."
    )


def test_rapport_action_heeft_tooltip_en(window):
    window.taal = "en_US"
    window._apply_language()
    QApplication.processEvents()
    assert window.rapport_action.toolTip() == (
        "Select a measurement in the history first."
    )


# ---------------------------------------------------------------------------
# Fase 11C — icoon op het Rapport-menu-item
# ---------------------------------------------------------------------------

def test_rapport_action_heeft_icoon(window):
    """Rapport maken… heeft een icoon zodra report.png bestaat.

    Conform de projectafspraak gebruiken we geen niet-bestaande _app-fixture:
    de bestaande `window`-fixture levert al een ToolHubWindow, en de
    QApplication wordt door de autouse `qapplication`-fixture op moduleniveau
    gezet.
    """
    from app.helpers.icon_paths import icoon_pad

    if icoon_pad("report") is None:
        pytest.skip("Geen report.png aanwezig; plaats eerst placeholders.")

    QApplication.processEvents()
    assert window.rapport_action is not None
    assert not window.rapport_action.icon().isNull(), (
        "Rapport-actie heeft geen icoon"
    )