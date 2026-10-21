"""
================================================================================
Module:     app/services/analysis_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-20
Auteur:     Bart Bossuyt

Doel:       Read-only applicatieservice voor grafieken en trends.

            Leest historiek via MeasurementHistoryService en zet de rijen om
            naar reeksen en aggregaties via app/helpers/analysis_series.py.
            De service schrijft nooit, kent geen Qt en wijzigt geen
            historische metingen of beoordelingen.

Wijzigingen:
  v1.0.0 (2026-10-09)  Eerste versie: ESR-, C- en D-tijdreeksen, scatter
                        ESR-vs-C, aggregaties per dag/week/maand.
  v1.1.0 (2026-10-20)  Fase 11G.5: optionele measurement_ids-filter.
                        load_rows() en alle reeksfuncties accepteren nu
                        een keyword-only measurement_ids: list[int] | None.
                        None = geen filter (bestaand gedrag). De filter
                        wordt na het ophalen toegepast, zodat de
                        bestaande service-API per bron atomair blijft en
                        de paginering ongewijzigd werkt.
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
        *,
        measurement_ids: list[int] | None = None,
    ) -> list[dict[str, Any]]:
        """Lees alle gefilterde historiekrijen, in pagina's, read-only.

        ``measurement_ids`` (11G.5): als niet-None, blijven alleen rijen
        over waarvan ``measurement.id`` in de lijst staat. De filtering
        gebeurt na het ophalen, zodat de bestaande service-API per bron
        atomair blijft en de paginering ongewijzigd werkt. None = geen
        filter (bestaand gedrag).
        """
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

        if measurement_ids is None:
            return rows

        toegestaan = set(int(i) for i in measurement_ids)
        return [
            row
            for row in rows
            if int(getattr(row["measurement"], "id", -1)) in toegestaan
        ]

    # ------------------------------------------------------------------
    # Reeksen
    # ------------------------------------------------------------------

    def esr_series(
        self,
        filters: Mapping[str, Any] | None = None,
        *,
        aggregation: Aggregation = "raw",
        measurement_ids: list[int] | None = None,
    ) -> list[TimeSeriesPoint]:
        rows = self.load_rows(filters, measurement_ids=measurement_ids)
        return aggregate_time_series(build_esr_series(rows), aggregation)

    def capacitance_series(
        self,
        filters: Mapping[str, Any] | None = None,
        *,
        aggregation: Aggregation = "raw",
        measurement_ids: list[int] | None = None,
    ) -> list[TimeSeriesPoint]:
        rows = self.load_rows(filters, measurement_ids=measurement_ids)
        return aggregate_time_series(build_capacitance_series(rows), aggregation)

    def dissipation_series(
        self,
        filters: Mapping[str, Any] | None = None,
        *,
        aggregation: Aggregation = "raw",
        measurement_ids: list[int] | None = None,
    ) -> list[TimeSeriesPoint]:
        rows = self.load_rows(filters, measurement_ids=measurement_ids)
        return aggregate_time_series(build_dissipation_series(rows), aggregation)

    def scatter_esr_vs_capacitance(
        self,
        filters: Mapping[str, Any] | None = None,
        *,
        measurement_ids: list[int] | None = None,
    ) -> list[ScatterPoint]:
        rows = self.load_rows(filters, measurement_ids=measurement_ids)
        return build_scatter_esr_vs_capacitance(rows)