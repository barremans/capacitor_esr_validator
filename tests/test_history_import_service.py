"""
================================================================================
Module:     tests/test_history_import_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-27
Auteur:     Bart Bossuyt

Doel:       Regressietests voor HistoryImportService (C1): dedup op
            natural key, aanvullen, foutisolatie per keten.
================================================================================
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.helpers.history_import import parse_rijen
from app.helpers.history_detail_export import DETAIL_EXPORT_HEADERS
from app.services.history_import_service import HistoryImportService
from app.storage.service import StorageService


class _Paths:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path


def _basis_rij(**overrides):
    rij = {kolom: "" for kolom in DETAIL_EXPORT_HEADERS}
    rij.update(
        {
            "tool_key": "ESR_CAPACITOR",
            "measured_at_ms": "1700000000000",
            "measurement_method": "EX_SITU",
            "sample_state": "NEW",
            "manufacturer": "TEST",
            "series": "S1",
            "part_number": "P1",
            "esr_nominal_capacitance_f": "0.00047",
            "esr_nominal_capacitance_value": "470",
            "esr_nominal_capacitance_unit": "µF",
            "esr_rated_voltage_v": "25",
            "esr_voltage_type": "DC",
            "esr_measured_capacitance_f": "0.000465",
            "esr_measured_esr_ohm": "0.2",
            "frequency_hz": "1000",
            "test_voltage_vrms": "0.6",
            "temperature_c": "20",
            "out_of_range": "False",
            "open_suspected": "False",
            "short_suspected": "False",
            "unstable_reading": "False",
            "assessed_at_ms": "1700000100000",
            "assessment_engine_version": "1.0",
            "final_status": "GOOD",
            "reliability_level": "HIGH",
        }
    )
    rij.update(overrides)
    return rij


def _ketens(*rijen):
    kop = list(DETAIL_EXPORT_HEADERS)
    return parse_rijen(
        [kop] + [[rij.get(kolom, "") for kolom in kop] for rij in rijen]
    )


@pytest.fixture
def storage(tmp_path: Path) -> StorageService:
    service = StorageService(tmp_path / "measurements.sqlite3", clock=lambda: 1_700_000_000_000)
    service.initialize()
    return service


def _service(tmp_path: Path) -> HistoryImportService:
    return HistoryImportService(
        path_service_factory=lambda: _Paths(tmp_path / "measurements.sqlite3"),
    )


def test_import_adds_new_chains(tmp_path):
    storage_service = StorageService(
        tmp_path / "measurements.sqlite3", clock=lambda: 1_700_000_000_000
    )
    storage_service.initialize()
    service = _service(tmp_path)
    resultaat = _ketens(_basis_rij())

    uitkomst = service.importeer(resultaat.ketens)

    assert uitkomst.toegevoegd == 1
    assert uitkomst.overgeslagen == 0
    assert uitkomst.fouten == 0


def test_import_dedups_identical_chain(tmp_path):
    storage_service = StorageService(
        tmp_path / "measurements.sqlite3", clock=lambda: 1_700_000_000_000
    )
    storage_service.initialize()
    service = _service(tmp_path)
    resultaat = _ketens(_basis_rij())
    service.importeer(resultaat.ketens)

    uitkomst = service.importeer(resultaat.ketens)

    assert uitkomst.toegevoegd == 0
    assert uitkomst.overgeslagen == 1


def test_import_aanvullen_voegt_duplicate_toe(tmp_path):
    storage_service = StorageService(
        tmp_path / "measurements.sqlite3", clock=lambda: 1_700_000_000_000
    )
    storage_service.initialize()
    service = _service(tmp_path)
    resultaat = _ketens(_basis_rij())
    service.importeer(resultaat.ketens)

    uitkomst = service.importeer(resultaat.ketens, aanvullen=True)

    assert uitkomst.toegevoegd == 1
    assert uitkomst.overgeslagen == 0


def test_import_returns_error_when_database_missing(tmp_path):
    service = _service(tmp_path)

    uitkomst = service.importeer(())

    assert uitkomst.toegevoegd == 0
    assert uitkomst.fout_details