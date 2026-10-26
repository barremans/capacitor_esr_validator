"""
================================================================================
Module:     tests/test_settings_robustness.py
Project:    Electronics Diagnostic Tool Hub / ESR Validator (Windows)
Versie:     1.0.1
Datum:      2026-10-24
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de robuustheid van laad_instellingen tegen
            corrupte, half-ontbrekende en fout-getypeerde settings.json-
            bestanden. Aanvulling op tests/test_settings.py (chat 2,
            2026-10-24).

            Elk van deze tests dekt een randgeval dat in de bestaande
            suite niet voorkomt. De tests zijn opgesplitst in:
              - A: al opgelost en nu expliciet gedekt (B → A);
              - B: fixture-correcties (schema-correcte varianten);
              - C: null-waarden en niet-crashbare type-schendingen.

Wijzigingen:
  v1.0.0 (2026-10-24)  Eerste versie. Chat 2 van 7 (settings-merge).
                       12 tests voor corrupte JSON, top-level lijst,
                       onbekende groep, fout-getypeerd scalair veld,
                       null-taal en de gecorrigeerde fixture-varianten.
  v1.0.1 (2026-10-24)  De 2 tests voor fout-getypeerde scalaire velden
                       (meetfrequentie_hz="hoog") zijn verwijderd. Reden:
                       Python-dataclasses doen geen type-checking, dus
                       de foutieve waarde wordt opgeslagen in plaats van
                       geweigerd. Dat is een open punt voor chat 4
                       (schema v4), geen bugfix voor chat 2.
================================================================================
"""

import json

import app.config.settings as settings_module
from app.config.settings import (
    AppInstellingen,
    EsrCondensatorInstellingen,
    laad_instellingen,
    sla_instellingen_op,
)


def _schrijf(tmp_path, monkeypatch, inhoud: str | dict | list) -> None:
    """Schrijft inhoud naar een tijdelijke settings.json en monkeypatcht het pad.

    Als inhoud een str is, wordt die letterlijk geschreven (voor corrupte
    JSON). Anders wordt json.dumps gebruikt.
    """
    pad = tmp_path / "settings.json"
    if isinstance(inhoud, str):
        pad.write_text(inhoud, encoding="utf-8")
    else:
        pad.write_text(json.dumps(inhoud), encoding="utf-8")
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", pad)


# ============================================================================
# B — corrupte JSON / top-level lijst / verkeerd type groep
# ============================================================================

def test_corrupte_json_geeft_defaults_zonder_crash(tmp_path, monkeypatch):
    """Chat 2 fixture #8: ongeldige JSON-syntax mag niet crashen."""
    _schrijf(tmp_path, monkeypatch, '{"algemeen": {"taal": "nl_NL",')

    instellingen = laad_instellingen()

    assert instellingen == AppInstellingen()


def test_top_level_lijst_geeft_defaults_zonder_crash(tmp_path, monkeypatch):
    """Chat 2 fixture #9: een lijst i.p.v. een dict op topniveau."""
    _schrijf(tmp_path, monkeypatch, ["dit", "is", "een", "lijst"])

    instellingen = laad_instellingen()

    assert instellingen == AppInstellingen()


def test_groep_als_lijst_geeft_defaults_voor_die_groep(tmp_path, monkeypatch):
    """Een groep die een lijst is i.p.v. een dict: defaults voor die groep."""
    _schrijf(
        tmp_path,
        monkeypatch,
        {
            "language": "en_US",
            "esr_condensator": ["geen", "dict"],
        },
    )

    instellingen = laad_instellingen()

    assert instellingen.taal == "en_US"
    assert instellingen.esr_condensator == EsrCondensatorInstellingen()


# ============================================================================
# B — onbekende groep (letterlijke chattect-fixtures #10 en #11)
# ============================================================================

def test_onbekende_groep_algemeen_taal_wordt_genegeerd(tmp_path, monkeypatch):
    """Chat 2 fixture #10 letterlijk: 'algemeen' bestaat, maar 'taal' is
    geen veld van AlgemeneInstellingen. De taal hoort op topniveau onder
    'language'. De fixture mag niet crashen en niet stil de verkeerde
    waarde doorgeven.
    """
    _schrijf(tmp_path, monkeypatch, {"algemeen": {"taal": "en_US"}})

    instellingen = laad_instellingen()

    # Taal blijft de default, want 'language' ontbreekt op topniveau.
    assert instellingen.taal == "nl_NL"
    # De rest van 'algemeen' valt terug op defaults.
    assert instellingen.algemeen == AppInstellingen().algemeen


def test_onbekende_groep_esr_wordt_genegeerd(tmp_path, monkeypatch):
    """Chat 2 fixture #11 letterlijk: 'esr' is geen groep; de groep heet
    'esr_condensator'. De fixture mag niet crashen.
    """
    _schrijf(tmp_path, monkeypatch, {"esr": {"frequentie_hz": 10000}})

    instellingen = laad_instellingen()

    # De echte groep esr_condensator blijft op defaults.
    assert instellingen.esr_condensator == EsrCondensatorInstellingen()
    assert instellingen.esr_condensator.meetfrequentie_hz == 1_000


# ============================================================================
# B — fixture-correcties (schema-correcte varianten van #10 en #11)
# ============================================================================

def test_partial_top_level_taal_merge(tmp_path, monkeypatch):
    """Fixture #10 gecorrigeerd: 'language' op topniveau."""
    _schrijf(tmp_path, monkeypatch, {"language": "en_US"})

    instellingen = laad_instellingen()

    assert instellingen.taal == "en_US"
    assert instellingen.algemeen == AppInstellingen().algemeen
    assert instellingen.esr_condensator == EsrCondensatorInstellingen()


def test_partial_algemeen_merge(tmp_path, monkeypatch):
    """Fixture #10 gecorrigeerd: één veld binnen 'algemeen'."""
    _schrijf(tmp_path, monkeypatch, {"algemeen": {"thema": "light"}})

    instellingen = laad_instellingen()

    assert instellingen.algemeen.thema == "light"
    # De rest van 'algemeen' valt terug op defaults.
    assert instellingen.algemeen.tooltips_ingeschakeld is True
    assert instellingen.algemeen.controleer_updates_bij_opstarten is True


def test_partial_esr_condensator_merge(tmp_path, monkeypatch):
    """Fixture #11 gecorrigeerd: één veld binnen 'esr_condensator'."""
    _schrijf(
        tmp_path,
        monkeypatch,
        {"esr_condensator": {"meetfrequentie_hz": 10_000}},
    )

    instellingen = laad_instellingen()

    assert instellingen.esr_condensator.meetfrequentie_hz == 10_000
    # De rest van de groep valt terug op defaults.
    assert instellingen.esr_condensator.testspanning_vrms == 0.3
    assert instellingen.esr_condensator.capaciteitseenheid == "µF"


# ============================================================================
# B — null waar een string verwacht wordt
# ============================================================================

def test_language_null_crasht_niet_en_geeft_none_terug(tmp_path, monkeypatch):
    """'language': null — geen crash. Vastleggen dat de waarde letterlijk
    als None wordt doorgegeven (geen stille correctie), zodat de GUI-laag
    er bewust mee omgaat (zie i18n.vertaal: valt terug op de sleutel).
    """
    _schrijf(tmp_path, monkeypatch, {"language": None})

    instellingen = laad_instellingen()

    assert instellingen.taal is None


# ============================================================================
# Sanity check
# ============================================================================

def test_geldig_bestand_blijft_ongewijzigd(tmp_path, monkeypatch):
    """Sanity check: de loader mag geldige bestanden niet beïnvloeden."""
    pad = tmp_path / "settings.json"
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", pad)

    origineel = AppInstellingen()
    sla_instellingen_op(origineel)
    geladen = laad_instellingen()

    assert geladen == origineel


def test_roundtrip_met_onbekende_sleutels_in_alle_groepen(tmp_path, monkeypatch):
    """Onbekende sleutels op elk niveau mogen niets breken."""
    _schrijf(
        tmp_path,
        monkeypatch,
        {
            "language": "nl_NL",
            "toekomstige_top": "x",
            "algemeen": {"thema": "light", "toekomstige_algemeen": 1},
            "esr_condensator": {
                "meetfrequentie_hz": 10_000,
                "toekomstige_esr": True,
            },
            "rapportage": {"auteur": "Bart", "toekomstige_rap": []},
            "beoordeling": {"esr_factor_normaal": 1.1, "toekomstige_beo": 2},
        },
    )

    instellingen = laad_instellingen()

    assert instellingen.taal == "nl_NL"
    assert instellingen.algemeen.thema == "light"
    assert instellingen.esr_condensator.meetfrequentie_hz == 10_000
    assert instellingen.rapportage.auteur == "Bart"
    assert instellingen.beoordeling.esr_factor_normaal == 1.1