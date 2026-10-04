"""
================================================================================
Module:     tests/test_main_window_context_documentation.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.1
Datum:      2026-10-03
Auteur:     Bart Bossuyt

Doel:       Kleine regressietest voor ESR -> centrale documentviewer-koppeling.

Wijzigingen:
  v1.0.0 (2026-10-03)  Eerste regressietest.
  v1.0.1 (2026-10-03)  Test gebruikt een eenvoudige dummy in plaats van
                        object.__new__ op QMainWindow-subklasse.
================================================================================
"""

from types import SimpleNamespace

from app.gui.main_window import ToolHubWindow


def test_context_documentation_forwards_document_id():
    class _DocumentationPage:
        def __init__(self):
            self.ids = []

        def open_document_by_id(self, document_id):
            self.ids.append(document_id)

    window = SimpleNamespace(documentation_page=_DocumentationPage())

    ToolHubWindow._open_context_documentation(window, "esr-lcr-meter")

    assert window.documentation_page.ids == ["esr-lcr-meter"]
