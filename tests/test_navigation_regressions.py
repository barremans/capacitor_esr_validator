"""
================================================================================
Module:     tests/test_navigation_regressions.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.1.0
Datum:      2026-10-02
Auteur:     Bart Bossuyt

Doel:       Regressietests voor Tool Hub-navigatie naar Diagnose, ESR en
            Documentatie, inclusief contextueel Terug/X-gedrag.
Wijzigingen:
  v1.1.0 (2026-10-02)  Documentatienavigatie en contextueel X-gedrag toegevoegd.
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


def test_hoofdmenu_naar_documentatie_en_terug():
    _app()
    window = ToolHubWindow()

    window._show_documentation()
    assert window.stack.currentWidget() is window.documentation_page

    window.documentation_page.back_requested.emit()
    assert window.stack.currentWidget() is window.hub_page


class _FakeCloseEvent:
    def __init__(self):
        self.accepted = False
        self.ignored = False

    def accept(self):
        self.accepted = True

    def ignore(self):
        self.ignored = True


def test_x_vanuit_documentatie_gaat_naar_hoofdmenu_en_sluit_niet():
    _app()
    window = ToolHubWindow()
    window._show_documentation()
    event = _FakeCloseEvent()

    window.closeEvent(event)

    assert event.ignored is True
    assert event.accepted is False
    assert window.stack.currentWidget() is window.hub_page
