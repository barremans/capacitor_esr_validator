"""
================================================================================
Module:     app/storage/schema.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Declaratieve SQLite-DDL voor de lokale meetdatabase.

            Schema v2 maakt de historiek expliciet multitool-ready door elke
            measurement een stabiele tool_key te geven. Bestaande ESR-records
            krijgen ESR_CAPACITOR. De bestaande zeven hoofdtabellen blijven
            behouden; er wordt geen ruwe meetdata herschreven.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste SQLite schema v1 met zeven hoofdtabellen.
  v1.1.0 (2026-10-01)  Schema v2: tool_key + index toegevoegd aan measurements;
                        create_schema_current() maakt rechtstreeks de huidige
                        structuur aan, met behoud van create_schema_v1() voor
                        migratie- en regressietests.
================================================================================
"""

from __future__ import annotations

import sqlite3


SCHEMA_V1_VERSION = 1
CURRENT_SCHEMA_VERSION = 2
DEFAULT_TOOL_KEY = "ESR_CAPACITOR"

SCHEMA_V1_TABLES = (
    "schema_meta",
    "component_models",
    "component_samples",
    "measurement_sessions",
    "measurements",
    "assessment_snapshots",
    "reference_snapshots",
)
SCHEMA_CURRENT_TABLES = SCHEMA_V1_TABLES

SCHEMA_V1_INDEXES = (
    "ux_schema_meta_single_row",
    "ix_component_models_identity",
    "ix_component_samples_model",
    "ix_component_samples_state",
    "ix_measurement_sessions_sample",
    "ix_measurements_session",
    "ix_measurements_history_order",
    "ix_measurements_method",
    "ix_measurements_instrument",
    "ix_measurements_frequency",
    "ix_measurements_test_voltage",
    "ix_assessment_snapshots_measurement",
    "ix_assessment_snapshots_status",
    "ix_reference_snapshots_assessment",
)
SCHEMA_CURRENT_INDEXES = SCHEMA_V1_INDEXES + ("ix_measurements_tool_key",)

SCHEMA_V1_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS schema_meta (
        schema_version INTEGER NOT NULL CHECK (schema_version >= 1),
        created_at_ms INTEGER NOT NULL CHECK (created_at_ms >= 0),
        last_migrated_at_ms INTEGER NOT NULL CHECK (last_migrated_at_ms >= 0)
    )
    """,
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_schema_meta_single_row ON schema_meta ((1))",
    """
    CREATE TABLE IF NOT EXISTS component_models (
        id INTEGER PRIMARY KEY,
        manufacturer TEXT, series TEXT, part_number TEXT, technology TEXT,
        nominal_capacitance_f REAL CHECK (nominal_capacitance_f IS NULL OR nominal_capacitance_f >= 0),
        nominal_capacitance_value REAL CHECK (nominal_capacitance_value IS NULL OR nominal_capacitance_value >= 0),
        nominal_capacitance_unit TEXT,
        rated_voltage_v REAL CHECK (rated_voltage_v IS NULL OR rated_voltage_v >= 0),
        voltage_type TEXT,
        tolerance_lower_pct REAL, tolerance_upper_pct REAL,
        temperature_min_c REAL, temperature_max_c REAL,
        case_size TEXT, notes TEXT,
        created_at_ms INTEGER NOT NULL CHECK (created_at_ms >= 0)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS component_samples (
        id INTEGER PRIMARY KEY,
        component_model_id INTEGER NOT NULL,
        sample_code TEXT,
        sample_state TEXT NOT NULL CHECK (sample_state IN ('NEW','NOS_UNKNOWN_AGE','USED_WORKING','USED_UNKNOWN','SUSPECT','FAILED_CONFIRMED','REFERENCE_SAMPLE','UNKNOWN')),
        source TEXT, batch_lot_code TEXT, date_code TEXT, visual_condition TEXT, notes TEXT,
        created_at_ms INTEGER NOT NULL CHECK (created_at_ms >= 0),
        FOREIGN KEY (component_model_id) REFERENCES component_models(id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS measurement_sessions (
        id INTEGER PRIMARY KEY,
        component_sample_id INTEGER NOT NULL,
        started_at_ms INTEGER NOT NULL CHECK (started_at_ms >= 0),
        ended_at_ms INTEGER CHECK (ended_at_ms IS NULL OR ended_at_ms >= 0),
        operator_name TEXT, customer TEXT, project TEXT, installation TEXT,
        module_board TEXT, component_reference TEXT, notes TEXT,
        created_at_ms INTEGER NOT NULL CHECK (created_at_ms >= 0),
        FOREIGN KEY (component_sample_id) REFERENCES component_samples(id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS measurements (
        id INTEGER PRIMARY KEY,
        measurement_session_id INTEGER NOT NULL,
        measured_at_ms INTEGER NOT NULL CHECK (measured_at_ms >= 0),
        measurement_method TEXT NOT NULL CHECK (measurement_method IN ('EX_SITU','ONE_LEG','IN_CIRCUIT')),
        instrument_key TEXT, instrument_name TEXT, instrument_profile_version TEXT,
        frequency_hz REAL CHECK (frequency_hz IS NULL OR frequency_hz > 0),
        test_voltage_vrms REAL CHECK (test_voltage_vrms IS NULL OR test_voltage_vrms >= 0),
        temperature_c REAL,
        power_off_confirmed INTEGER CHECK (power_off_confirmed IS NULL OR power_off_confirmed IN (0,1)),
        discharged_confirmed INTEGER CHECK (discharged_confirmed IS NULL OR discharged_confirmed IN (0,1)),
        residual_voltage_before_v REAL, residual_voltage_after_v REAL,
        capacitance_f REAL CHECK (capacitance_f IS NULL OR capacitance_f >= 0),
        esr_ohm REAL CHECK (esr_ohm IS NULL OR esr_ohm >= 0),
        dissipation_factor_d REAL, quality_factor_q REAL, impedance_z_ohm REAL, reactance_x_ohm REAL,
        out_of_range INTEGER NOT NULL DEFAULT 0 CHECK (out_of_range IN (0,1)),
        open_suspected INTEGER NOT NULL DEFAULT 0 CHECK (open_suspected IN (0,1)),
        short_suspected INTEGER NOT NULL DEFAULT 0 CHECK (short_suspected IN (0,1)),
        unstable_reading INTEGER NOT NULL DEFAULT 0 CHECK (unstable_reading IN (0,1)),
        parallel_components_notes TEXT, mechanical_condition_notes TEXT, notes TEXT,
        record_status TEXT, supersedes_measurement_id INTEGER, invalid_reason TEXT,
        created_at_ms INTEGER NOT NULL CHECK (created_at_ms >= 0),
        FOREIGN KEY (measurement_session_id) REFERENCES measurement_sessions(id) ON DELETE RESTRICT,
        FOREIGN KEY (supersedes_measurement_id) REFERENCES measurements(id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS assessment_snapshots (
        id INTEGER PRIMARY KEY, measurement_id INTEGER NOT NULL,
        assessed_at_ms INTEGER NOT NULL CHECK (assessed_at_ms >= 0),
        engine_version TEXT, capacitance_status TEXT, capacitance_deviation_pct REAL,
        esr_status TEXT, esr_factor REAL, consistency_status TEXT,
        derived_esr_from_d_ohm REAL CHECK (derived_esr_from_d_ohm IS NULL OR derived_esr_from_d_ohm >= 0),
        reliability_level TEXT, final_status TEXT,
        reasons_json TEXT, warnings_json TEXT, advice_json TEXT,
        created_at_ms INTEGER NOT NULL CHECK (created_at_ms >= 0),
        FOREIGN KEY (measurement_id) REFERENCES measurements(id) ON DELETE RESTRICT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reference_snapshots (
        id INTEGER PRIMARY KEY, assessment_snapshot_id INTEGER NOT NULL,
        reference_role TEXT, reference_level TEXT, reference_type TEXT,
        manufacturer TEXT, series TEXT, part_number TEXT,
        reference_value REAL, reference_unit TEXT,
        frequency_hz REAL CHECK (frequency_hz IS NULL OR frequency_hz > 0),
        temperature_c REAL,
        test_voltage_vrms REAL CHECK (test_voltage_vrms IS NULL OR test_voltage_vrms >= 0),
        dc_bias_v REAL, value_kind TEXT, source_name TEXT, source_document TEXT,
        source_version TEXT, source_data_version TEXT, source_entry_id TEXT, source_hash TEXT,
        snapshot_json TEXT,
        created_at_ms INTEGER NOT NULL CHECK (created_at_ms >= 0),
        FOREIGN KEY (assessment_snapshot_id) REFERENCES assessment_snapshots(id) ON DELETE RESTRICT
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_component_models_identity ON component_models (manufacturer, series, part_number)",
    "CREATE INDEX IF NOT EXISTS ix_component_samples_model ON component_samples (component_model_id)",
    "CREATE INDEX IF NOT EXISTS ix_component_samples_state ON component_samples (sample_state)",
    "CREATE INDEX IF NOT EXISTS ix_measurement_sessions_sample ON measurement_sessions (component_sample_id)",
    "CREATE INDEX IF NOT EXISTS ix_measurements_session ON measurements (measurement_session_id)",
    "CREATE INDEX IF NOT EXISTS ix_measurements_history_order ON measurements (measured_at_ms DESC, id DESC)",
    "CREATE INDEX IF NOT EXISTS ix_measurements_method ON measurements (measurement_method)",
    "CREATE INDEX IF NOT EXISTS ix_measurements_instrument ON measurements (instrument_key)",
    "CREATE INDEX IF NOT EXISTS ix_measurements_frequency ON measurements (frequency_hz)",
    "CREATE INDEX IF NOT EXISTS ix_measurements_test_voltage ON measurements (test_voltage_vrms)",
    "CREATE INDEX IF NOT EXISTS ix_assessment_snapshots_measurement ON assessment_snapshots (measurement_id, assessed_at_ms DESC, id DESC)",
    "CREATE INDEX IF NOT EXISTS ix_assessment_snapshots_status ON assessment_snapshots (final_status, reliability_level)",
    "CREATE INDEX IF NOT EXISTS ix_reference_snapshots_assessment ON reference_snapshots (assessment_snapshot_id)",
)


def create_schema_v1(connection: sqlite3.Connection, *, created_at_ms: int) -> None:
    """Maak exact legacy schema v1 aan; uitsluitend voor migratie/regressie."""
    for statement in SCHEMA_V1_STATEMENTS:
        connection.execute(statement)
    connection.execute(
        "INSERT OR IGNORE INTO schema_meta (schema_version, created_at_ms, last_migrated_at_ms) VALUES (?, ?, ?)",
        (SCHEMA_V1_VERSION, created_at_ms, created_at_ms),
    )


def apply_schema_v2_structure(connection: sqlite3.Connection) -> None:
    """Voeg alleen de v2-structuur toe; commit en schema_meta-update gebeuren elders."""
    columns = {row[1] for row in connection.execute("PRAGMA table_info(measurements)")}
    if "tool_key" not in columns:
        connection.execute(
            "ALTER TABLE measurements ADD COLUMN tool_key TEXT NOT NULL DEFAULT 'ESR_CAPACITOR'"
        )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS ix_measurements_tool_key ON measurements (tool_key)"
    )


def create_schema_current(connection: sqlite3.Connection, *, created_at_ms: int) -> None:
    """Maak een nieuwe database rechtstreeks in de huidige schema-toestand."""
    create_schema_v1(connection, created_at_ms=created_at_ms)
    apply_schema_v2_structure(connection)
    connection.execute(
        "UPDATE schema_meta SET schema_version = ?, last_migrated_at_ms = ?",
        (CURRENT_SCHEMA_VERSION, created_at_ms),
    )
