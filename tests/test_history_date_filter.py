"""
================================================================================
Module:     tests/test_history_date_filter.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de optionele lokale datum/periodefilter
            van de centrale read-only Historiek.
================================================================================
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

import app.gui.history_screen as history_module
from app.gui.history_screen import HistoryScreen
from app.helpers.history_filters import (
    build_history_filters,
    parse_local_date_start_ms,
    parse_local_date_end_ms,
)


@pytest.fixture(scope="module", autouse=True)
def qapplication():
    app = QApplication.instance() or QApplication([])
    yield app


def _fake_translate(key: str, taal: str = "nl_NL", **kwargs) -> str:
    mapping = {
        "historiek.filter.datum_formaat_fout": "ongeldige datum",
        "historiek.filter.datum_volgorde_fout": "ongeldige periode",
    }
    return mapping.get(key, key)


class _CapturingHistoryService:
    def __init__(self):
        self.filters = None

    def list_measurements(self, filters=None, *, limit=100, offset=0):
        self.filters = dict(filters or {})
        return []

    def get_measurement_detail(self, measurement_id):
        return None


def test_empty_dates_do_not_add_date_filters():
    assert parse_local_date_start_ms("") is None
    assert parse_local_date_end_ms("   ") is None

    result = build_history_filters(
        manufacturer=" TEST ",
        measured_from_ms=None,
        measured_to_ms=None,
    )

    assert result == {"manufacturer": "TEST"}


def test_single_local_day_uses_inclusive_day_boundaries():
    day = date(2026, 10, 1)

    start_ms = parse_local_date_start_ms("2026-10-01")
    end_ms = parse_local_date_end_ms("2026-10-01")

    expected_start = int(
        datetime.combine(day, datetime.min.time()).timestamp() * 1000
    )
    expected_end = int(
        datetime.combine(
            day + timedelta(days=1),
            datetime.min.time(),
        ).timestamp() * 1000
    ) - 1

    assert start_ms == expected_start
    assert end_ms == expected_end
    assert start_ms <= end_ms


def test_history_screen_passes_date_range_to_existing_storage_filters(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    service = _CapturingHistoryService()
    screen = HistoryScreen(taal="nl_NL", history_service=service)

    screen.filter_date_from.setText("2026-09-01")
    screen.filter_date_to.setText("2026-10-01")
    screen.refresh()

    assert service.filters["measured_from_ms"] == parse_local_date_start_ms(
        "2026-09-01"
    )
    assert service.filters["measured_to_ms"] == parse_local_date_end_ms(
        "2026-10-01"
    )


def test_invalid_date_is_visible_and_does_not_query_service(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    service = _CapturingHistoryService()
    screen = HistoryScreen(taal="nl_NL", history_service=service)

    screen.filter_date_from.setText("01/10/2026")
    screen.refresh()

    assert service.filters is None
    assert "ongeldige datum" in screen.state_label.text()


def test_reversed_date_range_is_rejected_before_query(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    service = _CapturingHistoryService()
    screen = HistoryScreen(taal="nl_NL", history_service=service)

    screen.filter_date_from.setText("2026-10-02")
    screen.filter_date_to.setText("2026-10-01")
    screen.refresh()

    assert service.filters is None
    assert "ongeldige periode" in screen.state_label.text()


def test_clear_filters_clears_both_dates(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    service = _CapturingHistoryService()
    screen = HistoryScreen(taal="nl_NL", history_service=service)

    screen.filter_date_from.setText("2026-09-01")
    screen.filter_date_to.setText("2026-10-01")
    screen._clear_filters()

    assert screen.filter_date_from.text() == ""
    assert screen.filter_date_to.text() == ""
