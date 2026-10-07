"""
================================================================================
Module:     app/gui/dialogs/import_wizard_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-07
Auteur:     Bart Bossuyt

Doel:       Modale wizard voor het importeren van een PDF of URL als
            documentatiebron. Roept de GUI-onafhankelijke services aan
            (import_pdf / import_url) en toont een samenvatting vóór
            bevestiging. Bij een bestaande bron toont de wizard een
            popup met drie keuzes (Behouden / Nieuwe versie / Overschrijven)
            via DuplicateSourceDialog. Geen netwerk- of PDF-logica in deze
            module buiten de hash-berekening.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie: radio voor type, bestandskiezer of
                       URL-veld, samenvatting, importeren.
  v1.0.1 (2026-10-06)  Per ongeluk binnengeslopen self-import verwijderd
                       die een circulaire import veroorzaakte.
  v1.0.2 (2026-10-07)  Titel-voorstel bij PDF is nu altijd de bestandsnaam
                       (zonder extensie). De PDF-metadata /Title is vaak
                       rommel en blijft alleen zichtbaar in het
                       samenvattingsblok.
  v1.1.0 (2026-10-07)  Duplicate-detectie vóór import (fase 5D'.2a):
                       find_duplicate + DuplicateSourceDialog. Gekozen
                       DuplicateAction wordt doorgegeven aan import_pdf /
                       import_url. Bij KEEP met match: geen import.
================================================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.documentation.duplicate_check import find_duplicate
from app.documentation.import_models import (
    DuplicateAction,
    DuplicateMatch,
    ImportValidationError,
)
from app.documentation.import_service import ImportService
from app.documentation.pdf_extract import (
    PdfExtractError,
    compute_file_hash,
    extract_pdf_metadata,
)
from app.documentation.pdf_import import import_pdf
from app.documentation.url_fetch import (
    UrlFetchError,
    UrlMetadata,
    fetch_url_metadata,
)
from app.documentation.url_import import import_url
from app.gui.dialogs.duplicate_source_dialog import DuplicateSourceDialog
from app.helpers.i18n import vertaal


class ImportWizardDialog(QDialog):
    """Modale wizard voor het importeren van een PDF of URL."""

    import_completed = Signal(str)  # source_id van de nieuwe bron

    def __init__(
        self,
        *,
        taal: str = "nl_NL",
        import_service: Optional[ImportService] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.taal = taal
        self.import_service = import_service or ImportService()

        # Interne toestand
        self._pdf_pad: Optional[Path] = None
        self._pdf_meta_titel: Optional[str] = None
        self._pdf_hash: Optional[str] = None
        self._url: Optional[str] = None
        self._url_meta: Optional[UrlMetadata] = None

        self.setModal(True)
        self.resize(560, 480)
        self.setMinimumSize(480, 420)

        self._build_ui()
        self._apply_language()
        self._update_state()

    # ---------------------------------------------------------------- helpers

    def _t(self, sleutel: str, **kwargs) -> str:
        return vertaal(sleutel, taal=self.taal, **kwargs)

    # ---------------------------------------------------------------- UI

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Titel
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.title_label)

        # Type-keuze
        self.type_label = QLabel()
        layout.addWidget(self.type_label)

        type_row = QHBoxLayout()
        self.radio_pdf = QRadioButton()
        self.radio_pdf.setChecked(True)
        self.radio_url = QRadioButton()
        self.type_group = QButtonGroup(self)
        self.type_group.addButton(self.radio_pdf)
        self.type_group.addButton(self.radio_url)
        self.radio_pdf.toggled.connect(self._on_type_changed)
        type_row.addWidget(self.radio_pdf)
        type_row.addWidget(self.radio_url)
        type_row.addStretch()
        layout.addLayout(type_row)

        # PDF-paneel
        self.pdf_panel = QWidget()
        pdf_layout = QHBoxLayout(self.pdf_panel)
        pdf_layout.setContentsMargins(0, 0, 0, 0)
        self.pdf_path_label = QLabel()
        self.pdf_path_label.setWordWrap(True)
        self.pdf_path_label.setStyleSheet("color: #AAAAAA;")
        pdf_layout.addWidget(self.pdf_path_label, 1)
        self.pdf_pick_btn = QPushButton()
        self.pdf_pick_btn.clicked.connect(self._pick_pdf)
        pdf_layout.addWidget(self.pdf_pick_btn)
        layout.addWidget(self.pdf_panel)

        # URL-paneel
        self.url_panel = QWidget()
        url_layout = QHBoxLayout(self.url_panel)
        url_layout.setContentsMargins(0, 0, 0, 0)
        self.url_edit = QLineEdit()
        self.url_edit.textChanged.connect(self._update_state)
        url_layout.addWidget(self.url_edit, 1)
        self.url_fetch_btn = QPushButton()
        self.url_fetch_btn.clicked.connect(self._fetch_url_metadata)
        url_layout.addWidget(self.url_fetch_btn)
        layout.addWidget(self.url_panel)

        # Titel-veld (bewerkbaar)
        form = QFormLayout()
        self.title_label_field = QLabel()
        self.title_edit = QLineEdit()
        form.addRow(self.title_label_field, self.title_edit)
        layout.addLayout(form)

        # Samenvatting
        self.summary_label = QLabel()
        layout.addWidget(self.summary_label)
        self.summary_browser = QTextBrowser()
        self.summary_browser.setMinimumHeight(120)
        self.summary_browser.setStyleSheet(
            "QTextBrowser { background-color:#252525; color:#F0F0F0; "
            "border:1px solid #4A4A4A; padding:8px; }"
        )
        layout.addWidget(self.summary_browser, 1)

        # Knoppen
        button_row = QHBoxLayout()
        button_row.addStretch()
        self.cancel_btn = QPushButton()
        self.cancel_btn.clicked.connect(self.reject)
        button_row.addWidget(self.cancel_btn)
        self.import_btn = QPushButton()
        self.import_btn.clicked.connect(self._perform_import)
        self.import_btn.setDefault(True)
        button_row.addWidget(self.import_btn)
        layout.addLayout(button_row)

    def _apply_language(self) -> None:
        self.setWindowTitle(self._t("documentatie.import.titel"))
        self.title_label.setText(self._t("documentatie.import.titel"))
        self.type_label.setText(self._t("documentatie.import.type_vraag"))
        self.radio_pdf.setText(self._t("documentatie.import.type_pdf"))
        self.radio_url.setText(self._t("documentatie.import.type_url"))
        self.pdf_path_label.setText(
            self._pdf_pad.name
            if self._pdf_pad
            else self._t("documentatie.import.geen_bestand")
        )
        self.pdf_pick_btn.setText(self._t("documentatie.import.kies_bestand"))
        self.url_edit.setPlaceholderText(
            self._t("documentatie.import.url_placeholder")
        )
        self.url_fetch_btn.setText(
            self._t("documentatie.import.metadata_ophalen")
        )
        self.title_label_field.setText(
            self._t("documentatie.import.veld_titel")
        )
        self.summary_label.setText(self._t("documentatie.import.samenvatting"))
        self.cancel_btn.setText(self._t("documentatie.import.annuleren"))
        self.import_btn.setText(self._t("documentatie.import.importeren"))

    # ---------------------------------------------------------------- events

    def _on_type_changed(self) -> None:
        self._update_state()

    def _update_state(self) -> None:
        is_pdf = self.radio_pdf.isChecked()
        self.pdf_panel.setVisible(is_pdf)
        self.url_panel.setVisible(not is_pdf)
        self.url_fetch_btn.setEnabled(
            not is_pdf and bool(self.url_edit.text().strip())
        )

        # Import-knop actief zodra een bron klaar is
        klaar = (
            (is_pdf and self._pdf_pad is not None)
            or (not is_pdf and self._url_meta is not None)
        )
        self.import_btn.setEnabled(klaar)

        # Samenvatting
        self._refresh_summary()

    def _pick_pdf(self) -> None:
        pad, _ = QFileDialog.getOpenFileName(
            self,
            self._t("documentatie.import.kies_bestand_titel"),
            "",
            "PDF (*.pdf)",
        )
        if not pad:
            return

        bron_pad = Path(pad)
        try:
            meta = extract_pdf_metadata(bron_pad)
        except PdfExtractError as exc:
            QMessageBox.warning(
                self,
                self._t("documentatie.import.fout_titel"),
                self._t("documentatie.import.fout_pdf", bericht=str(exc)),
            )
            return

        # Hash nu berekenen: nodig voor duplicate-detectie vóór import.
        try:
            self._pdf_hash = compute_file_hash(bron_pad)
        except PdfExtractError as exc:
            QMessageBox.warning(
                self,
                self._t("documentatie.import.fout_titel"),
                self._t("documentatie.import.fout_pdf", bericht=str(exc)),
            )
            return

        self._pdf_pad = bron_pad
        self._pdf_meta_titel = meta.title
        self.pdf_path_label.setText(bron_pad.name)

        # Titel-voorstel: altijd de bestandsnaam (zonder extensie). De
        # PDF-metadata-titel blijft zichtbaar in het samenvattingsblok.
        voorgestelde_titel = bron_pad.stem
        if not self.title_edit.text().strip():
            self.title_edit.setText(voorgestelde_titel)

        self._update_state()

    def _fetch_url_metadata(self) -> None:
        url = self.url_edit.text().strip()
        if not url:
            return

        try:
            meta = fetch_url_metadata(url)
        except UrlFetchError as exc:
            QMessageBox.warning(
                self,
                self._t("documentatie.import.fout_titel"),
                self._t("documentatie.import.fout_url", bericht=str(exc)),
            )
            return

        self._url = url
        self._url_meta = meta

        if not self.title_edit.text().strip():
            self.title_edit.setText(meta.og_title or meta.title or url)

        self._update_state()

    def _refresh_summary(self) -> None:
        if self.radio_pdf.isChecked() and self._pdf_pad:
            try:
                grootte = self._pdf_pad.stat().st_size
            except OSError:
                grootte = 0
            regels = [
                f"<b>{self._t('documentatie.import.samenvatting_type')}:</b> "
                f"{self._t('documentatie.import.type_pdf')}",
                f"<b>{self._t('documentatie.import.samenvatting_bestand')}:</b> "
                f"{self._pdf_pad.name}",
                f"<b>{self._t('documentatie.import.samenvatting_grootte')}:</b> "
                f"{grootte} bytes",
            ]
            if self._pdf_meta_titel:
                regels.append(
                    f"<b>{self._t('documentatie.import.samenvatting_pdf_titel')}:</b> "
                    f"{self._pdf_meta_titel}"
                )
            self.summary_browser.setHtml("<br>".join(regels))
            return

        if self.radio_url.isChecked() and self._url_meta:
            regels = [
                f"<b>{self._t('documentatie.import.samenvatting_type')}:</b> "
                f"{self._t('documentatie.import.type_url')}",
                f"<b>{self._t('documentatie.import.samenvatting_url')}:</b> "
                f"{self._url_meta.url}",
                f"<b>{self._t('documentatie.import.samenvatting_http')}:</b> "
                f"{self._url_meta.http_status}",
            ]
            if self._url_meta.title:
                regels.append(
                    f"<b>{self._t('documentatie.import.samenvatting_pagina_titel')}:</b> "
                    f"{self._url_meta.title}"
                )
            if self._url_meta.language:
                regels.append(
                    f"<b>{self._t('documentatie.import.samenvatting_taal')}:</b> "
                    f"{self._url_meta.language}"
                )
            self.summary_browser.setHtml("<br>".join(regels))
            return

        self.summary_browser.setHtml(
            f"<i style='color:#888;'>"
            f"{self._t('documentatie.import.samenvatting_leeg')}</i>"
        )

    # ---------------------------------------------------------------- duplicate

    def _check_duplicate(self) -> Optional[DuplicateMatch]:
        """Zoek een bestaande bron voor de huidige keuze.

        Retourneert None als er geen match is, of als er nog geen bron
        klaarstaat. Anders een DuplicateMatch.
        """
        if self.radio_pdf.isChecked():
            if self._pdf_hash is None:
                return None
            return find_duplicate(
                self.import_service, file_hash=self._pdf_hash
            )
        if self._url_meta is None:
            return None
        return find_duplicate(
            self.import_service, source_url=self._url_meta.url
        )

    # ---------------------------------------------------------------- importeren

    def _perform_import(self) -> None:
        titel = self.title_edit.text().strip() or None

        # Duplicate-check vóór import.
        match = self._check_duplicate()

        # Bepaal de actie.
        if match is not None:
            actie = DuplicateSourceDialog.vraag_actie(
                match=match,
                taal=self.taal,
                parent=self,
            )
            if actie is None:
                # Gebruiker annuleerde de popup: niets doen.
                return
            if actie is DuplicateAction.KEEP:
                # Niets wijzigen; wizard blijft open zodat de gebruiker
                # eventueel een andere keuze kan maken.
                return
        else:
            # Geen match: gewone import.
            actie = DuplicateAction.NEW_VERSION

        try:
            if self.radio_pdf.isChecked():
                if self._pdf_pad is None:
                    return
                result = import_pdf(
                    self._pdf_pad,
                    import_service=self.import_service,
                    title=titel,
                    duplicate_action=actie,
                )
            else:
                if self._url is None:
                    return
                result = import_url(
                    self._url,
                    import_service=self.import_service,
                    title=titel,
                    duplicate_action=actie,
                )
        except (PdfExtractError, UrlFetchError, ImportValidationError) as exc:
            QMessageBox.warning(
                self,
                self._t("documentatie.import.fout_titel"),
                self._t("documentatie.import.fout_import", bericht=str(exc)),
            )
            return

        # Succes: meld het resultaat en sluit
        self.import_completed.emit(result.source.source_id)
        self.accept()