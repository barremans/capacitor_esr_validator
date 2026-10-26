"""
================================================================================
Module:     app/data/references/__init__.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     2.1.0
Datum:      2026-10-26
Auteur:     Ontwikkelaar

Doel:       Laadt de ingebouwde referentietabellen uit esr_references.json
            en biedt een functie om de beste matching referentie te vinden
            voor een gegeven condensator. Ondersteunt meerdere profielen
            per frequentie. Kiest op basis van meetfrequentie.

            Sinds 4C wordt de technologie-match hard afgedwongen: een
            niet-elektrolytisch condensatortype levert geen referentie
            terug, ook niet via de default-parameter. De match werkt via
            de familie-logica uit app.helpers.technology, zodat
            "Aluminium elektrolytisch — Low ESR" wel matcht met het
            standaardprofiel.

Wijzigingen:
  v1.0.0 (2026-08-11)  Initiele versie. JSON-lader voor Peak Atlas ESR70
                       tabel, zoekfunctie op capaciteit en spanningsklasse.
  v2.0.0 (2026-10-15)  Profielen-model: meerdere profielen in één JSON,
                       elk met eigen frequentie en bron. zoek_referentie
                       accepteert meetfrequentie_hz en kiest het beste
                       profiel. Bij geen exacte match wordt het
                       dichtstbijzijnde profiel gekozen met fallback-
                       waarschuwing. Kleine capaciteiten (0,1–2,2 µF)
                       krijgen een apart screeningsprofiel.
  v2.1.0 (2026-10-26)  Chat 4 / 4C: harde type-match §14. De
                       standaardparameter blijft "Aluminium elektrolytisch"
                       voor backward-compat, maar:
                       - Een niet-elektrolytisch type levert None terug,
                         ongeacht of het via de default of expliciet
                         wordt doorgegeven. Geen stille terugval op een
                         elektrolytisch profiel.
                       - De profielselectie gebruikt familie-logica via
                         is_elektrolytisch_type, zodat Low ESR en
                         Bipolair/NP wel matchen.
                       - condensatortype=None matcht op alle profielen
                         (escape-hatch voor geavanceerd gebruik of
                         toekomstige technologieën).

Referentie: docs/validation_rules.md §2 (referentiehiërarchie) en §14
            (type-match), docs/context.md §14, overdracht.md §8.
================================================================================
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.helpers.technology import is_elektrolytisch_type
from app.services.assessment_service import ReferentieContext


@dataclass(frozen=True)
class EsrReferentieRegel:
    capaciteit_uf: float
    spanningsklasse_v: float
    esr_max_mohm: float


@dataclass(frozen=True)
class EsrReferentieProfiel:
    id: str
    naam: str
    bron: str
    bron_url: str
    condensatortype: str
    referentieniveau: int
    frequentie_hz: float
    typisch_of_maximaal: str
    betrouwbaarheidsniveau: str
    is_schatting: bool
    regels: tuple[EsrReferentieRegel, ...]


_PROFIELEN: list[EsrReferentieProfiel] = []
_PROFIELEN_GELADEN: bool = False


def _laad_profielen() -> list[EsrReferentieProfiel]:
    """Laadt alle profielen uit esr_references.json."""
    global _PROFIELEN, _PROFIELEN_GELADEN
    if _PROFIELEN_GELADEN:
        return _PROFIELEN

    root = Path(__file__).resolve().parent
    pad = root / "esr_references.json"
    if not pad.exists():
        _PROFIELEN_GELADEN = True
        return _PROFIELEN

    with pad.open("r", encoding="utf-8") as f:
        data = json.load(f)

    for profiel_data in data.get("profiles", []):
        regels = tuple(
            EsrReferentieRegel(
                capaciteit_uf=r["capaciteit_uf"],
                spanningsklasse_v=r["spanningsklasse_v"],
                esr_max_mohm=r["esr_max_mohm"],
            )
            for r in profiel_data.get("tabel", [])
        )
        profiel = EsrReferentieProfiel(
            id=profiel_data["id"],
            naam=profiel_data["naam"],
            bron=profiel_data["bron"],
            bron_url=profiel_data.get("bron_url", ""),
            condensatortype=profiel_data["condensatortype"],
            referentieniveau=profiel_data["referentieniveau"],
            frequentie_hz=profiel_data["frequentie_hz"],
            typisch_of_maximaal=profiel_data["typisch_of_maximaal"],
            betrouwbaarheidsniveau=profiel_data["betrouwbaarheidsniveau"],
            is_schatting=bool(profiel_data.get("is_schatting", False)),
            regels=regels,
        )
        _PROFIELEN.append(profiel)

    _PROFIELEN_GELADEN = True
    return _PROFIELEN


def _profiel_matcht_type(
    profiel: EsrReferentieProfiel,
    condensatortype: Optional[str],
) -> bool:
    """Bepaalt of een profiel bij het opgegeven condensatortype past.

    Sinds 4C: familie-match via is_elektrolytisch_type in plaats van
    exacte string-gelijkheid. Twee elektrolytische varianten matchen
    elkaar (bv. "Low ESR" met het standaardprofiel). Een
    niet-elektrolytisch type matcht nooit een elektrolytisch profiel.

    ``condensatortype=None`` matcht op alle profielen (escape-hatch).
    """
    if condensatortype is None:
        return True
    return is_elektrolytisch_type(profiel.condensatortype) == is_elektrolytisch_type(
        condensatortype
    )


def _beste_profiel_voor_frequentie(
    profielen: list[EsrReferentieProfiel],
    frequentie_hz: float,
    condensatortype: Optional[str],
) -> Optional[EsrReferentieProfiel]:
    """Kies het profiel met de dichtstbijzijnde frequentie.

    Voorkeur:
    1. Exacte frequentie-match.
    2. Dichtstbijzijnde frequentie.
    Alleen profielen met regels en met een passend technologie-type
    komen in aanmerking.
    """
    kandidaten = [
        p
        for p in profielen
        if _profiel_matcht_type(p, condensatortype) and len(p.regels) > 0
    ]
    if not kandidaten:
        return None

    # Exacte match
    for p in kandidaten:
        if p.frequentie_hz == frequentie_hz:
            return p

    # Dichtstbijzijnde
    return min(kandidaten, key=lambda p: abs(p.frequentie_hz - frequentie_hz))


def _beste_regel(
    profiel: EsrReferentieProfiel,
    capaciteit_uf: float,
    spanningsklasse_v: float,
) -> Optional[EsrReferentieRegel]:
    """Vind de dichtstbijzijnde regel binnen een profiel.

    Matcht eerst op capaciteit (logaritmisch), dan op spanning.
    """
    if not profiel.regels:
        return None

    # Dichtstbijzijnde capaciteit
    beste_cap = min(profiel.regels, key=lambda r: abs(r.capaciteit_uf - capaciteit_uf))
    cap_afw = abs(beste_cap.capaciteit_uf - capaciteit_uf)

    # Als de capaciteit binnen 20% zit, zoek dan de beste spanningsmatch
    # onder regels met (bijna) dezelfde capaciteit.
    if beste_cap.capaciteit_uf > 0 and cap_afw / beste_cap.capaciteit_uf <= 0.20:
        zelfde_cap = [
            r
            for r in profiel.regels
            if r.capaciteit_uf == beste_cap.capaciteit_uf
        ]
        if zelfde_cap:
            return min(
               zelfde_cap,
                key=lambda r: abs(r.spanningsklasse_v - spanningsklasse_v),
            )

    # Fallback: dichtstbijzijnde op capaciteit + spanning gecombineerd
    return min(
        profiel.regels,
        key=lambda r: (
            abs(r.capaciteit_uf - capaciteit_uf),
            abs(r.spanningsklasse_v - spanningsklasse_v),
        ),
    )


def zoek_referentie(
    capaciteit_uf: float,
    spanningsklasse_v: float,
    condensatortype: Optional[str] = "Aluminium elektrolytisch",
    meetfrequentie_hz: Optional[float] = None,
) -> Optional[ReferentieContext]:
    """Zoekt de beste matching referentie.

    Wanneer `meetfrequentie_hz` wordt meegegeven, kiest de functie het
    profiel met de dichtstbijzijnde frequentie. Wanneer die parameter
    ontbreekt, valt de functie terug op het eerst beschikbare profiel
    met regels (doorgaans ESR70 100 kHz), voor backward-compatibiliteit.

    Sinds 4C wordt de technologie-match hard afgedwongen:
    - Een niet-elektrolytisch type (tantaal, polymer, film, keramisch,
      supercondensator, Anders, Onbekend) levert ``None`` terug. Er is
      geen stille terugval op een elektrolytisch profiel.
    - Twee elektrolytische varianten matchen elkaar via de familie-
      logica (bv. "Low ESR" met het standaardprofiel).
    - ``condensatortype=None`` matcht op alle profielen (escape-hatch).
    """
    # 4C: harde blokkade vóór profielselectie. Een niet-elektrolytisch
    # type mag nooit een elektrolytisch profiel krijgen.
    if condensatortype is not None and not is_elektrolytisch_type(condensatortype):
        return None

    profielen = _laad_profielen()

    if meetfrequentie_hz is None:
        # Backward-compatible: kies het eerste passende profiel met regels.
        for p in profielen:
            if _profiel_matcht_type(p, condensatortype) and len(p.regels) > 0:
                profiel = p
                break
        else:
            return None
    else:
        profiel = _beste_profiel_voor_frequentie(
            profielen, meetfrequentie_hz, condensatortype
        )
        if profiel is None:
            return None

    regel = _beste_regel(profiel, capaciteit_uf, spanningsklasse_v)
    if regel is None:
        return None

    return ReferentieContext(
        esr_waarde=regel.esr_max_mohm,
        eenheid="mΩ",
        bron=profiel.bron,
        referentieniveau=profiel.referentieniveau,
        frequentie_hz=profiel.frequentie_hz,
        typisch_of_maximaal=profiel.typisch_of_maximaal,
        temperatuur_c=20.0,
        condensatortype=profiel.condensatortype,
    )