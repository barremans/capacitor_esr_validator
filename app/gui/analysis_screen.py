"""
================================================================================
Module:     app/gui/analysis_screen.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.2
Datum:      2026-10-09
Auteur:     Bart Bossuyt

Doel:       Read-only Analyse-pagina binnen het hoofdvenster.

            Toont tijdreeksen (ESR, capaciteit, D) en scatter (ESR vs. C)
            op basis van opgeslagen historiek. Leest via AnalysisService,
            schrijft nooit, en wijzigt geen historische data.

            De pagina is ESR-only. Wanneer een tweede diagnosetool bestaat,
            kan de grafiektype-dropdown per tool worden uitgebreid zonder
            de pagina zelf te herstructureren.

Wijzigingen:
  v1.0.0 (2026-10-09)  Eerste versie: filters, vier grafiektypes,
                        aggregatie-dropdown, QtCharts-weergave.
  v1.0.1 (2026-10-09)  Fix: __init__ roept nu apply_language() aan, zodat
                        de knopteksten, labels en combo-items vanaf de
                        constructie correct vertaald zijn.
  v1.0.2 (2026-10-09)  Fix: apply_language() roept refresh() niet langer
                        zelf aan. De pagina is bij constructie nog niet
                        zichtbaar; de eerste refresh komt via
                        ToolHubWindow._show_analysis() of de refresh-knop.
                        Dat houdt het aantal service-aanroepen minimaal en
                        maakt de volgorde van stub-calls voorspelbaar.
================================================================================
"""

from __future__ import annotations

from datetime import datetime
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
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.helpers.analysis_series import (
    ScatterPoint,
    TimeSeriesPoint,
)
from app.helpers.history_filters import (
    build_history_filters,
    parse_local_date_end_ms,
    parse_local_date_start_ms,
)
from app.helpers.history_formatting import (
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

_UNKNOWN_STATUS_COLOR = "#9E9E9E"
_LINE_COLOR = "#4AA3FF"
_SCATTER_NEUTRAL_COLOR = "#B0B0B0"


class AnalysisScreen(QWidget):
    """Read-only analyse-pagina met QtCharts-visualisaties."""

    back_requested = Signal()

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
        self._build_ui()
        self._install_shortcuts()
        # v1.0.1/v1.0.2: labels en combo-items initialiseren in de actieve
        # taal, maar zonder refresh. De pagina is bij constructie nog niet
        # zichtbaar; de eerste refresh komt via _show_analysis() of de
        # refresh-knop. Dat houdt het aantal service-aanroepen minimaal en
        # maakt de volgorde van stub-calls voorspelbaar.
        self._apply_static_labels(self.taal)

    # ------------------------------------------------------------------
    # i18n
    # ------------------------------------------------------------------

    def _t(self, sleutel: str, **kwargs) -> str:
        return vertaal(sleutel, taal=self.taal, **kwargs)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

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
        root.addWidget(self.chart_view, 1)

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

    # ------------------------------------------------------------------
    # Combo-vulling
    # ------------------------------------------------------------------

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

    def _apply_combo_labels(self) -> None:
        """Vertaal alle combo-items in één keer, na een taalwissel."""
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

    @staticmethod
    def _frequency_label(value: float) -> str:
        return f"{value:g} Hz" if value < 1000 else f"{value / 1000:g} kHz"

    # ------------------------------------------------------------------
    # Taalwissel
    # ------------------------------------------------------------------

    def _apply_static_labels(self, taal: str) -> None:
        """Zet alle statische labels en combo-items, zonder refresh."""
        self.taal = taal
        self.back_btn.setText(self._t("knop.terug"))
        self.title_label.setText(self._t("analyse.titel"))
        self.refresh_btn.setText(self._t("knop.verversen"))
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
        self._apply_combo_labels()

    def apply_language(self, taal: str) -> None:
        """Publieke taalwissel: statische labels én een refresh.

        Wordt door ToolHubWindow aangeroepen bij een taalwissel, wanneer
        de pagina in gebruik is. Voor de initiële constructie gebruiken
        we _apply_static_labels() (geen refresh).
        """
        self._apply_static_labels(taal)
        self.refresh()

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Refresh + grafiekopbouw
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        try:
            filters = self._active_filters()
        except ValueError as exc:
            self.state_label.setText(str(exc))
            self._replace_chart_empty(self._t("analyse.geen_gegevens"))
            return

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
            return

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

    # ------------------------------------------------------------------
    # Tijdreeksen
    # ------------------------------------------------------------------

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

        # Bepaal schaal en y-label op basis van het grafiektype.
        scale, y_label = self._scale_for(chart_type)
        scaled = [(p.x_ms, p.y * scale) for p in points]

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
        axis_y.applyNiceNumbers()

        self.chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

        first_ms = scaled[0][0]
        last_ms = scaled[-1][0]
        if first_ms == last_ms:
            # Eén punt: geef een minuut marge zodat de as iets toont.
            first_ms -= 60_000
            last_ms += 60_000
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
            self._t("analyse.aantal", aantal=len(points))
        )

    def _scale_for(self, chart_type: str) -> tuple[float, str]:
        """Geef (schaalfactor, y-aslabel) voor een tijdreeks."""
        if chart_type == _CHART_TYPE_ESR:
            return 1000.0, self._t("analyse.as.esr_mohm")
        if chart_type == _CHART_TYPE_CAPACITANCE:
            return 1e6, self._t("analyse.as.capaciteit_uf")
        if chart_type == _CHART_TYPE_DISSIPATION:
            return 1.0, self._t("analyse.as.d")
        return 1.0, ""

    # ------------------------------------------------------------------
    # Scatter
    # ------------------------------------------------------------------

    def _draw_scatter(self, points: list[ScatterPoint]) -> None:
        title = self._chart_type_label(_CHART_TYPE_SCATTER)
        self._prepare_chart(title=title, show_legend=True)

        if not points:
            self._replace_chart_empty(self._t("analyse.geen_gegevens"))
            self.state_label.setText(self._t("analyse.leeg"))
            return

        # Groepeer per categorie zodat elke status een eigen kleur krijgt.
        per_categorie: dict[str | None, list[ScatterPoint]] = {}
        for point in points:
            per_categorie.setdefault(point.category, []).append(point)

        # Sorteer zodat "geen status" als laatste getekend wordt.
        ordered_categories = sorted(
            per_categorie.keys(),
            key=lambda c: (c is None, c or ""),
        )

        for category in ordered_categories:
            group = per_categorie[category]
            series = QScatterSeries()
            series.setMarkerSize(11.0)
            series.setName(
                self._category_label(category)
            )
            series.setColor(
                QColor(self._category_color(category))
            )
            series.setBorderColor(QColor("#1E1E1E"))
            for point in group:
                series.append(point.x * 1e6, point.y * 1000.0)  # µF, mΩ
            self.chart.addSeries(series)

        axis_x = QValueAxis()
        axis_x.setTitleText(self._t("analyse.as.capaciteit_uf"))
        axis_x.setLabelsColor(QColor("#F0F0F0"))
        axis_x.setTitleBrush(QColor("#F0F0F0"))
        axis_x.setGridLineColor(QColor("#3A3A3A"))
        axis_x.applyNiceNumbers()

        axis_y = QValueAxis()
        axis_y.setTitleText(self._t("analyse.as.esr_mohm"))
        axis_y.setLabelsColor(QColor("#F0F0F0"))
        axis_y.setTitleBrush(QColor("#F0F0F0"))
        axis_y.setGridLineColor(QColor("#3A3A3A"))
        axis_y.applyNiceNumbers()

        self.chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        for series in self.chart.series():
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)

        x_values = [p.x * 1e6 for p in points]
        y_values = [p.y * 1000.0 for p in points]
        axis_x.setRange(min(x_values), max(x_values))
        axis_y.setRange(min(y_values), max(y_values))

        self.state_label.setText(
            self._t("analyse.aantal", aantal=len(points))
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