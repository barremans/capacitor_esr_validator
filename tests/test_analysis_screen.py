"""
================================================================================
Module:     tests/test_analysis_screen.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.6.2
Datum:      2026-10-20
Auteur:     Bart Bossuyt

Doel:       GUI-regressietests voor AnalysisScreen.

Wijzigingen:
  v1.0.0 (2026-10-09)  Eerste GUI-tests.
  v1.0.1 (2026-10-09)  Fix: pytest-qt is geen dependency.
  v1.0.2 (2026-10-09)  Fix: tests inspecteren laatste aanroep.
  v1.1.0 (2026-10-16)  Fase 11A.1: selectielijst, teller, wissen, export.
  v1.3.0 (2026-10-16)  Fase 11A.2: rapport-knop naast export-knop.
  v1.3.1 (2026-10-16)  Fase 11A.2-fix: echte implementatie testen.
  v1.4.0 (2026-10-20)  Fase 11G.3: vijf tests voor as-schaling en
                        tickformaat.
  v1.5.0 (2026-10-20)  Fase 11G.4: vijf tests voor zoom/pan.
  v1.6.0 (2026-10-20)  Fase 11G.5: zes tests voor selectie-gedreven
                        grafiek en klikbare scatter-punten.
  v1.6.1 (2026-10-20)  Fase 11G.5-fix: drie tests aangepast aan de
                        nieuwe refresh(preserve_selection=True)-flow.
  v1.6.2 (2026-10-20)  Fase 11G.5-fix: de scatter-klik-tests roepen nu
                        expliciet widget.refresh() aan na het zetten van
                        chart_type SCATTER, zodat de scatter-series
                        gegarandeerd getekend zijn vóór de klik. Zonder
                        die expliciete refresh bleef widget.chart.series()
                        leeg in de offscreen-testomgeving. De bestaande
                        test_selectie_wordt_gewist_bij_refresh is
                        ongewijzigd; de productiecode uit v1.6.2 zet de
                        "gewist"-melding weer bij een gewone refresh.
================================================================================
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCharts import QDateTimeAxis, QValueAxis
from PySide6.QtCore import Qt
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
    _EXPORT_SCOPE_FILTERED,
    _EXPORT_SCOPE_SELECTED,
    _EXPORT_TYPE_BOTH,
    _EXPORT_TYPE_DETAIL,
    _EXPORT_TYPE_OVERVIEW,
    AnalysisScreen,
)


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _ms(year: int, month: int, day: int) -> int:
    return int(datetime(year, month, day, tzinfo=timezone.utc).timestamp() * 1000)


class _EnumValue(str, Enum):
    VALUE = "VALUE"


class _FakeMeasurement:
    def __init__(
        self,
        measurement_id: int,
        measured_at_ms: int,
        *,
        tool_key: str = "ESR_CAPACITOR",
        esr_ohm: float | None = None,
        capacitance_f: float | None = None,
        dissipation_factor_d: float | None = None,
    ) -> None:
        self.id = measurement_id
        self.measured_at_ms = measured_at_ms
        self.tool_key = tool_key
        self.esr_ohm = esr_ohm
        self.capacitance_f = capacitance_f
        self.dissipation_factor_d = dissipation_factor_d


def _row(
    measurement_id: int,
    measured_at_ms: int,
    *,
    manufacturer: str = "TEST",
    series: str = "SYN",
    part_number: str | None = None,
    esr_ohm: float | None = None,
    capacitance_f: float | None = None,
    final_status: str | None = None,
) -> dict[str, Any]:
    return {
        "measurement": _FakeMeasurement(
            measurement_id,
            measured_at_ms,
            esr_ohm=esr_ohm,
            capacitance_f=capacitance_f,
        ),
        "manufacturer": manufacturer,
        "series": series,
        "part_number": part_number,
        "final_status": final_status,
    }


class _StubAnalysisService:
    def __init__(
        self,
        *,
        rows: list[dict[str, Any]] | None = None,
        esr_series: list[TimeSeriesPoint] | None = None,
        capacitance_series: list[TimeSeriesPoint] | None = None,
        dissipation_series: list[TimeSeriesPoint] | None = None,
        scatter: list[ScatterPoint] | None = None,
    ) -> None:
        self._rows = rows or []
        self._esr = esr_series or []
        self._c = capacitance_series or []
        self._d = dissipation_series or []
        self._scatter = scatter or []
        self.calls: list[tuple[str, dict[str, Any], str]] = []
        self.measurement_id_calls: list[list[int] | None] = []
        self.detail_calls: list[int] = []

    def load_rows(self, filters=None, *, measurement_ids=None):
        self.calls.append(("load_rows", dict(filters or {}), ""))
        self.measurement_id_calls.append(
            list(measurement_ids) if measurement_ids is not None else None
        )
        return list(self._rows)

    def esr_series(self, filters, *, aggregation, measurement_ids=None):
        self.calls.append(("esr", dict(filters or {}), aggregation))
        self.measurement_id_calls.append(
            list(measurement_ids) if measurement_ids is not None else None
        )
        return list(self._esr)

    def capacitance_series(self, filters, *, aggregation, measurement_ids=None):
        self.calls.append(("c", dict(filters or {}), aggregation))
        self.measurement_id_calls.append(
            list(measurement_ids) if measurement_ids is not None else None
        )
        return list(self._c)

    def dissipation_series(self, filters, *, aggregation, measurement_ids=None):
        self.calls.append(("d", dict(filters or {}), aggregation))
        self.measurement_id_calls.append(
            list(measurement_ids) if measurement_ids is not None else None
        )
        return list(self._d)

    def scatter_esr_vs_capacitance(self, filters, *, measurement_ids=None):
        self.calls.append(("scatter", dict(filters or {}), ""))
        self.measurement_id_calls.append(
            list(measurement_ids) if measurement_ids is not None else None
        )
        return list(self._scatter)

    def _history(self):
        outer = self

        class _History:
            def get_measurement_detail(self, measurement_id: int):
                outer.detail_calls.append(measurement_id)
                return {
                    "component_model": type("M", (), {
                        "id": 1, "manufacturer": "TEST", "series": "SYN",
                        "part_number": None,
                        "technology": "aluminium_elektrolytisch",
                        "nominal_capacitance_f": 470e-6,
                        "nominal_capacitance_value": 470.0,
                        "nominal_capacitance_unit": "µF",
                        "rated_voltage_v": 25.0, "voltage_type": "DC",
                        "tolerance_lower_pct": -20.0, "tolerance_upper_pct": 20.0,
                    })(),
                    "component_sample": type("S", (), {
                        "id": 2, "component_model_id": 1, "sample_code": None,
                        "sample_state": _EnumValue.VALUE,
                    })(),
                    "measurement_session": type("Sess", (), {
                        "id": 10, "component_sample_id": 2, "customer": None,
                        "project": None, "installation": None,
                        "module_board": None, "component_reference": None,
                    })(),
                    "measurement": _FakeMeasurement(
                        measurement_id, 1_700_000_000_000, esr_ohm=0.2
                    ),
                    "assessment_snapshots": [],
                    "reference_snapshots_by_assessment_id": {},
                }

        return _History()


@pytest.fixture
def stub_service() -> _StubAnalysisService:
    return _StubAnalysisService(
        rows=[
            _row(1, _ms(2026, 10, 1), esr_ohm=0.1, capacitance_f=470e-6,
                 final_status="waarschijnlijk_goed"),
            _row(2, _ms(2026, 10, 2), esr_ohm=0.2, capacitance_f=480e-6,
                 final_status="aandachtspunt"),
            _row(3, _ms(2026, 10, 3), esr_ohm=0.3, capacitance_f=490e-6),
        ],
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


# Basis
def test_screen_builds_with_expected_widgets(screen: AnalysisScreen) -> None:
    assert screen.back_btn.text() != ""
    assert screen.title_label.text() != ""
    assert screen.chart_type_combo.count() == 4
    assert screen.aggregation_combo.count() == 4
    assert screen.export_scope_combo.count() == 2
    assert screen.export_type_combo.count() == 3
    assert screen.selection_table.columnCount() == 5
    assert screen.report_btn.text() != ""


def test_default_chart_type_is_esr(screen: AnalysisScreen) -> None:
    assert screen.chart_type_combo.currentData() == _CHART_TYPE_ESR


def test_default_aggregation_is_raw(screen: AnalysisScreen) -> None:
    assert screen.aggregation_combo.currentData() == _AGGREGATION_RAW


def test_default_export_scope_is_selected(screen: AnalysisScreen) -> None:
    assert screen.export_scope_combo.currentData() == _EXPORT_SCOPE_SELECTED


# Service-aanroepen
def test_refresh_calls_esr_series_when_type_is_esr(
    screen: AnalysisScreen, stub_service: _StubAnalysisService
) -> None:
    stub_service.calls.clear()
    screen.refresh()
    assert any(call[0] == "esr" for call in stub_service.calls)
    assert any(call[0] == "load_rows" for call in stub_service.calls)


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


# Filters
def test_filters_are_passed_to_service(
    screen: AnalysisScreen, stub_service: _StubAnalysisService
) -> None:
    stub_service.calls.clear()
    screen.filter_manufacturer.setText("Panasonic")
    screen.filter_series.setText("FR")
    screen.refresh()
    esr_calls = [call for call in stub_service.calls if call[0] == "esr"]
    assert esr_calls
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


# Lege staat
def test_empty_series_shows_empty_state() -> None:
    _app()
    stub = _StubAnalysisService(esr_series=[])
    widget = AnalysisScreen(taal="nl_NL", analysis_service=stub)
    try:
        widget.refresh()
        assert widget.state_label.text() != ""
    finally:
        widget.deleteLater()


# Taalwissel
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
    assert any("time" in lbl.lower() or "esr" in lbl.lower() for lbl in labels)


# Signaal
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
    _app()
    widget = AnalysisScreen(taal="nl_NL", analysis_service=stub_service)
    try:
        spy = QSignalSpy(widget.back_requested)
        widget.sc_back.activated.emit()
        assert spy.count() == 1
    finally:
        widget.deleteLater()


# 11A.1 — selectielijst
def test_selectielijst_wordt_gevuld_uit_load_rows(screen: AnalysisScreen) -> None:
    screen.refresh()
    assert screen.selection_table.rowCount() == 3
    eerste_id = screen.selection_table.item(0, 0).data(Qt.ItemDataRole.UserRole)
    assert int(eerste_id) == 3


def test_selectie_telt_aantal(screen: AnalysisScreen) -> None:
    screen.refresh()
    screen.selection_table.item(0, 0).setCheckState(Qt.CheckState.Checked)
    assert "1" in screen.selection_count_label.text()


def test_selectie_wordt_gewist_bij_refresh(screen: AnalysisScreen) -> None:
    screen.refresh()
    screen.selection_table.item(0, 0).setCheckState(Qt.CheckState.Checked)
    assert screen._selected_measurement_ids() != []

    screen.refresh()

    assert screen._selected_measurement_ids() == []
    text = screen.state_label.text().lower()
    assert "gewist" in text or "cleared" in text


def test_selectie_signaal_vuurt_bij_checkbox_wijziging(
    screen: AnalysisScreen,
) -> None:
    screen.refresh()
    spy = QSignalSpy(screen.selection_changed)
    screen.selection_table.item(0, 0).setCheckState(Qt.CheckState.Checked)
    assert spy.count() >= 1


# 11A.2 — rapport-knop
def test_rapport_knop_disabled_zonder_selectie(screen: AnalysisScreen) -> None:
    screen.refresh()
    assert screen.report_btn.isEnabled() is False


def test_rapport_knop_enabled_met_selectie(screen: AnalysisScreen) -> None:
    screen.refresh()
    screen.selection_table.item(0, 0).setCheckState(Qt.CheckState.Checked)
    assert screen.report_btn.isEnabled() is True


def test_rapport_knop_zonder_selectie_toont_boodschap(
    screen: AnalysisScreen,
) -> None:
    """Zonder selectie toont de knop-handler een melding in de statusbalk."""
    screen.refresh()
    screen._open_report_for_selection()
    text = screen.state_label.text().lower()
    assert "selecteer" in text or "select" in text


# Export
def _patch_save_dialog(monkeypatch, target_path):
    monkeypatch.setattr(
        "app.gui.analysis_screen.QFileDialog.getSaveFileName",
        staticmethod(lambda *a, **kw: (str(target_path), "CSV files (*.csv)")),
    )


def _patch_both_directory(monkeypatch, target_dir):
    monkeypatch.setattr(
        "app.gui.analysis_screen.QFileDialog.getExistingDirectory",
        staticmethod(lambda *a, **kw: str(target_dir)),
    )


def test_export_zonder_selectie_toont_boodschap(
    screen: AnalysisScreen, monkeypatch
) -> None:
    screen.refresh()
    screen.export_scope_combo.setCurrentIndex(
        screen.export_scope_combo.findData(_EXPORT_SCOPE_SELECTED)
    )
    monkeypatch.setattr(
        "app.gui.analysis_screen.QFileDialog.getSaveFileName",
        staticmethod(lambda *a, **kw: ("", "")),
    )
    screen._export_selected_type()
    text = screen.state_label.text().lower()
    assert "selecteer" in text or "select" in text


def test_export_selectie_overzicht_schrijft_geselecteerde_metingen(
    screen: AnalysisScreen, monkeypatch, tmp_path
) -> None:
    screen.refresh()
    screen.export_scope_combo.setCurrentIndex(
        screen.export_scope_combo.findData(_EXPORT_SCOPE_SELECTED)
    )
    screen.export_type_combo.setCurrentIndex(
        screen.export_type_combo.findData(_EXPORT_TYPE_OVERVIEW)
    )
    for row in range(screen.selection_table.rowCount()):
        item = screen.selection_table.item(row, 0)
        if int(item.data(Qt.ItemDataRole.UserRole)) == 2:
            item.setCheckState(Qt.CheckState.Checked)
            break

    target = tmp_path / "overzicht.csv"
    _patch_save_dialog(monkeypatch, target)
    screen._export_selected_type()

    assert target.exists()
    inhoud = target.read_text(encoding="utf-8-sig")
    regels = [r for r in inhoud.splitlines() if r.strip()]
    assert len(regels) == 2


def test_export_filters_overzicht_schrijft_alle_rijen(
    screen: AnalysisScreen, monkeypatch, tmp_path
) -> None:
    screen.refresh()
    screen.export_scope_combo.setCurrentIndex(
        screen.export_scope_combo.findData(_EXPORT_SCOPE_FILTERED)
    )
    screen.export_type_combo.setCurrentIndex(
        screen.export_type_combo.findData(_EXPORT_TYPE_OVERVIEW)
    )

    target = tmp_path / "alles.csv"
    _patch_save_dialog(monkeypatch, target)
    screen._export_selected_type()

    assert target.exists()
    inhoud = target.read_text(encoding="utf-8-sig")
    regels = [r for r in inhoud.splitlines() if r.strip()]
    assert len(regels) == 4


def test_export_selectie_detail_roept_detail_op(
    screen: AnalysisScreen, stub_service: _StubAnalysisService,
    monkeypatch, tmp_path,
) -> None:
    screen.refresh()
    screen.export_scope_combo.setCurrentIndex(
        screen.export_scope_combo.findData(_EXPORT_SCOPE_SELECTED)
    )
    screen.export_type_combo.setCurrentIndex(
        screen.export_type_combo.findData(_EXPORT_TYPE_DETAIL)
    )
    for row in range(screen.selection_table.rowCount()):
        item = screen.selection_table.item(row, 0)
        if int(item.data(Qt.ItemDataRole.UserRole)) == 2:
            item.setCheckState(Qt.CheckState.Checked)
            break

    target = tmp_path / "detail.csv"
    _patch_save_dialog(monkeypatch, target)
    screen._export_selected_type()

    assert target.exists()
    assert stub_service.detail_calls == [2]


def test_export_beide_schrijft_twee_bestanden(
    screen: AnalysisScreen, monkeypatch, tmp_path
) -> None:
    screen.refresh()
    screen.export_scope_combo.setCurrentIndex(
        screen.export_scope_combo.findData(_EXPORT_SCOPE_FILTERED)
    )
    screen.export_type_combo.setCurrentIndex(
        screen.export_type_combo.findData(_EXPORT_TYPE_BOTH)
    )
    _patch_both_directory(monkeypatch, tmp_path)
    screen._export_selected_type()

    overzichten = list(tmp_path.glob("analyse_overzicht_*.csv"))
    details = list(tmp_path.glob("analyse_detail_*.csv"))
    assert len(overzichten) == 1
    assert len(details) == 1


# ============================================================================
# v1.4.0 — as-schaling en tickformaat (fase 11G.3)
# ============================================================================

def _y_axis(screen: AnalysisScreen) -> QValueAxis | None:
    for axis in screen.chart.axes():
        if isinstance(axis, QValueAxis):
            return axis
    return None


def _x_datetime_axis(screen: AnalysisScreen) -> QDateTimeAxis | None:
    for axis in screen.chart.axes():
        if isinstance(axis, QDateTimeAxis):
            return axis
    return None


def test_esr_y_as_heeft_tickformaat() -> None:
    """ESR in mΩ gebruikt %.0f (geen decimalen)."""
    _app()
    stub = _StubAnalysisService(
        esr_series=[
            TimeSeriesPoint(_ms(2026, 10, 1), 0.1, 1, "ESR_CAPACITOR"),
            TimeSeriesPoint(_ms(2026, 10, 2), 0.2, 2, "ESR_CAPACITOR"),
        ],
    )
    widget = AnalysisScreen(taal="nl_NL", analysis_service=stub)
    try:
        widget.refresh()
        axis_y = _y_axis(widget)
        assert axis_y is not None
        assert axis_y.labelFormat() == "%.0f"
        assert axis_y.tickCount() == 6
    finally:
        widget.deleteLater()


def test_capaciteit_y_as_heeft_tickformaat() -> None:
    _app()
    stub = _StubAnalysisService(
        capacitance_series=[
            TimeSeriesPoint(_ms(2026, 10, 1), 470e-6, 1, "ESR_CAPACITOR"),
            TimeSeriesPoint(_ms(2026, 10, 2), 480e-6, 2, "ESR_CAPACITOR"),
        ],
    )
    widget = AnalysisScreen(taal="nl_NL", analysis_service=stub)
    try:
        widget.chart_type_combo.setCurrentIndex(
            widget.chart_type_combo.findData(_CHART_TYPE_CAPACITANCE)
        )
        axis_y = _y_axis(widget)
        assert axis_y is not None
        assert axis_y.labelFormat() == "%.1f"
    finally:
        widget.deleteLater()


def test_dissipation_y_as_heeft_tickformaat() -> None:
    _app()
    stub = _StubAnalysisService(
        dissipation_series=[
            TimeSeriesPoint(_ms(2026, 10, 1), 0.01, 1, "ESR_CAPACITOR"),
            TimeSeriesPoint(_ms(2026, 10, 2), 0.02, 2, "ESR_CAPACITOR"),
        ],
    )
    widget = AnalysisScreen(taal="nl_NL", analysis_service=stub)
    try:
        widget.chart_type_combo.setCurrentIndex(
            widget.chart_type_combo.findData(_CHART_TYPE_DISSIPATION)
        )
        axis_y = _y_axis(widget)
        assert axis_y is not None
        assert axis_y.labelFormat() == "%.3f"
    finally:
        widget.deleteLater()


def test_y_as_range_heeft_marge() -> None:
    _app()
    stub = _StubAnalysisService(
        esr_series=[
            TimeSeriesPoint(_ms(2026, 10, 1), 0.1, 1, "ESR_CAPACITOR"),
            TimeSeriesPoint(_ms(2026, 10, 2), 0.2, 2, "ESR_CAPACITOR"),
        ],
    )
    widget = AnalysisScreen(taal="nl_NL", analysis_service=stub)
    try:
        widget.refresh()
        axis_y = _y_axis(widget)
        assert axis_y is not None
        assert axis_y.min() < 100.0
        assert axis_y.max() > 200.0
    finally:
        widget.deleteLater()


def test_datetime_as_formaat_kort_bereik() -> None:
    _app()
    stub = _StubAnalysisService(
        esr_series=[
            TimeSeriesPoint(_ms(2026, 10, 1), 0.1, 1, "ESR_CAPACITOR"),
            TimeSeriesPoint(_ms(2026, 10, 2), 0.2, 2, "ESR_CAPACITOR"),
        ],
    )
    widget = AnalysisScreen(taal="nl_NL", analysis_service=stub)
    try:
        widget.refresh()
        axis_x = _x_datetime_axis(widget)
        assert axis_x is not None
        assert axis_x.format() == "dd-MM HH:mm"
    finally:
        widget.deleteLater()


# ============================================================================
# v1.5.0 — zoom/pan (fase 11G.4)
# ============================================================================

def test_reset_zoom_knop_bestaat(screen: AnalysisScreen) -> None:
    screen.refresh()
    assert screen.reset_zoom_btn.text() != ""
    assert screen.reset_zoom_btn.isEnabled() is True


def test_reset_zoom_herstelt_oorspronkelijke_range() -> None:
    _app()
    stub = _StubAnalysisService(
        esr_series=[
            TimeSeriesPoint(_ms(2026, 10, 1), 0.1, 1, "ESR_CAPACITOR"),
            TimeSeriesPoint(_ms(2026, 10, 2), 0.2, 2, "ESR_CAPACITOR"),
        ],
    )
    widget = AnalysisScreen(taal="nl_NL", analysis_service=stub)
    try:
        widget.refresh()
        axis_y = _y_axis(widget)
        assert axis_y is not None
        origineel_min = axis_y.min()
        origineel_max = axis_y.max()

        axis_y.setRange(origineel_min + 10, origineel_max - 10)
        assert axis_y.min() > origineel_min

        widget.reset_zoom()

        assert axis_y.min() == pytest.approx(origineel_min)
        assert axis_y.max() == pytest.approx(origineel_max)
    finally:
        widget.deleteLater()


def test_ctrl_0_reset_zoom() -> None:
    _app()
    stub = _StubAnalysisService(
        esr_series=[
            TimeSeriesPoint(_ms(2026, 10, 1), 0.1, 1, "ESR_CAPACITOR"),
            TimeSeriesPoint(_ms(2026, 10, 2), 0.2, 2, "ESR_CAPACITOR"),
        ],
    )
    widget = AnalysisScreen(taal="nl_NL", analysis_service=stub)
    try:
        widget.refresh()
        axis_y = _y_axis(widget)
        assert axis_y is not None
        origineel_min = axis_y.min()
        origineel_max = axis_y.max()

        axis_y.setRange(origineel_min + 10, origineel_max - 10)
        widget.sc_reset_zoom.activated.emit()

        assert axis_y.min() == pytest.approx(origineel_min)
        assert axis_y.max() == pytest.approx(origineel_max)
    finally:
        widget.deleteLater()


def test_refresh_reset_zoom() -> None:
    _app()
    stub = _StubAnalysisService(
        esr_series=[
            TimeSeriesPoint(_ms(2026, 10, 1), 0.1, 1, "ESR_CAPACITOR"),
            TimeSeriesPoint(_ms(2026, 10, 2), 0.2, 2, "ESR_CAPACITOR"),
        ],
    )
    widget = AnalysisScreen(taal="nl_NL", analysis_service=stub)
    try:
        widget.refresh()
        axis_y = _y_axis(widget)
        assert axis_y is not None
        origineel_min = axis_y.min()
        origineel_max = axis_y.max()

        axis_y.setRange(origineel_min + 10, origineel_max - 10)
        widget.refresh()

        axis_y = _y_axis(widget)
        assert axis_y is not None
        assert axis_y.min() == pytest.approx(origineel_min)
        assert axis_y.max() == pytest.approx(origineel_max)
    finally:
        widget.deleteLater()


def test_zoom_reset_knop_i18n() -> None:
    _app()
    stub = _StubAnalysisService()

    widget_nl = AnalysisScreen(taal="nl_NL", analysis_service=stub)
    try:
        assert widget_nl.reset_zoom_btn.text() != "analyse.zoom.reset_knop"
        assert widget_nl.reset_zoom_btn.toolTip() != "analyse.zoom.reset_tooltip"
    finally:
        widget_nl.deleteLater()

    widget_en = AnalysisScreen(taal="en_US", analysis_service=stub)
    try:
        assert widget_en.reset_zoom_btn.text() != "analyse.zoom.reset_knop"
        assert widget_en.reset_zoom_btn.toolTip() != "analyse.zoom.reset_tooltip"
        assert widget_en.reset_zoom_btn.text() == "Reset zoom"
    finally:
        widget_en.deleteLater()


# ============================================================================
# v1.6.0 — selectie-gedreven grafiek en klikbare scatter-punten (11G.5)
# ============================================================================

def test_scope_selectie_beperkt_grafiek_tot_selectie() -> None:
    """Scope SELECTED + 1 aangevinkte meting -> service krijgt die ids.

    Volgt de echte GUI-flow: eerst refresh (selectie leeg), dan een
    meting aanvinken, dan refresh(preserve_selection=True) zoals de
    GUI doet bij scope-wissel of scatter-klik.
    """
    _app()
    stub = _StubAnalysisService(
        rows=[
            _row(1, _ms(2026, 10, 1), esr_ohm=0.1),
            _row(2, _ms(2026, 10, 2), esr_ohm=0.2),
            _row(3, _ms(2026, 10, 3), esr_ohm=0.3),
        ],
        esr_series=[
            TimeSeriesPoint(_ms(2026, 10, 1), 0.1, 1, "ESR_CAPACITOR"),
            TimeSeriesPoint(_ms(2026, 10, 2), 0.2, 2, "ESR_CAPACITOR"),
        ],
    )
    widget = AnalysisScreen(taal="nl_NL", analysis_service=stub)
    try:
        widget.refresh()
        # Rij 0 is de meest recente meting (id=3) vanwege de sortering.
        widget.selection_table.item(0, 0).setCheckState(Qt.CheckState.Checked)
        stub.measurement_id_calls.clear()

        widget.refresh(preserve_selection=True)

        assert any(
            ids == [3] for ids in stub.measurement_id_calls
        ), stub.measurement_id_calls
    finally:
        widget.deleteLater()


def test_scope_filters_geeft_measurement_ids_none() -> None:
    """Scope FILTERED -> service krijgt measurement_ids=None."""
    _app()
    stub = _StubAnalysisService(
        rows=[_row(1, _ms(2026, 10, 1))],
        esr_series=[TimeSeriesPoint(_ms(2026, 10, 1), 0.1, 1, "ESR_CAPACITOR")],
    )
    widget = AnalysisScreen(taal="nl_NL", analysis_service=stub)
    try:
        widget.export_scope_combo.setCurrentIndex(
            widget.export_scope_combo.findData(_EXPORT_SCOPE_FILTERED)
        )
        stub.measurement_id_calls.clear()

        widget.refresh(preserve_selection=True)

        assert all(
            ids is None for ids in stub.measurement_id_calls
        ), stub.measurement_id_calls
    finally:
        widget.deleteLater()


def test_klik_op_scatter_punt_selecteert_rij() -> None:
    """Klik op een scatter-punt -> bijbehorende rij staat aangevinkt."""
    _app()
    stub = _StubAnalysisService(
        rows=[
            _row(1, _ms(2026, 10, 1), esr_ohm=0.1, capacitance_f=470e-6),
            _row(2, _ms(2026, 10, 2), esr_ohm=0.2, capacitance_f=480e-6),
        ],
        scatter=[
            ScatterPoint(470e-6, 0.1, 1, "ESR_CAPACITOR", None),
            ScatterPoint(480e-6, 0.2, 2, "ESR_CAPACITOR", None),
        ],
    )
    widget = AnalysisScreen(taal="nl_NL", analysis_service=stub)
    try:
        # Zet eerst de scope op FILTERED zodat de klik-route niet
        # door een refresh() wordt overschreven.
        widget.export_scope_combo.setCurrentIndex(
            widget.export_scope_combo.findData(_EXPORT_SCOPE_FILTERED)
        )
        widget.chart_type_combo.setCurrentIndex(
            widget.chart_type_combo.findData(_CHART_TYPE_SCATTER)
        )
        # Expliciete refresh: garantie dat de scatter getekend is,
        # ongeacht of de signalen in de testomgeving al zijn verwerkt.
        widget.refresh()

        from PySide6.QtCharts import QScatterSeries
        reeksen = [s for s in widget.chart.series() if isinstance(s, QScatterSeries)]
        assert reeksen, "verwacht minstens één QScatterSeries"

        widget._on_scatter_clicked(reeksen[0])

        aangevinkt = widget._selected_measurement_ids()
        assert len(aangevinkt) == 1
    finally:
        widget.deleteLater()


def test_klik_op_scatter_punt_zonder_scope_selectie_hertekent_niet() -> None:
    """Scope FILTERED: een klik selecteert wel, maar hertekent niet."""
    _app()
    stub = _StubAnalysisService(
        rows=[
            _row(1, _ms(2026, 10, 1), esr_ohm=0.1, capacitance_f=470e-6),
            _row(2, _ms(2026, 10, 2), esr_ohm=0.2, capacitance_f=480e-6),
        ],
        scatter=[
            ScatterPoint(470e-6, 0.1, 1, "ESR_CAPACITOR", None),
            ScatterPoint(480e-6, 0.2, 2, "ESR_CAPACITOR", None),
        ],
    )
    widget = AnalysisScreen(taal="nl_NL", analysis_service=stub)
    try:
        widget.export_scope_combo.setCurrentIndex(
            widget.export_scope_combo.findData(_EXPORT_SCOPE_FILTERED)
        )
        widget.chart_type_combo.setCurrentIndex(
            widget.chart_type_combo.findData(_CHART_TYPE_SCATTER)
        )
        widget.refresh()

        from PySide6.QtCharts import QScatterSeries
        reeksen = [s for s in widget.chart.series() if isinstance(s, QScatterSeries)]
        assert reeksen, "verwacht minstens één QScatterSeries"
        stub.calls.clear()

        widget._on_scatter_clicked(reeksen[0])

        # Geen nieuwe service-calls (geen refresh).
        assert stub.calls == []
    finally:
        widget.deleteLater()


def test_scope_combo_i18n_nl_en() -> None:
    """De nieuwe analyse.scope.*-keys bestaan in NL en EN."""
    _app()
    stub = _StubAnalysisService()

    widget_nl = AnalysisScreen(taal="nl_NL", analysis_service=stub)
    try:
        labels_nl = [
            widget_nl.export_scope_combo.itemText(i)
            for i in range(widget_nl.export_scope_combo.count())
        ]
        assert all(lbl for lbl in labels_nl)
        assert "analyse.scope" not in " ".join(labels_nl)
    finally:
        widget_nl.deleteLater()

    widget_en = AnalysisScreen(taal="en_US", analysis_service=stub)
    try:
        labels_en = [
            widget_en.export_scope_combo.itemText(i)
            for i in range(widget_en.export_scope_combo.count())
        ]
        assert all(lbl for lbl in labels_en)
        assert any("selection" in lbl.lower() for lbl in labels_en)
    finally:
        widget_en.deleteLater()


def test_scope_wijziging_hertekent_grafiek() -> None:
    """Bij scope-wissel wordt refresh() aangeroepen (service opnieuw)."""
    _app()
    stub = _StubAnalysisService(
        rows=[_row(1, _ms(2026, 10, 1))],
        esr_series=[TimeSeriesPoint(_ms(2026, 10, 1), 0.1, 1, "ESR_CAPACITOR")],
    )
    widget = AnalysisScreen(taal="nl_NL", analysis_service=stub)
    try:
        stub.calls.clear()
        widget.export_scope_combo.setCurrentIndex(
            widget.export_scope_combo.findData(_EXPORT_SCOPE_FILTERED)
        )
        assert any(call[0] == "esr" for call in stub.calls)
    finally:
        widget.deleteLater()