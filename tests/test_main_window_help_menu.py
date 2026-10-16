"""
================================================================================
Module:     tests/test_main_window_help_menu.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.3.0
Datum:      2026-10-16
Auteur:     Bart Bossuyt

Doel:       Regressietests voor het Help-menu in ToolHubWindow. Oorspronkelijk
            (Fase 4E.4) alleen voor "Documentatie zoeken…". Sinds fase 9H
            ook voor "Controleren op updates…". Sinds fase 11C ook voor
            het icoon op het Help-item.

Wijzigingen:
  v1.0.2 (2026-10-05)  Taalonafhankelijk gemaakt. De applicatie start met de
                       opgeslagen gebruikersinstelling (kan EN zijn). Tests
                       zoeken nu op positie i.p.v. op NL-tekst, en forceren
                       expliciet een taal waar de tekst zelf getest wordt.
  v1.0.1 (2026-10-05)  Robuuster zoeken op substring i.p.v. exacte match.
  v1.0.0 (2026-10-05)  Eerste versie.
  v1.1.0 (2026-10-14)  Fase 9H: Help-menu heeft nu 5 niet-lege items
                       (Help, Documentatie zoeken…, Changelog,
                       Controleren op updates…, Over). Structuurtests
                       aangepast; nieuwe tests voor het update-item.
                       window wordt in elke test met check_on_startup=False
                       gebouwd, zodat de opstartcheck niet interfereert.
  v1.2.0 (2026-10-14)  Fase 11C: Help-menu-items hebben nu een icoon.
  v1.3.0 (2026-10-16)  Fase 11C-fix: test_help_menu_action_heeft_icoon
                       gebruikt geen niet-bestaande _app-fixture meer.
                       De QApplication wordt lokaal in de test opgehaald
                       via QApplication.instance() or QApplication([]),
                       conform de projectafspraak (geen pytest-qt,
                       geen qtbot, geen conftest.py).
================================================================================
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
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


def _update_item(menu: QMenu) -> QAction:
    """Het 'Controleren op updates…'-item, ongeacht taal.

    Het staat tussen het Changelog-item en het Over-item, dus op
    positie 3 (0-based) van de niet-lege acties.
    """
    acties = _niet_lege_acties(menu)
    assert len(acties) >= 5, (
        f"Help-menu heeft onverwachte structuur: "
        f"{[a.text() for a in acties]}"
    )
    return acties[3]


def test_help_menu_bevat_documentatie_zoeken_item():
    _app()
    window = ToolHubWindow(check_on_startup=False)
    menu = _help_menu(window)

    acties = _niet_lege_acties(menu)
    teksten = [a.text() for a in acties]

    assert len(acties) == 5, (
        f"Verwacht 5 items (Help, Documentatie zoeken…, Changelog, "
        f"Controleren op updates…, About), kreeg: {teksten}"
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
    window = ToolHubWindow(check_on_startup=False)
    menu = _help_menu(window)
    action = _zoek_item(menu)

    assert action.shortcut().isEmpty(), (
        f"Onverwachte shortcut: {action.shortcut().toString()}"
    )


def test_documentatie_zoeken_staat_tussen_help_en_changelog():
    _app()
    window = ToolHubWindow(check_on_startup=False)
    menu = _help_menu(window)

    acties = _niet_lege_acties(menu)
    teksten = [a.text() for a in acties]

    # Structuur: [Help, Documentatie zoeken…, Changelog, Updates…, About]
    assert len(acties) == 5, f"Onverwachte structuur: {teksten}"

    def _bevat(tekst: str, *fragmenten: str) -> bool:
        laag = tekst.lower()
        return any(f.lower() in laag for f in fragmenten)

    assert _bevat(acties[0].text(), "help"), teksten
    assert _bevat(acties[1].text(), "documentation", "documentatie"), teksten
    assert _bevat(acties[2].text(), "changelog", "wijzigingslog"), teksten
    assert _bevat(acties[3].text(), "update"), teksten
    assert _bevat(acties[4].text(), "about", "over"), teksten


def test_trigger_opent_search_help_dialog(monkeypatch):
    _app()
    window = ToolHubWindow(check_on_startup=False)
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
    window = ToolHubWindow(check_on_startup=False)

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


# ============================================================================
# v1.1.0 — Help-menu-item "Controleren op updates…" (fase 9H)
# ============================================================================

def test_help_menu_bevat_update_item():
    _app()
    window = ToolHubWindow(check_on_startup=False)
    menu = _help_menu(window)

    item = _update_item(menu)
    tekst = item.text().lower()
    assert "update" in tekst, f"Onverwachte tekst: '{item.text()}'"


def test_update_item_staat_tussen_changelog_en_over():
    _app()
    window = ToolHubWindow(check_on_startup=False)
    menu = _help_menu(window)

    acties = _niet_lege_acties(menu)
    teksten = [a.text().lower() for a in acties]

    idx_changelog = next(
        i for i, t in enumerate(teksten)
        if "changelog" in t or "wijzigingslog" in t
    )
    idx_update = next(i for i, t in enumerate(teksten) if "update" in t)
    idx_over = next(
        i for i, t in enumerate(teksten)
        if "about" in t or "over" in t
    )
    assert idx_changelog < idx_update < idx_over, teksten


def test_update_item_heeft_geen_shortcut():
    _app()
    window = ToolHubWindow(check_on_startup=False)
    menu = _help_menu(window)
    action = _update_item(menu)

    assert action.shortcut().isEmpty(), (
        f"Onverwachte shortcut: {action.shortcut().toString()}"
    )


def test_update_item_vertaalt_mee():
    _app()
    window = ToolHubWindow(check_on_startup=False)

    window._set_language("nl_NL")
    menu_nl = _help_menu(window)
    assert "update" in _update_item(menu_nl).text().lower()

    window._set_language("en_US")
    menu_en = _help_menu(window)
    assert "update" in _update_item(menu_en).text().lower()


def test_trigger_update_item_roept_handmatige_check_aan(monkeypatch):
    _app()
    window = ToolHubWindow(check_on_startup=False)
    menu = _help_menu(window)
    action = _update_item(menu)

    aangeroepen = {"n": 0}

    def _fake_check():
        aangeroepen["n"] += 1

    monkeypatch.setattr(window, "_check_for_updates_manually", _fake_check)

    action.trigger()

    assert aangeroepen["n"] == 1


# ============================================================================
# v1.2.0 — Fase 11C: iconen in het Help-menu
# ============================================================================

def test_help_menu_action_heeft_icoon():
    """Het Help-menu-item heeft een icoon zodra assets/icons/help.png bestaat.

    Conform de projectafspraak gebruiken we geen _app-fixture en geen
    pytest-qt: we halen de QApplication lokaal op.
    """
    from app.helpers.icon_paths import icoon_pad

    if icoon_pad("help") is None:
        pytest.skip("Geen help.png aanwezig; plaats eerst placeholders.")

    app = _app()
    window = ToolHubWindow(taal="nl_NL", check_on_startup=False)
    try:
        app.processEvents()
        menu = _help_menu(window)
        acties = _niet_lege_acties(menu)
        assert acties, "Help-menu heeft geen acties"
        eerste = acties[0]
        assert not eerste.icon().isNull(), "Help-actie heeft geen icoon"
    finally:
        window.deleteLater()
        app.processEvents()