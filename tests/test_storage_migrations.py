"""
================================================================================
Module:     tests/test_storage_migrations.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-23
Auteur:     Bart Bossuyt

Doel:       Gerichte regressietests voor het transactionele migratieframework.

            Bewijst geen-op-migratie bij current schema, sequentiële volgorde,
            versie-update na succes, rollback bij fout, behoud van data en
            expliciete weigering van ongeldige/toekomstige schema's.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste tests voor migrations.py.
  v1.1.0 (2026-10-23)  Fase 28E: nieuwe tests voor v1 → v3 en v2 → v3.
================================================================================
"""

import sqlite3

import pytest

from app.storage.exceptions import (
    InvalidDatabaseSchemaError,
    MigrationError,
    UnsupportedSchemaVersionError,
)
from app.storage.migrations import migrate_database, read_schema_version
from app.storage.schema import create_schema_v1


TEST_NOW_MS = 1_796_000_200_000


def _connection_with_v1() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    create_schema_v1(connection, created_at_ms=TEST_NOW_MS)
    connection.commit()
    return connection


def test_no_migration_when_schema_is_already_current() -> None:
    connection = _connection_with_v1()
    called = False

    def should_not_run(_: sqlite3.Connection) -> None:
        nonlocal called
        called = True

    result = migrate_database(
        connection,
        target_version=1,
        migrated_at_ms=TEST_NOW_MS + 1,
        migrations={1: should_not_run},
    )

    assert result == 1
    assert called is False


def test_migrations_run_sequentially_and_update_version_after_each_success() -> None:
    connection = _connection_with_v1()
    order: list[int] = []

    def to_v2(conn: sqlite3.Connection) -> None:
        assert read_schema_version(conn) == 1
        conn.execute("CREATE TABLE migration_v2 (value TEXT)")
        order.append(2)

    def to_v3(conn: sqlite3.Connection) -> None:
        assert read_schema_version(conn) == 2
        conn.execute("CREATE TABLE migration_v3 (value TEXT)")
        order.append(3)

    result = migrate_database(
        connection,
        target_version=3,
        migrated_at_ms=TEST_NOW_MS + 10,
        migrations={2: to_v2, 3: to_v3},
    )

    assert result == 3
    assert order == [2, 3]
    assert read_schema_version(connection) == 3


def test_failed_migration_rolls_back_step_and_does_not_advance_version() -> None:
    connection = _connection_with_v1()

    def failing_to_v2(conn: sqlite3.Connection) -> None:
        conn.execute("CREATE TABLE should_rollback (value TEXT)")
        raise RuntimeError("boom")

    with pytest.raises(MigrationError):
        migrate_database(
            connection,
            target_version=2,
            migrated_at_ms=TEST_NOW_MS + 10,
            migrations={2: failing_to_v2},
        )

    assert read_schema_version(connection) == 1
    table = connection.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type = 'table' AND name = 'should_rollback'
        """
    ).fetchone()
    assert table is None


def test_successful_earlier_step_remains_when_later_step_fails() -> None:
    connection = _connection_with_v1()

    def to_v2(conn: sqlite3.Connection) -> None:
        conn.execute("CREATE TABLE migration_v2 (value TEXT)")

    def failing_to_v3(conn: sqlite3.Connection) -> None:
        conn.execute("CREATE TABLE migration_v3 (value TEXT)")
        raise RuntimeError("boom")

    with pytest.raises(MigrationError):
        migrate_database(
            connection,
            target_version=3,
            migrated_at_ms=TEST_NOW_MS + 10,
            migrations={2: to_v2, 3: failing_to_v3},
        )

    assert read_schema_version(connection) == 2
    assert connection.execute(
        "SELECT name FROM sqlite_master WHERE name = 'migration_v2'"
    ).fetchone() is not None
    assert connection.execute(
        "SELECT name FROM sqlite_master WHERE name = 'migration_v3'"
    ).fetchone() is None


def test_migration_preserves_existing_user_data() -> None:
    connection = _connection_with_v1()
    connection.execute(
        """
        INSERT INTO component_models (technology, created_at_ms)
        VALUES (?, ?)
        """,
        ("KEEP", TEST_NOW_MS),
    )
    connection.commit()

    def to_v2(conn: sqlite3.Connection) -> None:
        conn.execute("ALTER TABLE component_models ADD COLUMN future_note TEXT")

    migrate_database(
        connection,
        target_version=2,
        migrated_at_ms=TEST_NOW_MS + 10,
        migrations={2: to_v2},
    )

    row = connection.execute(
        "SELECT technology FROM component_models"
    ).fetchone()
    assert row[0] == "KEEP"


def test_missing_migration_step_is_explicit_error() -> None:
    connection = _connection_with_v1()

    with pytest.raises(MigrationError, match="versie 2"):
        migrate_database(
            connection,
            target_version=2,
            migrated_at_ms=TEST_NOW_MS + 10,
            migrations={},
        )

    assert read_schema_version(connection) == 1


def test_future_schema_is_rejected() -> None:
    connection = _connection_with_v1()
    connection.execute("UPDATE schema_meta SET schema_version = 99")
    connection.commit()

    with pytest.raises(UnsupportedSchemaVersionError):
        migrate_database(
            connection,
            target_version=3,
            migrated_at_ms=TEST_NOW_MS + 10,
            migrations={},
        )


def test_missing_schema_meta_is_rejected() -> None:
    connection = sqlite3.connect(":memory:")

    with pytest.raises(InvalidDatabaseSchemaError):
        read_schema_version(connection)


# ---------------------------------------------------------------- 28E: v3

def test_migration_v1_to_v3_in_one_call_adds_both_v2_and_v3_structure() -> None:
    connection = _connection_with_v1()

    result = migrate_database(
        connection,
        target_version=3,
        migrated_at_ms=TEST_NOW_MS + 10,
    )

    assert result == 3

    columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(measurements)")
    }
    indexes = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='index' AND name NOT LIKE 'sqlite_%'"
        )
    }

    assert "tool_key" in columns
    assert "source_machine_id" in columns
    assert "source_measurement_id" in columns
    assert "ix_measurements_tool_key" in indexes
    assert "ix_measurements_source_identity" in indexes


def test_migration_v2_to_v3_adds_source_identity_columns() -> None:
    connection = _connection_with_v1()
    # Eerst naar v2.
    migrate_database(
        connection,
        target_version=2,
        migrated_at_ms=TEST_NOW_MS + 5,
    )
    assert read_schema_version(connection) == 2

    # Dan naar v3.
    migrate_database(
        connection,
        target_version=3,
        migrated_at_ms=TEST_NOW_MS + 10,
    )

    columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(measurements)")
    }
    assert "source_machine_id" in columns
    assert "source_measurement_id" in columns
    assert read_schema_version(connection) == 3


def test_migration_to_v3_preserves_existing_measurements() -> None:
    connection = _connection_with_v1()

    # Bouw een geldige meetketen op v1.
    connection.execute(
        "INSERT INTO component_models (manufacturer, created_at_ms) "
        "VALUES (?, ?)",
        ("Legacy", TEST_NOW_MS),
    )
    model_id = connection.execute(
        "SELECT id FROM component_models"
    ).fetchone()[0]
    connection.execute(
        "INSERT INTO component_samples "
        "(component_model_id, sample_state, created_at_ms) "
        "VALUES (?, 'UNKNOWN', ?)",
        (model_id, TEST_NOW_MS),
    )
    sample_id = connection.execute(
        "SELECT id FROM component_samples"
    ).fetchone()[0]
    connection.execute(
        "INSERT INTO measurement_sessions "
        "(component_sample_id, started_at_ms, created_at_ms) "
        "VALUES (?, ?, ?)",
        (sample_id, TEST_NOW_MS, TEST_NOW_MS),
    )
    session_id = connection.execute(
        "SELECT id FROM measurement_sessions"
    ).fetchone()[0]
    connection.execute(
        "INSERT INTO measurements "
        "(measurement_session_id, measured_at_ms, measurement_method, "
        "capacitance_f, esr_ohm, created_at_ms) "
        "VALUES (?, ?, 'EX_SITU', 470e-6, 0.2, ?)",
        (session_id, TEST_NOW_MS + 1, TEST_NOW_MS + 1),
    )
    connection.commit()

    migrate_database(
        connection,
        target_version=3,
        migrated_at_ms=TEST_NOW_MS + 10,
    )

    row = connection.execute(
        "SELECT capacitance_f, esr_ohm, tool_key, "
        "source_machine_id, source_measurement_id "
        "FROM measurements"
    ).fetchone()

    assert row[0] == 470e-6
    assert row[1] == 0.2
    assert row[2] == "ESR_CAPACITOR"
    assert row[3] is None
    assert row[4] is None