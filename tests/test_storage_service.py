"""
================================================================================
Module:     tests/test_storage_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Gerichte regressietests voor StorageService v1.

            Bewijst create/read voor de zeven hoofdtabellen, structurele
            validatie, raw-meetdata roundtrip, transactionele volledige save,
            rollback, snapshots, historiekfilters/sortering/paginatie en selectie
            van de nieuwste assessment-snapshot.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste StorageService-tests.
================================================================================
"""

from pathlib import Path
import sqlite3

import pytest

from app.storage.exceptions import (
    RelatedRecordNotFoundError,
    StorageValidationError,
)
from app.storage.models import MeasurementMethod, SampleState
from app.storage.service import StorageService


NOW = 1_796_100_000_000


@pytest.fixture
def service(tmp_path: Path) -> StorageService:
    storage = StorageService(
        tmp_path / "measurements.sqlite3",
        clock=lambda: NOW,
    )
    storage.initialize()
    return storage


def _create_basic_chain(
    service: StorageService,
    *,
    measured_at_ms: int = NOW + 100,
    esr_ohm: float | None = 0.123456789,
    final_status: str = "GOOD",
    reliability_level: str = "HIGH",
):
    model = service.create_component_model(
        manufacturer="Test Manufacturer",
        series="T-Series",
        part_number="T-100",
        technology="ALUMINUM_ELECTROLYTIC",
        nominal_capacitance_f=0.00022,
        nominal_capacitance_value=220,
        nominal_capacitance_unit="uF",
        rated_voltage_v=35,
    )
    sample = service.create_component_sample(
        component_model_id=model.id,
        sample_state=SampleState.NEW,
        sample_code="S-001",
    )
    session = service.create_measurement_session(
        component_sample_id=sample.id,
        started_at_ms=measured_at_ms - 10,
        operator_name="Tester",
    )
    measurement = service.create_measurement(
        measurement_session_id=session.id,
        measured_at_ms=measured_at_ms,
        measurement_method=MeasurementMethod.EX_SITU,
        instrument_key="LCR-ST1",
        frequency_hz=1000,
        test_voltage_vrms=0.6,
        temperature_c=21.5,
        capacitance_f=0.000219,
        esr_ohm=esr_ohm,
        dissipation_factor_d=0.1,
        out_of_range=esr_ohm is None,
    )
    assessment = service.create_assessment_snapshot(
        measurement_id=measurement.id,
        assessed_at_ms=measured_at_ms + 1,
        engine_version="test-engine-1",
        final_status=final_status,
        reliability_level=reliability_level,
    )
    reference = service.create_reference_snapshot(
        assessment_snapshot_id=assessment.id,
        reference_role="ESR_LIMIT",
        reference_level="MANUFACTURER_PART_NUMBER",
        reference_type="DATASHEET",
        reference_value=0.2,
        reference_unit="ohm",
        frequency_hz=1000,
        value_kind="MAXIMUM",
        source_name="Test datasheet",
    )
    return model, sample, session, measurement, assessment, reference


def test_initialize_creates_database(service: StorageService) -> None:
    assert service.database_path.is_file()


def test_create_and_read_all_seven_main_entities(service: StorageService) -> None:
    model, sample, session, measurement, assessment, reference = _create_basic_chain(service)

    assert service.get_component_model(model.id) == model
    assert service.get_component_sample(sample.id) == sample
    assert service.get_measurement_session(session.id) == session
    assert service.get_measurement(measurement.id) == measurement
    assert service.get_assessment_snapshots_for_measurement(measurement.id) == [assessment]
    assert service.get_reference_snapshots_for_assessment(assessment.id) == [reference]


def test_raw_esr_roundtrips_exactly_without_hidden_correction(service: StorageService) -> None:
    raw_esr = 0.123456789012345
    *_, measurement, _, _ = _create_basic_chain(service, esr_ohm=raw_esr)

    stored = service.get_measurement(measurement.id)

    assert stored.esr_ohm == raw_esr
    assert stored.frequency_hz == 1000.0
    assert stored.test_voltage_vrms == 0.6


def test_out_of_range_allows_null_raw_measurement_values(service: StorageService) -> None:
    model = service.create_component_model()
    sample = service.create_component_sample(
        component_model_id=model.id,
        sample_state="NEW",
    )
    session = service.create_measurement_session(
        component_sample_id=sample.id,
        started_at_ms=NOW,
    )

    measurement = service.create_measurement(
        measurement_session_id=session.id,
        measured_at_ms=NOW + 1,
        measurement_method="EX_SITU",
        capacitance_f=None,
        esr_ohm=None,
        out_of_range=True,
    )

    assert measurement.capacitance_f is None
    assert measurement.esr_ohm is None
    assert measurement.out_of_range is True


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("frequency_hz", 0),
        ("frequency_hz", -1),
        ("frequency_hz", float("nan")),
        ("esr_ohm", -0.1),
        ("esr_ohm", float("inf")),
        ("capacitance_f", float("-inf")),
    ],
)
def test_measurement_rejects_structurally_invalid_numeric_values(
    service: StorageService,
    field: str,
    value: float,
) -> None:
    model = service.create_component_model()
    sample = service.create_component_sample(
        component_model_id=model.id,
        sample_state="NEW",
    )
    session = service.create_measurement_session(
        component_sample_id=sample.id,
        started_at_ms=NOW,
    )
    kwargs = {
        "measurement_session_id": session.id,
        "measured_at_ms": NOW + 1,
        "measurement_method": "EX_SITU",
        field: value,
    }

    with pytest.raises(StorageValidationError):
        service.create_measurement(**kwargs)


def test_invalid_enum_values_are_rejected(service: StorageService) -> None:
    model = service.create_component_model()

    with pytest.raises(StorageValidationError):
        service.create_component_sample(
            component_model_id=model.id,
            sample_state="NOT_A_STATE",
        )

    sample = service.create_component_sample(
        component_model_id=model.id,
        sample_state="NEW",
    )
    session = service.create_measurement_session(
        component_sample_id=sample.id,
        started_at_ms=NOW,
    )

    with pytest.raises(StorageValidationError):
        service.create_measurement(
            measurement_session_id=session.id,
            measured_at_ms=NOW + 1,
            measurement_method="NOT_A_METHOD",
        )


def test_missing_parent_record_raises_related_record_error(service: StorageService) -> None:
    with pytest.raises(RelatedRecordNotFoundError):
        service.create_component_sample(
            component_model_id=999999,
            sample_state="NEW",
        )


def test_save_new_measurement_chain_commits_all_records(service: StorageService) -> None:
    result = service.save_new_measurement_chain(
        component_model={
            "manufacturer": "Chain Maker",
            "series": "C1",
            "part_number": "P1",
            "nominal_capacitance_f": 0.001,
        },
        component_sample={
            "sample_state": "NEW",
            "sample_code": "CHAIN-1",
        },
        measurement_session={
            "started_at_ms": NOW,
            "operator_name": "Bart",
        },
        measurement={
            "measured_at_ms": NOW + 10,
            "measurement_method": "EX_SITU",
            "frequency_hz": 1000,
            "capacitance_f": 0.001001,
            "esr_ohm": 0.08,
        },
        assessment_snapshot={
            "assessed_at_ms": NOW + 11,
            "engine_version": "1.0",
            "final_status": "GOOD",
            "reliability_level": "HIGH",
        },
        reference_snapshots=[
            {
                "reference_role": "ESR",
                "reference_level": "MANUFACTURER_PART_NUMBER",
                "reference_value": 0.1,
                "reference_unit": "ohm",
                "frequency_hz": 1000,
                "value_kind": "MAXIMUM",
            },
            {
                "reference_role": "CAPACITANCE",
                "reference_level": "MANUFACTURER_PART_NUMBER",
                "reference_value": 0.001,
                "reference_unit": "F",
                "value_kind": "TYPICAL",
            },
        ],
    )

    assert result["component_sample"].component_model_id == result["component_model"].id
    assert result["measurement_session"].component_sample_id == result["component_sample"].id
    assert result["measurement"].measurement_session_id == result["measurement_session"].id
    assert result["assessment_snapshot"].measurement_id == result["measurement"].id
    assert len(result["reference_snapshots"]) == 2
    assert all(
        ref.assessment_snapshot_id == result["assessment_snapshot"].id
        for ref in result["reference_snapshots"]
    )


def test_save_new_measurement_chain_rolls_back_everything_on_mid_chain_failure(
    service: StorageService,
) -> None:
    with pytest.raises(RelatedRecordNotFoundError):
        service.save_new_measurement_chain(
            component_model={"manufacturer": "Rollback Maker"},
            component_sample={"sample_state": "NEW"},
            measurement_session={"started_at_ms": NOW},
            measurement={
                "measured_at_ms": NOW + 1,
                "measurement_method": "EX_SITU",
                "supersedes_measurement_id": 999999,
            },
            assessment_snapshot={"assessed_at_ms": NOW + 2},
        )

    connection = sqlite3.connect(service.database_path)
    try:
        for table in (
            "component_models",
            "component_samples",
            "measurement_sessions",
            "measurements",
            "assessment_snapshots",
            "reference_snapshots",
        ):
            count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            assert count == 0
    finally:
        connection.close()


def test_assessment_history_is_newest_first(service: StorageService) -> None:
    *_, measurement, first, _ = _create_basic_chain(service)
    second = service.create_assessment_snapshot(
        measurement_id=measurement.id,
        assessed_at_ms=first.assessed_at_ms + 100,
        final_status="SUSPECT",
        reliability_level="HIGH",
    )

    assessments = service.get_assessment_snapshots_for_measurement(measurement.id)

    assert assessments == [second, first]


def test_get_measurement_detail_returns_complete_historical_chain(service: StorageService) -> None:
    model, sample, session, measurement, assessment, reference = _create_basic_chain(service)

    detail = service.get_measurement_detail(measurement.id)

    assert detail["component_model"] == model
    assert detail["component_sample"] == sample
    assert detail["measurement_session"] == session
    assert detail["measurement"] == measurement
    assert detail["assessment_snapshots"] == [assessment]
    assert detail["reference_snapshots_by_assessment_id"] == {
        assessment.id: [reference]
    }


def test_list_measurements_sorts_newest_first_and_supports_limit_offset(
    service: StorageService,
) -> None:
    first = _create_basic_chain(service, measured_at_ms=NOW + 10)[3]
    second = _create_basic_chain(service, measured_at_ms=NOW + 20)[3]
    third = _create_basic_chain(service, measured_at_ms=NOW + 30)[3]

    page = service.list_measurements(limit=2, offset=1)

    assert [item["measurement"].id for item in page] == [second.id, first.id]
    assert third.id not in [item["measurement"].id for item in page]


def test_list_measurements_supports_approved_filters(service: StorageService) -> None:
    wanted = _create_basic_chain(
        service,
        measured_at_ms=NOW + 100,
        final_status="GOOD",
        reliability_level="HIGH",
    )[3]
    _create_basic_chain(
        service,
        measured_at_ms=NOW + 200,
        final_status="SUSPECT",
        reliability_level="MEDIUM",
    )

    rows = service.list_measurements(
        {
            "manufacturer": "Test Manufacturer",
            "series": "T-Series",
            "part_number": "T-100",
            "sample_state": "NEW",
            "measurement_method": "EX_SITU",
            "instrument_key": "LCR-ST1",
            "frequency_hz": 1000,
            "test_voltage_vrms": 0.6,
            "final_status": "GOOD",
            "reliability_level": "HIGH",
            "measured_from_ms": NOW,
            "measured_to_ms": NOW + 150,
        }
    )

    assert [row["measurement"].id for row in rows] == [wanted.id]


def test_list_measurements_uses_latest_assessment_snapshot(service: StorageService) -> None:
    *_, measurement, old_assessment, _ = _create_basic_chain(
        service,
        final_status="OLD",
        reliability_level="LOW",
    )
    new_assessment = service.create_assessment_snapshot(
        measurement_id=measurement.id,
        assessed_at_ms=old_assessment.assessed_at_ms + 100,
        final_status="NEW",
        reliability_level="HIGH",
    )

    rows = service.list_measurements()

    assert len(rows) == 1
    assert rows[0]["latest_assessment_id"] == new_assessment.id
    assert rows[0]["final_status"] == "NEW"
    assert rows[0]["reliability_level"] == "HIGH"


def test_list_measurements_allows_measurement_without_assessment(service: StorageService) -> None:
    model = service.create_component_model(manufacturer="No Assessment")
    sample = service.create_component_sample(
        component_model_id=model.id,
        sample_state="UNKNOWN",
    )
    session = service.create_measurement_session(
        component_sample_id=sample.id,
        started_at_ms=NOW,
    )
    measurement = service.create_measurement(
        measurement_session_id=session.id,
        measured_at_ms=NOW + 1,
        measurement_method="IN_CIRCUIT",
    )

    rows = service.list_measurements()

    assert rows[0]["measurement"].id == measurement.id
    assert rows[0]["latest_assessment_id"] is None
    assert rows[0]["final_status"] is None


def test_list_measurements_rejects_unknown_filter(service: StorageService) -> None:
    with pytest.raises(StorageValidationError):
        service.list_measurements({"unknown_filter": "x"})


def test_public_service_exposes_no_measurement_update_or_delete_api() -> None:
    assert not hasattr(StorageService, "update_measurement")
    assert not hasattr(StorageService, "delete_measurement")
    assert not hasattr(StorageService, "delete_session")
    assert not hasattr(StorageService, "delete_sample")
    assert not hasattr(StorageService, "delete_model")
