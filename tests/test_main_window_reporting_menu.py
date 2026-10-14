"""
================================================================================
Module:     tests/test_main_window_reporting_menu.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.1
Datum:      2026-10-14
Auteur:     Bart Bossuyt

Doel:       GUI-regressietests voor het "Rapporteren"-menu in
            ToolHubWindow (Fase 9G, main_window.py v2.12.0).

            Dit is een ANDER menu dan het "Rapport maken…"-item uit
            Fase 8C (dat in test_main_window_report_menu.py wordt
            getest). Het "Rapporteren"-menu heeft twee acties:
              - "🐞 Bug of feature melden…" (opent BugDialog)
              - "Open cases tonen" (roept show_github_cases aan)

            Geen pytest-qt, geen qtbot. Gebruikt de QApplication-fixture
            en QApplication.processEvents() voor deleteLater().

            BELANGRIJK: _apply_language() ruimt de menu's op met
            menubar.clear() + deleteLater(). Een QMenu-pointer die je
            vóór die opruiming hebt opgehaald, is daarna dood. Daarom
            halen alle helpers in één keer de tekst op en bewaren nooit
            een QMenu-object tussen twee processEvents()-rondes.

Wijzigingen:
  v1.0.1 (2026-10-14)  Fix: RuntimeError "Internal C++ object (QMenu)
                       already deleted". Oorzaak: _vind_top_menu gaf
                       een QMenu-pointer terug, en _actie_labels gebruikte
                       die pointer na een tweede processEvents(). Tussen
                       beide rondes ruimde _apply_language() het menu op.
                       Oplossing: alle helpers lezen de menu-inhoud
                       onmiddellijk uit en geven strings terug, nooit
                       QMenu-objecten die bewaard worden.
  v1.0.0 (2026-10-14)  Eerste versie. Fase 9G.
================================================================================
"""

from __future__ import annotations

import json
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.gui.main_window import ToolHubWindow


@pytest.fixture(scope="module", autouse=True)
def qapplication():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def window():
    w = ToolHubWindow(taal="nl_NL")
    QApplication.processEvents()
    yield w
    w.close()
    QApplication.processEvents()


# --------------------------------------------------------------------- helpers
#
# Alle helpers hieronder lezen de menubar in één keer uit. Ze bewaren
# NOOIT een QMenu- of QAction-pointer, want die kan door deleteLater()
# ongeldig worden zodra er opnieuw processEvents() loopt.
#
def _menu_labels_voor(window, menu_titel):
    """Geef de lijst met labels van alle acties onder één top-level menu.

    Geeft None terug als het menu niet bestaat. Leest alles in één keer
    uit — geen QMenu-pointer die de caller kan hergebruiken.
    """
    QApplication.processEvents()
    menubar = window.menuBar()
    for menu_actie in menubar.actions():
        try:
            menu = menu_actie.menu()
        except RuntimeError:
            continue
        if menu is None:
            continue
        try:
            titel = menu.title()
        except RuntimeError:
            continue
        if titel != menu_titel:
            continue
        labels = []
        for actie in menu.actions():
            try:
                tekst = actie.text()
            except RuntimeError:
                continue
            if tekst:
                labels.append(tekst)
        return labels
    return None


def _top_menu_titels(window):
    """Geef de titels van alle top-level menu's, in volgorde."""
    QApplication.processEvents()
    titels = []
    menubar = window.menuBar()
    for menu_actie in menubar.actions():
        try:
            menu = menu_actie.menu()
        except RuntimeError:
            continue
        if menu is None:
            continue
        try:
            titels.append(menu.title())
        except RuntimeError:
            continue
    return titels


# --------------------------------------------------------------------- tests
def test_rapporteren_menu_bestaat_in_nl(window):
    titels = _top_menu_titels(window)
    assert "Rapporteren" in titels, (
        f"Top-level menu 'Rapporteren' niet gevonden. Beschikbare: {titels}"
    )


def test_rapporteren_menu_heeft_twee_acties(window):
    labels = _menu_labels_voor(window, "Rapporteren")
    assert labels is not None, "Menu 'Rapporteren' niet gevonden."
    assert len(labels) == 2, f"Verwacht 2 acties, gevonden: {labels}"


def test_rapporteren_menu_labels_nl(window):
    labels = _menu_labels_voor(window, "Rapporteren")
    assert labels is not None, "Menu 'Rapporteren' niet gevonden."
    assert "🐞 Bug of feature melden…" in labels
    assert "Open cases tonen" in labels


def test_rapporteren_menu_positie_tussen_diagnose_en_instellingen(window):
    titels = _top_menu_titels(window)
    assert "Diagnose" in titels
    assert "Rapporteren" in titels
    assert "Instellingen" in titels
    assert titels.index("Diagnose") < titels.index("Rapporteren")
    assert titels.index("Rapporteren") < titels.index("Instellingen")


def test_rapporteren_menu_labels_na_taalwissel_naar_engels(window):
    # Geen _set_language (dat schrijft naar settings.json), maar
    # window.taal + _apply_language() — zelfde aanpak als in het
    # bestaande test_main_window_report_menu.py v1.0.4.
    window.taal = "en_US"
    window._apply_language()
    QApplication.processEvents()

    labels = _menu_labels_voor(window, "Report")
    assert labels is not None, (
        f"Top-level menu 'Report' niet gevonden. Beschikbare: "
        f"{_top_menu_titels(window)}"
    )
    assert "🐞 Report a bug or feature…" in labels
    assert "Show open cases" in labels


def test_bug_report_actie_roept_bug_dialog_aan(window, monkeypatch):
    """De methode _show_bug_report_dialog() moet BugDialog aanroepen."""
    aangeroepen = {"count": 0, "parent": None}

    import bug_report_dialog

    class NepBugDialog:
        def __init__(self, parent=None, initial_type=None, initial_description=""):
            aangeroepen["count"] += 1
            aangeroepen["parent"] = parent

        def exec(self):
            return 0

    monkeypatch.setattr(bug_report_dialog, "BugDialog", NepBugDialog)

    window._show_bug_report_dialog()
    assert aangeroepen["count"] == 1
    assert aangeroepen["parent"] is window


def test_open_cases_actie_roept_show_github_cases_aan(window, monkeypatch):
    """De methode _show_open_cases() moet show_github_cases aanroepen."""
    aangeroepen = {"count": 0, "parent": None}

    import github_cases

    def nep_show(parent):
        aangeroepen["count"] += 1
        aangeroepen["parent"] = parent

    monkeypatch.setattr(github_cases, "show_github_cases", nep_show)

    window._show_open_cases()
    assert aangeroepen["count"] == 1
    assert aangeroepen["parent"] is window


def test_rapporteren_menu_blijft_na_meerdere_taalwissels(window):
    """NL → EN → NL: menu moet telkens correct opnieuw opgebouwd worden."""
    window.taal = "en_US"
    window._apply_language()
    QApplication.processEvents()
    window.taal = "nl_NL"
    window._apply_language()
    QApplication.processEvents()

    labels = _menu_labels_voor(window, "Rapporteren")
    assert labels is not None, (
        f"Menu 'Rapporteren' niet gevonden na taalwissels. Beschikbare: "
        f"{_top_menu_titels(window)}"
    )
    assert "🐞 Bug of feature melden…" in labels
    assert "Open cases tonen" in labels


def test_i18n_keys_bestaan_in_beide_talen():
    """Pure data-check: de drie nieuwe keys staan in beide app.json."""
    nl = json.load(open(os.path.join(PROJECT_ROOT, "i18n", "locales", "nl_NL", "app.json"),
                        encoding="utf-8"))
    en = json.load(open(os.path.join(PROJECT_ROOT, "i18n", "locales", "en_US", "app.json"),
                        encoding="utf-8"))
    for key in ("rapporteren", "bug_melden", "open_cases"):
        assert key in nl["menu"], f"NL mist menu.{key}"
        assert key in en["menu"], f"EN mist menu.{key}"


def test_i18n_keys_hebben_verwachte_waarden():
    """Bewaakt de exacte NL/EN waarden van de drie nieuwe keys."""
    nl = json.load(open(os.path.join(PROJECT_ROOT, "i18n", "locales", "nl_NL", "app.json"),
                        encoding="utf-8"))
    en = json.load(open(os.path.join(PROJECT_ROOT, "i18n", "locales", "en_US", "app.json"),
                        encoding="utf-8"))

    assert nl["menu"]["rapporteren"] == "Rapporteren"
    assert en["menu"]["rapporteren"] == "Report"
    assert nl["menu"]["bug_melden"] == "🐞 Bug of feature melden…"
    assert en["menu"]["bug_melden"] == "🐞 Report a bug or feature…"
    assert nl["menu"]["open_cases"] == "Open cases tonen"
    assert en["menu"]["open_cases"] == "Show open cases"