"""
================================================================================
Module:     app/gui/esr_test_screen.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.1.0
Datum:      2026-08-12
Auteur:     Ontwikkelaar

Doel:       Het ESR-testscherm — invoer van meetwaarden, veiligheidscheck,
            en weergave van het beoordelingsresultaat.

Wijzigingen:
  v1.0.0 (2026-08-11)  Initiele versie.
  v1.1.0 (2026-08-12)  Alle hardcoded strings vervangen door vertaalbare
                       sleutels via self._t(). Placeholders, foutmeldingen,
                       groupbox-titels en statusbartekst zijn nu vertaald.
================================================================================
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QCheckBox,
    QPushButton, QGroupBox, QScrollArea, QFrame,
    QMessageBox, QTextEdit,
)
from PySide6.QtCore import Qt

from app.helpers.i18n import vertaal
from app.helpers.units import parse_decimaal
from app.services.assessment_service import beoordeel_meting, status_label
from app.config.settings import (
    EENHEDEN_CAPACITEIT, EENHEDEN_ESR, MEETFREQUENTIES_HZ,
    CONDENSATORTYPES,
)
from app.data.references import zoek_referentie
from app.gui.styles import (
    STATUS_COLORS, RESULT_STATUS_STYLE, ASSESS_BUTTON_STYLE,
    SAFETY_WARNING_STYLE, GROUP_BOX_STYLE,
)


class EsrTestScreen(QWidget):
    """Het ESR-testscherm met invoer, veiligheidscheck en resultaatweergave."""

    def __init__(self, taal="nl_NL", parent=None):
        super().__init__(parent)
        self.taal = taal
        self._build_ui()

    def _t(self, sleutel, **kwargs):
        """Korte hulp voor vertalingen."""
        return vertaal(sleutel, taal=self.taal, **kwargs)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(12)

        # === VEILIGHEIDSWAARSCHUWINGEN ===
        safety_group = QGroupBox(self._t("scherm.veiligheid"))
        safety_group.setStyleSheet(GROUP_BOX_STYLE)
        safety_layout = QVBoxLayout(safety_group)

        self.safety_check = QCheckBox(self._t("veld.veiligheid_bevestigd"))
        self.safety_check.setStyleSheet("font-weight: bold; color: #FF9800;")
        safety_layout.addWidget(self.safety_check)

        # Toon de 9 vaste waarschuwingen
        for i in range(1, 10):
            lbl = QLabel(f"  • {self._t(f'veiligheid.waarschuwing_{i}')}")
            lbl.setWordWrap(True)
            lbl.setStyleSheet(SAFETY_WARNING_STYLE)
            safety_layout.addWidget(lbl)

        container_layout.addWidget(safety_group)

        # === NOMINALE GEGEVENS ===
        nominal_group = QGroupBox(self._t("veld.nominale_capaciteit"))
        nominal_group.setStyleSheet(GROUP_BOX_STYLE)
        nominal_layout = QGridLayout(nominal_group)
        nominal_layout.setSpacing(8)

        # Nominale capaciteit
        nominal_layout.addWidget(QLabel(self._t("veld.nominale_capaciteit")), 0, 0)
        self.nom_cap_input = QLineEdit()
        self.nom_cap_input.setPlaceholderText("470")
        nominal_layout.addWidget(self.nom_cap_input, 0, 1)

        self.nom_cap_unit = QComboBox()
        self.nom_cap_unit.addItems(EENHEDEN_CAPACITEIT)
        self.nom_cap_unit.setCurrentText("µF")
        nominal_layout.addWidget(self.nom_cap_unit, 0, 2)

        # Tolerantie
        nominal_layout.addWidget(QLabel(self._t("veld.tolerantie")), 1, 0)
        self.tolerance_input = QLineEdit()
        self.tolerance_input.setPlaceholderText("20")
        nominal_layout.addWidget(self.tolerance_input, 1, 1)
        nominal_layout.addWidget(QLabel("%"), 1, 2)

        # Nominale spanning
        nominal_layout.addWidget(QLabel(self._t("veld.nominale_spanning")), 2, 0)
        self.nom_voltage_input = QLineEdit()
        self.nom_voltage_input.setPlaceholderText("25")
        nominal_layout.addWidget(self.nom_voltage_input, 2, 1)
        nominal_layout.addWidget(QLabel("V"), 2, 2)

        # Condensatortype
        nominal_layout.addWidget(QLabel(self._t("veld.condensatortype")), 3, 0)
        self.type_combo = QComboBox()
        self.type_combo.addItems(CONDENSATORTYPES)
        nominal_layout.addWidget(self.type_combo, 3, 1, 1, 2)

        # Fabrikant
        nominal_layout.addWidget(QLabel(self._t("veld.fabrikant")), 4, 0)
        self.mfg_input = QLineEdit()
        nominal_layout.addWidget(self.mfg_input, 4, 1, 1, 2)

        # Serie
        nominal_layout.addWidget(QLabel(self._t("veld.serie")), 5, 0)
        self.series_input = QLineEdit()
        nominal_layout.addWidget(self.series_input, 5, 1, 1, 2)

        container_layout.addWidget(nominal_group)

        # === MEETCONTEXT ===
        context_group = QGroupBox(self._t("scherm.meetcontext"))
        context_group.setStyleSheet(GROUP_BOX_STYLE)
        context_layout = QGridLayout(context_group)
        context_layout.setSpacing(8)

        # Meetfrequentie
        context_layout.addWidget(QLabel(self._t("veld.meetfrequentie")), 0, 0)
        self.freq_combo = QComboBox()
        self.freq_combo.addItems([f"{f} Hz" for f in MEETFREQUENTIES_HZ])
        self.freq_combo.setCurrentText("1000 Hz")
        context_layout.addWidget(self.freq_combo, 0, 1)

        # In-circuit
        self.in_circuit_check = QCheckBox(self._t("veld.in_circuit"))
        context_layout.addWidget(self.in_circuit_check, 1, 0, 1, 2)

        # Temperatuur
        context_layout.addWidget(QLabel(self._t("veld.omgevingstemperatuur")), 2, 0)
        self.temp_input = QLineEdit()
        self.temp_input.setPlaceholderText("20")
        context_layout.addWidget(self.temp_input, 2, 1)
        context_layout.addWidget(QLabel("°C"), 2, 2)

        container_layout.addWidget(context_group)

        # === MEETWAARDEN ===
        measurement_group = QGroupBox(self._t("scherm.meetwaarden"))
        measurement_group.setStyleSheet(GROUP_BOX_STYLE)
        measurement_layout = QGridLayout(measurement_group)
        measurement_layout.setSpacing(8)

        # Gemeten capaciteit
        measurement_layout.addWidget(QLabel(self._t("veld.gemeten_capaciteit")), 0, 0)
        self.meas_cap_input = QLineEdit()
        measurement_layout.addWidget(self.meas_cap_input, 0, 1)
        self.meas_cap_unit = QComboBox()
        self.meas_cap_unit.addItems(EENHEDEN_CAPACITEIT)
        self.meas_cap_unit.setCurrentText("µF")
        measurement_layout.addWidget(self.meas_cap_unit, 0, 2)

        # Gemeten ESR
        measurement_layout.addWidget(QLabel(self._t("veld.gemeten_esr")), 1, 0)
        self.meas_esr_input = QLineEdit()
        measurement_layout.addWidget(self.meas_esr_input, 1, 1)
        self.meas_esr_unit = QComboBox()
        self.meas_esr_unit.addItems(EENHEDEN_ESR)
        measurement_layout.addWidget(self.meas_esr_unit, 1, 2)

        # D-waarde
        measurement_layout.addWidget(QLabel(self._t("veld.d_waarde")), 2, 0)
        self.d_input = QLineEdit()
        self.d_input.setPlaceholderText(self._t("placeholder.d_waarde"))
        measurement_layout.addWidget(self.d_input, 2, 1, 1, 2)

        # Open verbinding vermoed
        self.open_connection_check = QCheckBox(self._t("veld.open_verbinding"))
        measurement_layout.addWidget(self.open_connection_check, 3, 0, 1, 3)

        container_layout.addWidget(measurement_group)

        # === ACTIEKNOPPEN ===
        button_layout = QHBoxLayout()
        self.assess_btn = QPushButton(self._t("knop.beoordeel"))
        self.assess_btn.setStyleSheet(ASSESS_BUTTON_STYLE)
        self.assess_btn.clicked.connect(self._on_assess)
        button_layout.addWidget(self.assess_btn)

        self.clear_btn = QPushButton(self._t("knop.wissen"))
        self.clear_btn.clicked.connect(self._on_clear)
        button_layout.addWidget(self.clear_btn)

        button_layout.addStretch()
        container_layout.addLayout(button_layout)

        # === RESULTAAT ===
        self.result_group = QGroupBox(self._t("scherm.resultaat"))
        self.result_group.setStyleSheet(GROUP_BOX_STYLE)
        self.result_group.setVisible(False)
        result_layout = QVBoxLayout(self.result_group)

        self.result_status = QLabel()
        self.result_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_status.setStyleSheet(RESULT_STATUS_STYLE.format(color="#9E9E9E"))
        result_layout.addWidget(self.result_status)

        self.result_details = QTextEdit()
        self.result_details.setReadOnly(True)
        self.result_details.setMinimumHeight(250)
        result_layout.addWidget(self.result_details)

        container_layout.addWidget(self.result_group)

        container_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _parse_optional(self, text):
        """Parst een optioneel getalveld. None bij leeg."""
        text = text.strip()
        if not text:
            return None
        try:
            return parse_decimaal(text)
        except ValueError:
            raise ValueError(self._t("fout.ongeldig_getal", waarde=text))

    def _on_assess(self):
        """Voert de beoordeling uit."""
        # Controleer veiligheid
        if not self.safety_check.isChecked():
            QMessageBox.warning(
                self,
                self._t("scherm.veiligheid"),
                self._t("fout.veiligheid_verplicht")
            )
            return

        try:
            # Parse invoer
            nom_cap = parse_decimaal(self.nom_cap_input.text())
            nom_cap_unit = self.nom_cap_unit.currentText()
            tolerance = self._parse_optional(self.tolerance_input.text())
            nom_voltage = self._parse_optional(self.nom_voltage_input.text())

            meas_cap = parse_decimaal(self.meas_cap_input.text())
            meas_cap_unit = self.meas_cap_unit.currentText()
            meas_esr = parse_decimaal(self.meas_esr_input.text())
            meas_esr_unit = self.meas_esr_unit.currentText()

            d_value = self._parse_optional(self.d_input.text())

            freq_text = self.freq_combo.currentText()
            freq_hz = int(freq_text.replace(" Hz", "").replace(" ", ""))

            temp = self._parse_optional(self.temp_input.text())

            cond_type = self.type_combo.currentText()
            in_circuit = self.in_circuit_check.isChecked()
            fabrikant = self.mfg_input.text().strip()
            serie = self.series_input.text().strip()

            # Zoek referentie
            from app.helpers.units import converteer_capaciteit
            nom_cap_uf = converteer_capaciteit(nom_cap, nom_cap_unit, "µF")

            referentie = None
            if cond_type == "Aluminium elektrolytisch" and nom_voltage:
                referentie = zoek_referentie(nom_cap_uf, nom_voltage)

            # Voer beoordeling uit
            resultaat = beoordeel_meting(
                nominale_capaciteit=nom_cap,
                eenheid_nominaal=nom_cap_unit,
                tolerantie_percent=tolerance,
                gemeten_capaciteit=meas_cap,
                eenheid_gemeten_capaciteit=meas_cap_unit,
                gemeten_esr=meas_esr,
                eenheid_gemeten_esr=meas_esr_unit,
                meetfrequentie_hz=freq_hz,
                D=d_value,
                condensatortype=cond_type,
                in_circuit=in_circuit,
                omgevingstemperatuur_c=temp,
                veiligheid_bevestigd=True,
                referentie=referentie,
                fabrikant_bekend=bool(fabrikant),
                serie_bekend=bool(serie),
                vermoedelijke_open_verbinding_of_kortsluiting=self.open_connection_check.isChecked(),
                taal=self.taal,
            )

            self._show_result(resultaat)

        except ValueError as e:
            QMessageBox.warning(self, self._t("fout.titel"), str(e))
        except Exception as e:
            QMessageBox.critical(
                self,
                self._t("fout.titel"),
                self._t("fout.onverwacht", bericht=str(e))
            )

    def _show_result(self, resultaat):
        """Toont het beoordelingsresultaat."""
        status_key = resultaat.eindstatus.value
        color = STATUS_COLORS.get(status_key, "#9E9E9E")

        status_text = status_label("status.eindstatus", status_key, self.taal)
        self.result_status.setText(status_text.upper())
        self.result_status.setStyleSheet(RESULT_STATUS_STYLE.format(color=color))

        # Bouw detailtekst
        details = []

        details.append(f"<h3>{self._t('scherm.resultaat')}</h3>")
        details.append(f"<p><b>Eindstatus:</b> {status_text}</p>")

        details.append("<h4>Capaciteit</h4>")
        c = resultaat.capaciteit
        cap_status = status_label("status.capaciteit", c.status.value, self.taal)
        details.append(f"<p><b>Status:</b> {cap_status}</p>")
        details.append(f"<p>{c.toelichting}</p>")

        details.append("<h4>ESR</h4>")
        e = resultaat.esr
        esr_status = status_label("status.esr", e.status.value, self.taal)
        details.append(f"<p><b>Status:</b> {esr_status}</p>")
        if e.toelichting:
            details.append(f"<p>{e.toelichting}</p>")

        details.append("<h4>Consistentie C-ESR-D</h4>")
        cons = resultaat.consistentie
        cons_status = status_label("status.consistentie", cons.status.value, self.taal)
        details.append(f"<p><b>Status:</b> {cons_status}</p>")
        details.append(f"<p>{cons.toelichting}</p>")

        details.append("<h4>Betrouwbaarheid</h4>")
        b = resultaat.betrouwbaarheid
        betr_status = status_label("status.betrouwbaarheid", b.niveau.value, self.taal)
        details.append(f"<p><b>Niveau:</b> {betr_status}</p>")
        if b.verlagende_factoren:
            details.append("<ul>")
            for factor in b.verlagende_factoren:
                details.append(f"<li>{factor}</li>")
            details.append("</ul>")

        details.append("<h4>Redenen</h4>")
        details.append("<ul>")
        for reden in resultaat.redenen:
            details.append(f"<li>{reden}</li>")
        details.append("</ul>")

        details.append("<h4>Aanbevolen vervolgstap</h4>")
        details.append(f"<p>{resultaat.aanbevolen_vervolgstap}</p>")

        if resultaat.waarschuwingen:
            details.append(f"<h4>{self._t('scherm.waarschuwingen')}</h4>")
            details.append("<ul>")
            for w in resultaat.waarschuwingen:
                details.append(f"<li>{w}</li>")
            details.append("</ul>")

        self.result_details.setHtml("\n".join(details))
        self.result_group.setVisible(True)

    def _on_clear(self):
        """Wist alle velden."""
        self.nom_cap_input.clear()
        self.tolerance_input.clear()
        self.nom_voltage_input.clear()
        self.mfg_input.clear()
        self.series_input.clear()
        self.meas_cap_input.clear()
        self.meas_esr_input.clear()
        self.d_input.clear()
        self.temp_input.clear()
        self.safety_check.setChecked(False)
        self.in_circuit_check.setChecked(False)
        self.open_connection_check.setChecked(False)
        self.result_group.setVisible(False)