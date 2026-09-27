"""
================================================================================
Module:     app/gui/esr_test_screen.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.5.1
Datum:      2026-09-26
Auteur:     Ontwikkelaar

Doel:       Compact ESR-diagnosescherm voor nominale gegevens, meetcontext,
            meetwaarden en transparante beoordeling zonder primaire scrollbar.

Wijzigingen:
  v1.0.0 (2026-08-11)  Initiele versie.
  v1.1.0 (2026-08-12)  Alle GUI-teksten via i18n-sleutels.
  v1.2.0 (2026-09-26)  GUI compact herwerkt zonder QScrollArea; vaste
                       veiligheidstekst achter knop; drie exclusieve
                       meetmethoden toegevoegd; numerieke velden versmald;
                       OL/out-of-range toegevoegd; resultaat samengevat met
                       afzonderlijke detaildialoog.
  v1.3.0 (2026-09-26)  Geschikt gemaakt als pagina in één hoofdvenster;
                       terugnavigatie, instrumentprofiel en instelbare
                       testspanning toegevoegd.
  v1.3.1 (2026-09-26)  Contrast van de veiligheidsbevestiging verbeterd:
                       donkere tekst op lichte achtergrond, witte tekst
                       op groene achtergrond wanneer bevestigd.
  v1.4.0 (2026-09-26)  Expliciete veiligheidscheckbox toegevoegd; standaard-
                       voorstel ±20% voor aluminium elektrolytisch wordt
                       werkelijk als invoer gebruikt; detailweergave en
                       invoervelden kregen beter donker-thema-contrast.
  v1.5.0 (2026-09-26)  Frequenties gebruiksvriendelijk als 100 Hz / 1 kHz /
                       10 kHz weergegeven. Resultaat toont capaciteitsgrenzen,
                       ESR-referentie en indicatieve ESR-zones; Details toont
                       dezelfde grenzen met expliciete broncontext.
  v1.5.1 (2026-09-26)  Resultaatsamenvatting over echte regels verdeeld;
                       gemeten C en ESR toegevoegd voor snellere interpretatie.

Versiebeheer:
  - MAJOR: incompatibele architectuur/API-wijziging.
  - MINOR: nieuwe functionaliteit met behoud van projectdoel.
  - PATCH: bugfix/refactor zonder functionele uitbreiding.
  - Bij elke wijziging: Versie, Datum en Wijzigingen hierboven bijwerken.
================================================================================
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.config.instrument_profiles import INSTRUMENT_PROFIELEN, get_instrument_profiel
from app.config.settings import (
    laad_instellingen,
    CONDENSATORTYPES,
    EENHEDEN_CAPACITEIT,
    EENHEDEN_ESR,
    MEETFREQUENTIES_HZ,
)
from app.data.references import zoek_referentie
from app.gui.styles import (
    ASSESS_BUTTON_STYLE,
    GROUP_BOX_STYLE,
    RESULT_STATUS_STYLE,
    STATUS_COLORS,
)
from app.helpers.i18n import vertaal
from app.helpers.units import parse_decimaal
from app.services.assessment_service import (
    Meetmethode,
    beoordeel_meting,
    status_label,
)


NUMERIC_WIDTH = 115
UNIT_WIDTH = 80
TEXT_WIDTH = 190
COMBO_WIDTH = 220


def _format_frequency(freq_hz: float | int | None) -> str:
    """Toont frequentie compact zonder de interne Hz-waarde te wijzigen."""
    if freq_hz is None:
        return "—"
    freq = float(freq_hz)
    if freq >= 1000 and freq % 1000 == 0:
        return f"{freq / 1000:g} kHz"
    return f"{freq:g} Hz"


def _format_esr_ohm(value_ohm: float | None) -> str:
    """Toont ESR bij voorkeur in mΩ voor werkplaatswaarden onder 1 Ω."""
    if value_ohm is None:
        return "—"
    if abs(value_ohm) < 1.0:
        return f"{value_ohm * 1000:.4g} mΩ"
    return f"{value_ohm:.4g} Ω"


class EsrTestScreen(QWidget):
    """Compacte ESR-diagnose-interface als pagina in het hoofdvenster."""

    back_requested = Signal()

    def __init__(self, taal: str = "nl_NL", parent=None):
        super().__init__(parent)
        self.taal = taal
        self._laatste_resultaat_html = ""
        self._build_ui()
        self.setMinimumSize(1040, 620)
        self.resize(1120, 690)

    def _t(self, sleutel: str, **kwargs) -> str:
        return vertaal(sleutel, taal=self.taal, **kwargs)

    @staticmethod
    def _set_numeric_width(widget: QWidget) -> None:
        widget.setFixedWidth(NUMERIC_WIDTH)

    @staticmethod
    def _set_unit_width(widget: QWidget) -> None:
        widget.setFixedWidth(UNIT_WIDTH)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        root.addLayout(self._build_navigation_row())
        root.addLayout(self._build_safety_row())

        columns = QHBoxLayout()
        columns.setSpacing(10)
        columns.addWidget(self._build_component_group(), 1)
        columns.addWidget(self._build_context_group(), 1)
        columns.addWidget(self._build_measurement_group(), 1)
        root.addLayout(columns)

        root.addLayout(self._build_action_row())
        root.addWidget(self._build_result_group())
        root.addStretch(1)

    def _build_navigation_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        back_btn = QPushButton(self._t("knop.terug"))
        back_btn.setFixedWidth(100)
        back_btn.clicked.connect(self.back_requested.emit)
        row.addWidget(back_btn)

        title = QLabel(self._t("scherm.esr_test"))
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        row.addWidget(title)
        row.addStretch(1)
        return row

    def _build_safety_row(self) -> QHBoxLayout:
        row = QHBoxLayout()

        self.safety_check = QCheckBox(self._t("veld.veiligheid_bevestigd"))
        self.safety_check.setMinimumHeight(34)
        self.safety_check.setToolTip(self._t("tooltip.veiligheid_bevestigen"))
        self.safety_check.setStyleSheet(
            """
            QCheckBox {
                font-weight: 600;
                padding: 6px 10px;
                background-color: #3A3A3A;
                color: #F0F0F0;
                border: 1px solid #666666;
                border-radius: 4px;
            }
            QCheckBox:hover {
                border-color: #4AA3FF;
                background-color: #424242;
            }
            QCheckBox:checked {
                background-color: #2E7D32;
                color: #FFFFFF;
                border-color: #55B85A;
            }
            """
        )
        row.addWidget(self.safety_check, 1)

        help_btn = QPushButton(self._t("knop.veiligheidsinstructies"))
        help_btn.setMinimumHeight(34)
        help_btn.clicked.connect(self._show_safety_help)
        row.addWidget(help_btn)

        return row

    def _build_component_group(self) -> QGroupBox:
        group = QGroupBox(self._t("scherm.condensator"))
        group.setStyleSheet(GROUP_BOX_STYLE)
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        grid.addWidget(QLabel(self._t("veld.nominale_capaciteit")), 0, 0)
        self.nom_cap_input = QLineEdit()
        self.nom_cap_input.setPlaceholderText("470")
        self._set_numeric_width(self.nom_cap_input)
        grid.addWidget(self.nom_cap_input, 0, 1)

        self.nom_cap_unit = QComboBox()
        self.nom_cap_unit.addItems(EENHEDEN_CAPACITEIT)
        self.nom_cap_unit.setCurrentText("µF")
        self._set_unit_width(self.nom_cap_unit)
        grid.addWidget(self.nom_cap_unit, 0, 2)

        grid.addWidget(QLabel(self._t("veld.tolerantie")), 1, 0)
        self.tolerance_input = QLineEdit()
        self.tolerance_input.setText("20")
        self.tolerance_input.setPlaceholderText("20")
        self.tolerance_input.setToolTip(self._t("tooltip.tolerantie_standaard"))
        self._set_numeric_width(self.tolerance_input)
        grid.addWidget(self.tolerance_input, 1, 1)
        grid.addWidget(QLabel("%"), 1, 2)

        grid.addWidget(QLabel(self._t("veld.nominale_spanning")), 2, 0)
        self.nom_voltage_input = QLineEdit()
        self.nom_voltage_input.setPlaceholderText("25")
        self._set_numeric_width(self.nom_voltage_input)
        grid.addWidget(self.nom_voltage_input, 2, 1)
        grid.addWidget(QLabel("V"), 2, 2)

        grid.addWidget(QLabel(self._t("veld.condensatortype")), 3, 0)
        self.type_combo = QComboBox()
        self.type_combo.addItems(CONDENSATORTYPES)
        self.type_combo.setFixedWidth(COMBO_WIDTH)
        self.type_combo.currentTextChanged.connect(self._update_default_tolerance)
        grid.addWidget(self.type_combo, 3, 1, 1, 2)

        grid.addWidget(QLabel(self._t("veld.fabrikant")), 4, 0)
        self.mfg_input = QLineEdit()
        self.mfg_input.setFixedWidth(TEXT_WIDTH)
        grid.addWidget(self.mfg_input, 4, 1, 1, 2)

        grid.addWidget(QLabel(self._t("veld.serie")), 5, 0)
        self.series_input = QLineEdit()
        self.series_input.setFixedWidth(TEXT_WIDTH)
        grid.addWidget(self.series_input, 5, 1, 1, 2)

        grid.setColumnStretch(3, 1)
        return group

    def _update_default_tolerance(self, condensatortype: str) -> None:
        """Vult alleen een voorstel in; de gebruiker kan dit altijd overschrijven."""
        if condensatortype == "Aluminium elektrolytisch":
            if not self.tolerance_input.text().strip():
                self.tolerance_input.setText("20")
        elif self.tolerance_input.text().strip() == "20":
            self.tolerance_input.clear()

    def _build_context_group(self) -> QGroupBox:
        group = QGroupBox(self._t("scherm.meetcontext"))
        group.setStyleSheet(GROUP_BOX_STYLE)
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        grid.addWidget(QLabel(self._t("veld.meetmethode")), 0, 0)
        self.method_combo = QComboBox()
        self.method_combo.addItem(
            self._t("meetmethode.ex_situ"), Meetmethode.EX_SITU.value
        )
        self.method_combo.addItem(
            self._t("meetmethode.one_leg"), Meetmethode.ONE_LEG.value
        )
        self.method_combo.addItem(
            self._t("meetmethode.in_circuit"), Meetmethode.IN_CIRCUIT.value
        )
        self.method_combo.setFixedWidth(COMBO_WIDTH)
        grid.addWidget(self.method_combo, 0, 1, 1, 2)

        grid.addWidget(QLabel(self._t("veld.meetinstrument")), 1, 0)
        self.instrument_combo = QComboBox()
        for code, profiel in INSTRUMENT_PROFIELEN.items():
            self.instrument_combo.addItem(profiel.naam, code)
        self.instrument_combo.setFixedWidth(COMBO_WIDTH)
        grid.addWidget(self.instrument_combo, 1, 1, 1, 2)
        self.instrument_combo.currentIndexChanged.connect(self._update_instrument_profile)

        grid.addWidget(QLabel(self._t("veld.meetfrequentie")), 2, 0)
        self.freq_combo = QComboBox()
        self.freq_combo.setFixedWidth(COMBO_WIDTH)
        grid.addWidget(self.freq_combo, 2, 1, 1, 2)

        grid.addWidget(QLabel(self._t("veld.testspanning")), 3, 0)
        self.test_voltage_combo = QComboBox()
        self.test_voltage_combo.setFixedWidth(COMBO_WIDTH)
        grid.addWidget(self.test_voltage_combo, 3, 1, 1, 2)

        grid.addWidget(QLabel(self._t("veld.omgevingstemperatuur")), 4, 0)
        self.temp_input = QLineEdit()
        self.temp_input.setPlaceholderText("20")
        self._set_numeric_width(self.temp_input)
        grid.addWidget(self.temp_input, 4, 1)
        grid.addWidget(QLabel("°C"), 4, 2)

        self.method_info = QLabel(self._t("meetmethode.uitleg_ex_situ"))
        self.method_info.setWordWrap(True)
        self.method_info.setStyleSheet("color: #AAAAAA; font-size: 11px;")
        grid.addWidget(self.method_info, 5, 0, 1, 3)
        self.method_combo.currentIndexChanged.connect(self._update_method_info)

        self._update_instrument_profile()
        grid.setRowStretch(6, 1)
        return group

    def _build_measurement_group(self) -> QGroupBox:
        group = QGroupBox(self._t("scherm.meetwaarden"))
        group.setStyleSheet(GROUP_BOX_STYLE)
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        grid.addWidget(QLabel(self._t("veld.gemeten_capaciteit")), 0, 0)
        self.meas_cap_input = QLineEdit()
        self._set_numeric_width(self.meas_cap_input)
        grid.addWidget(self.meas_cap_input, 0, 1)

        self.meas_cap_unit = QComboBox()
        self.meas_cap_unit.addItems(EENHEDEN_CAPACITEIT)
        self.meas_cap_unit.setCurrentText("µF")
        self._set_unit_width(self.meas_cap_unit)
        grid.addWidget(self.meas_cap_unit, 0, 2)

        grid.addWidget(QLabel(self._t("veld.gemeten_esr")), 1, 0)
        self.meas_esr_input = QLineEdit()
        self._set_numeric_width(self.meas_esr_input)
        grid.addWidget(self.meas_esr_input, 1, 1)

        self.meas_esr_unit = QComboBox()
        self.meas_esr_unit.addItems(EENHEDEN_ESR)
        self._set_unit_width(self.meas_esr_unit)
        grid.addWidget(self.meas_esr_unit, 1, 2)

        grid.addWidget(QLabel(self._t("veld.d_waarde")), 2, 0)
        self.d_input = QLineEdit()
        self.d_input.setPlaceholderText(self._t("placeholder.d_waarde"))
        self._set_numeric_width(self.d_input)
        grid.addWidget(self.d_input, 2, 1, 1, 2)

        self.out_of_range_check = QPushButton(self._t("veld.buiten_bereik"))
        self.out_of_range_check.setCheckable(True)
        self.out_of_range_check.setToolTip(self._t("tooltip.buiten_bereik"))
        grid.addWidget(self.out_of_range_check, 3, 0, 1, 3)

        self.open_connection_check = QPushButton(self._t("veld.open_verbinding"))
        self.open_connection_check.setCheckable(True)
        grid.addWidget(self.open_connection_check, 4, 0, 1, 3)

        grid.setRowStretch(5, 1)
        return group

    def _build_action_row(self) -> QHBoxLayout:
        row = QHBoxLayout()

        self.assess_btn = QPushButton(self._t("knop.beoordeel"))
        self.assess_btn.setStyleSheet(ASSESS_BUTTON_STYLE)
        self.assess_btn.clicked.connect(self._on_assess)
        row.addWidget(self.assess_btn)

        clear_btn = QPushButton(self._t("knop.wissen"))
        clear_btn.clicked.connect(self._on_clear)
        row.addWidget(clear_btn)

        row.addStretch(1)
        return row

    def _build_result_group(self) -> QGroupBox:
        self.result_group = QGroupBox(self._t("scherm.resultaat"))
        self.result_group.setStyleSheet(GROUP_BOX_STYLE)
        self.result_group.setVisible(False)

        layout = QGridLayout(self.result_group)
        layout.setHorizontalSpacing(12)

        self.result_status = QLabel()
        self.result_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_status.setMinimumWidth(220)
        self.result_status.setStyleSheet(
            RESULT_STATUS_STYLE.format(color="#9E9E9E")
        )
        layout.addWidget(self.result_status, 0, 0, 2, 1)

        self.result_summary = QLabel()
        self.result_summary.setWordWrap(True)
        self.result_summary.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(self.result_summary, 0, 1)

        details_btn = QPushButton(self._t("knop.details"))
        details_btn.clicked.connect(self._show_result_details)
        layout.addWidget(details_btn, 1, 1, alignment=Qt.AlignmentFlag.AlignRight)

        layout.setColumnStretch(1, 1)
        return self.result_group

    def _update_method_info(self) -> None:
        method = self.method_combo.currentData()
        key = {
            Meetmethode.EX_SITU.value: "meetmethode.uitleg_ex_situ",
            Meetmethode.ONE_LEG.value: "meetmethode.uitleg_one_leg",
            Meetmethode.IN_CIRCUIT.value: "meetmethode.uitleg_in_circuit",
        }.get(method, "meetmethode.uitleg_ex_situ")
        self.method_info.setText(self._t(key))

    def _update_instrument_profile(self) -> None:
        code = self.instrument_combo.currentData()
        profiel = get_instrument_profiel(code)

        self.freq_combo.clear()
        for freq in profiel.frequenties_hz:
            self.freq_combo.addItem(_format_frequency(freq), freq)
        if profiel.standaard_frequentie_hz is not None:
            idx = self.freq_combo.findData(profiel.standaard_frequentie_hz)
            if idx >= 0:
                self.freq_combo.setCurrentIndex(idx)

        self.test_voltage_combo.clear()
        for voltage in profiel.testspanningen_vrms:
            self.test_voltage_combo.addItem(f"{voltage:g} Vrms", voltage)
        if profiel.standaard_testspanning_vrms is not None:
            idx = self.test_voltage_combo.findData(
                profiel.standaard_testspanning_vrms
            )
            if idx >= 0:
                self.test_voltage_combo.setCurrentIndex(idx)

    def _parse_optional(self, text: str):
        text = text.strip()
        if not text:
            return None
        try:
            return parse_decimaal(text)
        except ValueError as exc:
            raise ValueError(
                self._t("fout.ongeldig_getal", waarde=text)
            ) from exc

    def _on_assess(self) -> None:
        if not self.safety_check.isChecked():
            QMessageBox.warning(
                self,
                self._t("scherm.veiligheid"),
                self._t("fout.veiligheid_verplicht"),
            )
            return

        try:
            nom_cap = parse_decimaal(self.nom_cap_input.text())
            tolerance = self._parse_optional(self.tolerance_input.text())
            nom_voltage = self._parse_optional(self.nom_voltage_input.text())

            meas_cap = parse_decimaal(self.meas_cap_input.text())
            meas_esr = parse_decimaal(self.meas_esr_input.text())
            d_value = self._parse_optional(self.d_input.text())
            temp = self._parse_optional(self.temp_input.text())

            cond_type = self.type_combo.currentText()
            meetmethode = self.method_combo.currentData()
            instrument_code = self.instrument_combo.currentData()
            freq_hz = float(self.freq_combo.currentData())
            testspanning_vrms = float(self.test_voltage_combo.currentData())
            fabrikant = self.mfg_input.text().strip()
            serie = self.series_input.text().strip()

            from app.helpers.units import converteer_capaciteit

            nom_cap_uf = converteer_capaciteit(
                nom_cap, self.nom_cap_unit.currentText(), "µF"
            )

            referentie = None
            if cond_type == "Aluminium elektrolytisch" and nom_voltage:
                referentie = zoek_referentie(nom_cap_uf, nom_voltage)

            resultaat = beoordeel_meting(
                nominale_capaciteit=nom_cap,
                eenheid_nominaal=self.nom_cap_unit.currentText(),
                tolerantie_percent=tolerance,
                gemeten_capaciteit=meas_cap,
                eenheid_gemeten_capaciteit=self.meas_cap_unit.currentText(),
                gemeten_esr=meas_esr,
                eenheid_gemeten_esr=self.meas_esr_unit.currentText(),
                meetfrequentie_hz=freq_hz,
                D=d_value,
                condensatortype=cond_type,
                meetmethode=meetmethode,
                omgevingstemperatuur_c=temp,
                instrument_code=instrument_code,
                testspanning_vrms=testspanning_vrms,
                veiligheid_bevestigd=True,
                referentie=referentie,
                fabrikant_bekend=bool(fabrikant),
                serie_bekend=bool(serie),
                vermoedelijke_open_verbinding_of_kortsluiting=(
                    self.open_connection_check.isChecked()
                ),
                meetwaarde_buiten_bereik=self.out_of_range_check.isChecked(),
                taal=self.taal,
            )
            self._show_result(resultaat)

        except ValueError as exc:
            QMessageBox.warning(self, self._t("fout.titel"), str(exc))
        except Exception as exc:
            QMessageBox.critical(
                self,
                self._t("fout.titel"),
                self._t("fout.onverwacht", bericht=str(exc)),
            )

    def _show_result(self, resultaat) -> None:
        status_key = resultaat.eindstatus.value
        color = STATUS_COLORS.get(status_key, "#9E9E9E")
        status_text = status_label(
            "status.eindstatus", status_key, self.taal
        )

        self.result_status.setText(status_text.upper())
        self.result_status.setStyleSheet(
            RESULT_STATUS_STYLE.format(color=color)
        )

        reliability = status_label(
            "status.betrouwbaarheid",
            resultaat.betrouwbaarheid.niveau.value,
            self.taal,
        )
        cap = resultaat.capaciteit
        esr = resultaat.esr

        cap_text = (
            f"{cap.afwijking_percent:+.1f}%"
            if cap.afwijking_percent is not None
            else "—"
        )
        esr_factor = (
            f"{esr.factor:.2f}×" if esr.factor is not None else "—"
        )

        if (
            cap.nominale_waarde is not None
            and cap.tolerantie_percent is not None
        ):
            marge = cap.nominale_waarde * cap.tolerantie_percent / 100.0
            cap_min = cap.nominale_waarde - marge
            cap_max = cap.nominale_waarde + marge
            cap_grenzen = f"{cap_min:.4g}–{cap_max:.4g} {cap.eenheid}"
        else:
            cap_grenzen = "—"

        esr_ref = _format_esr_ohm(esr.referentie_esr_ohm)
        cap_gemeten = (
            f"{cap.gemeten_waarde:.4g} {cap.eenheid}"
            if cap.gemeten_waarde is not None
            else "—"
        )
        esr_gemeten = _format_esr_ohm(esr.gemeten_esr_ohm)

        self.result_summary.setText(
            self._t(
                "resultaat.samenvatting_grenzen",
                betrouwbaarheid=reliability,
                cap_gemeten=cap_gemeten,
                cap_afwijking=cap_text,
                cap_grenzen=cap_grenzen,
                esr_gemeten=esr_gemeten,
                esr_factor=esr_factor,
                esr_ref=esr_ref,
                advies=resultaat.aanbevolen_vervolgstap,
            )
        )

        self._laatste_resultaat_html = self._build_result_html(resultaat)
        self.result_group.setVisible(True)

    def _build_result_html(self, resultaat) -> str:
        status_text = status_label(
            "status.eindstatus", resultaat.eindstatus.value, self.taal
        )
        c = resultaat.capaciteit
        e = resultaat.esr
        cons = resultaat.consistentie
        b = resultaat.betrouwbaarheid
        instellingen = laad_instellingen().beoordeling

        cap_grenzen_html = "—"
        if c.nominale_waarde is not None and c.tolerantie_percent is not None:
            marge = c.nominale_waarde * c.tolerantie_percent / 100.0
            cap_min = c.nominale_waarde - marge
            cap_max = c.nominale_waarde + marge
            cap_grenzen_html = (
                f"{cap_min:.4g} – {cap_max:.4g} {c.eenheid} "
                f"(±{c.tolerantie_percent:.4g}%)"
            )

        esr_zones_html = "—"
        if e.referentie_esr_ohm is not None and e.referentie_esr_ohm > 0:
            ref = e.referentie_esr_ohm
            normaal = ref * instellingen.esr_factor_normaal
            aandacht = ref * instellingen.esr_factor_aandachtspunt
            verdacht = ref * instellingen.esr_factor_verdacht
            esr_zones_html = (
                f"{self._t('resultaat.esr_normaal')}: ≤ {_format_esr_ohm(normaal)}<br>"
                f"{self._t('resultaat.esr_aandacht')}: &gt; {_format_esr_ohm(normaal)} "
                f"t/m {_format_esr_ohm(aandacht)}<br>"
                f"{self._t('resultaat.esr_verdacht')}: &gt; {_format_esr_ohm(aandacht)} "
                f"t/m {_format_esr_ohm(verdacht)}<br>"
                f"{self._t('resultaat.esr_defect_indicatief')}: &gt; {_format_esr_ohm(verdacht)}"
            )

        html = [
            f"<h2>{self._t('scherm.resultaat')}</h2>",
            f"<p><b>{self._t('resultaat.eindstatus')}:</b> {status_text}</p>",
            f"<p><b>{self._t('veld.meetinstrument')}:</b> {resultaat.instrument_code or '—'}<br>"
            f"<b>{self._t('veld.testspanning')}:</b> "
            f"{resultaat.testspanning_vrms if resultaat.testspanning_vrms is not None else '—'} Vrms<br>"
            f"<b>{self._t('resultaat.meetfrequentie')}:</b> {_format_frequency(self.freq_combo.currentData())}<br>"
            f"<b>{self._t('resultaat.referentiebron')}:</b> {e.referentiebron or '—'}<br>"
            f"<b>{self._t('resultaat.referentieniveau')}:</b> {e.referentieniveau if e.referentieniveau is not None else '—'}</p>",
            f"<h3>{self._t('resultaat.capaciteit')}</h3>",
            f"<p>{c.toelichting}<br>"
            f"<b>{self._t('resultaat.toegestane_capaciteit')}:</b> {cap_grenzen_html}</p>",
            f"<h3>{self._t('resultaat.esr')}</h3>",
            f"<p>{e.toelichting}<br>"
            f"<b>{self._t('resultaat.esr_referentie')}:</b> {_format_esr_ohm(e.referentie_esr_ohm)}<br>"
            f"<b>{self._t('resultaat.esr_zones')}:</b><br>{esr_zones_html}<br>"
            f"<i>{self._t('resultaat.esr_zones_disclaimer')}</i></p>",
            f"<h3>{self._t('resultaat.consistentie')}</h3>",
            f"<p>{cons.toelichting}</p>",
            f"<h3>{self._t('resultaat.betrouwbaarheid')}</h3>",
            f"<p>{status_label('status.betrouwbaarheid', b.niveau.value, self.taal)}</p>",
        ]

        if b.verlagende_factoren:
            html.append("<ul>")
            html.extend(f"<li>{x}</li>" for x in b.verlagende_factoren)
            html.append("</ul>")

        html.append(f"<h3>{self._t('resultaat.redenen')}</h3><ul>")
        html.extend(f"<li>{x}</li>" for x in resultaat.redenen)
        html.append("</ul>")

        html.append(
            f"<h3>{self._t('resultaat.vervolgstap')}</h3>"
            f"<p>{resultaat.aanbevolen_vervolgstap}</p>"
        )

        if resultaat.waarschuwingen:
            html.append(
                f"<h3>{self._t('scherm.waarschuwingen')}</h3><ul>"
            )
            html.extend(
                f"<li>{x}</li>" for x in resultaat.waarschuwingen
            )
            html.append("</ul>")

        return "\n".join(html)

    def _show_result_details(self) -> None:
        if not self._laatste_resultaat_html:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(self._t("dialog.resultaat_details"))
        dialog.resize(720, 560)

        layout = QVBoxLayout(dialog)
        browser = QTextBrowser()
        browser.setStyleSheet(
            "QTextBrowser { background-color: #1E1E1E; color: #F0F0F0; "
            "border: 1px solid #555555; padding: 8px; }"
        )
        browser.document().setDefaultStyleSheet(
            "body { color: #F0F0F0; background-color: #1E1E1E; "
            "font-family: 'Segoe UI'; } "
            "h2, h3, b { color: #FFFFFF; } "
            "li, p { color: #F0F0F0; }"
        )
        browser.setHtml(self._laatste_resultaat_html)
        layout.addWidget(browser)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()

    def _on_clear(self) -> None:
        for widget in (
            self.nom_cap_input,
            self.tolerance_input,
            self.nom_voltage_input,
            self.mfg_input,
            self.series_input,
            self.meas_cap_input,
            self.meas_esr_input,
            self.d_input,
            self.temp_input,
        ):
            widget.clear()

        self.nom_cap_unit.setCurrentText("µF")
        self.meas_cap_unit.setCurrentText("µF")
        self.type_combo.setCurrentIndex(0)
        self.tolerance_input.setText("20")
        self.safety_check.setChecked(False)
        self.out_of_range_check.setChecked(False)
        self.open_connection_check.setChecked(False)
        self.method_combo.setCurrentIndex(0)
        self.result_group.setVisible(False)
        self._laatste_resultaat_html = ""

    def _show_safety_help(self) -> None:
        waarschuwingen = [
            f"• {self._t(f'veiligheid.waarschuwing_{i}')}"
            for i in range(1, 10)
        ]

        msg = QMessageBox(self)
        msg.setWindowTitle(self._t("dialog.veiligheid_titel"))
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(
            f"<h3>{self._t('scherm.veiligheid')}</h3>"
            f"<p>{'<br><br>'.join(waarschuwingen)}</p>"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
