"""
================================================================================
Module:     tests/test_documentation_screen.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.8.0
Datum:      2026-10-05
Auteur:     Bart Bossuyt

Doel:       GUI-regressietests voor de read-only Documentatiebibliotheek.

Wijzigingen:
  v1.0.0 (2026-10-02)  Eerste schermtests voor lege toestand, filters en taalwissel.
  v1.1.0 (2026-10-02)  Openknop/selectie en read-only documentdialoog getest.
  v1.2.0 (2026-10-03)  Vertaalbare documenttitels en live taalwissel getest.
  v1.3.0 (2026-10-03)  Openen van interne Markdown geeft de actieve taal door
                        aan de documentatieservice.
  v1.4.0 (2026-10-03)  Viewer-UX, selectiebehoud en vertaalde sluitknop getest.
  v1.5.0 (2026-10-03)  Documentinformatie, provenance en bron-URL's getest.
  v1.6.0 (2026-10-03)  Compact provenance-overzicht zonder supports-tags getest.
  v1.7.0 (2026-10-03)  Hoogtebegrenzing van het informatiepaneel vastgelegd.
  v1.8.0 (2026-10-05)  Help-knop, tooltips en lokale sneltoetsen getest.
================================================================================
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication, QPushButton

import app.gui.documentation_screen as documentation_module
from app.documentation.models import (
    DocumentCategory,
    DocumentMetadata,
    DocumentProvenanceRef,
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
            source_url="https://example.com/fm",
            tool_key="ESR_CAPACITOR",
            manufacturer="Panasonic",
            series="FM",
            part_number="EEU-FM1E471",
            document_version="3",
            document_date="2026-10-03",
            notes="Testnotitie",
            provenance=(
                DocumentProvenanceRef(
                    source_id="src-1",
                    source_title="Official FM datasheet",
                    source_kind="URL",
                    source_path=None,
                    source_url="https://example.com/source",
                    locator="Table 4",
                    supports=("esr", "capacitance"),
                    note="Official source",
                ),
            ),
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
        ("nl_NL", "documentatie.info.documentinformatie"): "Documentinformatie",
        ("nl_NL", "documentatie.info.broninformatie"): "Broninformatie",
        ("nl_NL", "documentatie.info.categorie"): "Categorie",
        ("nl_NL", "documentatie.info.fabrikant"): "Fabrikant",
        ("nl_NL", "documentatie.info.serie"): "Serie",
        ("nl_NL", "documentatie.info.partnummer"): "Partnummer",
        ("nl_NL", "documentatie.info.versie"): "Versie",
        ("nl_NL", "documentatie.info.datum"): "Datum",
        ("nl_NL", "documentatie.info.notities"): "Notities",
        ("nl_NL", "documentatie.info.bron_url"): "Bron-URL",
        ("nl_NL", "documentatie.info.locator"): "Locatie in bron",
        ("nl_NL", "documentatie.info.ondersteunt"): "Ondersteunt",
        ("nl_NL", "documentatie.info.bron_notitie"): "Bronnotitie",
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


def test_document_information_html_contains_metadata_provenance_and_urls(monkeypatch):
    _app()
    monkeypatch.setattr(documentation_module, "vertaal", _fake_translate)

    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )
    document = screen.documentation_service.get_document("doc-1")

    info_html = screen._document_information_html(document)

    assert "Documentinformatie" in info_html
    assert "Panasonic" in info_html
    assert "EEU-FM1E471" in info_html
    assert "2026-10-03" in info_html
    assert "Testnotitie" in info_html
    assert "Broninformatie" in info_html
    assert "Official FM datasheet" in info_html
    assert "Table 4" in info_html
    assert "esr, capacitance" not in info_html
    assert "https://example.com/fm" in info_html
    assert "https://example.com/source" in info_html

    info_browser = screen._create_document_information_browser(document)
    assert info_browser.minimumHeight() == 140
    assert info_browser.maximumHeight() == 200


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


# ---------------------------------------------------------------------------
# Sneltoetsen en help-knop (v1.8.0)
# ---------------------------------------------------------------------------


def _find_shortcuts_for_key(screen: DocumentationScreen, key_sequence: str):
    """Zoek alle QShortcut-instanties van een scherm op gegeven toetsen."""
    from PySide6.QtGui import QShortcut

    target = QKeySequence(key_sequence)
    matches = []
    for child in screen.findChildren(QShortcut):
        if child.key() == target:
            matches.append(child)
    return matches


def test_escape_shortcut_is_installed_with_widget_context():
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )

    shortcuts = _find_shortcuts_for_key(screen, "Esc")
    assert len(shortcuts) == 1
    assert shortcuts[0].context() == Qt.ShortcutContext.WidgetWithChildrenShortcut


def test_f1_shortcut_is_installed_with_widget_context():
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )

    shortcuts = _find_shortcuts_for_key(screen, "F1")
    assert len(shortcuts) == 1
    assert shortcuts[0].context() == Qt.ShortcutContext.WidgetWithChildrenShortcut


def test_return_shortcut_is_installed_with_widget_context():
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )

    shortcuts = _find_shortcuts_for_key(screen, "Return")
    assert len(shortcuts) == 1
    assert shortcuts[0].context() == Qt.ShortcutContext.WidgetWithChildrenShortcut


def test_ctrl_f_shortcut_is_installed_with_widget_context():
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )

    shortcuts = _find_shortcuts_for_key(screen, "Ctrl+F")
    assert len(shortcuts) == 1
    assert shortcuts[0].context() == Qt.ShortcutContext.WidgetWithChildrenShortcut


def test_ctrl_l_shortcut_is_installed_with_widget_context():
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )

    shortcuts = _find_shortcuts_for_key(screen, "Ctrl+L")
    assert len(shortcuts) == 1
    assert shortcuts[0].context() == Qt.ShortcutContext.WidgetWithChildrenShortcut


def test_ctrl_o_shortcut_is_installed_with_widget_context():
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )

    shortcuts = _find_shortcuts_for_key(screen, "Ctrl+O")
    assert len(shortcuts) == 1
    assert shortcuts[0].context() == Qt.ShortcutContext.WidgetWithChildrenShortcut


def test_help_button_exists_with_question_mark():
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )
    assert screen.help_btn.text() == "?"


def test_search_edit_has_tooltip_from_i18n():
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )
    assert screen.search_edit.toolTip().startswith("Zoek in documenten.")


def test_help_button_has_tooltip_from_i18n():
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )
    assert "Zoektaal" in screen.help_btn.toolTip()


def test_open_search_help_dialog_uses_search_help_dialog(monkeypatch):
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )

    called = {"count": 0}

    def _fake_exec(self):
        called["count"] += 1
        return 0

    from app.gui.dialogs.search_help_dialog import SearchHelpDialog
    from PySide6.QtWidgets import QDialog
    monkeypatch.setattr(QDialog, "exec", _fake_exec)

    screen._open_search_help_dialog()

    assert called["count"] == 1