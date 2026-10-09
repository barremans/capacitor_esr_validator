"""
================================================================================
Module:     app/services/analysis_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-09
Auteur:     Bart Bossuyt

Doel:       Read-only applicatieservice voor grafieken en trends.

            Leest historiek via MeasurementHistoryService en zet de rijen om
            naar reeksen en aggregaties via app/helpers/analysis_series.py.
            De service schrijft nooit, kent geen Qt en wijzigt geen
            historische metingen of beoordelingen.

Wijzigingen:
  v1.0.0 (2026-10-09)  Eerste versie: ESR-, C- en D-tijdreeksen, scatter
                        ESR-vs-C, aggregaties per dag/week/maand.
================================================================================
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from app.helpers.analysis_series import (
    Aggregation,
    ScatterPoint,
    TimeSeriesPoint,
    aggregate_time_series,
    build_capacitance_series,
    build_dissipation_series,
    build_esr_series,
    build_scatter_esr_vs_capacitance,
)
from app.services.history_service import MeasurementHistoryService


class AnalysisService:
    """Read-only analyse-laag bovenop de bestaande historiekservice."""

    def __init__(
        self,
        *,
        history_service: MeasurementHistoryService | None = None,
        history_service_factory: Callable[[], MeasurementHistoryService] | None = None,
        page_size: int = 500,
    ) -> None:
        if history_service is not None and history_service_factory is not None:
            raise ValueError(
                "Geef ofwel history_service, ofwel history_service_factory, niet beide."
            )
        self._history_service = history_service
        self._history_service_factory = history_service_factory
        self._page_size = int(page_size)
        if self._page_size < 1:
            raise ValueError("page_size moet een positief geheel getal zijn.")

    def _history(self) -> MeasurementHistoryService:
        if self._history_service is not None:
            return self._history_service
        if self._history_service_factory is not None:
            return self._history_service_factory()
        return MeasurementHistoryService()

    # ------------------------------------------------------------------
    # Interne read
    # ------------------------------------------------------------------

    def load_rows(
        self,
        filters: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Lees alle gefilterde historiekrijen, in pagina's, read-only."""
        history = self._history()
        rows: list[dict[str, Any]] = []
        offset = 0
        while True:
            chunk = history.list_measurements(
                filters,
                limit=self._page_size,
                offset=offset,
            )
            rows.extend(chunk)
            if len(chunk) < self._page_size:
                break
            offset += len(chunk)
        return rows

    # ------------------------------------------------------------------
    # Reeksen
    # ------------------------------------------------------------------

    def esr_series(
        self,
        filters: Mapping[str, Any] | None = None,
        *,
        aggregation: Aggregation = "raw",
    ) -> list[TimeSeriesPoint]:
        rows = self.load_rows(filters)
        return aggregate_time_series(build_esr_series(rows), aggregation)

    def capacitance_series(
        self,
        filters: Mapping[str, Any] | None = None,
        *,
        aggregation: Aggregation = "raw",
    ) -> list[TimeSeriesPoint]:
        rows = self.load_rows(filters)
        return aggregate_time_series(build_capacitance_series(rows), aggregation)

    def dissipation_series(
        self,
        filters: Mapping[str, Any] | None = None,
        *,
        aggregation: Aggregation = "raw",
    ) -> list[TimeSeriesPoint]:
        rows = self.load_rows(filters)
        return aggregate_time_series(build_dissipation_series(rows), aggregation)

    def scatter_esr_vs_capacitance(
        self,
        filters: Mapping[str, Any] | None = None,
    ) -> list[ScatterPoint]:
        rows = self.load_rows(filters)
        return build_scatter_esr_vs_capacitance(rows)