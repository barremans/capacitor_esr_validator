"""
================================================================================
Module:     app/gui/dialogs/bulk_edit_metadata_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-20
Auteur:     Bart Bossuyt

Doel:       Modale dialoog om de metadata van meerdere eigen imports in
            één keer te wijzigen. Elke metadata-rij heeft een eigen
            checkbox "Wijzigen"; alleen aangevinkte velden worden
            meegestuurd naar ImportService.update_metadata. Lege
            aangevinkte velden betekenen expliciet leegmaken.

            De dialoog wijzigt niets zelf: hij levert een dict met
            (veldnaam -> waarde) en een lijst source_ids aan de
            aanroeper. De aanroeper (DocumentationScreen) voert de
            GUI-loop uit over ImportService.update_metadata.

            De ingebouwde catalogus is read-only. Deze dialoog wordt
            alleen getoond voor een selectie die minstens één
            gebruikersimport bevat; de aanroeper filtert de lijst al
            vóór het openen.

Wijzigingen:
  v1.0.0 (2026-10-20)  Eerste versie (fase 11F.3). Analoog aan
                       EditMetadataDialog, maar met een checkbox per
                       veld en een lijst van te wijzigen bronnen.
================================================================================
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QDate, Qt
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


class BulkEditMetadataDialog(QDialog):
    """Modale editor voor de metadata van meerdere eigen imports.

    Levert via ``resultaat`` een dict met alleen de aangevinkte velden,
    plus de lijst source_ids. De aanroeper voert de bulk-update uit.
    """

    def __init__(
        self,
        *,
        bronnen: list[ImportSource],
        taal: str = "nl_NL",
        import_service: Optional[ImportService] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        if not bronnen:
            raise ValueError("BulkEditMetadataDialog vereist minstens één bron")
        self.taal = taal
        self.bronnen = list(bronnen)
        self.import_service = import_service or ImportService()

        # Resultaat: pas gezet bij accept(). De aanroeper leest dit.
        self.resultaat: Optional[dict] = None

        self.setModal(True)
        self.resize(620, 620)
        self.setMinimumSize(520, 560)
        self._zet_eigen_icoon()

        self._build_ui()
        self._apply_language()
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

    def _update_save_state(self) -> None:
        """Opslaan alleen actief als minstens één veld is aangevinkt."""
        self.save_btn.setEnabled(self._heeft_minstens_een_veld())

    def _heeft_minstens_een_veld(self) -> bool:
        return any(
            checkbox.isChecked()
            for checkbox in (
                self.titel_check,
                self.categorie_check,
                self.fabrikant_check,
                self.serie_check,
                self.partnummer_check,
                self.documentversie_check,
                self.documentdatum_check,
                self.notities_check,
            )
        )

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

        # Titel
        self.titel_check = QCheckBox()
        self.title_edit = QLineEdit()
        self.title_edit.setEnabled(False)
        self.titel_check.toggled.connect(self.title_edit.setEnabled)
        self.titel_check.toggled.connect(self._update_save_state)
        self.title_edit.textEdited.connect(self._update_save_state)
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.addWidget(self.title_edit, 1)
        title_row.addWidget(self.titel_check)
        title_widget = QWidget()
        title_widget.setLayout(title_row)
        self.title_label_field = QLabel()
        form.addRow(self.title_label_field, title_widget)

        # Categorie
        self.categorie_check = QCheckBox()
        self.categorie_combo = QComboBox()
        self.categorie_combo.setEnabled(False)
        self.categorie_check.toggled.connect(self.categorie_combo.setEnabled)
        self.categorie_check.toggled.connect(self._update_save_state)
        cat_row = QHBoxLayout()
        cat_row.setContentsMargins(0, 0, 0, 0)
        cat_row.addWidget(self.categorie_combo, 1)
        cat_row.addWidget(self.categorie_check)
        cat_widget = QWidget()
        cat_widget.setLayout(cat_row)
        self.categorie_label = QLabel()
        form.addRow(self.categorie_label, cat_widget)

        # Fabrikant
        self.fabrikant_check = QCheckBox()
        self.fabrikant_edit = QLineEdit()
        self.fabrikant_edit.setEnabled(False)
        self.fabrikant_check.toggled.connect(self.fabrikant_edit.setEnabled)
        self.fabrikant_check.toggled.connect(self._update_save_state)
        self.fabrikant_edit.textEdited.connect(
            lambda _t: naar_uppercase(self.fabrikant_edit)
        )
        self.fabrikant_label = QLabel()
        form.addRow(
            self._checkbox_rij(self.fabrikant_label, self.fabrikant_check),
            self.fabrikant_edit,
        )

        # Serie
        self.serie_check = QCheckBox()
        self.serie_edit = QLineEdit()
        self.serie_edit.setEnabled(False)
        self.serie_check.toggled.connect(self.serie_edit.setEnabled)
        self.serie_check.toggled.connect(self._update_save_state)
        self.serie_edit.textEdited.connect(
            lambda _t: naar_uppercase(self.serie_edit)
        )
        self.serie_label = QLabel()
        form.addRow(
            self._checkbox_rij(self.serie_label, self.serie_check),
            self.serie_edit,
        )

        # Partnummer
        self.partnummer_check = QCheckBox()
        self.partnummer_edit = QLineEdit()
        self.partnummer_edit.setEnabled(False)
        self.partnummer_check.toggled.connect(self.partnummer_edit.setEnabled)
        self.partnummer_check.toggled.connect(self._update_save_state)
        self.partnummer_edit.textEdited.connect(
            lambda _t: naar_uppercase(self.partnummer_edit)
        )
        self.partnummer_label = QLabel()
        form.addRow(
            self._checkbox_rij(self.partnummer_label, self.partnummer_check),
            self.partnummer_edit,
        )

        # Documentversie
        self.documentversie_check = QCheckBox()
        self.documentversie_edit = QLineEdit()
        self.documentversie_edit.setEnabled(False)
        self.documentversie_check.toggled.connect(
            self.documentversie_edit.setEnabled
        )
        self.documentversie_check.toggled.connect(self._update_save_state)
        self.documentversie_edit.textEdited.connect(
            lambda _t: naar_uppercase(self.documentversie_edit)
        )
        self.documentversie_label = QLabel()
        form.addRow(
            self._checkbox_rij(self.documentversie_label, self.documentversie_check),
            self.documentversie_edit,
        )

        # Documentdatum
        self.documentdatum_check = QCheckBox()
        self.documentdatum_edit = QDateEdit()
        self.documentdatum_edit.setCalendarPopup(True)
        self.documentdatum_edit.setDisplayFormat("yyyy-MM-dd")
        self.documentdatum_edit.setDate(QDate.currentDate())
        self.documentdatum_edit.setEnabled(False)
        self.documentdatum_check.toggled.connect(
            self.documentdatum_edit.setEnabled
        )
        self.documentdatum_check.toggled.connect(self._update_save_state)
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
        self.documentdatum_label = QLabel()
        form.addRow(
            self._checkbox_rij(self.documentdatum_label, self.documentdatum_check),
            datum_widget,
        )

        # Notities
        self.notities_check = QCheckBox()
        self.notities_edit = QLineEdit()
        self.notities_edit.setEnabled(False)
        self.notities_check.toggled.connect(self.notities_edit.setEnabled)
        self.notities_check.toggled.connect(self._update_save_state)
        self.notities_label = QLabel()
        form.addRow(
            self._checkbox_rij(self.notities_label, self.notities_check),
            self.notities_edit,
        )

        layout.addLayout(form)
        layout.addStretch()

        # Knoppen
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

    @staticmethod
    def _checkbox_rij(label: QLabel, checkbox: QCheckBox) -> QWidget:
        """Helper: label + checkbox naast elkaar als formulierlabel."""
        rij = QWidget()
        lay = QHBoxLayout(rij)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(label)
        lay.addStretch()
        lay.addWidget(checkbox)
        return rij

    def _apply_language(self) -> None:
        self.setWindowTitle(self._t("documentatie.bulk_edit.titel"))
        self.header_label.setText(self._t("documentatie.bulk_edit.titel"))
        self.subtitle_label.setText(
            self._t(
                "documentatie.bulk_edit_subtitel",
                aantal=len(self.bronnen),
            )
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
        self.notities_label.setText(
            self._t("documentatie.import.veld_notities")
        )
        self.datum_onbekend_checkbox.setText(
            self._t("documentatie.import.veld_documentdatum_onbekend")
        )
        for checkbox in (
            self.titel_check,
            self.categorie_check,
            self.fabrikant_check,
            self.serie_check,
            self.partnummer_check,
            self.documentversie_check,
            self.documentdatum_check,
            self.notities_check,
        ):
            checkbox.setText(self._t("documentatie.bulk_edit.wijzigen"))
            checkbox.setToolTip(
                self._t("documentatie.bulk_edit.wijzigen_tooltip")
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
        self.cancel_btn.setText(self._t("documentatie.bulk_edit.annuleren"))
        self.save_btn.setText(self._t("documentatie.bulk_edit.opslaan"))

    # ---------------------------------------------------------------- opslaan

    def _verzamel_wijzigingen(self) -> dict:
        """Bouw een dict met alleen de aangevinkte velden."""
        wijzigingen: dict = {}
        if self.titel_check.isChecked():
            wijzigingen["title"] = self.title_edit.text()
        if self.categorie_check.isChecked():
            wijzigingen["category"] = self._huidige_categorie()
        if self.fabrikant_check.isChecked():
            wijzigingen["manufacturer"] = self.fabrikant_edit.text()
        if self.serie_check.isChecked():
            wijzigingen["series"] = self.serie_edit.text()
        if self.partnummer_check.isChecked():
            wijzigingen["part_number"] = self.partnummer_edit.text()
        if self.documentversie_check.isChecked():
            wijzigingen["document_version"] = self.documentversie_edit.text()
        if self.documentdatum_check.isChecked():
            wijzigingen["document_date"] = self._documentdatum_waarde()
        if self.notities_check.isChecked():
            wijzigingen["notes"] = self.notities_edit.text()
        return wijzigingen

    def _save(self) -> None:
        wijzigingen = self._verzamel_wijzigingen()
        if not wijzigingen:
            # Zou niet moeten kunnen (knop disabled), maar defensief.
            return

        # Titel mag niet leeg zijn (ImportSource-validatie). Als de
        # gebruiker de titel-check aanvinkt maar leeg laat, weigeren we
        # de hele actie met een duidelijke melding.
        if "title" in wijzigingen and not str(wijzigingen["title"]).strip():
            QMessageBox.warning(
                self,
                self._t("documentatie.bulk_edit.fout_titel"),
                self._t("documentatie.bulk_edit.titel_leeg"),
            )
            return

        self.resultaat = {
            "source_ids": [b.source_id for b in self.bronnen],
            "wijzigingen": wijzigingen,
        }
        self.accept()

    def _zet_eigen_icoon(self) -> None:
        try:
            from app.helpers.icon_paths import zet_venster_icoon
            zet_venster_icoon(self)
        except Exception:
            pass