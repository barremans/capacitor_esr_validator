"""
================================================================================
Module:     app/helpers/analysis_series.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.1
Datum:      2026-10-09
Auteur:     Bart Bossuyt

Doel:       Pure, GUI- en storage-onafhankelijke functies voor het bouwen van
            tijdreeksen, scatterpunten en aggregaties op basis van reeds
            gelezen historiekrijen.

            Deze module schrijft nooit, kent geen database en importeert geen
            Qt. Ze accepteert dezelfde rij-dicts als
            StorageService.list_measurements() teruggeeft, en levert
            immutable dataclasses op zodat de GUI ze alleen nog hoeft te
            tekenen.

Wijzigingen:
  v1.0.0 (2026-10-09)  Eerste versie: TimeSeriesPoint, ScatterPoint,
                        reeksopbouw voor ESR/C/D, scatter ESR-vs-C,
                        aggregatie per dag/week/maand.
  v1.0.1 (2026-10-09)  Fix: aggregate_time_series() valideert de aggregatie
                        nu vóór de lege-input-return, zodat een onbekende
                        waarde ook bij een lege reeks ValueError oplevert.
                        _bucket_start_ms() behoudt zijn eigen raise als
                        verdediging in de diepte.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Literal


Aggregation = Literal["raw", "day", "week", "month"]

_VALID_AGGREGATIONS: frozenset[str] = frozenset(
    {"raw", "day", "week", "month"}
)


@dataclass(frozen=True, slots=True)
class TimeSeriesPoint:
    """Eén punt in een tijdreeks."""

    x_ms: int
    y: float
    measurement_id: int
    tool_key: str


@dataclass(frozen=True, slots=True)
class ScatterPoint:
    """Eén punt in een scattergrafiek, met optionele categorie voor kleur."""

    x: float
    y: float
    measurement_id: int
    tool_key: str
    category: str | None


# ---------------------------------------------------------------------------
# Rij-extractie
# ---------------------------------------------------------------------------

def _measurement(row: dict[str, Any]) -> Any:
    return row["measurement"]


def _tool_key(row: dict[str, Any]) -> str:
    return str(getattr(_measurement(row), "tool_key", "") or "")


def _measured_at_ms(row: dict[str, Any]) -> int | None:
    value = getattr(_measurement(row), "measured_at_ms", None)
    return int(value) if value is not None else None


def _measurement_id(row: dict[str, Any]) -> int:
    return int(_measurement(row).id)


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Tijdreeksen
# ---------------------------------------------------------------------------

def build_time_series(
    rows: Iterable[dict[str, Any]],
    *,
    value_key: str,
    tool_key: str = "ESR_CAPACITOR",
) -> list[TimeSeriesPoint]:
    """Bouw een tijdreeks van één meetwaarde.

    Rijen zonder tijdstip of zonder die meetwaarde worden overgeslagen.
    De volgorde is oplopend in tijd (oud → nieuw), zodat een grafiek
    direct van links naar rechts kan tekenen.
    """
    points: list[TimeSeriesPoint] = []
    for row in rows:
        if _tool_key(row) != tool_key:
            continue
        x_ms = _measured_at_ms(row)
        if x_ms is None:
            continue
        y = _as_float(getattr(_measurement(row), value_key, None))
        if y is None:
            continue
        points.append(
            TimeSeriesPoint(
                x_ms=x_ms,
                y=y,
                measurement_id=_measurement_id(row),
                tool_key=tool_key,
            )
        )
    points.sort(key=lambda p: (p.x_ms, p.measurement_id))
    return points


def build_esr_series(rows: Iterable[dict[str, Any]]) -> list[TimeSeriesPoint]:
    """ESR (Ω) over tijd voor ESR_CAPACITOR-metingen."""
    return build_time_series(rows, value_key="esr_ohm")


def build_capacitance_series(rows: Iterable[dict[str, Any]]) -> list[TimeSeriesPoint]:
    """Capaciteit (F) over tijd voor ESR_CAPACITOR-metingen."""
    return build_time_series(rows, value_key="capacitance_f")


def build_dissipation_series(rows: Iterable[dict[str, Any]]) -> list[TimeSeriesPoint]:
    """Dissipatiefactor D over tijd voor ESR_CAPACITOR-metingen."""
    return build_time_series(rows, value_key="dissipation_factor_d")


# ---------------------------------------------------------------------------
# Scatter
# ---------------------------------------------------------------------------

def build_scatter_esr_vs_capacitance(
    rows: Iterable[dict[str, Any]],
    *,
    tool_key: str = "ESR_CAPACITOR",
) -> list[ScatterPoint]:
    """Scatterpunten ESR (y) versus capaciteit (x), gekleurd per eindstatus."""
    points: list[ScatterPoint] = []
    for row in rows:
        if _tool_key(row) != tool_key:
            continue
        measurement = _measurement(row)
        x = _as_float(getattr(measurement, "capacitance_f", None))
        y = _as_float(getattr(measurement, "esr_ohm", None))
        if x is None or y is None:
            continue
        category = row.get("final_status")
        points.append(
            ScatterPoint(
                x=x,
                y=y,
                measurement_id=int(measurement.id),
                tool_key=tool_key,
                category=str(category) if category else None,
            )
        )
    points.sort(key=lambda p: (p.x, p.y, p.measurement_id))
    return points


# ---------------------------------------------------------------------------
# Aggregatie
# ---------------------------------------------------------------------------

def _bucket_start_ms(x_ms: int, aggregation: Aggregation) -> int:
    """Start van de bucket in UTC, in epoch-ms."""
    dt = datetime.fromtimestamp(x_ms / 1000.0, tz=timezone.utc)
    if aggregation == "day":
        start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    elif aggregation == "week":
        # Maandag als start van de week (ISO). Eerst middernacht, dan
        # terug naar maandag van die week.
        midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        start = midnight - timedelta(days=midnight.weekday())
    elif aggregation == "month":
        start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        raise ValueError(f"Onbekende aggregatie: {aggregation!r}")
    return int(start.timestamp() * 1000)


def aggregate_time_series(
    points: Iterable[TimeSeriesPoint],
    aggregation: Aggregation,
) -> list[TimeSeriesPoint]:
    """Aggregeer een tijdreeks tot gemiddelden per dag/week/maand.

    - ``raw`` geeft de invoer ongewijzigd terug (als lijst, opnieuw gesorteerd).
    - Bij aggregatie wordt per bucket het rekenkundig gemiddelde van ``y``
      genomen. Het resulterende punt houdt de bucket-start als ``x_ms`` en
      de ``measurement_id`` van het laatste punt in de bucket, zodat de
      GUI kan terugvinden welke meting het dichtst bij het gemiddelde hoort.

    Een onbekende aggregatie geeft altijd ValueError, ook bij een lege reeks.
    """
    if aggregation not in _VALID_AGGREGATIONS:
        raise ValueError(f"Onbekende aggregatie: {aggregation!r}")

    if aggregation == "raw":
        return sorted(points, key=lambda p: (p.x_ms, p.measurement_id))

    buckets: dict[int, list[TimeSeriesPoint]] = {}
    for point in points:
        key = _bucket_start_ms(point.x_ms, aggregation)
        buckets.setdefault(key, []).append(point)

    result: list[TimeSeriesPoint] = []
    for bucket_start in sorted(buckets):
        group = buckets[bucket_start]
        group_sorted = sorted(group, key=lambda p: (p.x_ms, p.measurement_id))
        average = sum(p.y for p in group_sorted) / len(group_sorted)
        last = group_sorted[-1]
        result.append(
            TimeSeriesPoint(
                x_ms=bucket_start,
                y=average,
                measurement_id=last.measurement_id,
                tool_key=last.tool_key,
            )
        )
    return result