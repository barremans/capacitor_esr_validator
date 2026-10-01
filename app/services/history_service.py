"""
================================================================================
Module:     app/services/history_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Applicatielaag voor read-only meet-historiek.

            Verbindt PathService en StorageService zonder GUI-code. Een nog niet
            bestaande database wordt niet aangemaakt door enkel de historiek te
            openen; in dat geval wordt een lege lijst teruggegeven. Bestaande
            databases worden wel via StorageService.initialize() gevalideerd en
            indien nodig gemigreerd voordat de historiek wordt gelezen.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste read-only history service voor de compacte
                        historiekweergave.
  v1.1.0 (2026-10-01)  Read-only detailopvraag toegevoegd via
                        StorageService.get_measurement_detail().
================================================================================
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from app.storage import PathService, StorageService


class MeasurementHistoryService:
    """Read-only applicatieservice bovenop de storage-historiek-API."""

    def __init__(
        self,
        *,
        path_service_factory: Callable[[], PathService] = PathService,
        storage_service_factory: Callable[[object], StorageService] = StorageService,
    ) -> None:
        self._path_service_factory = path_service_factory
        self._storage_service_factory = storage_service_factory

    def list_measurements(
        self,
        filters: Mapping[str, Any] | None = None,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Lees historiek zonder een ontbrekende database aan te maken."""
        paths = self._path_service_factory()
        database_path = paths.database_path

        if not database_path.exists():
            return []

        storage = self._storage_service_factory(database_path)
        storage.initialize()
        return storage.list_measurements(filters, limit=limit, offset=offset)
    def get_measurement_detail(self, measurement_id: int) -> dict[str, Any] | None:
        """Lees één volledige opgeslagen meetketen zonder writes uit te voeren."""
        paths = self._path_service_factory()
        database_path = paths.database_path

        if not database_path.exists():
            return None

        storage = self._storage_service_factory(database_path)
        storage.initialize()
        return storage.get_measurement_detail(measurement_id)

