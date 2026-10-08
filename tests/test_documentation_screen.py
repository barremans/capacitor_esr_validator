"""
================================================================================
Module:     tests/test_documentation_screen.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.11.0
Datum:      2026-10-08
Auteur:     Bart Bossuyt

Doel:       GUI-regressietests voor de read-only Documentatiebibliotheek.

Wijzigingen:
  v1.0.0 (2026-10-02)  Eerste schermtests.
  v1.1.0 (2026-10-02)  Openknop/selectie en read-only documentdialoog.
  v1.2.0 (2026-10-03)  Vertaalbare documenttitels.
  v1.3.0 (2026-10-03)  Openen van Markdown geeft taal door.
  v1.4.0 (2026-10-03)  Viewer-UX, selectiebehoud, sluitknop.
  v1.5.0 (2026-10-03)  Documentinformatie, provenance, bron-URL's.
  v1.6.0 (2026-10-03)  Compact provenance-overzicht.
  v1.7.0 (2026-10-03)  Hoogtebegrenzing van informatiepaneel.
  v1.8.0 (2026-10-05)  Help-knop, tooltips en lokale sneltoetsen.
  v1.9.0 (2026-10-07)  Fase 5D'.4: dispatch-tests voor source_kind.
  v1.9.1 (2026-10-07)  URL-bron opent altijd de live URL in de browser.
  v1.9.2 (2026-10-07)  Dubbele test verwijderd.
  v1.10.0 (2026-10-07) Fase 5D'.2c: Bewerken-knop-tests.
  v1.10.1 (2026-10-07) Fix: test_edit_selected_document_opent_editor
                       gebruikt nu een QObject-subclass met klasse-niveau
                       Signal(str) en een eigen exec() die de teller
                       ophoogt. Geen monkeypatch meer op QDialog.exec.
  v1.11.0 (2026-10-08) Fase 5D'.2e: tests voor Status wijzigen-knop,
                       Toon gearchiveerde-checkbox en Status-kolom.
                       Bestaande kolomindices aangepast (fabrikant van
                       kolom 2 → 3, enz.).
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

    def list_documents(
        self,
        *,
        search_text=None,
        category=None,
        tool_key=None,
        include_archived=False,
    ):
        document = DocumentMetadata(
            document_id="doc-1",
            title="FM Series",
            title_key="documentatie.document_titels.fm_series",
            category=DocumentCategory.DATASHEET,
            source_type=DocumentSourceType.FILE,
            source_path="docs/fm.md",
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
    def list_documents(
        self,
        *,
        search_text=None,
        category=None,
        tool_key=None,
        include_archived=False,
    ):
        return []


class _PdfDocumentationService:
    """Levert een geïmporteerd PDF-document."""

    def get_document(self, document_id):
        return DocumentMetadata(
            document_id="doc-pdf",
            title="Geïmporteerde PDF",
            title_key=None,
            category=DocumentCategory.DATASHEET,
            source_type=DocumentSourceType.FILE,
            source_path="sources/doc-pdf.pdf",
            source_url=None,
            tool_key=None,
            manufacturer=None,
            series=None,
            part_number=None,
            document_version=None,
            document_date=None,
            notes=None,
        )

    def list_documents(
        self,
        *,
        search_text=None,
        category=None,
        tool_key=None,
        include_archived=False,
    ):
        return [self.get_document("doc-pdf")]

    def read_document_text(self, document_id, *, language=None):
        raise AssertionError(
            "PDF mag niet via read_document_text gelezen worden."
        )


class _UrlDocumentationService:
    """Levert een geïmporteerde URL-bron."""

    def get_document(self, document_id):
        return DocumentMetadata(
            document_id="doc-url",
            title="Geïmporteerde URL",
            title_key=None,
            category=DocumentCategory.DATASHEET,
            source_type=DocumentSourceType.URL,
            source_path=None,
            source_url="https://example.com/bron",
            tool_key=None,
            manufacturer=None,
            series=None,
            part_number=None,
            document_version=None,
            document_date=None,
            notes=None,
        )

    def list_documents(
        self,
        *,
        search_text=None,
        category=None,
        tool_key=None,
        include_archived=False,
    ):
        return [self.get_document("doc-url")]


class _UserImportDocumentationService:
    """Levert één importeerbare PDF-bron (is_user_import=True)."""

    def __init__(self, *, import_status: str = "concept"):
        self._import_status = import_status

    def get_document(self, document_id):
        return DocumentMetadata(
            document_id="import-1",
            title="Eigen import",
            title_key=None,
            category=DocumentCategory.DATASHEET,
            source_type=DocumentSourceType.FILE,
            source_path="sources/import-1.pdf",
            source_url=None,
            tool_key=None,
            manufacturer="CHONG",
            series="CDX",
            part_number=None,
            document_version="V1.1",
            document_date="2026-10-08",
            notes=None,
            is_user_import=True,
            import_status=self._import_status,
        )

    def list_documents(
        self,
        *,
        search_text=None,
        category=None,
        tool_key=None,
        include_archived=False,
    ):
        if (
            self._import_status == "gearchiveerd"
            and not include_archived
        ):
            return []
        return [self.get_document("import-1")]


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


# ============================================================================
# Basis
# ============================================================================

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


# ============================================================================
# Sneltoetsen en help-knop
# ============================================================================

def _find_shortcuts_for_key(screen: DocumentationScreen, key_sequence: str):
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

    from PySide6.QtWidgets import QDialog
    monkeypatch.setattr(QDialog, "exec", _fake_exec)

    screen._open_search_help_dialog()

    assert called["count"] == 1


# ============================================================================
# v1.9.0 — dispatch op basis van source_kind
# ============================================================================

def test_pdf_document_wordt_extern_geopend(tmp_path, monkeypatch):
    """PDF moet via QDesktopServices geopend worden, niet via de interne viewer."""
    _app()
    sources_root = tmp_path / "sources"
    sources_root.mkdir()
    (sources_root / "doc-pdf.pdf").write_bytes(b"%PDF-1.4 fake")

    monkeypatch.setattr(
        documentation_module, "default_sources_dir", lambda: sources_root
    )

    geopend = {"pad": None}

    def _fake_open(url):
        geopend["pad"] = url.toLocalFile() or url.toString()
        return True

    monkeypatch.setattr(
        documentation_module.QDesktopServices, "openUrl", _fake_open
    )

    from PySide6.QtWidgets import QDialog
    monkeypatch.setattr(
        QDialog, "exec", lambda self: (_ for _ in ()).throw(
            AssertionError("Interne viewer mag niet voor PDF geopend worden.")
        )
    )

    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_PdfDocumentationService(),
    )

    result = screen.open_document_by_id("doc-pdf")

    assert result is True
    assert geopend["pad"] is not None
    assert geopend["pad"].endswith("doc-pdf.pdf")


def test_pdf_zonder_lokaal_bestand_geeft_statusmelding(tmp_path, monkeypatch):
    """Als het PDF-bestand ontbreekt, tonen we een statusmelding."""
    _app()
    sources_root = tmp_path / "sources"
    sources_root.mkdir()  # leeg

    monkeypatch.setattr(
        documentation_module, "default_sources_dir", lambda: sources_root
    )

    geopend = {"count": 0}
    monkeypatch.setattr(
        documentation_module.QDesktopServices,
        "openUrl",
        lambda url: geopend.__setitem__("count", geopend["count"] + 1) or True,
    )

    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_PdfDocumentationService(),
    )

    result = screen.open_document_by_id("doc-pdf")

    assert result is False
    assert geopend["count"] == 0
    assert "kon niet" in screen.status_label.text().lower()


def test_url_document_opent_altijd_live_url(tmp_path, monkeypatch):
    """URL-bron: ook als er een snapshot bestaat, openen we de live URL."""
    _app()
    snapshots_root = tmp_path / "snapshots"
    snapshots_root.mkdir()
    (snapshots_root / "doc-url.html").write_text(
        "<html>snapshot</html>", encoding="utf-8"
    )

    geopend = {"url": None}

    def _fake_open(url):
        geopend["url"] = url.toString()
        return True

    monkeypatch.setattr(
        documentation_module.QDesktopServices, "openUrl", _fake_open
    )

    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_UrlDocumentationService(),
    )

    result = screen.open_document_by_id("doc-url")

    assert result is True
    assert geopend["url"] == "https://example.com/bron"


def test_markdown_document_blijft_interne_viewer(monkeypatch):
    """Markdown wordt nog steeds via de interne viewer getoond."""
    _app()
    service = _FakeDocumentationService()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=service,
    )

    executed = {"count": 0}

    def _fake_exec(self):
        executed["count"] += 1
        return 0

    from PySide6.QtWidgets import QDialog
    monkeypatch.setattr(QDialog, "exec", _fake_exec)

    result = screen.open_document_by_id("doc-1")

    assert result is True
    assert executed["count"] == 1
    assert service.last_read_language == "nl_NL"


def test_onbekend_bestandstype_geeft_statusmelding(monkeypatch):
    """Onbekende extensie: statusmelding, geen externe open."""
    _app()
    document = DocumentMetadata(
        document_id="doc-unknown",
        title="Onbekend",
        title_key=None,
        category=DocumentCategory.DATASHEET,
        source_type=DocumentSourceType.FILE,
        source_path="sources/doc.rar",
        source_url=None,
        tool_key=None,
        manufacturer=None,
        series=None,
        part_number=None,
        document_version=None,
        document_date=None,
        notes=None,
    )

    class _Service:
        def get_document(self, document_id):
            return document

        def list_documents(self, **kwargs):
            return [document]

    geopend = {"count": 0}
    monkeypatch.setattr(
        documentation_module.QDesktopServices,
        "openUrl",
        lambda url: geopend.__setitem__("count", geopend["count"] + 1) or True,
    )

    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_Service(),
    )
    result = screen.open_document_by_id("doc-unknown")

    assert result is False
    assert geopend["count"] == 0
    assert screen.status_label.text() != ""


# ============================================================================
# v1.10.0 — Bewerken-knop (fase 5D'.2c)
# ============================================================================

def test_edit_btn_bestaat_en_is_disabled_zonder_selectie():
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )
    assert screen.edit_btn is not None
    assert screen.edit_btn.isEnabled() is False


def test_edit_btn_disabled_bij_ingebouwd_document():
    """Ingenbouwd document: is_user_import=False → Bewerken disabled."""
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )
    screen.table.selectRow(0)
    assert screen.open_btn.isEnabled() is True
    assert screen.edit_btn.isEnabled() is False


def test_edit_btn_enabled_bij_gebruikersimport():
    """Eigen import: is_user_import=True → Bewerken enabled."""
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_UserImportDocumentationService(),
    )
    screen.table.selectRow(0)
    assert screen.open_btn.isEnabled() is True
    assert screen.edit_btn.isEnabled() is True


def test_edit_btn_tooltip_wisselt_met_selectie():
    """Tooltip geeft uitleg waarom bewerken wel/niet kan."""
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_UserImportDocumentationService(),
    )
    # Geen selectie: tooltip = "alleen eigen"
    assert "alleen" in screen.edit_btn.toolTip().lower() or \
        "eigen" in screen.edit_btn.toolTip().lower()

    # Selectie van een import: tooltip = "bewerken"
    screen.table.selectRow(0)
    assert "bewerken" in screen.edit_btn.toolTip().lower()


def test_edit_btn_tooltip_bij_ingebouwd_document():
    """Ingenbouwd document: tooltip verwijst naar read-only."""
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )
    screen.table.selectRow(0)
    tooltip = screen.edit_btn.toolTip().lower()
    assert "eigen" in tooltip or "alleen" in tooltip


def test_edit_selected_document_zonder_selectie_doet_niets(monkeypatch):
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_UserImportDocumentationService(),
    )

    geopend = {"count": 0}
    from PySide6.QtWidgets import QDialog
    monkeypatch.setattr(
        QDialog, "exec",
        lambda self: geopend.__setitem__("count", geopend["count"] + 1) or 0,
    )

    screen._edit_selected_document()
    assert geopend["count"] == 0


def test_edit_selected_document_bij_ingebouwd_toont_informatie(monkeypatch):
    """Defensief: als de knop toch vuurt bij een ingebouwd document,
    tonen we een informatieve melding en openen we de editor NIET."""
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )
    screen.table.selectRow(0)

    from PySide6.QtWidgets import QMessageBox, QDialog
    geopend = {"info": 0, "dialog": 0}

    monkeypatch.setattr(
        QMessageBox, "information",
        staticmethod(lambda *a, **kw: geopend.__setitem__("info", geopend["info"] + 1)),
    )
    monkeypatch.setattr(
        QDialog, "exec",
        lambda self: geopend.__setitem__("dialog", geopend["dialog"] + 1) or 0,
    )

    screen._edit_selected_document()

    assert geopend["info"] == 1
    assert geopend["dialog"] == 0


def test_edit_selected_document_opent_editor(tmp_path, monkeypatch):
    """Bij een gebruikersimport opent de editor met de juiste bron."""
    _app()
    from PySide6.QtCore import QObject, Signal

    from app.documentation.import_service import ImportService

    service = ImportService(catalog_path=tmp_path / "cat.json")
    r = service.register_pdf(
        title="Eigen import",
        original_filename="eigen.pdf",
        file_hash="hash_x",
        category="DATASHEET",
        manufacturer="CHONG",
        series="CDX",
        document_version="V1.1",
    )

    # DocService die hetzelfde source_id levert als de ImportService.
    doc = DocumentMetadata(
        document_id=r.source.source_id,
        title="Eigen import",
        title_key=None,
        category=DocumentCategory.DATASHEET,
        source_type=DocumentSourceType.FILE,
        source_path="sources/eigen.pdf",
        source_url=None,
        tool_key=None,
        manufacturer="CHONG",
        series="CDX",
        part_number=None,
        document_version="V1.1",
        document_date=None,
        notes=None,
        is_user_import=True,
    )

    class _Service:
        def get_document(self, document_id):
            return doc

        def list_documents(self, **kwargs):
            return [doc]

    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_Service(),
        import_service=service,
    )
    screen.table.selectRow(0)

    geopend = {"count": 0, "bron": None}

    # Fake editor: een echt Qt-signaal op klasse-niveau, en exec die telt.
    class _FakeEditor(QObject):
        metadata_saved = Signal(str)

        def __init__(self, *, bron, taal, import_service, parent):
            super().__init__(parent)
            geopend["bron"] = bron

        def exec(self):
            geopend["count"] += 1
            return 0

    import app.gui.documentation_screen as mod
    monkeypatch.setattr(mod, "EditMetadataDialog", _FakeEditor)

    screen._edit_selected_document()

    assert geopend["count"] == 1
    assert geopend["bron"] is not None
    assert geopend["bron"].source_id == r.source.source_id


def test_on_metadata_saved_ververst_en_behoudt_selectie(monkeypatch):
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_UserImportDocumentationService(),
    )
    screen.table.selectRow(0)
    assert screen._selected_document_id() == "import-1"

    refresh_count = {"n": 0}
    originele_refresh = screen.refresh
    def _fake_refresh():
        refresh_count["n"] += 1
        originele_refresh()
    monkeypatch.setattr(screen, "refresh", _fake_refresh)

    screen._on_metadata_saved("import-1")

    assert refresh_count["n"] == 1
    assert screen._selected_document_id() == "import-1"


def test_import_service_lazy_aangemaakt(tmp_path):
    """Zonder override en zonder klik op Bewerken blijft de service None."""
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )
    # Nog geen klik op Bewerken geweest
    assert screen._import_service_cache is None

    # Eigenschap zorgt voor luie aanmaak
    service = screen._import_service()
    assert service is not None
    assert screen._import_service_cache is service


def test_import_service_override_wordt_gebruikt(tmp_path):
    """Bij een override gebruikt de screen die, niet een nieuwe."""
    _app()
    from app.documentation.import_service import ImportService

    service = ImportService(catalog_path=tmp_path / "cat.json")
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_UserImportDocumentationService(),
        import_service=service,
    )
    assert screen._import_service() is service


# ============================================================================
# v1.11.0 — Status wijzigen (fase 5D'.2e)
# ============================================================================

def test_status_btn_bestaat_en_is_disabled_zonder_selectie():
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )
    assert screen.status_btn is not None
    assert screen.status_btn.isEnabled() is False


def test_status_btn_disabled_bij_ingebouwd_document():
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )
    screen.table.selectRow(0)
    assert screen.open_btn.isEnabled() is True
    assert screen.status_btn.isEnabled() is False


def test_status_btn_enabled_bij_gebruikersimport():
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_UserImportDocumentationService(),
    )
    screen.table.selectRow(0)
    assert screen.status_btn.isEnabled() is True


def test_status_btn_tooltip_wisselt_met_selectie():
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_UserImportDocumentationService(),
    )
    tooltip_leeg = screen.status_btn.toolTip().lower()
    assert "eigen" in tooltip_leeg or "alleen" in tooltip_leeg

    screen.table.selectRow(0)
    tooltip_sel = screen.status_btn.toolTip().lower()
    assert "wijzig" in tooltip_sel or "status" in tooltip_sel


def test_change_selected_status_zonder_selectie_doet_niets(monkeypatch):
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_UserImportDocumentationService(),
    )

    geopend = {"count": 0}
    from PySide6.QtWidgets import QDialog
    monkeypatch.setattr(
        QDialog, "exec",
        lambda self: geopend.__setitem__("count", geopend["count"] + 1) or 0,
    )

    screen._change_selected_status()
    assert geopend["count"] == 0


def test_change_selected_status_bij_ingebouwd_toont_informatie(monkeypatch):
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )
    screen.table.selectRow(0)

    from PySide6.QtWidgets import QMessageBox, QDialog
    geopend = {"info": 0, "dialog": 0}

    monkeypatch.setattr(
        QMessageBox, "information",
        staticmethod(lambda *a, **kw: geopend.__setitem__("info", geopend["info"] + 1)),
    )
    monkeypatch.setattr(
        QDialog, "exec",
        lambda self: geopend.__setitem__("dialog", geopend["dialog"] + 1) or 0,
    )

    screen._change_selected_status()

    assert geopend["info"] == 1
    assert geopend["dialog"] == 0


def test_change_selected_status_opent_dialoog(tmp_path, monkeypatch):
    _app()
    from PySide6.QtCore import QObject, Signal

    from app.documentation.import_service import ImportService

    service = ImportService(catalog_path=tmp_path / "cat.json")
    r = service.register_pdf(
        title="Eigen import",
        original_filename="eigen.pdf",
        file_hash="hash_y",
    )

    doc = DocumentMetadata(
        document_id=r.source.source_id,
        title="Eigen import",
        title_key=None,
        category=DocumentCategory.DATASHEET,
        source_type=DocumentSourceType.FILE,
        source_path="sources/eigen.pdf",
        source_url=None,
        tool_key=None,
        manufacturer=None,
        series=None,
        part_number=None,
        document_version=None,
        document_date=None,
        notes=None,
        is_user_import=True,
        import_status="concept",
    )

    class _Service:
        def get_document(self, document_id):
            return doc

        def list_documents(self, **kwargs):
            return [doc]

    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_Service(),
        import_service=service,
    )
    screen.table.selectRow(0)

    geopend = {"count": 0, "bron": None}

    class _FakeDialog(QObject):
        status_changed = Signal(str)

        def __init__(self, *, bron, taal, import_service, parent):
            super().__init__(parent)
            geopend["bron"] = bron

        def exec(self):
            geopend["count"] += 1
            return 0

    import app.gui.documentation_screen as mod
    monkeypatch.setattr(mod, "ChangeStatusDialog", _FakeDialog)

    screen._change_selected_status()

    assert geopend["count"] == 1
    assert geopend["bron"] is not None
    assert geopend["bron"].source_id == r.source.source_id


def test_on_status_changed_ververst_en_behoudt_selectie(monkeypatch):
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_UserImportDocumentationService(),
    )
    screen.table.selectRow(0)
    assert screen._selected_document_id() == "import-1"

    refresh_count = {"n": 0}
    originele_refresh = screen.refresh
    def _fake_refresh():
        refresh_count["n"] += 1
        originele_refresh()
    monkeypatch.setattr(screen, "refresh", _fake_refresh)

    screen._on_status_changed("import-1")

    assert refresh_count["n"] == 1
    assert screen._selected_document_id() == "import-1"


def test_toon_gearchiveerd_checkbox_bestaat_en_is_standaard_uit():
    _app()
    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )
    assert screen.toon_gearchiveerd_checkbox is not None
    assert screen.toon_gearchiveerd_checkbox.isChecked() is False


def test_toon_gearchiveerd_toont_gearchiveerde_documenten():
    """Met checkbox aan worden gearchiveerde imports zichtbaar."""
    _app()
    service = _UserImportDocumentationService(import_status="gearchiveerd")

    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=service,
    )
    # Standaard verborgen
    assert screen.table.rowCount() == 0

    # Checkbox aan → zichtbaar
    screen.toon_gearchiveerd_checkbox.setChecked(True)
    assert screen.table.rowCount() == 1


def test_status_kolom_toont_juiste_vertaling(monkeypatch):
    _app()
    monkeypatch.setattr(documentation_module, "vertaal", _fake_translate)

    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_UserImportDocumentationService(
            import_status="concept"
        ),
    )

    # De Status-kolom is index 2
    assert screen.table.item(0, 2).text() == (
        "nl_NL:documentatie.status_kolom.concept"
    )


def test_kolomindices_na_toevoeging_status_kolom(monkeypatch):
    """Regressietest: de tabel heeft 6 kolommen met de juiste koppen."""
    _app()
    monkeypatch.setattr(documentation_module, "vertaal", _fake_translate)

    screen = DocumentationScreen(
        taal="nl_NL",
        documentation_service=_FakeDocumentationService(),
    )

    assert screen.table.columnCount() == 6
    headers = [
        screen.table.horizontalHeaderItem(i).text()
        for i in range(screen.table.columnCount())
    ]
    assert headers[0] == "nl_NL:documentatie.kolom.titel"
    assert headers[1] == "nl_NL:documentatie.kolom.categorie"
    assert headers[2] == "nl_NL:documentatie.kolom.status"
    assert headers[3] == "nl_NL:documentatie.kolom.fabrikant"
    assert headers[4] == "nl_NL:documentatie.kolom.serie"
    assert headers[5] == "nl_NL:documentatie.kolom.versie"