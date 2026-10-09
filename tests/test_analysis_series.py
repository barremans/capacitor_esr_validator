"""
================================================================================
Module:     tests/test_analysis_series.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-09
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de pure analyse-reeksfuncties.

Wijzigingen:
  v1.0.0 (2026-10-09)  Eerste tests: reeksopbouw ESR/C/D, scatter, sortering,
                        aggregatie per dag/week/maand, ontbrekende waarden.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from app.helpers.analysis_series import (
    ScatterPoint,
    TimeSeriesPoint,
    aggregate_time_series,
    build_capacitance_series,
    build_dissipation_series,
    build_esr_series,
    build_scatter_esr_vs_capacitance,
)


# ---------------------------------------------------------------------------
# Testhelpers
# ---------------------------------------------------------------------------

@dataclass
class _FakeMeasurement:
    id: int
    measured_at_ms: int
    tool_key: str = "ESR_CAPACITOR"
    esr_ohm: float | None = None
    capacitance_f: float | None = None
    dissipation_factor_d: float | None = None


def _row(
    *,
    measurement_id: int,
    measured_at_ms: int,
    esr_ohm: float | None = None,
    capacitance_f: float | None = None,
    dissipation_factor_d: float | None = None,
    final_status: str | None = None,
    tool_key: str = "ESR_CAPACITOR",
) -> dict:
    return {
        "measurement": _FakeMeasurement(
            id=measurement_id,
            measured_at_ms=measured_at_ms,
            tool_key=tool_key,
            esr_ohm=esr_ohm,
            capacitance_f=capacitance_f,
            dissipation_factor_d=dissipation_factor_d,
        ),
        "final_status": final_status,
    }


def _ms(year: int, month: int, day: int, hour: int = 12) -> int:
    return int(
        datetime(year, month, day, hour, tzinfo=timezone.utc).timestamp() * 1000
    )


# ---------------------------------------------------------------------------
# Tijdreeksen
# ---------------------------------------------------------------------------

def test_esr_series_skips_rows_without_esr() -> None:
    rows = [
        _row(measurement_id=1, measured_at_ms=_ms(2026, 10, 1), esr_ohm=0.1),
        _row(measurement_id=2, measured_at_ms=_ms(2026, 10, 2), esr_ohm=None),
        _row(measurement_id=3, measured_at_ms=_ms(2026, 10, 3), esr_ohm=0.3),
    ]
    series = build_esr_series(rows)
    assert [p.measurement_id for p in series] == [1, 3]
    assert [p.y for p in series] == [0.1, 0.3]


def test_esr_series_sorts_old_to_new() -> None:
    rows = [
        _row(measurement_id=1, measured_at_ms=_ms(2026, 10, 3), esr_ohm=0.3),
        _row(measurement_id=2, measured_at_ms=_ms(2026, 10, 1), esr_ohm=0.1),
        _row(measurement_id=3, measured_at_ms=_ms(2026, 10, 2), esr_ohm=0.2),
    ]
    series = build_esr_series(rows)
    assert [p.x_ms for p in series] == sorted(p.x_ms for p in series)
    assert [p.y for p in series] == [0.1, 0.2, 0.3]


def test_esr_series_ignores_other_tool_keys() -> None:
    rows = [
        _row(measurement_id=1, measured_at_ms=_ms(2026, 10, 1), esr_ohm=0.1),
        _row(
            measurement_id=2,
            measured_at_ms=_ms(2026, 10, 2),
            esr_ohm=9.9,
            tool_key="RESISTOR",
        ),
    ]
    series = build_esr_series(rows)
    assert [p.measurement_id for p in series] == [1]


def test_capacitance_and_dissipation_series_use_correct_field() -> None:
    rows = [
        _row(
            measurement_id=1,
            measured_at_ms=_ms(2026, 10, 1),
            capacitance_f=470e-6,
            dissipation_factor_d=0.12,
        ),
    ]
    c_series = build_capacitance_series(rows)
    d_series = build_dissipation_series(rows)
    assert c_series[0].y == pytest.approx(470e-6)
    assert d_series[0].y == pytest.approx(0.12)


def test_series_skips_rows_without_timestamp() -> None:
    rows = [
        _row(measurement_id=1, measured_at_ms=None, esr_ohm=0.1),  # type: ignore[arg-type]
        _row(measurement_id=2, measured_at_ms=_ms(2026, 10, 2), esr_ohm=0.2),
    ]
    series = build_esr_series(rows)
    assert [p.measurement_id for p in series] == [2]


# ---------------------------------------------------------------------------
# Scatter
# ---------------------------------------------------------------------------

def test_scatter_esr_vs_capacitance_pairs_values_and_keeps_category() -> None:
    rows = [
        _row(
            measurement_id=1,
            measured_at_ms=_ms(2026, 10, 1),
            capacitance_f=100e-6,
            esr_ohm=1.0,
            final_status="waarschijnlijk_goed",
        ),
        _row(
            measurement_id=2,
            measured_at_ms=_ms(2026, 10, 2),
            capacitance_f=100e-6,
            esr_ohm=None,  # geen ESR → overslaan
            final_status="twijfelachtig",
        ),
        _row(
            measurement_id=3,
            measured_at_ms=_ms(2026, 10, 3),
            capacitance_f=220e-6,
            esr_ohm=2.0,
            final_status=None,
        ),
    ]
    points = build_scatter_esr_vs_capacitance(rows)
    assert [p.measurement_id for p in points] == [1, 3]
    assert points[0].category == "waarschijnlijk_goed"
    assert points[1].category is None
    assert points[0].x == pytest.approx(100e-6)
    assert points[0].y == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Aggregatie
# ---------------------------------------------------------------------------

def _point(measurement_id: int, x_ms: int, y: float) -> TimeSeriesPoint:
    return TimeSeriesPoint(
        x_ms=x_ms, y=y, measurement_id=measurement_id, tool_key="ESR_CAPACITOR"
    )


def test_aggregate_raw_returns_sorted_copy() -> None:
    points = [
        _point(1, _ms(2026, 10, 3), 0.3),
        _point(2, _ms(2026, 10, 1), 0.1),
    ]
    result = aggregate_time_series(points, "raw")
    assert [p.x_ms for p in result] == sorted(p.x_ms for p in result)
    assert result is not points


def test_aggregate_by_day_averages_within_same_day() -> None:
    points = [
        _point(1, _ms(2026, 10, 1, hour=9), 0.10),
        _point(2, _ms(2026, 10, 1, hour=15), 0.30),
        _point(3, _ms(2026, 10, 2, hour=9), 0.50),
    ]
    result = aggregate_time_series(points, "day")
    assert len(result) == 2
    assert result[0].y == pytest.approx(0.20)
    assert result[1].y == pytest.approx(0.50)
    # Laatste meting in de bucket bepaalt measurement_id.
    assert result[0].measurement_id == 2


def test_aggregate_by_month_groups_across_days() -> None:
    points = [
        _point(1, _ms(2026, 9, 30), 0.10),
        _point(2, _ms(2026, 10, 1), 0.30),
        _point(3, _ms(2026, 10, 15), 0.50),
    ]
    result = aggregate_time_series(points, "month")
    assert len(result) == 2
    assert result[0].y == pytest.approx(0.10)
    assert result[1].y == pytest.approx(0.40)


def test_aggregate_by_week_uses_monday_as_start() -> None:
    # 2026-10-05 is een maandag, 2026-10-11 een zondag.
    monday = _ms(2026, 10, 5, hour=10)
    sunday = _ms(2026, 10, 11, hour=10)
    next_monday = _ms(2026, 10, 12, hour=10)
    points = [
        _point(1, monday, 0.10),
        _point(2, sunday, 0.30),
        _point(3, next_monday, 0.50),
    ]
    result = aggregate_time_series(points, "week")
    assert len(result) == 2
    assert result[0].y == pytest.approx(0.20)
    assert result[1].y == pytest.approx(0.50)


def test_aggregate_rejects_unknown_value() -> None:
    with pytest.raises(ValueError):
        aggregate_time_series([], "year")  # type: ignore[arg-type]


def test_aggregate_empty_input_returns_empty() -> None:
    assert aggregate_time_series([], "day") == []