"""
================================================================================
Module:     app/config/settings.py
Project:    Electronics Diagnostic Tool Hub / ESR Validator (Windows)
Versie:     1.9.1
Datum:      2026-10-26
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
  v1.8.1 (2026-10-23)  Fase 28B: machine_id toegevoegd aan
                       AlgemeneInstellingen (default ""). Wordt door
                       ExportService.verkrijg_machine_id() eenmalig
                       gegenereerd als UUID4 en daarna hergebruikt.
                       Backward-compatible: oude settings.json blijft
                       geldig, ontbrekende key valt terug op "".
  v1.8.2 (2026-10-23)  Fase 28F: laatste_exchangemap toegevoegd aan
                       AlgemeneInstellingen (default ""). Wordt door
                       de exchange-dialoog gebruikt voor de
                       export-/import-startmap. Backward-compatible.
  v1.9.0 (2026-10-26)  Chat 4 / 4A: type- en keuzelijst-validatie.
                       - Nieuwe constanten in BeoordelingsInstellingen:
                         esr_min_realistisch_ohm (default 1 µΩ) en
                         capaciteit_min_realistisch_f (default 1 pF).
                       - Nieuwe pure helper valideer_en_normaliseer()
                         die per veld type- en keuzelijst-validatie
                         toepast, zelfherstellend naar de dataclass-
                         default.
                       - taal wordt NIET genormaliseerd (dat is OV-S1,
                         gerouteerd naar chat 8).
  v1.9.1 (2026-10-26)  Chat 4 / 4A: bugfix in _normaliseer_veld.
                       De str-branch negeerde de `allowed`-parameter,
                       waardoor een string die wel een geldig type
                       maar geen geldige keuze was (bv.
                       condensatortype="xyz", meetmethode=
                       "HALF_IN_CIRCUIT") niet naar de default
                       terugviel. Nu respecteert de str-branch
                       `allowed` net zoals de int-branch. Twee
                       settings-tests die dit blootlegden zijn groen
                       zonder aanpassing van de tests.
================================================================================
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, replace
import json
from pathlib import Path
from typing import Any, Optional, TypeVar


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
    """Configureerbare grenswaarden voor de indicatieve beoordeling.

    ``esr_min_realistisch_ohm`` en ``capaciteit_min_realistisch_f`` zijn
    sinds 4A SANITY-drempels: een waarde eronder is fysiek onrealistisch
    en wordt niet numeriek beoordeeld. Ze zijn géén goed/fout-grens; de
    gewone beoordelingsdrempels (esr_factor_*, capaciteit_marge_binnen,
    consistentie_*) blijven ongewijzigd.
    """

    esr_factor_normaal: float = 1.0
    esr_factor_aandachtspunt: float = 2.0
    esr_factor_verdacht: float = 3.0
    capaciteit_marge_binnen: float = 0.9
    consistentie_marge: float = 2.0
    consistentie_eenhedenfout_drempel: float = 100.0
    # 4A sanity-drempels. Zie bovenstaande docstring.
    esr_min_realistisch_ohm: float = 1e-6
    capaciteit_min_realistisch_f: float = 1e-12


@dataclass(frozen=True)
class AlgemeneInstellingen:
    """Algemene voorkeuren; het thema kan sinds 11H.2 donker of licht zijn.

    ``thema`` accepteert "dark" of "light"; ongeldige waarden worden bij
    het laden genormaliseerd naar "dark" (zie normaliseer_thema()).

    ``qa_modus`` (sinds 11E.3) is een verborgen schakelaar voor QA: als
    True toont het Help-menu een extra item om de drie-knoppen
    update-melding te forceren, ook als er geen nieuwe versie is.
    Standaard False. Niet bedoeld voor eindgebruikers.

    ``machine_id`` (sinds 28B) is een eenmalig gegenereerde UUID4 die
    het toestel identificeert in export/import tussen toestellen
    (§2.28). Een lege string betekent "nog niet gegenereerd"; de
    ExportService genereert en bewaart er dan één.

    ``laatste_exchangemap`` (sinds 28F) is de laatst gebruikte map voor
    export/import tussen toestellen. Staat los van de documentatie-
    import- en exportmappen.
    """

    thema: str = STANDAARD_THEMA
    tooltips_ingeschakeld: bool = True
    standaard_exportmap: str = ""
    standaard_importmap: str = ""
    laatste_exportmap: str = ""
    laatste_importmap: str = ""
    laatste_rapportmap: str = ""
    laatste_exchangemap: str = ""
    exportmap_openen_na_export: bool = False
    controleer_updates_bij_opstarten: bool = True
    qa_modus: bool = False
    machine_id: str = ""


@dataclass(frozen=True)
class EsrCondensatorInstellingen:
    """Gebruikersdefaults voor de ESR / Condensator-tool."""

    capaciteitseenheid: str = "µF"
    tolerantie_percent: float = 20.0
    werkspanning_v: Optional[float] = None
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

    Opgelet: deze functie doet GEEN type-checking. Dat is bewust: de
    per-veld normalisatie gebeurt in `valideer_en_normaliseer`, die door
    `laad_instellingen` na het samenstellen wordt aangeroepen. Zo blijft
    elke groep ook bruikbaar als één veld corrupt is (in plaats van de
    hele groep te laten vallen).
    """
    if not isinstance(data, dict):
        return cls()

    bekende_velden = {item.name for item in fields(cls)}
    waarden = {k: v for k, v in data.items() if k in bekende_velden}
    try:
        return cls(**waarden)
    except (TypeError, ValueError):
        return cls()


def _normaliseer_veld(
    waarde: Any,
    default: Any,
    allowed: Optional[tuple] = None,
) -> Any:
    """Normaliseert één settings-veld naar zijn default bij afwijking.

    - ``bool``-velden: alleen ``bool`` wordt geaccepteerd.
    - ``int``-velden: alleen ``int`` (niet ``bool``); als ``allowed`` is
      opgegeven, moet de waarde in die tuple zitten.
    - ``float``-velden: ``int`` of ``float`` (niet ``bool``); wordt
      gecast naar ``float``.
    - ``str``-velden: alleen ``str``; als ``allowed`` is opgegeven, moet
      de waarde in die tuple zitten (sinds v1.9.1; voor v1.9.1 werd
      ``allowed`` in de str-branch genegeerd, waardoor bv.
      ``condensatortype="xyz"`` niet naar de default terugviel).
    - ``Optional``-velden: ``None`` plus het binnenste type.

    In alle andere gevallen wordt ``default`` teruggegeven. Puur, GUI-
    vrij, en zelfherstellend (consistent met `normaliseer_thema`).
    """
    if waarde is None:
        return default
    if isinstance(default, bool):
        return waarde if isinstance(waarde, bool) else default
    if isinstance(default, int):
        if isinstance(waarde, bool) or not isinstance(waarde, int):
            return default
        if allowed is not None and waarde not in allowed:
            return default
        return waarde
    if isinstance(default, float):
        if isinstance(waarde, bool) or not isinstance(waarde, (int, float)):
            return default
        return float(waarde)
    if isinstance(default, str):
        if not isinstance(waarde, str):
            return default
        if allowed is not None and waarde not in allowed:
            return default
        return waarde
    return waarde


def valideer_en_normaliseer(instellingen: AppInstellingen) -> AppInstellingen:
    """Past per veld type- en keuzelijst-validatie toe, zelfherstellend.

    Wordt door `laad_instellingen` aangeroepen ná het samenstellen van
    `AppInstellingen`, zodat een handmatig bewerkte `settings.json` met
    een verkeerd type (bv. ``meetfrequentie_hz="hoog"``) of een waarde
    buiten de keuzelijst nooit in de app terechtkomt.

    `taal` wordt NIET genormaliseerd: dat is OV-S1, gerouteerd naar
    chat 8. `thema` wordt al door `normaliseer_thema` afgehandeld.
    """
    algemeen = instellingen.algemeen
    esr = instellingen.esr_condensator
    rapportage = instellingen.rapportage
    beoordeling = instellingen.beoordeling

    algemeen_genormaliseerd = replace(
        algemeen,
        thema=normaliseer_thema(algemeen.thema),
        tooltips_ingeschakeld=_normaliseer_veld(
            algemeen.tooltips_ingeschakeld, True
        ),
        standaard_exportmap=_normaliseer_veld(algemeen.standaard_exportmap, ""),
        standaard_importmap=_normaliseer_veld(algemeen.standaard_importmap, ""),
        laatste_exportmap=_normaliseer_veld(algemeen.laatste_exportmap, ""),
        laatste_importmap=_normaliseer_veld(algemeen.laatste_importmap, ""),
        laatste_rapportmap=_normaliseer_veld(algemeen.laatste_rapportmap, ""),
        laatste_exchangemap=_normaliseer_veld(algemeen.laatste_exchangemap, ""),
        exportmap_openen_na_export=_normaliseer_veld(
            algemeen.exportmap_openen_na_export, False
        ),
        controleer_updates_bij_opstarten=_normaliseer_veld(
            algemeen.controleer_updates_bij_opstarten, True
        ),
        qa_modus=_normaliseer_veld(algemeen.qa_modus, False),
        machine_id=_normaliseer_veld(algemeen.machine_id, ""),
    )

    esr_genormaliseerd = replace(
        esr,
        capaciteitseenheid=_normaliseer_veld(
            esr.capaciteitseenheid, "µF", EENHEDEN_CAPACITEIT
        ),
        tolerantie_percent=_normaliseer_veld(esr.tolerantie_percent, 20.0),
        werkspanning_v=(
            esr.werkspanning_v
            if (
                esr.werkspanning_v is None
                or (
                    not isinstance(esr.werkspanning_v, bool)
                    and isinstance(esr.werkspanning_v, (int, float))
                )
            )
            else None
        ),
        condensatortype=_normaliseer_veld(
            esr.condensatortype, "Aluminium elektrolytisch", CONDENSATORTYPES
        ),
        fabrikant=_normaliseer_veld(esr.fabrikant, ""),
        meetmethode=_normaliseer_veld(esr.meetmethode, "EX_SITU", MEETMETHODEN),
        instrument_code=_normaliseer_veld(esr.instrument_code, "LCR_ST1"),
        meetfrequentie_hz=_normaliseer_veld(
            esr.meetfrequentie_hz, 1_000, MEETFREQUENTIES_HZ
        ),
        testspanning_vrms=_normaliseer_veld(
            esr.testspanning_vrms, 0.3, TESTSPANNINGEN_VRMS
        ),
        temperatuur_c=_normaliseer_veld(esr.temperatuur_c, 20.0),
        esr_eenheid=_normaliseer_veld(esr.esr_eenheid, "mΩ", EENHEDEN_ESR),
        bevestig_wissen=_normaliseer_veld(esr.bevestig_wissen, True),
    )

    rapportage_genormaliseerd = replace(
        rapportage,
        grafiek_opnemen=_normaliseer_veld(rapportage.grafiek_opnemen, False),
        technische_details_opnemen=_normaliseer_veld(
            rapportage.technische_details_opnemen, True
        ),
        referentiebron_opnemen=_normaliseer_veld(
            rapportage.referentiebron_opnemen, True
        ),
        datum_tijd_opnemen=_normaliseer_veld(
            rapportage.datum_tijd_opnemen, True
        ),
        werkplaats_bedrijf=_normaliseer_veld(rapportage.werkplaats_bedrijf, ""),
        auteur=_normaliseer_veld(rapportage.auteur, ""),
    )

    beoordeling_genormaliseerd = replace(
        beoordeling,
        esr_factor_normaal=_normaliseer_veld(beoordeling.esr_factor_normaal, 1.0),
        esr_factor_aandachtspunt=_normaliseer_veld(
            beoordeling.esr_factor_aandachtspunt, 2.0
        ),
        esr_factor_verdacht=_normaliseer_veld(
            beoordeling.esr_factor_verdacht, 3.0
        ),
        capaciteit_marge_binnen=_normaliseer_veld(
            beoordeling.capaciteit_marge_binnen, 0.9
        ),
        consistentie_marge=_normaliseer_veld(beoordeling.consistentie_marge, 2.0),
        consistentie_eenhedenfout_drempel=_normaliseer_veld(
            beoordeling.consistentie_eenhedenfout_drempel, 100.0
        ),
        esr_min_realistisch_ohm=_normaliseer_veld(
            beoordeling.esr_min_realistisch_ohm, 1e-6
        ),
        capaciteit_min_realistisch_f=_normaliseer_veld(
            beoordeling.capaciteit_min_realistisch_f, 1e-12
        ),
    )

    return replace(
        instellingen,
        algemeen=algemeen_genormaliseerd,
        esr_condensator=esr_genormaliseerd,
        rapportage=rapportage_genormaliseerd,
        beoordeling=beoordeling_genormaliseerd,
    )


def laad_instellingen() -> AppInstellingen:
    """Laadt settings.json, of veilige defaults wanneer laden niet lukt.

    Oude bestanden zonder de nieuwste velden blijven geldig; die velden
    vallen terug op hun dataclass-default. Sinds 11H.2 wordt het geladen
    thema genormaliseerd: een ongeldige waarde (bv. "blauw") valt terug
    op STANDAARD_THEMA. Sinds 4A wordt elk veld apart genormaliseerd via
    `valideer_en_normaliseer`: een verkeerd type (bv. "hoog" voor een
    int-veld) of een waarde buiten de keuzelijst valt terug op de
    dataclass-default, zonder de andere velden te raken.
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

            samengesteld = AppInstellingen(
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
            return valideer_en_normaliseer(samengesteld)
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