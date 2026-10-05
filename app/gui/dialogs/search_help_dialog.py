"""
================================================================================
Module:     app/gui/dialogs/search_help_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-05
Auteur:     Bart Bossuyt

Doel:       Modale read-only help-dialoog voor de documentatie-zoektaal.

            Toont de gebruikersuitleg over de zoekoperatoren (spatie/comma,
            pijp, prefix-min, prefix-bang, wildcard-procent). De inhoud komt
            uit i18n-keys onder 'documentatie.help.*'.

            Deze dialoog bevat geen zoeklogica, geen service en geen
            documentmetadata. Hij toont alleen de uitleg.

Wijzigingen:
  v1.0.0 (2026-10-05)  Eerste versie met i18n-gestuurde help-inhoud.
================================================================================
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.helpers.i18n import vertaal


class SearchHelpDialog(QDialog):
    """Read-only help-dialoog voor de documentatie-zoektaal."""

    def __init__(
        self,
        taal: str = "nl_NL",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.taal = taal
        self._build_ui()
        self._apply_content()

    def _t(self, sleutel: str, **kwargs) -> str:
        return vertaal(sleutel, taal=self.taal, **kwargs)

    def _build_ui(self) -> None:
        self.setModal(True)
        self.resize(680, 620)
        self.setMinimumSize(520, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setReadOnly(True)
        self.browser.setStyleSheet(
            "QTextBrowser { background-color: #1E1E1E; color: #F0F0F0; "
            "border: 1px solid #4A4A4A; padding: 12px; }"
        )
        self.browser.document().setDefaultStyleSheet(
            "body { color: #F0F0F0; background-color: #1E1E1E; "
            "font-family: 'Segoe UI'; font-size: 10.5pt; line-height: 1.4; } "
            "h1 { color: #FFFFFF; font-size: 18pt; margin-top: 4px; margin-bottom: 14px; } "
            "h2 { color: #FFFFFF; font-size: 13pt; margin-top: 18px; margin-bottom: 8px; } "
            "p { color: #F0F0F0; margin-top: 6px; margin-bottom: 8px; } "
            "li { color: #F0F0F0; margin-bottom: 4px; } "
            "a { color: #8AB4F8; text-decoration: underline; } "
            "code { color: #DCDCAA; background-color: #2A2A2A; padding: 2px 5px; } "
            "table { border-collapse: collapse; margin-top: 8px; margin-bottom: 10px; } "
            "th { color: #FFFFFF; background-color: #333333; font-weight: bold; "
            "border: 1px solid #666666; padding: 6px; } "
            "td { color: #F0F0F0; border: 1px solid #555555; padding: 6px; "
            "vertical-align: top; }"
        )
        layout.addWidget(self.browser, 1)

        button_row = QHBoxLayout()
        button_row.addStretch()

        self.close_btn = QPushButton()
        self.close_btn.setDefault(True)
        self.close_btn.clicked.connect(self.accept)
        button_row.addWidget(self.close_btn)

        layout.addLayout(button_row)

    def _apply_content(self) -> None:
        self.setWindowTitle(self._t("documentatie.help.titel"))
        self.close_btn.setText(self._t("documentatie.help.sluiten"))
        self.browser.setHtml(self._build_html())
        self.browser.verticalScrollBar().setValue(0)

    def apply_language(self, taal: str) -> None:
        """Werk de zichtbare teksten bij zonder de dialoog te sluiten."""
        self.taal = taal
        self._apply_content()

    def _build_html(self) -> str:
        t = self._t
        return (
            "<h1>{titel}</h1>"
            "<p>{inleiding}</p>"
            "<h2>{basis_titel}</h2>"
            "<p>{basis_tekst}</p>"
            "<h2>{operatoren_titel}</h2>"
            "{operatoren}"
            "<h2>{voorbeelden_titel}</h2>"
            "{voorbeelden}"
            "<h2>{tips_titel}</h2>"
            "<p>{tips}</p>"
            "<h2>{filters_titel}</h2>"
            "<p>{filters_tekst}</p>"
        ).format(
            titel=t("documentatie.help.titel"),
            inleiding=t("documentatie.help.inleiding"),
            basis_titel=t("documentatie.help.basis_titel"),
            basis_tekst=t("documentatie.help.basis_tekst"),
            operatoren_titel=t("documentatie.help.operatoren_titel"),
            operatoren=t("documentatie.help.operatoren"),
            voorbeelden_titel=t("documentatie.help.voorbeelden_titel"),
            voorbeelden=t("documentatie.help.voorbeelden"),
            tips_titel=t("documentatie.help.tips_titel"),
            tips=t("documentatie.help.tips"),
            filters_titel=t("documentatie.help.filters_titel"),
            filters_tekst=t("documentatie.help.filters_tekst"),
        )