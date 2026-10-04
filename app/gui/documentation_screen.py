"""
================================================================================
Module:     app/gui/documentation_screen.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.8.0
Datum:      2026-10-03
Auteur:     Bart Bossuyt

Doel:       Read-only scherm voor de centrale documentatiebibliotheek.

            Ondersteunt zoeken en filteren zonder documentmetadata te wijzigen.
            Import, AI-extractie, referentievalidatie en assessment-koppeling
            vallen bewust buiten deze fase.

Wijzigingen:
  v1.0.0 (2026-10-02)  Eerste read-only documentatiebibliotheekscherm.
  v1.1.0 (2026-10-02)  Interne Markdown-handleidingen kunnen read-only worden
                        geopend via knop of dubbelklik.
  v1.2.0 (2026-10-03)  Interne documenttitels volgen live de gekozen taal via
                        title_key; officiële brontitels blijven als fallback.
  v1.3.0 (2026-10-03)  Interne Markdown-inhoud wordt geopend in de actieve
                        app-taal met service-fallback naar nl_NL.
  v1.4.0 (2026-10-03)  Viewer-UX verbeterd: bredere documenttabel, rijkere
                        Markdown-weergave, vertaalde sluitknop, scrollstart
                        bovenaan en selectiebehoud na refresh/taalwissel.
  v1.5.0 (2026-10-03)  Documentinformatie en provenance zichtbaar gemaakt in
                        de read-only viewer, inclusief klikbare bron-URL's.
  v1.6.0 (2026-10-03)  Bovenste provenance-overzicht compacter gemaakt;
                        supports blijven in de Markdown-bronverantwoording.
  v1.7.0 (2026-10-03)  Hoogte van het informatiepaneel verfijnd zodat de
                        eerste provenance-regel niet wordt afgesneden.
  v1.8.0 (2026-10-03)  Publieke open_document_by_id()-API toegevoegd voor
                        contextueel openen vanuit diagnosetools.
================================================================================
"""

from __future__ import annotations

import html

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.documentation.models import DocumentCategory, DocumentMetadata
from app.documentation.service import DocumentationError, DocumentationService
from app.helpers.i18n import vertaal


class DocumentationScreen(QWidget):
    """Centrale read-only bibliotheek voor technische documentatie."""

    back_requested = Signal()

    def __init__(
        self,
        taal: str = "nl_NL",
        documentation_service: DocumentationService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.taal = taal
        self.documentation_service = (
            documentation_service
            if documentation_service is not None
            else DocumentationService()
        )

        self._build_ui()
        self.apply_language(self.taal)
        self.refresh()

    def _t(self, sleutel: str, **kwargs) -> str:
        return vertaal(sleutel, taal=self.taal, **kwargs)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        self.back_btn = QPushButton()
        self.back_btn.clicked.connect(self.back_requested.emit)
        top_row.addWidget(self.back_btn)
        top_row.addStretch()
        layout.addLayout(top_row)

        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(self.title_label)

        filter_row = QHBoxLayout()

        self.search_label = QLabel()
        filter_row.addWidget(self.search_label)

        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self.refresh)
        filter_row.addWidget(self.search_edit, 2)

        self.category_label = QLabel()
        filter_row.addWidget(self.category_label)

        self.category_combo = QComboBox()
        self.category_combo.currentIndexChanged.connect(self.refresh)
        filter_row.addWidget(self.category_combo, 1)

        self.tool_label = QLabel()
        filter_row.addWidget(self.tool_label)

        self.tool_combo = QComboBox()
        self.tool_combo.currentIndexChanged.connect(self.refresh)
        filter_row.addWidget(self.tool_combo, 1)

        layout.addLayout(filter_row)

        self.table = QTableWidget(0, 5)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self.table.itemSelectionChanged.connect(self._update_open_button)
        self.table.itemDoubleClicked.connect(
            lambda _item: self._open_selected_document()
        )
        layout.addWidget(self.table, 1)

        bottom_row = QHBoxLayout()
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        bottom_row.addWidget(self.status_label, 1)

        self.open_btn = QPushButton()
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self._open_selected_document)
        bottom_row.addWidget(self.open_btn)

        layout.addLayout(bottom_row)

    def apply_language(self, taal: str) -> None:
        """Werk alle zichtbare statische teksten bij zonder filters te wissen."""
        selected_category = self.category_combo.currentData()
        selected_tool = self.tool_combo.currentData()

        self.taal = taal
        self.back_btn.setText(self._t("knop.terug"))
        self.title_label.setText(self._t("documentatie.titel"))
        self.search_label.setText(self._t("documentatie.zoeken"))
        self.search_edit.setPlaceholderText(self._t("documentatie.zoeken_placeholder"))
        self.category_label.setText(self._t("documentatie.categorie"))
        self.tool_label.setText(self._t("documentatie.tool"))
        self.open_btn.setText(self._t("documentatie.openen"))

        self._rebuild_category_combo(selected_category)
        self._rebuild_tool_combo(selected_tool)

        headers = (
            self._t("documentatie.kolom.titel"),
            self._t("documentatie.kolom.categorie"),
            self._t("documentatie.kolom.fabrikant"),
            self._t("documentatie.kolom.serie"),
            self._t("documentatie.kolom.versie"),
        )
        self.table.setHorizontalHeaderLabels(headers)

        self.refresh()

    def _rebuild_category_combo(self, selected) -> None:
        self.category_combo.blockSignals(True)
        try:
            self.category_combo.clear()
            self.category_combo.addItem(
                self._t("documentatie.alle_categorieen"),
                None,
            )
            for category in DocumentCategory:
                self.category_combo.addItem(
                    self._category_label(category),
                    category.value,
                )
            self._restore_combo_value(self.category_combo, selected)
        finally:
            self.category_combo.blockSignals(False)

    def _rebuild_tool_combo(self, selected) -> None:
        self.tool_combo.blockSignals(True)
        try:
            self.tool_combo.clear()
            self.tool_combo.addItem(self._t("documentatie.alle_tools"), None)
            self.tool_combo.addItem(
                self._t("documentatie.algemeen"),
                "__GENERAL__",
            )
            self.tool_combo.addItem(
                self._t("tool_type.ESR_CAPACITOR"),
                "ESR_CAPACITOR",
            )
            self._restore_combo_value(self.tool_combo, selected)
        finally:
            self.tool_combo.blockSignals(False)

    @staticmethod
    def _restore_combo_value(combo: QComboBox, selected) -> None:
        if selected is None:
            combo.setCurrentIndex(0)
            return
        index = combo.findData(selected)
        combo.setCurrentIndex(index if index >= 0 else 0)

    def _category_label(self, category: DocumentCategory) -> str:
        return self._t(f"documentatie.categorieen.{category.value}")

    def _document_title(self, document: DocumentMetadata) -> str:
        """Vertaal interne titels; behoud officiële brontitel als fallback."""
        if not document.title_key:
            return document.title
        translated = self._t(document.title_key)
        if translated == document.title_key:
            return document.title
        return translated

    def refresh(self) -> None:
        """Herlaad de zichtbare read-only tabel volgens de huidige filters."""
        selected_document_id = self._selected_document_id()
        category = self.category_combo.currentData()
        tool_filter = self.tool_combo.currentData()

        service_tool_key = tool_filter
        if tool_filter == "__GENERAL__":
            service_tool_key = None

        try:
            documents = self.documentation_service.list_documents(
                search_text=self.search_edit.text(),
                category=category,
                tool_key=service_tool_key,
            )
            if tool_filter == "__GENERAL__":
                documents = [
                    document
                    for document in documents
                    if document.tool_key is None
                ]
        except DocumentationError as exc:
            self._populate_table([])
            self.status_label.setText(
                self._t("documentatie.fout", bericht=str(exc))
            )
            return

        self._populate_table(
            documents,
            selected_document_id=selected_document_id,
        )

        if documents:
            self.status_label.setText(
                self._t("documentatie.aantal", aantal=len(documents))
            )
        else:
            self.status_label.setText(self._t("documentatie.leeg"))

    def _populate_table(
        self,
        documents: list[DocumentMetadata],
        *,
        selected_document_id: str | None = None,
    ) -> None:
        self.table.setRowCount(len(documents))
        row_to_restore: int | None = None

        for row, document in enumerate(documents):
            values = (
                self._document_title(document),
                self._category_label(document.category),
                document.manufacturer or "",
                document.series or "",
                document.document_version or "",
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, document.document_id)
                self.table.setItem(row, column, item)

            if document.document_id == selected_document_id:
                row_to_restore = row

        if row_to_restore is not None:
            self.table.selectRow(row_to_restore)

        self._update_open_button()

    def _selected_document_id(self) -> str | None:
        selected_items = self.table.selectedItems()
        if not selected_items:
            return None
        document_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        return document_id if isinstance(document_id, str) and document_id else None

    def _update_open_button(self) -> None:
        self.open_btn.setEnabled(self._selected_document_id() is not None)

    def _document_information_html(self, document: DocumentMetadata) -> str:
        """Bouw een compact read-only HTML-overzicht van metadata en provenance."""

        def esc(value: object) -> str:
            return html.escape(str(value), quote=True)

        def row(label_key: str, value: str | None) -> str:
            if not value:
                return ""
            return (
                "<tr>"
                f"<td style='padding:2px 12px 2px 0; color:#BDBDBD; white-space:nowrap;'>"
                f"<b>{esc(self._t(label_key))}</b></td>"
                f"<td style='padding:2px 0; color:#F0F0F0;'>{esc(value)}</td>"
                "</tr>"
            )

        metadata_rows = "".join((
            row("documentatie.info.categorie", self._category_label(document.category)),
            row("documentatie.info.fabrikant", document.manufacturer),
            row("documentatie.info.serie", document.series),
            row("documentatie.info.partnummer", document.part_number),
            row("documentatie.info.versie", document.document_version),
            row("documentatie.info.datum", document.document_date),
            row("documentatie.info.notities", document.notes),
        ))

        source_url_html = ""
        if document.source_url:
            safe_url = esc(document.source_url)
            source_url_html = (
                "<tr>"
                f"<td style='padding:2px 12px 2px 0; color:#BDBDBD; white-space:nowrap;'>"
                f"<b>{esc(self._t('documentatie.info.bron_url'))}</b></td>"
                f"<td style='padding:2px 0;'><a href='{safe_url}'>{safe_url}</a></td>"
                "</tr>"
            )

        provenance_blocks: list[str] = []
        for index, ref in enumerate(document.provenance, start=1):
            details: list[str] = []
            if ref.locator:
                details.append(
                    f"<b>{esc(self._t('documentatie.info.locator'))}:</b> {esc(ref.locator)}"
                )
            if ref.note:
                details.append(
                    f"<b>{esc(self._t('documentatie.info.bron_notitie'))}:</b> {esc(ref.note)}"
                )
            if ref.source_url:
                safe_ref_url = esc(ref.source_url)
                details.append(
                    f"<b>{esc(self._t('documentatie.info.bron_url'))}:</b> "
                    f"<a href='{safe_ref_url}'>{safe_ref_url}</a>"
                )

            provenance_blocks.append(
                "<div style='margin:6px 0 10px 0;'>"
                f"<div><b>{index}. {esc(ref.source_title)}</b> "
                f"<span style='color:#9E9E9E;'>({esc(ref.source_id)})</span></div>"
                + "".join(
                    f"<div style='margin-left:14px; margin-top:2px;'>{detail}</div>"
                    for detail in details
                )
                + "</div>"
            )

        provenance_html = ""
        if provenance_blocks:
            provenance_html = (
                "<div style='margin-top:10px; padding-top:8px; border-top:1px solid #555555;'>"
                f"<div style='font-size:12pt; font-weight:bold; color:#FFFFFF;'>"
                f"{esc(self._t('documentatie.info.broninformatie'))}</div>"
                + "".join(provenance_blocks)
                + "</div>"
            )

        return (
            "<div style='font-family:Segoe UI; font-size:9.5pt; color:#F0F0F0;'>"
            f"<div style='font-size:12pt; font-weight:bold; color:#FFFFFF; margin-bottom:6px;'>"
            f"{esc(self._t('documentatie.info.documentinformatie'))}</div>"
            "<table cellspacing='0' cellpadding='0'>"
            f"{metadata_rows}{source_url_html}"
            "</table>"
            f"{provenance_html}"
            "</div>"
        )

    def _create_document_information_browser(
        self,
        document: DocumentMetadata,
    ) -> QTextBrowser:
        """Maak het metadata/provenance-paneel voor de viewer."""
        info_browser = QTextBrowser()
        info_browser.setOpenExternalLinks(True)
        info_browser.setHtml(self._document_information_html(document))
        info_browser.setMinimumHeight(140)
        info_browser.setMaximumHeight(200)
        info_browser.setStyleSheet(
            "QTextBrowser { background-color:#252525; color:#F0F0F0; "
            "border:1px solid #4A4A4A; padding:8px; }"
        )
        return info_browser

    def _open_selected_document(self) -> None:
        """Open het geselecteerde document via de centrale by-id viewer-API."""
        document_id = self._selected_document_id()
        if document_id is None:
            return
        self.open_document_by_id(document_id)

    def open_document_by_id(self, document_id: str) -> bool:
        """Open één document rechtstreeks op stabiele document-ID.

        Geeft True terug wanneer de viewer is geopend. Bij een documentatiefout
        wordt de bestaande statusmelding gebruikt en False teruggegeven.
        """
        try:
            document = self.documentation_service.get_document(document_id)
            content = self.documentation_service.read_document_text(
                document_id,
                language=self.taal,
            )
        except DocumentationError as exc:
            self.status_label.setText(
                self._t("documentatie.document_fout", bericht=str(exc))
            )
            return False

        dialog = QDialog(self)
        dialog.setWindowTitle(self._document_title(document))
        dialog.resize(960, 720)
        dialog.setMinimumSize(720, 520)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        info_browser = self._create_document_information_browser(document)
        layout.addWidget(info_browser)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setStyleSheet(
            "QTextBrowser { background-color: #1E1E1E; color: #F0F0F0; "
            "border: 1px solid #4A4A4A; padding: 10px; }"
        )
        browser.document().setDefaultStyleSheet(
            "body { color: #F0F0F0; background-color: #1E1E1E; "
            "font-family: 'Segoe UI'; font-size: 10.5pt; line-height: 1.35; } "
            "h1 { color: #FFFFFF; font-size: 20pt; margin-top: 8px; margin-bottom: 14px; } "
            "h2 { color: #FFFFFF; font-size: 15pt; margin-top: 18px; margin-bottom: 8px; } "
            "h3, h4 { color: #FFFFFF; margin-top: 14px; margin-bottom: 6px; } "
            "p { color: #F0F0F0; margin-top: 5px; margin-bottom: 8px; } "
            "li { color: #F0F0F0; margin-bottom: 4px; } "
            "a { color: #8AB4F8; text-decoration: underline; } "
            "code { color: #DCDCAA; background-color: #2A2A2A; padding: 2px 4px; } "
            "pre { color: #F0F0F0; background-color: #2A2A2A; "
            "border: 1px solid #4A4A4A; padding: 8px; } "
            "blockquote { color: #D0D0D0; border-left: 3px solid #6A6A6A; "
            "margin-left: 8px; padding-left: 10px; } "
            "table { border-collapse: collapse; margin-top: 8px; margin-bottom: 10px; } "
            "th { color: #FFFFFF; background-color: #333333; font-weight: bold; "
            "border: 1px solid #666666; padding: 5px; } "
            "td { color: #F0F0F0; border: 1px solid #555555; padding: 5px; }"
        )
        browser.setMarkdown(content)
        browser.verticalScrollBar().setValue(0)
        layout.addWidget(browser, 1)

        button_row = QHBoxLayout()
        button_row.addStretch()
        close_btn = QPushButton(self._t("documentatie.sluiten"))
        close_btn.clicked.connect(dialog.reject)
        button_row.addWidget(close_btn)
        layout.addLayout(button_row)

        dialog.exec()
        return True
