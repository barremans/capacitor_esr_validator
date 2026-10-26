"""
================================================================================
Module:     tests/test_main_window_import_menu.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.1
Datum:      2026-10-26
Auteur:     Bart Bossuyt

Doel:       GUI-regressietests voor het Bestand-menu-item "Document
            importeren…" en de koppeling naar ImportWizardDialog.
            Bewaakt de typfout-fix uit chat 3A (masterplan A2):
            _show_import_wizard() mag geen AttributeError meer geven
            en moet de dialoog daadwerkelijk openen.

Wijzigingen:
  v1.0.0 (2026-10-26)  Eerste versie.
  v1.0.1 (2026-10-26)  Fix: test_import_requested_signaal_is_gekoppeld
                       monkeypatchte eerst _show_import_wizard op het
                       venster. Dat werkt niet: de signaalverbinding
                       wijst naar de originele bound method, niet naar
                       het instantie-attribuut. De test monkeypatcht nu
                       alleen ImportWizardDialog, zodat de originele
                       _show_import_wizard draait en de fake dialoog
                       aanmaakt. Geen productiecodewijziging.
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


def _vind_menu_actie(window, tekst):
    """Zoek een QAction met exact deze tekst in de hele menubalk."""
    for menu_actie in window.menuBar().actions():
        try:
            menu = menu_actie.menu()
        except RuntimeError:
            continue
        if menu is None:
            continue
        for actie in menu.actions():
            try:
                if actie.text() == tekst:
                    return actie
            except RuntimeError:
                continue
    return None


# ---------------------------------------------------------------- menu-item

def test_import_menu_item_bestaat(window):
    assert _vind_menu_actie(window, "Document importeren…") is not None


def test_import_menu_item_heeft_sneltoets(window):
    actie = _vind_menu_actie(window, "Document importeren…")
    assert actie is not None
    assert actie.shortcut() == QKeySequence("Ctrl+I")


# ---------------------------------------------------------------- fix 3A

def test_show_import_wizard_opent_dialoog(monkeypatch):
    """Bewijst de typfout-fix: _show_import_wizard() opent de dialoog.

    Vóór de fix gaf de aanroep self._zet_dialoog_icono(dialog) een
    AttributeError, waardoor dialog.exec() nooit werd bereikt. Deze
    test monkeypatcht ImportWizardDialog naar een fake met een
    exec()-teller en controleert dat exec() precies één keer wordt
    aangeroepen.
    """
    app = QApplication.instance() or QApplication([])
    window = ToolHubWindow(taal="nl_NL", check_on_startup=False)
    try:
        geopend = {"exec_count": 0, "taal": None, "parent": None}

        class _FakeSignal:
            def connect(self, *args, **kwargs):
                pass

        class _FakeWizard:
            def __init__(self, *, taal, parent):
                geopend["taal"] = taal
                geopend["parent"] = parent
                self.import_completed = _FakeSignal()

            def exec(self):
                geopend["exec_count"] += 1
                return 0

        import app.gui.dialogs.import_wizard_dialog as wizard_mod
        monkeypatch.setattr(wizard_mod, "ImportWizardDialog", _FakeWizard)

        window._show_import_wizard()

        assert geopend["exec_count"] == 1
        assert geopend["taal"] == "nl_NL"
        assert geopend["parent"] is window
    finally:
        window.close()
        app.processEvents()


def test_import_requested_signaal_is_gekoppeld(monkeypatch):
    """DocumentationScreen.import_requested moet de wizard openen.

    We bewijzen de koppeling door het signaal te laten vuren en de
    ImportWizardDialog te monkeypatchen. De originele
    _show_import_wizard draait, doet zijn lokale import, en krijgt
    zo de fake dialoog. Zo blijft de bestaande signaalverbinding
    intact.
    """
    app = QApplication.instance() or QApplication([])
    window = ToolHubWindow(taal="nl_NL", check_on_startup=False)
    try:
        import app.gui.dialogs.import_wizard_dialog as wizard_mod

        geopend = {"exec_count": 0}

        class _FakeSignal:
            def connect(self, *args, **kwargs):
                pass

        class _FakeWizard:
            def __init__(self, *, taal, parent):
                self.import_completed = _FakeSignal()

            def exec(self):
                geopend["exec_count"] += 1
                return 0

        monkeypatch.setattr(wizard_mod, "ImportWizardDialog", _FakeWizard)

        window.documentation_page.import_requested.emit()

        assert geopend["exec_count"] == 1
    finally:
        window.close()
        app.processEvents()