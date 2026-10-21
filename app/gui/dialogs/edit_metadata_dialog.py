"""
================================================================================
Module:     app/gui/dialogs/edit_metadata_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.2.0
Datum:      2026-10-20
Auteur:     Bart Bossuyt

Doel:       Modale dialoog waarmee de gebruiker de metadata van een eigen
            import kan bewerken. Roept ImportService.update_metadata aan
            en raakt uitsluitend metadata aan: titel, categorie, fabrikant,
            serie, partnummer, documentversie, documentdatum, notities.
            Bronbestand, source_id, status en imported_at blijven
            onaangeroerd.

            De ingebouwde catalogus is read-only. Deze dialoog wordt alleen
            getoond voor documenten met is_user_import=True.

Wijzigingen:
  v1.0.0 (2026-10-07)  Eerste versie (fase 5D'.2c). Hergebruikt de
                       gedeelde helpers _metadata_form_helpers voor
                       categorie-dropdown en uppercase.
  v1.1.0 (2026-10-16)  Fase 11C: dialoog krijgt een venstericoon via
                        de centrale helper app/helpers/icon_paths.
                        Geen wijziging aan de metadatalogica.
  v1.2.0 (2026-10-20)  Fase 11F.4: datum-parsing verfijnd. Nieuwe pure
                        helper _parse_datum_naar_qdate accepteert naast
                        yyyy-MM-dd ook yyyy/MM/dd, dd-MM-yyyy, yyyy-MM
                        (dag 1) en yyyy (1 januari). Lukt geen enkel
                        formaat, dan blijft "Datum onbekend" aangevinkt.
                        Geen wijziging aan de overige metadatalogica.
================================================================================
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QDate, QSignalBlocker, Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.documentation.import_models import (
    ImportSource,
    ImportValidationError,
)
from app.documentation.import_service import ImportService
from app.documentation.models import DocumentCategory
from app.gui.dialogs._metadata_form_helpers import (
    naar_uppercase,
    vul_categorie_combo,
)
from app.helpers.i18n import vertaal


class EditMetadataDialog(QDialog):
    """Modale editor voor de metadata van één eigen import."""

    metadata_saved = Signal(str)  # source_id

    def __init__(
        self,
        *,
        bron: ImportSource,
        taal: str = "nl_NL",
        import_service: Optional[ImportService] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.taal = taal
        self.bron = bron
        self.import_service = import_service or ImportService()

        self.setModal(True)
        self.resize(560, 520)
        self.setMinimumSize(480, 460)
        self._zet_eigen_icoon()

        self._build_ui()
        self._apply_language()
        self._laad_bestaande_metadata()
        self._update_save_state()

    # ---------------------------------------------------------------- helpers

    def _t(self, sleutel: str, **kwargs) -> str:
        return vertaal(sleutel, taal=self.taal, **kwargs)

    def _huidige_categorie(self) -> str:
        data = self.categorie_combo.currentData()
        if data is None:
            return DocumentCategory.DATASHEET.value
        return str(data)

    def _documentdatum_waarde(self) -> Optional[str]:
        if self.datum_onbekend_checkbox.isChecked():
            return None
        return self.documentdatum_edit.date().toString("yyyy-MM-dd")

    def _on_datum_onbekend_gewisseld(self, aangevinkt: bool) -> None:
        self.documentdatum_edit.setEnabled(not aangevinkt)

    def _zet_datum_op_vandaag(self) -> None:
        if self.datum_onbekend_checkbox.isChecked():
            return
        self.documentdatum_edit.setDate(QDate.currentDate())

    def _update_save_state(self) -> None:
        """De Opslaan-knop is alleen actief als de titel niet leeg is."""
        self.save_btn.setEnabled(bool(self.title_edit.text().strip()))

    def _on_titel_bewerkt(self, _tekst: str) -> None:
        self._update_save_state()

    @staticmethod
    def _parse_datum_naar_qdate(ruwe: str) -> QDate:
        """Probeer een ruwe datumstring om te zetten naar een geldige QDate.

        Volgorde van ondersteunde formaten:
          1. yyyy-MM-dd   (ISO, exact)         bv. "2024-01-31"
          2. yyyy/MM/dd   (schuine streep)     bv. "2024/01/31"
          3. dd-MM-yyyy   (NL-notatie)         bv. "31-01-2024"
          4. yyyy-MM      (maand-only → dag 1) bv. "2024-01"
          5. yyyy         (jaar-only → 1 jan)  bv. "2024"

        Retourneert een ongeldige QDate als geen enkel formaat past.
        """
        tekst = (ruwe or "").strip()
        if not tekst:
            return QDate()

        # 1. ISO yyyy-MM-dd
        qdate = QDate.fromString(tekst, "yyyy-MM-dd")
        if qdate.isValid():
            return qdate

        # 2. yyyy/MM/dd
        qdate = QDate.fromString(tekst, "yyyy/MM/dd")
        if qdate.isValid():
            return qdate

        # 3. dd-MM-yyyy
        qdate = QDate.fromString(tekst, "dd-MM-yyyy")
        if qdate.isValid():
            return qdate

        # 4. yyyy-MM → dag 1
        if len(tekst) == 7 and tekst[4] == "-":
            jaar_str, maand_str = tekst.split("-", 1)
            try:
                jaar = int(jaar_str)
                maand = int(maand_str)
            except ValueError:
                return QDate()
            if 1 <= maand <= 12:
                qdate = QDate(jaar, maand, 1)
                if qdate.isValid():
                    return qdate

        # 5. yyyy → 1 januari
        if len(tekst) == 4 and tekst.isdigit():
            try:
                jaar = int(tekst)
            except ValueError:
                return QDate()
            qdate = QDate(jaar, 1, 1)
            if qdate.isValid():
                return qdate

        return QDate()

    # ---------------------------------------------------------------- UI

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.header_label = QLabel()
        self.header_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.header_label)

        self.subtitle_label = QLabel()
        self.subtitle_label.setStyleSheet("color: #AAAAAA;")
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)

        form = QFormLayout()

        self.title_label_field = QLabel()
        self.title_edit = QLineEdit()
        self.title_edit.textEdited.connect(self._on_titel_bewerkt)
        form.addRow(self.title_label_field, self.title_edit)

        self.categorie_label = QLabel()
        self.categorie_combo = QComboBox()
        form.addRow(self.categorie_label, self.categorie_combo)

        self.fabrikant_label = QLabel()
        self.fabrikant_edit = QLineEdit()
        self.fabrikant_edit.textEdited.connect(
            lambda _t: naar_uppercase(self.fabrikant_edit)
        )
        form.addRow(self.fabrikant_label, self.fabrikant_edit)

        self.serie_label = QLabel()
        self.serie_edit = QLineEdit()
        self.serie_edit.textEdited.connect(
            lambda _t: naar_uppercase(self.serie_edit)
        )
        form.addRow(self.serie_label, self.serie_edit)

        self.partnummer_label = QLabel()
        self.partnummer_edit = QLineEdit()
        self.partnummer_edit.textEdited.connect(
            lambda _t: naar_uppercase(self.partnummer_edit)
        )
        form.addRow(self.partnummer_label, self.partnummer_edit)

        self.documentversie_label = QLabel()
        self.documentversie_edit = QLineEdit()
        self.documentversie_edit.textEdited.connect(
            lambda _t: naar_uppercase(self.documentversie_edit)
        )
        form.addRow(
            self.documentversie_label, self.documentversie_edit
        )

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
        form.addRow(self.documentdatum_label, datum_widget)

        self.notities_label = QLabel()
        self.notities_edit = QLineEdit()
        form.addRow(self.notities_label, self.notities_edit)

        layout.addLayout(form)
        layout.addStretch()

        self._datum_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        self._datum_shortcut.activated.connect(self._zet_datum_op_vandaag)

        button_row = QHBoxLayout()
        button_row.addStretch()
        self.cancel_btn = QPushButton()
        self.cancel_btn.clicked.connect(self.reject)
        button_row.addWidget(self.cancel_btn)
        self.save_btn = QPushButton()
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self._save)
        button_row.addWidget(self.save_btn)
        layout.addLayout(button_row)

    def _apply_language(self) -> None:
        self.setWindowTitle(self._t("documentatie.bewerken_titel"))
        self.header_label.setText(self._t("documentatie.bewerken_titel"))
        self.subtitle_label.setText(
            self._t("documentatie.bewerken_subtitel")
        )
        self.title_label_field.setText(
            self._t("documentatie.import.veld_titel")
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
        self.cancel_btn.setText(
            self._t("documentatie.bewerken_annuleren")
        )
        self.save_btn.setText(self._t("documentatie.bewerken_opslaan"))

    # ---------------------------------------------------------------- data

    def _laad_bestaande_metadata(self) -> None:
        """Vul de velden met de bestaande waarden van de bron.

        Wordt aangeroepen nadat _apply_language de labels en de dropdown
        heeft gezet, zodat de categorie-selectie correct kan worden gezet.
        """
        self.title_edit.setText(self.bron.title)

        ruwe_categorie = self.bron.category
        if isinstance(ruwe_categorie, str) and ruwe_categorie.strip():
            gezocht = ruwe_categorie.strip().upper()
        else:
            gezocht = DocumentCategory.DATASHEET.value
        idx = self.categorie_combo.findData(gezocht)
        self.categorie_combo.setCurrentIndex(idx if idx >= 0 else 0)

        self.fabrikant_edit.setText(self.bron.manufacturer or "")
        self.serie_edit.setText(self.bron.series or "")
        self.partnummer_edit.setText(self.bron.part_number or "")
        self.documentversie_edit.setText(self.bron.document_version or "")
        self.notities_edit.setText(self.bron.notes or "")

        # Datum: probeer de ruwe string via _parse_datum_naar_qdate.
        # Lukt dat niet, dan "Datum onbekend" aanvinken.
        ruwe_datum = self.bron.document_date
        qdate = QDate()
        if isinstance(ruwe_datum, str) and ruwe_datum.strip():
            qdate = self._parse_datum_naar_qdate(ruwe_datum)

        if qdate.isValid():
            self.documentdatum_edit.setDate(qdate)
            with QSignalBlocker(self.datum_onbekend_checkbox):
                self.datum_onbekend_checkbox.setChecked(False)
            self.documentdatum_edit.setEnabled(True)
        else:
            with QSignalBlocker(self.datum_onbekend_checkbox):
                self.datum_onbekend_checkbox.setChecked(True)
            self.documentdatum_edit.setEnabled(False)

        self._update_save_state()

    # ---------------------------------------------------------------- opslaan

    def _save(self) -> None:
        titel = self.title_edit.text().strip()
        if not titel:
            return

        try:
            result = self.import_service.update_metadata(
                self.bron.source_id,
                title=titel,
                category=self._huidige_categorie(),
                manufacturer=self.fabrikant_edit.text(),
                series=self.serie_edit.text(),
                part_number=self.partnummer_edit.text(),
                document_version=self.documentversie_edit.text(),
                document_date=self._documentdatum_waarde(),
                notes=self.notities_edit.text(),
            )
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

        self.metadata_saved.emit(result.source.source_id)
        self.accept()

    def _zet_eigen_icoon(self) -> None:
        try:
            from app.helpers.icon_paths import zet_venster_icoon
            zet_venster_icoon(self)
        except Exception:
            pass