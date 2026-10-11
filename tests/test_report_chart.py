"""
================================================================================
Module:     tests/test_report_chart.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-10
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de Qt-specifieke grafiek-helper.

Wijzigingen:
  v1.0.0 (2026-10-10)  Eerste versie: base64-PNG-output, decodeerbaarheid,
                        lege reeks, niet-ESR tool.
================================================================================
"""

from __future__ import annotations

import base64
import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from app.helpers.analysis_series import ScatterPoint, TimeSeriesPoint
from app.helpers.report_chart import (
    render_chart_voor_detail,
    render_esr_over_tijd_png_base64,
    render_scatter_png_base64,
)


@pytest.fixture(scope="module", autouse=True)
def qapplication():
    app = QApplication.instance() or QApplication([])
    yield app


class _StubAnalysisService:
    def __init__(self, *, esr_reeks=None, scatter_reeks=None):
        self._esr = esr_reeks or []
        self._scatter = scatter_reeks or []

    def esr_series(self, filters=None, *, aggregation="raw"):
        return list(self._esr)

    def capacitance_series(self, filters=None, *, aggregation="raw"):
        return list(self._esr)

    def dissipation_series(self, filters=None, *, aggregation="raw"):
        return list(self._esr)

    def scatter_esr_vs_capacitance(self, filters=None):
        return list(self._scatter)


def _esr_punten():
    return [
        TimeSeriesPoint(x_ms=1_700_000_000_000, y=0.1, measurement_id=1, tool_key="ESR_CAPACITOR"),
        TimeSeriesPoint(x_ms=1_700_000_100_000, y=0.15, measurement_id=2, tool_key="ESR_CAPACITOR"),
        TimeSeriesPoint(x_ms=1_700_000_200_000, y=0.2, measurement_id=3, tool_key="ESR_CAPACITOR"),
    ]


def _scatter_punten():
    return [
        ScatterPoint(x=465e-6, y=0.2, measurement_id=1, tool_key="ESR_CAPACITOR", category="goed"),
        ScatterPoint(x=470e-6, y=0.15, measurement_id=2, tool_key="ESR_CAPACITOR", category="goed"),
        ScatterPoint(x=475e-6, y=0.25, measurement_id=3, tool_key="ESR_CAPACITOR", category="aandachtspunt"),
    ]


# ---------------------------------------------------------------------------
# ESR over tijd
# ---------------------------------------------------------------------------

def test_render_esr_over_tijd_geeft_base64_png():
    service = _StubAnalysisService(esr_reeks=_esr_punten())
    png = render_esr_over_tijd_png_base64(service)

    assert png is not None
    ruwe_bytes = base64.b64decode(png)
    # PNG-header: 89 50 4E 47 0D 0A 1A 0A
    assert ruwe_bytes[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_esr_over_tijd_none_bij_te_weinig_punten():
    service = _StubAnalysisService(esr_reeks=_esr_punten()[:1])
    png = render_esr_over_tijd_png_base64(service)

    assert png is None


def test_render_esr_over_tijd_none_bij_lege_reeks():
    service = _StubAnalysisService(esr_reeks=[])
    png = render_esr_over_tijd_png_base64(service)

    assert png is None


def test_render_esr_over_tijd_negeert_nan_en_inf():
    punten = _esr_punten() + [
        TimeSeriesPoint(x_ms=1_700_000_300_000, y=float("nan"), measurement_id=4, tool_key="ESR_CAPACITOR"),
        TimeSeriesPoint(x_ms=1_700_000_400_000, y=float("inf"), measurement_id=5, tool_key="ESR_CAPACITOR"),
    ]
    service = _StubAnalysisService(esr_reeks=punten)

    png = render_esr_over_tijd_png_base64(service)

    assert png is not None  # 3 geldige punten blijven over
    base64.b64decode(png)  # decodeerbaar


# ---------------------------------------------------------------------------
# Scatter
# ---------------------------------------------------------------------------

def test_render_scatter_geeft_base64_png():
    service = _StubAnalysisService(scatter_reeks=_scatter_punten())
    png = render_scatter_png_base64(service)

    assert png is not None
    ruwe_bytes = base64.b64decode(png)
    assert ruwe_bytes[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_scatter_none_bij_te_weinig_punten():
    service = _StubAnalysisService(scatter_reeks=_scatter_punten()[:1])
    png = render_scatter_png_base64(service)

    assert png is None


# ---------------------------------------------------------------------------
# render_chart_voor_detail
# ---------------------------------------------------------------------------

def _detail(tool_key: str = "ESR_CAPACITOR"):
    return {
        "measurement": SimpleNamespace(id=1, tool_key=tool_key, measured_at_ms=1_700_000_000_000),
        "component_model": SimpleNamespace(manufacturer="TEST", series="SYN", part_number=None),
    }


def test_render_chart_voor_detail_esr_gebruikt_esr_reeks():
    service = _StubAnalysisService(esr_reeks=_esr_punten())
    png = render_chart_voor_detail(_detail("ESR_CAPACITOR"), analysis_service=service)

    assert png is not None


def test_render_chart_voor_detail_esr_valt_terug_op_scatter():
    service = _StubAnalysisService(
        esr_reeks=_esr_punten()[:1],
        scatter_reeks=_scatter_punten(),
    )
    png = render_chart_voor_detail(_detail("ESR_CAPACITOR"), analysis_service=service)

    assert png is not None


def test_render_chart_voor_detail_andere_tool_geeft_none():
    service = _StubAnalysisService(esr_reeks=_esr_punten())
    png = render_chart_voor_detail(_detail("RESISTOR"), analysis_service=service)

    assert png is None


def test_render_chart_voor_detail_zonder_measurement_geeft_none():
    png = render_chart_voor_detail({}, analysis_service=_StubAnalysisService(esr_reeks=_esr_punten()))

    assert png is None