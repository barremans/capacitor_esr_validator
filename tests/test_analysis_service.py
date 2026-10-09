"""
================================================================================
Module:     tests/test_analysis_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-09
Auteur:     Bart Bossuyt

Doel:       Regressietests voor AnalysisService.

            Bewijst dat de service read-only is: elke schrijfmethode op de
            onderliggende historiekservice laat de test falen. Bewijst ook
            paginering, filterdoorgifte en de drie reekssoorten.

Wijzigingen:
  v1.0.0 (2026-10-09)  Eerste tests.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest

from app.services.analysis_service import AnalysisService


# ---------------------------------------------------------------------------
# Stubs
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
    measurement_id: int,
    measured_at_ms: int,
    *,
    esr_ohm: float | None = None,
    capacitance_f: float | None = None,
    dissipation_factor_d: float | None = None,
    final_status: str | None = None,
) -> dict[str, Any]:
    return {
        "measurement": _FakeMeasurement(
            id=measurement_id,
            measured_at_ms=measured_at_ms,
            esr_ohm=esr_ohm,
            capacitance_f=capacitance_f,
            dissipation_factor_d=dissipation_factor_d,
        ),
        "final_status": final_status,
    }


def _ms(year: int, month: int, day: int) -> int:
    return int(datetime(year, month, day, 12, tzinfo=timezone.utc).timestamp() * 1000)


class _ReadOnlyHistoryStub:
    """Alleen-lezen stub die elke schrijfmethode hard laat falen."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows
        self.list_calls: list[tuple[Any, int, int]] = []

    def list_measurements(self, filters=None, *, limit=100, offset=0):
        self.list_calls.append((filters, limit, offset))
        return list(self._rows[offset : offset + limit])

    def __getattr__(self, name: str) -> Any:
        if name.startswith(("create_", "save_", "update_", "delete_")):
            def _fail(*_args, **_kwargs):
                raise AssertionError(
                    f"AnalysisService mag nooit {name}() aanroepen."
                )

            return _fail
        raise AttributeError(name)


# ---------------------------------------------------------------------------
# Read-only garantie
# ---------------------------------------------------------------------------

def test_analysis_service_never_calls_write_methods() -> None:
    history = _ReadOnlyHistoryStub(
        [_row(1, _ms(2026, 10, 1), esr_ohm=0.1)]
    )
    service = AnalysisService(history_service=history)
    # Roept alle publieke methoden aan; faalt als er ooit een schrijfmethode
    # wordt aangeroepen.
    service.esr_series()
    service.capacitance_series()
    service.dissipation_series()
    service.scatter_esr_vs_capacitance()


# ---------------------------------------------------------------------------
# Paginering
# ---------------------------------------------------------------------------

def test_load_rows_paginates_until_shorter_chunk() -> None:
    rows = [_row(i, _ms(2026, 10, 1)) for i in range(1, 8)]
    history = _ReadOnlyHistoryStub(rows)
    service = AnalysisService(history_service=history, page_size=3)

    loaded = service.load_rows()

    assert len(loaded) == 7
    # Drie pagina's: 3 + 3 + 1.
    assert [call[2] for call in history.list_calls] == [0, 3, 6]
    assert all(call[1] == 3 for call in history.list_calls)


def test_load_rows_passes_filters_through_unchanged() -> None:
    history = _ReadOnlyHistoryStub([])
    service = AnalysisService(history_service=history)
    filters = {"tool_key": "ESR_CAPACITOR", "manufacturer": "Panasonic"}
    service.load_rows(filters)
    assert history.list_calls[0][0] == filters


# ---------------------------------------------------------------------------
# Reeksen via de service
# ---------------------------------------------------------------------------

def test_esr_series_returns_sorted_points() -> None:
    history = _ReadOnlyHistoryStub(
        [
            _row(1, _ms(2026, 10, 3), esr_ohm=0.3),
            _row(2, _ms(2026, 10, 1), esr_ohm=0.1),
            _row(3, _ms(2026, 10, 2), esr_ohm=0.2),
        ]
    )
    service = AnalysisService(history_service=history)
    series = service.esr_series()
    assert [p.y for p in series] == [0.1, 0.2, 0.3]


def test_esr_series_honours_day_aggregation() -> None:
    history = _ReadOnlyHistoryStub(
        [
            _row(1, _ms(2026, 10, 1), esr_ohm=0.10),
            _row(2, _ms(2026, 10, 1), esr_ohm=0.30),
            _row(3, _ms(2026, 10, 2), esr_ohm=0.50),
        ]
    )
    service = AnalysisService(history_service=history)
    series = service.esr_series(aggregation="day")
    assert len(series) == 2
    assert series[0].y == pytest.approx(0.20)


def test_scatter_esr_vs_capacitance_via_service() -> None:
    history = _ReadOnlyHistoryStub(
        [
            _row(
                1,
                _ms(2026, 10, 1),
                capacitance_f=100e-6,
                esr_ohm=1.0,
                final_status="waarschijnlijk_goed",
            ),
            _row(2, _ms(2026, 10, 2), capacitance_f=220e-6, esr_ohm=2.0),
        ]
    )
    service = AnalysisService(history_service=history)
    points = service.scatter_esr_vs_capacitance()
    assert [p.measurement_id for p in points] == [1, 2]
    assert points[0].category == "waarschijnlijk_goed"


# ---------------------------------------------------------------------------
# Constructie
# ---------------------------------------------------------------------------

def test_constructor_rejects_both_sources() -> None:
    with pytest.raises(ValueError):
        AnalysisService(
            history_service=_ReadOnlyHistoryStub([]),
            history_service_factory=lambda: _ReadOnlyHistoryStub([]),
        )


def test_constructor_rejects_invalid_page_size() -> None:
    with pytest.raises(ValueError):
        AnalysisService(history_service=_ReadOnlyHistoryStub([]), page_size=0)