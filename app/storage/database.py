"""
================================================================================
Module:     app/storage/database.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Veilige SQLite-connection- en initialisatielaag voor de lokale
            meetdatabase.

            Iedere connection activeert foreign keys, een busy timeout van
            5000 ms en sqlite3.Row. Nieuwe databases krijgen rechtstreeks het
            huidige schema; bestaande databases worden uitsluitend gevalideerd
            en indien nodig sequentieel gemigreerd.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste database-initialisatielaag met verplichte PRAGMA's,
                        schema-versiecontrole en koppeling aan migraties.
  v1.1.0 (2026-10-01)  Nieuwe databases starten rechtstreeks op schema v2;
                        bestaande v1-databases migreren transactioneel.
================================================================================
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import sqlite3
import time

from .exceptions import (
    DatabaseOpenError,
    InvalidDatabaseSchemaError,
    StorageInitializationError,
    UnsupportedSchemaVersionError,
)
from .migrations import migrate_database, read_schema_version
from .schema import (
    CURRENT_SCHEMA_VERSION,
    SCHEMA_CURRENT_INDEXES,
    SCHEMA_CURRENT_TABLES,
    create_schema_current,
)


BUSY_TIMEOUT_MS = 5000


def utc_now_ms() -> int:
    """Geef de huidige Unix epoch-tijd in milliseconden."""
    return time.time_ns() // 1_000_000


def open_database(database_path: Path | str) -> sqlite3.Connection:
    """Open één geconfigureerde SQLite-connection voor de applicatiedatabase."""
    path = Path(database_path)

    try:
        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
        return connection
    except sqlite3.Error as exc:
        raise DatabaseOpenError(
            f"De SQLite-database kon niet worden geopend: {path}"
        ) from exc


def validate_current_schema(connection: sqlite3.Connection) -> None:
    """Controleer dat het huidige schema alle verplichte objecten bevat."""
    version = read_schema_version(connection)
    if version != CURRENT_SCHEMA_VERSION:
        raise InvalidDatabaseSchemaError(
            "Schema-validatie kan alleen op de huidige ondersteunde versie worden "
            "uitgevoerd."
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

    missing_tables = set(SCHEMA_CURRENT_TABLES) - tables
    missing_indexes = set(SCHEMA_CURRENT_INDEXES) - indexes
    if missing_tables or missing_indexes:
        missing_parts = []
        if missing_tables:
            missing_parts.append(
                "tabellen: " + ", ".join(sorted(missing_tables))
            )
        if missing_indexes:
            missing_parts.append(
                "indexes: " + ", ".join(sorted(missing_indexes))
            )
        raise InvalidDatabaseSchemaError(
            "De database mist verplichte schema-objecten ("
            + "; ".join(missing_parts)
            + ")."
        )


def initialize_database(
    database_path: Path | str,
    *,
    clock: Callable[[], int] = utc_now_ms,
) -> None:
    """
    Initialiseer of valideer de database op ``database_path``.

    Een niet-bestaande database krijgt direct het actuele schema. Een bestaande
    database zonder herkenbaar schema wordt niet gewist of stilzwijgend opnieuw
    opgebouwd. Een ondersteunde oudere versie loopt via het migratieframework.
    """
    path = Path(database_path)
    existed_before_open = path.exists()
    now_ms = clock()

    if isinstance(now_ms, bool) or not isinstance(now_ms, int) or now_ms < 0:
        raise StorageInitializationError(
            "De storage-klok moet een niet-negatieve Unix epoch-ms integer geven."
        )

    connection = open_database(path)
    try:
        if not existed_before_open:
            try:
                connection.execute("BEGIN IMMEDIATE")
                create_schema_current(
                    connection,
                    created_at_ms=now_ms,
                )
                connection.commit()
            except sqlite3.Error as exc:
                connection.rollback()
                raise StorageInitializationError(
                    "De nieuwe SQLite-database kon niet worden geïnitialiseerd."
                ) from exc
            return

        current_version = read_schema_version(connection)
        if current_version > CURRENT_SCHEMA_VERSION:
            raise UnsupportedSchemaVersionError(
                "De database gebruikt schema-versie "
                f"{current_version}, maar deze applicatie ondersteunt maximaal "
                f"versie {CURRENT_SCHEMA_VERSION}."
            )

        if current_version < CURRENT_SCHEMA_VERSION:
            migrate_database(
                connection,
                target_version=CURRENT_SCHEMA_VERSION,
                migrated_at_ms=now_ms,
            )

        validate_current_schema(connection)
    except (
        InvalidDatabaseSchemaError,
        UnsupportedSchemaVersionError,
    ):
        raise
    finally:
        connection.close()
