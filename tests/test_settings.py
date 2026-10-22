"""
================================================================================
Module:     tests/test_settings.py
Project:    Electronics Diagnostic Tool Hub / ESR Validator (Windows)
Versie:     1.5.0
Datum:      2026-10-21
Auteur:     Bart Bossuyt

Doel:       Regressietests voor laden, opslaan en achterwaartse compatibiliteit
            van de centrale Settings-datalaag.

Wijzigingen:
  v1.0.0 (2026-09-27)  Eerste versie.
  v1.1.0 (2026-10-02)  Export/importmappen en open-na-export voorkeur getest.
  v1.2.0 (2026-10-07)  Tests voor laatste_importmap en laatste_exportmap
                        (fase 5D'.3).
  v1.3.0 (2026-10-11)  Fase 8D: tests voor laatste_rapportmap (Algemeen) en
                        auteur (Rapportage). Backward-compat: oude settings.json
                        zonder deze velden blijft geldig.
  v1.4.0 (2026-10-14)  Fase 9H: tests voor controleer_updates_bij_opstarten
                        (default True). Backward-compat: oude settings.json
                        zonder deze key blijft geldig en valt terug op True.
  v1.5.0 (2026-10-21)  Fase 11H.2: thema-validatie.
                        - Tests voor normaliseer_thema (geldig, ongeldig,
                          leeg, None, verkeerd type).
                        - laad_instellingen met ongeldige thema-waarde in
                          JSON valt terug op "dark".
                        - laad_instellingen met "thema": "light" laadt
                          correct.
                        - Roundtrip thema="light".
================================================================================
"""

import json
from dataclasses import replace

import app.config.settings as settings_module
from app.config.settings import (
    AppInstellingen,
    EsrCondensatorInstellingen,
    RapportageInstellingen,
    STANDAARD_THEMA,
    TOEGESTANE_THEMAS,
    laad_instellingen,
    normaliseer_thema,
    sla_instellingen_op,
)


def test_nieuwe_defaults_zijn_veilig_en_bestaand_gedrag_blijft_behouden():
    instellingen = AppInstellingen()

    assert instellingen.taal == "nl_NL"
    assert instellingen.algemeen.thema == "dark"
    assert instellingen.algemeen.standaard_exportmap == ""
    assert instellingen.algemeen.standaard_importmap == ""
    assert instellingen.algemeen.laatste_exportmap == ""
    assert instellingen.algemeen.laatste_importmap == ""
    assert instellingen.algemeen.laatste_rapportmap == ""
    assert instellingen.algemeen.exportmap_openen_na_export is False
    assert instellingen.algemeen.controleer_updates_bij_opstarten is True
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
    assert instellingen.rapportage.auteur == ""


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
        algemeen=replace(
            basis.algemeen,
            standaard_exportmap=r"C:\Exports",
            standaard_importmap=r"C:\Imports",
            laatste_exportmap=r"C:\Exports\Laatste",
            laatste_importmap=r"C:\Imports\Laatste",
            laatste_rapportmap=r"C:\Rapporten",
            exportmap_openen_na_export=True,
        ),
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
            auteur="Bart Bossuyt",
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


# ============================================================================
# v1.2.0 — laatste_importmap en laatste_exportmap
# ============================================================================

def test_laatste_mappen_default_leeg():
    instellingen = AppInstellingen()
    assert instellingen.algemeen.laatste_importmap == ""
    assert instellingen.algemeen.laatste_exportmap == ""


def test_oude_settings_json_zonder_laatste_mappen_blijft_geldig(
    tmp_path, monkeypatch
):
    """Bewijs backward-compat: oude settings.json zonder de nieuwe velden."""
    pad = tmp_path / "settings.json"
    pad.write_text(
        json.dumps(
            {
                "language": "nl_NL",
                "algemeen": {
                    "thema": "dark",
                    "tooltips_ingeschakeld": True,
                    "standaard_exportmap": r"C:\Exports",
                    "standaard_importmap": r"C:\Imports",
                    "exportmap_openen_na_export": True,
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", pad)

    instellingen = laad_instellingen()

    # Bestaande velden zijn geladen
    assert instellingen.algemeen.standaard_exportmap == r"C:\Exports"
    assert instellingen.algemeen.standaard_importmap == r"C:\Imports"
    assert instellingen.algemeen.exportmap_openen_na_export is True
    # Nieuwe velden zijn leeg (default)
    assert instellingen.algemeen.laatste_exportmap == ""
    assert instellingen.algemeen.laatste_importmap == ""


def test_laatste_mappen_roundtrip(tmp_path, monkeypatch):
    pad = tmp_path / "settings.json"
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", pad)

    basis = AppInstellingen()
    aangepast = replace(
        basis,
        algemeen=replace(
            basis.algemeen,
            laatste_importmap=r"C:\PDFs",
            laatste_exportmap=r"C:\CSV",
        ),
    )
    sla_instellingen_op(aangepast)
    geladen = laad_instellingen()

    assert geladen.algemeen.laatste_importmap == r"C:\PDFs"
    assert geladen.algemeen.laatste_exportmap == r"C:\CSV"


def test_laatste_mappen_overschrijven_elkaar_niet(tmp_path, monkeypatch):
    """Laatste_importmap en laatste_exportmap zijn onafhankelijk."""
    pad = tmp_path / "settings.json"
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", pad)

    basis = AppInstellingen()
    tussenstap = replace(
        basis,
        algemeen=replace(
            basis.algemeen,
            laatste_importmap=r"C:\PDFs",
            laatste_exportmap=r"C:\CSV",
        ),
    )
    sla_instellingen_op(tussenstap)

    # Alleen laatste_importmap wijzigen
    nieuw = replace(
        tussenstap,
        algemeen=replace(
            tussenstap.algemeen,
            laatste_importmap=r"D:\NieuwePDFs",
        ),
    )
    sla_instellingen_op(nieuw)
    geladen = laad_instellingen()

    assert geladen.algemeen.laatste_importmap == r"D:\NieuwePDFs"
    assert geladen.algemeen.laatste_exportmap == r"C:\CSV"


# ============================================================================
# v1.3.0 — laatste_rapportmap en auteur (fase 8D)
# ============================================================================

def test_laatste_rapportmap_default_leeg():
    instellingen = AppInstellingen()
    assert instellingen.algemeen.laatste_rapportmap == ""


def test_auteur_default_leeg():
    instellingen = AppInstellingen()
    assert instellingen.rapportage.auteur == ""


def test_oude_settings_json_zonder_laatste_rapportmap_blijft_geldig(
    tmp_path, monkeypatch
):
    """Backward-compat: oude settings.json zonder laatste_rapportmap."""
    pad = tmp_path / "settings.json"
    pad.write_text(
        json.dumps(
            {
                "language": "nl_NL",
                "algemeen": {
                    "thema": "dark",
                    "laatste_exportmap": r"C:\CSV",
                    "laatste_importmap": r"C:\PDFs",
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", pad)

    instellingen = laad_instellingen()

    assert instellingen.algemeen.laatste_exportmap == r"C:\CSV"
    assert instellingen.algemeen.laatste_importmap == r"C:\PDFs"
    assert instellingen.algemeen.laatste_rapportmap == ""


def test_oude_settings_json_zonder_auteur_blijft_geldig(tmp_path, monkeypatch):
    """Backward-compat: oude settings.json zonder auteur."""
    pad = tmp_path / "settings.json"
    pad.write_text(
        json.dumps(
            {
                "language": "nl_NL",
                "rapportage": {
                    "werkplaats_bedrijf": "Werkplaats",
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", pad)

    instellingen = laad_instellingen()

    assert instellingen.rapportage.werkplaats_bedrijf == "Werkplaats"
    assert instellingen.rapportage.auteur == ""


def test_laatste_rapportmap_roundtrip(tmp_path, monkeypatch):
    pad = tmp_path / "settings.json"
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", pad)

    basis = AppInstellingen()
    aangepast = replace(
        basis,
        algemeen=replace(
            basis.algemeen,
            laatste_rapportmap=r"C:\Rapporten",
        ),
        rapportage=replace(
            basis.rapportage,
            auteur="Bart Bossuyt",
        ),
    )
    sla_instellingen_op(aangepast)
    geladen = laad_instellingen()

    assert geladen.algemeen.laatste_rapportmap == r"C:\Rapporten"
    assert geladen.rapportage.auteur == "Bart Bossuyt"


def test_laatste_rapportmap_staat_los_van_exportmap(tmp_path, monkeypatch):
    """laatste_rapportmap en laatste_exportmap zijn onafhankelijk."""
    pad = tmp_path / "settings.json"
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", pad)

    basis = AppInstellingen()
    tussenstap = replace(
        basis,
        algemeen=replace(
            basis.algemeen,
            laatste_exportmap=r"C:\CSV",
            laatste_rapportmap=r"C:\Rapporten",
        ),
    )
    sla_instellingen_op(tussenstap)

    nieuw = replace(
        tussenstap,
        algemeen=replace(
            tussenstap.algemeen,
            laatste_rapportmap=r"D:\NieuweRapporten",
        ),
    )
    sla_instellingen_op(nieuw)
    geladen = laad_instellingen()

    assert geladen.algemeen.laatste_rapportmap == r"D:\NieuweRapporten"
    assert geladen.algemeen.laatste_exportmap == r"C:\CSV"


# ============================================================================
# v1.4.0 — controleer_updates_bij_opstarten (fase 9H)
# ============================================================================

def test_controleer_updates_default_aan():
    instellingen = AppInstellingen()
    assert instellingen.algemeen.controleer_updates_bij_opstarten is True


def test_oude_settings_json_zonder_update_key_blijft_geldig(
    tmp_path, monkeypatch
):
    """Backward-compat: oude settings.json zonder de nieuwe key."""
    pad = tmp_path / "settings.json"
    pad.write_text(
        json.dumps(
            {
                "language": "nl_NL",
                "algemeen": {
                    "thema": "dark",
                    "laatste_exportmap": r"C:\CSV",
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", pad)

    instellingen = laad_instellingen()

    assert instellingen.algemeen.laatste_exportmap == r"C:\CSV"
    # Nieuwe key valt terug op de default True
    assert instellingen.algemeen.controleer_updates_bij_opstarten is True


def test_update_key_roundtrip(tmp_path, monkeypatch):
    pad = tmp_path / "settings.json"
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", pad)

    basis = AppInstellingen()
    aangepast = replace(
        basis,
        algemeen=replace(
            basis.algemeen,
            controleer_updates_bij_opstarten=False,
        ),
    )
    sla_instellingen_op(aangepast)
    geladen = laad_instellingen()

    assert geladen.algemeen.controleer_updates_bij_opstarten is False


# ============================================================================
# v1.5.0 — thema-validatie (fase 11H.2)
# ============================================================================

def test_toegestane_themas_bevat_dark_en_light():
    assert TOEGESTANE_THEMAS == ("dark", "light")
    assert STANDAARD_THEMA == "dark"


def test_normaliseer_thema_geldige_waarden():
    assert normaliseer_thema("dark") == "dark"
    assert normaliseer_thema("light") == "light"


def test_normaliseer_thema_ongeldige_waarden_vallen_terug_op_dark():
    assert normaliseer_thema("blauw") == "dark"
    assert normaliseer_thema("") == "dark"
    assert normaliseer_thema(None) == "dark"
    assert normaliseer_thema(123) == "dark"
    assert normaliseer_thema("DARK") == "dark"  # case-sensitive
    assert normaliseer_thema(" light ") == "dark"  # geen trim


def test_laad_instellingen_met_ongeldig_thema_valt_terug_op_dark(
    tmp_path, monkeypatch
):
    """Backward-compat: een met de hand bewerkte settings.json met een
    ongeldige thema-waarde mag de app niet breken."""
    pad = tmp_path / "settings.json"
    pad.write_text(
        json.dumps(
            {
                "language": "nl_NL",
                "algemeen": {
                    "thema": "blauw",
                    "tooltips_ingeschakeld": True,
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", pad)

    instellingen = laad_instellingen()

    assert instellingen.algemeen.thema == "dark"
    assert instellingen.algemeen.tooltips_ingeschakeld is True


def test_laad_instellingen_met_thema_light_laadt_correct(
    tmp_path, monkeypatch
):
    pad = tmp_path / "settings.json"
    pad.write_text(
        json.dumps(
            {
                "language": "nl_NL",
                "algemeen": {
                    "thema": "light",
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", pad)

    instellingen = laad_instellingen()

    assert instellingen.algemeen.thema == "light"


def test_thema_light_roundtrip(tmp_path, monkeypatch):
    pad = tmp_path / "settings.json"
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", pad)

    basis = AppInstellingen()
    aangepast = replace(
        basis,
        algemeen=replace(basis.algemeen, thema="light"),
    )
    sla_instellingen_op(aangepast)
    geladen = laad_instellingen()

    assert geladen.algemeen.thema == "light"