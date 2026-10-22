"""
================================================================================
Module:     app/config/settings.py
Project:    Electronics Diagnostic Tool Hub / ESR Validator (Windows)
Versie:     1.8.0
Datum:      2026-10-21
Auteur:     Bart Bossuyt

Doel:       Centrale, aanpasbare instellingen voor de app.
            Geen beoordelingslogica hier, enkel waarden en persistente defaults.

Wijzigingen:
  v1.0.0 (2026-08-11)  Initiele versie. Configureerbare drempels,
                       vaste keuzelijsten, eenheidsconversiefactoren.
  v1.1.0 (2026-09-26)  Expliciete meetmethoden toegevoegd: EX_SITU,
                       ONE_LEG en IN_CIRCUIT.
  v1.2.0 (2026-09-27)  Settings-datamodel voorbereid voor Algemeen,
                       ESR / Condensator en Rapportage.
  v1.3.0 (2026-10-02)  Algemene bestandsvoorkeuren toegevoegd: standaard
                       exportmap, importmap en optioneel exportmap openen na
                       succesvolle export. Condensatortypes gecentraliseerd.
  v1.4.0 (2026-10-07)  laatste_importmap en laatste_exportmap toegevoegd
                       voor 5D'.3 (Wizard UX). Backward-compatible: oude
                       settings.json blijft geldig, ontbrekende keys worden
                       leeg.
  v1.5.0 (2026-10-11)  Fase 8D: laatste_rapportmap toegevoegd aan
                       AlgemeneInstellingen; auteur toegevoegd aan
                       RapportageInstellingen. Backward-compatible.
  v1.6.0 (2026-10-14)  Fase 9H: controleer_updates_bij_opstarten toegevoegd
                       aan AlgemeneInstellingen (default True).
  v1.7.0 (2026-10-16)  Fase 11E.3: qa_modus toegevoegd aan
                       AlgemeneInstellingen (default False). Wanneer True,
                       toont het Help-menu een extra item om de
                       drie-knoppen update-melding te forceren voor QA.
                       Backward-compatible: oude settings.json blijft
                       geldig, ontbrekende key valt terug op False.
  v1.8.0 (2026-10-21)  Fase 11H.2: thema-validatie.
                       - Nieuwe constanten TOEGESTANE_THEMAS en
                         STANDAARD_THEMA.
                       - Nieuwe pure helper normaliseer_thema(): geeft
                         "light" of "dark" terug; alles anders valt
                         terug op STANDAARD_THEMA.
                       - laad_instellingen() normaliseert het geladen
                         thema, zodat een met de hand bewerkte
                         settings.json met een ongeldige waarde veilig
                         op "dark" valt. Backward-compatible: bestaande
                         bestanden met "dark" of "light" blijven werken.
                       - Geen wijziging aan sla_instellingen_op(): de
                         GUI levert altijd een genormaliseerde waarde.
================================================================================
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
import json
from pathlib import Path
from typing import Any, TypeVar


SETTINGS_PATH = Path("settings.json")


EENHEDEN_CAPACITEIT = ("pF", "nF", "µF", "mF")
EENHEDEN_ESR = ("mΩ", "Ω")
MEETFREQUENTIES_HZ = (100, 1_000, 10_000)
TESTSPANNINGEN_VRMS = (0.3, 0.6)
CONDENSATORTYPES = (
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
)
AC_OF_DC = ("AC", "DC", "onbekend")
POLARITEITEN = ("gepolariseerd", "niet-gepolariseerd", "onbekend")
TYPISCH_OF_MAXIMAAL = ("typisch", "maximaal")
BETROUWBAARHEIDSNIVEAUS = ("hoog", "middel", "laag")
V_LOSS_EENHEDEN = ("V", "mV", "%", "dimensieloos", "onbekend")
STABILITEIT_OPTIES = ("stabiel", "schommelt licht", "schommelt sterk", "onbekend")
MEETMETHODEN = ("EX_SITU", "ONE_LEG", "IN_CIRCUIT")


# Sinds 11H.2: toegestane thema's en de fallback bij ongeldige waarden.
TOEGESTANE_THEMAS = ("dark", "light")
STANDAARD_THEMA = "dark"


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


def normaliseer_thema(waarde: Any) -> str:
    """Geeft een geldig thema terug.

    Retourneert ``waarde`` als die exact gelijk is aan een van
    TOEGESTANE_THEMAS. In alle andere gevallen (None, leeg, onbekend,
    verkeerd type) valt de functie terug op STANDAARD_THEMA. Puur en
    GUI-vrij, zodat de validatie ook los van Qt getest kan worden.
    """
    if isinstance(waarde, str) and waarde in TOEGESTANE_THEMAS:
        return waarde
    return STANDAARD_THEMA


@dataclass(frozen=True)
class BeoordelingsInstellingen:
    """Configureerbare grenswaarden voor de indicatieve beoordeling."""

    esr_factor_normaal: float = 1.0
    esr_factor_aandachtspunt: float = 2.0
    esr_factor_verdacht: float = 3.0
    capaciteit_marge_binnen: float = 0.9
    consistentie_marge: float = 2.0
    consistentie_eenhedenfout_drempel: float = 100.0


@dataclass(frozen=True)
class AlgemeneInstellingen:
    """Algemene voorkeuren; het thema kan sinds 11H.2 donker of licht zijn.

    ``thema`` accepteert "dark" of "light"; ongeldige waarden worden bij
    het laden genormaliseerd naar "dark" (zie normaliseer_thema()).

    ``qa_modus`` (sinds 11E.3) is een verborgen schakelaar voor QA: als
    True toont het Help-menu een extra item om de drie-knoppen
    update-melding te forceren, ook als er geen nieuwe versie is.
    Standaard False. Niet bedoeld voor eindgebruikers.
    """

    thema: str = STANDAARD_THEMA
    tooltips_ingeschakeld: bool = True
    standaard_exportmap: str = ""
    standaard_importmap: str = ""
    laatste_exportmap: str = ""
    laatste_importmap: str = ""
    laatste_rapportmap: str = ""
    exportmap_openen_na_export: bool = False
    controleer_updates_bij_opstarten: bool = True
    qa_modus: bool = False


@dataclass(frozen=True)
class EsrCondensatorInstellingen:
    """Gebruikersdefaults voor de ESR / Condensator-tool."""

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
    """Voorkeuren voor meetrapporten (fase 8)."""

    grafiek_opnemen: bool = False
    technische_details_opnemen: bool = True
    referentiebron_opnemen: bool = True
    datum_tijd_opnemen: bool = True
    werkplaats_bedrijf: str = ""
    auteur: str = ""


@dataclass(frozen=True)
class AppInstellingen:
    """Verzamelt alle instellingen die de app nodig heeft bij opstart."""

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
    Ontbrekende sleutels vallen terug op de dataclass-default.
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

    Oude bestanden zonder de nieuwste velden blijven geldig; die velden
    vallen terug op hun dataclass-default. Sinds 11H.2 wordt het geladen
    thema genormaliseerd: een ongeldige waarde (bv. "blauw") valt terug
    op STANDAARD_THEMA.
    """
    if SETTINGS_PATH.exists():
        try:
            with SETTINGS_PATH.open("r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                return AppInstellingen()

            algemeen = _dataclass_from_dict(
                AlgemeneInstellingen, data.get("algemeen", {})
            )
            algemeen = AlgemeneInstellingen(
                **{
                    **asdict(algemeen),
                    "thema": normaliseer_thema(algemeen.thema),
                }
            )

            return AppInstellingen(
                taal=data.get("language", "nl_NL"),
                algemeen=algemeen,
                esr_condensator=_dataclass_from_dict(
                    EsrCondensatorInstellingen,
                    data.get("esr_condensator", {}),
                ),
                rapportage=_dataclass_from_dict(
                    RapportageInstellingen,
                    data.get("rapportage", {}),
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