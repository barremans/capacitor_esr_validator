"""
================================================================================
Module:     app/gui/dialogs/change_status_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.2.0
Datum:      2026-10-19
Auteur:     Bart Bossuyt

Doel:       Modale dialoog waarmee de gebruiker de status van een eigen
            import kan wijzigen. Toont alleen de toegelaten overgangen
            (concept → actief → gearchiveerd, en terug) op basis van
            ImportStatus en _ALLOWED_TRANSITIONS uit import_models.
            Roept ImportService.set_status of ImportService.archive aan.
            De bron en de metadata blijven ongewijzigd; alleen de
            levenscyclus verandert.

            Sinds 11F.1 kan de gebruiker bij archiveren een optionele
            reden opgeven. Die reden wordt opgeslagen in archive_reason
            en blijft bewaard bij een latere revoke.

            De ingebouwde catalogus is read-only. Deze dialoog wordt
            alleen getoond voor documenten met is_user_import=True.

Wijzigingen:
  v1.0.0 (2026-10-08)  Eerste versie (fase 5D'.2e). Analoog aan
                       EditMetadataDialog, maar dan voor de status.
                       Bevestigingsvraag bij archiveren en bij terug
                       naar Concept; niet bij activeren.
  v1.1.0 (2026-10-16)  Fase 11C: dialoog krijgt een venstericoon via
                        de centrale helper app/helpers/icon_paths.
                        Geen wijziging aan de statuslogica.
  v1.2.0 (2026-10-19)  Fase 11F.1: optioneel redenveld bij archiveren.
                        Het veld is alleen zichtbaar als de doelstatus
                        GEARCHIVEERD is. Bij archiveren roept de dialoog
                        ImportService.archive(reason=...) aan; bij
                        andere overgangen blijft set_status gebruikt
                        worden.
================================================================================
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
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
    _ALLOWED_TRANSITIONS,
    ImportSource,
    ImportStatus,
    ImportValidationError,
)
from app.documentation.import_service import ImportService
from app.helpers.i18n import vertaal


class ChangeStatusDialog(QDialog):
    """Modale editor voor de status van één eigen import."""

    status_changed = Signal(str)  # source_id

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
        self.resize(480, 380)
        self.setMinimumSize(420, 320)
        self._zet_eigen_icoon()

        self._build_ui()
        self._apply_language()
        self._laad_toegelaten_overgangen()
        self._update_save_state()
        self._update_reden_zichtbaarheid()

    # ---------------------------------------------------------------- helpers

    def _t(self, sleutel: str, **kwargs) -> str:
        return vertaal(sleutel, taal=self.taal, **kwargs)

    def _status_label(self, status: ImportStatus) -> str:
        return self._t(f"documentatie.status_kolom.{status.value}")

    def _toegelaten_doelwitten(self) -> tuple[ImportStatus, ...]:
        """Lees de toegelaten nieuwe statussen uit _ALLOWED_TRANSITIONS.

        Sorteert stabiel op de volgorde uit de enum, zodat de dropdown
        deterministisch is.
        """
        toegelaten = _ALLOWED_TRANSITIONS.get(self.bron.status, frozenset())
        return tuple(
            status
            for status in ImportStatus
            if status in toegelaten
        )

    def _huidige_selectie(self) -> Optional[ImportStatus]:
        data = self.status_combo.currentData()
        if data is None:
            return None
        try:
            return ImportStatus(str(data))
        except ValueError:
            return None

    def _update_save_state(self) -> None:
        self.save_btn.setEnabled(self._huidige_selectie() is not None)

    def _update_reden_zichtbaarheid(self) -> None:
        """Toon het redenveld alleen als de doelstatus GEARCHIVEERD is."""
        toon = self._huidige_selectie() is ImportStatus.GEARCHIVEERD
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

        self.huidige_label = QLabel()
        self.huidige_value = QLabel()
        self.huidige_value.setStyleSheet("font-weight: bold;")
        form.addRow(self.huidige_label, self.huidige_value)

        self.nieuwe_label = QLabel()
        self.status_combo = QComboBox()
        self.status_combo.currentIndexChanged.connect(
            lambda _i: self._on_status_combo_changed()
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

    def _on_status_combo_changed(self) -> None:
        self._update_save_state()
        self._update_reden_zichtbaarheid()

    def _apply_language(self) -> None:
        self.setWindowTitle(self._t("documentatie.status_wijzigen_titel"))
        self.header_label.setText(self._t("documentatie.status_wijzigen_titel"))
        self.subtitle_label.setText(
            self._t("documentatie.status_wijzigen_subtitel")
        )
        self.huidige_label.setText(
            self._t("documentatie.status_wijzigen_huidige")
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
        self.huidige_value.setText(self._status_label(self.bron.status))
        self.cancel_btn.setText(
            self._t("documentatie.status_wijzigen_annuleren")
        )
        self.save_btn.setText(self._t("documentatie.status_wijzigen_opslaan"))

    def _laad_toegelaten_overgangen(self) -> None:
        """Vul de dropdown met de toegelaten nieuwe statussen."""
        self.status_combo.blockSignals(True)
        try:
            self.status_combo.clear()
            for status in self._toegelaten_doelwitten():
                self.status_combo.addItem(
                    self._status_label(status), status.value
                )
            if self.status_combo.count() > 0:
                self.status_combo.setCurrentIndex(0)
        finally:
            self.status_combo.blockSignals(False)

    # ---------------------------------------------------------------- opslaan

    def _bevestig(self, nieuwe_status: ImportStatus) -> bool:
        """Toon een bevestigingsvraag voor ingrijpende overgangen.

        Geen bevestiging voor CONCEPT → ACTIEF. Wel voor:
        - ACTIEF → GEARCHIVEERD
        - CONCEPT → GEARCHIVEERD
        - GEARCHIVEERD → CONCEPT
        - ACTIEF → CONCEPT
        """
        if nieuwe_status is ImportStatus.ACTIEF:
            return True

        if nieuwe_status is ImportStatus.GEARCHIVEERD:
            tekst = self._t(
                "documentatie.status_wijzigen_bevestiging_archiveren"
            )
        else:  # CONCEPT
            tekst = self._t(
                "documentatie.status_wijzigen_bevestiging_terug"
            )

        antwoord = QMessageBox.question(
            self,
            self._t("documentatie.status_wijzigen_titel"),
            tekst,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return antwoord == QMessageBox.StandardButton.Yes

    def _save(self) -> None:
        nieuwe_status = self._huidige_selectie()
        if nieuwe_status is None:
            return

        if not self._bevestig(nieuwe_status):
            return

        try:
            if nieuwe_status is ImportStatus.GEARCHIVEERD:
                reden = self.reden_edit.text()
                result = self.import_service.archive(
                    self.bron.source_id, reason=reden or None
                )
            else:
                result = self.import_service.set_status(
                    self.bron.source_id, nieuwe_status
                )
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

        self.status_changed.emit(result.source.source_id)
        self.accept()

    def _zet_eigen_icoon(self) -> None:
        try:
            from app.helpers.icon_paths import zet_venster_icoon
            zet_venster_icoon(self)
        except Exception:
            pass