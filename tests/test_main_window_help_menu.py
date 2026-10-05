"""
================================================================================
Module:     tests/test_main_window_help_menu.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.2
Datum:      2026-10-05
Auteur:     Bart Bossuyt

Doel:       Regressietests voor het Help-menu-item "Documentatie zoeken…"
            (Fase 4E.4). Controleert aanwezigheid, positie, i18n-tekst,
            afwezigheid van shortcut en dialooggedrag.

Wijzigingen:
  v1.0.2 (2026-10-05)  Taalonafhankelijk gemaakt. De applicatie start met de
                       opgeslagen gebruikersinstelling (kan EN zijn). Tests
                       zoeken nu op positie i.p.v. op NL-tekst, en forceren
                       expliciet een taal waar de tekst zelf getest wordt.
  v1.0.1 (2026-10-05)  Robuuster zoeken op substring i.p.v. exacte match.
  v1.0.0 (2026-10-05)  Eerste versie.
================================================================================
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu

from app.gui.main_window import ToolHubWindow


def _app():
    return QApplication.instance() or QApplication([])


def _help_menu(window: ToolHubWindow) -> QMenu:
    """Vind het Help-menu in de menubalk (NL of EN).

    De titel is in beide talen 'Help', dus we matchen case-insensitive.
    """
    for menu in window.menuBar().findChildren(QMenu):
        if menu.title().strip().lower() == "help":
            return menu
    raise AssertionError("Help-menu niet gevonden")


def _niet_lege_acties(menu: QMenu) -> list[QAction]:
    """Alle acties behalve separators en lege labels, in menu-volgorde."""
    return [
        a for a in menu.actions()
        if not a.isSeparator() and a.text().strip()
    ]


def _zoek_item(menu: QMenu) -> QAction:
    """Het 'Documentatie zoeken…'-item, ongeacht taal.

    Strategie: het staat tussen het Help-item (F1) en het Changelog-item.
    We identificeren het als de tweede actie in het Help-menu.
    """
    acties = _niet_lege_acties(menu)
    assert len(acties) >= 3, (
        f"Help-menu heeft onverwachte structuur: "
        f"{[a.text() for a in acties]}"
    )
    return acties[1]


def test_help_menu_bevat_documentatie_zoeken_item():
    _app()
    window = ToolHubWindow()
    menu = _help_menu(window)

    acties = _niet_lege_acties(menu)
    teksten = [a.text() for a in acties]

    assert len(acties) == 4, (
        f"Verwacht 4 items (Help, Documentatie zoeken…, Changelog, About), "
        f"kreeg: {teksten}"
    )

    # Het tweede item is het nieuwe zoek-help-item. De tekst eindigt op een
    # ellipsis-teken (… of ...), wat we tolerant checken.
    tweede = acties[1].text().rstrip(".… ").lower()
    assert "documentation" in tweede or "documentatie" in tweede, (
        f"Tweede Help-menu-item is onverwacht: '{acties[1].text()}' "
        f"(volledige lijst: {teksten})"
    )


def test_documentatie_zoeken_item_heeft_geen_shortcut():
    _app()
    window = ToolHubWindow()
    menu = _help_menu(window)
    action = _zoek_item(menu)

    assert action.shortcut().isEmpty(), (
        f"Onverwachte shortcut: {action.shortcut().toString()}"
    )


def test_documentatie_zoeken_staat_tussen_help_en_changelog():
    _app()
    window = ToolHubWindow()
    menu = _help_menu(window)

    acties = _niet_lege_acties(menu)
    teksten = [a.text() for a in acties]

    # Structuur: [Help, Documentatie zoeken…, Changelog, About]
    assert len(acties) == 4, f"Onverwachte structuur: {teksten}"

    def _bevat(tekst: str, *fragmenten: str) -> bool:
        laag = tekst.lower()
        return any(f.lower() in laag for f in fragmenten)

    assert _bevat(acties[0].text(), "help"), teksten
    assert _bevat(acties[1].text(), "documentation", "documentatie"), teksten
    assert _bevat(acties[2].text(), "changelog", "wijzigingslog"), teksten
    assert _bevat(acties[3].text(), "about", "over"), teksten


def test_trigger_opent_search_help_dialog(monkeypatch):
    _app()
    window = ToolHubWindow()
    menu = _help_menu(window)
    action = _zoek_item(menu)

    geopend = {"aantal": 0, "taal": None, "parent": None}

    from app.gui import main_window as mw

    class _FakeDialog:
        def __init__(self, taal="nl_NL", parent=None):
            geopend["aantal"] += 1
            geopend["taal"] = taal
            geopend["parent"] = parent

        def exec(self):
            return 0

    monkeypatch.setattr(mw, "SearchHelpDialog", _FakeDialog)

    action.trigger()

    assert geopend["aantal"] == 1
    assert geopend["taal"] == window.taal
    assert geopend["parent"] is window


def test_documentatie_zoeken_item_vertaalt_mee():
    """Forceer expliciet beide talen, ongeacht de opgeslagen gebruikersinstelling."""
    _app()
    window = ToolHubWindow()

    # Forceer NL
    window._set_language("nl_NL")
    menu_nl = _help_menu(window)
    item_nl = _zoek_item(menu_nl)
    assert "documentatie" in item_nl.text().lower(), (
        f"NL-tekst onverwacht: '{item_nl.text()}'"
    )

    # Forceer EN
    window._set_language("en_US")
    menu_en = _help_menu(window)
    item_en = _zoek_item(menu_en)
    assert "documentation" in item_en.text().lower(), (
        f"EN-tekst onverwacht: '{item_en.text()}'"
    )