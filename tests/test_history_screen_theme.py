"""
================================================================================
Module:     tests/test_history_screen_theme.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-21
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de theme-parameter op HistoryScreen en
            voor de detail-HTML per thema (fase 11H.5).

Wijzigingen:
  v1.0.0 (2026-10-21)  Eerste versie. Dekt:
                        - HistoryScreen(theme="light"/"dark") zet
                          self.theme correct via normaliseer_thema.
                        - Ongeldig thema valt terug op "dark".
                        - DETAIL_HTML_COLORS bevat precies "dark" en
                          "light".
                        - De state_label-kleur volgt het thema.
                        - apply_theme() werkt het thema bij en past de
                          state-label-kleur aan zonder refresh.
                        - apply_theme() met hetzelfde thema doet niets.
                        - _build_detail_html gebruikt de per-thema
                          QTextBrowser-stylesheet.
================================================================================
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from types import SimpleNamespace

from PySide6.QtWidgets import QApplication

from app.gui.history_screen import HistoryScreen, DETAIL_HTML_COLORS


def _app():
    return QApplication.instance() or QApplication([])


class _LegeService:
    """Levert geen metingen en geen detail."""

    def list_measurements(self, filters=None, *, limit=100, offset=0):
        return []

    def get_measurement_detail(self, measurement_id):
        return None


# ============================================================================
# Thema-parameter en normalisatie
# ============================================================================

def test_theme_parameter_dark_is_default():
    _app()
    scherm = HistoryScreen(taal="nl_NL", history_service=_LegeService())
    assert scherm.theme == "dark"


def test_theme_parameter_light_wordt_overgenomen():
    _app()
    scherm = HistoryScreen(
        taal="nl_NL",
        theme="light",
        history_service=_LegeService(),
    )
    assert scherm.theme == "light"


def test_theme_parameter_ongeldig_valt_terug_op_dark():
    _app()
    scherm = HistoryScreen(
        taal="nl_NL",
        theme="blauw",
        history_service=_LegeService(),
    )
    assert scherm.theme == "dark"


def test_detail_html_colors_bevat_dark_en_light():
    assert set(DETAIL_HTML_COLORS.keys()) == {"dark", "light"}
    assert DETAIL_HTML_COLORS["dark"]["body_bg"] == "#1E1E1E"
    assert DETAIL_HTML_COLORS["light"]["body_bg"] == "#FFFFFF"


# ============================================================================
# State-label-kleur volgt het thema
# ============================================================================

def test_dark_theme_zet_donkere_state_label_kleur():
    _app()
    scherm = HistoryScreen(
        taal="nl_NL", theme="dark", history_service=_LegeService()
    )
    assert DETAIL_HTML_COLORS["dark"]["state_label"] in scherm.state_label.styleSheet()


def test_light_theme_zet_lichte_state_label_kleur():
    _app()
    scherm = HistoryScreen(
        taal="nl_NL", theme="light", history_service=_LegeService()
    )
    assert DETAIL_HTML_COLORS["light"]["state_label"] in scherm.state_label.styleSheet()


# ============================================================================
# apply_theme() werkt de state-label-kleur bij
# ============================================================================

def test_apply_theme_wisselt_van_dark_naar_light():
    _app()
    scherm = HistoryScreen(
        taal="nl_NL", theme="dark", history_service=_LegeService()
    )

    scherm.apply_theme("light")

    assert scherm.theme == "light"
    assert DETAIL_HTML_COLORS["light"]["state_label"] in scherm.state_label.styleSheet()


def test_apply_theme_met_hetzelfde_thema_doet_niets():
    _app()
    scherm = HistoryScreen(
        taal="nl_NL", theme="dark", history_service=_LegeService()
    )
    before = scherm.state_label.styleSheet()

    scherm.apply_theme("dark")

    assert scherm.theme == "dark"
    assert scherm.state_label.styleSheet() == before


def test_apply_theme_ongeldig_valt_terug_op_dark():
    _app()
    scherm = HistoryScreen(
        taal="nl_NL", theme="light", history_service=_LegeService()
    )

    scherm.apply_theme("blauw")

    assert scherm.theme == "dark"


# ============================================================================
# Detail-HTML gebruikt de per-thema QTextBrowser-stylesheet
# ============================================================================

def test_show_detail_dialog_dark_gebruikt_donkere_stylesheet(monkeypatch):
    """De detaildialoog gebruikt de donkere QTextBrowser-stijl."""
    _app()
    scherm = HistoryScreen(
        taal="nl_NL", theme="dark", history_service=_LegeService()
    )

    # We monitoren de stylesheet die op de QTextBrowser wordt gezet
    # door _show_detail_dialog. De dialoog roept exec() aan; die
    # monkeypatchen we weg zodat de test niet blokkeert.
    vastgelegd = {}

    from PySide6.QtWidgets import QTextBrowser
    origineel = QTextBrowser.setHtml

    def _fake_set_html(self, html):
        vastgelegd.setdefault("stylesheets", []).append(
            self.document().defaultStyleSheet()
        )
        return origineel(self, html)

    monkeypatch.setattr(QTextBrowser, "setHtml", _fake_set_html)
    monkeypatch.setattr(
        "app.gui.history_screen.QDialog.exec", lambda self: 0
    )

    detail = _minimale_detail()
    scherm._show_detail_dialog(detail)

    assert vastgelegd["stylesheets"]
    ss = vastgelegd["stylesheets"][0]
    assert DETAIL_HTML_COLORS["dark"]["body_bg"] in ss
    assert DETAIL_HTML_COLORS["dark"]["body_fg"] in ss


def test_show_detail_dialog_light_gebruikt_lichte_stylesheet(monkeypatch):
    _app()
    scherm = HistoryScreen(
        taal="nl_NL", theme="light", history_service=_LegeService()
    )

    vastgelegd = {}

    from PySide6.QtWidgets import QTextBrowser
    origineel = QTextBrowser.setHtml

    def _fake_set_html(self, html):
        vastgelegd.setdefault("stylesheets", []).append(
            self.document().defaultStyleSheet()
        )
        return origineel(self, html)

    monkeypatch.setattr(QTextBrowser, "setHtml", _fake_set_html)
    monkeypatch.setattr(
        "app.gui.history_screen.QDialog.exec", lambda self: 0
    )

    detail = _minimale_detail()
    scherm._show_detail_dialog(detail)

    assert vastgelegd["stylesheets"]
    ss = vastgelegd["stylesheets"][0]
    assert DETAIL_HTML_COLORS["light"]["body_bg"] in ss
    assert DETAIL_HTML_COLORS["light"]["body_fg"] in ss


def _minimale_detail():
    """Minimale detail-structuur voor _show_detail_dialog."""
    return {
        "measurement": SimpleNamespace(
            id=1,
            tool_key="ESR_CAPACITOR",
            measured_at_ms=1_700_000_000_000,
            measurement_method="EX_SITU",
            instrument_name="LCR-ST1",
            instrument_key="LCR_ST1",
            frequency_hz=1000.0,
            test_voltage_vrms=0.6,
            temperature_c=20.0,
            power_off_confirmed=True,
            discharged_confirmed=True,
            capacitance_f=465e-6,
            esr_ohm=0.2,
            dissipation_factor_d=None,
            out_of_range=False,
            open_suspected=False,
            short_suspected=False,
        ),
        "component_model": SimpleNamespace(
            manufacturer="TEST",
            series="SYN",
            part_number=None,
            technology="Aluminium elektrolytisch",
            nominal_capacitance_value=470.0,
            nominal_capacitance_unit="µF",
            nominal_capacitance_f=470e-6,
            rated_voltage_v=16.0,
            tolerance_lower_pct=-20.0,
            tolerance_upper_pct=20.0,
        ),
        "component_sample": SimpleNamespace(
            sample_state=SimpleNamespace(value="nieuw"),
        ),
        "measurement_session": SimpleNamespace(
            started_at_ms=1_700_000_000_000,
            ended_at_ms=1_700_000_001_000,
        ),
        "assessment_snapshots": [],
        "reference_snapshots_by_assessment_id": {},
    }