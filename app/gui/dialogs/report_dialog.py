"""
================================================================================
Module:     app/gui/dialogs/report_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.5.0
Datum:      2026-10-16
Auteur:     Bart Bossuyt

Doel:       Modale dialoog voor het maken en opslaan van meetrapporten.

            De dialoog bouwt via ReportService een ReportBundle, rendert
            die met de pure HTML-renderer en toont een preview. De
            gebruiker kan optioneel een grafiek opnemen (alleen voor
            één ESR_CAPACITOR-meting) en het rapport opslaan als HTML of PDF.

            De dialoog schrijft nooit naar de database. Historische
            metingen en beoordelingen worden nooit opnieuw berekend.

Wijzigingen:
  v1.0.0 (2026-10-10)  Eerste versie: preview, grafiek-checkbox,
                        opslaan-HTML, opslaan-PDF.
  v1.0.1 (2026-10-10)  Fix: _start_directory() en _onthoud_map() lezen
                        laatste_rapportmap defensief via getattr().
  v1.1.0 (2026-10-11)  Fase 8D: laatste_rapportmap bestaat nu; auteur-
                        parameter; grafiek-checkbox start met de instelling.
  v1.2.0 (2026-10-11)  Fase 8D (vervolg): grafiek_default-parameter voor
                        determinisme.
  v1.3.0 (2026-10-16)  Fase 11A.2: classmethod for_measurements.
  v1.4.0 (2026-10-16)  Fase 11A.3: _start_directory() en _onthoud_map()
                        delegeren naar de nieuwe pure helper
                        app/helpers/dialog_start_directory (categorie
                        'rapport'). Geen gedragswijziging voor de
                        gebruiker.
  v1.5.0 (2026-10-16)  Fase 11C: dialoog krijgt een venstericoon via
                        de centrale helper app/helpers/icon_paths.
                        Geen wijziging aan de rapportlogica.
================================================================================
"""

from __future__ import annotations

import os
import subprocess
import sys
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
from app.helpers.dialog_start_directory import (
    beste_startmap as _beste_startmap_helper,
    onthoud_startmap as _onthoud_startmap_helper,
    startpad_voor_bestand as _startpad_voor_bestand_helper,
)
from app.helpers.i18n import vertaal
from app.helpers.report_chart import render_chart_voor_detail
from app.helpers.report_pdf import write_html_to_pdf
from app.helpers.report_render import render_measurement_report_html
from app.services.analysis_service import AnalysisService
from app.services.report_service import ReportBundle, ReportService


class ReportDialog(QDialog):
    """Modale dialoog die één of meerdere meetrapporten toont en kan opslaan."""

    def __init__(
        self,
        measurement_id: int,
        *,
        taal: str = "nl_NL",
        report_service: ReportService | None = None,
        analysis_service: AnalysisService | None = None,
        werkplaats: str = "",
        auteur: str = "",
        grafiek_default: bool = False,
        parent: QWidget | None = None,
        scope: str = "",
    ) -> None:
        self._init_intern(
            measurement_ids=[int(measurement_id)],
            scope=scope or "",
            taal=taal,
            report_service=report_service,
            analysis_service=analysis_service,
            werkplaats=werkplaats,
            auteur=auteur,
            grafiek_default=grafiek_default,
            parent=parent,
        )

    @classmethod
    def for_measurements(
        cls,
        measurement_ids: list[int],
        *,
        scope: str = "",
        taal: str = "nl_NL",
        report_service: ReportService | None = None,
        analysis_service: AnalysisService | None = None,
        werkplaats: str = "",
        auteur: str = "",
        grafiek_default: bool = False,
        parent: QWidget | None = None,
    ) -> "ReportDialog":
        if not isinstance(measurement_ids, list) or not measurement_ids:
            raise ValueError("measurement_ids moet een niet-lege lijst zijn.")
        dialog = cls.__new__(cls)
        dialog._init_intern(
            measurement_ids=[int(mid) for mid in measurement_ids],
            scope=scope,
            taal=taal,
            report_service=report_service,
            analysis_service=analysis_service,
            werkplaats=werkplaats,
            auteur=auteur,
            grafiek_default=grafiek_default,
            parent=parent,
        )
        return dialog

    def _init_intern(
        self,
        *,
        measurement_ids: list[int],
        scope: str,
        taal: str,
        report_service: ReportService | None,
        analysis_service: AnalysisService | None,
        werkplaats: str,
        auteur: str,
        grafiek_default: bool,
        parent: QWidget | None,
    ) -> None:
        QDialog.__init__(self, parent)

        self.taal = taal
        self._measurement_ids: list[int] = list(measurement_ids)
        self._measurement_id: int = self._measurement_ids[0]
        self._scope = scope
        self._report_service = report_service or ReportService()
        self._analysis_service = analysis_service or AnalysisService()
        self._werkplaats = werkplaats
        self._auteur = auteur
        self._grafiek_default = bool(grafiek_default)

        self._bundle: ReportBundle | None = None
        self._html: str = ""
        self._chart_png_base64: str | None = None
        self._grafiek_beschikbaar: bool = False

        try:
            self._instellingen = laad_instellingen()
        except (OSError, ValueError):
            self._instellingen = None

        self.setWindowTitle(self._t("report.dialoog.titel"))
        self.setModal(True)
        self.resize(900, 720)
        self._zet_eigen_icoon()

        self._build_ui()
        self._laad_bundle()
        self._render_preview()

    def _t(self, sleutel: str, **kwargs) -> str:
        return vertaal(sleutel, taal=self.taal, **kwargs)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        if len(self._measurement_ids) == 1:
            kop_tekst = self._t(
                "report.meting_kop", measurement_id=self._measurement_id
            )
        else:
            kop_tekst = self._t(
                "report.dialoog.meerdere_metingen_kop",
                aantal=len(self._measurement_ids),
            )
        self.kop_label = QLabel(kop_tekst)
        self.kop_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        root.addWidget(self.kop_label)

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

        self.grafiek_checkbox = QCheckBox(self._t("report.dialoog.grafiek_checkbox"))
        self.grafiek_checkbox.setChecked(self._grafiek_default)
        self.grafiek_checkbox.stateChanged.connect(self._on_grafiek_toggled)
        root.addWidget(self.grafiek_checkbox)

        self.grafiek_hint = QLabel("")
        self.grafiek_hint.setStyleSheet("color: #9E9E9E; font-size: 10px;")
        root.addWidget(self.grafiek_hint)

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

    def _laad_bundle(self) -> None:
        try:
            if len(self._measurement_ids) == 1:
                self._bundle = self._report_service.build_bundle(
                    self._measurement_id,
                    taal=self.taal,
                    werkplaats=self._werkplaats,
                    auteur=self._auteur,
                    scope=self._scope,
                )
            else:
                self._bundle = self._report_service.build_bundle_for_measurements(
                    list(self._measurement_ids),
                    taal=self.taal,
                    werkplaats=self._werkplaats,
                    auteur=self._auteur,
                    scope=self._scope,
                )
        except ValueError as exc:
            self._toon_fout(str(exc))
            self._bundle = None
            return

        self._grafiek_beschikbaar = False
        if len(self._measurement_ids) == 1:
            detail = self._bundle.detail
            measurement = detail.get("measurement")
            tool_key = str(getattr(measurement, "tool_key", "") or "")
            self._grafiek_beschikbaar = tool_key == "ESR_CAPACITOR"

        if not self._grafiek_beschikbaar:
            self.grafiek_checkbox.setEnabled(False)
            self.grafiek_checkbox.setChecked(False)
            if len(self._measurement_ids) > 1:
                self.grafiek_hint.setText(
                    self._t("report.dialoog.grafiek_meerdere_niet_beschikbaar")
                )
            else:
                self.grafiek_hint.setText(
                    self._t("report.dialoog.grafiek_niet_beschikbaar")
                )
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
    # Opslaan — 11A.3: alle map-logica via de centrale helper.
    # ------------------------------------------------------------------

    def _start_directory(self) -> str:
        """Beste startmap via de centrale helper (categorie 'rapport')."""
        map_ = _beste_startmap_helper("rapport")
        return str(map_) if map_ is not None else ""

    def _onthoud_map(self, bestand: Path) -> None:
        """Onthoud de map via de centrale helper (categorie 'rapport')."""
        _onthoud_startmap_helper("rapport", bestand)

    def _open_map_indien_gewenst(self, bestand: Path) -> None:
        if self._instellingen is None:
            return
        if not self._instellingen.algemeen.exportmap_openen_na_export:
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(bestand.parent))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(bestand.parent)])
            else:
                subprocess.Popen(["xdg-open", str(bestand.parent)])
        except OSError:
            pass

    def _default_bestandsnaam(self, extensie: str) -> str:
        if len(self._measurement_ids) == 1:
            return f"rapport_{self._measurement_id}.{extensie}"
        return f"rapport_{len(self._measurement_ids)}metingen.{extensie}"

    def _opslaan_html(self) -> None:
        if not self._html:
            return
        standaard = self._default_bestandsnaam("html")
        startpad = _startpad_voor_bestand_helper("rapport", standaard)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self._t("report.dialoog.opslaan_titel"),
            startpad,
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
        self._open_map_indien_gewenst(Path(file_path))
        self._toon_succes(self._t("report.dialoog.geslaagd_html", pad=file_path))

    def _opslaan_pdf(self) -> None:
        if not self._html:
            return
        standaard = self._default_bestandsnaam("pdf")
        startpad = _startpad_voor_bestand_helper("rapport", standaard)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self._t("report.dialoog.opslaan_titel"),
            startpad,
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
        self._open_map_indien_gewenst(Path(file_path))
        self._toon_succes(self._t("report.dialoog.geslaagd_pdf", pad=file_path))

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
        
    def _zet_eigen_icoon(self) -> None:
        try:
            from app.helpers.icon_paths import zet_venster_icoon
            zet_venster_icoon(self)
        except Exception:
            pass