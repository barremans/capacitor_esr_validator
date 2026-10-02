"""
================================================================================
Module:     tests/test_history_robustness.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Regressietests voor read-only Historiek-robuustheid:
            ontbrekende database, ontbrekende measurement-id, meerdere rijen
            en veilige GUI-toestand na een refresh-fout.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste gerichte Historiek-robuustheidstests.
================================================================================
"""

from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

import app.gui.history_screen as history_module
from app.gui.history_screen import HistoryScreen
from app.services.history_service import MeasurementHistoryService
from app.storage.paths import PathService
from app.storage.service import StorageService


@pytest.fixture(scope="module", autouse=True)
def qapplication():
    app = QApplication.instance() or QApplication([])
    yield app


def _fake_translate(key: str, taal: str = "nl_NL", **kwargs) -> str:
    if kwargs:
        return f"{key}:{kwargs}"
    return key


def _measurement(
    measurement_id: int,
    *,
    measured_at_ms: int,
    tool_key: str = "ESR_CAPACITOR",
    method: str = "EX_SITU",
    instrument_name: str = "LCR-ST1",
    capacitance_f: float | None = 470e-6,
    esr_ohm: float | None = 0.12,
):
    return SimpleNamespace(
        id=measurement_id,
        measured_at_ms=measured_at_ms,
        tool_key=tool_key,
        measurement_method=method,
        instrument_name=instrument_name,
        instrument_key="LCR_ST1",
        capacitance_f=capacitance_f,
        esr_ohm=esr_ohm,
    )


def _history_row(measurement, *, manufacturer="TEST", series="SERIES"):
    return {
        "measurement": measurement,
        "manufacturer": manufacturer,
        "series": series,
        "part_number": None,
        "final_status": "waarschijnlijk_goed",
        "reliability_level": "hoog",
    }


class _StaticHistoryService:
    def __init__(self, rows):
        self.rows = list(rows)

    def list_measurements(self, filters=None, *, limit=100, offset=0):
        return self.rows[offset:offset + limit]

    def get_measurement_detail(self, measurement_id):
        return None


class _FailingHistoryService:
    def list_measurements(self, filters=None, *, limit=100, offset=0):
        raise RuntimeError("synthetische leesfout")

    def get_measurement_detail(self, measurement_id):
        raise RuntimeError("synthetische detailfout")


def test_missing_database_returns_empty_without_creating_database(tmp_path):
    paths = PathService(base_dir=tmp_path)
    service = MeasurementHistoryService(path_service_factory=lambda: paths)

    assert not paths.database_path.exists()
    assert service.list_measurements() == []
    assert service.get_measurement_detail(1) is None
    assert not paths.database_path.exists()


def test_missing_measurement_id_in_existing_database_returns_none(tmp_path):
    paths = PathService(base_dir=tmp_path)
    paths.ensure_runtime_directories()

    storage = StorageService(paths.database_path, clock=lambda: 1_700_000_000_000)
    storage.initialize()
    assert paths.database_path.exists()

    service = MeasurementHistoryService(path_service_factory=lambda: paths)

    assert service.get_measurement_detail(999_999) is None


def test_history_screen_handles_multiple_rows(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)

    rows = [
        _history_row(_measurement(2, measured_at_ms=2_000)),
        _history_row(_measurement(1, measured_at_ms=1_000)),
    ]
    screen = HistoryScreen(
        taal="nl_NL",
        history_service=_StaticHistoryService(rows),
    )

    screen.refresh()

    assert screen.table.rowCount() == 2
    assert screen.table.item(0, 0).data(history_module.Qt.ItemDataRole.UserRole) == 2
    assert screen.table.item(1, 0).data(history_module.Qt.ItemDataRole.UserRole) == 1
    assert not screen.detail_btn.isEnabled()
    assert not screen.repeat_btn.isEnabled()

    screen.table.selectRow(0)
    screen._update_detail_button()

    assert screen.detail_btn.isEnabled()
    assert screen.repeat_btn.isEnabled()


def test_refresh_error_clears_rows_and_disables_actions(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)

    screen = HistoryScreen(
        taal="nl_NL",
        history_service=_StaticHistoryService(
            [_history_row(_measurement(1, measured_at_ms=1_000))]
        ),
    )
    screen.refresh()
    screen.table.selectRow(0)
    screen._update_detail_button()

    assert screen.detail_btn.isEnabled()
    assert screen.repeat_btn.isEnabled()

    screen._history_service = _FailingHistoryService()
    screen.refresh()

    assert screen.table.rowCount() == 0
    assert not screen.detail_btn.isEnabled()
    assert not screen.repeat_btn.isEnabled()
    assert "historiek.fout" in screen.state_label.text()
