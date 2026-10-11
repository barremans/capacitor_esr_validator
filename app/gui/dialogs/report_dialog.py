"""
================================================================================
Module:     app/gui/dialogs/report_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.1
Datum:      2026-10-10
Auteur:     Bart Bossuyt

Doel:       Modale dialoog voor het maken en opslaan van meetrapporten.

            De dialoog bouwt via ReportService een ReportBundle, rendert
            die met de pure HTML-renderer en toont een preview. De
            gebruiker kan optioneel een grafiek opnemen (alleen voor
            ESR_CAPACITOR) en het rapport opslaan als HTML of PDF.

            De dialoog schrijft nooit naar de database. Historische
            metingen en beoordelingen worden nooit opnieuw berekend.

Wijzigingen:
  v1.0.0 (2026-10-10)  Eerste versie: preview, grafiek-checkbox,
                        opslaan-HTML, opslaan-PDF.
  v1.0.1 (2026-10-10)  Fix: _start_directory() en _onthoud_map() lezen
                        laatste_rapportmap defensief via getattr(). De
                        instelling bestaat pas vanaf 8D; in 8C werkt de
                        dialoog zonder die instelling en valt terug op
                        standaard_exportmap.
================================================================================
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.config.settings import laad_instellingen
from app.helpers.i18n import vertaal
from app.helpers.report_chart import render_chart_voor_detail
from app.helpers.report_pdf import write_html_to_pdf
from app.helpers.report_render import render_measurement_report_html
from app.services.analysis_service import AnalysisService
from app.services.report_service import ReportBundle, ReportService


def _laatste_rapportmap(instellingen) -> str:
    """Lees laatste_rapportmap defensief; de instelling bestaat pas vanaf 8D."""
    return getattr(instellingen.algemeen, "laatste_rapportmap", "") or ""


class ReportDialog(QDialog):
    """Modale dialoog die één meetrapport toont en kan opslaan."""

    def __init__(
        self,
        measurement_id: int,
        *,
        taal: str = "nl_NL",
        report_service: ReportService | None = None,
        analysis_service: AnalysisService | None = None,
        werkplaats: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.taal = taal
        self._measurement_id = int(measurement_id)
        self._report_service = report_service or ReportService()
        self._analysis_service = analysis_service or AnalysisService()
        self._werkplaats = werkplaats

        self._bundle: ReportBundle | None = None
        self._html: str = ""
        self._chart_png_base64: str | None = None
        self._grafiek_beschikbaar: bool = False

        self.setWindowTitle(self._t("report.dialoog.titel"))
        self.setModal(True)
        self.resize(900, 720)

        self._build_ui()
        self._laad_bundle()
        self._render_preview()

    # ------------------------------------------------------------------
    # i18n
    # ------------------------------------------------------------------

    def _t(self, sleutel: str, **kwargs) -> str:
        return vertaal(sleutel, taal=self.taal, **kwargs)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        # Kop met meet-id en titel
        self.kop_label = QLabel(
            self._t("report.meting_kop", measurement_id=self._measurement_id)
        )
        self.kop_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        root.addWidget(self.kop_label)

        # Preview
        preview_kop = QLabel(self._t("report.dialoog.preview_titel"))
        preview_kop.setStyleSheet("color: #BDBDBD;")
        root.addWidget(preview_kop)

        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(False)
        self.preview.setStyleSheet(
            "QTextBrowser { background-color: #1E1E1E; color: #F0F0F0; "
            "border: 1px solid #555; }"
        )
        root.addWidget(self.preview, 1)

        # Grafiek-checkbox
        self.grafiek_checkbox = QCheckBox(self._t("report.dialoog.grafiek_checkbox"))
        self.grafiek_checkbox.setChecked(False)
        self.grafiek_checkbox.stateChanged.connect(self._on_grafiek_toggled)
        root.addWidget(self.grafiek_checkbox)

        self.grafiek_hint = QLabel("")
        self.grafiek_hint.setStyleSheet("color: #9E9E9E; font-size: 10px;")
        root.addWidget(self.grafiek_hint)

        # Knoppen
        knoppen = QHBoxLayout()
        knoppen.addStretch(1)

        self.opslaan_html_btn = QPushButton(self._t("report.dialoog.opslaan_html"))
        self.opslaan_html_btn.clicked.connect(self._opslaan_html)
        knoppen.addWidget(self.opslaan_html_btn)

        self.opslaan_pdf_btn = QPushButton(self._t("report.dialoog.opslaan_pdf"))
        self.opslaan_pdf_btn.clicked.connect(self._opslaan_pdf)
        knoppen.addWidget(self.opslaan_pdf_btn)

        self.sluiten_btn = QPushButton(self._t("report.dialoog.sluiten"))
        self.sluiten_btn.clicked.connect(self.reject)
        knoppen.addWidget(self.sluiten_btn)

        root.addLayout(knoppen)

    # ------------------------------------------------------------------
    # Data laden
    # ------------------------------------------------------------------

    def _laad_bundle(self) -> None:
        try:
            self._bundle = self._report_service.build_bundle(
                self._measurement_id,
                taal=self.taal,
                werkplaats=self._werkplaats,
            )
        except ValueError as exc:
            self._toon_fout(str(exc))
            self._bundle = None
            return

        # Bepaal of er een grafiek beschikbaar is voor deze meting.
        detail = self._bundle.detail
        measurement = detail.get("measurement")
        tool_key = str(getattr(measurement, "tool_key", "") or "")
        self._grafiek_beschikbaar = tool_key == "ESR_CAPACITOR"

        if not self._grafiek_beschikbaar:
            self.grafiek_checkbox.setEnabled(False)
            self.grafiek_checkbox.setChecked(False)
            self.grafiek_hint.setText(self._t("report.dialoog.grafiek_niet_beschikbaar"))
        else:
            self.grafiek_hint.setText("")

    def _render_preview(self) -> None:
        if self._bundle is None:
            self.preview.setHtml(
                f"<p style='color:#F0F0F0;'>{self._t('report.dialoog.fout', bericht='')}</p>"
            )
            self._html = ""
            return

        chart_map: dict[int, str] = {}
        if self._chart_png_base64 is not None:
            chart_map[self._measurement_id] = self._chart_png_base64

        try:
            self._html = render_measurement_report_html(
                self._bundle,
                chart_png_base64_per_meting=chart_map,
            )
        except Exception as exc:
            self._toon_fout(str(exc))
            self._html = ""
            return

        self.preview.setHtml(self._html)

    # ------------------------------------------------------------------
    # Grafiek
    # ------------------------------------------------------------------

    def _on_grafiek_toggled(self, _state: int) -> None:
        if not self._grafiek_beschikbaar:
            self._chart_png_base64 = None
            self._render_preview()
            return

        if self.grafiek_checkbox.isChecked():
            if self._bundle is None:
                return
            try:
                self._chart_png_base64 = render_chart_voor_detail(
                    self._bundle.detail,
                    analysis_service=self._analysis_service,
                    taal=self.taal,
                )
            except Exception as exc:
                self._chart_png_base64 = None
                self._toon_fout(str(exc))
                return
            if self._chart_png_base64 is None:
                self.grafiek_hint.setText(
                    self._t("report.dialoog.grafiek_niet_beschikbaar")
                )
        else:
            self._chart_png_base64 = None

        self._render_preview()

    # ------------------------------------------------------------------
    # Opslaan
    # ------------------------------------------------------------------

    def _start_directory(self) -> str:
        """Beste startmap voor de opslaandialoog.

        Leest laatste_rapportmap defensief: die instelling bestaat pas
        vanaf 8D. Zonder die instelling valt de dialoog terug op
        standaard_exportmap, en anders op niets.
        """
        try:
            instellingen = laad_instellingen()
        except (OSError, ValueError):
            return ""

        kandidaten = [
            _laatste_rapportmap(instellingen),
            instellingen.algemeen.standaard_exportmap,
        ]
        for kandidaat in kandidaten:
            if not kandidaat:
                continue
            try:
                pad = Path(kandidaat).expanduser()
            except (OSError, ValueError):
                continue
            if pad.is_dir():
                return str(pad)
        return ""

    def _onthoud_map(self, bestand: Path) -> None:
        """Werk laatste_rapportmap bij na een geslaagde opslag.

        De instelling bestaat pas vanaf 8D. Faalt stil als ze nog niet
        bestaat: het onthouden van de map is een gemaksfunctie.
        """
        try:
            from dataclasses import replace as _dc_replace
            from app.config.settings import sla_instellingen_op

            nieuwe_map = str(bestand.parent)
            instellingen = laad_instellingen()

            if not hasattr(instellingen.algemeen, "laatste_rapportmap"):
                return
            if _laatste_rapportmap(instellingen) == nieuwe_map:
                return

            bijgewerkt = _dc_replace(
                instellingen,
                algemeen=_dc_replace(
                    instellingen.algemeen,
                    laatste_rapportmap=nieuwe_map,
                ),
            )
            sla_instellingen_op(bijgewerkt)
        except (OSError, ValueError):
            pass

    def _opslaan_html(self) -> None:
        if not self._html:
            return
        start = self._start_directory()
        standaard = f"rapport_{self._measurement_id}.html"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self._t("report.dialoog.opslaan_titel"),
            str(Path(start) / standaard) if start else standaard,
            self._t("report.dialoog.html_filter"),
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".html"):
            file_path += ".html"

        try:
            Path(file_path).write_text(self._html, encoding="utf-8")
        except OSError as exc:
            self._toon_fout(str(exc))
            return

        self._onthoud_map(Path(file_path))
        self._toon_succes(self._t("report.dialoog.geslaagd_html", pad=file_path))

    def _opslaan_pdf(self) -> None:
        if not self._html:
            return
        start = self._start_directory()
        standaard = f"rapport_{self._measurement_id}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self._t("report.dialoog.opslaan_titel"),
            str(Path(start) / standaard) if start else standaard,
            self._t("report.dialoog.pdf_filter"),
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".pdf"):
            file_path += ".pdf"

        try:
            write_html_to_pdf(
                self._html,
                file_path,
                titel=self._t("report.titel"),
            )
        except (OSError, ValueError) as exc:
            self._toon_fout(str(exc))
            return

        self._onthoud_map(Path(file_path))
        self._toon_succes(self._t("report.dialoog.geslaagd_pdf", pad=file_path))

    # ------------------------------------------------------------------
    # Meldingen
    # ------------------------------------------------------------------

    def _toon_fout(self, bericht: str) -> None:
        QMessageBox.warning(
            self,
            self._t("report.dialoog.titel"),
            self._t("report.dialoog.fout", bericht=bericht),
        )

    def _toon_succes(self, bericht: str) -> None:
        QMessageBox.information(
            self,
            self._t("report.dialoog.titel"),
            bericht,
        )