"""
================================================================================
Module:     app/services/assessment_service.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.3.0
Datum:      2026-09-29
Auteur:     Ontwikkelaar

Doel:       Kernlogica van de indicatieve beoordeling: capaciteitsvalidatie,
            indicatieve ESR-beoordeling, interne C-ESR-D-consistentiecontrole,
            betrouwbaarheidsbepaling en de samengestelde eindstatus. Bevat
            GEEN GUI-code en raakt de database niet rechtstreeks aan.

Wijzigingen:
  v1.0.0 (2026-08-11)  Initiele versie. Volledige beoordelingsketen:
                       C-validatie -> ESR -> consistentie -> betrouwbaarheid
                       -> eindstatus. Alle regels uit validation_rules.md
                       geimplementeerd.
  v1.1.0 (2026-09-26)  Meetmethode als expliciete enum toegevoegd
                       (EX_SITU / ONE_LEG / IN_CIRCUIT), out-of-range/OL
                       toegevoegd en type-mismatch van referenties bewaakt.
  v1.2.0 (2026-09-26)  Instrumentcode en testspanning toegevoegd aan de
                       meetcontext van het resultaat; nog zonder effect op
                       de ESR-grensfactoren.
  v1.3.0 (2026-09-29)  Referentie zonder frequentie veilig afgehandeld:
                       ESR wordt niet numeriek beoordeeld en betrouwbaarheid
                       blijft conservatief laag; geen verborgen conversie.

Referentie: docs/validation_rules.md (volledig), in het bijzonder:
            §2 referentiehiërarchie, §3 capaciteitsvalidatie,
            §4 indicatieve ESR-beoordeling, §5 consistentiecontrole,
            §6 betrouwbaarheid, §7 eindstatus, §10 veiligheidsteksten.

Multilanguage: GEEN enkele weergavetekst staat hier hardcoded. Elke functie
neemt een `taal`-parameter (default "nl_NL") en haalt alle tekst op via
app.helpers.i18n.vertaal().

Belangrijk (§9 en §26 van PROJECT_CONTEXT): er wordt hier NERGENS een
automatische frequentieconversie uitgevoerd. Een frequentieverschil
tussen meting en referentie leidt uitsluitend tot een waarschuwing en
een lagere betrouwbaarheid — nooit tot een herberekende waarde.
================================================================================
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.config.settings import (
    CAPACITEIT_FACTOR_NAAR_FARAD,
    BeoordelingsInstellingen,
    laad_instellingen,
)
from app.helpers.i18n import STANDAARD_TAAL, vertaal
from app.helpers.units import converteer_esr


# ---------------------------------------------------------------------------
# Statussen — neutrale, taalonafhankelijke codes (§17 context, §3-§7
# validation_rules.md). De .value is de vertaalsleutel-suffix, NOOIT het
# weergegeven label.
# ---------------------------------------------------------------------------
class CapaciteitsStatus(str, Enum):
    BINNEN_TOLERANTIE = "binnen_tolerantie"
    OP_GRENS = "op_grens"
    BUITEN_TOLERANTIE = "buiten_tolerantie"
    NIET_BEOORDEELBAAR = "niet_beoordeelbaar"


class EsrStatus(str, Enum):
    WAARSCHIJNLIJK_NORMAAL = "waarschijnlijk_normaal"
    AANDACHTSPUNT = "aandachtspunt"
    VERDACHT = "verdacht"
    WAARSCHIJNLIJK_DEFECT = "waarschijnlijk_defect"
    NIET_TE_BEOORDELEN = "niet_te_beoordelen"


class ConsistentieStatus(str, Enum):
    NIET_BEOORDEELD = "niet_beoordeeld"
    CONSISTENT = "consistent"
    MOGELIJKE_INCONSISTENTIE = "mogelijke_inconsistentie"
    STERKE_AANWIJZING_EENHEDENFOUT = "sterke_aanwijzing_eenhedenfout"


class Betrouwbaarheid(str, Enum):
    HOOG = "hoog"
    MIDDEL = "middel"
    LAAG = "laag"


class Meetmethode(str, Enum):
    """Fysieke meetopstelling; exact één waarde per meting."""

    EX_SITU = "EX_SITU"
    ONE_LEG = "ONE_LEG"
    IN_CIRCUIT = "IN_CIRCUIT"


class Eindstatus(str, Enum):
    NIET_BEOORDEELD = "niet_beoordeeld"
    WAARSCHIJNLIJK_GOED = "waarschijnlijk_goed"
    AANDACHTSPUNT = "aandachtspunt"
    TWIJFELACHTIG = "twijfelachtig"
    WAARSCHIJNLIJK_DEFECT = "waarschijnlijk_defect"
    NIET_TE_BEOORDELEN = "niet_te_beoordelen"


_BETROUWBAARHEID_ORDINAAL = {
    Betrouwbaarheid.LAAG: 0,
    Betrouwbaarheid.MIDDEL: 1,
    Betrouwbaarheid.HOOG: 2,
}
_ORDINAAL_NAAR_BETROUWBAARHEID = {v: k for k, v in _BETROUWBAARHEID_ORDINAAL.items()}


def status_label(namespace: str, status_waarde: str, taal: str = STANDAARD_TAAL) -> str:
    """Vertaalt een statuscode naar het weergegeven label.

    Bv. status_label("status.capaciteit", CapaciteitsStatus.OP_GRENS.value)
    -> "op grens" (nl_NL) of "at the boundary" (en_US).
    """
    return vertaal(f"{namespace}.{status_waarde}", taal=taal)


def veiligheidswaarschuwingen(taal: str = STANDAARD_TAAL) -> tuple[str, ...]:
    """Vaste veiligheidswaarschuwingen (§19 context, §10 validation_rules.md),
    vertaald naar de gevraagde taal. Letterlijk te tonen op elk scherm met
    meetinvoer of -resultaat.
    """
    return tuple(
        vertaal(f"veiligheid.waarschuwing_{i}", taal=taal) for i in range(1, 10)
    )


# ---------------------------------------------------------------------------
# Resultaatstructuren — elk resultaat is transparant opgebouwd (§18 context)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CapaciteitsResultaat:
    status: CapaciteitsStatus
    nominale_waarde: Optional[float]
    gemeten_waarde: Optional[float]
    eenheid: Optional[str]
    tolerantie_percent: Optional[float]
    afwijking_absoluut: Optional[float]
    afwijking_percent: Optional[float]
    toelichting: str


@dataclass(frozen=True)
class ReferentieContext:
    """Alle informatie over de referentiebron die voor de ESR-vergelijking
    gebruikt wordt. Wordt door de aanroepende code samengesteld op basis
    van de referentiehiërarchie (§2 validation_rules.md) — deze module
    kiest zelf geen referentie, ze past ze enkel toe.
    """

    esr_waarde: float
    eenheid: str
    bron: str
    referentieniveau: int  # 1 (exacte datasheet) t.e.m. 7 (relatieve vergelijking)
    frequentie_hz: float
    typisch_of_maximaal: str  # "typisch" | "maximaal"
    temperatuur_c: Optional[float] = None
    condensatortype: Optional[str] = None
    fabrikant: Optional[str] = None
    serie: Optional[str] = None


@dataclass(frozen=True)
class EsrResultaat:
    status: EsrStatus
    factor: Optional[float]
    gemeten_esr_ohm: Optional[float]
    referentie_esr_ohm: Optional[float]
    referentiebron: Optional[str]
    referentieniveau: Optional[int]
    frequentie_wijkt_af: bool
    toelichting: str


@dataclass(frozen=True)
class ConsistentieResultaat:
    status: ConsistentieStatus
    esr_verwacht_ohm: Optional[float]
    esr_gemeten_ohm: Optional[float]
    factor: Optional[float]
    toelichting: str


@dataclass(frozen=True)
class BetrouwbaarheidsResultaat:
    niveau: Betrouwbaarheid
    verlagende_factoren: tuple[str, ...]


@dataclass(frozen=True)
class Beoordeling:
    """Het volledige, transparante eindresultaat van een meting (§18 context)."""

    eindstatus: Eindstatus
    redenen: tuple[str, ...]
    aanbevolen_vervolgstap: str
    waarschuwingen: tuple[str, ...]
    capaciteit: CapaciteitsResultaat
    esr: EsrResultaat
    consistentie: ConsistentieResultaat
    betrouwbaarheid: BetrouwbaarheidsResultaat
    meetmethode: Meetmethode
    instrument_code: Optional[str]
    testspanning_vrms: Optional[float]


# ---------------------------------------------------------------------------
# §3 — Capaciteitsvalidatie
# ---------------------------------------------------------------------------
def beoordeel_capaciteit(
    nominale_capaciteit: float,
    eenheid_nominaal: str,
    gemeten_capaciteit: float,
    eenheid_gemeten: str,
    tolerantie_percent: Optional[float],
    instellingen: Optional[BeoordelingsInstellingen] = None,
    taal: str = STANDAARD_TAAL,
) -> CapaciteitsResultaat:
    """Beoordeelt de gemeten capaciteit t.o.v. de nominale waarde en
    tolerantie (docs/validation_rules.md §3).

    De eenheidsconversie tussen `eenheid_nominaal` en `eenheid_gemeten`
    is toegelaten (expliciete eenheidsconversie, geen frequentieconversie).
    """

    from app.helpers.units import converteer_capaciteit  # lokale import: geen cirkel

    instellingen = instellingen or laad_instellingen().beoordeling

    if tolerantie_percent is None:
        return CapaciteitsResultaat(
            status=CapaciteitsStatus.NIET_BEOORDEELBAAR,
            nominale_waarde=nominale_capaciteit,
            gemeten_waarde=None,
            eenheid=eenheid_nominaal,
            tolerantie_percent=None,
            afwijking_absoluut=None,
            afwijking_percent=None,
            toelichting=vertaal("toelichting.capaciteit.tolerantie_onbekend", taal=taal),
        )

    gemeten_in_nominale_eenheid = converteer_capaciteit(
        gemeten_capaciteit, eenheid_gemeten, eenheid_nominaal
    )
    afwijking_absoluut = gemeten_in_nominale_eenheid - nominale_capaciteit
    afwijking_percent = (afwijking_absoluut / nominale_capaciteit) * 100.0
    abs_afwijking_percent = abs(afwijking_percent)

    grens_binnen = tolerantie_percent * instellingen.capaciteit_marge_binnen

    if abs_afwijking_percent <= grens_binnen:
        status = CapaciteitsStatus.BINNEN_TOLERANTIE
    elif abs_afwijking_percent <= tolerantie_percent:
        status = CapaciteitsStatus.OP_GRENS
    else:
        status = CapaciteitsStatus.BUITEN_TOLERANTIE

    toelichting = vertaal(
        "toelichting.capaciteit.resultaat",
        taal=taal,
        gemeten=gemeten_in_nominale_eenheid,
        eenheid=eenheid_nominaal,
        nominaal=nominale_capaciteit,
        afwijking=afwijking_percent,
        tolerantie=tolerantie_percent,
    )

    return CapaciteitsResultaat(
        status=status,
        nominale_waarde=nominale_capaciteit,
        gemeten_waarde=gemeten_in_nominale_eenheid,
        eenheid=eenheid_nominaal,
        tolerantie_percent=tolerantie_percent,
        afwijking_absoluut=afwijking_absoluut,
        afwijking_percent=afwijking_percent,
        toelichting=toelichting,
    )


# ---------------------------------------------------------------------------
# §4 — Indicatieve ESR-beoordeling
# ---------------------------------------------------------------------------
def beoordeel_esr(
    gemeten_esr: float,
    eenheid_gemeten_esr: str,
    meetfrequentie_hz: float,
    referentie: Optional[ReferentieContext],
    instellingen: Optional[BeoordelingsInstellingen] = None,
    taal: str = STANDAARD_TAAL,
) -> EsrResultaat:
    """Vergelijkt de gemeten ESR met de gekozen referentie
    (docs/validation_rules.md §4). Geeft NIET_TE_BEOORDELEN als er geen
    referentie is (§2: geen enkel hiërarchieniveau leverde bruikbare data).

    Er wordt GEEN automatische frequentieconversie uitgevoerd; een
    frequentieverschil leidt enkel tot een waarschuwing in de toelichting.
    """

    instellingen = instellingen or laad_instellingen().beoordeling

    if referentie is None:
        return EsrResultaat(
            status=EsrStatus.NIET_TE_BEOORDELEN,
            factor=None,
            gemeten_esr_ohm=None,
            referentie_esr_ohm=None,
            referentiebron=None,
            referentieniveau=None,
            frequentie_wijkt_af=False,
            toelichting=vertaal("toelichting.esr.geen_referentie", taal=taal),
        )

    gemeten_ohm = converteer_esr(gemeten_esr, eenheid_gemeten_esr, "Ω")
    referentie_ohm = converteer_esr(referentie.esr_waarde, referentie.eenheid, "Ω")

    # Een ESR-referentie zonder meetfrequentie is volgens het datamodel
    # onvolledig en mag niet als numerieke vergelijkingsgrens worden gebruikt.
    # Er wordt bewust geen frequentie aangenomen of omgerekend.
    if referentie.frequentie_hz is None:
        return EsrResultaat(
            status=EsrStatus.NIET_TE_BEOORDELEN,
            factor=None,
            gemeten_esr_ohm=gemeten_ohm,
            referentie_esr_ohm=referentie_ohm,
            referentiebron=referentie.bron,
            referentieniveau=referentie.referentieniveau,
            frequentie_wijkt_af=False,
            toelichting=vertaal("toelichting.esr.referentie_ongeldig", taal=taal),
        )

    if referentie_ohm <= 0:
        return EsrResultaat(
            status=EsrStatus.NIET_TE_BEOORDELEN,
            factor=None,
            gemeten_esr_ohm=gemeten_ohm,
            referentie_esr_ohm=referentie_ohm,
            referentiebron=referentie.bron,
            referentieniveau=referentie.referentieniveau,
            frequentie_wijkt_af=False,
            toelichting=vertaal("toelichting.esr.referentie_ongeldig", taal=taal),
        )

    factor = gemeten_ohm / referentie_ohm

    if factor <= instellingen.esr_factor_normaal:
        status = EsrStatus.WAARSCHIJNLIJK_NORMAAL
    elif factor <= instellingen.esr_factor_aandachtspunt:
        status = EsrStatus.AANDACHTSPUNT
    elif factor <= instellingen.esr_factor_verdacht:
        status = EsrStatus.VERDACHT
    else:
        status = EsrStatus.WAARSCHIJNLIJK_DEFECT

    frequentie_wijkt_af = meetfrequentie_hz != referentie.frequentie_hz

    toelichting = vertaal(
        "toelichting.esr.resultaat",
        taal=taal,
        factor=factor,
        bron=referentie.bron,
        niveau=referentie.referentieniveau,
        frequentie=referentie.frequentie_hz,
        typisch_of_maximaal=referentie.typisch_of_maximaal,
    )
    if frequentie_wijkt_af:
        toelichting += vertaal(
            "toelichting.esr.frequentie_waarschuwing",
            taal=taal,
            meetfrequentie=meetfrequentie_hz,
            referentiefrequentie=referentie.frequentie_hz,
        )

    return EsrResultaat(
        status=status,
        factor=factor,
        gemeten_esr_ohm=gemeten_ohm,
        referentie_esr_ohm=referentie_ohm,
        referentiebron=referentie.bron,
        referentieniveau=referentie.referentieniveau,
        frequentie_wijkt_af=frequentie_wijkt_af,
        toelichting=toelichting,
    )


# ---------------------------------------------------------------------------
# §5 — Interne C-ESR-D-consistentiecontrole (signaal, geen afkeurregel)
# ---------------------------------------------------------------------------
def controleer_consistentie(
    gemeten_capaciteit: float,
    eenheid_capaciteit: str,
    gemeten_esr: float,
    eenheid_esr: str,
    D: Optional[float],
    frequentie_hz: float,
    instellingen: Optional[BeoordelingsInstellingen] = None,
    taal: str = STANDAARD_TAAL,
) -> ConsistentieResultaat:
    """Grove plausibiliteitscheck: D ≈ 2·π·f·C·ESR (docs/validation_rules.md §5).

    Dit is uitdrukkelijk GEEN goed/afkeurregel — enkel een signaal om
    eenhedenfouten, mΩ/Ω-verwisseling of een verkeerde frequentie te
    helpen detecteren. Zonder D-waarde wordt geen controle uitgevoerd.
    """

    instellingen = instellingen or laad_instellingen().beoordeling

    if D is None:
        return ConsistentieResultaat(
            status=ConsistentieStatus.NIET_BEOORDEELD,
            esr_verwacht_ohm=None,
            esr_gemeten_ohm=None,
            factor=None,
            toelichting=vertaal("toelichting.consistentie.geen_d", taal=taal),
        )

    if gemeten_capaciteit <= 0 or frequentie_hz <= 0:
        return ConsistentieResultaat(
            status=ConsistentieStatus.NIET_BEOORDEELD,
            esr_verwacht_ohm=None,
            esr_gemeten_ohm=None,
            factor=None,
            toelichting=vertaal("toelichting.consistentie.ongeldige_invoer", taal=taal),
        )

    c_farad = gemeten_capaciteit * CAPACITEIT_FACTOR_NAAR_FARAD[eenheid_capaciteit]
    esr_gemeten_ohm = converteer_esr(gemeten_esr, eenheid_esr, "Ω")

    esr_verwacht_ohm = D / (2 * math.pi * frequentie_hz * c_farad)

    if esr_verwacht_ohm <= 0 or esr_gemeten_ohm <= 0:
        return ConsistentieResultaat(
            status=ConsistentieStatus.NIET_BEOORDEELD,
            esr_verwacht_ohm=esr_verwacht_ohm,
            esr_gemeten_ohm=esr_gemeten_ohm,
            factor=None,
            toelichting=vertaal("toelichting.consistentie.niet_positief", taal=taal),
        )

    factor = max(esr_gemeten_ohm, esr_verwacht_ohm) / min(esr_gemeten_ohm, esr_verwacht_ohm)

    if factor <= instellingen.consistentie_marge:
        status = ConsistentieStatus.CONSISTENT
        toelichting = vertaal(
            "toelichting.consistentie.consistent",
            taal=taal,
            esr_gemeten=esr_gemeten_ohm,
            esr_verwacht=esr_verwacht_ohm,
            marge=instellingen.consistentie_marge,
        )
    elif factor < instellingen.consistentie_eenhedenfout_drempel:
        status = ConsistentieStatus.MOGELIJKE_INCONSISTENTIE
        toelichting = vertaal(
            "toelichting.consistentie.mogelijke_inconsistentie",
            taal=taal,
            esr_gemeten=esr_gemeten_ohm,
            factor=factor,
            esr_verwacht=esr_verwacht_ohm,
        )
    else:
        status = ConsistentieStatus.STERKE_AANWIJZING_EENHEDENFOUT
        toelichting = vertaal(
            "toelichting.consistentie.sterke_aanwijzing", taal=taal, factor=factor
        )

    return ConsistentieResultaat(
        status=status,
        esr_verwacht_ohm=esr_verwacht_ohm,
        esr_gemeten_ohm=esr_gemeten_ohm,
        factor=factor,
        toelichting=toelichting,
    )


# ---------------------------------------------------------------------------
# §6 — Betrouwbaarheid
# ---------------------------------------------------------------------------
def bepaal_betrouwbaarheid(
    referentieniveau: Optional[int],
    referentiefrequentie_hz: Optional[float],
    meetfrequentie_hz: float,
    omgevingstemperatuur_c: Optional[float],
    condensatortype: str,
    meetmethode: Meetmethode | str,
    referentie_typisch_of_maximaal: Optional[str],
    fabrikant_bekend: bool,
    serie_bekend: bool,
    consistentie_status: ConsistentieStatus,
    referentie_condensatortype: Optional[str] = None,
    taal: str = STANDAARD_TAAL,
) -> BetrouwbaarheidsResultaat:
    """Bepaalt betrouwbaarheid uit bronkwaliteit en meetcontext.

    De meetmethode is geen losse boolean meer:
    EX_SITU  -> geen extra bovengrens;
    ONE_LEG  -> betrouwbaarheid maximaal MIDDEL;
    IN_CIRCUIT -> betrouwbaarheid maximaal LAAG.

    Andere verlagende factoren blijven cumulatief van toepassing.
    """

    try:
        methode = meetmethode if isinstance(meetmethode, Meetmethode) else Meetmethode(meetmethode)
    except ValueError as exc:
        raise ValueError(f"Onbekende meetmethode: {meetmethode}") from exc

    if referentieniveau is None:
        start_niveau = Betrouwbaarheid.LAAG
    elif referentieniveau <= 3:
        start_niveau = Betrouwbaarheid.HOOG
    elif referentieniveau <= 5:
        start_niveau = Betrouwbaarheid.MIDDEL
    else:
        start_niveau = Betrouwbaarheid.LAAG

    verlagende_factoren: list[str] = []

    if referentiefrequentie_hz is None:
        # Zonder bekende referentiefrequentie is een ESR-vergelijking niet
        # voldoende onderbouwd; betrouwbaarheid blijft daarom maximaal LAAG.
        start_niveau = Betrouwbaarheid.LAAG
    elif referentiefrequentie_hz != meetfrequentie_hz:
        verlagende_factoren.append(
            vertaal("betrouwbaarheid_factor.referentiefrequentie_wijkt_af", taal=taal)
        )

    if omgevingstemperatuur_c is None:
        verlagende_factoren.append(
            vertaal("betrouwbaarheid_factor.temperatuur_onbekend", taal=taal)
        )

    if condensatortype != "Aluminium elektrolytisch":
        verlagende_factoren.append(
            vertaal("betrouwbaarheid_factor.condensatortype_onbekend", taal=taal)
        )

    if (
        referentie_condensatortype
        and referentie_condensatortype != condensatortype
    ):
        verlagende_factoren.append(
            vertaal("betrouwbaarheid_factor.referentietype_wijkt_af", taal=taal)
        )

    if referentie_typisch_of_maximaal == "typisch":
        verlagende_factoren.append(
            vertaal("betrouwbaarheid_factor.typisch_niet_maximaal", taal=taal)
        )

    if not fabrikant_bekend or not serie_bekend:
        verlagende_factoren.append(
            vertaal("betrouwbaarheid_factor.fabrikant_serie_onbekend", taal=taal)
        )

    if consistentie_status in (
        ConsistentieStatus.MOGELIJKE_INCONSISTENTIE,
        ConsistentieStatus.STERKE_AANWIJZING_EENHEDENFOUT,
    ):
        verlagende_factoren.append(
            vertaal("betrouwbaarheid_factor.mogelijke_inconsistentie", taal=taal)
        )

    ordinaal = _BETROUWBAARHEID_ORDINAAL[start_niveau] - len(verlagende_factoren)
    ordinaal = max(0, ordinaal)

    if methode == Meetmethode.ONE_LEG:
        verlagende_factoren.append(
            vertaal("betrouwbaarheid_factor.one_leg", taal=taal)
        )
        ordinaal = min(ordinaal, _BETROUWBAARHEID_ORDINAAL[Betrouwbaarheid.MIDDEL])
    elif methode == Meetmethode.IN_CIRCUIT:
        verlagende_factoren.append(
            vertaal("betrouwbaarheid_factor.in_circuit", taal=taal)
        )
        ordinaal = _BETROUWBAARHEID_ORDINAAL[Betrouwbaarheid.LAAG]

    # Een bewust gekozen referentie van een ander condensatortype is nooit
    # betrouwbaarder dan LAAG.
    if (
        referentie_condensatortype
        and referentie_condensatortype != condensatortype
    ):
        ordinaal = _BETROUWBAARHEID_ORDINAAL[Betrouwbaarheid.LAAG]

    eind_niveau = _ORDINAAL_NAAR_BETROUWBAARHEID[ordinaal]

    return BetrouwbaarheidsResultaat(
        niveau=eind_niveau,
        verlagende_factoren=tuple(verlagende_factoren),
    )


# ---------------------------------------------------------------------------
# §7 — Eindstatus
# ---------------------------------------------------------------------------
def bepaal_eindstatus(
    capaciteit: CapaciteitsResultaat,
    esr: EsrResultaat,
    consistentie: ConsistentieResultaat,
    betrouwbaarheid: BetrouwbaarheidsResultaat,
    veiligheid_bevestigd: bool,
    invoer_volledig: bool = True,
    vermoedelijke_open_verbinding_of_kortsluiting: bool = False,
    meetwaarde_buiten_bereik: bool = False,
    taal: str = STANDAARD_TAAL,
) -> tuple[Eindstatus, tuple[str, ...], str]:
    """Stelt de eindstatus samen uit de deelresultaten
    (docs/validation_rules.md §7). Kiest bij twijfel altijd het
    voorzichtigste (laagste) niveau — nooit optimistisch afronden.

    Geeft (eindstatus, redenen, aanbevolen_vervolgstap) terug.
    """

    if meetwaarde_buiten_bereik:
        return (
            Eindstatus.NIET_TE_BEOORDELEN,
            (vertaal("eindstatus_reden.buiten_bereik", taal=taal),),
            vertaal("eindstatus_vervolgstap.controleer_meetbereik", taal=taal),
        )

    if not invoer_volledig:
        return (
            Eindstatus.NIET_BEOORDEELD,
            (vertaal("eindstatus_reden.invoer_onvolledig", taal=taal),),
            vertaal("eindstatus_vervolgstap.vul_aan", taal=taal),
        )

    redenen: list[str] = []
    if capaciteit.status == CapaciteitsStatus.NIET_BEOORDEELBAAR:
        redenen.append(vertaal("eindstatus_reden.tolerantie_onbekend", taal=taal))
    if esr.status == EsrStatus.NIET_TE_BEOORDELEN:
        redenen.append(vertaal("eindstatus_reden.geen_referentie", taal=taal))
    if not veiligheid_bevestigd:
        redenen.append(vertaal("eindstatus_reden.veiligheid_ontbreekt", taal=taal))

    if redenen:
        return (
            Eindstatus.NIET_TE_BEOORDELEN,
            tuple(redenen),
            vertaal("eindstatus_vervolgstap.vul_aan_of_bevestig", taal=taal),
        )

    sterke_inconsistentie = consistentie.status == ConsistentieStatus.STERKE_AANWIJZING_EENHEDENFOUT
    mogelijke_inconsistentie = consistentie.status == ConsistentieStatus.MOGELIJKE_INCONSISTENTIE

    if capaciteit.status == CapaciteitsStatus.BUITEN_TOLERANTIE and vermoedelijke_open_verbinding_of_kortsluiting:
        return (
            Eindstatus.WAARSCHIJNLIJK_DEFECT,
            (
                vertaal("eindstatus_reden.capaciteit_buiten_tolerantie_defect", taal=taal),
                vertaal("eindstatus_reden.open_verbinding_vermoed", taal=taal),
            ),
            vertaal("eindstatus_vervolgstap.vervang_component", taal=taal),
        )

    if esr.status == EsrStatus.WAARSCHIJNLIJK_DEFECT and betrouwbaarheid.niveau in (
        Betrouwbaarheid.HOOG,
        Betrouwbaarheid.MIDDEL,
    ):
        niveau_label = status_label("status.betrouwbaarheid", betrouwbaarheid.niveau.value, taal)
        return (
            Eindstatus.WAARSCHIJNLIJK_DEFECT,
            (
                esr.toelichting,
                vertaal("eindstatus_reden.betrouwbaarheid_label", taal=taal, niveau=niveau_label),
            ),
            vertaal("eindstatus_vervolgstap.vervang_of_bevestig", taal=taal),
        )

    aantal_alarmsignalen = sum(
        [
            esr.status in (EsrStatus.VERDACHT, EsrStatus.WAARSCHIJNLIJK_DEFECT),
            capaciteit.status == CapaciteitsStatus.BUITEN_TOLERANTIE,
            sterke_inconsistentie,
        ]
    )
    if aantal_alarmsignalen >= 2:
        return (
            Eindstatus.WAARSCHIJNLIJK_DEFECT,
            (
                vertaal("eindstatus_reden.meerdere_criteria", taal=taal),
                capaciteit.toelichting,
                esr.toelichting,
                consistentie.toelichting,
            ),
            vertaal("eindstatus_vervolgstap.vervang_of_bevestig", taal=taal),
        )

    if (
        capaciteit.status == CapaciteitsStatus.BUITEN_TOLERANTIE
        or esr.status == EsrStatus.VERDACHT
        or mogelijke_inconsistentie
    ):
        return (
            Eindstatus.TWIJFELACHTIG,
            (capaciteit.toelichting, esr.toelichting, consistentie.toelichting),
            vertaal("eindstatus_vervolgstap.vergelijk_of_ontkoppel", taal=taal),
        )

    if (
        capaciteit.status == CapaciteitsStatus.OP_GRENS
        or esr.status == EsrStatus.AANDACHTSPUNT
        or betrouwbaarheid.niveau == Betrouwbaarheid.LAAG
    ):
        niveau_label = status_label("status.betrouwbaarheid", betrouwbaarheid.niveau.value, taal)
        factoren_tekst = ", ".join(betrouwbaarheid.verlagende_factoren) or vertaal(
            "betrouwbaarheid_factor.geen_verlagende_factoren", taal=taal
        )
        return (
            Eindstatus.AANDACHTSPUNT,
            (
                capaciteit.toelichting,
                esr.toelichting,
                vertaal(
                    "eindstatus_reden.betrouwbaarheid_met_factoren",
                    taal=taal,
                    niveau=niveau_label,
                    factoren=factoren_tekst,
                ),
            ),
            vertaal("eindstatus_vervolgstap.herhaal_meting", taal=taal),
        )

    if (
        capaciteit.status == CapaciteitsStatus.BINNEN_TOLERANTIE
        and esr.status == EsrStatus.WAARSCHIJNLIJK_NORMAAL
        and not sterke_inconsistentie
        and betrouwbaarheid.niveau != Betrouwbaarheid.LAAG
    ):
        return (
            Eindstatus.WAARSCHIJNLIJK_GOED,
            (capaciteit.toelichting, esr.toelichting),
            vertaal("eindstatus_vervolgstap.geen_actie", taal=taal),
        )

    # Vangnet: geen enkele striktere regel was van toepassing. Conservatief
    # ingeschat als aandachtspunt in plaats van optimistisch af te ronden.
    return (
        Eindstatus.AANDACHTSPUNT,
        (
            vertaal("eindstatus_reden.geen_striktere_regel", taal=taal),
            capaciteit.toelichting,
            esr.toelichting,
        ),
        vertaal("eindstatus_vervolgstap.controleer_handmatig", taal=taal),
    )


# ---------------------------------------------------------------------------
# Orkestratie: alle stappen samen (§1 volgorde van beoordeling)
# ---------------------------------------------------------------------------
def beoordeel_meting(
    *,
    nominale_capaciteit: float,
    eenheid_nominaal: str,
    tolerantie_percent: Optional[float],
    gemeten_capaciteit: float,
    eenheid_gemeten_capaciteit: str,
    gemeten_esr: float,
    eenheid_gemeten_esr: str,
    meetfrequentie_hz: float,
    D: Optional[float],
    condensatortype: str,
    meetmethode: Meetmethode | str,
    omgevingstemperatuur_c: Optional[float],
    instrument_code: Optional[str] = None,
    testspanning_vrms: Optional[float] = None,
    veiligheid_bevestigd: bool,
    referentie: Optional[ReferentieContext] = None,
    fabrikant_bekend: bool = False,
    serie_bekend: bool = False,
    vermoedelijke_open_verbinding_of_kortsluiting: bool = False,
    meetwaarde_buiten_bereik: bool = False,
    invoer_volledig: bool = True,
    instellingen: Optional[BeoordelingsInstellingen] = None,
    taal: str = STANDAARD_TAAL,
) -> Beoordeling:
    """Voert de volledige beoordelingsketen uit.

    `meetmethode` is verplicht en exclusief. `meetwaarde_buiten_bereik`
    forceert de eindstatus naar NIET_TE_BEOORDELEN; ingevoerde numerieke
    waarden worden dan alleen als registratie beschouwd.
    """

    instellingen = instellingen or laad_instellingen().beoordeling
    methode = meetmethode if isinstance(meetmethode, Meetmethode) else Meetmethode(meetmethode)

    capaciteit_resultaat = beoordeel_capaciteit(
        nominale_capaciteit,
        eenheid_nominaal,
        gemeten_capaciteit,
        eenheid_gemeten_capaciteit,
        tolerantie_percent,
        instellingen,
        taal,
    )

    # Automatische type mismatch wordt niet aanvaard als betrouwbare bron.
    referentie_type_mismatch = bool(
        referentie
        and referentie.condensatortype
        and referentie.condensatortype != condensatortype
    )

    esr_resultaat = beoordeel_esr(
        gemeten_esr,
        eenheid_gemeten_esr,
        meetfrequentie_hz,
        referentie,
        instellingen,
        taal,
    )

    consistentie_resultaat = controleer_consistentie(
        gemeten_capaciteit,
        eenheid_gemeten_capaciteit,
        gemeten_esr,
        eenheid_gemeten_esr,
        D,
        meetfrequentie_hz,
        instellingen,
        taal,
    )

    betrouwbaarheid_resultaat = bepaal_betrouwbaarheid(
        referentieniveau=referentie.referentieniveau if referentie else None,
        referentiefrequentie_hz=referentie.frequentie_hz if referentie else None,
        meetfrequentie_hz=meetfrequentie_hz,
        omgevingstemperatuur_c=omgevingstemperatuur_c,
        condensatortype=condensatortype,
        meetmethode=methode,
        referentie_typisch_of_maximaal=referentie.typisch_of_maximaal if referentie else None,
        fabrikant_bekend=fabrikant_bekend,
        serie_bekend=serie_bekend,
        consistentie_status=consistentie_resultaat.status,
        referentie_condensatortype=referentie.condensatortype if referentie else None,
        taal=taal,
    )

    eindstatus, redenen, vervolgstap = bepaal_eindstatus(
        capaciteit_resultaat,
        esr_resultaat,
        consistentie_resultaat,
        betrouwbaarheid_resultaat,
        veiligheid_bevestigd,
        invoer_volledig,
        vermoedelijke_open_verbinding_of_kortsluiting,
        meetwaarde_buiten_bereik,
        taal,
    )

    waarschuwingen: list[str] = []

    if esr_resultaat.frequentie_wijkt_af:
        waarschuwingen.append(
            vertaal("veiligheid.frequentie_wijkt_af", taal=taal)
        )

    if methode == Meetmethode.IN_CIRCUIT:
        waarschuwingen.append(
            vertaal("veiligheid.in_circuit", taal=taal)
        )
    elif methode == Meetmethode.ONE_LEG:
        waarschuwingen.append(
            vertaal("veiligheid.one_leg", taal=taal)
        )

    if referentie_type_mismatch:
        waarschuwingen.append(
            vertaal("veiligheid.referentietype_wijkt_af", taal=taal)
        )

    if meetwaarde_buiten_bereik:
        waarschuwingen.append(
            vertaal("veiligheid.buiten_bereik", taal=taal)
        )

    if (
        consistentie_resultaat.status
        == ConsistentieStatus.STERKE_AANWIJZING_EENHEDENFOUT
    ):
        waarschuwingen.append(
            vertaal("veiligheid.eenhedenfout", taal=taal)
        )

    return Beoordeling(
        eindstatus=eindstatus,
        redenen=redenen,
        aanbevolen_vervolgstap=vervolgstap,
        waarschuwingen=tuple(waarschuwingen),
        capaciteit=capaciteit_resultaat,
        esr=esr_resultaat,
        consistentie=consistentie_resultaat,
        betrouwbaarheid=betrouwbaarheid_resultaat,
        meetmethode=methode,
        instrument_code=instrument_code,
        testspanning_vrms=testspanning_vrms,
    )
