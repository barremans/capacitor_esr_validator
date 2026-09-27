"""
================================================================================
Module:     tests/test_gui_regressions.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.0.0
Datum:      2026-09-26
Auteur:     Ontwikkelaar

Doel:       Regressietests voor GUI-gerelateerde invoerregels die rechtstreeks
            invloed hebben op de beoordelingslogica.

Wijzigingen:
  v1.0.0 (2026-09-26)  Eerste regressietests voor standaardtolerantie en
                       praktijkmeting 330 µF / 35 V.

Versiebeheer:
  - MAJOR: incompatibele architectuur- of API-wijziging.
  - MINOR: nieuwe functionaliteit.
  - PATCH: bugfix, kleine optimalisatie of interne refactor.
  - Bij elke wijziging: Versie, Datum en Wijzigingen hierboven bijwerken.
================================================================================
"""

import pytest

from app.services.assessment_service import (
    CapaciteitsStatus,
    ConsistentieStatus,
    Meetmethode,
    beoordeel_meting,
)


def test_praktijkmeting_330uf_35v_tolerantie_wordt_gebruikt():
    resultaat = beoordeel_meting(
        nominale_capaciteit=330.0,
        eenheid_nominaal="µF",
        tolerantie_percent=20.0,
        gemeten_capaciteit=286.2,
        eenheid_gemeten_capaciteit="µF",
        gemeten_esr=62.3,
        eenheid_gemeten_esr="mΩ",
        meetfrequentie_hz=10_000.0,
        D=1.1207,
        condensatortype="Aluminium elektrolytisch",
        meetmethode=Meetmethode.EX_SITU,
        omgevingstemperatuur_c=20.0,
        instrument_code="LCR_ST1",
        testspanning_vrms=0.3,
        veiligheid_bevestigd=True,
        referentie=None,
        fabrikant_bekend=False,
        serie_bekend=False,
    )

    assert resultaat.capaciteit.tolerantie_percent == pytest.approx(20.0)
    assert resultaat.capaciteit.afwijking_percent == pytest.approx(-13.272727, rel=1e-5)
    assert resultaat.capaciteit.status in {
        CapaciteitsStatus.BINNEN_TOLERANTIE,
        CapaciteitsStatus.OP_GRENS,
    }
    assert resultaat.consistentie.status == ConsistentieStatus.CONSISTENT
    assert resultaat.consistentie.esr_verwacht_ohm == pytest.approx(0.06232, rel=2e-3)
