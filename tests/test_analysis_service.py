"""
================================================================================
Module:     tests/test_analysis_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.2.0
Datum:      2026-10-27
Auteur:     Bart Bossuyt

Doel:       Regressietests voor AnalysisService.

Wijzigingen:
  v1.0.0 (2026-10-09)  Eerste versie: ESR/C/D-reeksen, scatter,
                        aggregaties.
  v1.1.0 (2026-10-20)  Fase 11G.5: tests voor de optionele
                        measurement_ids-filter in load_rows en in de
                        reeksfuncties.
  v1.2.0 (2026-10-27)  Fase 5D: vier tests voor vergelijken(). Bewijst
                        de volgorde, de max_reeksen-validatie, het
                        lege-input-gedrag en de lege rijen-input.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from app.helpers.analysis_series import (
    ScatterPoint,
    TimeSeriesPoint,
    VergelijkReeks,
)
from app.services.analysis_service import AnalysisService


@dataclass
class _FakeMeasurement:
    id: int
    measured_at_ms: int
    tool_key: str = "ESR_CAPACITOR"
    esr_ohm: float | None = None
    capacitance_f: float | None = None
    dissipation_factor_d: float | None = None


def _row(
    measurement_id: int,
    measured_at_ms: int,
    *,
    esr_ohm: float | None = None,
    capacitance_f: float | None = None,
    dissipation_factor_d: float | None = None,
) -> dict[str, Any]:
    return {
        "measurement": _FakeMeasurement(
            id=measurement_id,
            measured_at_ms=measured_at_ms,
            esr_ohm=esr_ohm,
            capacitance_f=capacitance_f,
            dissipation_factor_d=dissipation_factor_d,
        ),
        "manufacturer": "TEST",
        "series": "SYN",
        "final_status": None,
    }


class _FakeHistory:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = list(rows)

    def list_measurements(self, filters=None, *, limit=100, offset=0):
        return self._rows[offset:offset + limit]


def _make_service(rows: list[dict[str, Any]]) -> AnalysisService:
    return AnalysisService(history_service=_FakeHistory(rows))


def test_load_rows_zonder_filter_geeft_alle_rijen() -> None:
    service = _make_service([
        _row(1, 1_000, esr_ohm=0.1),
        _row(2, 2_000, esr_ohm=0.2),
        _row(3, 3_000, esr_ohm=0.3),
    ])
    rows = service.load_rows()
    assert [r["measurement"].id for r in rows] == [1, 2, 3]


def test_esr_series_geeft_verwachte_punten() -> None:
    service = _make_service([
        _row(1, 1_000, esr_ohm=0.1),
        _row(2, 2_000, esr_ohm=0.2),
    ])
    points = service.esr_series()
    assert isinstance(points[0], TimeSeriesPoint)
    assert points[0].measurement_id == 1
    assert points[1].measurement_id == 2


def test_scatter_geeft_verwachte_punten() -> None:
    service = _make_service([
        _row(1, 1_000, esr_ohm=0.1, capacitance_f=470e-6),
        _row(2, 2_000, esr_ohm=0.2, capacitance_f=480e-6),
    ])
    points = service.scatter_esr_vs_capacitance()
    assert all(isinstance(p, ScatterPoint) for p in points)
    assert [p.measurement_id for p in points] == [1, 2]


def test_aggregation_dag_groepeert_per_dag() -> None:
    service = _make_service([
        _row(1, 1_700_000_000_000, esr_ohm=0.1),
        _row(2, 1_700_001_000_000, esr_ohm=0.2),
    ])
    points = service.esr_series(aggregation="day")
    assert len(points) >= 1


# ============================================================================
# v1.1.0 — measurement_ids-filter (fase 11G.5)
# ============================================================================

def test_load_rows_filtert_op_measurement_ids() -> None:
    """Alleen de opgegeven ids blijven over."""
    service = _make_service([
        _row(1, 1_000, esr_ohm=0.1),
        _row(2, 2_000, esr_ohm=0.2),
        _row(3, 3_000, esr_ohm=0.3),
    ])
    rows = service.load_rows(measurement_ids=[2])
    assert [r["measurement"].id for r in rows] == [2]


def test_load_rows_measurement_ids_none_geeft_alle_rijen() -> None:
    """None = geen filter (bestaand gedrag)."""
    service = _make_service([
        _row(1, 1_000, esr_ohm=0.1),
        _row(2, 2_000, esr_ohm=0.2),
    ])
    rows = service.load_rows(measurement_ids=None)
    assert [r["measurement"].id for r in rows] == [1, 2]


# ============================================================================
# v1.2.0 — vergelijken() (fase 5D)
# ============================================================================

def test_vergelijken_volgt_ids_volgorde() -> None:
    """De volgorde van de reeksen volgt de ids, niet de sortering van rijen."""
    service = _make_service([
        _row(1, 1_000, esr_ohm=0.1),
        _row(2, 2_000, esr_ohm=0.2),
        _row(3, 3_000, esr_ohm=0.3),
    ])
    reeksen = service.vergelijken([3, 1])
    assert all(isinstance(r, VergelijkReeks) for r in reeksen)
    assert [r.measurement_id for r in reeksen] == [3, 1]
    assert [r.color_index for r in reeksen] == [0, 1]


def test_vergelijken_te_veel_reeksen_faalt() -> None:
    """Bij meer dan max_reeksen: ValueError."""
    service = _make_service([_row(i, i * 1_000, esr_ohm=0.1) for i in range(1, 7)])
    with pytest.raises(ValueError, match="Te veel reeksen"):
        service.vergelijken([1, 2, 3, 4, 5, 6], max_reeksen=5)


def test_vergelijken_leeg_input_faalt() -> None:
    """Lege measurement_ids: ValueError."""
    service = _make_service([])
    with pytest.raises(ValueError, match="measurement_ids"):
        service.vergelijken([])


def test_vergelijken_lege_rijen_geeft_lege_reeksen() -> None:
    """Bij een lege service blijven de reeksen bestaan, maar zonder punten."""
    service = _make_service([])
    reeksen = service.vergelijken([1, 2])
    assert len(reeksen) == 2
    assert all(r.points == () for r in reeksen)