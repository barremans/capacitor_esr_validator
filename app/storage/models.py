"""
================================================================================
Module:     app/storage/models.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Immutable Python-modellen voor de zeven storage-entiteiten van
            SQLite schema v1 en de expliciet goedgekeurde enumwaarden.

            De modellen bevatten uitsluitend persistente data. Ze voeren geen
            ESR-beoordeling, referentieselectie of verborgen meetcorrecties uit.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste versie voor schema v1: schema_meta,
                        component_models, component_samples,
                        measurement_sessions, measurements,
                        assessment_snapshots en reference_snapshots.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SampleState(str, Enum):
    """Goedgekeurde toestanden van een fysiek componentsample."""

    NEW = "NEW"
    NOS_UNKNOWN_AGE = "NOS_UNKNOWN_AGE"
    USED_WORKING = "USED_WORKING"
    USED_UNKNOWN = "USED_UNKNOWN"
    SUSPECT = "SUSPECT"
    FAILED_CONFIRMED = "FAILED_CONFIRMED"
    REFERENCE_SAMPLE = "REFERENCE_SAMPLE"
    UNKNOWN = "UNKNOWN"


class MeasurementMethod(str, Enum):
    """Ondersteunde meetcontexten voor een meetrun."""

    EX_SITU = "EX_SITU"
    ONE_LEG = "ONE_LEG"
    IN_CIRCUIT = "IN_CIRCUIT"


@dataclass(frozen=True, slots=True)
class SchemaMeta:
    """Persistente schemaversie en schema-timestamps."""

    schema_version: int
    created_at_ms: int
    last_migrated_at_ms: int


@dataclass(frozen=True, slots=True)
class ComponentModel:
    """Componenttype/model; geen fysiek exemplaar."""

    id: int
    manufacturer: str | None
    series: str | None
    part_number: str | None
    technology: str | None
    nominal_capacitance_f: float | None
    nominal_capacitance_value: float | None
    nominal_capacitance_unit: str | None
    rated_voltage_v: float | None
    voltage_type: str | None
    tolerance_lower_pct: float | None
    tolerance_upper_pct: float | None
    temperature_min_c: float | None
    temperature_max_c: float | None
    case_size: str | None
    notes: str | None
    created_at_ms: int


@dataclass(frozen=True, slots=True)
class ComponentSample:
    """Fysiek exemplaar van een componentmodel."""

    id: int
    component_model_id: int
    sample_code: str | None
    sample_state: SampleState
    source: str | None
    batch_lot_code: str | None
    date_code: str | None
    visual_condition: str | None
    notes: str | None
    created_at_ms: int


@dataclass(frozen=True, slots=True)
class MeasurementSession:
    """Groepeert samenhangende meetruns van hetzelfde fysieke sample."""

    id: int
    component_sample_id: int
    started_at_ms: int
    ended_at_ms: int | None
    operator_name: str | None
    customer: str | None
    project: str | None
    installation: str | None
    module_board: str | None
    component_reference: str | None
    notes: str | None
    created_at_ms: int


@dataclass(frozen=True, slots=True)
class Measurement:
    """Ruwe meetdata en meetcontext van één meetrun."""

    id: int
    measurement_session_id: int
    measured_at_ms: int
    measurement_method: MeasurementMethod
    instrument_key: str | None
    instrument_name: str | None
    instrument_profile_version: str | None
    frequency_hz: float | None
    test_voltage_vrms: float | None
    temperature_c: float | None
    power_off_confirmed: bool | None
    discharged_confirmed: bool | None
    residual_voltage_before_v: float | None
    residual_voltage_after_v: float | None
    capacitance_f: float | None
    esr_ohm: float | None
    dissipation_factor_d: float | None
    quality_factor_q: float | None
    impedance_z_ohm: float | None
    reactance_x_ohm: float | None
    out_of_range: bool
    open_suspected: bool
    short_suspected: bool
    unstable_reading: bool
    parallel_components_notes: str | None
    mechanical_condition_notes: str | None
    notes: str | None
    record_status: str | None
    supersedes_measurement_id: int | None
    invalid_reason: str | None
    created_at_ms: int


@dataclass(frozen=True, slots=True)
class AssessmentSnapshot:
    """Immutable snapshot van een assessment voor één measurement."""

    id: int
    measurement_id: int
    assessed_at_ms: int
    engine_version: str | None
    capacitance_status: str | None
    capacitance_deviation_pct: float | None
    esr_status: str | None
    esr_factor: float | None
    consistency_status: str | None
    derived_esr_from_d_ohm: float | None
    reliability_level: str | None
    final_status: str | None
    reasons_json: str | None
    warnings_json: str | None
    advice_json: str | None
    created_at_ms: int


@dataclass(frozen=True, slots=True)
class ReferenceSnapshot:
    """Immutable snapshot van de werkelijk gebruikte technische referentie."""

    id: int
    assessment_snapshot_id: int
    reference_role: str | None
    reference_level: str | None
    reference_type: str | None
    manufacturer: str | None
    series: str | None
    part_number: str | None
    reference_value: float | None
    reference_unit: str | None
    frequency_hz: float | None
    temperature_c: float | None
    test_voltage_vrms: float | None
    dc_bias_v: float | None
    value_kind: str | None
    source_name: str | None
    source_document: str | None
    source_version: str | None
    source_data_version: str | None
    source_entry_id: str | None
    source_hash: str | None
    snapshot_json: str | None
    created_at_ms: int
