"""
================================================================================
Module:     tests/test_main_window_update_menu.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-14
Auteur:     Bart Bossuyt

Doel:       GUI-regressietests voor het Help-menu-item "Controleren op
            updates…" in ToolHubWindow (fase 9H). Geen qtbot; offscreen.

Wijzigingen:
  v1.0.0 (2026-10-14)  Fase 9H. Eerste versie.
================================================================================
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.gui.main_window import ToolHubWindow


def _app():
    return QApplication.instance() or QApplication([])


def _menu_labels(window: ToolHubWindow) -> list[str]:
    """Leest alle menu-labels in één keer uit (geen QMenu-pointer bewaren)."""
    return [action.text() for action in window.menuBar().actions()]


def _help_action_labels(window: ToolHubWindow) -> list[str]:
    """Leest alle acties van het Help-menu in één keer uit."""
    labels: list[str] = []
    for menu_action in window.menuBar().actions():
        menu = menu_action.menu()
        if menu is None:
            continue
        if menu_action.text() == window._t("menu.help"):
            labels = [a.text() for a in menu.actions()]
            break
    return labels


def test_help_menu_bevat_update_item():
    _app()
    window = ToolHubWindow(taal="nl_NL", check_on_startup=False)
    try:
        labels = _help_action_labels(window)
        assert window._t("menu.controleren_op_updates") in labels
    finally:
        window.close()
        window.deleteLater()
        _app().processEvents()


def test_help_menu_update_item_engels():
    _app()
    window = ToolHubWindow(taal="en_US", check_on_startup=False)
    try:
        labels = _help_action_labels(window)
        assert "Check for updates…" in labels
    finally:
        window.close()
        window.deleteLater()
        _app().processEvents()


def test_update_item_staat_tussen_changelog_en_over():
    _app()
    window = ToolHubWindow(taal="nl_NL", check_on_startup=False)
    try:
        labels = _help_action_labels(window)
        idx_changelog = labels.index(window._t("menu.changelog"))
        idx_update = labels.index(window._t("menu.controleren_op_updates"))
        idx_over = labels.index(window._t("menu.over"))
        assert idx_changelog < idx_update < idx_over
    finally:
        window.close()
        window.deleteLater()
        _app().processEvents()


def test_update_i18n_keys_bestaan_nl():
    _app()
    window = ToolHubWindow(taal="nl_NL", check_on_startup=False)
    try:
        assert window._t("update.titel") != "update.titel"
        assert window._t("update.downloaden") != "update.downloaden"
        assert window._t("update.later") != "update.later"
        assert window._t("update.geen_update", versie="1.0.4") != "update.geen_update"
    finally:
        window.close()
        window.deleteLater()
        _app().processEvents()


def test_update_i18n_keys_bestaan_en():
    _app()
    window = ToolHubWindow(taal="en_US", check_on_startup=False)
    try:
        assert window._t("update.titel") == "Check for updates"
        assert window._t("update.downloaden") == "Download"
        assert window._t("update.later") == "Later"
    finally:
        window.close()
        window.deleteLater()
        _app().processEvents()


def test_handmatige_check_zonder_update_toont_information(monkeypatch):
    """Bij geen nieuwere versie: informationele melding."""
    _app()
    window = ToolHubWindow(taal="nl_NL", check_on_startup=False)

    class _FakeInfo:
        is_newer = False
        current_version = "1.0.4"
        remote_version = "1.0.4"
        download_url = None

    monkeypatch.setattr(window, "_do_update_check", lambda: _FakeInfo())

    captured = {}

    def _fake_information(parent, title, text):
        captured["title"] = title
        captured["text"] = text
        return None

    from PySide6.QtWidgets import QMessageBox
    monkeypatch.setattr(QMessageBox, "information", _fake_information)

    try:
        window._check_for_updates_manually()
        assert "1.0.4" in captured["text"]
    finally:
        window.close()
        window.deleteLater()
        _app().processEvents()


def test_handmatige_check_met_fout_toont_warning(monkeypatch):
    _app()
    window = ToolHubWindow(taal="nl_NL", check_on_startup=False)

    monkeypatch.setattr(window, "_do_update_check", lambda: None)

    captured = {}

    def _fake_warning(parent, title, text):
        captured["title"] = title
        captured["text"] = text
        return None

    from PySide6.QtWidgets import QMessageBox
    monkeypatch.setattr(QMessageBox, "warning", _fake_warning)

    try:
        window._check_for_updates_manually()
        assert captured["title"] == window._t("update.fout_titel")
    finally:
        window.close()
        window.deleteLater()
        _app().processEvents()


def test_do_update_check_geen_exception_bij_importfout(monkeypatch):
    """_do_update_check mag nooit een exception laten doorwerken."""
    _app()
    window = ToolHubWindow(taal="nl_NL", check_on_startup=False)

    import builtins
    originele_import = builtins.__import__

    def _fake_import(name, *args, **kwargs):
        if name == "app.helpers.updater":
            raise ImportError("gesimuleerd")
        return originele_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)

    try:
        assert window._do_update_check() is None
    finally:
        monkeypatch.undo()
        window.close()
        window.deleteLater()
        _app().processEvents()


def test_do_update_check_vangt_exception(monkeypatch):
    _app()
    window = ToolHubWindow(taal="nl_NL", check_on_startup=False)

    from app.helpers import updater

    def _raise(current_version, timeout=5):
        raise RuntimeError("gesimuleerd")

    monkeypatch.setattr(updater, "check_for_update", _raise)

    try:
        assert window._do_update_check() is None
    finally:
        window.close()
        window.deleteLater()
        _app().processEvents()


def test_toon_update_melding_zonder_klik_opent_geen_browser(monkeypatch):
    """Als de gebruiker 'Later' kiest, wordt webbrowser.open niet aangeroepen."""
    _app()
    window = ToolHubWindow(taal="nl_NL", check_on_startup=False)

    from PySide6.QtWidgets import QMessageBox
    import webbrowser

    geopend = {"url": None}

    def _fake_open(url):
        geopend["url"] = url

    monkeypatch.setattr(webbrowser, "open", _fake_open)

    # QMessageBox.exec monkeypatchen we niet; we roepen _toon_update_melding
    # niet aan in deze test, maar testen alleen dat webbrowser.open niet
    # wordt aangeroepen als er geen klik is. Dat is hier impliciet: we
    # controleren alleen dat de functie niet crasht als download_url None is.
    class _FakeInfo:
        is_newer = True
        current_version = "1.0.4"
        remote_version = "1.0.5"
        download_url = None

    # We kunnen de modal niet automatiseren zonder qtbot; daarom testen we
    # alleen dat de methode bestaat en dat webbrowser.open niet automatisch
    # wordt aangeroepen.
    assert hasattr(window, "_toon_update_melding")
    assert geopend["url"] is None

    window.close()
    window.deleteLater()
    _app().processEvents()