"""
================================================================================
Module:     app/gui/dialogs/duplicate_source_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-07
Auteur:     Bart Bossuyt

Doel:       Modale popup die de gebruiker bij een bestaande bron drie
            keuzes voorlegt: Behouden / Nieuwe versie toevoegen /
            Overschrijven (fase 5D'.2a). Geeft de keuze terug als
            DuplicateAction, of None bij annuleren. Geen services, geen
            I/O — alleen presentatie.

Wijzigingen:
  v1.0.0 (2026-10-07)  Eerste versie: drie radio-opties, samenvatting
                       van de bestaande bron, keuze via exec().
================================================================================
"""

from __future__ import annotations

import time
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.documentation.import_models import (
    DuplicateAction,
    DuplicateMatch,
    ImportStatus,
)
from app.helpers.i18n import vertaal


class DuplicateSourceDialog(QDialog):
    """Popup voor een bestaande bron bij import.

    Retourneert via exec() een int (QDialog.Accepted / QDialog.Rejected).
    De gekozen DuplicateAction is op te vragen via .gekozen_actie.
    """

    def __init__(
        self,
        *,
        match: DuplicateMatch,
        taal: str = "nl_NL",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.match = match
        self.taal = taal
        self.gekozen_actie: Optional[DuplicateAction] = None

        self.setModal(True)
        self.resize(560, 420)
        self.setMinimumSize(480, 360)

        self._build_ui()
        self._apply_language()
        self._update_state()

    # ---------------------------------------------------------------- helpers

    def _t(self, sleutel: str, **kwargs) -> str:
        return vertaal(sleutel, taal=self.taal, **kwargs)

    def _status_tekst(self, status: ImportStatus) -> str:
        if status is ImportStatus.CONCEPT:
            return self._t("documentatie.import.duplicate.status_concept")
        if status is ImportStatus.ACTIEF:
            return self._t("documentatie.import.duplicate.status_actief")
        if status is ImportStatus.GEARCHIVEERD:
            return self._t(
                "documentatie.import.duplicate.status_gearchiveerd"
            )
        return status.value

    def _format_datum(self, imported_at_ms: int) -> str:
        """Formatteer Unix-ms naar lokale datum-tijd, leesbaar voor mensen."""
        try:
            struct = time.localtime(imported_at_ms / 1000)
            return time.strftime("%Y-%m-%d %H:%M", struct)
        except (OverflowError, OSError, ValueError):
            return str(imported_at_ms)

    def _match_type_tekst(self) -> str:
        if self.match.match_type == "file_hash":
            return self._t("documentatie.import.duplicate.match_type_bestand")
        return self._t("documentatie.import.duplicate.match_type_url")

    # ---------------------------------------------------------------- UI

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Titel
        self.title_label = QLabel()
        self.title_label.setStyleSheet(
            "font-size: 16px; font-weight: bold;"
        )
        layout.addWidget(self.title_label)

        # Bestaande-bron-samenvatting
        self.info_browser = QTextBrowser()
        self.info_browser.setMinimumHeight(120)
        self.info_browser.setStyleSheet(
            "QTextBrowser { background-color:#252525; color:#F0F0F0; "
            "border:1px solid #4A4A4A; padding:8px; }"
        )
        layout.addWidget(self.info_browser, 1)

        # Drie radio-opties
        self.radio_behouden = QRadioButton()
        self.radio_nieuwe_versie = QRadioButton()
        self.radio_overschrijven = QRadioButton()

        self.actie_group = QButtonGroup(self)
        self.actie_group.addButton(self.radio_behouden)
        self.actie_group.addButton(self.radio_nieuwe_versie)
        self.actie_group.addButton(self.radio_overschrijven)

        # Standaard: Behouden (veiligste optie).
        self.radio_behouden.setChecked(True)

        self.radio_behouden.toggled.connect(self._update_state)
        self.radio_nieuwe_versie.toggled.connect(self._update_state)
        self.radio_overschrijven.toggled.connect(self._update_state)

        layout.addWidget(self.radio_behouden)
        layout.addWidget(self.radio_nieuwe_versie)
        layout.addWidget(self.radio_overschrijven)

        # Detailtekst onder de opties (klein, grijs)
        self.detail_label = QLabel()
        self.detail_label.setWordWrap(True)
        self.detail_label.setStyleSheet("color: #AAAAAA; font-size: 11px;")
        layout.addWidget(self.detail_label)

        # Knoppen
        button_row = QHBoxLayout()
        button_row.addStretch()
        self.cancel_btn = QPushButton()
        self.cancel_btn.clicked.connect(self.reject)
        button_row.addWidget(self.cancel_btn)
        self.ok_btn = QPushButton()
        self.ok_btn.clicked.connect(self._accept)
        self.ok_btn.setDefault(True)
        button_row.addWidget(self.ok_btn)
        layout.addLayout(button_row)

    def _apply_language(self) -> None:
        self.setWindowTitle(self._t("documentatie.import.duplicate.titel"))
        self.title_label.setText(self._t("documentatie.import.duplicate.titel"))

        # Samenvatting van de bestaande bron
        b = self.match.bestaande
        regels = [
            f"<b>{self._t('documentatie.import.duplicate.match_type_label')}:</b> "
            f"{self._match_type_tekst()}",
            f"<b>{self._t('documentatie.import.duplicate.bestaande_titel')}:</b> "
            f"{b.title}",
            f"<b>{self._t('documentatie.import.duplicate.bestaande_status')}:</b> "
            f"{self._status_tekst(b.status)}",
            f"<b>{self._t('documentatie.import.duplicate.bestaande_datum')}:</b> "
            f"{self._format_datum(b.imported_at)}",
        ]
        if b.source_url:
            regels.append(
                f"<b>{self._t('documentatie.import.duplicate.bestaande_url')}:</b> "
                f"{b.source_url}"
            )
        if b.original_filename:
            regels.append(
                f"<b>{self._t('documentatie.import.duplicate.bestaande_bestand')}:</b> "
                f"{b.original_filename}"
            )
        self.info_browser.setHtml("<br>".join(regels))

        self.radio_behouden.setText(
            self._t("documentatie.import.duplicate.optie_behouden")
        )
        self.radio_nieuwe_versie.setText(
            self._t("documentatie.import.duplicate.optie_nieuwe_versie")
        )
        self.radio_overschrijven.setText(
            self._t("documentatie.import.duplicate.optie_overschrijven")
        )
        self.cancel_btn.setText(
            self._t("documentatie.import.duplicate.annuleren")
        )
        self.ok_btn.setText(
            self._t("documentatie.import.duplicate.doorgaan")
        )
        self._update_state()

    # ---------------------------------------------------------------- events

    def _update_state(self) -> None:
        if self.radio_behouden.isChecked():
            self.detail_label.setText(
                self._t("documentatie.import.duplicate.detail_behouden")
            )
        elif self.radio_nieuwe_versie.isChecked():
            self.detail_label.setText(
                self._t(
                    "documentatie.import.duplicate.detail_nieuwe_versie"
                )
            )
        elif self.radio_overschrijven.isChecked():
            self.detail_label.setText(
                self._t(
                    "documentatie.import.duplicate.detail_overschrijven"
                )
            )

    def _accept(self) -> None:
        if self.radio_behouden.isChecked():
            self.gekozen_actie = DuplicateAction.KEEP
        elif self.radio_nieuwe_versie.isChecked():
            self.gekozen_actie = DuplicateAction.NEW_VERSION
        elif self.radio_overschrijven.isChecked():
            self.gekozen_actie = DuplicateAction.OVERWRITE
        else:
            # Geen radio actief: zou niet mogen met een default-checked.
            return
        self.accept()

    # ---------------------------------------------------------------- publiek

    @staticmethod
    def vraag_actie(
        *,
        match: DuplicateMatch,
        taal: str = "nl_NL",
        parent: Optional[QWidget] = None,
    ) -> Optional[DuplicateAction]:
        """Toon de popup modaal en geef de gekozen actie terug.

        Retourneert None als de gebruiker annuleert.
        """
        dialog = DuplicateSourceDialog(match=match, taal=taal, parent=parent)
        resultaat = dialog.exec()
        if resultaat == QDialog.Accepted:
            return dialog.gekozen_actie
        return None