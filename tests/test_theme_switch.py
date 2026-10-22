"""
================================================================================
Module:     tests/test_theme_switch.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-21
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de theme-parameter op ToolHubWindow en de
            live themawissel via _apply_settings (fase 11H.3).

Wijzigingen:
  v1.0.0 (2026-10-21)  Eerste versie.
  v1.0.1 (2026-10-21)  Fix na v1.0.0: ToolHubWindow.__init__ past het
                        thema nu ook bij opstart toe.
  v1.0.2 (2026-10-21)  Performance: elke test ruimt zijn ToolHubWindow
                        op via deleteLater() + processEvents().
  v1.0.3 (2026-10-21)  Opruiming gecentraliseerd in conftest.py.
  v1.1.0 (2026-10-21)  Sinds main_window.py v2.22.0 beheert het venster
                        zijn eigen stylesheet (self.setStyleSheet in
                        plaats van QApplication.setStyleSheet). De
                        tests controleren daarom window.styleSheet()
                        in plaats van QApplication.instance().styleSheet().
                        Dat is wat de nieuwe architectuur belooft: het
                        venster is eigenaar van zijn stijl, de globale
                        QApplication-stylesheet is alleen voor dialogen
                        zonder parent (gezet door main.py bij opstart).
                        Logica van de tests blijft identiek; alleen de
                        assertie verandert van app.styleSheet() naar
                        window.styleSheet().
================================================================================
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from dataclasses import replace

from PySide6.QtWidgets import QApplication

import app.gui.main_window as main_window_module
from app.config.settings import AppInstellingen
from app.gui.main_window import ToolHubWindow
from app.gui.styles import DARK_THEME_STYLESHEET, LIGHT_THEME_STYLESHEET


def _app():
    return QApplication.instance() or QApplication([])


def _forceer_instellingen(monkeypatch, *, thema: str):
    """Laat laad_instellingen() een vast AppInstellingen teruggeven.

    Zo blijven de tests onafhankelijk van de settings.json in de
    projectroot en van eventuele eerdere tests.
    """
    basis = AppInstellingen()
    vast = replace(basis, algemeen=replace(basis.algemeen, thema=thema))
    monkeypatch.setattr(
        main_window_module, "laad_instellingen", lambda: vast
    )
    return vast


def _maak_window(
    monkeypatch,
    *,
    settings_thema: str = "dark",
    theme: str | None = None,
) -> ToolHubWindow:
    """Maakt een ToolHubWindow met vaste settings.

    Het opruimen gebeurt centraal door de autouse-fixture
    _ruim_qt_op() in conftest.py. Deze helper doet alleen de vaste
    settings-monkeypatch en de constructie.
    """
    _app()
    _forceer_instellingen(monkeypatch, thema=settings_thema)
    return ToolHubWindow(theme=theme, check_on_startup=False)


# ============================================================================
# Theme-parameter op ToolHubWindow
# ============================================================================

def test_theme_parameter_light_zet_lichte_stylesheet(monkeypatch):
    window = _maak_window(monkeypatch, settings_thema="dark", theme="light")
    assert window.styleSheet() == LIGHT_THEME_STYLESHEET
    assert window.theme == "light"


def test_theme_parameter_dark_zet_donkere_stylesheet(monkeypatch):
    window = _maak_window(monkeypatch, settings_thema="light", theme="dark")
    assert window.styleSheet() == DARK_THEME_STYLESHEET
    assert window.theme == "dark"


def test_theme_parameter_heeft_voorrang_op_settings_json(monkeypatch):
    """Analoog aan taal: de expliciete parameter wint."""
    window = _maak_window(monkeypatch, settings_thema="dark", theme="light")
    assert window.theme == "light"
    assert window.styleSheet() == LIGHT_THEME_STYLESHEET


def test_zonder_parameter_erft_window_thema_uit_settings(monkeypatch):
    window = _maak_window(monkeypatch, settings_thema="light", theme=None)
    assert window.theme == "light"


def test_ongeldige_theme_parameter_valt_terug_op_dark(monkeypatch):
    window = _maak_window(monkeypatch, settings_thema="light", theme="blauw")
    assert window.theme == "dark"


def test_ongeldig_thema_in_settings_valt_terug_op_dark(monkeypatch):
    window = _maak_window(monkeypatch, settings_thema="blauw", theme=None)
    assert window.theme == "dark"


# ============================================================================
# Live themawissel via _apply_settings
# ============================================================================

def test_apply_settings_wisselt_van_dark_naar_light(monkeypatch):
    window = _maak_window(monkeypatch, settings_thema="dark")
    assert window.theme == "dark"

    basis = AppInstellingen()
    nieuw = replace(basis, algemeen=replace(basis.algemeen, thema="light"))
    window._apply_settings(nieuw)

    assert window.theme == "light"
    assert window.styleSheet() == LIGHT_THEME_STYLESHEET


def test_apply_settings_wisselt_van_light_naar_dark(monkeypatch):
    window = _maak_window(monkeypatch, settings_thema="light")
    assert window.theme == "light"

    basis = AppInstellingen()
    nieuw = replace(basis, algemeen=replace(basis.algemeen, thema="dark"))
    window._apply_settings(nieuw)

    assert window.theme == "dark"
    assert window.styleSheet() == DARK_THEME_STYLESHEET


def test_apply_settings_met_ongeldig_thema_valt_terug_op_dark(monkeypatch):
    window = _maak_window(monkeypatch, settings_thema="light")
    assert window.theme == "light"

    basis = AppInstellingen()
    nieuw = replace(basis, algemeen=replace(basis.algemeen, thema="blauw"))
    window._apply_settings(nieuw)

    assert window.theme == "dark"
    assert window.styleSheet() == DARK_THEME_STYLESHEET


def test_apply_settings_zonder_thema_wijziging_laat_theme_ongewijzigd(monkeypatch):
    """Als het thema niet wijzigt, blijft de venster-stylesheet staan.

    Om de test onafhankelijk te maken van testvolgorde zetten we eerst
    expliciet de tegenovergestelde stylesheet op het venster. Daarna
    passen we _apply_settings toe met hetzelfde thema; de
    venster-stylesheet moet ongemoeid blijven.
    """
    window = _maak_window(monkeypatch, settings_thema="light")
    assert window.theme == "light"

    # Zet expliciet een andere stylesheet op het venster om te bewijzen
    # dat _apply_settings met ongewijzigd thema niets aanpast.
    window.setStyleSheet(DARK_THEME_STYLESHEET)

    basis = AppInstellingen()
    nieuw = replace(
        basis,
        algemeen=replace(basis.algemeen, thema="light"),
    )
    window._apply_settings(nieuw)

    assert window.theme == "light"
    assert window.styleSheet() == DARK_THEME_STYLESHEET