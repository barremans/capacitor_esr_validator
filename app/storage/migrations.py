"""
================================================================================
Module:     app/storage/migrations.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Transactioneel en sequentieel migratieframework voor de lokale
            SQLite-meetdatabase.

            Iedere migratiestap draait in een eigen transactie. De waarde in
            schema_meta.schema_version wordt pas na een volledig geslaagde stap
            verhoogd. Dit bestand bevat geen GUI- of assessmentlogica.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste migratieframework met sequentiële stappen,
                        rollback per mislukte stap en expliciete versiecontrole.
================================================================================
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
import sqlite3

from .exceptions import (
    InvalidDatabaseSchemaError,
    MigrationError,
    UnsupportedSchemaVersionError,
)
from .schema import CURRENT_SCHEMA_VERSION


MigrationStep = Callable[[sqlite3.Connection], None]

# Sleutel = doelversie van de migratiestap. Schema v1 is het initiële schema en
# heeft daarom geen migratiestap nodig. Toekomstig bijvoorbeeld: 2: _migrate_v1_to_v2.
MIGRATIONS: dict[int, MigrationStep] = {}


def read_schema_version(connection: sqlite3.Connection) -> int:
    """Lees de enige geldige schema_version uit schema_meta."""
    table_exists = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        ("schema_meta",),
    ).fetchone()

    if table_exists is None:
        raise InvalidDatabaseSchemaError(
            "De database bevat geen schema_meta-tabel."
        )

    rows = connection.execute(
        "SELECT schema_version FROM schema_meta"
    ).fetchall()

    if len(rows) != 1:
        raise InvalidDatabaseSchemaError(
            "schema_meta moet exact één rij bevatten."
        )

    version = rows[0][0]
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise InvalidDatabaseSchemaError(
            "schema_meta bevat geen geldige positieve schemaversie."
        )

    return version


def migrate_database(
    connection: sqlite3.Connection,
    *,
    target_version: int = CURRENT_SCHEMA_VERSION,
    migrated_at_ms: int,
    migrations: Mapping[int, MigrationStep] | None = None,
) -> int:
    """
    Migreer een bestaande database sequentieel naar ``target_version``.

    Elke afzonderlijke versiestap is atomair. Bij een fout wordt uitsluitend de
    actieve stap teruggedraaid; reeds succesvol gecommitte versiestappen blijven
    geldig. De schema-versie wordt pas na de geslaagde migratiecode bijgewerkt.
    """
    if target_version < 1:
        raise ValueError("target_version moet minstens 1 zijn.")
    if migrated_at_ms < 0:
        raise ValueError("migrated_at_ms mag niet negatief zijn.")

    current_version = read_schema_version(connection)

    if current_version > target_version:
        raise UnsupportedSchemaVersionError(
            "De database gebruikt schema-versie "
            f"{current_version}, maar deze applicatie ondersteunt maximaal "
            f"versie {target_version}."
        )

    if current_version == target_version:
        return current_version

    available_migrations = MIGRATIONS if migrations is None else migrations

    for next_version in range(current_version + 1, target_version + 1):
        migration = available_migrations.get(next_version)
        if migration is None:
            raise MigrationError(
                "Geen migratiestap beschikbaar voor schema-versie "
                f"{next_version}."
            )

        try:
            connection.execute("BEGIN IMMEDIATE")
            migration(connection)
            connection.execute(
                """
                UPDATE schema_meta
                SET schema_version = ?,
                    last_migrated_at_ms = ?
                """,
                (next_version, migrated_at_ms),
            )
            connection.commit()
        except Exception as exc:
            connection.rollback()
            if isinstance(exc, MigrationError):
                raise
            raise MigrationError(
                f"Migratie naar schema-versie {next_version} is mislukt."
            ) from exc

    return read_schema_version(connection)
