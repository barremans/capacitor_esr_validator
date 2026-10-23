"""
================================================================================
Module:     tests/test_main_window_exchange_menu.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-23
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de twee Bestand-menu-items van §2.28F:
            "Exporteren naar toestel…" en "Importeren van toestel…".

Wijzigingen:
  v1.0.0 (2026-10-23)  Eerste versie.
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
    w = ToolHubWindow(taal="nl_NL", check_on_startup=False)
    QApplication.processEvents()
    yield w
    w.close()
    QApplication.processEvents()


def _alle_menu_acties(window):
    resultaat = []
    for menu_actie in window.menuBar().actions():
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


def _vind(window, tekst):
    for act_tekst, actie in _alle_menu_acties(window):
        if act_tekst == tekst:
            return actie
    return None


def test_export_menu_item_bestaat(window):
    assert _vind(window, "Exporteren naar toestel…") is not None


def test_export_menu_item_heeft_sneltoets(window):
    actie = _vind(window, "Exporteren naar toestel…")
    assert actie is not None
    assert actie.shortcut() == QKeySequence("Ctrl+Shift+E")


def test_import_menu_item_bestaat(window):
    assert _vind(window, "Importeren van toestel…") is not None


def test_import_menu_item_heeft_sneltoets(window):
    actie = _vind(window, "Importeren van toestel…")
    assert actie is not None
    assert actie.shortcut() == QKeySequence("Ctrl+Shift+I")


def test_menu_items_vertalen_naar_engels(window):
    window.taal = "en_US"
    window._apply_language()
    QApplication.processEvents()
    assert _vind(window, "Export to device…") is not None
    assert _vind(window, "Import from device…") is not None