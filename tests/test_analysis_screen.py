"""
================================================================================
Module:     tests/test_analysis_screen.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.2
Datum:      2026-10-09
Auteur:     Bart Bossuyt

Doel:       GUI-regressietests voor AnalysisScreen (Fase 7B).

            Volgt dezelfde aanpak als tests/test_documentation_screen.py:
            QT_QPA_PLATFORM=offscreen, een lokale _app()-helper en geen
            pytest-qt dependency. Signaaltests gebruiken QSignalSpy uit
            PySide6.QtTest.

            Gebruikt een stub-AnalysisService zodat er geen database of
            QtCharts-rendering nodig is om de logica te bewijzen.

Wijzigingen:
  v1.0.0 (2026-10-09)  Eerste GUI-tests (met qtbot).
  v1.0.1 (2026-10-09)  Fix: pytest-qt is geen dependency van dit project.
                        Herschreven zonder qtbot, in de stijl van
                        tests/test_documentation_screen.py.
  v1.0.2 (2026-10-09)  Fix: tests die de service-aanroepen inspecteren
                        wissen eerst stub_service.calls, en pakken de
                        laatste aanroep in plaats van de eerste. Dat
                        maakt ze robuust tegen init-refresh en toekomstige
                        extra refresh()-rondes.
================================================================================
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from app.helpers.analysis_series import ScatterPoint, TimeSeriesPoint
from app.gui.analysis_screen import (
    _AGGREGATION_DAY,
    _AGGREGATION_MONTH,
    _AGGREGATION_RAW,
    _CHART_TYPE_CAPACITANCE,
    _CHART_TYPE_DISSIPATION,
    _CHART_TYPE_ESR,
    _CHART_TYPE_SCATTER,
    AnalysisScreen,
)


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _ms(year: int, month: int, day: int) -> int:
    return int(datetime(year, month, day, tzinfo=timezone.utc).timestamp() * 1000)


# ---------------------------------------------------------------------------
# Stub-service
# ---------------------------------------------------------------------------

class _StubAnalysisService:
    """Bevriest de reeksen en registreert de filteraanroepen."""

    def __init__(
        self,
        *,
        esr_series: list[TimeSeriesPoint] | None = None,
        capacitance_series: list[TimeSeriesPoint] | None = None,
        dissipation_series: list[TimeSeriesPoint] | None = None,
        scatter: list[ScatterPoint] | None = None,
    ) -> None:
        self._esr = esr_series or []
        self._c = capacitance_series or []
        self._d = dissipation_series or []
        self._scatter = scatter or []
        self.calls: list[tuple[str, dict[str, Any], str]] = []

    def esr_series(self, filters, *, aggregation):
        self.calls.append(("esr", dict(filters or {}), aggregation))
        return list(self._esr)

    def capacitance_series(self, filters, *, aggregation):
        self.calls.append(("c", dict(filters or {}), aggregation))
        return list(self._c)

    def dissipation_series(self, filters, *, aggregation):
        self.calls.append(("d", dict(filters or {}), aggregation))
        return list(self._d)

    def scatter_esr_vs_capacitance(self, filters):
        self.calls.append(("scatter", dict(filters or {}), ""))
        return list(self._scatter)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def stub_service() -> _StubAnalysisService:
    return _StubAnalysisService(
        esr_series=[
            TimeSeriesPoint(_ms(2026, 10, 1), 0.1, 1, "ESR_CAPACITOR"),
            TimeSeriesPoint(_ms(2026, 10, 2), 0.2, 2, "ESR_CAPACITOR"),
        ],
    )


@pytest.fixture
def screen(stub_service: _StubAnalysisService) -> AnalysisScreen:
    _app()
    widget = AnalysisScreen(taal="nl_NL", analysis_service=stub_service)
    yield widget
    widget.deleteLater()


# ---------------------------------------------------------------------------
# Bouw
# ---------------------------------------------------------------------------

def test_screen_builds_with_expected_widgets(screen: AnalysisScreen) -> None:
    assert screen.back_btn.text() != ""
    assert screen.title_label.text() != ""
    assert screen.chart_type_combo.count() == 4
    assert screen.aggregation_combo.count() == 4


def test_default_chart_type_is_esr(screen: AnalysisScreen) -> None:
    assert screen.chart_type_combo.currentData() == _CHART_TYPE_ESR


def test_default_aggregation_is_raw(screen: AnalysisScreen) -> None:
    assert screen.aggregation_combo.currentData() == _AGGREGATION_RAW


# ---------------------------------------------------------------------------
# Service-aanroepen
# ---------------------------------------------------------------------------

def test_refresh_calls_esr_series_when_type_is_esr(
    screen: AnalysisScreen, stub_service: _StubAnalysisService
) -> None:
    stub_service.calls.clear()
    screen.refresh()
    assert any(call[0] == "esr" for call in stub_service.calls)


def test_changing_chart_type_to_capacitance_calls_capacitance(
    screen: AnalysisScreen, stub_service: _StubAnalysisService
) -> None:
    stub_service.calls.clear()
    index = screen.chart_type_combo.findData(_CHART_TYPE_CAPACITANCE)
    screen.chart_type_combo.setCurrentIndex(index)
    assert any(call[0] == "c" for call in stub_service.calls)


def test_changing_chart_type_to_dissipation_calls_dissipation(
    screen: AnalysisScreen, stub_service: _StubAnalysisService
) -> None:
    stub_service.calls.clear()
    index = screen.chart_type_combo.findData(_CHART_TYPE_DISSIPATION)
    screen.chart_type_combo.setCurrentIndex(index)
    assert any(call[0] == "d" for call in stub_service.calls)


def test_changing_chart_type_to_scatter_calls_scatter(
    screen: AnalysisScreen, stub_service: _StubAnalysisService
) -> None:
    stub_service.calls.clear()
    index = screen.chart_type_combo.findData(_CHART_TYPE_SCATTER)
    screen.chart_type_combo.setCurrentIndex(index)
    assert any(call[0] == "scatter" for call in stub_service.calls)


def test_changing_aggregation_is_passed_through(
    screen: AnalysisScreen, stub_service: _StubAnalysisService
) -> None:
    stub_service.calls.clear()
    index = screen.aggregation_combo.findData(_AGGREGATION_DAY)
    screen.aggregation_combo.setCurrentIndex(index)
    assert any(call[2] == _AGGREGATION_DAY for call in stub_service.calls)


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

def test_filters_are_passed_to_service(
    screen: AnalysisScreen, stub_service: _StubAnalysisService
) -> None:
    stub_service.calls.clear()
    screen.filter_manufacturer.setText("Panasonic")
    screen.filter_series.setText("FR")
    screen.refresh()
    # Pak de laatste esr-aanroep; er kunnen meerdere refresh()-rondes zijn
    # (bijv. door een taalwissel of toekomstige interne refresh).
    esr_calls = [call for call in stub_service.calls if call[0] == "esr"]
    assert esr_calls, "refresh() moet minimaal één esr_series()-aanroep doen."
    filters = esr_calls[-1][1]
    assert filters.get("manufacturer") == "Panasonic"
    assert filters.get("series") == "FR"
    assert filters.get("tool_key") == "ESR_CAPACITOR"


def test_invalid_date_shows_error_and_does_not_call_service(
    screen: AnalysisScreen, stub_service: _StubAnalysisService
) -> None:
    stub_service.calls.clear()
    screen.filter_date_from.setText("niet-een-datum")
    screen.refresh()
    assert stub_service.calls == []
    assert screen.state_label.text() != ""


def test_date_order_error_is_reported(
    screen: AnalysisScreen, stub_service: _StubAnalysisService
) -> None:
    stub_service.calls.clear()
    screen.filter_date_from.setText("2026-10-10")
    screen.filter_date_to.setText("2026-10-01")
    screen.refresh()
    assert stub_service.calls == []
    assert screen.state_label.text() != ""


def test_clear_filters_resets_inputs(screen: AnalysisScreen) -> None:
    screen.filter_manufacturer.setText("X")
    screen.filter_series.setText("Y")
    screen.filter_date_from.setText("2026-10-01")
    screen._clear_filters()
    assert screen.filter_manufacturer.text() == ""
    assert screen.filter_series.text() == ""
    assert screen.filter_date_from.text() == ""


# ---------------------------------------------------------------------------
# Lege staat
# ---------------------------------------------------------------------------

def test_empty_series_shows_empty_state() -> None:
    _app()
    stub = _StubAnalysisService(esr_series=[])
    widget = AnalysisScreen(taal="nl_NL", analysis_service=stub)
    try:
        widget.refresh()
        assert widget.state_label.text() != ""
    finally:
        widget.deleteLater()


# ---------------------------------------------------------------------------
# Taalwissel
# ---------------------------------------------------------------------------

def test_apply_language_changes_title(screen: AnalysisScreen) -> None:
    nl_title = screen.title_label.text()
    screen.apply_language("en_US")
    assert screen.title_label.text() != nl_title
    assert screen.title_label.text() != ""


def test_apply_language_updates_combo_items(screen: AnalysisScreen) -> None:
    screen.apply_language("en_US")
    labels = [
        screen.chart_type_combo.itemText(i)
        for i in range(screen.chart_type_combo.count())
    ]
    assert all(lbl for lbl in labels)
    assert any(
        "time" in lbl.lower() or "esr" in lbl.lower() for lbl in labels
    )


# ---------------------------------------------------------------------------
# Signaal
# ---------------------------------------------------------------------------

def test_back_button_emits_signal(stub_service: _StubAnalysisService) -> None:
    _app()
    widget = AnalysisScreen(taal="nl_NL", analysis_service=stub_service)
    try:
        spy = QSignalSpy(widget.back_requested)
        widget.back_btn.click()
        assert spy.count() == 1
    finally:
        widget.deleteLater()


def test_escape_shortcut_emits_back_signal(
    stub_service: _StubAnalysisService,
) -> None:
    """Esc op de Analyse-pagina moet hetzelfde signaal geven als de terug-knop."""
    _app()
    widget = AnalysisScreen(taal="nl_NL", analysis_service=stub_service)
    try:
        spy = QSignalSpy(widget.back_requested)
        widget.sc_back.activated.emit()
        assert spy.count() == 1
    finally:
        widget.deleteLater()