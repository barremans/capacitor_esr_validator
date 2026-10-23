"""
================================================================================
Module:     tests/test_storage_schema.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.2.0
Datum:      2026-10-23
Auteur:     Bart Bossuyt

Doel:       Gerichte regressietests voor storage models en SQLite schema.

            Bewijst de zeven hoofdtabellen, schema_meta-singleton,
            schema-versie/timestamps, indexes, RESTRICT-relaties,
            goedgekeurde enumwaarden en het ontbreken van verborgen
            gecorrigeerde ESR-velden.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste tests voor models.py en schema.py.
  v1.1.0 (2026-10-01)  Schema v2: tool_key.
  v1.2.0 (2026-10-23)  Fase 28E: schema v3. Nieuwe tests voor
                        source_machine_id, source_measurement_id en
                        ix_measurements_source_identity.
================================================================================
"""

from dataclasses import fields
import sqlite3

import pytest

from app.storage.models import (
    AssessmentSnapshot,
    ComponentModel,
    ComponentSample,
    Measurement,
    MeasurementMethod,
    MeasurementSession,
    ReferenceSnapshot,
    SampleState,
    SchemaMeta,
)
from app.storage.schema import (
    CURRENT_SCHEMA_VERSION,
    SCHEMA_V1_VERSION,
    SCHEMA_V1_INDEXES,
    SCHEMA_V1_TABLES,
    SCHEMA_CURRENT_INDEXES,
    create_schema_v1,
    create_schema_current,
)


TEST_NOW_MS = 1_796_000_000_123


def _open_memory_database() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _column_names(
    connection: sqlite3.Connection,
    table_name: str,
) -> tuple[str, ...]:
    rows = connection.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()
    return tuple(row[1] for row in rows)


def test_current_schema_version_is_three() -> None:
    assert CURRENT_SCHEMA_VERSION == 3


def test_schema_v1_creates_exact_main_tables() -> None:
    connection = _open_memory_database()

    create_schema_v1(
        connection,
        created_at_ms=TEST_NOW_MS,
    )

    tables = {
        row[0]
        for row in connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            """
        )
    }

    assert tables == set(SCHEMA_V1_TABLES)


def test_schema_columns_match_storage_models() -> None:
    connection = _open_memory_database()
    create_schema_current(
        connection,
        created_at_ms=TEST_NOW_MS,
    )

    expected_models = {
        "schema_meta": SchemaMeta,
        "component_models": ComponentModel,
        "component_samples": ComponentSample,
        "measurement_sessions": MeasurementSession,
        "measurements": Measurement,
        "assessment_snapshots": AssessmentSnapshot,
        "reference_snapshots": ReferenceSnapshot,
    }

    for table_name, model_type in expected_models.items():
        assert _column_names(connection, table_name) == tuple(
            field.name
            for field in fields(model_type)
        )


def test_schema_v1_creates_expected_indexes() -> None:
    connection = _open_memory_database()
    create_schema_v1(
        connection,
        created_at_ms=TEST_NOW_MS,
    )

    indexes = {
        row[0]
        for row in connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'index'
              AND name NOT LIKE 'sqlite_%'
            """
        )
    }

    assert indexes == set(SCHEMA_V1_INDEXES)


def test_schema_meta_has_one_current_version_row_with_epoch_ms() -> None:
    connection = _open_memory_database()

    create_schema_v1(
        connection,
        created_at_ms=TEST_NOW_MS,
    )

    rows = connection.execute(
        """
        SELECT schema_version, created_at_ms, last_migrated_at_ms
        FROM schema_meta
        """
    ).fetchall()

    assert rows == [
        (
            SCHEMA_V1_VERSION,
            TEST_NOW_MS,
            TEST_NOW_MS,
        )
    ]


def test_create_schema_v1_is_idempotent_and_preserves_schema_meta() -> None:
    connection = _open_memory_database()

    create_schema_v1(
        connection,
        created_at_ms=TEST_NOW_MS,
    )
    create_schema_v1(
        connection,
        created_at_ms=TEST_NOW_MS + 999,
    )

    rows = connection.execute(
        """
        SELECT schema_version, created_at_ms, last_migrated_at_ms
        FROM schema_meta
        """
    ).fetchall()

    assert rows == [
        (
            SCHEMA_V1_VERSION,
            TEST_NOW_MS,
            TEST_NOW_MS,
        )
    ]


def test_schema_meta_physically_rejects_second_row() -> None:
    connection = _open_memory_database()
    create_schema_v1(
        connection,
        created_at_ms=TEST_NOW_MS,
    )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO schema_meta (
                schema_version,
                created_at_ms,
                last_migrated_at_ms
            )
            VALUES (?, ?, ?)
            """,
            (
                SCHEMA_V1_VERSION,
                TEST_NOW_MS + 1,
                TEST_NOW_MS + 1,
            ),
        )


def test_sample_state_values_match_approved_set() -> None:
    assert {state.value for state in SampleState} == {
        "NEW",
        "NOS_UNKNOWN_AGE",
        "USED_WORKING",
        "USED_UNKNOWN",
        "SUSPECT",
        "FAILED_CONFIRMED",
        "REFERENCE_SAMPLE",
        "UNKNOWN",
    }


def test_measurement_method_values_match_approved_set() -> None:
    assert {method.value for method in MeasurementMethod} == {
        "EX_SITU",
        "ONE_LEG",
        "IN_CIRCUIT",
    }


def test_measurements_schema_contains_no_hidden_corrected_esr_fields() -> None:
    connection = _open_memory_database()
    create_schema_v1(
        connection,
        created_at_ms=TEST_NOW_MS,
    )

    measurement_columns = set(
        _column_names(connection, "measurements")
    )

    assert "corrected_esr" not in measurement_columns
    assert "normalized_esr" not in measurement_columns
    assert "estimated_esr_100khz" not in measurement_columns
    assert "temperature_corrected_esr" not in measurement_columns


def test_measurements_allow_null_raw_values_for_out_of_range() -> None:
    connection = _open_memory_database()
    create_schema_v1(
        connection,
        created_at_ms=TEST_NOW_MS,
    )

    connection.execute(
        """
        INSERT INTO component_models (
            technology,
            created_at_ms
        )
        VALUES (?, ?)
        """,
        ("ALUMINUM_ELECTROLYTIC", TEST_NOW_MS),
    )
    component_model_id = connection.execute(
        "SELECT id FROM component_models"
    ).fetchone()[0]

    connection.execute(
        """
        INSERT INTO component_samples (
            component_model_id,
            sample_state,
            created_at_ms
        )
        VALUES (?, ?, ?)
        """,
        (
            component_model_id,
            SampleState.NEW.value,
            TEST_NOW_MS,
        ),
    )
    component_sample_id = connection.execute(
        "SELECT id FROM component_samples"
    ).fetchone()[0]

    connection.execute(
        """
        INSERT INTO measurement_sessions (
            component_sample_id,
            started_at_ms,
            created_at_ms
        )
        VALUES (?, ?, ?)
        """,
        (
            component_sample_id,
            TEST_NOW_MS,
            TEST_NOW_MS,
        ),
    )
    session_id = connection.execute(
        "SELECT id FROM measurement_sessions"
    ).fetchone()[0]

    connection.execute(
        """
        INSERT INTO measurements (
            measurement_session_id,
            measured_at_ms,
            measurement_method,
            capacitance_f,
            esr_ohm,
            out_of_range,
            created_at_ms
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            TEST_NOW_MS,
            MeasurementMethod.EX_SITU.value,
            None,
            None,
            1,
            TEST_NOW_MS,
        ),
    )

    stored = connection.execute(
        """
        SELECT capacitance_f, esr_ohm, out_of_range
        FROM measurements
        """
    ).fetchone()

    assert stored == (None, None, 1)


def test_foreign_keys_use_restrict_for_historical_relations() -> None:
    connection = _open_memory_database()
    create_schema_v1(
        connection,
        created_at_ms=TEST_NOW_MS,
    )

    relations = {
        "component_samples": {"component_models"},
        "measurement_sessions": {"component_samples"},
        "measurements": {"measurement_sessions", "measurements"},
        "assessment_snapshots": {"measurements"},
        "reference_snapshots": {"assessment_snapshots"},
    }

    for table_name, expected_targets in relations.items():
        rows = connection.execute(
            f"PRAGMA foreign_key_list({table_name})"
        ).fetchall()

        assert {row[2] for row in rows} == expected_targets
        assert {row[6].upper() for row in rows} == {"RESTRICT"}


def test_current_schema_adds_tool_key_and_index() -> None:
    connection = _open_memory_database()
    create_schema_current(connection, created_at_ms=TEST_NOW_MS)
    columns = set(_column_names(connection, "measurements"))
    indexes = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")}
    assert "tool_key" in columns
    assert "ix_measurements_tool_key" in indexes
    assert indexes == set(SCHEMA_CURRENT_INDEXES)
    assert connection.execute("SELECT schema_version FROM schema_meta").fetchone()[0] == 3


def test_current_schema_adds_source_identity_columns_and_index() -> None:
    connection = _open_memory_database()
    create_schema_current(connection, created_at_ms=TEST_NOW_MS)

    columns = set(_column_names(connection, "measurements"))
    indexes = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='index' AND name NOT LIKE 'sqlite_%'"
        )
    }

    assert "source_machine_id" in columns
    assert "source_measurement_id" in columns
    assert "ix_measurements_source_identity" in indexes
    assert connection.execute(
        "SELECT schema_version FROM schema_meta"
    ).fetchone()[0] == 3


def test_current_schema_source_identity_columns_are_nullable() -> None:
    connection = _open_memory_database()
    create_schema_current(connection, created_at_ms=TEST_NOW_MS)

    rows = connection.execute(
        "PRAGMA table_info(measurements)"
    ).fetchall()
    kolommen = {row[1]: row for row in rows}

    # PRAGMA table_info: index 3 = notnull, index 4 = default value
    assert kolommen["source_machine_id"][3] == 0  # nullable
    assert kolommen["source_measurement_id"][3] == 0  # nullable


def test_measurement_model_has_source_identity_fields_with_none_default() -> None:
    field_names = [field.name for field in fields(Measurement)]
    assert field_names[-2:] == [
        "source_machine_id",
        "source_measurement_id",
    ]


def test_measurement_can_be_constructed_without_source_identity() -> None:
    """Backward-compat: bestaande constructors zonder herkomst blijven werken."""
    measurement = Measurement(
        id=1,
        measurement_session_id=1,
        measured_at_ms=0,
        measurement_method=MeasurementMethod.EX_SITU,
        instrument_key=None,
        instrument_name=None,
        instrument_profile_version=None,
        frequency_hz=None,
        test_voltage_vrms=None,
        temperature_c=None,
        power_off_confirmed=None,
        discharged_confirmed=None,
        residual_voltage_before_v=None,
        residual_voltage_after_v=None,
        capacitance_f=None,
        esr_ohm=None,
        dissipation_factor_d=None,
        quality_factor_q=None,
        impedance_z_ohm=None,
        reactance_x_ohm=None,
        out_of_range=False,
        open_suspected=False,
        short_suspected=False,
        unstable_reading=False,
        parallel_components_notes=None,
        mechanical_condition_notes=None,
        notes=None,
        record_status=None,
        supersedes_measurement_id=None,
        invalid_reason=None,
        created_at_ms=0,
        tool_key="ESR_CAPACITOR",
    )
    assert measurement.source_machine_id is None
    assert measurement.source_measurement_id is None