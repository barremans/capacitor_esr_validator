"""
================================================================================
Module:     app/services/assessment_service.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.7.1
Datum:      2026-10-26
Auteur:     Ontwikkelaar

Doel:       Kernlogica van de indicatieve beoordeling: capaciteitsvalidatie,
            indicatieve ESR-beoordeling, interne C-ESR-D-consistentiecontrole,
            betrouwbaarheidsbepaling en de samengestelde eindstatus. Bevat
            GEEN GUI-code en raakt de database niet rechtstreeks aan.

Wijzigingen:
  v1.0.0 (2026-08-11)  Initiele versie. Volledige beoordelingsketen.
  v1.1.0 (2026-09-26)  Meetmethode als expliciete enum.
  v1.2.0 (2026-09-26)  Instrumentcode en testspanning in resultaat.
  v1.3.0 (2026-09-29)  Referentie zonder frequentie veilig afgehandeld.
  v1.4.0 (2026-10-15)  Beoordeling.referentiefrequentie_hz.
  v1.5.0 (2026-10-16)  Inhoudelijke vs. administratieve verlagers.
  v1.6.0 (2026-10-16)  Beoordeling.taal.
  v1.7.0 (2026-10-26)  Chat 4 / 4A: B1 (familie-predicaat) en B2
                       (fysieke plausibiliteitscheck).
  v1.7.1 (2026-10-26)  Chat 4 / 4C: harde type-match §14.
                       - De lokale definities van `is_elektrolytisch_type`
                         en `_zelfde_technologie_familie` zijn verplaatst
                         naar app.helpers.technology (één bron van
                         waarheid, gedeeld met app.data.references en
                         app.gui.esr_test_screen). De namen blijven
                         beschikbaar via re-export.
                       - `beoordeel_meting` voegt een extra waarschuwing
                         toe (`veiligheid.geen_elektrolytische_referentie`)
                         wanneer het condensatortype niet elektrolytisch
                         is. Zo ziet de gebruiker expliciet dat de
                         beoordeling zonder elektrolytische ESR-referentie
                         is uitgevoerd, ook al geeft de GUI standaard al
                         geen referentie meer.

Referentie: docs/validation_rules.md (volledig), in het bijzonder:
            §2 referentiehiërarchie, §3 capaciteitsvalidatie,
            §4 indicatieve ESR-beoordeling, §5 consistentiecontrole,
            §6 betrouwbaarheid, §7 eindstatus, §10 veiligheidsteksten,
            §14 type-match.
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
from app.helpers.technology import (
    is_elektrolytisch_type,
    zelfde_technologie_familie,
)
from app.helpers.units import converteer_esr


# ---------------------------------------------------------------------------
# Statussen — neutrale, taalonafhankelijke codes.
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


# Re-export voor backward-compat: bestaande tests importeren
# `is_elektrolytisch_type` uit deze module. De implementatie staat in
# app.helpers.technology (sinds 4C).
__all__ = [
    "is_elektrolytisch_type",
    "zelfde_technologie_familie",
    "status_label",
    "veiligheidswaarschuwingen",
    "CapaciteitsStatus",
    "EsrStatus",
    "ConsistentieStatus",
    "Betrouwbaarheid",
    "Meetmethode",
    "Eindstatus",
    "CapaciteitsResultaat",
    "ReferentieContext",
    "EsrResultaat",
    "ConsistentieResultaat",
    "BetrouwbaarheidsResultaat",
    "Beoordeling",
    "beoordeel_capaciteit",
    "beoordeel_esr",
    "controleer_consistentie",
    "bepaal_betrouwbaarheid",
    "bepaal_eindstatus",
    "beoordeel_meting",
]


def status_label(namespace: str, status_waarde: str, taal: str = STANDAARD_TAAL) -> str:
    """Vertaalt een statuscode naar het weergegeven label."""
    return vertaal(f"{namespace}.{status_waarde}", taal=taal)


def veiligheidswaarschuwingen(taal: str = STANDAARD_TAAL) -> tuple[str, ...]:
    """Vaste veiligheidswaarschuwingen (§19 context, §10 validation_rules.md)."""
    return tuple(
        vertaal(f"veiligheid.waarschuwing_{i}", taal=taal) for i in range(1, 10)
    )


# ---------------------------------------------------------------------------
# Resultaatstructuren
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
    gebruikt wordt.
    """

    esr_waarde: float
    eenheid: str
    bron: str
    referentieniveau: int
    frequentie_hz: float
    typisch_of_maximaal: str
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
    """Betrouwbaarheid met onderscheid tussen inhoudelijke en administratieve
    verlagers (fase 11B).
    """

    niveau: Betrouwbaarheid
    verlagende_factoren: tuple[str, ...]
    inhoudelijke_verlagers: tuple[str, ...] = ()


@dataclass(frozen=True)
class Beoordeling:
    """Het volledige, transparante eindresultaat van een meting (§18 context).
    """

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
    referentiefrequentie_hz: Optional[float] = None
    taal: str = STANDAARD_TAAL


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
    """
    from app.helpers.units import converteer_capaciteit  # lokale import: geen cirkel

    instellingen = instellingen or laad_instellingen().beoordeling

    gemeten_in_nominale_eenheid = converteer_capaciteit(
        gemeten_capaciteit, eenheid_gemeten, eenheid_nominaal
    )
    gemeten_in_farad = (
        gemeten_in_nominale_eenheid
        * CAPACITEIT_FACTOR_NAAR_FARAD[eenheid_nominaal]
    )

    # 4A sanity: capaciteit moet fysiek realistisch zijn vóór beoordeling.
    if gemeten_in_farad < instellingen.capaciteit_min_realistisch_f:
        return CapaciteitsResultaat(
            status=CapaciteitsStatus.NIET_BEOORDEELBAAR,
            nominale_waarde=nominale_capaciteit,
            gemeten_waarde=gemeten_in_nominale_eenheid,
            eenheid=eenheid_nominaal,
            tolerantie_percent=tolerantie_percent,
            afwijking_absoluut=None,
            afwijking_percent=None,
            toelichting=vertaal(
                "toelichting.capaciteit.fysiek_onrealistisch",
                taal=taal,
                gemeten=gemeten_in_nominale_eenheid,
                eenheid=eenheid_nominaal,
            ),
        )

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
    (docs/validation_rules.md §4).
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

    # 4A sanity: ESR moet fysiek realistisch zijn vóór beoordeling.
    if gemeten_ohm < instellingen.esr_min_realistisch_ohm:
        return EsrResultaat(
            status=EsrStatus.NIET_TE_BEOORDELEN,
            factor=None,
            gemeten_esr_ohm=gemeten_ohm,
            referentie_esr_ohm=referentie_ohm,
            referentiebron=referentie.bron,
            referentieniveau=referentie.referentieniveau,
            frequentie_wijkt_af=False,
            toelichting=vertaal(
                "toelichting.esr.fysiek_onrealistisch",
                taal=taal,
                gemeten=gemeten_esr,
                eenheid=eenheid_gemeten_esr,
            ),
        )

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
# §5 — Interne C-ESR-D-consistentiecontrole
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
    inhoudelijke_verlagers: list[str] = []

    if referentiefrequentie_hz is None:
        start_niveau = Betrouwbaarheid.LAAG
    elif referentiefrequentie_hz != meetfrequentie_hz:
        tekst = vertaal("betrouwbaarheid_factor.referentiefrequentie_wijkt_af", taal=taal)
        verlagende_factoren.append(tekst)
        inhoudelijke_verlagers.append(tekst)

    if omgevingstemperatuur_c is None:
        verlagende_factoren.append(
            vertaal("betrouwbaarheid_factor.temperatuur_onbekend", taal=taal)
        )

    # Familie-predicaat via de gedeelde helper.
    if not is_elektrolytisch_type(condensatortype):
        tekst = vertaal("betrouwbaarheid_factor.condensatortype_onbekend", taal=taal)
        verlagende_factoren.append(tekst)
        inhoudelijke_verlagers.append(tekst)

    # Type-mismatch tussen referentie en meting via de gedeelde helper.
    if referentie_condensatortype and not zelfde_technologie_familie(
        referentie_condensatortype, condensatortype
    ):
        tekst = vertaal("betrouwbaarheid_factor.referentietype_wijkt_af", taal=taal)
        verlagende_factoren.append(tekst)
        inhoudelijke_verlagers.append(tekst)

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
        tekst = vertaal("betrouwbaarheid_factor.mogelijke_inconsistentie", taal=taal)
        verlagende_factoren.append(tekst)
        inhoudelijke_verlagers.append(tekst)

    ordinaal = _BETROUWBAARHEID_ORDINAAL[start_niveau] - len(verlagende_factoren)
    ordinaal = max(0, ordinaal)

    if methode == Meetmethode.ONE_LEG:
        tekst = vertaal("betrouwbaarheid_factor.one_leg", taal=taal)
        verlagende_factoren.append(tekst)
        inhoudelijke_verlagers.append(tekst)
        ordinaal = min(ordinaal, _BETROUWBAARHEID_ORDINAAL[Betrouwbaarheid.MIDDEL])
    elif methode == Meetmethode.IN_CIRCUIT:
        tekst = vertaal("betrouwbaarheid_factor.in_circuit", taal=taal)
        verlagende_factoren.append(tekst)
        inhoudelijke_verlagers.append(tekst)
        ordinaal = _BETROUWBAARHEID_ORDINAAL[Betrouwbaarheid.LAAG]

    if referentie_condensatortype and not zelfde_technologie_familie(
        referentie_condensatortype, condensatortype
    ):
        ordinaal = _BETROUWBAARHEID_ORDINAAL[Betrouwbaarheid.LAAG]

    eind_niveau = _ORDINAAL_NAAR_BETROUWBAARHEID[ordinaal]

    return BetrouwbaarheidsResultaat(
        niveau=eind_niveau,
        verlagende_factoren=tuple(verlagende_factoren),
        inhoudelijke_verlagers=tuple(inhoudelijke_verlagers),
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
    (docs/validation_rules.md §7).
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
        or betrouwbaarheid.inhoudelijke_verlagers
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
    ):
        if betrouwbaarheid.niveau == Betrouwbaarheid.LAAG:
            niveau_label = status_label(
                "status.betrouwbaarheid", betrouwbaarheid.niveau.value, taal
            )
            factoren_tekst = ", ".join(betrouwbaarheid.verlagende_factoren) or vertaal(
                "betrouwbaarheid_factor.geen_verlagende_factoren", taal=taal
            )
            return (
                Eindstatus.WAARSCHIJNLIJK_GOED,
                (
                    capaciteit.toelichting,
                    esr.toelichting,
                    vertaal(
                        "eindstatus_reden.betrouwbaarheid_laag_administratief",
                        taal=taal,
                        niveau=niveau_label,
                        factoren=factoren_tekst,
                    ),
                ),
                vertaal("eindstatus_vervolgstap.geen_actie", taal=taal),
            )
        return (
            Eindstatus.WAARSCHIJNLIJK_GOED,
            (capaciteit.toelichting, esr.toelichting),
            vertaal("eindstatus_vervolgstap.geen_actie", taal=taal),
        )

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
# Orkestratie: alle stappen samen
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

    # 4C: technologie-match via de gedeelde helper.
    referentie_type_mismatch = bool(
        referentie
        and referentie.condensatortype
        and not zelfde_technologie_familie(referentie.condensatortype, condensatortype)
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

    if (
        esr_resultaat.gemeten_esr_ohm is not None
        and esr_resultaat.gemeten_esr_ohm < instellingen.esr_min_realistisch_ohm
    ):
        waarschuwingen.append(
            vertaal("veiligheid.esr_onrealistisch", taal=taal)
        )
    if (
        capaciteit_resultaat.gemeten_waarde is not None
        and capaciteit_resultaat.eenheid is not None
        and capaciteit_resultaat.gemeten_waarde
        * CAPACITEIT_FACTOR_NAAR_FARAD[capaciteit_resultaat.eenheid]
        < instellingen.capaciteit_min_realistisch_f
    ):
        waarschuwingen.append(
            vertaal("veiligheid.capaciteit_onrealistisch", taal=taal)
        )

    # 4C: expliciete waarschuwing wanneer het condensatortype niet
    # elektrolytisch is. De GUI geeft in dat geval al geen referentie
    # meer, maar de waarschuwing maakt het ook zichtbaar voor andere
    # aanroepers van de assessment-service.
    if not is_elektrolytisch_type(condensatortype):
        waarschuwingen.append(
            vertaal("veiligheid.geen_elektrolytische_referentie", taal=taal)
        )

    referentiefrequentie_hz = referentie.frequentie_hz if referentie else None

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
        referentiefrequentie_hz=referentiefrequentie_hz,
        taal=taal,
    )