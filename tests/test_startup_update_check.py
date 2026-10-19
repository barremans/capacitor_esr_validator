"""
================================================================================
Module:     tests/test_startup_update_check.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-16
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de niet-blokkerende opstartcheck in
            ToolHubWindow (fase 9H). Geen qtbot; offscreen.

            Sinds v1.1.0 (fase 11E.1) gebruikt de GUI de async variant
            _do_update_check_async(on_result). De tests monkeypatchen
            die methode en roepen de callback zelf aan, zodat de
            GUI-logica deterministisch getest wordt zonder echte
            threads. De bestaande synchrone _do_update_check blijft
            bestaan en wordt apart getest in
            test_main_window_update_menu.py.

Wijzigingen:
  v1.0.0 (2026-10-14)  Fase 9H. Eerste versie.
  v1.1.0 (2026-10-16)  Fase 11E.1: tests gebruiken de async variant
                        _do_update_check_async(on_result).
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

    def _fake_async(on_result):
        on_result(_FakeInfo())

    monkeypatch.setattr(window, "_do_update_check_async", _fake_async)

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

    def _fake_async(on_result):
        on_result(_FakeInfo())

    monkeypatch.setattr(window, "_do_update_check_async", _fake_async)

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

    def _fake_async(on_result):
        on_result(None)

    monkeypatch.setattr(window, "_do_update_check_async", _fake_async)

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