"""
================================================================================
Module:     app/helpers/units.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.0.0
Datum:      2026-08-11
Auteur:     Ontwikkelaar

Doel:       Kleine, herbruikbare hulpfuncties voor het parsen van decimale
            getallen (komma of punt) en het omzetten van capaciteits- en
            ESR-eenheden. GEEN beoordelingslogica.

Wijzigingen:
  v1.0.0 (2026-08-11)  Initiele versie. parse_decimaal, converteer_capaciteit,
                       converteer_esr.

Referentie: docs/data_model.md §9 (vaste keuzelijsten), §3-6 (getal-
            velden met komma/punt); docs/validation_rules.md §3
            (expliciete eenheidsconversie is toegelaten, in tegenstelling
            tot frequentieconversie).

Belangrijk: dit is EENHEIDSconversie (pF <-> µF, mΩ <-> Ω), wat volgens
het contextdocument (§9) uitdrukkelijk is toegelaten. Dit is NIET de
frequentieconversie die nergens automatisch mag gebeuren.
================================================================================
"""

from __future__ import annotations

from app.config.settings import CAPACITEIT_FACTOR_NAAR_FARAD, ESR_FACTOR_NAAR_OHM


def parse_decimaal(tekst: str) -> float:
    """Zet een door de gebruiker ingevoerde tekst om naar een float.

    Aanvaardt zowel komma als punt als decimaalteken (docs/data_model.md,
    testgeval 3 uit de context: "Komma en punt als decimaalteken").
    Spaties rond de tekst worden genegeerd. Duizendtalscheidingstekens
    worden bewust NIET ondersteund, om dubbelzinnigheid met het
    decimaalteken te vermijden (bv. "1.234" zou zowel 1234 als 1,234
    kunnen betekenen) — de gebruiker voert waarden zonder scheidingsteken in.

    Raises:
        ValueError: als de tekst geen geldig getal voorstelt.
    """
    if tekst is None:
        raise ValueError("Geen waarde ingevoerd.")

    schoon = tekst.strip()
    if schoon == "":
        raise ValueError("Geen waarde ingevoerd.")

    genormaliseerd = schoon.replace(",", ".")

    try:
        return float(genormaliseerd)
    except ValueError as exc:
        raise ValueError(f"'{tekst}' is geen geldig getal.") from exc


def _valideer_eenheid(eenheid: str, toegelaten: dict) -> None:
    if eenheid not in toegelaten:
        opties = ", ".join(toegelaten.keys())
        raise ValueError(
            f"Onbekende eenheid '{eenheid}'. Toegelaten waarden: {opties}."
        )


def converteer_capaciteit(waarde: float, van_eenheid: str, naar_eenheid: str) -> float:
    """Zet een capaciteitswaarde om tussen pF, nF, µF en mF.

    Dit is expliciete eenheidsconversie op vraag van de gebruiker/de
    app-logica (bv. om nominale en gemeten capaciteit te vergelijken in
    dezelfde eenheid, docs/validation_rules.md §3) — géén automatische
    frequentieconversie.
    """
    _valideer_eenheid(van_eenheid, CAPACITEIT_FACTOR_NAAR_FARAD)
    _valideer_eenheid(naar_eenheid, CAPACITEIT_FACTOR_NAAR_FARAD)

    waarde_in_farad = waarde * CAPACITEIT_FACTOR_NAAR_FARAD[van_eenheid]
    return waarde_in_farad / CAPACITEIT_FACTOR_NAAR_FARAD[naar_eenheid]


def converteer_esr(waarde: float, van_eenheid: str, naar_eenheid: str) -> float:
    """Zet een ESR-waarde om tussen mΩ en Ω.

    Zie docs/validation_rules.md §4: beide waarden moeten in dezelfde
    eenheid staan vóór vergelijking; dit is de expliciete conversie die
    dat mogelijk maakt (testgeval 2 uit de context).
    """
    _valideer_eenheid(van_eenheid, ESR_FACTOR_NAAR_OHM)
    _valideer_eenheid(naar_eenheid, ESR_FACTOR_NAAR_OHM)

    waarde_in_ohm = waarde * ESR_FACTOR_NAAR_OHM[van_eenheid]
    return waarde_in_ohm / ESR_FACTOR_NAAR_OHM[naar_eenheid]