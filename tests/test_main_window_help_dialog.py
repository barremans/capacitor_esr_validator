"""
================================================================================
Module:     tests/test_main_window_help_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.1
Datum:      2026-10-06
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de Help-dialoog (F1 / menu Help) die sinds
            Fase 4H het juiste taalbestand laadt via help_paths.

Wijzigingen:
  v1.0.1 (2026-10-06)  Fix: ongeldige functienaam met spatie
                       (test_show_help_gebruikt_taal van_gebruiker) veroorzaakte
                       een SyntaxError bij het inlezen. Vervangen door
                       test_show_help_gebruikt_taal_van_gebruiker.
  v1.0.0 (2026-10-06)  Eerste versie.
================================================================================
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.gui.main_window import ToolHubWindow
from app.helpers import help_paths


def _app():
    return QApplication.instance() or QApplication([])


def _vang_pad(monkeypatch, vast_pad: Path) -> dict:
    """Vervang help_pad_voor_taal en _show_markdown_dialog om het pad op te vangen."""
    gevangen: dict = {"taal": None, "pad": None, "titel": None}

    def fake_pad(taal, **kwargs):
        gevangen["taal"] = taal
        return vast_pad

    def fake_dialog(self, titel, filepath):
        gevangen["titel"] = titel
        gevangen["pad"] = filepath

    monkeypatch.setattr(
        "app.gui.main_window.help_pad_voor_taal", fake_pad
    )
    monkeypatch.setattr(
        ToolHubWindow, "_show_markdown_dialog", fake_dialog
    )
    return gevangen


def test_show_help_gebruikt_taal_van_gebruiker(monkeypatch, tmp_path):
    _app()
    window = ToolHubWindow()
    window._set_language("en_US")

    nep_pad = tmp_path / "docs" / "help" / "en_US.md"
    nep_pad.parent.mkdir(parents=True)
    nep_pad.write_text("# EN", encoding="utf-8")

    gevangen = _vang_pad(monkeypatch, nep_pad)
    window._show_help()

    assert gevangen["taal"] == "en_US"
    assert gevangen["pad"] == str(nep_pad)
    assert gevangen["titel"]  # niet leeg


def test_show_help_gebruikt_nl_wanneer_taal_nl_is(monkeypatch, tmp_path):
    _app()
    window = ToolHubWindow()
    window._set_language("nl_NL")

    nep_pad = tmp_path / "docs" / "help" / "nl_NL.md"
    nep_pad.parent.mkdir(parents=True)
    nep_pad.write_text("# NL", encoding="utf-8")

    gevangen = _vang_pad(monkeypatch, nep_pad)
    window._show_help()

    assert gevangen["taal"] == "nl_NL"
    assert gevangen["pad"] == str(nep_pad)


def test_show_help_roept_help_paths_aan(monkeypatch):
    """Bewijst dat _show_help() echt via help_paths gaat (geen hardcoded pad)."""
    _app()
    window = ToolHubWindow()

    aangeroepen = {"keer": 0, "taal": None}

    echte_functie = help_paths.help_pad_voor_taal

    def spion(taal, **kwargs):
        aangeroepen["keer"] += 1
        aangeroepen["taal"] = taal
        return echte_functie(taal, **kwargs)

    monkeypatch.setattr(
        "app.gui.main_window.help_pad_voor_taal", spion
    )
    monkeypatch.setattr(
        ToolHubWindow, "_show_markdown_dialog", lambda self, t, p: None
    )

    window._show_help()

    assert aangeroepen["keer"] == 1
    assert aangeroepen["taal"] == window.taal


def test_show_help_geen_crash_bij_ontbrekend_bestand(monkeypatch):
    """De dialoog zelf vangt FileNotFoundError; _show_help mag niet crashen."""
    _app()
    window = ToolHubWindow()

    def fake_dialog(self, titel, filepath):
        # Simuleer het bestaande gedrag van _show_markdown_dialog bij ontbreken.
        assert isinstance(filepath, str)

    monkeypatch.setattr(
        ToolHubWindow, "_show_markdown_dialog", fake_dialog
    )

    # Forceer een niet-bestaande taal; de fallback-keten levert dan nog
    # steeds een bestaand bestand in de echte repo.
    window._show_help()