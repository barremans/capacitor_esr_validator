"""
================================================================================
Module:     tests/test_analysis_screen_nan.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.2
Datum:      2026-10-10
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de NaN/Inf-verdediging in AnalysisScreen
            (fase 8B.2, 8B.2a en 8B.2b). Bewijst dat niet-eindige
            meetwaarden de grafiek niet laten crashen en geen Qt-
            waarschuwingen meer veroorzaken.

Wijzigingen:
  v1.0.0 (2026-10-10)  Eerste versie: _finite_filter, tijdreeks en scatter
                        met NaN/Inf-input.
  v1.0.1 (2026-10-10)  Extra tests voor overloop na schaling (8B.2a):
                        een eindige p.x of p.y die door de vermenigvuldiging
                        ±Inf wordt, moet ook worden weggefilterd.
  v1.0.2 (2026-10-10)  Extra tests voor absurde x_ms (8B.2b): de x-as
                        wordt geklemd op [1970-01-01, 2100-01-01] zodat
                        QDateTime.fromMSecsSinceEpoch niet overloopt.
================================================================================
"""

from __future__ import annotations

import math
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from app.gui.analysis_screen import (
    AnalysisScreen,
    _is_finite,
    _veilige_x_ms,
)
from app.helpers.analysis_series import ScatterPoint, TimeSeriesPoint


@pytest.fixture(scope="module", autouse=True)
def qapplication():
    app = QApplication.instance() or QApplication([])
    yield app


class _StubAnalysisService:
    """Analyse-service die vaste reeksen teruggeeft, inclusief NaN/Inf."""

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


# ---------------------------------------------------------------------------
# _is_finite
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "waarde,verwacht",
    [
        (1.0, True),
        (0, True),
        (-1.5, True),
        (float("nan"), False),
        (float("inf"), False),
        (float("-inf"), False),
        (None, False),
        (True, False),
        (False, False),
        ("1.0", False),
    ],
)
def test_is_finite(waarde, verwacht):
    assert _is_finite(waarde) is verwacht


# ---------------------------------------------------------------------------
# _veilige_x_ms
# ---------------------------------------------------------------------------

def test_veilige_x_ms_klemt_negatief_op_nul():
    assert _veilige_x_ms(-1000) == 0


def test_veilige_x_ms_klemt_te_groot_op_max():
    assert _veilige_x_ms(10**18) == 4_102_444_800_000


def test_veilige_x_ms_laat_geldige_waarde_onveranderd():
    assert _veilige_x_ms(1_700_000_000_000) == 1_700_000_000_000


# ---------------------------------------------------------------------------
# _finite_filter
# ---------------------------------------------------------------------------

def test_finite_filter_verwijdert_nan_en_inf():
    punten = [
        (1_700_000_000_000, 100.0),
        (1_700_000_001_000, float("nan")),
        (1_700_000_002_000, float("inf")),
        (1_700_000_003_000, float("-inf")),
        (1_700_000_004_000, 200.0),
    ]

    resultaat = AnalysisScreen._finite_filter(punten)

    assert resultaat == [
        (1_700_000_000_000, 100.0),
        (1_700_000_004_000, 200.0),
    ]


def test_finite_filter_leeg_bij_alleen_nan():
    punten = [
        (1_700_000_000_000, float("nan")),
        (1_700_000_001_000, float("inf")),
    ]

    assert AnalysisScreen._finite_filter(punten) == []


# ---------------------------------------------------------------------------
# Tijdreeks met NaN
# ---------------------------------------------------------------------------

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


def test_draw_time_series_met_alleen_nan_valt_terug_op_leeg():
    punten = [
        TimeSeriesPoint(
            x_ms=1_700_000_000_000,
            y=float("nan"),
            measurement_id=1,
            tool_key="ESR_CAPACITOR",
        ),
        TimeSeriesPoint(
            x_ms=1_700_000_001_000,
            y=float("inf"),
            measurement_id=2,
            tool_key="ESR_CAPACITOR",
        ),
    ]

    scherm = AnalysisScreen(
        taal="nl_NL",
        analysis_service=_StubAnalysisService(esr_reeks=punten),
    )
    scherm.refresh()

    assert scherm.state_label.text()
    assert len(scherm.chart.series()) == 0


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
            # 1e308 is eindig, maar 1e308 * 1000 = +Inf.
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
    # Mag niet crashen en er moeten assen zijn.
    scherm.refresh()
    assert scherm.chart.axes()


# ---------------------------------------------------------------------------
# Scatter met NaN
# ---------------------------------------------------------------------------

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


def test_draw_scatter_met_alleen_nan_valt_terug_op_leeg():
    punten = [
        ScatterPoint(
            x=float("nan"),
            y=float("nan"),
            measurement_id=1,
            tool_key="ESR_CAPACITOR",
            category=None,
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

    assert len(scherm.chart.series()) == 0


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
            # 1e308 is eindig, maar 1e308 * 1000 = +Inf.
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


# ---------------------------------------------------------------------------
# apply_language doet geen refresh meer (8B.2a)
# ---------------------------------------------------------------------------

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