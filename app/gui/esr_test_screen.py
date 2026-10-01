"""
================================================================================
Module:     app/gui/esr_test_screen.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.8.0
Datum:      2026-10-01
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
  v1.5.2 (2026-09-27)  Compacte GUI-opruiming: labelkolommen flexibeler gemaakt,
                       dubbele GroupBox-styling verwijderd en ESR-paginatitel
                       minder dominant gemaakt. Beoordelingslogica ongewijzigd.
  v1.5.3 (2026-09-27)  Breedteverdeling van de drie hoofdgroepen verfijnd zodat
                       lange Meetcontext-labels, waaronder Omgevingstemperatuur,
                       volledig leesbaar blijven. Geen logica gewijzigd.
  v1.5.4 (2026-09-27)  Omgevingstemperatuur-label compact gemaakt met volledige
                       tekst als tooltip, zodat de drie-kolommenlayout stabiel
                       blijft. Geen beoordelingslogica gewijzigd.
  v1.6.0 (2026-09-28)  Opgeslagen ESR/Condensator-defaults gekoppeld aan het
                       invoerscherm. Wissen herstelt configuratiedefaults maar
                       wist meetresultaten. Beoordelingslogica ongewijzigd.
  v1.6.1 (2026-09-28)  Instelling bevestig_wissen gekoppeld: optionele
                       bevestigingsvraag vóór Wissen. Bestaande wis- en
                       beoordelingslogica verder ongewijzigd.
  v1.6.2 (2026-09-28)  OL/out-of-range laat een lege ESR-invoer toe;
                       intern wordt alleen voor de serviceketen 0,0 gebruikt.
                       Normale metingen blijven een numerieke ESR vereisen.
  v1.6.3 (2026-09-29)  OL/out-of-range laat ook een lege gemeten
                       capaciteit toe; intern wordt alleen voor de serviceketen
                       0,0 gebruikt. Normale metingen blijven numeriek verplicht.
  v1.6.4 (2026-09-29)  Contrast van resultaat- en veiligheidsdialogen expliciet
                       vastgelegd voor betrouwbare leesbaarheid in donker thema.
  v1.7.0 (2026-10-01)  Na beoordeling kan de exact beoordeelde meetrun lokaal
                       worden opgeslagen via MeasurementPersistenceService.
                       OL/out-of-range met lege C/ESR blijft in storage NULL.
  v1.8.0 (2026-10-01)  Veilige "Herhaal meting"-preset toegevoegd: component-
                       en meetcontext worden hersteld, maar meetwaarden, safety,
                       resultaat en assessment blijven leeg/nieuw.
  v1.6.5 (2026-09-29)  Compact resultaat maakt frequentiemismatch expliciet bij
                       de ESR-factor; vergelijking blijft zichtbaar maar wordt
                       duidelijk als indicatief gemarkeerd.

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
from app.services.repeat_measurement_service import RepeatMeasurementPreset
from app.services.measurement_persistence_service import (
    EsrMeasurementSaveData,
    MeasurementPersistenceService,
)
from app.storage.exceptions import StorageError


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

    def __init__(
        self,
        taal: str = "nl_NL",
        parent=None,
        persistence_service: MeasurementPersistenceService | None = None,
    ):
        super().__init__(parent)
        self.taal = taal
        self._laatste_resultaat_html = ""
        self._laatste_opslag_payload: EsrMeasurementSaveData | None = None
        self._persistence_service = (
            persistence_service
            if persistence_service is not None
            else MeasurementPersistenceService()
        )
        self._build_ui()
        self._apply_saved_defaults()
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
        self.repeat_banner = QLabel()
        self.repeat_banner.setWordWrap(True)
        self.repeat_banner.setVisible(False)
        self.repeat_banner.setStyleSheet(
            "background-color: #263238; color: #E0F2F1; "
            "border: 1px solid #546E7A; border-radius: 4px; padding: 6px 10px;"
        )
        root.addWidget(self.repeat_banner)

        root.addLayout(self._build_safety_row())

        columns = QHBoxLayout()
        columns.setSpacing(10)
        columns.addWidget(self._build_component_group(), 10)
        columns.addWidget(self._build_context_group(), 11)
        columns.addWidget(self._build_measurement_group(), 10)
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
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
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
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        grid.setColumnMinimumWidth(0, 145)
        grid.setColumnStretch(1, 1)

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
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        grid.setColumnMinimumWidth(0, 158)
        grid.setColumnStretch(1, 1)

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

        temp_label = QLabel(self._t("veld.omgevingstemperatuur_kort"))
        temp_label.setToolTip(self._t("tooltip.omgevingstemperatuur"))
        grid.addWidget(temp_label, 4, 0)
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
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        grid.setColumnMinimumWidth(0, 150)
        grid.setColumnStretch(1, 1)

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

        self.save_btn = QPushButton(self._t("knop.meting_opslaan"))
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._on_save_measurement)
        row.addWidget(self.save_btn)

        row.addStretch(1)
        return row

    def _build_result_group(self) -> QGroupBox:
        self.result_group = QGroupBox(self._t("scherm.resultaat"))
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

    def _apply_saved_defaults(self) -> None:
        """Past opgeslagen ESR/Condensator-defaults veilig toe op de invoervelden."""
        defaults = laad_instellingen().esr_condensator

        if self.nom_cap_unit.findText(defaults.capaciteitseenheid) >= 0:
            self.nom_cap_unit.setCurrentText(defaults.capaciteitseenheid)
        if self.meas_cap_unit.findText(defaults.capaciteitseenheid) >= 0:
            self.meas_cap_unit.setCurrentText(defaults.capaciteitseenheid)

        self.tolerance_input.setText(f"{defaults.tolerantie_percent:g}")
        self.nom_voltage_input.setText(
            "" if defaults.werkspanning_v is None else f"{defaults.werkspanning_v:g}"
        )

        type_index = self.type_combo.findText(defaults.condensatortype)
        if type_index >= 0:
            self.type_combo.setCurrentIndex(type_index)

        self.mfg_input.setText(defaults.fabrikant)

        method_index = self.method_combo.findData(defaults.meetmethode)
        if method_index >= 0:
            self.method_combo.setCurrentIndex(method_index)

        instrument_index = self.instrument_combo.findData(defaults.instrument_code)
        if instrument_index >= 0:
            self.instrument_combo.setCurrentIndex(instrument_index)
        self._update_instrument_profile()

        freq_index = self.freq_combo.findData(defaults.meetfrequentie_hz)
        if freq_index >= 0:
            self.freq_combo.setCurrentIndex(freq_index)

        voltage_index = self.test_voltage_combo.findData(defaults.testspanning_vrms)
        if voltage_index >= 0:
            self.test_voltage_combo.setCurrentIndex(voltage_index)

        self.temp_input.setText(f"{defaults.temperatuur_c:g}")

        if self.meas_esr_unit.findText(defaults.esr_eenheid) >= 0:
            self.meas_esr_unit.setCurrentText(defaults.esr_eenheid)

    def apply_repeat_preset(self, preset: RepeatMeasurementPreset) -> None:
        """Vul alleen historische component- en meetcontext voor een nieuwe run."""
        self._apply_saved_defaults()

        if (
            preset.nominal_capacitance_unit
            and self.nom_cap_unit.findText(preset.nominal_capacitance_unit) >= 0
        ):
            self.nom_cap_unit.setCurrentText(preset.nominal_capacitance_unit)
        self.nom_cap_input.setText(
            "" if preset.nominal_capacitance_value is None
            else f"{preset.nominal_capacitance_value:g}"
        )
        self.tolerance_input.setText(
            "" if preset.tolerance_percent is None else f"{preset.tolerance_percent:g}"
        )
        self.nom_voltage_input.setText(
            "" if preset.rated_voltage_v is None else f"{preset.rated_voltage_v:g}"
        )

        if preset.technology:
            type_index = self.type_combo.findText(preset.technology)
            if type_index >= 0:
                self.type_combo.setCurrentIndex(type_index)
        self.mfg_input.setText(preset.manufacturer or "")
        self.series_input.setText(preset.series or "")

        if preset.measurement_method:
            method_index = self.method_combo.findData(preset.measurement_method)
            if method_index >= 0:
                self.method_combo.setCurrentIndex(method_index)

        if preset.instrument_key:
            instrument_index = self.instrument_combo.findData(preset.instrument_key)
            if instrument_index >= 0:
                self.instrument_combo.setCurrentIndex(instrument_index)
                self._update_instrument_profile()

        if preset.frequency_hz is not None:
            freq_index = self.freq_combo.findData(preset.frequency_hz)
            if freq_index >= 0:
                self.freq_combo.setCurrentIndex(freq_index)
        if preset.test_voltage_vrms is not None:
            voltage_index = self.test_voltage_combo.findData(preset.test_voltage_vrms)
            if voltage_index >= 0:
                self.test_voltage_combo.setCurrentIndex(voltage_index)
        self.temp_input.setText(
            "" if preset.temperature_c is None else f"{preset.temperature_c:g}"
        )

        # Nieuwe run: historische meetuitkomst en safety nooit overnemen.
        self.meas_cap_input.clear()
        self.meas_esr_input.clear()
        self.d_input.clear()
        self.safety_check.setChecked(False)
        self.out_of_range_check.setChecked(False)
        self.open_connection_check.setChecked(False)
        self.result_group.setVisible(False)
        self._laatste_resultaat_html = ""
        self._laatste_opslag_payload = None
        self.save_btn.setEnabled(False)

        self.repeat_banner.setText(
            self._t(
                "herhalen.banner",
                measurement_id=preset.source_measurement_id,
            )
        )
        self.repeat_banner.setVisible(True)

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

            out_of_range = self.out_of_range_check.isChecked()

            if out_of_range and not self.meas_cap_input.text().strip():
                # Alleen voor de bestaande assessment-API is 0,0 technisch nodig.
                # Voor storage bewaren we hieronder expliciet None/NULL.
                raw_meas_cap = None
                meas_cap = 0.0
            else:
                raw_meas_cap = parse_decimaal(self.meas_cap_input.text())
                meas_cap = raw_meas_cap

            if out_of_range and not self.meas_esr_input.text().strip():
                # Alleen voor de bestaande assessment-API is 0,0 technisch nodig.
                # Voor storage bewaren we hieronder expliciet None/NULL.
                raw_meas_esr = None
                meas_esr = 0.0
            else:
                raw_meas_esr = parse_decimaal(self.meas_esr_input.text())
                meas_esr = raw_meas_esr

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
                meetwaarde_buiten_bereik=out_of_range,
                taal=self.taal,
            )
            self._show_result(resultaat)

            self._laatste_opslag_payload = EsrMeasurementSaveData(
                nominal_capacitance_value=nom_cap,
                nominal_capacitance_unit=self.nom_cap_unit.currentText(),
                tolerance_percent=tolerance,
                rated_voltage_v=nom_voltage,
                technology=cond_type,
                manufacturer=fabrikant or None,
                series=serie or None,
                measurement_method=meetmethode,
                instrument_key=instrument_code,
                instrument_name=self.instrument_combo.currentText() or None,
                frequency_hz=freq_hz,
                test_voltage_vrms=testspanning_vrms,
                temperature_c=temp,
                safety_confirmed=True,
                measured_capacitance_value=raw_meas_cap,
                measured_capacitance_unit=self.meas_cap_unit.currentText(),
                measured_esr_value=raw_meas_esr,
                measured_esr_unit=self.meas_esr_unit.currentText(),
                dissipation_factor_d=d_value,
                out_of_range=out_of_range,
                open_suspected=self.open_connection_check.isChecked(),
                assessment=resultaat,
                reference=referentie,
            )
            self.save_btn.setEnabled(True)

        except ValueError as exc:
            QMessageBox.warning(self, self._t("fout.titel"), str(exc))
        except Exception as exc:
            QMessageBox.critical(
                self,
                self._t("fout.titel"),
                self._t("fout.onverwacht", bericht=str(exc)),
            )

    def _on_save_measurement(self) -> None:
        """Slaat uitsluitend de laatst beoordeelde, onveranderlijke meetrun op."""
        if self._laatste_opslag_payload is None:
            return

        try:
            saved = self._persistence_service.save_esr_measurement(
                self._laatste_opslag_payload
            )
            measurement_id = saved["measurement"].id
        except StorageError as exc:
            QMessageBox.critical(
                self,
                self._t("opslag.meting_opslaan_fout_titel"),
                self._t(
                    "opslag.meting_opslaan_fout_tekst",
                    bericht=str(exc),
                ),
            )
            return
        except Exception as exc:
            QMessageBox.critical(
                self,
                self._t("opslag.meting_opslaan_fout_titel"),
                self._t(
                    "opslag.meting_opslaan_fout_tekst",
                    bericht=str(exc),
                ),
            )
            return

        self._laatste_opslag_payload = None
        self.save_btn.setEnabled(False)
        QMessageBox.information(
            self,
            self._t("opslag.meting_opgeslagen_titel"),
            self._t(
                "opslag.meting_opgeslagen_tekst",
                measurement_id=measurement_id,
            ),
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
        if esr.factor is not None and esr.frequentie_wijkt_af:
            ref_freq = getattr(resultaat, "referentiefrequentie_hz", None)
            # De Beoordeling bewaart de referentiefrequentie momenteel niet apart.
            # De ingebouwde referentiebron gebruikt 100 kHz; toon daarom alleen
            # de meetfrequentie en markeer de factor ondubbelzinnig als indicatief.
            esr_factor = (
                f"{esr_factor}* ({_format_frequency(self.freq_combo.currentData())} gemeten; "
                f"referentiefrequentie wijkt af)"
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

        summary_text = self._t(
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
        if esr.factor is not None and esr.frequentie_wijkt_af:
            summary_text += "\n* Indicatieve ESR-vergelijking: meet- en referentiefrequentie verschillen."
        self.result_summary.setText(summary_text)

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
        defaults = laad_instellingen().esr_condensator
        if defaults.bevestig_wissen:
            antwoord = QMessageBox.question(
                self,
                self._t("dialog.wissen_titel"),
                self._t("dialog.wissen_tekst"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if antwoord != QMessageBox.StandardButton.Yes:
                return

        # Meetresultaten en toestand wissen; configuratiedefaults daarna herstellen.
        for widget in (
            self.meas_cap_input,
            self.meas_esr_input,
            self.d_input,
        ):
            widget.clear()

        self.safety_check.setChecked(False)
        self.out_of_range_check.setChecked(False)
        self.open_connection_check.setChecked(False)
        self.result_group.setVisible(False)
        self._laatste_resultaat_html = ""
        self._laatste_opslag_payload = None
        self.save_btn.setEnabled(False)
        self.repeat_banner.setVisible(False)

        self._apply_saved_defaults()

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
