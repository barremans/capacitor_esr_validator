"""
================================================================================
Module:     tests/test_documentation_screen.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-02
Auteur:     Bart Bossuyt

Doel:       GUI-regressietests voor de read-only Documentatiebibliotheek.

Wijzigingen:
  v1.0.0 (2026-10-02)  Eerste schermtests voor lege toestand, filters en taalwissel.
================================================================================
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import app.gui.documentation_screen as documentation_module
from app.documentation.models import (
    DocumentCategory,
    DocumentMetadata,
    DocumentSourceType,
)
from app.gui.documentation_screen import DocumentationScreen


def _app():
    return QApplication.instance() or QApplication([])


class _FakeDocumentationService:
    def list_documents(self, *, search_text=None, category=None, tool_key=None):
        document = DocumentMetadata(
            document_id="doc-1",
            title="FM Series",
            category=DocumentCategory.DATASHEET,
            source_type=DocumentSourceType.FILE,
            source_path="docs/fm.pdf",
            source_url=None,
            tool_key="ESR_CAPACITOR",
            manufacturer="Panasonic",
            series="FM",
            part_number=None,
            document_version="3",
            document_date=None,
            notes=None,
        )
        if category and category != "DATASHEET":
            return []
        if tool_key and tool_key != "ESR_CAPACITOR":
            return []
        if search_text and search_text.casefold() not in "fm series panasonic".casefold():
            return []
        return [document]


class _EmptyDocumentationService:
    def list_documents(self, *, search_text=None, category=None, tool_key=None):
        return []


def _fake_translate(key: str, taal: str = "nl_NL", **kwargs) -> str:
    value = f"{taal}:{key}"
    if kwargs:
        value += ":" + ",".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
    return value


def test_empty_library_is_safe():
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_EmptyDocumentationService(),
    )

    assert screen.table.rowCount() == 0
    assert screen.status_label.text() == "Geen documenten gevonden."


def test_filters_refresh_read_only_table():
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )

    assert screen.table.rowCount() == 1
    screen.search_edit.setText("not-found")
    assert screen.table.rowCount() == 0
    screen.search_edit.setText("Panasonic")
    assert screen.table.rowCount() == 1


def test_language_switch_preserves_search_and_filter_values(monkeypatch):
    _app()
    monkeypatch.setattr(documentation_module, "vertaal", _fake_translate)

    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )
    screen.search_edit.setText("Panasonic")
    category_index = screen.category_combo.findData("DATASHEET")
    tool_index = screen.tool_combo.findData("ESR_CAPACITOR")
    screen.category_combo.setCurrentIndex(category_index)
    screen.tool_combo.setCurrentIndex(tool_index)

    screen.apply_language("en_US")

    assert screen.title_label.text() == "en_US:documentatie.titel"
    assert screen.back_btn.text() == "en_US:knop.terug"
    assert screen.search_edit.text() == "Panasonic"
    assert screen.category_combo.currentData() == "DATASHEET"
    assert screen.tool_combo.currentData() == "ESR_CAPACITOR"
