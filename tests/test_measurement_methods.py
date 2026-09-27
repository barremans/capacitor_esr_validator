"""
================================================================================
Module:     tests/test_measurement_methods.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.0.0
Datum:      2026-09-26
Auteur:     Ontwikkelaar

Doel:       Geparametriseerde regressietests voor verschillende fysieke
            meetopstellingen en testspanningen.

Wijzigingen:
  v1.0.0 (2026-09-26)  Eerste versie.

Versiebeheer:
  - MAJOR: incompatibele test/API-wijziging.
  - MINOR: nieuwe testscenario's.
  - PATCH: correcties/refactor.
================================================================================
"""

import pytest

from app.services.assessment_service import (
    Betrouwbaarheid,
    ConsistentieStatus,
    Meetmethode,
    bepaal_betrouwbaarheid,
)


@pytest.mark.parametrize(
    ("meetmethode", "verwacht"),
    [
        (Meetmethode.EX_SITU, Betrouwbaarheid.HOOG),
        (Meetmethode.ONE_LEG, Betrouwbaarheid.MIDDEL),
        (Meetmethode.IN_CIRCUIT, Betrouwbaarheid.LAAG),
    ],
)
def test_betrouwbaarheid_per_meetmethode(meetmethode, verwacht):
    resultaat = bepaal_betrouwbaarheid(
        referentieniveau=1,
        referentiefrequentie_hz=1_000,
        meetfrequentie_hz=1_000,
        omgevingstemperatuur_c=20,
        condensatortype="Aluminium elektrolytisch",
        meetmethode=meetmethode,
        referentie_typisch_of_maximaal="maximaal",
        fabrikant_bekend=True,
        serie_bekend=True,
        consistentie_status=ConsistentieStatus.CONSISTENT,
    )
    assert resultaat.niveau == verwacht
