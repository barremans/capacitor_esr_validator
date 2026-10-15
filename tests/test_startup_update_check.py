"""
================================================================================
Module:     tests/test_startup_update_check.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-14
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de niet-blokkerende opstartcheck in
            ToolHubWindow (fase 9H). Geen qtbot; offscreen.

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


def test_check_on_startup_false_plant_geen_check(monkeypatch):
    """Met check_on_startup=False mag er geen QTimer gepland worden."""
    _app()

    from PySide6.QtCore import QTimer
    originele_single_shot = QTimer.singleShot
    aangeroepen = {"n": 0}

    def _fake_single_shot(ms, func):
        aangeroepen["n"] += 1
        return originele_single_shot(ms, func)

    monkeypatch.setattr(QTimer, "singleShot", staticmethod(_fake_single_shot))

    window = ToolHubWindow(taal="nl_NL", check_on_startup=False)
    try:
        assert aangeroepen["n"] == 0
    finally:
        window.close()
        window.deleteLater()
        _app().processEvents()


def test_check_on_startup_true_plant_check(monkeypatch):
    """Met check_on_startup=True moet er minstens één singleShot gepland zijn."""
    _app()

    from PySide6.QtCore import QTimer
    originele_single_shot = QTimer.singleShot
    aangeroepen = {"n": 0}

    def _fake_single_shot(ms, func):
        aangeroepen["n"] += 1
        return originele_single_shot(ms, func)

    monkeypatch.setattr(QTimer, "singleShot", staticmethod(_fake_single_shot))

    window = ToolHubWindow(taal="nl_NL", check_on_startup=True)
    try:
        assert aangeroepen["n"] >= 1
    finally:
        window.close()
        window.deleteLater()
        _app().processEvents()


def test_run_startup_update_check_geen_melding_bij_geen_update(monkeypatch):
    """Bij geen nieuwere versie: geen melding, geen crash."""
    _app()
    window = ToolHubWindow(taal="nl_NL", check_on_startup=False)

    class _FakeInfo:
        is_newer = False
        current_version = "1.0.4"
        remote_version = "1.0.4"
        download_url = None

    monkeypatch.setattr(window, "_do_update_check", lambda: _FakeInfo())

    from PySide6.QtWidgets import QMessageBox
    gemeld = {"n": 0}

    def _fake_toon(info):
        gemeld["n"] += 1

    monkeypatch.setattr(window, "_toon_update_melding", _fake_toon)
    monkeypatch.setattr(
        QMessageBox, "information",
        lambda *a, **k: gemeld.__setitem__("n", gemeld["n"] + 1),
    )

    try:
        window._run_startup_update_check()
        assert gemeld["n"] == 0
    finally:
        window.close()
        window.deleteLater()
        _app().processEvents()


def test_run_startup_update_check_melding_bij_update(monkeypatch):
    """Bij een nieuwere versie: precies één melding."""
    _app()
    window = ToolHubWindow(taal="nl_NL", check_on_startup=False)

    class _FakeInfo:
        is_newer = True
        current_version = "1.0.4"
        remote_version = "1.0.5"
        download_url = "https://example.com/setup.exe"

    monkeypatch.setattr(window, "_do_update_check", lambda: _FakeInfo())

    gemeld = {"n": 0}

    def _fake_toon(info):
        gemeld["n"] += 1
        assert info.is_newer is True

    monkeypatch.setattr(window, "_toon_update_melding", _fake_toon)

    try:
        window._run_startup_update_check()
        assert gemeld["n"] == 1
    finally:
        window.close()
        window.deleteLater()
        _app().processEvents()


def test_run_startup_update_check_fout_geen_melding(monkeypatch):
    """Bij een fout (None): geen melding, geen crash."""
    _app()
    window = ToolHubWindow(taal="nl_NL", check_on_startup=False)

    monkeypatch.setattr(window, "_do_update_check", lambda: None)

    gemeld = {"n": 0}

    def _fake_toon(info):
        gemeld["n"] += 1

    monkeypatch.setattr(window, "_toon_update_melding", _fake_toon)

    try:
        window._run_startup_update_check()
        assert gemeld["n"] == 0
    finally:
        window.close()
        window.deleteLater()
        _app().processEvents()