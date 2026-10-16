"""
================================================================================
Module:     tests/test_main_icon.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-16
Auteur:     Bart Bossuyt

Doel:       Regressietests voor het applicatie-icoon in main.py (fase 11C).
            We testen niet main() zelf (die roept sys.exit), maar wel dat
            de gebruikte helper een geldig QIcon teruggeeft en dat
            QApplication.setWindowIcon() het icoon aanvaardt.

Wijzigingen:
  v1.0.0 (2026-10-16)  Eerste versie.
================================================================================
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from app.helpers.icon_paths import applicatie_icoon


def _app():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def test_applicatie_icoon_is_geldig():
    app = _app()
    icoon = applicatie_icoon()
    assert icoon is not None
    assert not icoon.isNull()
    # Zet het op de QApplication; dit mag niet crashen.
    app.setWindowIcon(icoon)
    assert not app.windowIcon().isNull()