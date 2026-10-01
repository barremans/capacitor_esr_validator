"""
================================================================================
Module:     tests/test_storage_v1_completion.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Afrondende regressietests voor de oorspronkelijke Storage v1-definitie
            die ook onder latere schema-versies geldig moeten blijven.

            Bewijst volledige snapshot-roundtrips, behoud van ruwe meetcontext,
            historische append-mostly integriteit, RESTRICT-relaties en behoud
            van oudere assessment/reference snapshots naast nieuwere snapshots.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste afrondende Storage v1-regressietests.
  v1.1.0 (2026-10-01)  Schema-meta test volgt CURRENT_SCHEMA_VERSION in plaats
                       van schema-versie 1 hard te coderen.
================================================================================
"""

from pathlib import Path
import sqlite3

import pytest

from app.storage.database import open_database
from app.storage.schema import CURRENT_SCHEMA_VERSION
from app.storage.service import StorageService


NOW = 1_796_200_000_000


@pytest.fixture
def service(tmp_path: Path) -> StorageService:
    storage = StorageService(
        tmp_path / "measurements.sqlite3",
        clock=lambda: NOW,
    )
    storage.initialize()
    return storage


def _base_measurement(service: StorageService):
    model = service.create_component_model(
        manufacturer="Roundtrip Maker",
        series="RT",
        part_number="RT-220",
        technology="ALUMINUM_ELECTROLYTIC",
        nominal_capacitance_f=0.00022,
        nominal_capacitance_value=220,
        nominal_capacitance_unit="uF",
        rated_voltage_v=35,
        voltage_type="DC",
        tolerance_lower_pct=-20.0,
        tolerance_upper_pct=20.0,
        temperature_min_c=-40.0,
        temperature_max_c=105.0,
        case_size="10x20",
        notes="model-note",
    )
    sample = service.create_component_sample(
        component_model_id=model.id,
        sample_state="NEW",
        sample_code="RT-SAMPLE-1",
        source="BENCH",
        batch_lot_code="LOT-42",
        date_code="2626",
        visual_condition="OK",
        notes="sample-note",
    )
    session = service.create_measurement_session(
        component_sample_id=sample.id,
        started_at_ms=NOW + 10,
        ended_at_ms=NOW + 20,
        operator_name="Bart",
        customer="Customer",
        project="Project",
        installation="Installation",
        module_board="Board-A",
        component_reference="C17",
        notes="session-note",
    )
    measurement = service.create_measurement(
        measurement_session_id=session.id,
        measured_at_ms=NOW + 15,
        measurement_method="ONE_LEG",
        instrument_key="LCR-ST1",
        instrument_name="Smart Tweezer",
        instrument_profile_version="1.2.3",
        frequency_hz=10_000.0,
        test_voltage_vrms=0.6,
        temperature_c=22.75,
        power_off_confirmed=True,
        discharged_confirmed=True,
        residual_voltage_before_v=0.0123456789,
        residual_voltage_after_v=0.00123456789,
        capacitance_f=0.00021987654321,
        esr_ohm=0.0876543210987,
        dissipation_factor_d=0.04321,
        quality_factor_q=23.142,
        impedance_z_ohm=0.123456789,
        reactance_x_ohm=-0.087654321,
        out_of_range=False,
        open_suspected=False,
        short_suspected=False,
        unstable_reading=True,
        parallel_components_notes="parallel-context",
        mechanical_condition_notes="mechanical-context",
        notes="measurement-note",
        record_status="ACTIVE",
        invalid_reason=None,
    )
    return model, sample, session, measurement


def test_full_raw_measurement_context_roundtrips_without_mutation(
    service: StorageService,
) -> None:
    _, _, _, measurement = _base_measurement(service)

    stored = service.get_measurement(measurement.id)

    assert stored == measurement
    assert stored.esr_ohm == 0.0876543210987
    assert stored.capacitance_f == 0.00021987654321
    assert stored.frequency_hz == 10_000.0
    assert stored.test_voltage_vrms == 0.6
    assert stored.temperature_c == 22.75
    assert stored.power_off_confirmed is True
    assert stored.discharged_confirmed is True
    assert stored.unstable_reading is True
    assert stored.parallel_components_notes == "parallel-context"
    assert stored.mechanical_condition_notes == "mechanical-context"


def test_assessment_snapshot_full_roundtrip_keeps_status_and_reliability_separate(
    service: StorageService,
) -> None:
    _, _, _, measurement = _base_measurement(service)
    snapshot = service.create_assessment_snapshot(
        measurement_id=measurement.id,
        assessed_at_ms=NOW + 30,
        engine_version="engine-2.4.0",
        capacitance_status="GOOD",
        capacitance_deviation_pct=-0.056,
        esr_status="SUSPECT",
        esr_factor=1.75,
        consistency_status="PLAUSIBLE",
        derived_esr_from_d_ohm=0.09123,
        reliability_level="MEDIUM",
        final_status="SUSPECT",
        reasons_json='["reason-a","reason-b"]',
        warnings_json='["warning-a"]',
        advice_json='["advice-a"]',
    )

    stored = service.get_assessment_snapshots_for_measurement(measurement.id)

    assert stored == [snapshot]
    assert stored[0].esr_status == "SUSPECT"
    assert stored[0].reliability_level == "MEDIUM"
    assert stored[0].final_status == "SUSPECT"
    assert stored[0].reasons_json == '["reason-a","reason-b"]'
    assert stored[0].warnings_json == '["warning-a"]'
    assert stored[0].advice_json == '["advice-a"]'


def test_reference_snapshot_full_roundtrip_preserves_source_and_conditions(
    service: StorageService,
) -> None:
    _, _, _, measurement = _base_measurement(service)
    assessment = service.create_assessment_snapshot(
        measurement_id=measurement.id,
        assessed_at_ms=NOW + 30,
        engine_version="engine-2.4.0",
    )
    reference = service.create_reference_snapshot(
        assessment_snapshot_id=assessment.id,
        reference_role="ESR_LIMIT",
        reference_level="MANUFACTURER_PART_NUMBER",
        reference_type="DATASHEET",
        manufacturer="Example Capacitors",
        series="XR",
        part_number="XR220M35",
        reference_value=0.095,
        reference_unit="ohm",
        frequency_hz=100_000.0,
        temperature_c=20.0,
        test_voltage_vrms=0.5,
        dc_bias_v=0.0,
        value_kind="MAXIMUM",
        source_name="Example XR datasheet",
        source_document="XR-series.pdf",
        source_version="rev-C",
        source_data_version="2026.10",
        source_entry_id="XR220M35-esr-100k",
        source_hash="sha256:example",
        snapshot_json='{"limit_kind":"MAXIMUM","frequency_hz":100000}',
    )

    stored = service.get_reference_snapshots_for_assessment(assessment.id)

    assert stored == [reference]
    assert stored[0].reference_level == "MANUFACTURER_PART_NUMBER"
    assert stored[0].value_kind == "MAXIMUM"
    assert stored[0].frequency_hz == 100_000.0
    assert stored[0].temperature_c == 20.0
    assert stored[0].test_voltage_vrms == 0.5
    assert stored[0].source_document == "XR-series.pdf"
    assert stored[0].source_data_version == "2026.10"
    assert stored[0].snapshot_json == '{"limit_kind":"MAXIMUM","frequency_hz":100000}'


def test_new_assessment_does_not_overwrite_older_snapshot_or_references(
    service: StorageService,
) -> None:
    _, _, _, measurement = _base_measurement(service)
    first = service.create_assessment_snapshot(
        measurement_id=measurement.id,
        assessed_at_ms=NOW + 30,
        engine_version="engine-1",
        final_status="GOOD",
        reliability_level="HIGH",
    )
    first_ref = service.create_reference_snapshot(
        assessment_snapshot_id=first.id,
        reference_role="ESR_LIMIT",
        reference_level="GENERAL_TABLE",
        value_kind="SCREENING",
        reference_value=0.2,
        reference_unit="ohm",
        source_name="reference-pack-v1",
    )
    second = service.create_assessment_snapshot(
        measurement_id=measurement.id,
        assessed_at_ms=NOW + 40,
        engine_version="engine-2",
        final_status="SUSPECT",
        reliability_level="MEDIUM",
    )
    second_ref = service.create_reference_snapshot(
        assessment_snapshot_id=second.id,
        reference_role="ESR_LIMIT",
        reference_level="MANUFACTURER_PART_NUMBER",
        value_kind="MAXIMUM",
        reference_value=0.1,
        reference_unit="ohm",
        source_name="datasheet-v2",
    )

    detail = service.get_measurement_detail(measurement.id)

    assert detail["assessment_snapshots"] == [second, first]
    assert detail["reference_snapshots_by_assessment_id"][first.id] == [first_ref]
    assert detail["reference_snapshots_by_assessment_id"][second.id] == [second_ref]


def test_historical_parent_records_are_restrict_protected(service: StorageService) -> None:
    model, sample, session, measurement = _base_measurement(service)
    assessment = service.create_assessment_snapshot(
        measurement_id=measurement.id,
        assessed_at_ms=NOW + 30,
    )
    service.create_reference_snapshot(
        assessment_snapshot_id=assessment.id,
        reference_role="ESR_LIMIT",
    )

    connection = open_database(service.database_path)
    try:
        for table, record_id in (
            ("component_models", model.id),
            ("component_samples", sample.id),
            ("measurement_sessions", session.id),
            ("measurements", measurement.id),
            ("assessment_snapshots", assessment.id),
        ):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
            connection.rollback()
    finally:
        connection.close()


def test_schema_meta_remains_single_row_after_repeated_initialize(
    service: StorageService,
) -> None:
    service.initialize()
    service.initialize()

    connection = open_database(service.database_path)
    try:
        rows = connection.execute(
            "SELECT schema_version, created_at_ms, last_migrated_at_ms FROM schema_meta"
        ).fetchall()
    finally:
        connection.close()

    assert len(rows) == 1
    assert rows[0][0] == CURRENT_SCHEMA_VERSION
    assert rows[0][1] == NOW
    assert rows[0][2] == NOW


def test_storage_package_has_no_gui_or_assessment_imports() -> None:
    storage_dir = Path(__file__).resolve().parents[1] / "app" / "storage"

    for path in storage_dir.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "app.gui" not in source
        assert "app.services.assessment" not in source
        assert "assessment_service" not in source
