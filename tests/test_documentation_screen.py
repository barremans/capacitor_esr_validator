"""
================================================================================
Module:     tests/test_documentation_screen.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.4.0
Datum:      2026-10-03
Auteur:     Bart Bossuyt

Doel:       GUI-regressietests voor de read-only Documentatiebibliotheek.

Wijzigingen:
  v1.0.0 (2026-10-02)  Eerste schermtests voor lege toestand, filters en taalwissel.
  v1.1.0 (2026-10-02)  Openknop/selectie en read-only documentdialoog getest.
  v1.2.0 (2026-10-03)  Vertaalbare documenttitels en live taalwissel getest.
  v1.3.0 (2026-10-03)  Openen van interne Markdown geeft de actieve taal door
                        aan de documentatieservice.
  v1.4.0 (2026-10-03)  Viewer-UX, selectiebehoud en vertaalde sluitknop getest.
================================================================================
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

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
    def __init__(self):
        self.last_read_language = None

    def get_document(self, document_id):
        return self.list_documents()[0]

    def read_document_text(self, document_id, *, language=None):
        self.last_read_language = language
        return "# FM Series\nRead-only guide."

    def list_documents(self, *, search_text=None, category=None, tool_key=None):
        document = DocumentMetadata(
            document_id="doc-1",
            title="FM Series",
            title_key="documentatie.document_titels.fm_series",
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
    titles = {
        ("nl_NL", "documentatie.document_titels.fm_series"): "FM-serie",
        ("en_US", "documentatie.document_titels.fm_series"): "FM Series",
        ("nl_NL", "documentatie.sluiten"): "Sluiten",
        ("en_US", "documentatie.sluiten"): "Close",
    }
    value = titles.get((taal, key), f"{taal}:{key}")
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


def test_refresh_preserves_selected_document_when_still_visible():
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )
    screen.table.selectRow(0)

    screen.refresh()

    assert screen._selected_document_id() == "doc-1"
    assert screen.open_btn.isEnabled() is True


def test_language_switch_preserves_search_filter_and_selection(monkeypatch):
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
    screen.table.selectRow(0)

    screen.apply_language("en_US")

    assert screen.title_label.text() == "en_US:documentatie.titel"
    assert screen.back_btn.text() == "en_US:knop.terug"
    assert screen.search_edit.text() == "Panasonic"
    assert screen.category_combo.currentData() == "DATASHEET"
    assert screen.tool_combo.currentData() == "ESR_CAPACITOR"
    assert screen._selected_document_id() == "doc-1"


def test_open_button_follows_row_selection():
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )

    assert screen.open_btn.isEnabled() is False
    screen.table.selectRow(0)
    assert screen.open_btn.isEnabled() is True


def test_open_selected_document_uses_read_only_dialog(monkeypatch):
    _app()
    service = _FakeDocumentationService()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=service,
    )
    screen.table.selectRow(0)

    executed = {"count": 0}
    dialog_state = {}

    def _fake_exec(self):
        executed["count"] += 1
        dialog_state["buttons"] = [
            button.text() for button in self.findChildren(QPushButton)
        ]
        return 0

    from PySide6.QtWidgets import QDialog
    monkeypatch.setattr(QDialog, "exec", _fake_exec)

    screen._open_selected_document()

    assert executed["count"] == 1
    assert service.last_read_language == "nl_NL"
    assert "Sluiten" in dialog_state["buttons"]


def test_document_title_changes_live_with_language(monkeypatch):
    _app()
    monkeypatch.setattr(documentation_module, "vertaal", _fake_translate)

    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )

    assert screen.table.item(0, 0).text() == "FM-serie"

    screen.apply_language("en_US")

    assert screen.table.item(0, 0).text() == "FM Series"


def test_document_title_falls_back_to_official_title_when_key_missing(monkeypatch):
    _app()
    monkeypatch.setattr(
        documentation_module,
        "vertaal",
        lambda key, taal="nl_NL", **kwargs: key,
    )

    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )

    assert screen.table.item(0, 0).text() == "FM Series"
