"""
================================================================================
Module:     tests/test_storage_database.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Gerichte regressietests voor SQLite connection- en database-
            initialisatiegedrag.

            Bewijst dat een database pas bij initialize ontstaat, het huidige
            schema krijgt, verplichte PRAGMA's gebruikt en bestaande ongeldige
            of toekomstige schema's niet stilzwijgend reset.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste database-initialisatie- en connectiontests.
================================================================================
"""

from pathlib import Path
import sqlite3

import pytest

from app.storage.database import (
    BUSY_TIMEOUT_MS,
    initialize_database,
    open_database,
)
from app.storage.exceptions import (
    DatabaseOpenError,
    InvalidDatabaseSchemaError,
    UnsupportedSchemaVersionError,
)
from app.storage.schema import CURRENT_SCHEMA_VERSION, SCHEMA_V1_TABLES


TEST_NOW_MS = 1_796_000_100_000


def _fixed_clock() -> int:
    return TEST_NOW_MS


def test_initialize_creates_database_only_when_called(tmp_path: Path) -> None:
    database_path = tmp_path / "measurements.sqlite3"

    assert not database_path.exists()

    initialize_database(database_path, clock=_fixed_clock)

    assert database_path.is_file()


def test_initialize_new_database_creates_current_schema_and_meta(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "measurements.sqlite3"
    initialize_database(database_path, clock=_fixed_clock)

    connection = open_database(database_path)
    try:
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
        meta = connection.execute(
            """
            SELECT schema_version, created_at_ms, last_migrated_at_ms
            FROM schema_meta
            """
        ).fetchone()
    finally:
        connection.close()

    assert tables == set(SCHEMA_V1_TABLES)
    assert tuple(meta) == (
        CURRENT_SCHEMA_VERSION,
        TEST_NOW_MS,
        TEST_NOW_MS,
    )


def test_open_database_applies_required_connection_settings(tmp_path: Path) -> None:
    database_path = tmp_path / "measurements.sqlite3"
    initialize_database(database_path, clock=_fixed_clock)

    connection = open_database(database_path)
    try:
        foreign_keys = connection.execute("PRAGMA foreign_keys").fetchone()[0]
        busy_timeout = connection.execute("PRAGMA busy_timeout").fetchone()[0]

        row = connection.execute(
            "SELECT schema_version FROM schema_meta"
        ).fetchone()
    finally:
        connection.close()

    assert foreign_keys == 1
    assert busy_timeout == BUSY_TIMEOUT_MS
    assert isinstance(row, sqlite3.Row)


def test_initialize_is_idempotent_and_preserves_existing_data(tmp_path: Path) -> None:
    database_path = tmp_path / "measurements.sqlite3"
    initialize_database(database_path, clock=_fixed_clock)

    connection = open_database(database_path)
    try:
        connection.execute(
            """
            INSERT INTO component_models (technology, created_at_ms)
            VALUES (?, ?)
            """,
            ("TEST_TECHNOLOGY", TEST_NOW_MS),
        )
        connection.commit()
    finally:
        connection.close()

    initialize_database(
        database_path,
        clock=lambda: TEST_NOW_MS + 999,
    )

    connection = open_database(database_path)
    try:
        count = connection.execute(
            "SELECT COUNT(*) FROM component_models"
        ).fetchone()[0]
        meta = connection.execute(
            """
            SELECT schema_version, created_at_ms, last_migrated_at_ms
            FROM schema_meta
            """
        ).fetchone()
    finally:
        connection.close()

    assert count == 1
    assert tuple(meta) == (
        CURRENT_SCHEMA_VERSION,
        TEST_NOW_MS,
        TEST_NOW_MS,
    )


def test_existing_database_without_schema_meta_is_rejected_without_reset(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "measurements.sqlite3"
    connection = sqlite3.connect(database_path)
    connection.execute("CREATE TABLE keep_me (value TEXT NOT NULL)")
    connection.execute("INSERT INTO keep_me (value) VALUES (?)", ("data",))
    connection.commit()
    connection.close()

    with pytest.raises(InvalidDatabaseSchemaError):
        initialize_database(database_path, clock=_fixed_clock)

    connection = sqlite3.connect(database_path)
    try:
        value = connection.execute("SELECT value FROM keep_me").fetchone()[0]
    finally:
        connection.close()

    assert value == "data"


def test_future_schema_version_is_rejected_without_change(tmp_path: Path) -> None:
    database_path = tmp_path / "measurements.sqlite3"
    initialize_database(database_path, clock=_fixed_clock)

    connection = sqlite3.connect(database_path)
    connection.execute(
        "UPDATE schema_meta SET schema_version = ?",
        (CURRENT_SCHEMA_VERSION + 1,),
    )
    connection.commit()
    connection.close()

    with pytest.raises(UnsupportedSchemaVersionError):
        initialize_database(database_path, clock=_fixed_clock)

    connection = sqlite3.connect(database_path)
    try:
        version = connection.execute(
            "SELECT schema_version FROM schema_meta"
        ).fetchone()[0]
    finally:
        connection.close()

    assert version == CURRENT_SCHEMA_VERSION + 1


def test_open_database_wraps_sqlite_open_error(tmp_path: Path) -> None:
    database_path = tmp_path / "missing-parent" / "measurements.sqlite3"

    with pytest.raises(DatabaseOpenError):
        open_database(database_path)


def test_current_version_with_missing_schema_object_is_rejected_without_repair(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "measurements.sqlite3"
    initialize_database(database_path, clock=_fixed_clock)

    connection = sqlite3.connect(database_path)
    connection.execute("DROP INDEX ix_measurements_frequency")
    connection.commit()
    connection.close()

    with pytest.raises(InvalidDatabaseSchemaError, match="ix_measurements_frequency"):
        initialize_database(database_path, clock=_fixed_clock)

    connection = sqlite3.connect(database_path)
    try:
        exists = connection.execute(
            """
            SELECT 1 FROM sqlite_master
            WHERE type = 'index' AND name = ?
            """,
            ("ix_measurements_frequency",),
        ).fetchone()
    finally:
        connection.close()

    assert exists is None
