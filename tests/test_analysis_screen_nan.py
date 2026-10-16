"""
================================================================================
Module:     tests/test_analysis_screen_nan.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.3
Datum:      2026-10-16
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de NaN/Inf-verdediging in AnalysisScreen
            (Fase 7B.2) en voor het niet-blokkeren van refresh bij
            onvolledige meetwaarden.

Wijzigingen:
  v1.0.0 (2026-10-10)  Eerste versie: NaN/Inf in tijdreeksen en scatter.
  v1.0.1 (2026-10-10)  Fix: _is_finite accepteert uitsluitend int/float.
  v1.0.2 (2026-10-10)  Fix: applyNiceNumbers() verwijderd.
  v1.0.3 (2026-10-16)  Fase 11A.3-fix: _StubAnalysisService heeft nu ook
                        een load_rows()-methode. Sinds 11A.1 roept
                        AnalysisScreen.refresh() eerst load_rows() aan
                        voor de selectielijst. Zonder die methode op de
                        stub faalde refresh() met "object has no attribute
                        'load_rows'" en werd de rest van de test niet
                        uitgevoerd. De stub retourneert een lege lijst
                        voor de selectielijst; de reeksen/scatter blijven
                        gevuld zoals voorheen. Geen wijziging aan de
                        productiecode.
================================================================================
"""

from __future__ import annotations

import os
from typing import Any

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from app.helpers.analysis_series import ScatterPoint, TimeSeriesPoint
from app.gui.analysis_screen import AnalysisScreen


def _app():
    return QApplication.instance() or QApplication([])


class _StubAnalysisService:
    """Bevriest reeksen en levert een lege selectielijst voor load_rows.

    Sinds 11A.1 roept AnalysisScreen.refresh() eerst load_rows() aan
    voor de selectielijst. De stub moet die methode dus hebben. We
    retourneren een lege lijst, zodat de grafiek-tests zich op de
    reeksen kunnen blijven richten.
    """

    def __init__(
        self,
        *,
        esr_reeks: list[TimeSeriesPoint] | None = None,
        scatter_reeks: list[ScatterPoint] | None = None,
        rows: list[dict[str, Any]] | None = None,
    ) -> None:
        self._esr = esr_reeks or []
        self._scatter = scatter_reeks or []
        self._rows = rows or []

    def load_rows(self, filters=None):
        return list(self._rows)

    def esr_series(self, filters=None, *, aggregation="raw"):
        return list(self._esr)

    def capacitance_series(self, filters=None, *, aggregation="raw"):
        return []

    def dissipation_series(self, filters=None, *, aggregation="raw"):
        return []

    def scatter_esr_vs_capacitance(self, filters=None):
        return list(self._scatter)


# ============================================================================
# Tijdreeksen met NaN/Inf
# ============================================================================

def test_draw_time_series_met_nan_crasht_niet():
    punten = [
        TimeSeriesPoint(
            x_ms=1_700_000_000_000,
            y=0.1,
            measurement_id=1,
            tool_key="ESR_CAPACITOR",
        ),
        TimeSeriesPoint(
            x_ms=1_700_000_001_000,
            y=float("nan"),
            measurement_id=2,
            tool_key="ESR_CAPACITOR",
        ),
        TimeSeriesPoint(
            x_ms=1_700_000_002_000,
            y=0.2,
            measurement_id=3,
            tool_key="ESR_CAPACITOR",
        ),
    ]

    scherm = AnalysisScreen(
        taal="nl_NL",
        analysis_service=_StubAnalysisService(esr_reeks=punten),
    )
    scherm.refresh()

    assert "2" in scherm.state_label.text()


def test_draw_time_series_overloop_na_schaling_wordt_gefilterd():
    """Een eindige y die door vermenigvuldiging ±Inf wordt, moet ook weg."""
    punten = [
        TimeSeriesPoint(
            x_ms=1_700_000_000_000,
            y=0.1,
            measurement_id=1,
            tool_key="ESR_CAPACITOR",
        ),
        TimeSeriesPoint(
            x_ms=1_700_000_001_000,
            y=1e308,
            measurement_id=2,
            tool_key="ESR_CAPACITOR",
        ),
        TimeSeriesPoint(
            x_ms=1_700_000_002_000,
            y=0.2,
            measurement_id=3,
            tool_key="ESR_CAPACITOR",
        ),
    ]

    scherm = AnalysisScreen(
        taal="nl_NL",
        analysis_service=_StubAnalysisService(esr_reeks=punten),
    )
    scherm.refresh()

    assert "2" in scherm.state_label.text()


def test_draw_time_series_met_absurd_grote_x_crasht_niet():
    """Een x_ms van 1e18 mag QDateTime niet laten overlopen (8B.2b)."""
    punten = [
        TimeSeriesPoint(
            x_ms=1_700_000_000_000, y=0.1, measurement_id=1, tool_key="ESR_CAPACITOR"
        ),
        TimeSeriesPoint(
            x_ms=10**18, y=0.2, measurement_id=2, tool_key="ESR_CAPACITOR"
        ),
    ]
    scherm = AnalysisScreen(
        taal="nl_NL",
        analysis_service=_StubAnalysisService(esr_reeks=punten),
    )
    scherm.refresh()
    assert scherm.chart.axes()


# ============================================================================
# Scatter met NaN/Inf
# ============================================================================

def test_draw_scatter_met_nan_crasht_niet():
    punten = [
        ScatterPoint(
            x=465e-6,
            y=0.2,
            measurement_id=1,
            tool_key="ESR_CAPACITOR",
            category="aandachtspunt",
        ),
        ScatterPoint(
            x=float("nan"),
            y=0.3,
            measurement_id=2,
            tool_key="ESR_CAPACITOR",
            category="goed",
        ),
        ScatterPoint(
            x=470e-6,
            y=float("inf"),
            measurement_id=3,
            tool_key="ESR_CAPACITOR",
            category="goed",
        ),
        ScatterPoint(
            x=480e-6,
            y=0.25,
            measurement_id=4,
            tool_key="ESR_CAPACITOR",
            category="goed",
        ),
    ]

    scherm = AnalysisScreen(
        taal="nl_NL",
        analysis_service=_StubAnalysisService(scatter_reeks=punten),
    )
    scherm.chart_type_combo.setCurrentIndex(
        scherm.chart_type_combo.findData("SCATTER_ESR_C")
    )
    scherm.refresh()

    assert "2" in scherm.state_label.text()


def test_draw_scatter_overloop_na_schaling_wordt_gefilterd():
    """Een eindige p.x of p.y die door schaling ±Inf wordt, moet ook weg."""
    punten = [
        ScatterPoint(
            x=465e-6,
            y=0.2,
            measurement_id=1,
            tool_key="ESR_CAPACITOR",
            category="goed",
        ),
        ScatterPoint(
            x=465e-6,
            y=1e308,
            measurement_id=2,
            tool_key="ESR_CAPACITOR",
            category="goed",
        ),
        ScatterPoint(
            x=470e-6,
            y=0.25,
            measurement_id=3,
            tool_key="ESR_CAPACITOR",
            category="goed",
        ),
    ]

    scherm = AnalysisScreen(
        taal="nl_NL",
        analysis_service=_StubAnalysisService(scatter_reeks=punten),
    )
    scherm.chart_type_combo.setCurrentIndex(
        scherm.chart_type_combo.findData("SCATTER_ESR_C")
    )
    scherm.refresh()

    assert "2" in scherm.state_label.text()


# ============================================================================
# apply_language doet geen service-call
# ============================================================================

def test_apply_language_doet_geen_service_call():
    """Sinds v1.0.5 doet apply_language geen data-refresh meer."""
    service = _StubAnalysisService(esr_reeks=[
        TimeSeriesPoint(
            x_ms=1_700_000_000_000, y=0.1, measurement_id=1, tool_key="ESR_CAPACITOR"
        ),
        TimeSeriesPoint(
            x_ms=1_700_000_001_000, y=0.2, measurement_id=2, tool_key="ESR_CAPACITOR"
        ),
    ])

    class _TelService:
        def __init__(self, inner):
            self._inner = inner
            self.calls = 0

        def load_rows(self, filters=None):
            return self._inner.load_rows(filters)

        def esr_series(self, filters=None, *, aggregation="raw"):
            self.calls += 1
            return self._inner.esr_series(filters, aggregation=aggregation)

        def capacitance_series(self, filters=None, *, aggregation="raw"):
            self.calls += 1
            return self._inner.capacitance_series(filters, aggregation=aggregation)

        def dissipation_series(self, filters=None, *, aggregation="raw"):
            self.calls += 1
            return self._inner.dissipation_series(filters, aggregation=aggregation)

        def scatter_esr_vs_capacitance(self, filters=None):
            self.calls += 1
            return self._inner.scatter_esr_vs_capacitance(filters)

    tel = _TelService(service)
    scherm = AnalysisScreen(taal="nl_NL", analysis_service=tel)

    # Bij constructie: geen refresh, dus 0 calls.
    assert tel.calls == 0

    # Taalwissel: nog steeds geen refresh.
    scherm.apply_language("en_US")
    assert tel.calls == 0

    # Expliciete refresh: nu wel.
    scherm.refresh()
    assert tel.calls == 1