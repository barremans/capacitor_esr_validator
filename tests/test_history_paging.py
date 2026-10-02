"""
================================================================================
Module:     tests/test_history_paging.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Regressietests voor limit/offset paging in centrale Historiek.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste pagingtests: look-ahead, vorige/volgende,
                        filter-reset en taalwissel met behoud van pagina.
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


@pytest.fixture(scope="module", autouse=True)
def qapplication():
    app = QApplication.instance() or QApplication([])
    yield app


def _fake_translate(key: str, taal: str = "nl_NL", **kwargs) -> str:
    if key == "historiek.paging.pagina":
        return f"{taal}:page:{kwargs['pagina']}"
    return f"{taal}:{key}"


def _measurement(measurement_id: int):
    return SimpleNamespace(
        id=measurement_id,
        measured_at_ms=measurement_id,
        tool_key="ESR_CAPACITOR",
        measurement_method="EX_SITU",
        instrument_name="LCR-ST1",
        instrument_key="LCR_ST1",
        capacitance_f=470e-6,
        esr_ohm=0.12,
    )


def _row(measurement_id: int):
    return {
        "measurement": _measurement(measurement_id),
        "manufacturer": "TEST",
        "series": "SERIES",
        "part_number": None,
        "final_status": "waarschijnlijk_goed",
        "reliability_level": "hoog",
    }


class _PagedHistoryService:
    def __init__(self, total: int):
        self.rows = [_row(index + 1) for index in range(total)]
        self.calls = []

    def list_measurements(self, filters=None, *, limit=100, offset=0):
        self.calls.append(
            {
                "filters": dict(filters or {}),
                "limit": limit,
                "offset": offset,
            }
        )
        return self.rows[offset: offset + limit]

    def get_measurement_detail(self, measurement_id):
        return None


def test_first_page_uses_lookahead_and_enables_next(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    service = _PagedHistoryService(total=205)
    screen = HistoryScreen(taal="nl_NL", history_service=service)

    screen.refresh()

    assert service.calls[-1]["limit"] == 101
    assert service.calls[-1]["offset"] == 0
    assert screen.table.rowCount() == 100
    assert not screen.previous_page_btn.isEnabled()
    assert screen.next_page_btn.isEnabled()
    assert screen.page_label.text() == "nl_NL:page:1"


def test_next_page_uses_offset_and_last_page_disables_next(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    service = _PagedHistoryService(total=205)
    screen = HistoryScreen(taal="nl_NL", history_service=service)

    screen.refresh()
    screen._next_page()

    assert service.calls[-1]["offset"] == 100
    assert screen.table.rowCount() == 100
    assert screen.previous_page_btn.isEnabled()
    assert screen.next_page_btn.isEnabled()
    assert screen.page_label.text() == "nl_NL:page:2"

    screen._next_page()

    assert service.calls[-1]["offset"] == 200
    assert screen.table.rowCount() == 5
    assert screen.previous_page_btn.isEnabled()
    assert not screen.next_page_btn.isEnabled()
    assert screen.page_label.text() == "nl_NL:page:3"


def test_previous_page_moves_back_exactly_one_page(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    service = _PagedHistoryService(total=205)
    screen = HistoryScreen(taal="nl_NL", history_service=service)

    screen.refresh()
    screen._next_page()
    screen._previous_page()

    assert service.calls[-1]["offset"] == 0
    assert screen.page_label.text() == "nl_NL:page:1"
    assert not screen.previous_page_btn.isEnabled()


def test_apply_filters_resets_to_first_page(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    service = _PagedHistoryService(total=205)
    screen = HistoryScreen(taal="nl_NL", history_service=service)

    screen.refresh()
    screen._next_page()
    assert screen.page_label.text() == "nl_NL:page:2"

    screen.filter_manufacturer.setText("TEST")
    screen._apply_filters()

    assert service.calls[-1]["offset"] == 0
    assert service.calls[-1]["filters"]["manufacturer"] == "TEST"
    assert screen.page_label.text() == "nl_NL:page:1"


def test_language_switch_preserves_current_page(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    service = _PagedHistoryService(total=205)
    screen = HistoryScreen(taal="nl_NL", history_service=service)

    screen.refresh()
    screen._next_page()
    assert screen.page_label.text() == "nl_NL:page:2"

    screen.apply_language("en_US")

    assert screen.page_label.text() == "en_US:page:2"
    assert screen.previous_page_btn.text() == "en_US:historiek.paging.vorige"
    assert screen.next_page_btn.text() == "en_US:historiek.paging.volgende"
    assert service.calls[-1]["offset"] == 100
