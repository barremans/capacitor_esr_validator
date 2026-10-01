"""
================================================================================
Module:     tests/test_measurement_persistence_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Gerichte regressietests voor de koppeling van een reeds beoordeelde
            ESR-meetflow naar StorageService.

Wijzigingen:
  v1.0.0 (2026-10-01)  Test transactionele mapping, NULL bij lege OL-waarden,
                        snapshotvelden en lazy database-initialisatie.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import pytest

from app.services.measurement_persistence_service import (
    EsrMeasurementSaveData,
    MeasurementPersistenceService,
)
from app.storage.service import StorageService


@dataclass(frozen=True)
class _Status:
    value: str


@dataclass(frozen=True)
class _Cap:
    status: _Status
    afwijking_percent: float | None


@dataclass(frozen=True)
class _Esr:
    status: _Status
    factor: float | None


@dataclass(frozen=True)
class _Cons:
    status: _Status
    esr_verwacht_ohm: float | None


@dataclass(frozen=True)
class _Reliability:
    niveau: _Status


@dataclass(frozen=True)
class _Assessment:
    capaciteit: _Cap
    esr: _Esr
    consistentie: _Cons
    betrouwbaarheid: _Reliability
    eindstatus: _Status
    redenen: tuple[str, ...]
    waarschuwingen: tuple[str, ...]
    aanbevolen_vervolgstap: str


@dataclass(frozen=True)
class _Reference:
    esr_waarde: float
    eenheid: str
    bron: str
    referentieniveau: int
    frequentie_hz: float
    typisch_of_maximaal: str
    temperatuur_c: float | None = None
    condensatortype: str | None = None
    fabrikant: str | None = None
    serie: str | None = None


class _Paths:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.database_path = root / "data" / "measurements.sqlite3"
        self.ensure_called = False

    def ensure_runtime_directories(self) -> None:
        self.ensure_called = True
        (self.root / "data").mkdir(parents=True, exist_ok=True)


def _assessment() -> _Assessment:
    return _Assessment(
        capaciteit=_Cap(_Status("binnen_tolerantie"), -1.25),
        esr=_Esr(_Status("waarschijnlijk_normaal"), 1.1),
        consistentie=_Cons(_Status("consistent"), 0.12),
        betrouwbaarheid=_Reliability(_Status("middel")),
        eindstatus=_Status("waarschijnlijk_goed"),
        redenen=("reden 1",),
        waarschuwingen=("waarschuwing 1",),
        aanbevolen_vervolgstap="Geen actie.",
    )


def _data(**overrides):
    values = dict(
        nominal_capacitance_value=470.0,
        nominal_capacitance_unit="µF",
        tolerance_percent=20.0,
        rated_voltage_v=25.0,
        technology="Aluminium elektrolytisch",
        manufacturer="TestCo",
        series="A1",
        measurement_method="EX_SITU",
        instrument_key="LCR-ST1",
        instrument_name="LCR-ST1 Smart Tweezer",
        frequency_hz=1000.0,
        test_voltage_vrms=0.6,
        temperature_c=20.0,
        safety_confirmed=True,
        measured_capacitance_value=465.0,
        measured_capacitance_unit="µF",
        measured_esr_value=120.0,
        measured_esr_unit="mΩ",
        dissipation_factor_d=0.35,
        out_of_range=False,
        open_suspected=False,
        assessment=_assessment(),
        reference=_Reference(
            esr_waarde=0.11,
            eenheid="Ω",
            bron="test-reference",
            referentieniveau=5,
            frequentie_hz=100000.0,
            typisch_of_maximaal="typisch",
            temperatuur_c=20.0,
            condensatortype="Aluminium elektrolytisch",
        ),
    )
    values.update(overrides)
    return EsrMeasurementSaveData(**values)


def test_save_creates_database_only_when_save_is_called(tmp_path: Path) -> None:
    paths = _Paths(tmp_path / "runtime")
    service = MeasurementPersistenceService(
        path_service_factory=lambda: paths,
        clock=lambda: 1_800_000_000_123,
    )

    assert not paths.database_path.exists()

    saved = service.save_esr_measurement(_data())

    assert paths.ensure_called is True
    assert paths.database_path.exists()
    assert saved["measurement"].id > 0


def test_save_roundtrips_normalized_raw_values_and_snapshots(tmp_path: Path) -> None:
    paths = _Paths(tmp_path / "runtime")
    service = MeasurementPersistenceService(
        path_service_factory=lambda: paths,
        clock=lambda: 1_800_000_000_123,
    )

    saved = service.save_esr_measurement(_data())

    storage = StorageService(paths.database_path, clock=lambda: 1_800_000_000_123)
    detail = storage.get_measurement_detail(saved["measurement"].id)

    model = detail["component_model"]
    measurement = detail["measurement"]
    assessment = detail["assessment_snapshots"][0]
    references = detail["reference_snapshots_by_assessment_id"][assessment.id]

    assert model.nominal_capacitance_value == 470.0
    assert model.nominal_capacitance_unit == "µF"
    assert model.nominal_capacitance_f == pytest.approx(470e-6)
    assert model.tolerance_lower_pct == -20.0
    assert model.tolerance_upper_pct == 20.0

    assert measurement.capacitance_f == pytest.approx(465e-6)
    assert measurement.esr_ohm == pytest.approx(0.12)
    assert measurement.frequency_hz == 1000.0
    assert measurement.test_voltage_vrms == 0.6

    assert assessment.engine_version == "1.3.0"
    assert assessment.final_status == "waarschijnlijk_goed"
    assert json.loads(assessment.reasons_json) == ["reden 1"]
    assert json.loads(assessment.warnings_json) == ["waarschuwing 1"]
    assert json.loads(assessment.advice_json) == ["Geen actie."]

    assert len(references) == 1
    reference = references[0]
    assert reference.reference_value == 0.11
    assert reference.reference_unit == "Ω"
    assert reference.frequency_hz == 100000.0
    assert reference.value_kind == "TYPICAL"
    assert reference.source_name == "test-reference"


def test_blank_out_of_range_values_are_saved_as_null_not_zero(tmp_path: Path) -> None:
    paths = _Paths(tmp_path / "runtime")
    service = MeasurementPersistenceService(
        path_service_factory=lambda: paths,
        clock=lambda: 1_800_000_000_123,
    )

    saved = service.save_esr_measurement(
        _data(
            measured_capacitance_value=None,
            measured_esr_value=None,
            out_of_range=True,
            reference=None,
        )
    )

    storage = StorageService(paths.database_path, clock=lambda: 1_800_000_000_123)
    measurement = storage.get_measurement(saved["measurement"].id)

    assert measurement.out_of_range is True
    assert measurement.capacitance_f is None
    assert measurement.esr_ohm is None
    assert saved["reference_snapshots"] == ()


def test_reference_maximum_keeps_distinct_value_kind(tmp_path: Path) -> None:
    paths = _Paths(tmp_path / "runtime")
    service = MeasurementPersistenceService(
        path_service_factory=lambda: paths,
        clock=lambda: 1_800_000_000_123,
    )
    reference = _Reference(
        esr_waarde=0.2,
        eenheid="Ω",
        bron="datasheet",
        referentieniveau=2,
        frequentie_hz=100000.0,
        typisch_of_maximaal="maximaal",
    )

    saved = service.save_esr_measurement(_data(reference=reference))
    stored = saved["reference_snapshots"][0]

    assert stored.value_kind == "MAXIMUM"
    assert stored.reference_value == 0.2
