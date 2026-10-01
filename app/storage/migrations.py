"""
================================================================================
Module:     app/storage/migrations.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Transactioneel en sequentieel migratieframework voor de lokale
            SQLite-meetdatabase.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste migratieframework.
  v1.1.0 (2026-10-01)  Migratie v1 -> v2 toegevoegd: bestaande measurements
                        krijgen tool_key='ESR_CAPACITOR' en tool-index.
================================================================================
"""
from __future__ import annotations
from collections.abc import Callable, Mapping
import sqlite3
from .exceptions import InvalidDatabaseSchemaError, MigrationError, UnsupportedSchemaVersionError
from .schema import CURRENT_SCHEMA_VERSION, apply_schema_v2_structure

MigrationStep = Callable[[sqlite3.Connection], None]

def _migrate_v1_to_v2(connection: sqlite3.Connection) -> None:
    apply_schema_v2_structure(connection)

MIGRATIONS: dict[int, MigrationStep] = {2: _migrate_v1_to_v2}

def read_schema_version(connection: sqlite3.Connection) -> int:
    table_exists = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", ("schema_meta",)).fetchone()
    if table_exists is None:
        raise InvalidDatabaseSchemaError("De database bevat geen schema_meta-tabel.")
    rows = connection.execute("SELECT schema_version FROM schema_meta").fetchall()
    if len(rows) != 1:
        raise InvalidDatabaseSchemaError("schema_meta moet exact één rij bevatten.")
    version = rows[0][0]
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise InvalidDatabaseSchemaError("schema_meta bevat geen geldige positieve schemaversie.")
    return version

def migrate_database(connection: sqlite3.Connection, *, target_version: int = CURRENT_SCHEMA_VERSION, migrated_at_ms: int, migrations: Mapping[int, MigrationStep] | None = None) -> int:
    if target_version < 1:
        raise ValueError("target_version moet minstens 1 zijn.")
    if migrated_at_ms < 0:
        raise ValueError("migrated_at_ms mag niet negatief zijn.")
    current_version = read_schema_version(connection)
    if current_version > target_version:
        raise UnsupportedSchemaVersionError(f"De database gebruikt schema-versie {current_version}, maar deze applicatie ondersteunt maximaal versie {target_version}.")
    if current_version == target_version:
        return current_version
    available_migrations = MIGRATIONS if migrations is None else migrations
    for next_version in range(current_version + 1, target_version + 1):
        migration = available_migrations.get(next_version)
        if migration is None:
            raise MigrationError(f"Geen migratiestap beschikbaar voor schema-versie {next_version}.")
        try:
            connection.execute("BEGIN IMMEDIATE")
            migration(connection)
            connection.execute("UPDATE schema_meta SET schema_version=?, last_migrated_at_ms=?", (next_version, migrated_at_ms))
            connection.commit()
        except Exception as exc:
            connection.rollback()
            if isinstance(exc, MigrationError):
                raise
            raise MigrationError(f"Migratie naar schema-versie {next_version} is mislukt.") from exc
    return read_schema_version(connection)
