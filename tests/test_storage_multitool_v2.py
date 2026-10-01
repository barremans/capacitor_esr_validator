"""
================================================================================
Module:     tests/test_storage_multitool_v2.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Regressietests voor schema v2 multitool-discriminator en veilige
            migratie van bestaande ESR-historiek.
================================================================================
"""
from pathlib import Path
import sqlite3

from app.storage.database import initialize_database, open_database
from app.storage.schema import CURRENT_SCHEMA_VERSION, create_schema_v1
from app.storage.service import StorageService

NOW = 1_800_000_123_000


def _create_v1_database(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    create_schema_v1(connection, created_at_ms=NOW)
    connection.execute("INSERT INTO component_models (manufacturer, created_at_ms) VALUES (?, ?)", ("Legacy", NOW))
    model_id = connection.execute("SELECT id FROM component_models").fetchone()[0]
    connection.execute("INSERT INTO component_samples (component_model_id, sample_state, created_at_ms) VALUES (?, 'UNKNOWN', ?)", (model_id, NOW))
    sample_id = connection.execute("SELECT id FROM component_samples").fetchone()[0]
    connection.execute("INSERT INTO measurement_sessions (component_sample_id, started_at_ms, created_at_ms) VALUES (?, ?, ?)", (sample_id, NOW, NOW))
    session_id = connection.execute("SELECT id FROM measurement_sessions").fetchone()[0]
    connection.execute(
        "INSERT INTO measurements (measurement_session_id, measured_at_ms, measurement_method, capacitance_f, esr_ohm, created_at_ms) VALUES (?, ?, 'EX_SITU', ?, ?, ?)",
        (session_id, NOW + 1, 470e-6, 0.2, NOW + 1),
    )
    connection.commit()
    connection.close()


def test_initialize_migrates_v1_measurements_to_esr_tool_key_without_data_loss(tmp_path: Path) -> None:
    path = tmp_path / "measurements.sqlite3"
    _create_v1_database(path)

    initialize_database(path, clock=lambda: NOW + 100)

    connection = open_database(path)
    try:
        assert connection.execute("SELECT schema_version FROM schema_meta").fetchone()[0] == CURRENT_SCHEMA_VERSION == 2
        row = connection.execute("SELECT tool_key, capacitance_f, esr_ohm FROM measurements").fetchone()
        assert tuple(row) == ("ESR_CAPACITOR", 470e-6, 0.2)
        assert connection.execute("SELECT COUNT(*) FROM measurements").fetchone()[0] == 1
    finally:
        connection.close()


def test_new_measurement_defaults_to_esr_capacitor_and_history_can_filter_by_tool(tmp_path: Path) -> None:
    service = StorageService(tmp_path / "measurements.sqlite3", clock=lambda: NOW)
    service.initialize()
    model = service.create_component_model(manufacturer="Test")
    sample = service.create_component_sample(component_model_id=model.id, sample_state="UNKNOWN")
    session = service.create_measurement_session(component_sample_id=sample.id, started_at_ms=NOW)
    measurement = service.create_measurement(
        measurement_session_id=session.id,
        measured_at_ms=NOW + 1,
        measurement_method="EX_SITU",
    )

    assert measurement.tool_key == "ESR_CAPACITOR"
    rows = service.list_measurements({"tool_key": "ESR_CAPACITOR"})
    assert [item["measurement"].id for item in rows] == [measurement.id]
    assert service.list_measurements({"tool_key": "RESISTOR"}) == []
