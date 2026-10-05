"""
================================================================================
Module:     tests/test_search_help_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-05
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de read-only help-dialoog van de zoektaal.

            Bewijst dat:
              - de dialoog zonder fout opent
              - de i18n-keys correct geresolved worden (NL en EN)
              - alle help-secties in de HTML terechtkomen
              - de sluitknop de vertaalde tekst toont
              - taalwissel live doorwerkt
              - de dialoog read-only is

Wijzigingen:
  v1.0.0 (2026-10-05)  Eerste versie.
================================================================================
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.gui.dialogs.search_help_dialog import SearchHelpDialog


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_dialog_opens_without_error():
    _app()
    dialog = SearchHelpDialog(taal="nl_NL")
    assert dialog is not None
    assert dialog.isModal() is True


def test_dialog_title_comes_from_i18n_nl():
    _app()
    dialog = SearchHelpDialog(taal="nl_NL")
    assert dialog.windowTitle() == "Documenten zoeken"


def test_dialog_title_comes_from_i18n_en():
    _app()
    dialog = SearchHelpDialog(taal="en_US")
    assert dialog.windowTitle() == "Search documents"


def test_close_button_uses_i18n_text_nl():
    _app()
    dialog = SearchHelpDialog(taal="nl_NL")
    assert dialog.close_btn.text() == "Sluiten"


def test_close_button_uses_i18n_text_en():
    _app()
    dialog = SearchHelpDialog(taal="en_US")
    assert dialog.close_btn.text() == "Close"


def test_html_contains_all_sections_nl():
    _app()
    dialog = SearchHelpDialog(taal="nl_NL")
    html = dialog.browser.toHtml()

    # Kopjes uit de i18n-keys
    assert "Documenten zoeken" in html
    assert "Basiszoekopdracht" in html
    assert "Operatoren" in html
    assert "Voorbeelden" in html
    assert "Tips" in html
    assert "Verschil met filters" in html


def test_html_contains_all_sections_en():
    _app()
    dialog = SearchHelpDialog(taal="en_US")
    html = dialog.browser.toHtml()

    assert "Search documents" in html
    assert "Basic search" in html
    assert "Operators" in html
    assert "Examples" in html
    assert "Tips" in html
    assert "Difference with filters" in html


def test_html_contains_operator_examples():
    _app()
    dialog = SearchHelpDialog(taal="nl_NL")
    html = dialog.browser.toHtml()

    # Belangrijke operatoren moeten in de uitleg staan
    assert "wildcard" in html.lower()
    assert "exact" in html.lower()
    assert "uitsluiten" in html.lower() or "exclude" in html.lower()


def test_html_contains_operators_table_content():
    _app()
    dialog = SearchHelpDialog(taal="nl_NL")
    html = dialog.browser.toHtml()

    # De operator-tabel bevat de specifieke tekens
    for teken in ("spatie", "|", "-", "!", "%"):
        assert teken in html, f"operator '{teken}' ontbreekt"


def test_language_switch_updates_content_live():
    _app()
    dialog = SearchHelpDialog(taal="nl_NL")
    assert dialog.windowTitle() == "Documenten zoeken"
    assert dialog.close_btn.text() == "Sluiten"

    dialog.apply_language("en_US")

    assert dialog.windowTitle() == "Search documents"
    assert dialog.close_btn.text() == "Close"
    html = dialog.browser.toHtml()
    assert "Search documents" in html
    assert "Basic search" in html


def test_browser_is_read_only():
    _app()
    dialog = SearchHelpDialog(taal="nl_NL")
    assert dialog.browser.isReadOnly() is True


def test_close_button_accepts_dialog(monkeypatch):
    _app()
    dialog = SearchHelpDialog(taal="nl_NL")

    accepted = {"called": False}

    def _fake_accept(self):
        accepted["called"] = True

    monkeypatch.setattr(SearchHelpDialog, "accept", _fake_accept)
    dialog.close_btn.click()

    assert accepted["called"] is True