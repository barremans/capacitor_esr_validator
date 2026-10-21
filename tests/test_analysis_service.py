"""
================================================================================
Module:     tests/test_analysis_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-20
Auteur:     Bart Bossuyt

Doel:       Regressietests voor AnalysisService.

Wijzigingen:
  v1.0.0 (2026-10-09)  Eerste versie: ESR/C/D-reeksen, scatter,
                        aggregaties.
  v1.1.0 (2026-10-20)  Fase 11G.5: tests voor de optionele
                        measurement_ids-filter in load_rows en in de
                        reeksfuncties.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from app.helpers.analysis_series import (
    ScatterPoint,
    TimeSeriesPoint,
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