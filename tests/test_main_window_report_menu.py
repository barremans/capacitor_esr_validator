"""
================================================================================
Module:     tests/test_main_window_report_menu.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.4
Datum:      2026-10-10
Auteur:     Bart Bossuyt

Doel:       Regressietests voor het menu-item "Rapport maken…" (Fase 8C).

Wijzigingen:
  v1.0.0 (2026-10-10)  Eerste versie.
  v1.0.1 (2026-10-10)  Fix: _vind_actie gebruikte
                        type(window.menuBar().addMenu("x")) om QMenu te
                        vinden, maar dat voegde een dummy-menu toe en
                        verstoorde de menubar. Nu direct QMenu.
  v1.0.2 (2026-10-10)  Fix: _vind_actie gebruikt menubar.actions() in
                        plaats van findChildren(QMenu).
  v1.0.3 (2026-10-10)  Fix: ToolHubWindow.__init__ respecteert nu de
                        parameter taal (main_window v2.11.3).
  v1.0.4 (2026-10-10)  Fix: deleteLater() wordt niet verwerkt in tests
                        zonder event loop. Daardoor blijven oude QActions
                        in half-opgeruimde toestand hangen en geeft
                        .text() RuntimeError. Oplossing: roep
                        QApplication.processEvents() aan in de fixture
                        en na elke _apply_language(). Bovendien doet de
                        taalwissel-test geen _set_language meer (dat
                        schrijft naar settings.json); in plaats daarvan
                        wordt self.taal gezet en _apply_language()
                        aangeroepen.
================================================================================
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication

from app.gui.main_window import ToolHubWindow


@pytest.fixture(scope="module", autouse=True)
def qapplication():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def window():
    w = ToolHubWindow(taal="nl_NL")
    # v1.0.4: laat deleteLater() verwerken vóór we de menubar inspecteren.
    QApplication.processEvents()
    yield w
    w.close()
    QApplication.processEvents()


def _alle_menu_acties(window):
    """Geef alle levende QActions in de menubar.

    Verzamelt de tekst onmiddellijk, zodat we niet later op dode
    QAction-wrappers stuiten.
    """
    resultaat = []
    menubar = window.menuBar()
    for menu_actie in menubar.actions():
        try:
            menu = menu_actie.menu()
        except RuntimeError:
            continue
        if menu is None:
            continue
        for actie in menu.actions():
            try:
                tekst = actie.text()
            except RuntimeError:
                continue
            resultaat.append((tekst, actie))
    return resultaat


def _vind_actie(window, tekst: str):
    """Zoek een QAction met de gegeven tekst in de menubar."""
    for act_tekst, actie in _alle_menu_acties(window):
        if act_tekst == tekst:
            return actie
    return None


def _beschikbare_teksten(window):
    return [tekst for tekst, _ in _alle_menu_acties(window)]


def test_menu_dump_bij_fout(window):
    """Diagnostische test: bevestigt dat er menu-acties bestaan."""
    teksten = _beschikbare_teksten(window)
    assert len(teksten) > 0, "Geen enkele menu-actie gevonden in de menubar."


def test_menu_item_rapport_bestaat(window):
    actie = _vind_actie(window, "Rapport maken…")
    assert actie is not None, (
        "Menu-item 'Rapport maken…' niet gevonden. "
        f"Beschikbare items: {_beschikbare_teksten(window)}"
    )


def test_menu_item_rapport_heeft_sneltoets(window):
    actie = _vind_actie(window, "Rapport maken…")
    assert actie is not None, (
        "Menu-item 'Rapport maken…' niet gevonden. "
        f"Beschikbare items: {_beschikbare_teksten(window)}"
    )
    assert actie.shortcut() == QKeySequence("Ctrl+P")


def test_menu_item_rapport_vertaalt_mee_naar_engels(window):
    # v1.0.4: geen _set_language meer (dat schrijft settings.json).
    # In plaats daarvan zetten we self.taal en roepen we _apply_language()
    # rechtstreeks aan.
    window.taal = "en_US"
    window._apply_language()
    QApplication.processEvents()

    actie = _vind_actie(window, "Create report…")
    assert actie is not None, (
        "Menu-item 'Create report…' niet gevonden na taalwissel. "
        f"Beschikbare items: {_beschikbare_teksten(window)}"
    )