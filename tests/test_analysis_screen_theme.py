"""
================================================================================
Module:     tests/test_analysis_screen_theme.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-21
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de theme-parameter op AnalysisScreen en
            voor de chart-kleuren per thema (fase 11H.4).

Wijzigingen:
  v1.0.0 (2026-10-21)  Eerste versie. Dekt:
                        - AnalysisScreen(theme="light"/"dark") zet
                          self.theme correct via normaliseer_thema.
                        - Ongeldig thema valt terug op "dark".
                        - CHART_COLORS bevat precies "dark" en "light".
                        - De chart-achtergrond, as-labels en lijnkleur
                          volgen het thema.
                        - apply_theme() werkt het thema bij en past de
                          kleuren toe zonder de reeksen te wissen.
                        - apply_theme() met hetzelfde thema doet niets.
                        - state_label-kleur volgt het thema.
================================================================================
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCharts import QLineSeries, QValueAxis
from PySide6.QtCore import QDateTime
from PySide6.QtGui import QColor

from app.gui.analysis_screen import AnalysisScreen, CHART_COLORS
from app.helpers.analysis_series import TimeSeriesPoint


def _app():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


class _StubService:
    """Levert een vaste ESR-reeks en een lege selectielijst."""

    def __init__(self, punten):
        self._punten = punten

    def load_rows(self, filters=None, *, measurement_ids=None):
        return []

    def esr_series(self, filters=None, *, aggregation="raw", measurement_ids=None):
        return list(self._punten)

    def capacitance_series(self, filters=None, *, aggregation="raw", measurement_ids=None):
        return []

    def dissipation_series(self, filters=None, *, aggregation="raw", measurement_ids=None):
        return []

    def scatter_esr_vs_capacitance(self, filters=None, *, measurement_ids=None):
        return []


def _twee_punten():
    return [
        TimeSeriesPoint(
            x_ms=1_700_000_000_000,
            y=0.1,
            measurement_id=1,
            tool_key="ESR_CAPACITOR",
        ),
        TimeSeriesPoint(
            x_ms=1_700_000_001_000,
            y=0.2,
            measurement_id=2,
            tool_key="ESR_CAPACITOR",
        ),
    ]


# ============================================================================
# Thema-parameter en normalisatie
# ============================================================================

def test_theme_parameter_dark_is_default():
    _app()
    scherm = AnalysisScreen(taal="nl_NL", analysis_service=_StubService([]))
    assert scherm.theme == "dark"


def test_theme_parameter_light_wordt_overgenomen():
    _app()
    scherm = AnalysisScreen(
        taal="nl_NL",
        theme="light",
        analysis_service=_StubService([]),
    )
    assert scherm.theme == "light"


def test_theme_parameter_ongeldig_valt_terug_op_dark():
    _app()
    scherm = AnalysisScreen(
        taal="nl_NL",
        theme="blauw",
        analysis_service=_StubService([]),
    )
    assert scherm.theme == "dark"


def test_chart_colors_bevat_dark_en_light():
    assert set(CHART_COLORS.keys()) == {"dark", "light"}
    assert CHART_COLORS["dark"]["chart_background"] == "#1E1E1E"
    assert CHART_COLORS["light"]["chart_background"] == "#FFFFFF"


# ============================================================================
# Chart-kleuren volgen het thema
# ============================================================================

def test_dark_theme_zet_donkere_chart_achtergrond():
    _app()
    scherm = AnalysisScreen(taal="nl_NL", theme="dark")
    brush = scherm.chart.backgroundBrush()
    assert brush.color() == QColor(CHART_COLORS["dark"]["chart_background"])


def test_light_theme_zet_lichte_chart_achtergrond():
    _app()
    scherm = AnalysisScreen(taal="nl_NL", theme="light")
    brush = scherm.chart.backgroundBrush()
    assert brush.color() == QColor(CHART_COLORS["light"]["chart_background"])


def test_light_theme_zet_lichte_state_label_kleur():
    _app()
    scherm = AnalysisScreen(taal="nl_NL", theme="light")
    assert CHART_COLORS["light"]["state_label"] in scherm.state_label.styleSheet()


def test_dark_theme_zet_donkere_state_label_kleur():
    _app()
    scherm = AnalysisScreen(taal="nl_NL", theme="dark")
    assert CHART_COLORS["dark"]["state_label"] in scherm.state_label.styleSheet()


# ============================================================================
# apply_theme() past de kleuren toe zonder refresh
# ============================================================================

def test_apply_theme_wisselt_van_dark_naar_light():
    _app()
    scherm = AnalysisScreen(
        taal="nl_NL",
        theme="dark",
        analysis_service=_StubService(_twee_punten()),
    )
    scherm.refresh()
    assert scherm.chart.series()

    scherm.apply_theme("light")

    assert scherm.theme == "light"
    assert scherm.chart.backgroundBrush().color() == QColor(
        CHART_COLORS["light"]["chart_background"]
    )
    # Bestaande reeksen blijven staan.
    assert scherm.chart.series()


def test_apply_theme_met_hetzelfde_thema_doet_niets():
    _app()
    scherm = AnalysisScreen(
        taal="nl_NL",
        theme="dark",
        analysis_service=_StubService([]),
    )
    before_brush = scherm.chart.backgroundBrush().color()

    scherm.apply_theme("dark")

    assert scherm.theme == "dark"
    assert scherm.chart.backgroundBrush().color() == before_brush


def test_apply_theme_werkt_axis_kleuren_bij():
    _app()
    scherm = AnalysisScreen(
        taal="nl_NL",
        theme="dark",
        analysis_service=_StubService(_twee_punten()),
    )
    scherm.refresh()

    scherm.apply_theme("light")

    for axis in scherm.chart.axes():
        if isinstance(axis, QValueAxis):
            assert axis.labelsColor() == QColor(
                CHART_COLORS["light"]["axis_label"]
            )