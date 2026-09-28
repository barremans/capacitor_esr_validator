"""
================================================================================
Module:     tests/test_navigation_regressions.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.0.0
Datum:      2026-09-27
Auteur:     Bart Bossuyt

Doel:       Regressietests voor Tool Hub -> Diagnose -> ESR navigatie.
================================================================================
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.gui.main_window import ToolHubWindow


def _app():
    return QApplication.instance() or QApplication([])


def test_start_op_hoofdmenu():
    _app()
    window = ToolHubWindow()
    assert window.stack.currentWidget() is window.hub_page


def test_hoofdmenu_naar_diagnose_naar_esr():
    _app()
    window = ToolHubWindow()

    window._show_diagnose()
    assert window.stack.currentWidget() is window.diagnose_page

    window._open_esr_test()
    assert window.stack.currentWidget() is window.esr_page


def test_esr_terug_gaat_naar_diagnose():
    _app()
    window = ToolHubWindow()
    window._open_esr_test()

    window.esr_page.back_requested.emit()

    assert window.stack.currentWidget() is window.diagnose_page
