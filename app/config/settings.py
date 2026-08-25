"""
================================================================================
Module:     app/config/settings.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.0.0
Datum:      2026-08-11
Auteur:     Ontwikkelaar

Doel:       Centrale, aanpasbare instellingen voor de app.
            Geen beoordelingslogica hier, enkel waarden.

Wijzigingen:
  v1.0.0 (2026-08-11)  Initiele versie. Configureerbare drempels,
                       vaste keuzelijsten, eenheidsconversiefactoren.
                       Gebaseerd op docs/validation_rules.md §11.

Referentie: docs/validation_rules.md §11 (Samenvatting configureerbare
            parameters) en docs/data_model.md §9 (vaste keuzelijsten).
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field

import json
import os
from pathlib import Path

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

    # ESR-verhoudingsdrempels (validation_rules.md §4, §12 context).
    esr_factor_normaal: float = 1.0
    esr_factor_aandachtspunt: float = 2.0
    esr_factor_verdacht: float = 3.0

    # Capaciteitstolerantie: aandeel van tolerantie_percent waarbinnen
    # een afwijking nog als "binnen tolerantie" geldt, i.p.v. "op grens".
    # [AANNAME], zie validation_rules.md §3.
    capaciteit_marge_binnen: float = 0.9

    # Interne C-ESR-D-consistentiecontrole. [AANNAME], open vraag 13
    # (welke foutmarge is aanvaardbaar), zie validation_rules.md §5.
    consistentie_marge: float = 2.0
    consistentie_eenhedenfout_drempel: float = 100.0


@dataclass(frozen=True)
class AppInstellingen:
    """Verzamelt alle instellingen die de app nodig heeft bij opstart."""

    taal: str = "nl_NL"
    beoordeling: BeoordelingsInstellingen = field(
        default_factory=BeoordelingsInstellingen
    )


def laad_instellingen() -> AppInstellingen:
    """Laadt instellingen uit settings.json, of default als bestand ontbreekt."""
    if SETTINGS_PATH.exists():
        try:
            with SETTINGS_PATH.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return AppInstellingen(
                taal=data.get("language", "nl_NL"),
                beoordeling=BeoordelingsInstellingen(**data.get("beoordeling", {}))
            )
        except Exception:
            pass
    return AppInstellingen()

def sla_instellingen_op(instellingen: AppInstellingen) -> None:
    """Slaat instellingen op naar settings.json."""
    data = {
        "language": instellingen.taal,
        "beoordeling": {
            "esr_factor_normaal": instellingen.beoordeling.esr_factor_normaal,
            "esr_factor_aandachtspunt": instellingen.beoordeling.esr_factor_aandachtspunt,
            "esr_factor_verdacht": instellingen.beoordeling.esr_factor_verdacht,
            "capaciteit_marge_binnen": instellingen.beoordeling.capaciteit_marge_binnen,
            "consistentie_marge": instellingen.beoordeling.consistentie_marge,
            "consistentie_eenhedenfout_drempel": instellingen.beoordeling.consistentie_eenhedenfout_drempel,
        }
    }
    with SETTINGS_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)