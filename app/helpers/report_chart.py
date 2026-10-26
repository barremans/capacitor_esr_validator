"""
================================================================================
Module:     app/helpers/report_chart.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.2.0
Datum:      2026-10-26
Auteur:     Bart Bossuyt

Doel:       Qt-specifieke grafiek-helper voor meetrapporten.

            Bouwt een QChart met ESR-over-tijd en/of scatter (ESR vs. C)
            op basis van de bestaande AnalysisService, en levert een
            base64-PNG-string die de pure renderer als <img> kan inbedden.

            Alleen voor ESR_CAPACITOR. Voor andere tool_keys geeft de helper
            None terug, zodat de renderer geen grafieksectie toont.

            Dezelfde NaN/Inf-verdediging als app/gui/analysis_screen.py:
            niet-eindige waarden worden uit de reeks gefilterd vóór de
            as-range wordt gezet. In de scatter-variant schalen we eerst
            en filteren we daarna, omdat een eindige p.x of p.y door de
            vermenigvuldiging met 1e6 resp. 1000.0 alsnog ±Inf kan worden.
            applyNiceNumbers() wordt niet gebruikt: het riep intern
            setRange() aan op basis van een nog niet geattache reeks en
            gaf dan "Attempting to set invalid range for value axis".

            Sinds v1.1.0 gebruiken beide render-functies dezelfde pure
            Y-as-clamping-helper als AnalysisScreen (app/helpers/
            chart_axis.py), zodat de rapportgrafiek en de GUI-grafiek
            nooit uit elkaar lopen.

Wijzigingen:
  v1.0.0 (2026-10-10)  Eerste versie: render_esr_over_tijd_png_base64(),
                        render_scatter_png_base64(), render_chart_voor_detail().
  v1.0.1 (2026-10-10)  Fix: _is_finite accepteert nu uitsluitend int en
                        float, consistent met analysis_screen.py. Strings
                        worden geweigerd zodat een onverwachte string uit
                        de storage zichtbaar wordt in plaats van stil te
                        worden geaccepteerd.
  v1.0.2 (2026-10-10)  Fix: scatter schaalt nu vóór het filteren. Een
                        eindige p.x of p.y kon door de vermenigvuldiging
                        met 1e6 resp. 1000.0 alsnog ±Inf worden, waarna
                        QValueAxis.setRange een Qt-waarschuwing gaf.
  v1.0.3 (2026-10-10)  Fix: applyNiceNumbers() verwijderd. Bovendien klemt
                        render_esr_over_tijd_png_base64 de x-as op
                        [1970-01-01, 2100-01-01] zodat een absurde x_ms
                        QDateTime niet laat overlopen.
  v1.1.0 (2026-10-26)  Fase 5A: dezelfde slimme Y-as-clamping als
                        AnalysisScreen via de nieuwe pure helper
                        app/helpers/chart_axis.py. render_esr_over_tijd_
                        png_base64 en render_scatter_png_base64 gebruiken
                        bereken_y_as_range(). Voorkomt drift tussen de
                        GUI-grafiek en de rapportgrafiek.
  v1.2.0 (2026-10-26)  Fase 5B: leesbare X-as-labels in
                        render_scatter_png_base64 via de nieuwe pure
                        helper bereken_x_as_ticks(). Voorkomt dat Qt bij
                        een log-verdeeld bereik (bv. 0,1 µF tot 1.160 µF)
                        de labels afkapt tot "...".
================================================================================
"""

from __future__ import annotations

import base64
import math
from typing import Any

from PySide6.QtCharts import (
    QChart,
    QChartView,
    QDateTimeAxis,
    QLineSeries,
    QScatterSeries,
    QValueAxis,
)
from PySide6.QtCore import QBuffer, QByteArray, QDateTime, QIODevice, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QApplication

from app.gui.styles import STATUS_COLORS
from app.helpers.analysis_series import (
    ScatterPoint,
    TimeSeriesPoint,
)
from app.helpers.chart_axis import bereken_x_as_ticks, bereken_y_as_range
from app.helpers.history_filters import build_history_filters
from app.services.analysis_service import AnalysisService


_LINE_COLOR = "#4AA3FF"
_UNKNOWN_STATUS_COLOR = "#9E9E9E"
_SCATTER_NEUTRAL_COLOR = "#B0B0B0"

_MIN_MS = 0
_MAX_MS = 4_102_444_800_000


def _is_finite(value: Any) -> bool:
    """True als value een eindig getal is (geen NaN, geen ±Inf).

    Accepteert uitsluitend int en float (geen bool, geen string).
    """
    if value is None or isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _veilige_x_ms(value: int) -> int:
    """Klem een epoch-ms waarde op het veilige bereik voor QDateTime."""
    if value < _MIN_MS:
        return _MIN_MS
    if value > _MAX_MS:
        return _MAX_MS
    return int(value)


def _zorg_voor_qapplication() -> None:
    """Zorg dat er een QApplication bestaat vóór we widgets maken."""
    if QApplication.instance() is None:
        QApplication([])


def _chart_naar_base64_png(chart: QChart, *, breedte: int = 900, hoogte: int = 500) -> str:
    """Render een QChart naar een base64-PNG-string."""
    _zorg_voor_qapplication()

    view = QChartView(chart)
    view.setRenderHint(QPainter.RenderHint.Antialiasing)
    view.resize(breedte, hoogte)

    afbeelding = view.grab().toImage()

    byte_array = QByteArray()
    buffer = QBuffer(byte_array)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    afbeelding.save(buffer, "PNG")
    buffer.close()

    return base64.b64encode(bytes(byte_array)).decode("ascii")


def _stijl_chart(chart: QChart) -> None:
    chart.setBackgroundBrush(QColor("#1E1E1E"))
    chart.setPlotAreaBackgroundBrush(QColor("#1E1E1E"))
    chart.setPlotAreaBackgroundVisible(True)
    chart.legend().setVisible(False)
    chart.legend().setLabelColor(QColor("#F0F0F0"))
    chart.setAnimationOptions(QChart.AnimationOption.NoAnimation)


def render_esr_over_tijd_png_base64(
    analysis_service: AnalysisService,
    *,
    filters: dict[str, Any] | None = None,
    aggregation: str = "raw",
) -> str | None:
    """ESR-over-tijd als base64-PNG. None als er geen geldige punten zijn."""
    punten: list[TimeSeriesPoint] = analysis_service.esr_series(
        filters or {}, aggregation=aggregation  # type: ignore[arg-type]
    )
    ruwe = [(p.x_ms, p.y * 1000.0) for p in punten if _is_finite(p.y) and _is_finite(p.x_ms)]
    # v1.0.2: ook na schaling controleren, want p.y * 1000.0 kan ±Inf worden.
    ruwe = [(x, y) for x, y in ruwe if _is_finite(y) and _is_finite(x)]
    if len(ruwe) < 2:
        return None

    chart = QChart()
    _stijl_chart(chart)
    chart.setTitle("ESR over tijd (mΩ)")

    series = QLineSeries()
    pen = QPen(QColor(_LINE_COLOR))
    pen.setWidth(2)
    series.setPen(pen)
    for x_ms, y in ruwe:
        series.append(float(x_ms), float(y))
    chart.addSeries(series)

    axis_x = QDateTimeAxis()
    axis_x.setFormat("dd-MM-yyyy")
    axis_x.setTickCount(min(6, max(2, len(ruwe))))
    axis_x.setLabelsColor(QColor("#F0F0F0"))
    axis_x.setGridLineColor(QColor("#3A3A3A"))

    axis_y = QValueAxis()
    axis_y.setTitleText("ESR (mΩ)")
    axis_y.setLabelsColor(QColor("#F0F0F0"))
    axis_y.setTitleBrush(QColor("#F0F0F0"))
    axis_y.setGridLineColor(QColor("#3A3A3A"))
    # v1.0.3: applyNiceNumbers() verwijderd (zie moduleheader).

    chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
    chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
    series.attachAxis(axis_x)
    series.attachAxis(axis_y)

    first_ms = _veilige_x_ms(ruwe[0][0])
    last_ms = _veilige_x_ms(ruwe[-1][0])
    if first_ms == last_ms:
        first_ms = _veilige_x_ms(first_ms - 60_000)
        last_ms = _veilige_x_ms(last_ms + 60_000)
    if first_ms >= last_ms:
        last_ms = first_ms + 60_000
    axis_x.setRange(
        QDateTime.fromMSecsSinceEpoch(first_ms),
        QDateTime.fromMSecsSinceEpoch(last_ms),
    )

    y_values = [y for _, y in ruwe]
    y_min, y_max, _n_outliers = bereken_y_as_range(y_values)
    axis_y.setRange(y_min, y_max)

    return _chart_naar_base64_png(chart)


def render_scatter_png_base64(
    analysis_service: AnalysisService,
    *,
    filters: dict[str, Any] | None = None,
) -> str | None:
    """Scatter ESR vs. C als base64-PNG. None als er geen geldige punten zijn."""
    punten: list[ScatterPoint] = analysis_service.scatter_esr_vs_capacitance(
        filters or {}
    )

    # v1.0.2: schaal eerst (µF, mΩ), filter daarna.
    geschaald: list[tuple[ScatterPoint, float, float]] = []
    for p in punten:
        if not _is_finite(p.x) or not _is_finite(p.y):
            continue
        x_scaled = p.x * 1e6
        y_scaled = p.y * 1000.0
        if not _is_finite(x_scaled) or not _is_finite(y_scaled):
            continue
        geschaald.append((p, x_scaled, y_scaled))

    if len(geschaald) < 2:
        return None

    geldig = [p for p, _, _ in geschaald]
    x_geschaald = [x for _, x, _ in geschaald]
    y_geschaald = [y for _, _, y in geschaald]

    chart = QChart()
    _stijl_chart(chart)
    chart.setTitle("ESR vs. capaciteit")
    chart.legend().setVisible(True)

    per_categorie: dict[str | None, list[ScatterPoint]] = {}
    for punt in geldig:
        per_categorie.setdefault(punt.category, []).append(punt)

    for categorie, groep in per_categorie.items():
        series = QScatterSeries()
        series.setMarkerSize(11.0)
        series.setName(categorie or "onbekend")
        series.setColor(
            QColor(
                STATUS_COLORS.get(categorie or "", _SCATTER_NEUTRAL_COLOR)
                if categorie
                else _SCATTER_NEUTRAL_COLOR
            )
        )
        series.setBorderColor(QColor("#1E1E1E"))
        for punt in groep:
            series.append(punt.x * 1e6, punt.y * 1000.0)
        chart.addSeries(series)

    x_min = min(x_geschaald)
    x_max = max(x_geschaald)
    if x_min == x_max:
        x_min -= 1.0
        x_max += 1.0

    x_tick_count, x_label_format, x_labels_angle = bereken_x_as_ticks(
        x_min, x_max
    )

    axis_x = QValueAxis()
    axis_x.setTitleText("C (µF)")
    axis_x.setLabelFormat(x_label_format)
    axis_x.setTickCount(x_tick_count)
    axis_x.setLabelsAngle(x_labels_angle)
    axis_x.setLabelsColor(QColor("#F0F0F0"))
    axis_x.setTitleBrush(QColor("#F0F0F0"))
    axis_x.setGridLineColor(QColor("#3A3A3A"))

    axis_y = QValueAxis()
    axis_y.setTitleText("ESR (mΩ)")
    axis_y.setLabelsColor(QColor("#F0F0F0"))
    axis_y.setTitleBrush(QColor("#F0F0F0"))
    axis_y.setGridLineColor(QColor("#3A3A3A"))

    chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
    chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
    for series in chart.series():
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

    axis_x.setRange(x_min, x_max)
    y_min, y_max, _n_outliers = bereken_y_as_range(y_geschaald)
    axis_y.setRange(y_min, y_max)

    return _chart_naar_base64_png(chart)


def render_chart_voor_detail(
    detail: dict[str, Any],
    *,
    analysis_service: AnalysisService | None = None,
    taal: str = "nl_NL",
) -> str | None:
    """Kies de juiste grafiek voor één detail en geef base64-PNG terug."""
    measurement = detail.get("measurement")
    if measurement is None:
        return None
    tool_key = str(getattr(measurement, "tool_key", "") or "")
    if tool_key != "ESR_CAPACITOR":
        return None

    service = analysis_service or AnalysisService()

    model = detail.get("component_model")
    filters = build_history_filters(
        tool_key="ESR_CAPACITOR",
        manufacturer=getattr(model, "manufacturer", None) if model else None,
        series=getattr(model, "series", None) if model else None,
    )

    # Eerst ESR-over-tijd proberen; als dat te weinig punten geeft, scatter.
    png = render_esr_over_tijd_png_base64(service, filters=filters)
    if png is not None:
        return png
    return render_scatter_png_base64(service, filters=filters)