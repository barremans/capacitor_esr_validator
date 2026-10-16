"""
================================================================================
Module:     tests/test_history_screen_report_button.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.2.0
Datum:      2026-10-16
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de "Rapport"-knop in HistoryScreen.

Wijzigingen:
  v1.0.0 (2026-10-10)  Eerste versie.
  v1.1.0 (2026-10-16)  Fase 11A.1: test voor selection_changed-signaal.
  v1.1.1 (2026-10-16)  Fase 11A.1-fix: correcte tests voor dedup.
  v1.2.0 (2026-10-16)  Fase 11A.2: test dat de rapport-knop de
                        checkbox-selectie gebruikt voor scope 'selectie'.
================================================================================
"""

from __future__ import annotations

import os
from enum import Enum
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from app.gui.history_screen import HistoryScreen


@pytest.fixture(scope="module", autouse=True)
def qapplication():
    app = QApplication.instance() or QApplication([])
    yield app


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


class _Service:
    def __init__(self, total=3):
        self.rows = [_overview_row(i + 1) for i in range(total)]

    def list_measurements(self, filters=None, *, limit=100, offset=0):
        return self.rows[offset: offset + limit]

    def get_measurement_detail(self, measurement_id):
        return None


def test_report_knop_bestaat_en_is_uitgeschakeld():
    screen = HistoryScreen(taal="nl_NL", history_service=_Service())
    assert screen.report_btn.isEnabled() is False


def test_report_knop_gaat_aan_bij_selectie():
    screen = HistoryScreen(taal="nl_NL", history_service=_Service())
    screen.refresh()
    screen.table.setCurrentCell(0, 1)
    assert screen.report_btn.isEnabled() is True


def test_report_knop_opent_dialoog(monkeypatch):
    screen = HistoryScreen(taal="nl_NL", history_service=_Service())
    screen.refresh()
    screen.table.setCurrentCell(0, 1)

    geopend = {}

    monkeypatch.setattr(
        "app.gui.history_screen.HistoryScreen._open_report_dialog",
        lambda self, mid: geopend.setdefault("measurement_id", mid),
    )

    screen._show_report_for_selected()
    assert geopend["measurement_id"] == 1


# ---------------------------------------------------------------------------
# 11A.1 — selection_changed-signaal
# ---------------------------------------------------------------------------

def test_selection_changed_signal_vuurt_bij_checkbox_wijziging():
    screen = HistoryScreen(taal="nl_NL", history_service=_Service())
    screen.refresh()

    spy = QSignalSpy(screen.selection_changed)
    screen.table.item(0, 0).setCheckState(Qt.CheckState.Checked)
    assert spy.count() >= 1


def test_selection_changed_signal_vuurt_bij_rij_selectie():
    screen = HistoryScreen(taal="nl_NL", history_service=_Service())
    screen.refresh()

    spy = QSignalSpy(screen.selection_changed)
    screen.table.setCurrentCell(0, 1)
    assert spy.count() >= 1


def test_selection_changed_signal_vuurt_wanneer_refresh_selectie_wist():
    screen = HistoryScreen(taal="nl_NL", history_service=_Service())
    screen.refresh()
    screen.table.item(0, 0).setCheckState(Qt.CheckState.Checked)

    spy = QSignalSpy(screen.selection_changed)
    screen.refresh()

    assert spy.count() >= 1


def test_selection_changed_signal_vuurt_niet_tweemaal_zonder_wijziging():
    screen = HistoryScreen(taal="nl_NL", history_service=_Service())
    screen.refresh()
    spy = QSignalSpy(screen.selection_changed)
    screen.refresh()
    assert spy.count() == 0


# ---------------------------------------------------------------------------
# 11A.2 — checkbox-selectie krijgt voorrang op rij-selectie
# ---------------------------------------------------------------------------

def test_rapport_knop_gebruikt_checkbox_selectie(monkeypatch):
    """Bij een checkbox-selectie opent de knop een multi-rapport."""
    screen = HistoryScreen(taal="nl_NL", history_service=_Service())
    screen.refresh()
    # Vink twee checkboxen aan.
    screen.table.item(0, 0).setCheckState(Qt.CheckState.Checked)
    screen.table.item(1, 0).setCheckState(Qt.CheckState.Checked)

    geopend = {"ids": None, "scope": None}

    def _fake_multi(self, ids, *, scope):
        geopend["ids"] = list(ids)
        geopend["scope"] = scope

    monkeypatch.setattr(
        "app.gui.history_screen.HistoryScreen._open_report_dialog_voor_ids",
        _fake_multi,
    )

    screen._show_report_for_selected()

    assert geopend["ids"] is not None
    assert len(geopend["ids"]) == 2
    assert geopend["scope"] == "Selectie"


def test_rapport_knop_valt_terug_op_rij_selectie_zonder_checkbox(monkeypatch):
    """Zonder checkbox-selectie gebruikt de knop de rij-selectie (scope enkel)."""
    screen = HistoryScreen(taal="nl_NL", history_service=_Service())
    screen.refresh()
    screen.table.setCurrentCell(0, 1)

    geopend = {"measurement_id": None}

    monkeypatch.setattr(
        "app.gui.history_screen.HistoryScreen._open_report_dialog",
        lambda self, mid: geopend.__setitem__("measurement_id", mid),
    )

    screen._show_report_for_selected()
    assert geopend["measurement_id"] == 1