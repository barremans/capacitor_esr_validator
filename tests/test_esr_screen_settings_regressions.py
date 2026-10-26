"""
================================================================================
Module:     tests/test_esr_screen_settings_regressions.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.5.1
Datum:      2026-10-26
Auteur:     Ontwikkelaar

Doel:       GUI-regressietests voor opgeslagen ESR/Condensator-defaults en
            de optionele bevestiging bij Wissen.

Wijzigingen:
  v1.0.0 t/m v1.5.0  zie eerdere versies.
  v1.5.1 (2026-10-26) Chat 4 / 4C: twee tests voor de familie-check in
                       _on_assess. Low ESR krijgt een referentie;
                       tantaal krijgt geen referentie (maar wel de
                       waarschuwing uit de assessment-service).
================================================================================
"""

import os
from dataclasses import replace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox

import app.gui.esr_test_screen as esr_screen_module
from app.config.settings import AppInstellingen
from app.gui.esr_test_screen import EsrTestScreen
from app.storage.models import Meetstatus


def _app():
    return QApplication.instance() or QApplication([])


def _instellingen(**wijzigingen):
    basis = AppInstellingen()
    return replace(
        basis,
        esr_condensator=replace(basis.esr_condensator, **wijzigingen),
    )


def test_opgeslagen_defaults_worden_op_esr_scherm_toegepast(monkeypatch):
    _app()
    instellingen = _instellingen(
        capaciteitseenheid="mF",
        tolerantie_percent=15.0,
        werkspanning_v=35.0,
        condensatortype="Aluminium elektrolytisch",
        fabrikant="Testfabrikant",
        meetmethode="ONE_LEG",
        instrument_code="LCR_ST1",
        meetfrequentie_hz=10_000,
        testspanning_vrms=0.6,
        temperatuur_c=27.0,
        esr_eenheid="Ω",
        bevestig_wissen=True,
    )
    monkeypatch.setattr(esr_screen_module, "laad_instellingen", lambda: instellingen)

    screen = EsrTestScreen()

    assert screen.nom_cap_unit.currentText() == "mF"
    assert screen.meas_cap_unit.currentText() == "mF"
    assert screen.tolerance_input.text() == "15"
    assert screen.nom_voltage_input.text() == "35"
    assert screen.type_combo.currentText() == "Aluminium elektrolytisch"
    assert screen.mfg_input.text() == "Testfabrikant"
    assert screen.method_combo.currentData() == "ONE_LEG"
    assert screen.instrument_combo.currentData() == "LCR_ST1"
    assert screen.freq_combo.currentData() == 10_000
    assert screen.test_voltage_combo.currentData() == 0.6
    assert screen.temp_input.text() == "27"
    assert screen.meas_esr_unit.currentText() == "Ω"


def test_wissen_met_bevestiging_nee_behoudt_invoer(monkeypatch):
    _app()
    instellingen = _instellingen(bevestig_wissen=True)
    monkeypatch.setattr(esr_screen_module, "laad_instellingen", lambda: instellingen)
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.No,
    )

    screen = EsrTestScreen()
    screen.nom_cap_input.setText("470")
    screen.meas_cap_input.setText("455")
    screen.meas_esr_input.setText("0.08")
    screen.d_input.setText("0.12")
    screen.safety_check.setChecked(True)
    screen.out_of_range_check.setChecked(True)
    screen.open_connection_check.setChecked(True)

    screen._on_clear()

    assert screen.nom_cap_input.text() == "470"
    assert screen.meas_cap_input.text() == "455"
    assert screen.meas_esr_input.text() == "0.08"
    assert screen.d_input.text() == "0.12"
    assert screen.safety_check.isChecked()
    assert screen.out_of_range_check.isChecked()
    assert screen.open_connection_check.isChecked()


def test_wissen_met_bevestiging_ja_wist_meting_en_herstelt_defaults(monkeypatch):
    _app()
    instellingen = _instellingen(
        capaciteitseenheid="mF",
        tolerantie_percent=10.0,
        werkspanning_v=50.0,
        fabrikant="Defaultfabrikant",
        meetmethode="ONE_LEG",
        meetfrequentie_hz=10_000,
        testspanning_vrms=0.6,
        temperatuur_c=25.0,
        esr_eenheid="Ω",
        bevestig_wissen=True,
    )
    monkeypatch.setattr(esr_screen_module, "laad_instellingen", lambda: instellingen)
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )

    screen = EsrTestScreen()
    screen.tolerance_input.setText("33")
    screen.nom_voltage_input.setText("16")
    screen.mfg_input.setText("Gewijzigd")
    screen.method_combo.setCurrentIndex(
        screen.method_combo.findData("IN_CIRCUIT")
    )
    screen.freq_combo.setCurrentIndex(screen.freq_combo.findData(100))
    screen.test_voltage_combo.setCurrentIndex(
        screen.test_voltage_combo.findData(0.3)
    )
    screen.temp_input.setText("40")
    screen.meas_cap_unit.setCurrentText("µF")
    screen.meas_esr_unit.setCurrentText("mΩ")

    screen.meas_cap_input.setText("450")
    screen.meas_esr_input.setText("75")
    screen.d_input.setText("0.2")
    screen.safety_check.setChecked(True)
    screen.out_of_range_check.setChecked(True)
    screen.open_connection_check.setChecked(True)
    screen._laatste_resultaat_html = "<p>test</p>"
    screen.result_group.setVisible(True)

    screen._on_clear()

    assert screen.meas_cap_input.text() == ""
    assert screen.meas_esr_input.text() == ""
    assert screen.d_input.text() == ""
    assert not screen.safety_check.isChecked()
    assert not screen.out_of_range_check.isChecked()
    assert not screen.open_connection_check.isChecked()
    assert not screen.result_group.isVisible()
    assert screen._laatste_resultaat_html == ""

    assert screen.nom_cap_unit.currentText() == "mF"
    assert screen.meas_cap_unit.currentText() == "mF"
    assert screen.tolerance_input.text() == "10"
    assert screen.nom_voltage_input.text() == "50"
    assert screen.mfg_input.text() == "Defaultfabrikant"
    assert screen.method_combo.currentData() == "ONE_LEG"
    assert screen.freq_combo.currentData() == 10_000
    assert screen.test_voltage_combo.currentData() == 0.6
    assert screen.temp_input.text() == "25"
    assert screen.meas_esr_unit.currentText() == "Ω"


def test_wissen_zonder_bevestiging_toont_geen_dialoog(monkeypatch):
    _app()
    instellingen = _instellingen(bevestig_wissen=False)
    monkeypatch.setattr(esr_screen_module, "laad_instellingen", lambda: instellingen)

    aangeroepen = []

    def onverwachte_vraag(*args, **kwargs):
        aangeroepen.append(True)
        return QMessageBox.StandardButton.No

    monkeypatch.setattr(QMessageBox, "question", onverwachte_vraag)

    screen = EsrTestScreen()
    screen.meas_cap_input.setText("470")
    screen.meas_esr_input.setText("80")
    screen.d_input.setText("0.1")
    screen.safety_check.setChecked(True)

    screen._on_clear()

    assert aangeroepen == []
    assert screen.meas_cap_input.text() == ""
    assert screen.meas_esr_input.text() == ""
    assert screen.d_input.text() == ""
    assert not screen.safety_check.isChecked()

def _vul_geldige_meting_in(screen):
    """Vult de minimaal benodigde invoer voor _on_assess zonder echte referentie-eis."""
    screen.nom_cap_input.setText("470")
    screen.nom_voltage_input.setText("25")
    screen.meas_cap_input.setText("465")
    screen.meas_esr_input.setText("100")
    screen.safety_check.setChecked(True)


def test_normale_meting_laat_lege_esr_niet_toe(monkeypatch):
    """Zonder OL blijft gemeten ESR verplicht."""
    instellingen = _instellingen(bevestig_wissen=False)
    monkeypatch.setattr(esr_screen_module, "laad_instellingen", lambda: instellingen)

    service_aangeroepen = []
    monkeypatch.setattr(
        esr_screen_module,
        "beoordeel_meting",
        lambda **kwargs: service_aangeroepen.append(kwargs),
    )

    waarschuwingen = []
    monkeypatch.setattr(
        esr_screen_module.QMessageBox,
        "warning",
        lambda *args, **kwargs: waarschuwingen.append((args, kwargs)),
    )

    screen = EsrTestScreen()
    _vul_geldige_meting_in(screen)
    screen.meas_esr_input.clear()
    screen.out_of_range_check.setChecked(False)

    screen._on_assess()

    assert waarschuwingen
    assert service_aangeroepen == []


def test_normale_meting_laat_lege_gemeten_capaciteit_niet_toe(monkeypatch):
    """Zonder OL blijft gemeten capaciteit verplicht."""
    instellingen = _instellingen(bevestig_wissen=False)
    monkeypatch.setattr(esr_screen_module, "laad_instellingen", lambda: instellingen)

    service_aangeroepen = []
    monkeypatch.setattr(
        esr_screen_module,
        "beoordeel_meting",
        lambda **kwargs: service_aangeroepen.append(kwargs),
    )

    waarschuwingen = []
    monkeypatch.setattr(
        esr_screen_module.QMessageBox,
        "warning",
        lambda *args, **kwargs: waarschuwingen.append((args, kwargs)),
    )

    screen = EsrTestScreen()
    _vul_geldige_meting_in(screen)
    screen.meas_cap_input.clear()
    screen.out_of_range_check.setChecked(False)

    screen._on_assess()

    assert waarschuwingen
    assert service_aangeroepen == []


def test_ol_out_of_range_laat_beide_lege_meetvelden_toe(monkeypatch):
    """Bij OL mogen capaciteit en ESR tegelijk leeg zijn."""
    instellingen = _instellingen(bevestig_wissen=False)
    monkeypatch.setattr(esr_screen_module, "laad_instellingen", lambda: instellingen)
    monkeypatch.setattr(esr_screen_module, "zoek_referentie", lambda *args, **kwargs: None)

    doorgestuurd = {}

    class FakeResultaat:
        pass

    def fake_beoordeel_meting(**kwargs):
        doorgestuurd.update(kwargs)
        return FakeResultaat()

    monkeypatch.setattr(esr_screen_module, "beoordeel_meting", fake_beoordeel_meting)
    monkeypatch.setattr(EsrTestScreen, "_show_result", lambda self, resultaat: None)

    waarschuwingen = []
    monkeypatch.setattr(
        esr_screen_module.QMessageBox,
        "warning",
        lambda *args, **kwargs: waarschuwingen.append((args, kwargs)),
    )

    screen = EsrTestScreen()
    _vul_geldige_meting_in(screen)
    screen.meas_cap_input.clear()
    screen.meas_esr_input.clear()
    screen.out_of_range_check.setChecked(True)

    screen._on_assess()

    assert waarschuwingen == []
    assert doorgestuurd["meetwaarde_buiten_bereik"] is True
    assert doorgestuurd["gemeten_capaciteit"] == 0.0
    assert doorgestuurd["gemeten_esr"] == 0.0


def test_ol_out_of_range_laat_ongeldige_esr_tekst_niet_toe(monkeypatch):
    """OL versoepelt alleen lege invoer; tekst als 'abc' blijft ongeldig."""
    instellingen = _instellingen(bevestig_wissen=False)
    monkeypatch.setattr(esr_screen_module, "laad_instellingen", lambda: instellingen)

    service_aangeroepen = []
    monkeypatch.setattr(
        esr_screen_module,
        "beoordeel_meting",
        lambda **kwargs: service_aangeroepen.append(kwargs),
    )

    waarschuwingen = []
    monkeypatch.setattr(
        esr_screen_module.QMessageBox,
        "warning",
        lambda *args, **kwargs: waarschuwingen.append((args, kwargs)),
    )

    screen = EsrTestScreen()
    _vul_geldige_meting_in(screen)
    screen.meas_esr_input.setText("abc")
    screen.out_of_range_check.setChecked(True)

    screen._on_assess()

    assert waarschuwingen
    assert service_aangeroepen == []


def test_ol_out_of_range_laat_ongeldige_capaciteitstekst_niet_toe(monkeypatch):
    """OL versoepelt alleen lege invoer; ongeldige capaciteitstekst blijft fout."""
    instellingen = _instellingen(bevestig_wissen=False)
    monkeypatch.setattr(esr_screen_module, "laad_instellingen", lambda: instellingen)

    service_aangeroepen = []
    monkeypatch.setattr(
        esr_screen_module,
        "beoordeel_meting",
        lambda **kwargs: service_aangeroepen.append(kwargs),
    )

    waarschuwingen = []
    monkeypatch.setattr(
        esr_screen_module.QMessageBox,
        "warning",
        lambda *args, **kwargs: waarschuwingen.append((args, kwargs)),
    )

    screen = EsrTestScreen()
    _vul_geldige_meting_in(screen)
    screen.meas_cap_input.setText("abc")
    screen.out_of_range_check.setChecked(True)

    screen._on_assess()

    assert waarschuwingen
    assert service_aangeroepen == []


def test_ol_out_of_range_laat_lege_gemeten_capaciteit_toe(monkeypatch):
    """Bij OL/out-of-range mag een fictieve gemeten capaciteit niet verplicht zijn."""
    instellingen = _instellingen(bevestig_wissen=False)
    monkeypatch.setattr(esr_screen_module, "laad_instellingen", lambda: instellingen)
    monkeypatch.setattr(esr_screen_module, "zoek_referentie", lambda *args, **kwargs: None)

    doorgestuurd = {}

    class FakeResultaat:
        pass

    def fake_beoordeel_meting(**kwargs):
        doorgestuurd.update(kwargs)
        return FakeResultaat()

    monkeypatch.setattr(esr_screen_module, "beoordeel_meting", fake_beoordeel_meting)
    monkeypatch.setattr(EsrTestScreen, "_show_result", lambda self, resultaat: None)

    waarschuwingen = []
    monkeypatch.setattr(
        esr_screen_module.QMessageBox,
        "warning",
        lambda *args, **kwargs: waarschuwingen.append((args, kwargs)),
    )

    screen = EsrTestScreen()
    _vul_geldige_meting_in(screen)
    screen.meas_cap_input.clear()
    screen.out_of_range_check.setChecked(True)
    screen.open_connection_check.setChecked(False)

    screen._on_assess()

    assert waarschuwingen == []
    assert doorgestuurd["meetwaarde_buiten_bereik"] is True


def test_ol_out_of_range_laat_lege_esr_toe(monkeypatch):
    """Bij OL/out-of-range mag een fictieve numerieke ESR niet verplicht zijn."""
    instellingen = _instellingen(bevestig_wissen=False)
    monkeypatch.setattr(esr_screen_module, "laad_instellingen", lambda: instellingen)
    monkeypatch.setattr(esr_screen_module, "zoek_referentie", lambda *args, **kwargs: None)

    doorgestuurd = {}

    class FakeResultaat:
        pass

    def fake_beoordeel_meting(**kwargs):
        doorgestuurd.update(kwargs)
        return FakeResultaat()

    monkeypatch.setattr(esr_screen_module, "beoordeel_meting", fake_beoordeel_meting)
    monkeypatch.setattr(EsrTestScreen, "_show_result", lambda self, resultaat: None)

    waarschuwingen = []
    monkeypatch.setattr(
        esr_screen_module.QMessageBox,
        "warning",
        lambda *args, **kwargs: waarschuwingen.append((args, kwargs)),
    )

    screen = EsrTestScreen()
    _vul_geldige_meting_in(screen)
    screen.meas_esr_input.clear()
    screen.out_of_range_check.setChecked(True)
    screen.open_connection_check.setChecked(False)

    screen._on_assess()

    assert waarschuwingen == []
    assert doorgestuurd["meetwaarde_buiten_bereik"] is True


def test_ol_out_of_range_wordt_afzonderlijk_doorgestuurd(monkeypatch):
    _app()
    instellingen = _instellingen(bevestig_wissen=False)
    monkeypatch.setattr(esr_screen_module, "laad_instellingen", lambda: instellingen)
    monkeypatch.setattr(esr_screen_module, "zoek_referentie", lambda *args, **kwargs: None)

    ontvangen = {}

    class FakeResultaat:
        pass

    def fake_beoordeel_meting(**kwargs):
        ontvangen.update(kwargs)
        return FakeResultaat()

    monkeypatch.setattr(esr_screen_module, "beoordeel_meting", fake_beoordeel_meting)
    monkeypatch.setattr(EsrTestScreen, "_show_result", lambda self, resultaat: None)

    screen = EsrTestScreen()
    _vul_geldige_meting_in(screen)
    screen.out_of_range_check.setChecked(True)
    screen.open_connection_check.setChecked(False)

    screen._on_assess()

    assert ontvangen["meetwaarde_buiten_bereik"] is True
    assert ontvangen["vermoedelijke_open_verbinding_of_kortsluiting"] is False


def test_open_short_wordt_afzonderlijk_doorgestuurd(monkeypatch):
    _app()
    instellingen = _instellingen(bevestig_wissen=False)
    monkeypatch.setattr(esr_screen_module, "laad_instellingen", lambda: instellingen)
    monkeypatch.setattr(esr_screen_module, "zoek_referentie", lambda *args, **kwargs: None)

    ontvangen = {}

    class FakeResultaat:
        pass

    def fake_beoordeel_meting(**kwargs):
        ontvangen.update(kwargs)
        return FakeResultaat()

    monkeypatch.setattr(esr_screen_module, "beoordeel_meting", fake_beoordeel_meting)
    monkeypatch.setattr(EsrTestScreen, "_show_result", lambda self, resultaat: None)

    screen = EsrTestScreen()
    _vul_geldige_meting_in(screen)
    screen.out_of_range_check.setChecked(False)
    screen.open_connection_check.setChecked(True)

    screen._on_assess()

    assert ontvangen["meetwaarde_buiten_bereik"] is False
    assert ontvangen["vermoedelijke_open_verbinding_of_kortsluiting"] is True


# ---------------------------------------------------------------- 4B: meetstatus

def test_meetstatus_voor_opslag_normal_zonder_checkboxes():
    """4B: geen checkboxen aan -> Meetstatus.NORMAL."""
    _app()
    screen = EsrTestScreen()

    assert screen._meetstatus_voor_opslag() == Meetstatus.NORMAL


def test_meetstatus_voor_opslag_ol_met_out_of_range_checkbox():
    """4B: alleen out_of_range_check aan -> Meetstatus.OL."""
    _app()
    screen = EsrTestScreen()
    screen.out_of_range_check.setChecked(True)

    assert screen._meetstatus_voor_opslag() == Meetstatus.OL


def test_meetstatus_voor_opslag_unknown_met_open_connection_checkbox():
    """4B: alleen open_connection_check aan -> Meetstatus.UNKNOWN."""
    _app()
    screen = EsrTestScreen()
    screen.open_connection_check.setChecked(True)

    assert screen._meetstatus_voor_opslag() == Meetstatus.UNKNOWN


def test_meetstatus_voor_opslag_ol_wint_van_open_connection():
    """4B: beide checkboxen aan -> Meetstatus.OL (out_of_range wint)."""
    _app()
    screen = EsrTestScreen()
    screen.out_of_range_check.setChecked(True)
    screen.open_connection_check.setChecked(True)

    assert screen._meetstatus_voor_opslag() == Meetstatus.OL


# ---------------------------------------------------------------- 4C: type-match

def test_low_esr_krijgt_referentie_via_gui(monkeypatch):
    """4C: de familie-check in _on_assess zorgt dat 'Aluminium
    elektrolytisch — Low ESR' een referentie krijgt. Vóór 4C gaf de
    exacte string-match geen referentie, een regressie van 4A."""
    _app()
    instellingen = _instellingen(bevestig_wissen=False)
    monkeypatch.setattr(esr_screen_module, "laad_instellingen", lambda: instellingen)

    # Vervang zoek_referentie door een stub die de aanroep registreert
    # en een dummy ReferentieContext teruggeeft.
    from app.services.assessment_service import ReferentieContext

    referentie_aanroepen = []

    def fake_zoek_referentie(cap, volt, condensatortype=..., meetfrequentie_hz=None):
        referentie_aanroepen.append((cap, volt, condensatortype, meetfrequentie_hz))
        return ReferentieContext(
            esr_waarde=400,
            eenheid="mΩ",
            bron="test",
            referentieniveau=5,
            frequentie_hz=1000,
            typisch_of_maximaal="maximaal",
            condensatortype="Aluminium elektrolytisch",
        )

    monkeypatch.setattr(esr_screen_module, "zoek_referentie", fake_zoek_referentie)

    ontvangen = {}

    class FakeResultaat:
        taal = "nl_NL"
        waarschuwingen = ()
        eindstatus = type("E", (), {"value": "waarschijnlijk_goed"})()
        capaciteit = type("C", (), {
            "afwijking_percent": 0.0,
            "nominale_waarde": 470,
            "tolerantie_percent": 20,
            "eenheid": "µF",
            "gemeten_waarde": 470,
        })()
        esr = type("E2", (), {
            "factor": 1.0,
            "frequentie_wijkt_af": False,
            "referentie_esr_ohm": 0.4,
            "gemeten_esr_ohm": 0.4,
            "referentiebron": "test",
            "referentieniveau": 5,
        })()
        consistentie = type("Co", (), {"toelichting": ""})()
        betrouwbaarheid = type("B", (), {"niveau": type("N", (), {"value": "middel"})(), "verlagende_factoren": ()})()
        redenen = ()
        aanbevolen_vervolgstap = ""
        instrument_code = "LCR_ST1"
        testspanning_vrms = 0.6
        referentiefrequentie_hz = 1000

    def fake_beoordeel_meting(**kwargs):
        ontvangen.update(kwargs)
        return FakeResultaat()

    monkeypatch.setattr(esr_screen_module, "beoordeel_meting", fake_beoordeel_meting)
    monkeypatch.setattr(EsrTestScreen, "_show_result", lambda self, resultaat: None)

    screen = EsrTestScreen()
    _vul_geldige_meting_in(screen)
    # Wijzig condensatortype naar Low ESR.
    idx = screen.type_combo.findText("Aluminium elektrolytisch — Low ESR")
    assert idx >= 0
    screen.type_combo.setCurrentIndex(idx)

    screen._on_assess()

    # De GUI moet zoek_referentie hebben aangeroepen met Low ESR.
    assert referentie_aanroepen
    assert referentie_aanroepen[0][2] == "Aluminium elektrolytisch — Low ESR"
    # En de referentie moet aan beoordeel_meting zijn doorgegeven.
    assert ontvangen["referentie"] is not None


def test_tantaal_krijgt_geen_referentie_via_gui(monkeypatch):
    """4C: tantaal is niet-elektrolytisch; de GUI roept zoek_referentie
    niet aan en geeft referentie=None door aan beoordeel_meting."""
    _app()
    instellingen = _instellingen(bevestig_wissen=False)
    monkeypatch.setattr(esr_screen_module, "laad_instellingen", lambda: instellingen)

    referentie_aanroepen = []

    def fake_zoek_referentie(*args, **kwargs):
        referentie_aanroepen.append((args, kwargs))
        return None

    monkeypatch.setattr(esr_screen_module, "zoek_referentie", fake_zoek_referentie)

    ontvangen = {}

    class FakeResultaat:
        taal = "nl_NL"
        waarschuwingen = ()
        eindstatus = type("E", (), {"value": "niet_te_beoordelen"})()
        capaciteit = type("C", (), {
            "afwijking_percent": None,
            "nominale_waarde": 470,
            "tolerantie_percent": 20,
            "eenheid": "µF",
            "gemeten_waarde": 470,
        })()
        esr = type("E2", (), {
            "factor": None,
            "frequentie_wijkt_af": False,
            "referentie_esr_ohm": None,
            "gemeten_esr_ohm": None,
            "referentiebron": None,
            "referentieniveau": None,
        })()
        consistentie = type("Co", (), {"toelichting": ""})()
        betrouwbaarheid = type("B", (), {"niveau": type("N", (), {"value": "laag"})(), "verlagende_factoren": ()})()
        redenen = ()
        aanbevolen_vervolgstap = ""
        instrument_code = "LCR_ST1"
        testspanning_vrms = 0.6
        referentiefrequentie_hz = None

    def fake_beoordeel_meting(**kwargs):
        ontvangen.update(kwargs)
        return FakeResultaat()

    monkeypatch.setattr(esr_screen_module, "beoordeel_meting", fake_beoordeel_meting)
    monkeypatch.setattr(EsrTestScreen, "_show_result", lambda self, resultaat: None)

    screen = EsrTestScreen()
    _vul_geldige_meting_in(screen)
    idx = screen.type_combo.findText("Tantaal elektrolytisch")
    assert idx >= 0
    screen.type_combo.setCurrentIndex(idx)

    screen._on_assess()

    # De GUI mag zoek_referentie NIET hebben aangeroepen voor tantaal.
    assert referentie_aanroepen == []
    # En de referentie moet None zijn.
    assert ontvangen["referentie"] is None