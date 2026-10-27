"""
================================================================================
Module:     tests/test_analysis_series.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-27
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de pure analyse-reeksfuncties.

Wijzigingen:
  v1.0.0 (2026-10-09)  Eerste versie.
  v1.1.0 (2026-10-27)  Fase 5D: vier tests voor build_vergelijk_reeksen().
                        Bewijst de volgorde (ids bepalen kleur_index), de
                        max_reeksen-validatie, het lege-input-gedrag en
                        de ESR-sortering per reeks.
================================================================================
"""

from __future__ import annotations

from typing import Any

import pytest

from app.helpers.analysis_series import (
    TimeSeriesPoint,
    VergelijkReeks,
    aggregate_time_series,
    build_vergelijk_reeksen,
)


def _row(
    measurement_id: int,
    measured_at_ms: int,
    *,
    esr_ohm: float | None = 0.1,
    tool_key: str = "ESR_CAPACITOR",
) -> dict[str, Any]:
    """Minimale rij zoals StorageService.list_measurements() teruggeeft."""

    class _M:
        pass

    m = _M()
    m.id = measurement_id
    m.measured_at_ms = measured_at_ms
    m.tool_key = tool_key
    m.esr_ohm = esr_ohm
    m.capacitance_f = None
    m.dissipation_factor_d = None
    return {"measurement": m, "final_status": None}


def test_build_vergelijk_reeksen_volgt_ids_volgorde() -> None:
    """De volgorde van de reeksen volgt measurement_ids, niet de sortering van rijen."""
    rijen = [
        _row(1, 1_000, esr_ohm=0.1),
        _row(2, 2_000, esr_ohm=0.2),
        _row(3, 3_000, esr_ohm=0.3),
    ]
    reeksen = build_vergelijk_reeksen(
        rijen, measurement_ids=[3, 1], max_reeksen=5
    )
    assert isinstance(reeksen, list)
    assert all(isinstance(r, VergelijkReeks) for r in reeksen)
    assert [r.measurement_id for r in reeksen] == [3, 1]
    assert [r.color_index for r in reeksen] == [0, 1]
    assert reeksen[0].points == (
        TimeSeriesPoint(3_000, 0.3, 3, "ESR_CAPACITOR"),
    )
    assert reeksen[1].points == (
        TimeSeriesPoint(1_000, 0.1, 1, "ESR_CAPACITOR"),
    )


def test_build_vergelijk_reeksen_te_veel_reeksen_faalt() -> None:
    """Bij meer dan max_reeksen: ValueError met het aantal en het maximum."""
    rijen = [_row(i, i * 1_000) for i in range(1, 7)]
    with pytest.raises(ValueError, match="Te veel reeksen"):
        build_vergelijk_reeksen(
            rijen, measurement_ids=[1, 2, 3, 4, 5, 6], max_reeksen=5
        )


def test_build_vergelijk_reeksen_max_reeksen_moet_positief_zijn() -> None:
    """max_reeksen < 1 is ongeldig."""
    with pytest.raises(ValueError, match="max_reeksen"):
        build_vergelijk_reeksen([], measurement_ids=[1], max_reeksen=0)


def test_build_vergelijk_reeksen_leeg_geeft_lege_reeksen() -> None:
    """Bij een lege rijenset blijven de reeksen bestaan, maar zonder punten.

    Dat is bewust: de gebruiker heeft de meting aangevinkt, dus de
    legenda moet hem tonen, ook als de reeks leeg is.
    """
    reeksen = build_vergelijk_reeksen(
        [], measurement_ids=[1, 2], max_reeksen=5
    )
    assert len(reeksen) == 2
    assert reeksen[0].measurement_id == 1
    assert reeksen[0].points == ()
    assert reeksen[1].measurement_id == 2
    assert reeksen[1].points == ()