"""
================================================================================
Module:     app/gui/analysis_screen.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.3.0
Datum:      2026-10-16
Auteur:     Bart Bossuyt

Doel:       Read-only Analyse-pagina binnen het hoofdvenster.

Wijzigingen:
  v1.0.0 (2026-10-09)  Eerste versie: filters, vier grafiektypes,
                        aggregatie-dropdown, QtCharts-weergave.
  v1.0.1 (2026-10-09)  Fix: __init__ roept nu apply_language() aan.
  v1.0.2 (2026-10-09)  Fix: apply_language() roept refresh() niet langer
                        zelf aan.
  v1.0.3 (2026-10-10)  Fix: NaN/Inf in meetwaarden.
  v1.0.4 (2026-10-10)  Fix: _is_finite accepteert uitsluitend int en float.
  v1.0.5 (2026-10-10)  Fix: scatter schaalt nu vóór het filteren.
  v1.0.6 (2026-10-10)  Fix: applyNiceNumbers() verwijderd.
  v1.1.0 (2026-10-16)  Fase 11A.1: compacte selectielijst, scope-DDL,
                        exportknop voor CSV.
  v1.2.0 (2026-10-16)  Fase 11A.2: knop "Rapport maken…" naast exportknop.
  v1.3.0 (2026-10-16)  Fase 11A.3: map-logica delegeert naar de nieuwe
                        pure helper app/helpers/dialog_start_directory.
================================================================================
"""

from __future__ import annotations

import math
from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtCharts import (
    QChart,
    QChartView,
    QDateTimeAxis,
    QLineSeries,
    QScatterSeries,
    QValueAxis,
)
from PySide6.QtCore import QDateTime, Qt, Signal
from PySide6.QtGui import QColor, QKeySequence, QPainter, QPen, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config.settings import laad_instellingen
from app.helpers.analysis_series import (
    ScatterPoint,
    TimeSeriesPoint,
)
from app.helpers.dialog_start_directory import (
    beste_startmap as _beste_startmap_helper,
    onthoud_startmap as _onthoud_startmap_helper,
    startpad_voor_bestand as _startpad_voor_bestand_helper,
)
from app.helpers.history_csv_export import write_history_csv
from app.helpers.history_detail_export import (
    DETAIL_EXPORT_HEADERS,
    detail_row_values,
)
from app.helpers.history_filters import (
    build_history_filters,
    parse_local_date_end_ms,
    parse_local_date_start_ms,
)
from app.helpers.history_formatting import (
    component_label,
    format_local_datetime,
    format_measurement_values,
    measurement_method_translation_key,
)
from app.helpers.i18n import vertaal
from app.gui.styles import STATUS_COLORS
from app.services.analysis_service import AnalysisService


_CHART_TYPE_ESR = "ESR"
_CHART_TYPE_CAPACITANCE = "CAPACITANCE"
_CHART_TYPE_DISSIPATION = "DISSIPATION"
_CHART_TYPE_SCATTER = "SCATTER_ESR_C"

_AGGREGATION_RAW = "raw"
_AGGREGATION_DAY = "day"
_AGGREGATION_WEEK = "week"
_AGGREGATION_MONTH = "month"

_EXPORT_TYPE_OVERVIEW = "OVERVIEW"
_EXPORT_TYPE_DETAIL = "DETAIL"
_EXPORT_TYPE_BOTH = "BOTH"

_EXPORT_SCOPE_SELECTED = "SELECTED"
_EXPORT_SCOPE_FILTERED = "FILTERED"

_UNKNOWN_STATUS_COLOR = "#9E9E9E"
_LINE_COLOR = "#4AA3FF"
_SCATTER_NEUTRAL_COLOR = "#B0B0B0"

_MIN_MS = 0
_MAX_MS = 4_102_444_800_000


def _is_finite(value: Any) -> bool:
    if value is None or isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _veilige_x_ms(value: int) -> int:
    if value < _MIN_MS:
        return _MIN_MS
    if value > _MAX_MS:
        return _MAX_MS
    return int(value)


class AnalysisScreen(QWidget):
    """Read-only analyse-pagina met QtCharts-visualisaties."""

    back_requested = Signal()
    selection_changed = Signal()

    def __init__(
        self,
        taal: str = "nl_NL",
        *,
        analysis_service: AnalysisService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.taal = taal
        self._analysis_service = analysis_service or AnalysisService()
        self._current_rows: list[dict[str, Any]] = []
        self._build_ui()
        self._install_shortcuts()
        self._apply_static_labels(self.taal)

    def _t(self, sleutel: str, **kwargs) -> str:
        return vertaal(sleutel, taal=self.taal, **kwargs)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(10)

        top = QHBoxLayout()
        self.back_btn = QPushButton()
        self.back_btn.setFixedWidth(100)
        self.back_btn.clicked.connect(self.back_requested.emit)
        top.addWidget(self.back_btn)

        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        top.addWidget(self.title_label)
        top.addStretch()

        self.chart_type_combo = QComboBox()
        self._fill_chart_type_combo()
        self.chart_type_combo.setMinimumWidth(180)
        self.chart_type_combo.currentIndexChanged.connect(self.refresh)
        top.addWidget(self.chart_type_combo)

        self.aggregation_combo = QComboBox()
        self._fill_aggregation_combo()
        self.aggregation_combo.setMinimumWidth(140)
        self.aggregation_combo.currentIndexChanged.connect(self.refresh)
        top.addWidget(self.aggregation_combo)

        self.refresh_btn = QPushButton()
        self.refresh_btn.clicked.connect(self.refresh)
        top.addWidget(self.refresh_btn)
        root.addLayout(top)

        export_row = QHBoxLayout()
        export_row.addStretch()

        self.export_scope_combo = QComboBox()
        self._fill_export_scope_combo()
        self.export_scope_combo.setMinimumWidth(190)
        self.export_scope_combo.currentIndexChanged.connect(
            lambda _i: self._update_selection_count()
        )
        export_row.addWidget(self.export_scope_combo)

        self.export_type_combo = QComboBox()
        self._fill_export_type_combo()
        self.export_type_combo.setMinimumWidth(165)
        export_row.addWidget(self.export_type_combo)

        self.selection_count_label = QLabel("")
        export_row.addWidget(self.selection_count_label)

        self.report_btn = QPushButton()
        self.report_btn.setEnabled(False)
        self.report_btn.clicked.connect(self._open_report_for_selection)
        export_row.addWidget(self.report_btn)

        self.export_btn = QPushButton()
        self.export_btn.clicked.connect(self._export_selected_type)
        export_row.addWidget(self.export_btn)
        root.addLayout(export_row)

        self.filter_group = QGroupBox()
        self.filter_group.setCheckable(True)
        self.filter_group.setChecked(False)
        filter_layout = QVBoxLayout(self.filter_group)

        self.filter_body = QWidget()
        filter_body_layout = QVBoxLayout(self.filter_body)
        filter_body_layout.setContentsMargins(0, 0, 0, 0)

        self.filter_form = QFormLayout()
        self.filter_form.setHorizontalSpacing(10)
        self.filter_form.setVerticalSpacing(6)

        self.filter_manufacturer = QLineEdit()
        self.filter_manufacturer_label = QLabel()
        self.filter_form.addRow(self.filter_manufacturer_label, self.filter_manufacturer)

        self.filter_series = QLineEdit()
        self.filter_series_label = QLabel()
        self.filter_form.addRow(self.filter_series_label, self.filter_series)

        self.filter_date_from = QLineEdit()
        self.filter_date_from_label = QLabel()
        self.filter_form.addRow(self.filter_date_from_label, self.filter_date_from)

        self.filter_date_to = QLineEdit()
        self.filter_date_to_label = QLabel()
        self.filter_form.addRow(self.filter_date_to_label, self.filter_date_to)

        self.filter_method = QComboBox()
        self._fill_method_filter()
        self.filter_method_label = QLabel()
        self.filter_form.addRow(self.filter_method_label, self.filter_method)

        self.filter_instrument = QLineEdit()
        self.filter_instrument_label = QLabel()
        self.filter_form.addRow(self.filter_instrument_label, self.filter_instrument)

        self.filter_frequency = QComboBox()
        self._fill_frequency_filter()
        self.filter_frequency_label = QLabel()
        self.filter_form.addRow(self.filter_frequency_label, self.filter_frequency)

        filter_body_layout.addLayout(self.filter_form)

        filter_buttons = QHBoxLayout()
        filter_buttons.addStretch(1)
        self.clear_filters_btn = QPushButton()
        self.clear_filters_btn.clicked.connect(self._clear_filters)
        filter_buttons.addWidget(self.clear_filters_btn)
        self.apply_filters_btn = QPushButton()
        self.apply_filters_btn.clicked.connect(self.refresh)
        filter_buttons.addWidget(self.apply_filters_btn)
        filter_body_layout.addLayout(filter_buttons)
        filter_layout.addWidget(self.filter_body)
        self.filter_body.setVisible(False)
        self.filter_group.toggled.connect(self.filter_body.setVisible)
        root.addWidget(self.filter_group)

        self.state_label = QLabel("")
        self.state_label.setWordWrap(True)
        self.state_label.setStyleSheet("color: #C8C8C8;")
        root.addWidget(self.state_label)

        self.splitter = QSplitter(Qt.Orientation.Vertical)

        self.chart = QChart()
        self.chart.setBackgroundBrush(QColor("#1E1E1E"))
        self.chart.setPlotAreaBackgroundBrush(QColor("#1E1E1E"))
        self.chart.setPlotAreaBackgroundVisible(True)
        self.chart.legend().setVisible(True)
        self.chart.legend().setLabelColor(QColor("#F0F0F0"))
        self.chart.setAnimationOptions(QChart.AnimationOption.NoAnimation)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart_view.setStyleSheet("background-color: #1E1E1E;")
        self.splitter.addWidget(self.chart_view)

        self.selection_panel = QWidget()
        selection_layout = QVBoxLayout(self.selection_panel)
        selection_layout.setContentsMargins(0, 0, 0, 0)
        selection_layout.setSpacing(6)

        self.selection_title_label = QLabel()
        self.selection_title_label.setStyleSheet("font-weight: bold;")
        selection_layout.addWidget(self.selection_title_label)

        self.selection_table = QTableWidget(0, 5)
        self.selection_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.selection_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.selection_table.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.selection_table.setAlternatingRowColors(True)
        self.selection_table.verticalHeader().setVisible(False)
        self.selection_table.setSortingEnabled(False)
        self.selection_table.itemChanged.connect(self._on_selection_item_changed)
        selection_layout.addWidget(self.selection_table, 1)

        self.splitter.addWidget(self.selection_panel)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)
        root.addWidget(self.splitter, 1)

    def _install_shortcuts(self) -> None:
        ctx = Qt.ShortcutContext.WidgetWithChildrenShortcut

        self.sc_back = QShortcut(QKeySequence("Esc"), self)
        self.sc_back.setContext(ctx)
        self.sc_back.activated.connect(self.back_requested.emit)

        self.sc_refresh = QShortcut(QKeySequence("Ctrl+R"), self)
        self.sc_refresh.setContext(ctx)
        self.sc_refresh.activated.connect(self.refresh)

        self.sc_focus_filter = QShortcut(QKeySequence("Ctrl+F"), self)
        self.sc_focus_filter.setContext(ctx)
        self.sc_focus_filter.activated.connect(self._focus_filters)

    def _focus_filters(self) -> None:
        self.filter_group.setChecked(True)
        self.filter_body.setVisible(True)
        self.filter_manufacturer.setFocus()

    def _fill_chart_type_combo(self) -> None:
        current = (
            self.chart_type_combo.currentData()
            if self.chart_type_combo.count()
            else _CHART_TYPE_ESR
        )
        self.chart_type_combo.blockSignals(True)
        try:
            self.chart_type_combo.clear()
            for data in (
                _CHART_TYPE_ESR,
                _CHART_TYPE_CAPACITANCE,
                _CHART_TYPE_DISSIPATION,
                _CHART_TYPE_SCATTER,
            ):
                self.chart_type_combo.addItem("", data)
            index = self.chart_type_combo.findData(current)
            self.chart_type_combo.setCurrentIndex(index if index >= 0 else 0)
        finally:
            self.chart_type_combo.blockSignals(False)

    def _fill_aggregation_combo(self) -> None:
        current = (
            self.aggregation_combo.currentData()
            if self.aggregation_combo.count()
            else _AGGREGATION_RAW
        )
        self.aggregation_combo.blockSignals(True)
        try:
            self.aggregation_combo.clear()
            for data in (
                _AGGREGATION_RAW,
                _AGGREGATION_DAY,
                _AGGREGATION_WEEK,
                _AGGREGATION_MONTH,
            ):
                self.aggregation_combo.addItem("", data)
            index = self.aggregation_combo.findData(current)
            self.aggregation_combo.setCurrentIndex(index if index >= 0 else 0)
        finally:
            self.aggregation_combo.blockSignals(False)

    def _fill_method_filter(self) -> None:
        current = (
            self.filter_method.currentData()
            if self.filter_method.count()
            else None
        )
        self.filter_method.blockSignals(True)
        try:
            self.filter_method.clear()
            self.filter_method.addItem("", None)
            for value in ("EX_SITU", "ONE_LEG", "IN_CIRCUIT"):
                self.filter_method.addItem("", value)
            index = self.filter_method.findData(current)
            self.filter_method.setCurrentIndex(index if index >= 0 else 0)
        finally:
            self.filter_method.blockSignals(False)

    def _fill_frequency_filter(self) -> None:
        current = (
            self.filter_frequency.currentData()
            if self.filter_frequency.count()
            else None
        )
        self.filter_frequency.blockSignals(True)
        try:
            self.filter_frequency.clear()
            self.filter_frequency.addItem("", None)
            for frequency in (100.0, 1000.0, 10000.0):
                self.filter_frequency.addItem("", frequency)
            index = self.filter_frequency.findData(current)
            self.filter_frequency.setCurrentIndex(index if index >= 0 else 0)
        finally:
            self.filter_frequency.blockSignals(False)

    def _fill_export_scope_combo(self) -> None:
        current = (
            self.export_scope_combo.currentData()
            if self.export_scope_combo.count()
            else _EXPORT_SCOPE_SELECTED
        )
        self.export_scope_combo.blockSignals(True)
        try:
            self.export_scope_combo.clear()
            self.export_scope_combo.addItem("", _EXPORT_SCOPE_SELECTED)
            self.export_scope_combo.addItem("", _EXPORT_SCOPE_FILTERED)
            index = self.export_scope_combo.findData(current)
            self.export_scope_combo.setCurrentIndex(index if index >= 0 else 0)
        finally:
            self.export_scope_combo.blockSignals(False)

    def _fill_export_type_combo(self) -> None:
        current = (
            self.export_type_combo.currentData()
            if self.export_type_combo.count()
            else _EXPORT_TYPE_OVERVIEW
        )
        self.export_type_combo.blockSignals(True)
        try:
            self.export_type_combo.clear()
            self.export_type_combo.addItem("", _EXPORT_TYPE_OVERVIEW)
            self.export_type_combo.addItem("", _EXPORT_TYPE_DETAIL)
            self.export_type_combo.addItem("", _EXPORT_TYPE_BOTH)
            index = self.export_type_combo.findData(current)
            self.export_type_combo.setCurrentIndex(index if index >= 0 else 0)
        finally:
            self.export_type_combo.blockSignals(False)

    def _apply_combo_labels(self) -> None:
        for index in range(self.chart_type_combo.count()):
            data = self.chart_type_combo.itemData(index)
            self.chart_type_combo.setItemText(index, self._chart_type_label(data))

        for index in range(self.aggregation_combo.count()):
            data = self.aggregation_combo.itemData(index)
            self.aggregation_combo.setItemText(index, self._aggregation_label(data))

        for index in range(self.filter_method.count()):
            data = self.filter_method.itemData(index)
            if data is None:
                text = self._t("historiek.filter.alle")
            else:
                text = self._t(measurement_method_translation_key(data))
            self.filter_method.setItemText(index, text)

        for index in range(self.filter_frequency.count()):
            data = self.filter_frequency.itemData(index)
            if data is None:
                text = self._t("historiek.filter.alle")
            else:
                text = self._frequency_label(float(data))
            self.filter_frequency.setItemText(index, text)

        for index in range(self.export_scope_combo.count()):
            data = self.export_scope_combo.itemData(index)
            self.export_scope_combo.setItemText(
                index, self._export_scope_label(data)
            )

        for index in range(self.export_type_combo.count()):
            data = self.export_type_combo.itemData(index)
            self.export_type_combo.setItemText(
                index, self._export_type_label(data)
            )

    def _chart_type_label(self, data: str) -> str:
        mapping = {
            _CHART_TYPE_ESR: "analyse.grafiektype.esr",
            _CHART_TYPE_CAPACITANCE: "analyse.grafiektype.capaciteit",
            _CHART_TYPE_DISSIPATION: "analyse.grafiektype.d",
            _CHART_TYPE_SCATTER: "analyse.grafiektype.scatter_esr_c",
        }
        return self._t(mapping.get(data, data))

    def _aggregation_label(self, data: str) -> str:
        mapping = {
            _AGGREGATION_RAW: "analyse.aggregatie.ruw",
            _AGGREGATION_DAY: "analyse.aggregatie.dag",
            _AGGREGATION_WEEK: "analyse.aggregatie.week",
            _AGGREGATION_MONTH: "analyse.aggregatie.maand",
        }
        return self._t(mapping.get(data, data))

    def _export_scope_label(self, data: str) -> str:
        mapping = {
            _EXPORT_SCOPE_SELECTED: "analyse.export.scope_selectie",
            _EXPORT_SCOPE_FILTERED: "analyse.export.scope_filters",
        }
        return self._t(mapping.get(data, data))

    def _export_type_label(self, data: str) -> str:
        mapping = {
            _EXPORT_TYPE_OVERVIEW: "analyse.export.type_overzicht",
            _EXPORT_TYPE_DETAIL: "analyse.export.type_detail",
            _EXPORT_TYPE_BOTH: "analyse.export.type_beide",
        }
        return self._t(mapping.get(data, data))

    @staticmethod
    def _frequency_label(value: float) -> str:
        return f"{value:g} Hz" if value < 1000 else f"{value / 1000:g} kHz"

    def _apply_static_labels(self, taal: str) -> None:
        self.taal = taal
        self.back_btn.setText(self._t("knop.terug"))
        self.title_label.setText(self._t("analyse.titel"))
        self.refresh_btn.setText(self._t("knop.verversen"))
        self.export_btn.setText(self._t("analyse.export.knop"))
        self.report_btn.setText(self._t("analyse.rapport.knop"))
        self.filter_group.setTitle(self._t("historiek.filter.titel"))
        self.filter_manufacturer_label.setText(self._t("historiek.filter.fabrikant"))
        self.filter_series_label.setText(self._t("historiek.filter.serie"))
        self.filter_date_from_label.setText(self._t("historiek.filter.datum_van"))
        self.filter_date_to_label.setText(self._t("historiek.filter.datum_tot"))
        self.filter_method_label.setText(self._t("historiek.filter.meetmethode"))
        self.filter_instrument_label.setText(self._t("historiek.filter.instrument"))
        self.filter_frequency_label.setText(self._t("historiek.filter.frequentie"))
        self.filter_manufacturer.setPlaceholderText(
            self._t("historiek.filter.exact_placeholder")
        )
        self.filter_series.setPlaceholderText(
            self._t("historiek.filter.exact_placeholder")
        )
        self.filter_date_from.setPlaceholderText(
            self._t("historiek.filter.datum_placeholder")
        )
        self.filter_date_to.setPlaceholderText(
            self._t("historiek.filter.datum_placeholder")
        )
        self.filter_instrument.setPlaceholderText(
            self._t("historiek.filter.exact_placeholder")
        )
        self.clear_filters_btn.setText(self._t("historiek.filter.wissen"))
        self.apply_filters_btn.setText(self._t("historiek.filter.toepassen"))
        self.selection_title_label.setText(self._t("analyse.selectie.titel"))
        self._apply_selection_headers()
        self._apply_combo_labels()
        self._update_selection_count()

    def _apply_selection_headers(self) -> None:
        self.selection_table.setHorizontalHeaderLabels(
            [
                "",
                self._t("analyse.selectie.kolom.datum"),
                self._t("analyse.selectie.kolom.component"),
                self._t("analyse.selectie.kolom.meetwaarden"),
                self._t("analyse.selectie.kolom.status"),
            ]
        )
        header = self.selection_table.horizontalHeader()
        for column in range(self.selection_table.columnCount()):
            header.setStretchLastSection(False)
            self.selection_table.resizeColumnToContents(column)
        self.selection_table.setColumnWidth(
            0, max(36, self.selection_table.columnWidth(0))
        )
        header.setStretchLastSection(True)

    def apply_language(self, taal: str) -> None:
        self._apply_static_labels(taal)

    def _clear_filters(self) -> None:
        self.filter_manufacturer.clear()
        self.filter_series.clear()
        self.filter_date_from.clear()
        self.filter_date_to.clear()
        self.filter_method.setCurrentIndex(0)
        self.filter_instrument.clear()
        self.filter_frequency.setCurrentIndex(0)
        self.refresh()

    def _active_filters(self) -> dict[str, Any]:
        try:
            measured_from_ms = parse_local_date_start_ms(self.filter_date_from.text())
            measured_to_ms = parse_local_date_end_ms(self.filter_date_to.text())
        except ValueError as exc:
            raise ValueError(
                self._t("historiek.filter.datum_formaat_fout")
            ) from exc

        if (
            measured_from_ms is not None
            and measured_to_ms is not None
            and measured_from_ms > measured_to_ms
        ):
            raise ValueError(self._t("historiek.filter.datum_volgorde_fout"))

        return build_history_filters(
            tool_key="ESR_CAPACITOR",
            manufacturer=self.filter_manufacturer.text(),
            series=self.filter_series.text(),
            measurement_method=self.filter_method.currentData(),
            instrument_key=self.filter_instrument.text(),
            frequency_hz=self.filter_frequency.currentData(),
            measured_from_ms=measured_from_ms,
            measured_to_ms=measured_to_ms,
        )

    def _populate_selection_table(self, rows: list[dict[str, Any]]) -> None:
        rows_sorted = sorted(
            rows,
            key=lambda r: (
                -int(getattr(r["measurement"], "measured_at_ms", 0) or 0),
                int(getattr(r["measurement"], "id", 0) or 0),
            ),
        )

        self.selection_table.blockSignals(True)
        try:
            self.selection_table.setRowCount(len(rows_sorted))
            for row_index, row in enumerate(rows_sorted):
                measurement = row["measurement"]

                select_item = QTableWidgetItem("")
                select_item.setFlags(
                    Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable
                    | Qt.ItemFlag.ItemIsUserCheckable
                )
                select_item.setCheckState(Qt.CheckState.Unchecked)
                select_item.setData(Qt.ItemDataRole.UserRole, measurement.id)
                select_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.selection_table.setItem(row_index, 0, select_item)

                measured_at_ms = getattr(measurement, "measured_at_ms", None)
                values = [
                    format_local_datetime(measured_at_ms),
                    component_label(row),
                    format_measurement_values(measurement.tool_key, measurement),
                    (
                        self._t(f"status.eindstatus.{row['final_status']}")
                        if row.get("final_status")
                        else "—"
                    ),
                ]
                for offset, value in enumerate(values, start=1):
                    item = QTableWidgetItem(str(value))
                    item.setData(Qt.ItemDataRole.UserRole, measurement.id)
                    self.selection_table.setItem(row_index, offset, item)
        finally:
            self.selection_table.blockSignals(False)

        self._apply_selection_headers()
        self._update_selection_count()

    def _on_selection_item_changed(self, item: QTableWidgetItem) -> None:
        if item.column() == 0:
            self._update_selection_count()
            self.selection_changed.emit()

    def _selected_measurement_ids(self) -> list[int]:
        ids: list[int] = []
        for row in range(self.selection_table.rowCount()):
            item = self.selection_table.item(row, 0)
            if item is None or item.checkState() != Qt.CheckState.Checked:
                continue
            value = item.data(Qt.ItemDataRole.UserRole)
            if value is not None:
                ids.append(int(value))
        return ids

    def _clear_selection(self) -> bool:
        gewist = False
        self.selection_table.blockSignals(True)
        try:
            for row in range(self.selection_table.rowCount()):
                item = self.selection_table.item(row, 0)
                if item is None:
                    continue
                if item.checkState() == Qt.CheckState.Checked:
                    item.setCheckState(Qt.CheckState.Unchecked)
                    gewist = True
        finally:
            self.selection_table.blockSignals(False)
        return gewist

    def _update_selection_count(self) -> None:
        aantal = len(self._selected_measurement_ids())
        self.selection_count_label.setText(
            self._t("analyse.selectie.geselecteerd_aantal", aantal=aantal)
        )
        self.report_btn.setEnabled(aantal > 0)
        self.selection_changed.emit()

    def refresh(self) -> None:
        had_selectie = self._clear_selection()
        try:
            filters = self._active_filters()
        except ValueError as exc:
            self.state_label.setText(str(exc))
            self._replace_chart_empty(self._t("analyse.geen_gegevens"))
            self.selection_table.setRowCount(0)
            self._current_rows = []
            return

        try:
            rows = self._analysis_service.load_rows(filters)
        except Exception as exc:
            self.state_label.setText(self._t("analyse.fout", bericht=str(exc)))
            self._replace_chart_empty(self._t("analyse.geen_gegevens"))
            self.selection_table.setRowCount(0)
            self._current_rows = []
            return

        self._current_rows = list(rows)

        chart_type = self.chart_type_combo.currentData()
        aggregation = self.aggregation_combo.currentData()

        try:
            if chart_type == _CHART_TYPE_SCATTER:
                points = self._analysis_service.scatter_esr_vs_capacitance(filters)
                self._draw_scatter(points)
            else:
                series = self._analysis_service_for(chart_type, aggregation, filters)
                self._draw_time_series(series, chart_type)
        except Exception as exc:
            self.state_label.setText(self._t("analyse.fout", bericht=str(exc)))
            self._replace_chart_empty(self._t("analyse.geen_gegevens"))

        self._populate_selection_table(self._current_rows)
        if had_selectie:
            self.state_label.setText(
                self._t("analyse.selectie.gewijzigd_bij_verversen")
            )

    def _analysis_service_for(
        self,
        chart_type: str,
        aggregation: str,
        filters: dict[str, Any],
    ) -> list[TimeSeriesPoint]:
        if chart_type == _CHART_TYPE_ESR:
            return self._analysis_service.esr_series(filters, aggregation=aggregation)
        if chart_type == _CHART_TYPE_CAPACITANCE:
            return self._analysis_service.capacitance_series(
                filters, aggregation=aggregation
            )
        if chart_type == _CHART_TYPE_DISSIPATION:
            return self._analysis_service.dissipation_series(
                filters, aggregation=aggregation
            )
        return []

    def _replace_chart_empty(self, message: str) -> None:
        self.chart.removeAllSeries()
        for axis in list(self.chart.axes()):
            self.chart.removeAxis(axis)
        self.chart.setTitle(message)
        self.chart.legend().setVisible(False)

    def _prepare_chart(self, *, title: str, show_legend: bool) -> None:
        self.chart.removeAllSeries()
        for axis in list(self.chart.axes()):
            self.chart.removeAxis(axis)
        self.chart.setTitle(title)
        self.chart.legend().setVisible(show_legend)

    @staticmethod
    def _finite_filter(
        punten: list[tuple[int, float]],
    ) -> list[tuple[int, float]]:
        resultaat: list[tuple[int, float]] = []
        for x_ms, y in punten:
            if not _is_finite(y):
                continue
            if not _is_finite(x_ms):
                continue
            resultaat.append((int(x_ms), float(y)))
        return resultaat

    def _draw_time_series(
        self,
        points: list[TimeSeriesPoint],
        chart_type: str,
    ) -> None:
        title = self._chart_type_label(chart_type)
        self._prepare_chart(title=title, show_legend=False)

        if not points:
            self._replace_chart_empty(self._t("analyse.geen_gegevens"))
            self.state_label.setText(self._t("analyse.leeg"))
            return

        scale, y_label = self._scale_for(chart_type)
        ruwe_punten = [(p.x_ms, p.y * scale) for p in points]
        scaled = self._finite_filter(ruwe_punten)

        if not scaled:
            self._replace_chart_empty(self._t("analyse.geen_gegevens"))
            self.state_label.setText(self._t("analyse.leeg"))
            return

        series = QLineSeries()
        series.setName(y_label)
        pen = QPen(QColor(_LINE_COLOR))
        pen.setWidth(2)
        series.setPen(pen)

        for x_ms, y in scaled:
            series.append(float(x_ms), float(y))
        self.chart.addSeries(series)

        axis_x = QDateTimeAxis()
        axis_x.setFormat("dd-MM-yyyy")
        axis_x.setTitleText(self._t("analyse.as.datum"))
        axis_x.setTickCount(min(6, max(2, len(scaled))))
        axis_x.setLabelsColor(QColor("#F0F0F0"))
        axis_x.setTitleBrush(QColor("#F0F0F0"))
        axis_x.setGridLineColor(QColor("#3A3A3A"))

        axis_y = QValueAxis()
        axis_y.setTitleText(y_label)
        axis_y.setLabelsColor(QColor("#F0F0F0"))
        axis_y.setTitleBrush(QColor("#F0F0F0"))
        axis_y.setGridLineColor(QColor("#3A3A3A"))

        self.chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

        first_ms = _veilige_x_ms(scaled[0][0])
        last_ms = _veilige_x_ms(scaled[-1][0])
        if first_ms == last_ms:
            first_ms = _veilige_x_ms(first_ms - 60_000)
            last_ms = _veilige_x_ms(last_ms + 60_000)
        if first_ms >= last_ms:
            last_ms = first_ms + 60_000
        axis_x.setRange(
            QDateTime.fromMSecsSinceEpoch(first_ms),
            QDateTime.fromMSecsSinceEpoch(last_ms),
        )

        y_values = [y for _, y in scaled]
        y_min = min(y_values)
        y_max = max(y_values)
        if y_min == y_max:
            margin = abs(y_min) * 0.1 or 1.0
            y_min -= margin
            y_max += margin
        axis_y.setRange(y_min, y_max)

        self.state_label.setText(
            self._t("analyse.aantal", aantal=len(scaled))
        )

    def _scale_for(self, chart_type: str) -> tuple[float, str]:
        if chart_type == _CHART_TYPE_ESR:
            return 1000.0, self._t("analyse.as.esr_mohm")
        if chart_type == _CHART_TYPE_CAPACITANCE:
            return 1e6, self._t("analyse.as.capaciteit_uf")
        if chart_type == _CHART_TYPE_DISSIPATION:
            return 1.0, self._t("analyse.as.d")
        return 1.0, ""

    def _draw_scatter(self, points: list[ScatterPoint]) -> None:
        title = self._chart_type_label(_CHART_TYPE_SCATTER)
        self._prepare_chart(title=title, show_legend=True)

        if not points:
            self._replace_chart_empty(self._t("analyse.geen_gegevens"))
            self.state_label.setText(self._t("analyse.leeg"))
            return

        geschaald: list[tuple[ScatterPoint, float, float]] = []
        for p in points:
            if not _is_finite(p.x) or not _is_finite(p.y):
                continue
            x_scaled = p.x * 1e6
            y_scaled = p.y * 1000.0
            if not _is_finite(x_scaled) or not _is_finite(y_scaled):
                continue
            geschaald.append((p, x_scaled, y_scaled))

        if not geschaald:
            self._replace_chart_empty(self._t("analyse.geen_gegevens"))
            self.state_label.setText(self._t("analyse.leeg"))
            return

        geldige_punten = [p for p, _, _ in geschaald]
        x_geschaald = [x for _, x, _ in geschaald]
        y_geschaald = [y for _, _, y in geschaald]

        per_categorie: dict[str | None, list[ScatterPoint]] = {}
        for point in geldige_punten:
            per_categorie.setdefault(point.category, []).append(point)

        ordered_categories = sorted(
            per_categorie.keys(),
            key=lambda c: (c is None, c or ""),
        )

        for category in ordered_categories:
            group = per_categorie[category]
            series = QScatterSeries()
            series.setMarkerSize(11.0)
            series.setName(self._category_label(category))
            series.setColor(QColor(self._category_color(category)))
            series.setBorderColor(QColor("#1E1E1E"))
            for point in group:
                series.append(point.x * 1e6, point.y * 1000.0)
            self.chart.addSeries(series)

        axis_x = QValueAxis()
        axis_x.setTitleText(self._t("analyse.as.capaciteit_uf"))
        axis_x.setLabelsColor(QColor("#F0F0F0"))
        axis_x.setTitleBrush(QColor("#F0F0F0"))
        axis_x.setGridLineColor(QColor("#3A3A3A"))

        axis_y = QValueAxis()
        axis_y.setTitleText(self._t("analyse.as.esr_mohm"))
        axis_y.setLabelsColor(QColor("#F0F0F0"))
        axis_y.setTitleBrush(QColor("#F0F0F0"))
        axis_y.setGridLineColor(QColor("#3A3A3A"))

        self.chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        for series in self.chart.series():
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)

        axis_x.setRange(min(x_geschaald), max(x_geschaald))
        axis_y.setRange(min(y_geschaald), max(y_geschaald))

        self.state_label.setText(
            self._t("analyse.aantal", aantal=len(geldige_punten))
        )

    def _category_label(self, category: str | None) -> str:
        if not category:
            return self._t("analyse.status_onbekend")
        sleutel = f"status.eindstatus.{category}"
        vertaald = self._t(sleutel)
        if vertaald == sleutel:
            return category
        return vertaald

    @staticmethod
    def _category_color(category: str | None) -> str:
        if category is None:
            return _SCATTER_NEUTRAL_COLOR
        return STATUS_COLORS.get(category, _UNKNOWN_STATUS_COLOR)

    # ------------------------------------------------------------------
    # Rapport
    # ------------------------------------------------------------------

    def _open_report_for_selection(self) -> None:
        selected_ids = self._selected_measurement_ids()
        if not selected_ids:
            self.state_label.setText(self._t("analyse.rapport.geen_selectie"))
            return

        from app.gui.dialogs.report_dialog import ReportDialog

        werkplaats = ""
        auteur = ""
        try:
            instellingen = laad_instellingen()
            werkplaats = instellingen.rapportage.werkplaats_bedrijf
            auteur = instellingen.rapportage.auteur
        except (OSError, ValueError):
            pass

        dialog = ReportDialog.for_measurements(
            selected_ids,
            scope=self._t("report.scope.selectie"),
            taal=self.taal,
            werkplaats=werkplaats,
            auteur=auteur,
            grafiek_default=False,
            parent=self,
        )
        dialog.exec()

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _export_selected_type(self) -> None:
        export_type = self.export_type_combo.currentData()
        if export_type == _EXPORT_TYPE_DETAIL:
            self._export_detail_csv()
        elif export_type == _EXPORT_TYPE_BOTH:
            self._export_both_csv()
        else:
            self._export_overview_csv()

    def _rows_for_export(self) -> list[dict[str, Any]] | None:
        scope = self.export_scope_combo.currentData()
        if scope == _EXPORT_SCOPE_SELECTED:
            selected_ids = set(self._selected_measurement_ids())
            if not selected_ids:
                self.state_label.setText(
                    self._t("analyse.selectie.geen_selectie")
                )
                return None
            return [
                row
                for row in self._current_rows
                if int(row["measurement"].id) in selected_ids
            ]
        return list(self._current_rows)

    def _overview_headers(self) -> list[str]:
        return [
            self._t("historiek.kolom.datum_tijd"),
            self._t("historiek.kolom.component"),
            self._t("historiek.kolom.meetwaarden"),
            self._t("historiek.kolom.status"),
        ]

    def _overview_row_values(self, row: dict[str, Any]) -> list[str]:
        measurement = row["measurement"]
        return [
            format_local_datetime(measurement.measured_at_ms),
            component_label(row),
            format_measurement_values(measurement.tool_key, measurement),
            (
                self._t(f"status.eindstatus.{row['final_status']}")
                if row.get("final_status")
                else "—"
            ),
        ]

    def _export_timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def _default_export_filename(
        self,
        export_type: str,
        *,
        timestamp: str | None = None,
    ) -> str:
        stamp = timestamp or self._export_timestamp()
        if export_type == _EXPORT_TYPE_DETAIL:
            return self._t(
                "analyse.export.bestandsnaam_detail", timestamp=stamp
            )
        return self._t(
            "analyse.export.bestandsnaam_overzicht", timestamp=stamp
        )

    def _beste_export_start_directory(self) -> Path | None:
        """Beste startmap via de centrale helper (categorie 'export')."""
        return _beste_startmap_helper("export")

    def _onthoud_laatste_exportmap(self, doel_pad: Path) -> None:
        """Onthoud de map via de centrale helper (categorie 'export')."""
        _onthoud_startmap_helper("export", doel_pad)

    def _export_start_path(self, default_filename: str) -> str:
        return _startpad_voor_bestand_helper("export", default_filename)

    def _choose_export_path(
        self,
        *,
        default_filename: str,
        dialog_title_key: str,
    ) -> str | None:
        file_path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            self._t(dialog_title_key),
            self._export_start_path(default_filename),
            self._t("analyse.export.bestandsfilter"),
        )
        if not file_path:
            return None
        if not file_path.lower().endswith(".csv"):
            file_path += ".csv"
        return file_path

    def _choose_export_both_directory(self) -> str | None:
        start_directory = self._beste_export_start_directory()
        chosen = QFileDialog.getExistingDirectory(
            self,
            self._t("analyse.export.beide_dialoog_titel"),
            str(start_directory) if start_directory is not None else "",
        )
        return chosen or None

    def _export_overview_csv(self) -> None:
        try:
            rows = self._rows_for_export()
        except Exception as exc:
            self.state_label.setText(
                self._t("analyse.export.fout", bericht=str(exc))
            )
            return
        if rows is None:
            return
        if not rows:
            self.state_label.setText(self._t("analyse.export.leeg"))
            return

        default_filename = self._default_export_filename(_EXPORT_TYPE_OVERVIEW)
        file_path = self._choose_export_path(
            default_filename=default_filename,
            dialog_title_key="analyse.export.dialoog_titel",
        )
        if file_path is None:
            return

        try:
            write_history_csv(
                file_path,
                self._overview_headers(),
                (self._overview_row_values(row) for row in rows),
            )
        except Exception as exc:
            self.state_label.setText(
                self._t("analyse.export.fout", bericht=str(exc))
            )
            return

        self.state_label.setText(
            self._t(
                "analyse.export.geslaagd",
                aantal=len(rows),
                pad=file_path,
            )
        )
        self._onthoud_laatste_exportmap(Path(file_path))

    def _export_detail_csv(self) -> None:
        try:
            rows = self._rows_for_export()
        except Exception as exc:
            self.state_label.setText(
                self._t("analyse.export.fout", bericht=str(exc))
            )
            return
        if rows is None:
            return
        if not rows:
            self.state_label.setText(self._t("analyse.export.leeg"))
            return

        details: list[dict[str, Any]] = []
        try:
            for row in rows:
                measurement_id = int(row["measurement"].id)
                detail = self._analysis_service._history().get_measurement_detail(
                    measurement_id
                )
                if detail is None:
                    raise ValueError(
                        f"Geen detaildata voor measurement_id={measurement_id}."
                    )
                details.append(detail)
        except Exception as exc:
            self.state_label.setText(
                self._t("analyse.export.fout", bericht=str(exc))
            )
            return

        default_filename = self._default_export_filename(_EXPORT_TYPE_DETAIL)
        file_path = self._choose_export_path(
            default_filename=default_filename,
            dialog_title_key="analyse.export.detail_dialoog_titel",
        )
        if file_path is None:
            return

        try:
            write_history_csv(
                file_path,
                DETAIL_EXPORT_HEADERS,
                (detail_row_values(detail) for detail in details),
            )
        except Exception as exc:
            self.state_label.setText(
                self._t("analyse.export.fout", bericht=str(exc))
            )
            return

        self.state_label.setText(
            self._t(
                "analyse.export.geslaagd",
                aantal=len(details),
                pad=file_path,
            )
        )
        self._onthoud_laatste_exportmap(Path(file_path))

    def _export_both_csv(self) -> None:
        try:
            rows = self._rows_for_export()
        except Exception as exc:
            self.state_label.setText(
                self._t("analyse.export.fout", bericht=str(exc))
            )
            return
        if rows is None:
            return
        if not rows:
            self.state_label.setText(self._t("analyse.export.leeg"))
            return

        details: list[dict[str, Any]] = []
        try:
            for row in rows:
                measurement_id = int(row["measurement"].id)
                detail = self._analysis_service._history().get_measurement_detail(
                    measurement_id
                )
                if detail is None:
                    raise ValueError(
                        f"Geen detaildata voor measurement_id={measurement_id}."
                    )
                details.append(detail)
        except Exception as exc:
            self.state_label.setText(
                self._t("analyse.export.fout", bericht=str(exc))
            )
            return

        directory = self._choose_export_both_directory()
        if directory is None:
            return

        timestamp = self._export_timestamp()
        overview_path = str(
            Path(directory)
            / self._default_export_filename(
                _EXPORT_TYPE_OVERVIEW, timestamp=timestamp
            )
        )
        detail_path = str(
            Path(directory)
            / self._default_export_filename(
                _EXPORT_TYPE_DETAIL, timestamp=timestamp
            )
        )

        try:
            write_history_csv(
                overview_path,
                self._overview_headers(),
                (self._overview_row_values(row) for row in rows),
            )
            write_history_csv(
                detail_path,
                DETAIL_EXPORT_HEADERS,
                (detail_row_values(detail) for detail in details),
            )
        except Exception as exc:
            self.state_label.setText(
                self._t("analyse.export.fout", bericht=str(exc))
            )
            return

        self.state_label.setText(
            self._t(
                "analyse.export.geslaagd",
                aantal=len(rows),
                pad=directory,
            )
        )
        self._onthoud_laatste_exportmap(Path(directory))