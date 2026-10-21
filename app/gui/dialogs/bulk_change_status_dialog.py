"""
================================================================================
Module:     app/gui/dialogs/bulk_change_status_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-20
Auteur:     Bart Bossuyt

Doel:       Modale dialoog om de status van meerdere eigen imports in
            één keer te wijzigen. De gebruiker kiest één doelstatus
            (concept / actief / gearchiveerd) en optioneel een reden
            bij archiveren. De aanroeper voert de GUI-loop uit over
            ImportService.set_status of ImportService.archive.

            Anders dan ChangeStatusDialog toont deze dialoog geen
            "huidige status" per rij: de selectie kan bronnen met
            verschillende huidige statussen bevatten. De gebruiker kiest
            de doelstatus; rijen waarvan de overgang niet is toegelaten
            worden door de aanroeper als "overgeslagen" geteld.

Wijzigingen:
  v1.0.0 (2026-10-20)  Eerste versie (fase 11F.3). Analoog aan
                       ChangeStatusDialog, maar met een vaste
                       doelstatus-keuze en een lijst van te wijzigen
                       bronnen.
================================================================================
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
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
    ImportStatus,
)
from app.documentation.import_service import ImportService
from app.helpers.i18n import vertaal


class BulkChangeStatusDialog(QDialog):
    """Modale editor voor de status van meerdere eigen imports.

    Levert via ``resultaat`` een dict met de gekozen doelstatus en
    (bij archiveren) de optionele reden. De aanroeper voert de
    bulk-update uit.
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
            raise ValueError(
                "BulkChangeStatusDialog vereist minstens één bron"
            )
        self.taal = taal
        self.bronnen = list(bronnen)
        self.import_service = import_service or ImportService()

        # Resultaat: pas gezet bij accept(). De aanroeper leest dit.
        self.resultaat: Optional[dict] = None

        self.setModal(True)
        self.resize(500, 340)
        self.setMinimumSize(440, 300)
        self._zet_eigen_icoon()

        self._build_ui()
        self._apply_language()
        self._update_reden_zichtbaarheid()

    # ---------------------------------------------------------------- helpers

    def _t(self, sleutel: str, **kwargs) -> str:
        return vertaal(sleutel, taal=self.taal, **kwargs)

    def _status_label(self, status: ImportStatus) -> str:
        return self._t(f"documentatie.status_kolom.{status.value}")

    def _huidige_doelstatus(self) -> ImportStatus:
        data = self.status_combo.currentData()
        if data is None:
            return ImportStatus.CONCEPT
        try:
            return ImportStatus(str(data))
        except ValueError:
            return ImportStatus.CONCEPT

    def _update_reden_zichtbaarheid(self) -> None:
        toon = self._huidige_doelstatus() is ImportStatus.GEARCHIVEERD
        self.reden_label.setVisible(toon)
        self.reden_edit.setVisible(toon)

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

        self.nieuwe_label = QLabel()
        self.status_combo = QComboBox()
        self.status_combo.currentIndexChanged.connect(
            lambda _i: self._update_reden_zichtbaarheid()
        )
        form.addRow(self.nieuwe_label, self.status_combo)

        self.reden_label = QLabel()
        self.reden_edit = QLineEdit()
        form.addRow(self.reden_label, self.reden_edit)

        layout.addLayout(form)
        layout.addStretch()

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
        self.setWindowTitle(self._t("documentatie.bulk_status.titel"))
        self.header_label.setText(self._t("documentatie.bulk_status.titel"))
        self.subtitle_label.setText(
            self._t(
                "documentatie.bulk_status_subtitel",
                aantal=len(self.bronnen),
            )
        )
        self.nieuwe_label.setText(
            self._t("documentatie.status_wijzigen_nieuwe")
        )
        self.reden_label.setText(
            self._t("documentatie.status_wijzigen_reden.reden_label")
        )
        self.reden_edit.setPlaceholderText(
            self._t("documentatie.status_wijzigen_reden.reden_placeholder")
        )
        self.reden_edit.setToolTip(
            self._t("documentatie.status_wijzigen_reden.reden_tooltip")
        )
        # Dropdown vullen: drie mogelijke doelstatussen.
        self.status_combo.blockSignals(True)
        try:
            self.status_combo.clear()
            for status in ImportStatus:
                self.status_combo.addItem(
                    self._status_label(status), status.value
                )
            self.status_combo.setCurrentIndex(0)
        finally:
            self.status_combo.blockSignals(False)
        self.cancel_btn.setText(self._t("documentatie.bulk_status.annuleren"))
        self.save_btn.setText(self._t("documentatie.bulk_status.opslaan"))

    # ---------------------------------------------------------------- opslaan

    def _bevestig(self, doelstatus: ImportStatus) -> bool:
        """Toon één bevestigingsvraag voor de hele batch.

        Geen bevestiging voor doelstatus ACTIEF. Wel voor CONCEPT en
        GEARCHIVEERD.
        """
        if doelstatus is ImportStatus.ACTIEF:
            return True

        if doelstatus is ImportStatus.GEARCHIVEERD:
            tekst = self._t(
                "documentatie.bulk_status.bevestiging_archiveren",
                aantal=len(self.bronnen),
            )
        else:
            tekst = self._t(
                "documentatie.bulk_status.bevestiging_concept",
                aantal=len(self.bronnen),
            )

        antwoord = QMessageBox.question(
            self,
            self._t("documentatie.bulk_status.titel"),
            tekst,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return antwoord == QMessageBox.StandardButton.Yes

    def _save(self) -> None:
        doelstatus = self._huidige_doelstatus()

        if not self._bevestig(doelstatus):
            return

        reden = None
        if doelstatus is ImportStatus.GEARCHIVEERD:
            tekst = self.reden_edit.text()
            reden = tekst if tekst.strip() else None

        self.resultaat = {
            "source_ids": [b.source_id for b in self.bronnen],
            "doelstatus": doelstatus,
            "reason": reden,
        }
        self.accept()

    def _zet_eigen_icoon(self) -> None:
        try:
            from app.helpers.icon_paths import zet_venster_icoon
            zet_venster_icoon(self)
        except Exception:
            pass