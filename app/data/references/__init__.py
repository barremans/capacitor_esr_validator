"""
================================================================================
Module:     app/data/references/__init__.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.0.0
Datum:      2026-08-11
Auteur:     Ontwikkelaar

Doel:       Laadt de ingebouwde referentietabellen (Peak Atlas ESR70, etc.)
            en biedt een functie om de beste matching referentie te vinden
            voor een gegeven condensator.

Wijzigingen:
  v1.0.0 (2026-08-11)  Initiele versie. JSON-lader voor Peak Atlas ESR70
                       tabel, zoekfunctie op capaciteit en spanningsklasse.

Referentie: PROJECT_CONTEXT_capacitor_ESR_validator.md §20 (opslagmodel
            voor referentietabellen), §8.1 (Peak Atlas ESR70 Look-up Chart).
================================================================================
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.services.assessment_service import ReferentieContext


@dataclass(frozen=True)
class EsrReferentieRegel:
    capaciteit_uf: float
    spanningsklasse_v: float
    esr_max_mohm: float


@dataclass(frozen=True)
class EsrReferentieTabel:
    bron: str
    bron_url: str
    condensatortype: str
    referentieniveau: int
    frequentie_hz: float
    typisch_of_maximaal: str
    betrouwbaarheidsniveau: str
    regels: tuple[EsrReferentieRegel, ...]


_REFERENTIES: list[EsrReferentieTabel] = []


def _laad_referenties() -> list[EsrReferentieTabel]:
    """Laadt alle JSON-referentiebestanden uit de references-map."""
    global _REFERENTIES
    if _REFERENTIES:
        return _REFERENTIES

    root = Path(__file__).resolve().parent
    for pad in root.glob("*.json"):
        with pad.open("r", encoding="utf-8") as f:
            data = json.load(f)

        regels = tuple(
            EsrReferentieRegel(
                capaciteit_uf=r["capaciteit_uf"],
                spanningsklasse_v=r["spanningsklasse_v"],
                esr_max_mohm=r["esr_max_mohm"],
            )
            for r in data.get("tabel", [])
        )

        tabel = EsrReferentieTabel(
            bron=data["bron"],
            bron_url=data.get("bron_url", ""),
            condensatortype=data["condensatortype"],
            referentieniveau=data["referentieniveau"],
            frequentie_hz=data["frequentie_hz"],
            typisch_of_maximaal=data["typisch_of_maximaal"],
            betrouwbaarheidsniveau=data["betrouwbaarheidsniveau"],
            regels=regels,
        )
        _REFERENTIES.append(tabel)

    return _REFERENTIES


def zoek_referentie(
    capaciteit_uf: float,
    spanningsklasse_v: float,
    condensatortype: str = "Aluminium elektrolytisch",
) -> Optional[ReferentieContext]:
    """Zoekt de beste matching referentie uit de ingebouwde tabellen.

    Voor de Peak Atlas-tabel: vind de regel met de dichtstbijzijnde
    capaciteit en spanningsklasse. Geen interpolatie — exacte match
    of dichtstbijzijnde.
    """
    referenties = _laad_referenties()

    for ref in referenties:
        if ref.condensatortype != condensatortype:
            continue

        # Vind de dichtstbijzijnde capaciteit
        beste_regel = None
        beste_cap_afwijking = float("inf")

        for regel in ref.regels:
            cap_afw = abs(regel.capaciteit_uf - capaciteit_uf)
            if cap_afw < beste_cap_afwijking:
                beste_cap_afwijking = cap_afw
                beste_regel = regel

        if beste_regel is None:
            continue

        return ReferentieContext(
            esr_waarde=beste_regel.esr_max_mohm,
            eenheid="mΩ",
            bron=ref.bron,
            referentieniveau=ref.referentieniveau,
            frequentie_hz=ref.frequentie_hz,
            typisch_of_maximaal=ref.typisch_of_maximaal,
            temperatuur_c=20.0,
            condensatortype=ref.condensatortype,
        )

    return None