"""
================================================================================
Module:     app/gui/dialogs/settings_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Validator (Windows)
Versie:     1.0.1
Datum:      2026-09-27
Auteur:     Ontwikkelaar

Doel:       Modale Settings-dialoog met tabs Algemeen, ESR / Condensator en
            Rapportage. Bewerkt een lokale kopie; Toepassen/OK leveren een
            nieuw AppInstellingen-object op zonder zelf beoordelingslogica uit
            te voeren.

Wijzigingen:
  v1.0.1 (2026-09-27)  Tabteksten expliciet leesbaar gemaakt in het donkere
                       thema, inclusief actieve/inactieve/hover-status.
  v1.0.0 (2026-09-27)  Eerste implementatie van de drie Settings-tabs en
                       bediening Herstellen/Annuleren/Toepassen/OK.
================================================================================
"""

from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.config.settings import (
    AlgemeneInstellingen,
    AppInstellingen,
    EENHEDEN_CAPACITEIT,
    EENHEDEN_ESR,
    EsrCondensatorInstellingen,
    MEETFREQUENTIES_HZ,
    MEETMETHODEN,
    RapportageInstellingen,
    TESTSPANNINGEN_VRMS,
)
from app.helpers.i18n import vertaal


class SettingsDialog(QDialog):
    """Bewerkt applicatie-instellingen zonder niet-toegepaste wijzigingen te lekken."""

    settings_applied = Signal(object)

    def __init__(self, instellingen: AppInstellingen, taal: str = "nl_NL", parent=None):
        super().__init__(parent)
        self.taal = taal
        self._basis = instellingen
        self._toegepast = instellingen

        self.setWindowTitle(self._t("settings.titel"))
        self.setModal(True)
        self.resize(650, 560)

        hoofd = QVBoxLayout(self)
        self.tabs = QTabWidget()
        # QTabBar erft op Windows niet altijd de gewenste tekstkleur uit het
        # centrale donkere thema. Houd deze lokale correctie beperkt tot tabs.
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                color: #f2f2f2;
                background-color: #333438;
                border: 1px solid #55575c;
                border-bottom: none;
                padding: 8px 14px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                color: #ffffff;
                background-color: #55575c;
            }
            QTabBar::tab:hover:!selected {
                color: #ffffff;
                background-color: #414247;
            }
            QTabWidget::pane {
                border: 1px solid #55575c;
                top: -1px;
            }
        """)
        self.tabs.addTab(self._build_algemeen_tab(), self._t("settings.tab.algemeen"))
        self.tabs.addTab(self._build_esr_tab(), self._t("settings.tab.esr"))
        self.tabs.addTab(self._build_rapportage_tab(), self._t("settings.tab.rapportage"))
        hoofd.addWidget(self.tabs)

        knoppen = QHBoxLayout()
        self.herstel_btn = QPushButton(self._t("settings.knop.herstellen"))
        self.annuleer_btn = QPushButton(self._t("settings.knop.annuleren"))
        self.toepassen_btn = QPushButton(self._t("settings.knop.toepassen"))
        self.ok_btn = QPushButton(self._t("settings.knop.ok"))

        self.herstel_btn.clicked.connect(self._herstel_actieve_tab)
        self.annuleer_btn.clicked.connect(self.reject)
        self.toepassen_btn.clicked.connect(self._toepassen)
        self.ok_btn.clicked.connect(self._ok)

        knoppen.addWidget(self.herstel_btn)
        knoppen.addStretch()
        knoppen.addWidget(self.annuleer_btn)
        knoppen.addWidget(self.toepassen_btn)
        knoppen.addWidget(self.ok_btn)
        hoofd.addLayout(knoppen)

        self._load_widgets(instellingen)

    def _t(self, sleutel: str, **kwargs):
        return vertaal(sleutel, taal=self.taal, **kwargs)

    @staticmethod
    def _select(combo: QComboBox, value) -> None:
        tekst = str(value)
        index = combo.findData(value)
        if index < 0:
            index = combo.findText(tekst)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _build_algemeen_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)

        self.taal_combo = QComboBox()
        self.taal_combo.addItem("Nederlands", "nl_NL")
        self.taal_combo.addItem("English", "en_US")
        form.addRow(self._t("settings.algemeen.taal"), self.taal_combo)

        self.thema_combo = QComboBox()
        self.thema_combo.addItem(self._t("settings.algemeen.thema_donker"), "dark")
        self.thema_combo.setEnabled(False)
        self.thema_combo.setToolTip(self._t("settings.algemeen.thema_tooltip"))
        form.addRow(self._t("settings.algemeen.thema"), self.thema_combo)

        self.tooltips_check = QCheckBox(self._t("settings.algemeen.tooltips"))
        form.addRow("", self.tooltips_check)
        return tab

    def _build_esr_tab(self) -> QWidget:
        tab = QWidget()
        form = QFormLayout(tab)

        self.cap_eenheid_combo = QComboBox()
        self.cap_eenheid_combo.addItems(EENHEDEN_CAPACITEIT)
        form.addRow(self._t("settings.esr.cap_eenheid"), self.cap_eenheid_combo)

        self.tolerantie_spin = QDoubleSpinBox()
        self.tolerantie_spin.setRange(0.0, 100.0)
        self.tolerantie_spin.setDecimals(1)
        self.tolerantie_spin.setSuffix(" %")
        form.addRow(self._t("settings.esr.tolerantie"), self.tolerantie_spin)

        self.werkspanning_spin = QDoubleSpinBox()
        self.werkspanning_spin.setRange(0.0, 10000.0)
        self.werkspanning_spin.setDecimals(1)
        self.werkspanning_spin.setSuffix(" V")
        self.werkspanning_spin.setSpecialValueText(self._t("settings.esr.geen_default"))
        form.addRow(self._t("settings.esr.werkspanning"), self.werkspanning_spin)

        self.type_combo = QComboBox()
        self.type_combo.addItems((
            "Aluminium elektrolytisch",
            "Aluminium elektrolytisch — Low ESR",
            "Aluminium elektrolytisch — Bipolair/NP",
            "Conductive polymer",
            "Hybrid polymer",
            "Tantaal elektrolytisch",
            "Tantaal polymer",
            "Film",
            "Keramisch / MLCC",
            "Supercondensator",
            "Onbekend",
            "Anders",
        ))
        form.addRow(self._t("settings.esr.type"), self.type_combo)

        self.fabrikant_edit = QLineEdit()
        form.addRow(self._t("settings.esr.fabrikant"), self.fabrikant_edit)

        self.meetmethode_combo = QComboBox()
        for code in MEETMETHODEN:
            self.meetmethode_combo.addItem(self._t(f"settings.meetmethode.{code}"), code)
        form.addRow(self._t("settings.esr.meetmethode"), self.meetmethode_combo)

        self.instrument_combo = QComboBox()
        self.instrument_combo.addItem("LCR-ST1 Smart Tweezer", "LCR_ST1")
        form.addRow(self._t("settings.esr.instrument"), self.instrument_combo)

        self.frequentie_combo = QComboBox()
        for waarde in MEETFREQUENTIES_HZ:
            self.frequentie_combo.addItem(f"{waarde:g} Hz", waarde)
        form.addRow(self._t("settings.esr.frequentie"), self.frequentie_combo)

        self.testspanning_combo = QComboBox()
        for waarde in TESTSPANNINGEN_VRMS:
            self.testspanning_combo.addItem(f"{waarde:g} Vrms", waarde)
        form.addRow(self._t("settings.esr.testspanning"), self.testspanning_combo)

        self.temperatuur_spin = QDoubleSpinBox()
        self.temperatuur_spin.setRange(-50.0, 150.0)
        self.temperatuur_spin.setDecimals(1)
        self.temperatuur_spin.setSuffix(" °C")
        form.addRow(self._t("settings.esr.temperatuur"), self.temperatuur_spin)

        self.esr_eenheid_combo = QComboBox()
        self.esr_eenheid_combo.addItems(EENHEDEN_ESR)
        form.addRow(self._t("settings.esr.esr_eenheid"), self.esr_eenheid_combo)

        self.bevestig_wissen_check = QCheckBox(self._t("settings.esr.bevestig_wissen"))
        form.addRow("", self.bevestig_wissen_check)
        return tab

    def _build_rapportage_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        uitleg = QLabel(self._t("settings.rapportage.uitleg"))
        uitleg.setWordWrap(True)
        layout.addWidget(uitleg)

        self.grafiek_check = QCheckBox(self._t("settings.rapportage.grafiek"))
        self.details_check = QCheckBox(self._t("settings.rapportage.details"))
        self.referentie_check = QCheckBox(self._t("settings.rapportage.referentie"))
        self.datum_check = QCheckBox(self._t("settings.rapportage.datum"))
        layout.addWidget(self.grafiek_check)
        layout.addWidget(self.details_check)
        layout.addWidget(self.referentie_check)
        layout.addWidget(self.datum_check)

        form = QFormLayout()
        self.werkplaats_edit = QLineEdit()
        form.addRow(self._t("settings.rapportage.werkplaats"), self.werkplaats_edit)
        layout.addLayout(form)
        layout.addStretch()
        return tab

    def _load_widgets(self, instellingen: AppInstellingen) -> None:
        self._select(self.taal_combo, instellingen.taal)
        self._select(self.thema_combo, instellingen.algemeen.thema)
        self.tooltips_check.setChecked(instellingen.algemeen.tooltips_ingeschakeld)

        esr = instellingen.esr_condensator
        self._select(self.cap_eenheid_combo, esr.capaciteitseenheid)
        self.tolerantie_spin.setValue(esr.tolerantie_percent)
        self.werkspanning_spin.setValue(esr.werkspanning_v or 0.0)
        self._select(self.type_combo, esr.condensatortype)
        self.fabrikant_edit.setText(esr.fabrikant)
        self._select(self.meetmethode_combo, esr.meetmethode)
        self._select(self.instrument_combo, esr.instrument_code)
        self._select(self.frequentie_combo, esr.meetfrequentie_hz)
        self._select(self.testspanning_combo, esr.testspanning_vrms)
        self.temperatuur_spin.setValue(esr.temperatuur_c)
        self._select(self.esr_eenheid_combo, esr.esr_eenheid)
        self.bevestig_wissen_check.setChecked(esr.bevestig_wissen)

        rapport = instellingen.rapportage
        self.grafiek_check.setChecked(rapport.grafiek_opnemen)
        self.details_check.setChecked(rapport.technische_details_opnemen)
        self.referentie_check.setChecked(rapport.referentiebron_opnemen)
        self.datum_check.setChecked(rapport.datum_tijd_opnemen)
        self.werkplaats_edit.setText(rapport.werkplaats_bedrijf)

    def _widgets_naar_instellingen(self) -> AppInstellingen:
        werkspanning = self.werkspanning_spin.value()
        if werkspanning == 0.0:
            werkspanning = None

        algemeen = AlgemeneInstellingen(
            thema=self.thema_combo.currentData() or "dark",
            tooltips_ingeschakeld=self.tooltips_check.isChecked(),
        )
        esr = EsrCondensatorInstellingen(
            capaciteitseenheid=self.cap_eenheid_combo.currentText(),
            tolerantie_percent=self.tolerantie_spin.value(),
            werkspanning_v=werkspanning,
            condensatortype=self.type_combo.currentText(),
            fabrikant=self.fabrikant_edit.text().strip(),
            meetmethode=self.meetmethode_combo.currentData(),
            instrument_code=self.instrument_combo.currentData(),
            meetfrequentie_hz=self.frequentie_combo.currentData(),
            testspanning_vrms=self.testspanning_combo.currentData(),
            temperatuur_c=self.temperatuur_spin.value(),
            esr_eenheid=self.esr_eenheid_combo.currentText(),
            bevestig_wissen=self.bevestig_wissen_check.isChecked(),
        )
        rapportage = RapportageInstellingen(
            grafiek_opnemen=self.grafiek_check.isChecked(),
            technische_details_opnemen=self.details_check.isChecked(),
            referentiebron_opnemen=self.referentie_check.isChecked(),
            datum_tijd_opnemen=self.datum_check.isChecked(),
            werkplaats_bedrijf=self.werkplaats_edit.text().strip(),
        )
        return replace(
            self._toegepast,
            taal=self.taal_combo.currentData(),
            algemeen=algemeen,
            esr_condensator=esr,
            rapportage=rapportage,
        )

    def _toepassen(self) -> None:
        self._toegepast = self._widgets_naar_instellingen()
        self.settings_applied.emit(self._toegepast)

    def _ok(self) -> None:
        self._toepassen()
        self.accept()

    def _herstel_actieve_tab(self) -> None:
        antwoord = QMessageBox.question(
            self,
            self._t("settings.herstellen.titel"),
            self._t("settings.herstellen.tekst"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if antwoord != QMessageBox.StandardButton.Yes:
            return

        index = self.tabs.currentIndex()
        if index == 0:
            standaard = replace(
                self._widgets_naar_instellingen(),
                taal="nl_NL",
                algemeen=AlgemeneInstellingen(),
            )
        elif index == 1:
            standaard = replace(
                self._widgets_naar_instellingen(),
                esr_condensator=EsrCondensatorInstellingen(),
            )
        else:
            standaard = replace(
                self._widgets_naar_instellingen(),
                rapportage=RapportageInstellingen(),
            )
        self._load_widgets(standaard)

    @property
    def toegepaste_instellingen(self) -> AppInstellingen:
        return self._toegepast
