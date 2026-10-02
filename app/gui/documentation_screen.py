"""
================================================================================
Module:     app/gui/documentation_screen.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-02
Auteur:     Bart Bossuyt

Doel:       Read-only scherm voor de centrale documentatiebibliotheek.

            Ondersteunt zoeken en filteren zonder documentmetadata te wijzigen.
            Import, AI-extractie, referentievalidatie en assessment-koppeling
            vallen bewust buiten deze fase.

Wijzigingen:
  v1.0.0 (2026-10-02)  Eerste read-only documentatiebibliotheekscherm.
================================================================================
"""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
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
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

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

    def refresh(self) -> None:
        """Herlaad de zichtbare read-only tabel volgens de huidige filters."""
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

        self._populate_table(documents)
        if documents:
            self.status_label.setText(
                self._t("documentatie.aantal", aantal=len(documents))
            )
        else:
            self.status_label.setText(self._t("documentatie.leeg"))

    def _populate_table(self, documents: list[DocumentMetadata]) -> None:
        self.table.setRowCount(len(documents))

        for row, document in enumerate(documents):
            values = (
                document.title,
                self._category_label(document.category),
                document.manufacturer or "",
                document.series or "",
                document.document_version or "",
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, document.document_id)
                self.table.setItem(row, column, item)

        self.table.resizeColumnsToContents()
