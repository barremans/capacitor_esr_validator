"""
================================================================================
Module:     tests/test_history_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de read-only applicatieservice voor historiek.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste tests: ontbrekende DB blijft afwezig en bestaande
                        DB wordt geïnitialiseerd/gelezen via StorageService.
  v1.1.0 (2026-10-01)  Detailopvraag delegeert read-only naar StorageService en
                        maakt geen ontbrekende database aan.
================================================================================
"""

from pathlib import Path

from app.services.history_service import MeasurementHistoryService


class _Paths:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path


class _StorageStub:
    def __init__(self, path: object) -> None:
        self.path = Path(path)
        self.initialize_calls = 0
        self.list_calls = []
        self.detail_calls = []

    def initialize(self) -> None:
        self.initialize_calls += 1

    def list_measurements(self, filters=None, *, limit=100, offset=0):
        self.list_calls.append((filters, limit, offset))
        return [{"ok": True}]

    def get_measurement_detail(self, measurement_id):
        self.detail_calls.append(measurement_id)
        return {"measurement_id": measurement_id}


def test_history_without_database_returns_empty_and_does_not_create_file(tmp_path: Path) -> None:
    database_path = tmp_path / "data" / "measurements.sqlite3"
    created = []

    def storage_factory(path: object):
        created.append(path)
        return _StorageStub(path)

    service = MeasurementHistoryService(
        path_service_factory=lambda: _Paths(database_path),
        storage_service_factory=storage_factory,
    )

    assert service.list_measurements() == []
    assert not database_path.exists()
    assert created == []


def test_history_existing_database_delegates_to_storage(tmp_path: Path) -> None:
    database_path = tmp_path / "measurements.sqlite3"
    database_path.write_bytes(b"existing")
    storage = _StorageStub(database_path)

    service = MeasurementHistoryService(
        path_service_factory=lambda: _Paths(database_path),
        storage_service_factory=lambda path: storage,
    )

    result = service.list_measurements(
        {"manufacturer": "AIC"},
        limit=25,
        offset=5,
    )

    assert result == [{"ok": True}]
    assert storage.initialize_calls == 1
    assert storage.list_calls == [({"manufacturer": "AIC"}, 25, 5)]


def test_detail_without_database_returns_none_and_does_not_create_file(tmp_path: Path) -> None:
    database_path = tmp_path / "data" / "measurements.sqlite3"
    created = []

    service = MeasurementHistoryService(
        path_service_factory=lambda: _Paths(database_path),
        storage_service_factory=lambda path: created.append(path),
    )

    assert service.get_measurement_detail(1) is None
    assert not database_path.exists()
    assert created == []


def test_detail_existing_database_delegates_to_storage(tmp_path: Path) -> None:
    database_path = tmp_path / "measurements.sqlite3"
    database_path.write_bytes(b"existing")
    storage = _StorageStub(database_path)
    service = MeasurementHistoryService(
        path_service_factory=lambda: _Paths(database_path),
        storage_service_factory=lambda path: storage,
    )

    assert service.get_measurement_detail(42) == {"measurement_id": 42}
    assert storage.initialize_calls == 1
    assert storage.detail_calls == [42]
