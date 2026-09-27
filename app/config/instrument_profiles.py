"""
================================================================================
Module:     app/config/instrument_profiles.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.0.0
Datum:      2026-09-26
Auteur:     Ontwikkelaar

Doel:       Centrale instrumentprofielen voor meettoestellen. Een profiel
            definieert alleen toestelcapaciteiten (zoals frequenties en
            testspanningen), geen beoordelingslogica.

Wijzigingen:
  v1.0.0 (2026-09-26)  Eerste versie met LCR-ST1 Smart Tweezer en een generiek
                       handmatig profiel.

Versiebeheer:
  - MAJOR: incompatibele architectuur/API-wijziging.
  - MINOR: nieuwe functionaliteit.
  - PATCH: bugfix/refactor.
  - Bij elke wijziging: Versie, Datum en Wijzigingen hierboven bijwerken.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InstrumentProfiel:
    """Beschrijft de instelbare meetmogelijkheden van één instrument."""

    code: str
    naam: str
    frequenties_hz: tuple[int, ...]
    testspanningen_vrms: tuple[float, ...]
    standaard_frequentie_hz: int | None = None
    standaard_testspanning_vrms: float | None = None


INSTRUMENT_PROFIELEN: dict[str, InstrumentProfiel] = {
    "LCR_ST1": InstrumentProfiel(
        code="LCR_ST1",
        naam="LCR-ST1 Smart Tweezer",
        frequenties_hz=(100, 1_000, 10_000),
        testspanningen_vrms=(0.3, 0.6),
        standaard_frequentie_hz=1_000,
        standaard_testspanning_vrms=0.3,
    ),
    "MANUAL": InstrumentProfiel(
        code="MANUAL",
        naam="Handmatig / ander toestel",
        frequenties_hz=(100, 1_000, 10_000),
        testspanningen_vrms=(0.3, 0.6),
        standaard_frequentie_hz=1_000,
        standaard_testspanning_vrms=0.3,
    ),
}


def get_instrument_profiel(code: str) -> InstrumentProfiel:
    """Geeft een profiel terug en faalt expliciet bij een onbekende code."""
    try:
        return INSTRUMENT_PROFIELEN[code]
    except KeyError as exc:
        raise ValueError(f"Onbekend instrumentprofiel: {code}") from exc
