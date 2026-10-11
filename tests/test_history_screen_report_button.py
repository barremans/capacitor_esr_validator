"""
================================================================================
Module:     tests/test_history_screen_report_button.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-10
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de "Rapport"-knop in HistoryScreen (Fase 8C).

Wijzigingen:
  v1.0.0 (2026-10-10)  Eerste versie.
================================================================================
"""

from __future__ import annotations

import os
from enum import Enum
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt
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

    # Selecteer de eerste rij (via de tijd-kolom, niet de checkbox).
    screen.table.setCurrentCell(0, 1)
    assert screen.report_btn.isEnabled() is True


def test_report_knop_opent_dialoog(monkeypatch):
    screen = HistoryScreen(taal="nl_NL", history_service=_Service())
    screen.refresh()
    screen.table.setCurrentCell(0, 1)

    geopend = {}

    class _FakeDialog:
        def __init__(self, measurement_id, **kwargs):
            geopend["measurement_id"] = measurement_id
        def exec(self):
            return 0

    monkeypatch.setattr(
        "app.gui.history_screen.HistoryScreen._open_report_dialog",
        lambda self, mid: geopend.setdefault("measurement_id", mid),
    )

    screen._show_report_for_selected()
    assert geopend["measurement_id"] == 1