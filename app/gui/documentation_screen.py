"""
================================================================================
Module:     app/gui/documentation_screen.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     2.3.0
Datum:      2026-10-08
Auteur:     Bart Bossuyt

Doel:       Read-only scherm voor de centrale documentatiebibliotheek.

            Ondersteunt zoeken en filteren zonder documentmetadata te wijzigen.
            Import, AI-extractie, referentievalidatie en assessment-koppeling
            vallen bewust buiten deze fase. Sinds 5D'.2c kan de gebruiker
            via een Bewerken-knop de metadata van een eigen import aanpassen
            (niet van ingebouwde documenten). Sinds 5D'.2e kan de gebruiker
            via een Status wijzigen-knop de levenscyclus van een eigen
            import aanpassen. Een extra checkbox maakt gearchiveerde
            imports zichtbaar in de lijst.

Wijzigingen:
  v1.0.0 (2026-10-02)  Eerste read-only documentatiebibliotheekscherm.
  v1.1.0 (2026-10-02)  Interne Markdown-handleidingen kunnen read-only worden
                        geopend via knop of dubbelklik.
  v1.2.0 (2026-10-03)  Interne documenttitels volgen live de gekozen taal via
                        title_key; officiële brontitels blijven als fallback.
  v1.3.0 (2026-10-03)  Interne Markdown-inhoud wordt geopend in de actieve
                        app-taal met service-fallback naar nl_NL.
  v1.4.0 (2026-10-03)  Viewer-UX verbeterd.
  v1.5.0 (2026-10-03)  Documentinformatie en provenance zichtbaar gemaakt.
  v1.6.0 (2026-10-03)  Provenance-overzicht compacter.
  v1.7.0 (2026-10-03)  Hoogte van informatiepaneel verfijnd.
  v1.8.0 (2026-10-03)  Publieke open_document_by_id()-API toegevoegd.
  v1.9.0 (2026-10-05)  Help-knop en F1 openen de zoektaal-help-dialoog.
  v1.9.1 (2026-10-05)  Lokale WidgetWithChildrenShortcut-sneltoetsen.
  v2.0.0 (2026-10-06)  Fase 5E: import_requested signaal, Importeer-knop.
  v2.1.0 (2026-10-07)  Fase 5D'.4: dispatch op basis van source_kind.
  v2.1.1 (2026-10-07)  URL-bron opent altijd de live URL in de browser,
                        niet de lokale snapshot.
  v2.2.0 (2026-10-07)  Fase 5D'.2c: Bewerken-knop. Alleen actief voor
                        documenten uit de gebruikerscatalogus
                        (is_user_import=True). Opent EditMetadataDialog
                        en ververst de tabel na succes.
  v2.3.0 (2026-10-08)  Fase 5D'.2e: Status wijzigen-knop. Alleen actief
                        voor eigen imports. Opent ChangeStatusDialog en
                        ververst de tabel na succes. Nieuwe checkbox
                        "Toon gearchiveerde". Nieuwe Status-kolom in de
                        tabel.
================================================================================
"""

from __future__ import annotations

import html

from pathlib import Path

from PySide6.QtCore import QUrl, Signal, Qt
from PySide6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.documentation.import_models import ImportValidationError
from app.documentation.import_service import ImportService
from app.documentation.models import DocumentCategory, DocumentMetadata
from app.documentation.service import DocumentationError, DocumentationService
from app.documentation.pdf_extract import default_sources_dir
from app.gui.dialogs.change_status_dialog import ChangeStatusDialog
from app.gui.dialogs.edit_metadata_dialog import EditMetadataDialog
from app.gui.dialogs.search_help_dialog import SearchHelpDialog
from app.helpers.document_source_paths import (
    resolve_local_path,
    source_kind,
)
from app.helpers.i18n import vertaal


class DocumentationScreen(QWidget):
    """Centrale read-only bibliotheek voor technische documentatie."""

    back_requested = Signal()
    import_requested = Signal()

    def __init__(
        self,
        taal: str = "nl_NL",
        documentation_service: DocumentationService | None = None,
        import_service: ImportService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.taal = taal
        self.documentation_service = (
            documentation_service
            if documentation_service is not None
            else DocumentationService()
        )
        # ImportService wordt alleen gebruikt voor de metadata-editor en
        # de status-editor. We maken hem lui aan bij de eerste klik, zodat
        # tests die geen gebruikerscatalogus hebben geen onbedoelde
        # ImportService krijgen.
        self._import_service_override = import_service
        self._import_service_cache: ImportService | None = import_service

        self._build_ui()
        self._setup_shortcuts()
        self.apply_language(self.taal)
        self.refresh()

    def _t(self, sleutel: str, **kwargs) -> str:
        return vertaal(sleutel, taal=self.taal, **kwargs)

    def _import_service(self) -> ImportService:
        """Lui aanmaken van de ImportService voor de editor(s).

        In productie: de standaardservice die de gebruikerscatalogus leest.
        In tests: de meegegeven override, zodat geen %LOCALAPPDATA% wordt
        aangeraakt.
        """
        if self._import_service_cache is None:
            self._import_service_cache = ImportService()
        return self._import_service_cache

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        self.back_btn = QPushButton()
        self.back_btn.clicked.connect(self.back_requested.emit)
        top_row.addWidget(self.back_btn)
        top_row.addStretch()

        self.import_btn = QPushButton()
        self.import_btn.clicked.connect(self.import_requested.emit)
        top_row.addWidget(self.import_btn)

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

        self.help_btn = QPushButton()
        self.help_btn.setFixedWidth(32)
        self.help_btn.clicked.connect(self._open_search_help_dialog)
        filter_row.addWidget(self.help_btn)

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

        self.toon_gearchiveerd_checkbox = QCheckBox()
        self.toon_gearchiveerd_checkbox.toggled.connect(self.refresh)
        filter_row.addWidget(self.toon_gearchiveerd_checkbox)

        layout.addLayout(filter_row)

        # 6 kolommen: Titel, Categorie, Status, Fabrikant, Serie, Versie
        self.table = QTableWidget(0, 6)
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
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        self.table.itemSelectionChanged.connect(self._update_action_buttons)
        self.table.itemDoubleClicked.connect(
            lambda _item: self._open_selected_document()
        )
        layout.addWidget(self.table, 1)

        bottom_row = QHBoxLayout()
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        bottom_row.addWidget(self.status_label, 1)

        self.edit_btn = QPushButton()
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self._edit_selected_document)
        bottom_row.addWidget(self.edit_btn)

        self.status_btn = QPushButton()
        self.status_btn.setEnabled(False)
        self.status_btn.clicked.connect(self._change_selected_status)
        bottom_row.addWidget(self.status_btn)

        self.open_btn = QPushButton()
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self._open_selected_document)
        bottom_row.addWidget(self.open_btn)

        layout.addLayout(bottom_row)

    def _setup_shortcuts(self) -> None:
        """Lokale sneltoetsen voor dit scherm."""
        context = Qt.ShortcutContext.WidgetWithChildrenShortcut

        QShortcut(
            QKeySequence(Qt.Key.Key_Escape),
            self,
            activated=self.back_requested.emit,
            context=context,
        )
        QShortcut(
            QKeySequence(Qt.Key.Key_Return),
            self,
            activated=self._open_selected_document,
            context=context,
        )
        QShortcut(
            QKeySequence("Ctrl+F"),
            self,
            activated=self._focus_search_edit,
            context=context,
        )
        QShortcut(
            QKeySequence("Ctrl+L"),
            self,
            activated=self._focus_and_select_search_edit,
            context=context,
        )
        QShortcut(
            QKeySequence("Ctrl+O"),
            self,
            activated=self._open_selected_document,
            context=context,
        )
        QShortcut(
            QKeySequence(Qt.Key.Key_F1),
            self,
            activated=self._open_search_help_dialog,
            context=context,
        )

    def _focus_search_edit(self) -> None:
        self.search_edit.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self.search_edit.deselect()

    def _focus_and_select_search_edit(self) -> None:
        self.search_edit.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self.search_edit.selectAll()

    def _open_search_help_dialog(self) -> None:
        dialog = SearchHelpDialog(taal=self.taal, parent=self)
        dialog.exec()

    def apply_language(self, taal: str) -> None:
        """Werk alle zichtbare statische teksten bij zonder filters te wissen."""
        selected_category = self.category_combo.currentData()
        selected_tool = self.tool_combo.currentData()

        self.taal = taal
        self.back_btn.setText(self._t("knop.terug"))
        self.import_btn.setText(self._t("documentatie.import.knop"))
        self.import_btn.setToolTip(self._t("documentatie.import.knop_tooltip"))
        self.title_label.setText(self._t("documentatie.titel"))
        self.search_label.setText(self._t("documentatie.zoeken"))
        self.search_edit.setPlaceholderText(self._t("documentatie.zoeken_placeholder"))
        self.search_edit.setToolTip(self._t("documentatie.zoeken_tooltip"))
        self.help_btn.setText(self._t("documentatie.help_knop"))
        self.help_btn.setToolTip(self._t("documentatie.help_knop_tooltip"))
        self.category_label.setText(self._t("documentatie.categorie"))
        self.tool_label.setText(self._t("documentatie.tool"))
        self.open_btn.setText(self._t("documentatie.openen"))
        self.edit_btn.setText(self._t("documentatie.bewerken"))
        self.status_btn.setText(self._t("documentatie.status_wijzigen"))
        self.toon_gearchiveerd_checkbox.setText(
            self._t("documentatie.toon_gearchiveerd")
        )
        self.toon_gearchiveerd_checkbox.setToolTip(
            self._t("documentatie.toon_gearchiveerd_tooltip")
        )

        self._rebuild_category_combo(selected_category)
        self._rebuild_tool_combo(selected_tool)

        headers = (
            self._t("documentatie.kolom.titel"),
            self._t("documentatie.kolom.categorie"),
            self._t("documentatie.kolom.status"),
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
        if not document.title_key:
            return document.title
        translated = self._t(document.title_key)
        if translated == document.title_key:
            return document.title
        return translated

    def _status_label(self, document: DocumentMetadata) -> str:
        """Vertaal de import_status van een document, of leeg voor ingebouwd."""
        status = getattr(document, "import_status", None)
        if not isinstance(status, str) or not status.strip():
            return ""
        sleutel = f"documentatie.status_kolom.{status.strip().lower()}"
        vertaald = self._t(sleutel)
        if vertaald == sleutel:
            return ""
        return vertaald

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
                include_archived=self.toon_gearchiveerd_checkbox.isChecked(),
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
                self._status_label(document),
                document.manufacturer or "",
                document.series or "",
                document.document_version or "",
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, document.document_id)
                # Bewaar ook of dit een gebruikersimport is, zodat de
                # Bewerken- en Status-knop kunnen beslissen. We gebruiken
                # een aparte rol om de UserRole (document_id) niet te
                # overschrijven.
                item.setData(
                    Qt.ItemDataRole.UserRole + 1,
                    bool(document.is_user_import),
                )
                self.table.setItem(row, column, item)

            if document.document_id == selected_document_id:
                row_to_restore = row

        if row_to_restore is not None:
            self.table.selectRow(row_to_restore)

        self._update_action_buttons()

    def _selected_document_id(self) -> str | None:
        selected_items = self.table.selectedItems()
        if not selected_items:
            return None
        document_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        return document_id if isinstance(document_id, str) and document_id else None

    def _selected_is_user_import(self) -> bool:
        selected_items = self.table.selectedItems()
        if not selected_items:
            return False
        vlag = selected_items[0].data(Qt.ItemDataRole.UserRole + 1)
        return bool(vlag)

    def _update_action_buttons(self) -> None:
        """Openen is altijd actief bij selectie; Bewerken en Status alleen bij import."""
        heeft_selectie = self._selected_document_id() is not None
        self.open_btn.setEnabled(heeft_selectie)

        mag_bewerken = heeft_selectie and self._selected_is_user_import()
        self.edit_btn.setEnabled(mag_bewerken)
        if mag_bewerken:
            self.edit_btn.setToolTip(
                self._t("documentatie.bewerken_tooltip")
            )
        else:
            self.edit_btn.setToolTip(
                self._t("documentatie.bewerken_alleen_eigen")
            )

        self.status_btn.setEnabled(mag_bewerken)
        if mag_bewerken:
            self.status_btn.setToolTip(
                self._t("documentatie.status_wijzigen_tooltip")
            )
        else:
            self.status_btn.setToolTip(
                self._t("documentatie.status_wijzigen_alleen_eigen")
            )

    def select_document_by_id(self, document_id: str) -> bool:
        """Selecteer een document in de tabel op basis van zijn ID."""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is None:
                continue
            if item.data(Qt.ItemDataRole.UserRole) == document_id:
                self.table.selectRow(row)
                self.table.scrollToItem(item)
                return True
        return False

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

    def _edit_selected_document(self) -> None:
        """Open de metadata-editor voor het geselecteerde import-item."""
        document_id = self._selected_document_id()
        if document_id is None:
            return
        if not self._selected_is_user_import():
            # Zou niet moeten kunnen (knop disabled), maar defensief.
            QMessageBox.information(
                self,
                self._t("documentatie.bewerken_titel"),
                self._t("documentatie.bewerken_alleen_eigen"),
            )
            return

        try:
            bron = self._import_service().get(document_id)
        except ImportValidationError as exc:
            QMessageBox.warning(
                self,
                self._t("documentatie.bewerken_fout_titel"),
                self._t(
                    "documentatie.bewerken_fout_bericht",
                    bericht=str(exc),
                ),
            )
            return

        dialog = EditMetadataDialog(
            bron=bron,
            taal=self.taal,
            import_service=self._import_service(),
            parent=self,
        )
        dialog.metadata_saved.connect(self._on_metadata_saved)
        dialog.exec()

    def _on_metadata_saved(self, source_id: str) -> None:
        """Ververs de tabel na een succesvolle metadata-edit."""
        self.refresh()
        # Houd de selectie vast.
        if source_id:
            self.select_document_by_id(source_id)

    def _change_selected_status(self) -> None:
        """Open de status-editor voor het geselecteerde import-item."""
        document_id = self._selected_document_id()
        if document_id is None:
            return
        if not self._selected_is_user_import():
            # Zou niet moeten kunnen (knop disabled), maar defensief.
            QMessageBox.information(
                self,
                self._t("documentatie.status_wijzigen_titel"),
                self._t("documentatie.status_wijzigen_alleen_eigen"),
            )
            return

        try:
            bron = self._import_service().get(document_id)
        except ImportValidationError as exc:
            QMessageBox.warning(
                self,
                self._t("documentatie.status_wijzigen_fout_titel"),
                self._t(
                    "documentatie.status_wijzigen_fout_bericht",
                    bericht=str(exc),
                ),
            )
            return

        dialog = ChangeStatusDialog(
            bron=bron,
            taal=self.taal,
            import_service=self._import_service(),
            parent=self,
        )
        dialog.status_changed.connect(self._on_status_changed)
        dialog.exec()

    def _on_status_changed(self, source_id: str) -> None:
        """Ververs de tabel na een succesvolle statuswijziging.

        Als de nieuwe status 'gearchiveerd' is, kan het document
        verdwijnen uit de standaardweergave. We behouden de selectie
        alleen als het document nog zichtbaar is.
        """
        self.refresh()
        if source_id:
            self.select_document_by_id(source_id)

    def _open_selected_document(self) -> None:
        """Open het geselecteerde document via de centrale by-id viewer-API."""
        document_id = self._selected_document_id()
        if document_id is None:
            return
        self.open_document_by_id(document_id)

    def _open_external(self, url: QUrl) -> bool:
        """Open een URL of lokaal bestand via het besturingssysteem."""
        try:
            return bool(QDesktopServices.openUrl(url))
        except Exception:
            return False

    def _open_document_external(self, document: DocumentMetadata) -> bool:
        """Open een niet-Markdown-bron extern.

        Retourneert True bij succes, False bij fout (met statusmelding).
        """
        kind = source_kind(document)

        if kind == "url":
            # URL-bron: altijd de live URL openen in de browser.
            # De lokale snapshot blijft bewaard voor provenance, maar is
            # niet langer het open-doel (5D'.4-correctie v2.1.1).
            if not document.source_url:
                self.status_label.setText(
                    self._t(
                        "documentatie.document_fout",
                        bericht=self._t("documentatie.onbekend_bestandstype"),
                    )
                )
                return False
            return self._open_external(QUrl(document.source_url))

        if kind in ("pdf", "word", "excel"):
            lokaal_pad = resolve_local_path(
                document,
                sources_root=default_sources_dir(),
            )
            if lokaal_pad is None:
                self.status_label.setText(
                    self._t(
                        "documentatie.document_fout",
                        bericht=self._t("documentatie.bestand_niet_gevonden"),
                    )
                )
                return False
            return self._open_external(QUrl.fromLocalFile(str(lokaal_pad)))

        # kind == "onbekend"
        self.status_label.setText(
            self._t(
                "documentatie.document_fout",
                bericht=self._t("documentatie.onbekend_bestandstype"),
            )
        )
        return False

    def open_document_by_id(self, document_id: str) -> bool:
        """Open één document rechtstreeks op stabiele document-ID.

        Dispatcht op basis van source_kind:
          - markdown → interne viewer (bestaand gedrag)
          - pdf/word/excel → extern openen in de standaard-app
          - url → live URL openen in de browser
          - onbekend → statusmelding, geen viewer

        Geeft True terug wanneer het openen gelukt is, anders False.
        """
        try:
            document = self.documentation_service.get_document(document_id)
        except DocumentationError as exc:
            self.status_label.setText(
                self._t("documentatie.document_fout", bericht=str(exc))
            )
            return False

        kind = source_kind(document)

        if kind != "markdown":
            return self._open_document_external(document)

        # Markdown/tekst: interne viewer.
        try:
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