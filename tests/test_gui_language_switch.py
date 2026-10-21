"""
================================================================================
Module:     tests/test_gui_language_switch.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.3.1
Datum:      2026-10-20
Auteur:     Bart Bossuyt

Doel:       Regressietests voor live taalwissel in Hoofdmenu/Diagnose, ESR en
            Historiek. Bewijst dat zichtbare statische GUI-teksten vernieuwen
            zonder meetinvoer of actieve filterwaarden te wissen.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste regressietests voor de taalwissel-UX-fix.
  v1.1.0 (2026-10-02)  Documentatiepagina opgenomen in live taalwisseltests.
  v1.1.1 (2026-10-03)  analysis test toegevoegd
  v1.2.0 (2026-10-16)  Fase 11D: test dat na een beoordeling in NL een
                        live taalwissel naar EN de taal-mismatch-banner
                        toont en de reeds vertaalde resultaatstrings niet
                        stil vermengt met de nieuwe GUI-taal. De test
                        gebruikt een echt Beoordeling-object via
                        beoordeel_meting, niet een stub. De stub van
                        laad_instellingen levert nu ook een
                        `beoordeling`-namespace, nodig voor de ESR-zones
                        in _build_result_html. Zichtbaarheid van de banner
                        wordt getoetst met isHidden() i.p.v. isVisible(),
                        omdat het scherm in de offscreen-test nooit
                        getoond wordt.
  v1.3.0 (2026-10-20)  Fase 11F.4 (§4.23): _fake_translate doet nu
                        echte format-vervanging (zoals vertaal() in
                        productie) in plaats van kwargs achter de
                        sleutel te plakken. De tests blijven
                        ongewijzigd; de asserties gebruiken nog steeds
                        de kwargs-controle via de placeholders in de
                        verwachte strings.
  v1.3.1 (2026-10-20)  Fix: _fake_translate deed in v1.3.0 alleen
                        echte format-vervanging als de sleutel-string
                        zelf {placeholders} bevatte. Voor sleutels
                        zoals resultaat.taal_mismatch_banner (waar de
                        placeholders in het i18n-bestand staan, niet
                        in de sleutel-string) gingen de kwargs
                        verloren, waardoor de banner-assertie faalde.
                        Nu: als de sleutel geen {placeholders} bevat,
                        worden de kwargs alsnog als [k=v,...] achter
                        de sleutel geplakt (oud gedrag). Voor sleutels
                        met {placeholders} in de sleutel-string wordt
                        echte format-vervanging gebruikt.
================================================================================
"""

from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

import app.gui.documentation_screen as documentation_module
import app.gui.esr_test_screen as esr_module
import app.gui.history_screen as history_module
import app.gui.main_window as main_window_module
from app.gui.esr_test_screen import EsrTestScreen
from app.gui.history_screen import HistoryScreen
from app.gui.main_window import ToolHubWindow
from app.services.assessment_service import (
    Meetmethode,
    ReferentieContext,
    beoordeel_meting,
)


@pytest.fixture(scope="module", autouse=True)
def qapplication():
    app = QApplication.instance() or QApplication([])
    yield app


def _fake_translate(key: str, taal: str = "nl_NL", **kwargs) -> str:
    """Teststub voor vertaal(): echte format-vervanging waar mogelijk.

    - Als de sleutel zelf {placeholders} bevat: vervang die met kwargs
      (echte format-vervanging, conform productie).
    - Als de sleutel geen {placeholders} bevat: plak de kwargs als
      [k=v,...] achter de sleutel, zoals de oude stub deed. Dit is
      nodig voor tests die controleren dát de kwargs zijn doorgegeven
      aan vertaal(), ook al staan de placeholders in het i18n-bestand
      en niet in de sleutel-string (bv. resultaat.taal_mismatch_banner).
    """
    result = f"{taal}:{key}"
    if not kwargs:
        return result
    if "{" in result:
        try:
            return result.format(**kwargs)
        except (KeyError, IndexError):
            return result
    kv = ",".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
    return f"{result}[{kv}]"


def _fake_esr_settings():
    instrument_code = next(iter(esr_module.INSTRUMENT_PROFIELEN))
    profile = esr_module.get_instrument_profiel(instrument_code)
    frequency = profile.standaard_frequentie_hz or profile.frequenties_hz[0]
    test_voltage = (
        profile.standaard_testspanning_vrms
        if profile.standaard_testspanning_vrms is not None
        else profile.testspanningen_vrms[0]
    )
    return SimpleNamespace(
        esr_condensator=SimpleNamespace(
            capaciteitseenheid="µF",
            tolerantie_percent=20.0,
            werkspanning_v=None,
            condensatortype=esr_module.CONDENSATORTYPES[0],
            fabrikant="",
            meetmethode="EX_SITU",
            instrument_code=instrument_code,
            meetfrequentie_hz=frequency,
            testspanning_vrms=test_voltage,
            temperatuur_c=20.0,
            esr_eenheid="mΩ",
            bevestig_wissen=False,
        ),
        beoordeling=SimpleNamespace(
            capaciteit_marge_binnen=0.9,
            esr_factor_normaal=1.0,
            esr_factor_aandachtspunt=2.0,
            esr_factor_verdacht=3.0,
            consistentie_marge=2.0,
            consistentie_eenhedenfout_drempel=100.0,
        ),
    )


class _EmptyHistoryService:
    def list_measurements(self, filters=None, *, limit=100, offset=0):
        return []

    def get_measurement_detail(self, measurement_id):
        return None


def _maak_echt_resultaat(taal: str):
    """Produceer een echt Beoordeling-object in de gevraagde taal."""
    referentie = ReferentieContext(
        esr_waarde=100,
        eenheid="mΩ",
        bron="Test",
        referentieniveau=1,
        frequentie_hz=1000,
        typisch_of_maximaal="maximaal",
        condensatortype="Aluminium elektrolytisch",
    )
    return beoordeel_meting(
        nominale_capaciteit=100,
        eenheid_nominaal="µF",
        tolerantie_percent=20,
        gemeten_capaciteit=100,
        eenheid_gemeten_capaciteit="µF",
        gemeten_esr=80,
        eenheid_gemeten_esr="mΩ",
        meetfrequentie_hz=1000,
        D=None,
        condensatortype="Aluminium elektrolytisch",
        meetmethode=Meetmethode.EX_SITU,
        omgevingstemperatuur_c=20,
        veiligheid_bevestigd=True,
        referentie=referentie,
        fabrikant_bekend=True,
        serie_bekend=True,
        taal=taal,
    )


def test_esr_language_switch_preserves_user_input(monkeypatch):
    monkeypatch.setattr(esr_module, "vertaal", _fake_translate)
    monkeypatch.setattr(esr_module, "laad_instellingen", _fake_esr_settings)

    screen = EsrTestScreen(taal="nl_NL")
    screen.nom_cap_input.setText("470")
    screen.meas_cap_input.setText("465")
    screen.meas_esr_input.setText("200")
    screen.safety_check.setChecked(True)
    screen.out_of_range_check.setChecked(True)
    screen.method_combo.setCurrentIndex(1)
    selected_method = screen.method_combo.currentData()

    screen.apply_language("en_US")

    assert screen.title_label.text() == "en_US:scherm.esr_test"
    assert screen.component_group.title() == "en_US:scherm.condensator"
    assert screen.context_group.title() == "en_US:scherm.meetcontext"
    assert screen.measurement_group.title() == "en_US:scherm.meetwaarden"
    assert screen.back_btn.text() == "en_US:knop.terug"
    assert screen.assess_btn.text() == "en_US:knop.beoordeel"
    assert screen.method_combo.currentData() == selected_method
    assert screen.nom_cap_input.text() == "470"
    assert screen.meas_cap_input.text() == "465"
    assert screen.meas_esr_input.text() == "200"
    assert screen.safety_check.isChecked() is True
    assert screen.out_of_range_check.isChecked() is True


def test_history_language_switch_updates_filter_labels_and_keeps_values(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)

    screen = HistoryScreen(
        taal="nl_NL",
        history_service=_EmptyHistoryService(),
    )
    screen.filter_manufacturer.setText("Panasonic")
    screen.filter_series.setText("FM")
    screen.filter_method.setCurrentIndex(2)
    selected_method = screen.filter_method.currentData()

    screen.apply_language("en_US")

    assert screen.filter_tool_label.text() == "en_US:historiek.filter.tool"
    assert screen.filter_manufacturer_label.text() == "en_US:historiek.filter.fabrikant"
    assert screen.filter_series_label.text() == "en_US:historiek.filter.serie"
    assert screen.filter_method_label.text() == "en_US:historiek.filter.meetmethode"
    assert screen.filter_instrument_label.text() == "en_US:historiek.filter.instrument"
    assert screen.filter_frequency_label.text() == "en_US:historiek.filter.frequentie"
    assert screen.filter_status_label.text() == "en_US:historiek.filter.status"
    assert screen.filter_reliability_label.text() == "en_US:historiek.filter.betrouwbaarheid"
    assert screen.filter_manufacturer.text() == "Panasonic"
    assert screen.filter_series.text() == "FM"
    assert screen.filter_method.currentData() == selected_method


def test_main_window_language_switch_updates_current_page_title(monkeypatch):
    monkeypatch.setattr(main_window_module, "vertaal", _fake_translate)
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    monkeypatch.setattr(documentation_module, "vertaal", _fake_translate)
    monkeypatch.setattr(esr_module, "vertaal", _fake_translate)
    monkeypatch.setattr(esr_module, "laad_instellingen", _fake_esr_settings)
    monkeypatch.setattr(
        main_window_module,
        "laad_instellingen",
        lambda: SimpleNamespace(taal="nl_NL"),
    )

    window = ToolHubWindow()
    window.stack.setCurrentWidget(window.diagnose_page)
    window.taal = "en_US"

    window._apply_language()

    assert window.hub_title_label.text() == "en_US:app.titel"
    assert window.hub_subtitle_label.text() == "en_US:scherm.hoofdmenu"
    assert window.diagnose_back_btn.text() == "en_US:knop.terug"
    assert window.diagnose_title_label.text() == "en_US:scherm.diagnose"
    assert window.esr_page.title_label.text() == "en_US:scherm.esr_test"
    assert window.documentation_page.title_label.text() == "en_US:documentatie.titel"
    assert window.windowTitle() == "en_US:app.titel — en_US:scherm.diagnose"

def test_language_switch_updates_analysis_page_title() -> None:
    """Fase 7B: taalwissel vertaalt de Analyse-pagina."""
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])

    from app.gui.main_window import ToolHubWindow

    window = ToolHubWindow(taal="nl_NL")
    try:
        window._set_language("en_US")
        assert window.analysis_page.taal == "en_US"
        assert window.analysis_page.title_label.text() != ""
    finally:
        window.deleteLater()


# ---------------------------------------------------------------------------
# Fase 11D — i18n-menging oplossen
# ---------------------------------------------------------------------------

def test_language_switch_na_beoordeling_toont_banner_en_behoudt_oude_strings(monkeypatch):
    """Fase 11D: na een beoordeling in NL toont een live taalwissel naar EN
    een nette banner. De reeds vertaalde resultaatstrings blijven in het NL
    (de taal van het Beoordeling-object) en worden niet vermengd met EN
    GUI-teksten."""
    monkeypatch.setattr(esr_module, "vertaal", _fake_translate)
    monkeypatch.setattr(esr_module, "laad_instellingen", _fake_esr_settings)

    screen = EsrTestScreen(taal="nl_NL")

    resultaat_nl = _maak_echt_resultaat("nl_NL")
    screen._laatste_resultaat = resultaat_nl
    screen._show_result(resultaat_nl)

    assert screen.result_language_banner.isHidden() is True
    assert resultaat_nl.taal == "nl_NL"

    screen.apply_language("en_US")

    assert screen.title_label.text() == "en_US:scherm.esr_test"
    assert screen.assess_btn.text() == "en_US:knop.beoordeel"

    assert screen.result_language_banner.isHidden() is False
    banner_tekst = screen.result_language_banner.text()
    assert "nl_NL" in banner_tekst
    assert "en_US" in banner_tekst
    assert banner_tekst.startswith("en_US:resultaat.taal_mismatch_banner")

    assert screen._laatste_resultaat.taal == "nl_NL"
    assert screen.result_summary.text().startswith("nl_NL:")


def test_banner_verbergt_na_nieuwe_beoordeling_in_nieuwe_taal(monkeypatch):
    """Fase 11D: als de gebruiker opnieuw beoordeelt in de nieuwe taal,
    verdwijnt de banner."""
    monkeypatch.setattr(esr_module, "vertaal", _fake_translate)
    monkeypatch.setattr(esr_module, "laad_instellingen", _fake_esr_settings)

    screen = EsrTestScreen(taal="nl_NL")

    resultaat_nl = _maak_echt_resultaat("nl_NL")
    screen._laatste_resultaat = resultaat_nl
    screen._show_result(resultaat_nl)

    screen.apply_language("en_US")
    assert screen.result_language_banner.isHidden() is False

    resultaat_en = _maak_echt_resultaat("en_US")
    screen._laatste_resultaat = resultaat_en
    screen._show_result(resultaat_en)

    assert screen.result_language_banner.isHidden() is True
    assert screen._laatste_resultaat.taal == "en_US"


def test_banner_verdwijnt_na_wissen(monkeypatch):
    """Fase 11D: bij Wissen verdwijnt de taal-mismatch-banner."""
    monkeypatch.setattr(esr_module, "vertaal", _fake_translate)
    monkeypatch.setattr(esr_module, "laad_instellingen", _fake_esr_settings)

    screen = EsrTestScreen(taal="nl_NL")
    resultaat_nl = _maak_echt_resultaat("nl_NL")
    screen._laatste_resultaat = resultaat_nl
    screen._show_result(resultaat_nl)

    screen.apply_language("en_US")
    assert screen.result_language_banner.isHidden() is False

    screen._on_clear()
    assert screen.result_language_banner.isHidden() is True