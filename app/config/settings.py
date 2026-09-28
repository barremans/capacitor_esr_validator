"""
================================================================================
Module:     app/config/settings.py
Project:    Electronics Diagnostic Tool Hub / ESR Validator (Windows)
Versie:     1.2.0
Datum:      2026-09-27
Auteur:     Ontwikkelaar

Doel:       Centrale, aanpasbare instellingen voor de app.
            Geen beoordelingslogica hier, enkel waarden en persistente defaults.

Wijzigingen:
  v1.0.0 (2026-08-11)  Initiele versie. Configureerbare drempels,
                       vaste keuzelijsten, eenheidsconversiefactoren.
  v1.1.0 (2026-09-26)  Expliciete meetmethoden toegevoegd: EX_SITU,
                       ONE_LEG en IN_CIRCUIT.
                       Gebaseerd op docs/validation_rules.md §11.
  v1.2.0 (2026-09-27)  Settings-datamodel voorbereid voor Algemeen,
                       ESR / Condensator en Rapportage. Bestaande settings.json
                       blijft achterwaarts compatibel. Beoordelingsdrempels
                       inhoudelijk ongewijzigd.

Referentie: docs/validation_rules.md §11, docs/data_model.md §9 en
            functional_design_multitool_questionnaire.md §14.
================================================================================
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
import json
from pathlib import Path
from typing import Any, TypeVar


SETTINGS_PATH = Path("settings.json")


# ---------------------------------------------------------------------------
# Vaste keuzelijsten (docs/data_model.md §9)
# ---------------------------------------------------------------------------
EENHEDEN_CAPACITEIT = ("pF", "nF", "µF", "mF")
EENHEDEN_ESR = ("mΩ", "Ω")
MEETFREQUENTIES_HZ = (100, 1_000, 10_000)
TESTSPANNINGEN_VRMS = (0.3, 0.6)
CONDENSATORTYPES = ("Aluminium elektrolytisch", "Anders")
AC_OF_DC = ("AC", "DC", "onbekend")
POLARITEITEN = ("gepolariseerd", "niet-gepolariseerd", "onbekend")
TYPISCH_OF_MAXIMAAL = ("typisch", "maximaal")
BETROUWBAARHEIDSNIVEAUS = ("hoog", "middel", "laag")
V_LOSS_EENHEDEN = ("V", "mV", "%", "dimensieloos", "onbekend")
STABILITEIT_OPTIES = ("stabiel", "schommelt licht", "schommelt sterk", "onbekend")
MEETMETHODEN = ("EX_SITU", "ONE_LEG", "IN_CIRCUIT")

# Vermenigvuldigingsfactoren t.o.v. de basiseenheid (F voor capaciteit,
# Ω voor ESR) — gebruikt door app/helpers/units.py, hier gecentraliseerd
# zodat er precies één bron van waarheid is voor eenheidsconversie.
CAPACITEIT_FACTOR_NAAR_FARAD = {
    "pF": 1e-12,
    "nF": 1e-9,
    "µF": 1e-6,
    "mF": 1e-3,
}
ESR_FACTOR_NAAR_OHM = {
    "mΩ": 1e-3,
    "Ω": 1.0,
}


# ---------------------------------------------------------------------------
# Configureerbare beoordelingsdrempels (docs/validation_rules.md §11)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class BeoordelingsInstellingen:
    """Configureerbare grenswaarden voor de indicatieve beoordeling.

    Elke waarde hier komt letterlijk overeen met een parameter uit
    docs/validation_rules.md §11. Waarden gemarkeerd [AANNAME] in dat
    document staan hier met dezelfde default en dezelfde toelichting.
    """

    esr_factor_normaal: float = 1.0
    esr_factor_aandachtspunt: float = 2.0
    esr_factor_verdacht: float = 3.0
    capaciteit_marge_binnen: float = 0.9
    consistentie_marge: float = 2.0
    consistentie_eenhedenfout_drempel: float = 100.0


# ---------------------------------------------------------------------------
# Gebruikersinstellingen per Settings-tab
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class AlgemeneInstellingen:
    """Algemene voorkeuren; donker thema is voorlopig het ondersteunde thema."""

    thema: str = "dark"
    tooltips_ingeschakeld: bool = True


@dataclass(frozen=True)
class EsrCondensatorInstellingen:
    """Gebruikersdefaults voor de ESR / Condensator-tool.

    Serie en partnummer staan hier bewust niet in: daarvoor is volgens het
    functioneel ontwerp geen gebruikersdefault voorzien.

    De standaard testspanning blijft 0.3 Vrms om het bestaande LCR-ST1-profiel
    en het huidige applicatiegedrag niet stilzwijgend te wijzigen.
    """

    capaciteitseenheid: str = "µF"
    tolerantie_percent: float = 20.0
    werkspanning_v: float | None = None
    condensatortype: str = "Aluminium elektrolytisch"
    fabrikant: str = ""
    meetmethode: str = "EX_SITU"
    instrument_code: str = "LCR_ST1"
    meetfrequentie_hz: int = 1_000
    testspanning_vrms: float = 0.3
    temperatuur_c: float = 20.0
    esr_eenheid: str = "mΩ"
    bevestig_wissen: bool = True


@dataclass(frozen=True)
class RapportageInstellingen:
    """Voorkeuren voor latere rapportage; nog geen report-engine."""

    grafiek_opnemen: bool = False
    technische_details_opnemen: bool = True
    referentiebron_opnemen: bool = True
    datum_tijd_opnemen: bool = True
    werkplaats_bedrijf: str = ""


@dataclass(frozen=True)
class AppInstellingen:
    """Verzamelt alle instellingen die de app nodig heeft bij opstart.

    ``taal`` blijft op topniveau voor compatibiliteit met de bestaande GUI.
    Het behoort functioneel tot de tab Algemeen.
    """

    taal: str = "nl_NL"
    algemeen: AlgemeneInstellingen = field(default_factory=AlgemeneInstellingen)
    esr_condensator: EsrCondensatorInstellingen = field(
        default_factory=EsrCondensatorInstellingen
    )
    rapportage: RapportageInstellingen = field(
        default_factory=RapportageInstellingen
    )
    beoordeling: BeoordelingsInstellingen = field(
        default_factory=BeoordelingsInstellingen
    )


T = TypeVar("T")


def _dataclass_from_dict(cls: type[T], data: Any) -> T:
    """Maakt een settings-dataclass uit bekende velden.

    Onbekende sleutels worden genegeerd zodat een settings.json uit een
    nieuwere versie de huidige versie niet volledig onbruikbaar maakt.
    """
    if not isinstance(data, dict):
        return cls()

    bekende_velden = {item.name for item in fields(cls)}
    waarden = {k: v for k, v in data.items() if k in bekende_velden}
    try:
        return cls(**waarden)
    except (TypeError, ValueError):
        return cls()


def laad_instellingen() -> AppInstellingen:
    """Laadt settings.json, of veilige defaults wanneer laden niet lukt.

    Oude bestanden met alleen ``language`` en ``beoordeling`` blijven geldig.
    """
    if SETTINGS_PATH.exists():
        try:
            with SETTINGS_PATH.open("r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                return AppInstellingen()

            return AppInstellingen(
                taal=data.get("language", "nl_NL"),
                algemeen=_dataclass_from_dict(
                    AlgemeneInstellingen, data.get("algemeen", {})
                ),
                esr_condensator=_dataclass_from_dict(
                    EsrCondensatorInstellingen,
                    data.get("esr_condensator", {}),
                ),
                rapportage=_dataclass_from_dict(
                    RapportageInstellingen, data.get("rapportage", {})
                ),
                beoordeling=_dataclass_from_dict(
                    BeoordelingsInstellingen, data.get("beoordeling", {})
                ),
            )
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass

    return AppInstellingen()


def sla_instellingen_op(instellingen: AppInstellingen) -> None:
    """Slaat alle settings-groepen op naar settings.json."""
    data = {
        "language": instellingen.taal,
        "algemeen": asdict(instellingen.algemeen),
        "esr_condensator": asdict(instellingen.esr_condensator),
        "rapportage": asdict(instellingen.rapportage),
        "beoordeling": asdict(instellingen.beoordeling),
    }

    with SETTINGS_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
