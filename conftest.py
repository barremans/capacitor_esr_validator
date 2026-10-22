"""
================================================================================
Module:     conftest.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-21
Auteur:     Bart Bossuyt

Doel:       Minimale, projectbrede pytest-configuratie voor GUI-tests.
            - Zet QT_QPA_PLATFORM=offscreen vóór PySide6 geïmporteerd
              wordt, zodat elke GUI-test zonder scherm kan draaien.
            - Ruimt na elke test alle widgets op via deleteLater() +
              processEvents(). Zonder deze opruiming groeit de globale
              widget-stapel aan en wordt elke widget-aanmaak in een
              volgende test trager.

Wijzigingen:
  v1.0.0 (2026-10-21)  Eerste versie. Vervangt de afspraak "er is geen
                        conftest.py" uit overdracht.md §1: een minimale
                        conftest.py met een autouse-opruimfixture is
                        toegestaan en verplicht voor GUI-tests. Geen
                        qtbot, geen pytest-qt, geen projectimports.
                        Gebruikte topLevelWidgets() en één
                        processEvents()-ronde.
  v1.1.0 (2026-10-21)  Robuuster: allWidgets() in plaats van
                        topLevelWidgets(), drie processEvents()-rondes
                        in plaats van één. topLevelWidgets() sloeg
                        widgets met een parent over; die bleven in de
                        stapel staan tot hun top-level parent werd
                        opgeruimd. allWidgets() pakt alles, en drie
                        rondes zorgen dat de delete-queue leeg is.
                        Nog steeds geen projectimports, geen qtbot.
================================================================================
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(autouse=True)
def _ruim_qt_op():
    """Ruimt na elke test alle widgets op.

    De fixture is autouse, dus elke test (ook pure tests zonder Qt)
    krijgt hem. Voor pure tests is QApplication.instance() None en
    doet de fixture niets. Voor GUI-tests ruimt hij alle widgets op,
    ook de kinderen, zodat een volgende test niet hoeft te betalen
    voor de widgets van de vorige.
    """
    yield
    app = QApplication.instance()
    if app is None:
        return
    for widget in app.allWidgets():
        widget.deleteLater()
    for _ in range(3):
        app.processEvents()