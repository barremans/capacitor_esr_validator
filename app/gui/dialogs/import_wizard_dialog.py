"""
================================================================================
Module:     app/gui/dialogs/import_wizard_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.7.0
Datum:      2026-10-09
Auteur:     Bart Bossuyt

Doel:       Modale wizard voor het importeren van een PDF, Word-document,
            Excel-werkmap of URL als documentatiebron. Roept de
            GUI-onafhankelijke services aan (import_pdf / import_docx /
            import_xlsx / import_url) en toont een samenvatting vóór
            bevestiging. Bij een bestaande bron toont de wizard een
            popup met drie keuzes (Behouden / Nieuwe versie / Overschrijven)
            via DuplicateSourceDialog. Sinds 5D'.2b bevat de wizard ook
            een metadata-sectie (categorie verplicht, rest optioneel).
            Sinds 5D'.2d is documentdatum een QDateEdit met kalenderpopup
            en "Datum onbekend"-checkbox, en worden identificatievelden
            automatisch in uppercase gezet. Sinds 5D'.2c gebruikt de
            wizard de gedeelde helpers uit _metadata_form_helpers.
            Sinds 6B ondersteunt de wizard ook Word (.docx) en Excel
            (.xlsx); de oude formaten .doc en .xls worden geweigerd.
            Sinds 6C toont de wizard een expliciete succesmelding na
            een geslaagde import, zodat de gebruiker visueel bevestiging
            krijgt vóór het sluiten van de wizard.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie.
  v1.0.1 (2026-10-06)  Self-import verwijderd.
  v1.0.2 (2026-10-07)  Titel-voorstel bij PDF is nu altijd bestandsnaam.
  v1.1.0 (2026-10-07)  Duplicate-detectie vóór import (5D'.2a).
  v1.2.0 (2026-10-07)  Fase 5D'.3: startmap + laatste_importmap.
  v1.2.1 (2026-10-07)  Titelveld wordt alleen automatisch overschreven
                       als de gebruiker het niet handmatig heeft bewerkt.
  v1.3.0 (2026-10-07)  Fase 5D'.2b: metadata-sectie in de wizard.
  v1.4.0 (2026-10-07)  Fase 5D'.2d: UX-verfijning (QDateEdit,
                       "Datum onbekend", Ctrl+D, uppercase).
  v1.5.0 (2026-10-07)  Fase 5D'.2c: gedeelde helpers uit
                       _metadata_form_helpers gebruikt voor
                       categorie-dropdown en uppercase. Geen
                       gedragswijziging.
  v1.6.0 (2026-10-09)  Fase 6B: vier radio buttons (PDF / Word / Excel /
                       URL). Nieuwe methoden _pick_docx en _pick_xlsx,
                       uitbreiding van _update_state, _refresh_summary,
                       _check_duplicate en _perform_import. .doc en
                       .xls worden geweigerd door de extractors.
  v1.7.0 (2026-10-09)  Fase 6C: succesmelding na geslaagde import via
                       QMessageBox.information met de titel van het
                       geïmporteerde document.
================================================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDateEdit,
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

from app.config.settings import (
    AppInstellingen,
    laad_instellingen,
    sla_instellingen_op,
)
from app.documentation.duplicate_check import find_duplicate
from app.documentation.import_models import (
    DuplicateAction,
    DuplicateMatch,
    ImportValidationError,
)
from app.documentation.import_service import ImportService
from app.documentation.models import DocumentCategory
from app.documentation.pdf_extract import (
    PdfExtractError,
    compute_file_hash,
    extract_pdf_metadata,
)
from app.documentation.pdf_import import import_pdf
from app.documentation.docx_extract import (
    DocxExtractError,
    compute_file_hash as compute_docx_hash,
    extract_docx_metadata,
)
from app.documentation.docx_import import import_docx
from app.documentation.xlsx_extract import (
    XlsxExtractError,
    compute_file_hash as compute_xlsx_hash,
    extract_xlsx_metadata,
)
from app.documentation.xlsx_import import import_xlsx
from app.documentation.url_fetch import (
    UrlFetchError,
    UrlMetadata,
    fetch_url_metadata,
)
from app.documentation.url_import import import_url
from app.gui.dialogs._metadata_form_helpers import (
    CATEGORIE_VOLGORDE,
    naar_uppercase,
    vul_categorie_combo,
)
from app.gui.dialogs.duplicate_source_dialog import DuplicateSourceDialog
from app.helpers.i18n import vertaal
from dataclasses import replace as _dc_replace


class ImportWizardDialog(QDialog):
    """Modale wizard voor het importeren van een PDF, Word, Excel of URL."""

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

        # Interne toestand — PDF
        self._pdf_pad: Optional[Path] = None
        self._pdf_meta_titel: Optional[str] = None
        self._pdf_hash: Optional[str] = None
        # Interne toestand — DOCX
        self._docx_pad: Optional[Path] = None
        self._docx_meta_titel: Optional[str] = None
        self._docx_hash: Optional[str] = None
        # Interne toestand — XLSX
        self._xlsx_pad: Optional[Path] = None
        self._xlsx_meta_titel: Optional[str] = None
        self._xlsx_hash: Optional[str] = None
        # Interne toestand — URL
        self._url: Optional[str] = None
        self._url_meta: Optional[UrlMetadata] = None
        # Titelveld-state: True zolang de titel automatisch is ingevuld en
        # de gebruiker hem niet handmatig heeft bewerkt.
        self._titel_automatisch: bool = True

        self.setModal(True)
        self.resize(620, 700)
        self.setMinimumSize(520, 640)

        self._build_ui()
        self._apply_language()
        self._update_state()

    # ---------------------------------------------------------------- helpers

    def _t(self, sleutel: str, **kwargs) -> str:
        return vertaal(sleutel, taal=self.taal, **kwargs)

    @staticmethod
    def _map_bestaat(pad: str) -> bool:
        """Controleer of pad een bestaande map is."""
        if not pad:
            return False
        try:
            return Path(pad).expanduser().is_dir()
        except (OSError, ValueError):
            return False

    def _start_map_voor_pdf(self, instellingen: AppInstellingen) -> str:
        """Bepaal de beste startmap voor de PDF-bestandskiezer."""
        laatste = instellingen.algemeen.laatste_importmap
        if self._map_bestaat(laatste):
            return laatste
        standaard = instellingen.algemeen.standaard_importmap
        if self._map_bestaat(standaard):
            return standaard
        return ""

    def _onthoud_laatste_importmap(self, gekozen_pad: Path) -> None:
        """Werk laatste_importmap bij na een geslaagde bestandskeuze."""
        try:
            nieuwe_map = str(gekozen_pad.parent)
            instellingen = laad_instellingen()
            if instellingen.algemeen.laatste_importmap == nieuwe_map:
                return
            bijgewerkt = _dc_replace(
                instellingen,
                algemeen=_dc_replace(
                    instellingen.algemeen,
                    laatste_importmap=nieuwe_map,
                ),
            )
            sla_instellingen_op(bijgewerkt)
        except (OSError, ValueError):
            pass

    def _stel_titel_voor(self, voorgestelde_titel: str) -> None:
        """Zet een automatische titel, tenzij de gebruiker handmatig typte."""
        if self._titel_automatisch or not self.title_edit.text().strip():
            self.title_edit.setText(voorgestelde_titel)
            self._titel_automatisch = True

    def _on_titel_handmatig_bewerkt(self, _tekst: str) -> None:
        """Markeer het titelveld als handmatig bewerkt."""
        self._titel_automatisch = False

    # ---------------------------------------------------------------- metadata

    def _huidige_categorie(self) -> str:
        """Lees de gekozen categorie als DocumentCategory.value."""
        data = self.categorie_combo.currentData()
        if data is None:
            return DocumentCategory.DATASHEET.value
        return str(data)

    def _documentdatum_waarde(self) -> Optional[str]:
        """Lees de documentdatum als ISO-string, of None."""
        if self.datum_onbekend_checkbox.isChecked():
            return None
        return self.documentdatum_edit.date().toString("yyyy-MM-dd")

    def _metadata_uit_formulier(self) -> dict:
        """Verzamel alle metadata-velden behalve notes."""
        return {
            "category": self._huidige_categorie(),
            "manufacturer": self.fabrikant_edit.text(),
            "series": self.serie_edit.text(),
            "part_number": self.partnummer_edit.text(),
            "document_version": self.documentversie_edit.text(),
            "document_date": self._documentdatum_waarde(),
        }

    def _notities_uit_formulier(self) -> Optional[str]:
        """Lees het notitieveld; leeg wordt None."""
        tekst = self.notities_edit.text()
        return tekst if tekst.strip() else None

    def _on_datum_onbekend_gewisseld(self, aangevinkt: bool) -> None:
        """Schakel het datumveld in of uit op basis van de checkbox."""
        self.documentdatum_edit.setEnabled(not aangevinkt)

    def _zet_datum_op_vandaag(self) -> None:
        """Sneltoets Ctrl+D: zet de documentdatum op vandaag."""
        if self.datum_onbekend_checkbox.isChecked():
            return
        self.documentdatum_edit.setDate(QDate.currentDate())

    def _toon_succesmelding(self, titel: str) -> None:
        """Toon een korte bevestiging dat het document geïmporteerd is.

        Wordt aangeroepen vóór self.accept(), zodat de gebruiker ziet
        dat de import geslaagd is. De wizard blijft open tot de gebruiker
        op OK klikt; daarna sluit hij.
        """
        QMessageBox.information(
            self,
            self._t("documentatie.import.succes_titel"),
            self._t("documentatie.import.succes_bericht", titel=titel),
        )

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
        self.radio_word = QRadioButton()
        self.radio_excel = QRadioButton()
        self.radio_url = QRadioButton()
        self.type_group = QButtonGroup(self)
        self.type_group.addButton(self.radio_pdf)
        self.type_group.addButton(self.radio_word)
        self.type_group.addButton(self.radio_excel)
        self.type_group.addButton(self.radio_url)
        self.radio_pdf.toggled.connect(self._on_type_changed)
        type_row.addWidget(self.radio_pdf)
        type_row.addWidget(self.radio_word)
        type_row.addWidget(self.radio_excel)
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

        # Word-paneel
        self.word_panel = QWidget()
        word_layout = QHBoxLayout(self.word_panel)
        word_layout.setContentsMargins(0, 0, 0, 0)
        self.word_path_label = QLabel()
        self.word_path_label.setWordWrap(True)
        self.word_path_label.setStyleSheet("color: #AAAAAA;")
        word_layout.addWidget(self.word_path_label, 1)
        self.word_pick_btn = QPushButton()
        self.word_pick_btn.clicked.connect(self._pick_docx)
        word_layout.addWidget(self.word_pick_btn)
        layout.addWidget(self.word_panel)

        # Excel-paneel
        self.excel_panel = QWidget()
        excel_layout = QHBoxLayout(self.excel_panel)
        excel_layout.setContentsMargins(0, 0, 0, 0)
        self.excel_path_label = QLabel()
        self.excel_path_label.setWordWrap(True)
        self.excel_path_label.setStyleSheet("color: #AAAAAA;")
        excel_layout.addWidget(self.excel_path_label, 1)
        self.excel_pick_btn = QPushButton()
        self.excel_pick_btn.clicked.connect(self._pick_xlsx)
        excel_layout.addWidget(self.excel_pick_btn)
        layout.addWidget(self.excel_panel)

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
        titel_form = QFormLayout()
        self.title_label_field = QLabel()
        self.title_edit = QLineEdit()
        self.title_edit.textEdited.connect(self._on_titel_handmatig_bewerkt)
        titel_form.addRow(self.title_label_field, self.title_edit)
        layout.addLayout(titel_form)

        # Metadata-sectie
        self.metadata_label = QLabel()
        self.metadata_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.metadata_label)

        metadata_form = QFormLayout()
        self.categorie_label = QLabel()
        self.categorie_combo = QComboBox()
        metadata_form.addRow(self.categorie_label, self.categorie_combo)

        self.fabrikant_label = QLabel()
        self.fabrikant_edit = QLineEdit()
        self.fabrikant_edit.textEdited.connect(
            lambda _t: naar_uppercase(self.fabrikant_edit)
        )
        metadata_form.addRow(self.fabrikant_label, self.fabrikant_edit)

        self.serie_label = QLabel()
        self.serie_edit = QLineEdit()
        self.serie_edit.textEdited.connect(
            lambda _t: naar_uppercase(self.serie_edit)
        )
        metadata_form.addRow(self.serie_label, self.serie_edit)

        self.partnummer_label = QLabel()
        self.partnummer_edit = QLineEdit()
        self.partnummer_edit.textEdited.connect(
            lambda _t: naar_uppercase(self.partnummer_edit)
        )
        metadata_form.addRow(self.partnummer_label, self.partnummer_edit)

        self.documentversie_label = QLabel()
        self.documentversie_edit = QLineEdit()
        self.documentversie_edit.textEdited.connect(
            lambda _t: naar_uppercase(self.documentversie_edit)
        )
        metadata_form.addRow(
            self.documentversie_label, self.documentversie_edit
        )

        # Documentdatum: QDateEdit + "Datum onbekend"-checkbox
        self.documentdatum_label = QLabel()
        self.documentdatum_edit = QDateEdit()
        self.documentdatum_edit.setCalendarPopup(True)
        self.documentdatum_edit.setDisplayFormat("yyyy-MM-dd")
        self.documentdatum_edit.setDate(QDate.currentDate())
        self.datum_onbekend_checkbox = QCheckBox()
        self.datum_onbekend_checkbox.toggled.connect(
            self._on_datum_onbekend_gewisseld
        )
        datum_row = QHBoxLayout()
        datum_row.setContentsMargins(0, 0, 0, 0)
        datum_row.addWidget(self.documentdatum_edit, 1)
        datum_row.addWidget(self.datum_onbekend_checkbox)
        datum_widget = QWidget()
        datum_widget.setLayout(datum_row)
        metadata_form.addRow(self.documentdatum_label, datum_widget)

        self.notities_label = QLabel()
        self.notities_edit = QLineEdit()
        metadata_form.addRow(self.notities_label, self.notities_edit)

        layout.addLayout(metadata_form)

        # Ctrl+D binnen de dialoog: zet documentdatum op vandaag.
        self._datum_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        self._datum_shortcut.activated.connect(self._zet_datum_op_vandaag)

        # Samenvatting
        self.summary_label = QLabel()
        layout.addWidget(self.summary_label)
        self.summary_browser = QTextBrowser()
        self.summary_browser.setMinimumHeight(100)
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
        self.radio_word.setText(self._t("documentatie.import.type_word"))
        self.radio_excel.setText(self._t("documentatie.import.type_excel"))
        self.radio_url.setText(self._t("documentatie.import.type_url"))
        self.pdf_path_label.setText(
            self._pdf_pad.name
            if self._pdf_pad
            else self._t("documentatie.import.geen_bestand")
        )
        self.word_path_label.setText(
            self._docx_pad.name
            if self._docx_pad
            else self._t("documentatie.import.geen_bestand")
        )
        self.excel_path_label.setText(
            self._xlsx_pad.name
            if self._xlsx_pad
            else self._t("documentatie.import.geen_bestand")
        )
        self.pdf_pick_btn.setText(self._t("documentatie.import.kies_bestand"))
        self.word_pick_btn.setText(self._t("documentatie.import.kies_word"))
        self.excel_pick_btn.setText(self._t("documentatie.import.kies_excel"))
        self.url_edit.setPlaceholderText(
            self._t("documentatie.import.url_placeholder")
        )
        self.url_fetch_btn.setText(
            self._t("documentatie.import.metadata_ophalen")
        )
        self.title_label_field.setText(
            self._t("documentatie.import.veld_titel")
        )
        self.metadata_label.setText(
            self._t("documentatie.import.metadata_sectie")
        )
        self.categorie_label.setText(
            self._t("documentatie.import.veld_categorie")
        )
        self.fabrikant_label.setText(
            self._t("documentatie.import.veld_fabrikant")
        )
        self.serie_label.setText(self._t("documentatie.import.veld_serie"))
        self.partnummer_label.setText(
            self._t("documentatie.import.veld_partnummer")
        )
        self.documentversie_label.setText(
            self._t("documentatie.import.veld_documentversie")
        )
        self.documentdatum_label.setText(
            self._t("documentatie.import.veld_documentdatum")
        )
        self.datum_onbekend_checkbox.setText(
            self._t("documentatie.import.veld_documentdatum_onbekend")
        )
        self.documentdatum_edit.setToolTip(
            self._t("documentatie.import.datum_vandaag_tooltip")
        )
        self.notities_label.setText(
            self._t("documentatie.import.veld_notities")
        )
        # Categorie-labels vullen/herzetten via de gedeelde helper.
        huidige_selectie = self.categorie_combo.currentData()
        vul_categorie_combo(self.categorie_combo, self._t)
        if self.categorie_combo.count() > 0:
            if huidige_selectie is None:
                self.categorie_combo.setCurrentIndex(0)
            else:
                index = self.categorie_combo.findData(huidige_selectie)
                self.categorie_combo.setCurrentIndex(
                    index if index >= 0 else 0
                )
        self.summary_label.setText(self._t("documentatie.import.samenvatting"))
        self.cancel_btn.setText(self._t("documentatie.import.annuleren"))
        self.import_btn.setText(self._t("documentatie.import.importeren"))

    # ---------------------------------------------------------------- events

    def _on_type_changed(self) -> None:
        self._update_state()

    def _update_state(self) -> None:
        is_pdf = self.radio_pdf.isChecked()
        is_word = self.radio_word.isChecked()
        is_excel = self.radio_excel.isChecked()
        is_url = self.radio_url.isChecked()

        self.pdf_panel.setVisible(is_pdf)
        self.word_panel.setVisible(is_word)
        self.excel_panel.setVisible(is_excel)
        self.url_panel.setVisible(is_url)

        self.url_fetch_btn.setEnabled(
            is_url and bool(self.url_edit.text().strip())
        )

        klaar = (
            (is_pdf and self._pdf_pad is not None)
            or (is_word and self._docx_pad is not None)
            or (is_excel and self._xlsx_pad is not None)
            or (is_url and self._url_meta is not None)
        )
        self.import_btn.setEnabled(klaar)

        self._refresh_summary()

    def _pick_pdf(self) -> None:
        instellingen = laad_instellingen()
        start_map = self._start_map_voor_pdf(instellingen)

        pad, _ = QFileDialog.getOpenFileName(
            self,
            self._t("documentatie.import.kies_bestand_titel"),
            start_map,
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

        self._stel_titel_voor(bron_pad.stem)
        self._onthoud_laatste_importmap(bron_pad)

        self._update_state()

    def _pick_docx(self) -> None:
        instellingen = laad_instellingen()
        start_map = self._start_map_voor_pdf(instellingen)

        pad, _ = QFileDialog.getOpenFileName(
            self,
            self._t("documentatie.import.kies_word_titel"),
            start_map,
            "Word (*.docx)",
        )
        if not pad:
            return

        bron_pad = Path(pad)
        try:
            meta = extract_docx_metadata(bron_pad)
        except DocxExtractError as exc:
            QMessageBox.warning(
                self,
                self._t("documentatie.import.fout_titel"),
                self._t("documentatie.import.fout_word", bericht=str(exc)),
            )
            return

        try:
            self._docx_hash = compute_docx_hash(bron_pad)
        except DocxExtractError as exc:
            QMessageBox.warning(
                self,
                self._t("documentatie.import.fout_titel"),
                self._t("documentatie.import.fout_word", bericht=str(exc)),
            )
            return

        self._docx_pad = bron_pad
        self._docx_meta_titel = meta.title
        self.word_path_label.setText(bron_pad.name)

        self._stel_titel_voor(bron_pad.stem)
        self._onthoud_laatste_importmap(bron_pad)

        self._update_state()

    def _pick_xlsx(self) -> None:
        instellingen = laad_instellingen()
        start_map = self._start_map_voor_pdf(instellingen)

        pad, _ = QFileDialog.getOpenFileName(
            self,
            self._t("documentatie.import.kies_excel_titel"),
            start_map,
            "Excel (*.xlsx)",
        )
        if not pad:
            return

        bron_pad = Path(pad)
        try:
            meta = extract_xlsx_metadata(bron_pad)
        except XlsxExtractError as exc:
            QMessageBox.warning(
                self,
                self._t("documentatie.import.fout_titel"),
                self._t("documentatie.import.fout_excel", bericht=str(exc)),
            )
            return

        try:
            self._xlsx_hash = compute_xlsx_hash(bron_pad)
        except XlsxExtractError as exc:
            QMessageBox.warning(
                self,
                self._t("documentatie.import.fout_titel"),
                self._t("documentatie.import.fout_excel", bericht=str(exc)),
            )
            return

        self._xlsx_pad = bron_pad
        self._xlsx_meta_titel = meta.title
        self.excel_path_label.setText(bron_pad.name)

        self._stel_titel_voor(bron_pad.stem)
        self._onthoud_laatste_importmap(bron_pad)

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

        self._stel_titel_voor(meta.og_title or meta.title or url)

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

        if self.radio_word.isChecked() and self._docx_pad:
            try:
                grootte = self._docx_pad.stat().st_size
            except OSError:
                grootte = 0
            regels = [
                f"<b>{self._t('documentatie.import.samenvatting_type')}:</b> "
                f"{self._t('documentatie.import.type_word')}",
                f"<b>{self._t('documentatie.import.samenvatting_bestand')}:</b> "
                f"{self._docx_pad.name}",
                f"<b>{self._t('documentatie.import.samenvatting_grootte')}:</b> "
                f"{grootte} bytes",
            ]
            try:
                meta = extract_docx_metadata(self._docx_pad)
                regels.append(
                    f"<b>{self._t('documentatie.import.samenvatting_paragrafen')}:</b> "
                    f"{meta.paragraph_count}"
                )
            except DocxExtractError:
                pass
            if self._docx_meta_titel:
                regels.append(
                    f"<b>{self._t('documentatie.import.samenvatting_pdf_titel')}:</b> "
                    f"{self._docx_meta_titel}"
                )
            self.summary_browser.setHtml("<br>".join(regels))
            return

        if self.radio_excel.isChecked() and self._xlsx_pad:
            try:
                grootte = self._xlsx_pad.stat().st_size
            except OSError:
                grootte = 0
            regels = [
                f"<b>{self._t('documentatie.import.samenvatting_type')}:</b> "
                f"{self._t('documentatie.import.type_excel')}",
                f"<b>{self._t('documentatie.import.samenvatting_bestand')}:</b> "
                f"{self._xlsx_pad.name}",
                f"<b>{self._t('documentatie.import.samenvatting_grootte')}:</b> "
                f"{grootte} bytes",
            ]
            try:
                meta = extract_xlsx_metadata(self._xlsx_pad)
                regels.append(
                    f"<b>{self._t('documentatie.import.samenvatting_bladen')}:</b> "
                    f"{meta.sheet_count}"
                )
            except XlsxExtractError:
                pass
            if self._xlsx_meta_titel:
                regels.append(
                    f"<b>{self._t('documentatie.import.samenvatting_pdf_titel')}:</b> "
                    f"{self._xlsx_meta_titel}"
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
        """Zoek een bestaande bron voor de huidige keuze."""
        if self.radio_pdf.isChecked():
            if self._pdf_hash is None:
                return None
            return find_duplicate(
                self.import_service, file_hash=self._pdf_hash
            )
        if self.radio_word.isChecked():
            if self._docx_hash is None:
                return None
            return find_duplicate(
                self.import_service, file_hash=self._docx_hash
            )
        if self.radio_excel.isChecked():
            if self._xlsx_hash is None:
                return None
            return find_duplicate(
                self.import_service, file_hash=self._xlsx_hash
            )
        if self._url_meta is None:
            return None
        return find_duplicate(
            self.import_service, source_url=self._url_meta.url
        )

    # ---------------------------------------------------------------- importeren

    def _perform_import(self) -> None:
        titel = self.title_edit.text().strip() or None
        metadata = self._metadata_uit_formulier()
        notities = self._notities_uit_formulier()

        match = self._check_duplicate()

        if match is not None:
            actie = DuplicateSourceDialog.vraag_actie(
                match=match,
                taal=self.taal,
                parent=self,
            )
            if actie is None:
                return
            if actie is DuplicateAction.KEEP:
                return
        else:
            actie = DuplicateAction.NEW_VERSION

        try:
            if self.radio_pdf.isChecked():
                if self._pdf_pad is None:
                    return
                result = import_pdf(
                    self._pdf_pad,
                    import_service=self.import_service,
                    title=titel,
                    notes=notities,
                    duplicate_action=actie,
                    **metadata,
                )
            elif self.radio_word.isChecked():
                if self._docx_pad is None:
                    return
                result = import_docx(
                    self._docx_pad,
                    import_service=self.import_service,
                    title=titel,
                    notes=notities,
                    duplicate_action=actie,
                    **metadata,
                )
            elif self.radio_excel.isChecked():
                if self._xlsx_pad is None:
                    return
                result = import_xlsx(
                    self._xlsx_pad,
                    import_service=self.import_service,
                    title=titel,
                    notes=notities,
                    duplicate_action=actie,
                    **metadata,
                )
            else:
                if self._url is None:
                    return
                result = import_url(
                    self._url,
                    import_service=self.import_service,
                    title=titel,
                    notes=notities,
                    duplicate_action=actie,
                    **metadata,
                )
        except (
            PdfExtractError,
            DocxExtractError,
            XlsxExtractError,
            UrlFetchError,
            ImportValidationError,
        ) as exc:
            QMessageBox.warning(
                self,
                self._t("documentatie.import.fout_titel"),
                self._t("documentatie.import.fout_import", bericht=str(exc)),
            )
            return

        # Toon bevestiging vóór het sluiten van de wizard.
        if result.changed:
            self._toon_succesmelding(result.source.title)

        self.import_completed.emit(result.source.source_id)
        self.accept()