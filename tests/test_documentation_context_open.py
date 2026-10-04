"""
================================================================================
Module:     tests/test_documentation_context_open.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-03
Auteur:     Bart Bossuyt

Doel:       Regressietest voor rechtstreeks openen op document-ID.
================================================================================
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDialog

from app.documentation.models import (
    DocumentCategory,
    DocumentMetadata,
    DocumentSourceType,
)
from app.gui.documentation_screen import DocumentationScreen


def _app():
    return QApplication.instance() or QApplication([])


class _Service:
    def __init__(self):
        self.requested_language = None

    def list_documents(self, *, search_text=None, category=None, tool_key=None):
        return []

    def get_document(self, document_id):
        assert document_id == "esr-safe-discharge"
        return DocumentMetadata(
            document_id=document_id,
            title="Condensator veilig ontladen vóór meting",
            title_key="documentatie.document_titels.esr_safe_discharge",
            category=DocumentCategory.SAFETY,
            source_type=DocumentSourceType.FILE,
            source_path="internal/nl_NL/capacitor_safe_discharge.md",
            source_url=None,
            tool_key="ESR_CAPACITOR",
            manufacturer=None,
            series=None,
            part_number=None,
            document_version="1.0",
            document_date="2026-10-02",
            notes=None,
        )

    def read_document_text(self, document_id, *, language=None):
        self.requested_language = language
        return "# Veilig ontladen"


def test_open_document_by_id_uses_active_language(monkeypatch):
    _app()
    service = _Service()
    screen = DocumentationScreen(
        taal="en_US",
        documentation_service=service,
    )

    monkeypatch.setattr(QDialog, "exec", lambda self: 0)

    assert screen.open_document_by_id("esr-safe-discharge") is True
    assert service.requested_language == "en_US"
