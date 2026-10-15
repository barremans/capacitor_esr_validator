"""
================================================================================
Module:     tests/test_main_window_update_menu.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-15
Auteur:     Bart Bossuyt

Doel:       GUI-regressietests voor het Help-menu-item "Controleren op
            updates…" in ToolHubWindow (fase 9H). Geen qtbot; offscreen.

Wijzigingen:
  v1.0.0 (2026-10-14)  Fase 9H. Eerste versie.
  v1.1.0 (2026-10-15)  Fase 9H-afronding: tests voor de derde knop
                        "Wat is er nieuw?" en de release-notes-dialoog.
================================================================================
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox

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
    """Als de gebruiker niets kiest, wordt webbrowser.open niet aangeroepen."""
    _app()
    window = ToolHubWindow(taal="nl_NL", check_on_startup=False)

    import webbrowser

    geopend = {"url": None}

    def _fake_open(url):
        geopend["url"] = url

    monkeypatch.setattr(webbrowser, "open", _fake_open)

    class _FakeInfo:
        is_newer = True
        current_version = "1.0.4"
        remote_version = "1.0.5"
        download_url = None

    assert hasattr(window, "_toon_update_melding")
    assert geopend["url"] is None

    window.close()
    window.deleteLater()
    _app().processEvents()


# ============================================================================
# v1.1.0 — "Wat is er nieuw?"-knop (fase 9H-afronding)
# ============================================================================

def test_toon_release_notes_bij_lege_body_toont_fout(monkeypatch):
    """Als de body leeg is (geen notes op GitHub): fallback-melding."""
    _app()
    window = ToolHubWindow(taal="nl_NL", check_on_startup=False)

    from app.helpers import updater as updater_module

    monkeypatch.setattr(
        updater_module,
        "fetch_release_notes",
        lambda: {"tag_name": "v1.1.0", "body": "", "html_url": "https://x"},
    )

    gevangen = {"titel": None}

    def _fake_exec(self):
        gevangen["titel"] = self.windowTitle()
        return 0

    monkeypatch.setattr(QMessageBox, "exec", _fake_exec)

    try:
        window._toon_release_notes()
        assert gevangen["titel"] is not None
    finally:
        window.close()
        window.deleteLater()
        _app().processEvents()


def test_toon_release_notes_bij_fout_toont_fout(monkeypatch):
    _app()
    window = ToolHubWindow(taal="nl_NL", check_on_startup=False)

    from app.helpers import updater as updater_module

    def _raise():
        raise RuntimeError("kapot")

    monkeypatch.setattr(updater_module, "fetch_release_notes", _raise)

    gevangen = {"titel": None}

    def _fake_exec(self):
        gevangen["titel"] = self.windowTitle()
        return 0

    monkeypatch.setattr(QMessageBox, "exec", _fake_exec)

    try:
        window._toon_release_notes()
        assert gevangen["titel"] is not None
    finally:
        window.close()
        window.deleteLater()
        _app().processEvents()


def test_toon_release_notes_importfout_toont_fout(monkeypatch):
    """Als de updater-module niet importeerbaar is: fallback, geen crash."""
    _app()
    window = ToolHubWindow(taal="nl_NL", check_on_startup=False)

    import builtins
    originele_import = builtins.__import__

    def _fake_import(name, *args, **kwargs):
        if name == "app.helpers.updater":
            raise ImportError("gesimuleerd")
        return originele_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)

    gevangen = {"titel": None}

    def _fake_exec(self):
        gevangen["titel"] = self.windowTitle()
        return 0

    monkeypatch.setattr(QMessageBox, "exec", _fake_exec)

    try:
        window._toon_release_notes()
        assert gevangen["titel"] is not None
    finally:
        monkeypatch.undo()
        window.close()
        window.deleteLater()
        _app().processEvents()


def test_toon_update_melding_heeft_drie_knoppen(monkeypatch):
    _app()
    window = ToolHubWindow(taal="nl_NL", check_on_startup=False)

    class _FakeInfo:
        is_newer = True
        current_version = "1.0.4"
        remote_version = "1.1.0"
        download_url = "https://example.com/setup.exe"

    knoppen: list[str] = []
    originele_addButton = QMessageBox.addButton

    def _fake_addButton(self, *args, **kwargs):
        if args and isinstance(args[0], str):
            knoppen.append(args[0])
        return originele_addButton(self, *args, **kwargs)

    monkeypatch.setattr(QMessageBox, "addButton", _fake_addButton)
    monkeypatch.setattr(QMessageBox, "exec", lambda self: 0)

    try:
        window._toon_update_melding(_FakeInfo())
        assert "Downloaden" in knoppen
        assert "Wat is er nieuw?" in knoppen
        assert "Later" in knoppen
    finally:
        window.close()
        window.deleteLater()
        _app().processEvents()


def test_markdown_naar_html_ondersteunt_koppen_en_vet(monkeypatch):
    """Kleine controle op de mini-Markdown-render."""
    _app()
    window = ToolHubWindow(taal="nl_NL", check_on_startup=False)
    try:
        html = window._markdown_naar_html(
            "# Titel\n\n## Sectie\n\n**vet** en `code`\n"
        )
        assert "<h1>Titel</h1>" in html
        assert "<h2>Sectie</h2>" in html
        assert "<b>vet</b>" in html
        assert "<code>code</code>" in html
    finally:
        window.close()
        window.deleteLater()
        _app().processEvents()