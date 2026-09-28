"""
================================================================================
Module:     tests/test_settings.py
Project:    Electronics Diagnostic Tool Hub / ESR Validator (Windows)
Versie:     1.0.0
Datum:      2026-09-27
Auteur:     Ontwikkelaar

Doel:       Regressietests voor laden, opslaan en achterwaartse compatibiliteit
            van de centrale Settings-datalaag.
================================================================================
"""

import json
from dataclasses import replace

import app.config.settings as settings_module
from app.config.settings import (
    AppInstellingen,
    EsrCondensatorInstellingen,
    laad_instellingen,
    sla_instellingen_op,
)


def test_nieuwe_defaults_zijn_veilig_en_bestaand_gedrag_blijft_behouden():
    instellingen = AppInstellingen()

    assert instellingen.taal == "nl_NL"
    assert instellingen.algemeen.thema == "dark"
    assert instellingen.esr_condensator.capaciteitseenheid == "µF"
    assert instellingen.esr_condensator.tolerantie_percent == 20.0
    assert instellingen.esr_condensator.werkspanning_v is None
    assert instellingen.esr_condensator.meetmethode == "EX_SITU"
    assert instellingen.esr_condensator.instrument_code == "LCR_ST1"
    assert instellingen.esr_condensator.meetfrequentie_hz == 1000
    assert instellingen.esr_condensator.testspanning_vrms == 0.3
    assert instellingen.esr_condensator.temperatuur_c == 20.0
    assert instellingen.esr_condensator.esr_eenheid == "mΩ"
    assert instellingen.esr_condensator.bevestig_wissen is True


def test_oude_settings_json_blijft_laadbaar(tmp_path, monkeypatch):
    pad = tmp_path / "settings.json"
    pad.write_text(
        json.dumps(
            {
                "language": "en_US",
                "beoordeling": {
                    "esr_factor_normaal": 1.1,
                    "esr_factor_aandachtspunt": 2.2,
                    "esr_factor_verdacht": 3.3,
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", pad)

    instellingen = laad_instellingen()

    assert instellingen.taal == "en_US"
    assert instellingen.beoordeling.esr_factor_normaal == 1.1
    assert instellingen.beoordeling.esr_factor_aandachtspunt == 2.2
    assert instellingen.beoordeling.esr_factor_verdacht == 3.3
    assert instellingen.esr_condensator == EsrCondensatorInstellingen()


def test_opslaan_en_opnieuw_laden_bewaart_alle_settingsgroepen(tmp_path, monkeypatch):
    pad = tmp_path / "settings.json"
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", pad)

    basis = AppInstellingen()
    aangepast = replace(
        basis,
        taal="en_US",
        esr_condensator=replace(
            basis.esr_condensator,
            meetfrequentie_hz=10_000,
            testspanning_vrms=0.6,
            bevestig_wissen=False,
        ),
        rapportage=replace(
            basis.rapportage,
            grafiek_opnemen=True,
            werkplaats_bedrijf="Werkplaats",
        ),
    )

    sla_instellingen_op(aangepast)
    geladen = laad_instellingen()

    assert geladen == aangepast


def test_onbekende_sleutels_maken_settings_niet_onbruikbaar(tmp_path, monkeypatch):
    pad = tmp_path / "settings.json"
    pad.write_text(
        json.dumps(
            {
                "language": "nl_NL",
                "esr_condensator": {
                    "meetfrequentie_hz": 10_000,
                    "toekomstige_optie": "mag genegeerd worden",
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", pad)

    instellingen = laad_instellingen()

    assert instellingen.esr_condensator.meetfrequentie_hz == 10_000
    assert instellingen.esr_condensator.testspanning_vrms == 0.3
