"""
================================================================================
Module:     app/storage/service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Publieke storage-service voor de lokale SQLite-meethistoriek.

            Biedt create/read-operaties voor de zeven hoofdtabellen, een
            transactionele save_new_measurement_chain(), structurele validatie
            en read-only historiekqueries. De service bevat geen GUI-code,
            assessmentberekeningen of referentieselectielogica en wijzigt ruwe
            meetwaarden niet.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste StorageService met CRUD-create/read, transactionele
                        volledige meetketen, structurele validatie en historiek-
                        filters volgens het goedgekeurde v1-contract.
  v1.1.0 (2026-10-01)  tool_key toegevoegd aan measurements en historiekfilter.
                        Bestaande callers blijven ESR_CAPACITOR als default krijgen.
================================================================================
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict
import math
from pathlib import Path
import sqlite3
from typing import Any

from .database import initialize_database, open_database, utc_now_ms
from .exceptions import (
    RelatedRecordNotFoundError,
    StorageError,
    StorageIntegrityError,
    StorageValidationError,
    StoredDataFormatError,
)
from .schema import DEFAULT_TOOL_KEY
from .models import (
    AssessmentSnapshot,
    ComponentModel,
    ComponentSample,
    Measurement,
    MeasurementMethod,
    MeasurementSession,
    ReferenceSnapshot,
    SampleState,
)


_ALLOWED_HISTORY_FILTERS = {
    "tool_key",
    "manufacturer",
    "series",
    "part_number",
    "sample_state",
    "measurement_method",
    "instrument_key",
    "frequency_hz",
    "test_voltage_vrms",
    "final_status",
    "reliability_level",
    "measured_from_ms",
    "measured_to_ms",
}


class StorageService:
    """Storage-API voor meetdata, snapshots en read-only historiek."""

    def __init__(
        self,
        database_path: Path | str,
        *,
        clock: Callable[[], int] = utc_now_ms,
    ) -> None:
        self.database_path = Path(database_path)
        self._clock = clock

    def initialize(self) -> None:
        """Initialiseer/valideer de database via de centrale database-laag."""
        initialize_database(self.database_path, clock=self._clock)

    # ------------------------------------------------------------------
    # Create API
    # ------------------------------------------------------------------

    def create_component_model(
        self,
        *,
        manufacturer: str | None = None,
        series: str | None = None,
        part_number: str | None = None,
        technology: str | None = None,
        nominal_capacitance_f: float | None = None,
        nominal_capacitance_value: float | None = None,
        nominal_capacitance_unit: str | None = None,
        rated_voltage_v: float | None = None,
        voltage_type: str | None = None,
        tolerance_lower_pct: float | None = None,
        tolerance_upper_pct: float | None = None,
        temperature_min_c: float | None = None,
        temperature_max_c: float | None = None,
        case_size: str | None = None,
        notes: str | None = None,
    ) -> ComponentModel:
        values = {
            "manufacturer": manufacturer,
            "series": series,
            "part_number": part_number,
            "technology": technology,
            "nominal_capacitance_f": self._finite_nonnegative(
                "nominal_capacitance_f", nominal_capacitance_f
            ),
            "nominal_capacitance_value": self._finite_nonnegative(
                "nominal_capacitance_value", nominal_capacitance_value
            ),
            "nominal_capacitance_unit": nominal_capacitance_unit,
            "rated_voltage_v": self._finite_nonnegative(
                "rated_voltage_v", rated_voltage_v
            ),
            "voltage_type": voltage_type,
            "tolerance_lower_pct": self._finite_optional(
                "tolerance_lower_pct", tolerance_lower_pct
            ),
            "tolerance_upper_pct": self._finite_optional(
                "tolerance_upper_pct", tolerance_upper_pct
            ),
            "temperature_min_c": self._finite_optional(
                "temperature_min_c", temperature_min_c
            ),
            "temperature_max_c": self._finite_optional(
                "temperature_max_c", temperature_max_c
            ),
            "case_size": case_size,
            "notes": notes,
            "created_at_ms": self._now_ms(),
        }
        return self._create_one(self._insert_component_model, values)

    def create_component_sample(
        self,
        *,
        component_model_id: int,
        sample_state: SampleState | str,
        sample_code: str | None = None,
        source: str | None = None,
        batch_lot_code: str | None = None,
        date_code: str | None = None,
        visual_condition: str | None = None,
        notes: str | None = None,
    ) -> ComponentSample:
        values = {
            "component_model_id": self._positive_id(
                "component_model_id", component_model_id
            ),
            "sample_code": sample_code,
            "sample_state": self._sample_state(sample_state).value,
            "source": source,
            "batch_lot_code": batch_lot_code,
            "date_code": date_code,
            "visual_condition": visual_condition,
            "notes": notes,
            "created_at_ms": self._now_ms(),
        }
        return self._create_one(self._insert_component_sample, values)

    def create_measurement_session(
        self,
        *,
        component_sample_id: int,
        started_at_ms: int,
        ended_at_ms: int | None = None,
        operator_name: str | None = None,
        customer: str | None = None,
        project: str | None = None,
        installation: str | None = None,
        module_board: str | None = None,
        component_reference: str | None = None,
        notes: str | None = None,
    ) -> MeasurementSession:
        started_at_ms = self._epoch_ms("started_at_ms", started_at_ms)
        ended_at_ms = self._epoch_ms_optional("ended_at_ms", ended_at_ms)
        if ended_at_ms is not None and ended_at_ms < started_at_ms:
            raise StorageValidationError(
                "ended_at_ms mag niet vóór started_at_ms liggen."
            )
        values = {
            "component_sample_id": self._positive_id(
                "component_sample_id", component_sample_id
            ),
            "started_at_ms": started_at_ms,
            "ended_at_ms": ended_at_ms,
            "operator_name": operator_name,
            "customer": customer,
            "project": project,
            "installation": installation,
            "module_board": module_board,
            "component_reference": component_reference,
            "notes": notes,
            "created_at_ms": self._now_ms(),
        }
        return self._create_one(self._insert_measurement_session, values)

    def create_measurement(
        self,
        *,
        measurement_session_id: int,
        measured_at_ms: int,
        measurement_method: MeasurementMethod | str,
        tool_key: str = DEFAULT_TOOL_KEY,
        instrument_key: str | None = None,
        instrument_name: str | None = None,
        instrument_profile_version: str | None = None,
        frequency_hz: float | None = None,
        test_voltage_vrms: float | None = None,
        temperature_c: float | None = None,
        power_off_confirmed: bool | None = None,
        discharged_confirmed: bool | None = None,
        residual_voltage_before_v: float | None = None,
        residual_voltage_after_v: float | None = None,
        capacitance_f: float | None = None,
        esr_ohm: float | None = None,
        dissipation_factor_d: float | None = None,
        quality_factor_q: float | None = None,
        impedance_z_ohm: float | None = None,
        reactance_x_ohm: float | None = None,
        out_of_range: bool = False,
        open_suspected: bool = False,
        short_suspected: bool = False,
        unstable_reading: bool = False,
        parallel_components_notes: str | None = None,
        mechanical_condition_notes: str | None = None,
        notes: str | None = None,
        record_status: str | None = None,
        supersedes_measurement_id: int | None = None,
        invalid_reason: str | None = None,
    ) -> Measurement:
        values = self._validated_measurement_values(
            measurement_session_id=measurement_session_id,
            measured_at_ms=measured_at_ms,
            measurement_method=measurement_method,
            tool_key=tool_key,
            instrument_key=instrument_key,
            instrument_name=instrument_name,
            instrument_profile_version=instrument_profile_version,
            frequency_hz=frequency_hz,
            test_voltage_vrms=test_voltage_vrms,
            temperature_c=temperature_c,
            power_off_confirmed=power_off_confirmed,
            discharged_confirmed=discharged_confirmed,
            residual_voltage_before_v=residual_voltage_before_v,
            residual_voltage_after_v=residual_voltage_after_v,
            capacitance_f=capacitance_f,
            esr_ohm=esr_ohm,
            dissipation_factor_d=dissipation_factor_d,
            quality_factor_q=quality_factor_q,
            impedance_z_ohm=impedance_z_ohm,
            reactance_x_ohm=reactance_x_ohm,
            out_of_range=out_of_range,
            open_suspected=open_suspected,
            short_suspected=short_suspected,
            unstable_reading=unstable_reading,
            parallel_components_notes=parallel_components_notes,
            mechanical_condition_notes=mechanical_condition_notes,
            notes=notes,
            record_status=record_status,
            supersedes_measurement_id=supersedes_measurement_id,
            invalid_reason=invalid_reason,
            created_at_ms=self._now_ms(),
        )
        return self._create_one(self._insert_measurement, values)

    def create_assessment_snapshot(
        self,
        *,
        measurement_id: int,
        assessed_at_ms: int,
        engine_version: str | None = None,
        capacitance_status: str | None = None,
        capacitance_deviation_pct: float | None = None,
        esr_status: str | None = None,
        esr_factor: float | None = None,
        consistency_status: str | None = None,
        derived_esr_from_d_ohm: float | None = None,
        reliability_level: str | None = None,
        final_status: str | None = None,
        reasons_json: str | None = None,
        warnings_json: str | None = None,
        advice_json: str | None = None,
    ) -> AssessmentSnapshot:
        values = {
            "measurement_id": self._positive_id("measurement_id", measurement_id),
            "assessed_at_ms": self._epoch_ms("assessed_at_ms", assessed_at_ms),
            "engine_version": engine_version,
            "capacitance_status": capacitance_status,
            "capacitance_deviation_pct": self._finite_optional(
                "capacitance_deviation_pct", capacitance_deviation_pct
            ),
            "esr_status": esr_status,
            "esr_factor": self._finite_optional("esr_factor", esr_factor),
            "consistency_status": consistency_status,
            "derived_esr_from_d_ohm": self._finite_nonnegative(
                "derived_esr_from_d_ohm", derived_esr_from_d_ohm
            ),
            "reliability_level": reliability_level,
            "final_status": final_status,
            "reasons_json": reasons_json,
            "warnings_json": warnings_json,
            "advice_json": advice_json,
            "created_at_ms": self._now_ms(),
        }
        return self._create_one(self._insert_assessment_snapshot, values)

    def create_reference_snapshot(
        self,
        *,
        assessment_snapshot_id: int,
        reference_role: str | None = None,
        reference_level: str | None = None,
        reference_type: str | None = None,
        manufacturer: str | None = None,
        series: str | None = None,
        part_number: str | None = None,
        reference_value: float | None = None,
        reference_unit: str | None = None,
        frequency_hz: float | None = None,
        temperature_c: float | None = None,
        test_voltage_vrms: float | None = None,
        dc_bias_v: float | None = None,
        value_kind: str | None = None,
        source_name: str | None = None,
        source_document: str | None = None,
        source_version: str | None = None,
        source_data_version: str | None = None,
        source_entry_id: str | None = None,
        source_hash: str | None = None,
        snapshot_json: str | None = None,
    ) -> ReferenceSnapshot:
        values = {
            "assessment_snapshot_id": self._positive_id(
                "assessment_snapshot_id", assessment_snapshot_id
            ),
            "reference_role": reference_role,
            "reference_level": reference_level,
            "reference_type": reference_type,
            "manufacturer": manufacturer,
            "series": series,
            "part_number": part_number,
            "reference_value": self._finite_optional(
                "reference_value", reference_value
            ),
            "reference_unit": reference_unit,
            "frequency_hz": self._finite_positive("frequency_hz", frequency_hz),
            "temperature_c": self._finite_optional(
                "temperature_c", temperature_c
            ),
            "test_voltage_vrms": self._finite_nonnegative(
                "test_voltage_vrms", test_voltage_vrms
            ),
            "dc_bias_v": self._finite_optional("dc_bias_v", dc_bias_v),
            "value_kind": value_kind,
            "source_name": source_name,
            "source_document": source_document,
            "source_version": source_version,
            "source_data_version": source_data_version,
            "source_entry_id": source_entry_id,
            "source_hash": source_hash,
            "snapshot_json": snapshot_json,
            "created_at_ms": self._now_ms(),
        }
        return self._create_one(self._insert_reference_snapshot, values)

    def save_new_measurement_chain(
        self,
        *,
        component_model: Mapping[str, Any],
        component_sample: Mapping[str, Any],
        measurement_session: Mapping[str, Any],
        measurement: Mapping[str, Any],
        assessment_snapshot: Mapping[str, Any],
        reference_snapshots: Sequence[Mapping[str, Any]] = (),
    ) -> dict[str, Any]:
        """Sla model→sample→session→measurement→assessment→references atomair op."""
        # Valideer en normaliseer eerst alles wat onafhankelijk van database-ID's is.
        model_values = self._component_model_mapping(component_model)
        sample_values = self._component_sample_mapping(component_sample)
        session_values = self._measurement_session_mapping(measurement_session)
        measurement_values = self._measurement_mapping(measurement)
        assessment_values = self._assessment_mapping(assessment_snapshot)
        reference_values = [self._reference_mapping(item) for item in reference_snapshots]

        connection = open_database(self.database_path)
        try:
            connection.execute("BEGIN IMMEDIATE")

            model = self._insert_component_model(connection, model_values)
            sample_values["component_model_id"] = model.id
            sample = self._insert_component_sample(connection, sample_values)

            session_values["component_sample_id"] = sample.id
            session = self._insert_measurement_session(connection, session_values)

            measurement_values["measurement_session_id"] = session.id
            measurement_obj = self._insert_measurement(connection, measurement_values)

            assessment_values["measurement_id"] = measurement_obj.id
            assessment = self._insert_assessment_snapshot(connection, assessment_values)

            references: list[ReferenceSnapshot] = []
            for values in reference_values:
                values["assessment_snapshot_id"] = assessment.id
                references.append(self._insert_reference_snapshot(connection, values))

            connection.commit()
            return {
                "component_model": model,
                "component_sample": sample,
                "measurement_session": session,
                "measurement": measurement_obj,
                "assessment_snapshot": assessment,
                "reference_snapshots": tuple(references),
            }
        except StorageError:
            connection.rollback()
            raise
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            raise StorageIntegrityError(
                "De volledige meetketen schendt een database-integriteitsregel."
            ) from exc
        except sqlite3.Error as exc:
            connection.rollback()
            raise StorageError(
                "De volledige meetketen kon niet worden opgeslagen."
            ) from exc
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    # ------------------------------------------------------------------
    # Read API
    # ------------------------------------------------------------------

    def get_component_model(self, record_id: int) -> ComponentModel:
        return self._get_one("component_models", record_id, self._row_component_model)

    def get_component_sample(self, record_id: int) -> ComponentSample:
        return self._get_one("component_samples", record_id, self._row_component_sample)

    def get_measurement_session(self, record_id: int) -> MeasurementSession:
        return self._get_one(
            "measurement_sessions", record_id, self._row_measurement_session
        )

    def get_measurement(self, record_id: int) -> Measurement:
        return self._get_one("measurements", record_id, self._row_measurement)

    def get_assessment_snapshots_for_measurement(
        self,
        measurement_id: int,
    ) -> list[AssessmentSnapshot]:
        measurement_id = self._positive_id("measurement_id", measurement_id)
        rows = self._fetchall(
            """
            SELECT *
            FROM assessment_snapshots
            WHERE measurement_id = ?
            ORDER BY assessed_at_ms DESC, id DESC
            """,
            (measurement_id,),
        )
        return [self._row_assessment_snapshot(row) for row in rows]

    def get_reference_snapshots_for_assessment(
        self,
        assessment_snapshot_id: int,
    ) -> list[ReferenceSnapshot]:
        assessment_snapshot_id = self._positive_id(
            "assessment_snapshot_id", assessment_snapshot_id
        )
        rows = self._fetchall(
            """
            SELECT *
            FROM reference_snapshots
            WHERE assessment_snapshot_id = ?
            ORDER BY id ASC
            """,
            (assessment_snapshot_id,),
        )
        return [self._row_reference_snapshot(row) for row in rows]

    def get_measurement_detail(self, measurement_id: int) -> dict[str, Any]:
        measurement = self.get_measurement(measurement_id)
        session = self.get_measurement_session(measurement.measurement_session_id)
        sample = self.get_component_sample(session.component_sample_id)
        model = self.get_component_model(sample.component_model_id)
        assessments = self.get_assessment_snapshots_for_measurement(measurement.id)
        references = {
            item.id: self.get_reference_snapshots_for_assessment(item.id)
            for item in assessments
        }
        return {
            "component_model": model,
            "component_sample": sample,
            "measurement_session": session,
            "measurement": measurement,
            "assessment_snapshots": assessments,
            "reference_snapshots_by_assessment_id": references,
        }

    def list_measurements(
        self,
        filters: Mapping[str, Any] | None = None,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Geef read-only historiek met de nieuwste assessment-snapshot per run."""
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise StorageValidationError("limit moet een positieve integer zijn.")
        if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
            raise StorageValidationError("offset moet een niet-negatieve integer zijn.")

        filters = {} if filters is None else dict(filters)
        unknown = set(filters) - _ALLOWED_HISTORY_FILTERS
        if unknown:
            raise StorageValidationError(
                "Onbekende historiekfilter(s): " + ", ".join(sorted(unknown))
            )

        clauses: list[str] = []
        parameters: list[Any] = []

        direct_filters = {
            "tool_key": "m.tool_key",
            "manufacturer": "cm.manufacturer",
            "series": "cm.series",
            "part_number": "cm.part_number",
            "sample_state": "cs.sample_state",
            "measurement_method": "m.measurement_method",
            "instrument_key": "m.instrument_key",
            "frequency_hz": "m.frequency_hz",
            "test_voltage_vrms": "m.test_voltage_vrms",
            "final_status": "a.final_status",
            "reliability_level": "a.reliability_level",
        }
        for key, column in direct_filters.items():
            if key in filters and filters[key] is not None:
                value = filters[key]
                if key == "sample_state":
                    value = self._sample_state(value).value
                elif key == "measurement_method":
                    value = self._measurement_method(value).value
                elif key in {"frequency_hz", "test_voltage_vrms"}:
                    value = self._finite_optional(key, value)
                clauses.append(f"{column} = ?")
                parameters.append(value)

        if filters.get("measured_from_ms") is not None:
            clauses.append("m.measured_at_ms >= ?")
            parameters.append(
                self._epoch_ms("measured_from_ms", filters["measured_from_ms"])
            )
        if filters.get("measured_to_ms") is not None:
            clauses.append("m.measured_at_ms <= ?")
            parameters.append(
                self._epoch_ms("measured_to_ms", filters["measured_to_ms"])
            )

        where_sql = ""
        if clauses:
            where_sql = "WHERE " + " AND ".join(clauses)

        sql = f"""
            SELECT
                m.*,
                cm.manufacturer AS model_manufacturer,
                cm.series AS model_series,
                cm.part_number AS model_part_number,
                cs.sample_state AS sample_state,
                a.id AS latest_assessment_id,
                a.assessed_at_ms AS latest_assessed_at_ms,
                a.final_status AS final_status,
                a.reliability_level AS reliability_level
            FROM measurements AS m
            JOIN measurement_sessions AS ms ON ms.id = m.measurement_session_id
            JOIN component_samples AS cs ON cs.id = ms.component_sample_id
            JOIN component_models AS cm ON cm.id = cs.component_model_id
            LEFT JOIN assessment_snapshots AS a
              ON a.id = (
                  SELECT a2.id
                  FROM assessment_snapshots AS a2
                  WHERE a2.measurement_id = m.id
                  ORDER BY a2.assessed_at_ms DESC, a2.id DESC
                  LIMIT 1
              )
            {where_sql}
            ORDER BY m.measured_at_ms DESC, m.id DESC
            LIMIT ? OFFSET ?
        """
        parameters.extend((limit, offset))
        rows = self._fetchall(sql, tuple(parameters))

        result: list[dict[str, Any]] = []
        for row in rows:
            measurement = self._row_measurement(row)
            result.append(
                {
                    "measurement": measurement,
                    "manufacturer": row["model_manufacturer"],
                    "series": row["model_series"],
                    "part_number": row["model_part_number"],
                    "sample_state": self._sample_state_from_storage(row["sample_state"]),
                    "latest_assessment_id": row["latest_assessment_id"],
                    "latest_assessed_at_ms": row["latest_assessed_at_ms"],
                    "final_status": row["final_status"],
                    "reliability_level": row["reliability_level"],
                }
            )
        return result

    # ------------------------------------------------------------------
    # Insert helpers: gebruiken een bestaande connection; geen transacties.
    # ------------------------------------------------------------------

    def _insert_component_model(
        self,
        connection: sqlite3.Connection,
        values: Mapping[str, Any],
    ) -> ComponentModel:
        record_id = self._insert(connection, "component_models", values)
        return self._get_one_on_connection(
            connection, "component_models", record_id, self._row_component_model
        )

    def _insert_component_sample(
        self,
        connection: sqlite3.Connection,
        values: Mapping[str, Any],
    ) -> ComponentSample:
        self._require_exists(connection, "component_models", values["component_model_id"])
        record_id = self._insert(connection, "component_samples", values)
        return self._get_one_on_connection(
            connection, "component_samples", record_id, self._row_component_sample
        )

    def _insert_measurement_session(
        self,
        connection: sqlite3.Connection,
        values: Mapping[str, Any],
    ) -> MeasurementSession:
        self._require_exists(connection, "component_samples", values["component_sample_id"])
        record_id = self._insert(connection, "measurement_sessions", values)
        return self._get_one_on_connection(
            connection, "measurement_sessions", record_id, self._row_measurement_session
        )

    def _insert_measurement(
        self,
        connection: sqlite3.Connection,
        values: Mapping[str, Any],
    ) -> Measurement:
        self._require_exists(
            connection, "measurement_sessions", values["measurement_session_id"]
        )
        supersedes = values.get("supersedes_measurement_id")
        if supersedes is not None:
            self._require_exists(connection, "measurements", supersedes)
        record_id = self._insert(connection, "measurements", values)
        return self._get_one_on_connection(
            connection, "measurements", record_id, self._row_measurement
        )

    def _insert_assessment_snapshot(
        self,
        connection: sqlite3.Connection,
        values: Mapping[str, Any],
    ) -> AssessmentSnapshot:
        self._require_exists(connection, "measurements", values["measurement_id"])
        record_id = self._insert(connection, "assessment_snapshots", values)
        return self._get_one_on_connection(
            connection, "assessment_snapshots", record_id, self._row_assessment_snapshot
        )

    def _insert_reference_snapshot(
        self,
        connection: sqlite3.Connection,
        values: Mapping[str, Any],
    ) -> ReferenceSnapshot:
        self._require_exists(
            connection, "assessment_snapshots", values["assessment_snapshot_id"]
        )
        record_id = self._insert(connection, "reference_snapshots", values)
        return self._get_one_on_connection(
            connection, "reference_snapshots", record_id, self._row_reference_snapshot
        )

    # ------------------------------------------------------------------
    # Mapping helpers voor transactionele chain.
    # FK's in de aangeleverde mappings worden bewust genegeerd/overschreven.
    # ------------------------------------------------------------------

    def _component_model_mapping(self, data: Mapping[str, Any]) -> dict[str, Any]:
        allowed = {
            "manufacturer", "series", "part_number", "technology",
            "nominal_capacitance_f", "nominal_capacitance_value",
            "nominal_capacitance_unit", "rated_voltage_v", "voltage_type",
            "tolerance_lower_pct", "tolerance_upper_pct", "temperature_min_c",
            "temperature_max_c", "case_size", "notes",
        }
        self._reject_unknown_mapping_keys("component_model", data, allowed)
        values = dict(data)
        values["nominal_capacitance_f"] = self._finite_nonnegative(
            "nominal_capacitance_f", values.get("nominal_capacitance_f")
        )
        values["nominal_capacitance_value"] = self._finite_nonnegative(
            "nominal_capacitance_value", values.get("nominal_capacitance_value")
        )
        values["rated_voltage_v"] = self._finite_nonnegative(
            "rated_voltage_v", values.get("rated_voltage_v")
        )
        for key in (
            "tolerance_lower_pct", "tolerance_upper_pct",
            "temperature_min_c", "temperature_max_c",
        ):
            values[key] = self._finite_optional(key, values.get(key))
        values["created_at_ms"] = self._now_ms()
        return values

    def _component_sample_mapping(self, data: Mapping[str, Any]) -> dict[str, Any]:
        allowed = {
            "sample_code", "sample_state", "source", "batch_lot_code", "date_code",
            "visual_condition", "notes", "component_model_id",
        }
        self._reject_unknown_mapping_keys("component_sample", data, allowed)
        values = {key: value for key, value in data.items() if key != "component_model_id"}
        if "sample_state" not in values:
            raise StorageValidationError("component_sample.sample_state is verplicht.")
        values["sample_state"] = self._sample_state(values["sample_state"]).value
        values["created_at_ms"] = self._now_ms()
        return values

    def _measurement_session_mapping(self, data: Mapping[str, Any]) -> dict[str, Any]:
        allowed = {
            "component_sample_id", "started_at_ms", "ended_at_ms", "operator_name",
            "customer", "project", "installation", "module_board",
            "component_reference", "notes",
        }
        self._reject_unknown_mapping_keys("measurement_session", data, allowed)
        values = {key: value for key, value in data.items() if key != "component_sample_id"}
        if "started_at_ms" not in values:
            raise StorageValidationError("measurement_session.started_at_ms is verplicht.")
        values["started_at_ms"] = self._epoch_ms("started_at_ms", values["started_at_ms"])
        values["ended_at_ms"] = self._epoch_ms_optional(
            "ended_at_ms", values.get("ended_at_ms")
        )
        if (
            values["ended_at_ms"] is not None
            and values["ended_at_ms"] < values["started_at_ms"]
        ):
            raise StorageValidationError(
                "ended_at_ms mag niet vóór started_at_ms liggen."
            )
        values["created_at_ms"] = self._now_ms()
        return values

    def _measurement_mapping(self, data: Mapping[str, Any]) -> dict[str, Any]:
        allowed = {
            "measurement_session_id", "measured_at_ms", "measurement_method", "tool_key",
            "instrument_key", "instrument_name", "instrument_profile_version",
            "frequency_hz", "test_voltage_vrms", "temperature_c",
            "power_off_confirmed", "discharged_confirmed",
            "residual_voltage_before_v", "residual_voltage_after_v", "capacitance_f",
            "esr_ohm", "dissipation_factor_d", "quality_factor_q",
            "impedance_z_ohm", "reactance_x_ohm", "out_of_range", "open_suspected",
            "short_suspected", "unstable_reading", "parallel_components_notes",
            "mechanical_condition_notes", "notes", "record_status",
            "supersedes_measurement_id", "invalid_reason",
        }
        self._reject_unknown_mapping_keys("measurement", data, allowed)
        values = {key: value for key, value in data.items() if key != "measurement_session_id"}
        if "measured_at_ms" not in values or "measurement_method" not in values:
            raise StorageValidationError(
                "measurement.measured_at_ms en measurement_method zijn verplicht."
            )
        values["measurement_session_id"] = 1  # tijdelijk; wordt in transactie overschreven
        values.setdefault("tool_key", DEFAULT_TOOL_KEY)
        values["created_at_ms"] = self._now_ms()
        return self._validated_measurement_values(**values)

    def _assessment_mapping(self, data: Mapping[str, Any]) -> dict[str, Any]:
        allowed = {
            "measurement_id", "assessed_at_ms", "engine_version", "capacitance_status",
            "capacitance_deviation_pct", "esr_status", "esr_factor",
            "consistency_status", "derived_esr_from_d_ohm", "reliability_level",
            "final_status", "reasons_json", "warnings_json", "advice_json",
        }
        self._reject_unknown_mapping_keys("assessment_snapshot", data, allowed)
        values = {key: value for key, value in data.items() if key != "measurement_id"}
        if "assessed_at_ms" not in values:
            raise StorageValidationError("assessment_snapshot.assessed_at_ms is verplicht.")
        values["measurement_id"] = 1  # tijdelijk; wordt in transactie overschreven
        values["assessed_at_ms"] = self._epoch_ms("assessed_at_ms", values["assessed_at_ms"])
        values["capacitance_deviation_pct"] = self._finite_optional(
            "capacitance_deviation_pct", values.get("capacitance_deviation_pct")
        )
        values["esr_factor"] = self._finite_optional("esr_factor", values.get("esr_factor"))
        values["derived_esr_from_d_ohm"] = self._finite_nonnegative(
            "derived_esr_from_d_ohm", values.get("derived_esr_from_d_ohm")
        )
        values["created_at_ms"] = self._now_ms()
        return values

    def _reference_mapping(self, data: Mapping[str, Any]) -> dict[str, Any]:
        allowed = {
            "assessment_snapshot_id", "reference_role", "reference_level",
            "reference_type", "manufacturer", "series", "part_number",
            "reference_value", "reference_unit", "frequency_hz", "temperature_c",
            "test_voltage_vrms", "dc_bias_v", "value_kind", "source_name",
            "source_document", "source_version", "source_data_version",
            "source_entry_id", "source_hash", "snapshot_json",
        }
        self._reject_unknown_mapping_keys("reference_snapshot", data, allowed)
        values = {key: value for key, value in data.items() if key != "assessment_snapshot_id"}
        values["reference_value"] = self._finite_optional(
            "reference_value", values.get("reference_value")
        )
        values["frequency_hz"] = self._finite_positive(
            "frequency_hz", values.get("frequency_hz")
        )
        values["temperature_c"] = self._finite_optional(
            "temperature_c", values.get("temperature_c")
        )
        values["test_voltage_vrms"] = self._finite_nonnegative(
            "test_voltage_vrms", values.get("test_voltage_vrms")
        )
        values["dc_bias_v"] = self._finite_optional("dc_bias_v", values.get("dc_bias_v"))
        values["created_at_ms"] = self._now_ms()
        return values

    # ------------------------------------------------------------------
    # Low-level database helpers.
    # ------------------------------------------------------------------

    def _create_one(self, inserter: Callable[..., Any], values: Mapping[str, Any]) -> Any:
        connection = open_database(self.database_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            result = inserter(connection, values)
            connection.commit()
            return result
        except StorageError:
            connection.rollback()
            raise
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            raise StorageIntegrityError(
                "De record schendt een database-integriteitsregel."
            ) from exc
        except sqlite3.Error as exc:
            connection.rollback()
            raise StorageError("De databasebewerking is mislukt.") from exc
        finally:
            connection.close()

    @staticmethod
    def _insert(
        connection: sqlite3.Connection,
        table_name: str,
        values: Mapping[str, Any],
    ) -> int:
        columns = tuple(values.keys())
        placeholders = ", ".join("?" for _ in columns)
        sql = (
            f"INSERT INTO {table_name} ({', '.join(columns)}) "
            f"VALUES ({placeholders})"
        )
        cursor = connection.execute(sql, tuple(values[column] for column in columns))
        if cursor.lastrowid is None:
            raise StorageIntegrityError("SQLite gaf geen record-ID terug.")
        return int(cursor.lastrowid)

    @staticmethod
    def _require_exists(
        connection: sqlite3.Connection,
        table_name: str,
        record_id: Any,
    ) -> None:
        row = connection.execute(
            f"SELECT 1 FROM {table_name} WHERE id = ?",
            (record_id,),
        ).fetchone()
        if row is None:
            raise RelatedRecordNotFoundError(
                f"Gerelateerde record ontbreekt: {table_name} id={record_id}."
            )

    def _get_one(self, table_name: str, record_id: int, mapper: Callable[[sqlite3.Row], Any]) -> Any:
        record_id = self._positive_id("record_id", record_id)
        connection = open_database(self.database_path)
        try:
            return self._get_one_on_connection(connection, table_name, record_id, mapper)
        except sqlite3.Error as exc:
            raise StorageError("De databasebewerking is mislukt.") from exc
        finally:
            connection.close()

    @staticmethod
    def _get_one_on_connection(
        connection: sqlite3.Connection,
        table_name: str,
        record_id: int,
        mapper: Callable[[sqlite3.Row], Any],
    ) -> Any:
        row = connection.execute(
            f"SELECT * FROM {table_name} WHERE id = ?",
            (record_id,),
        ).fetchone()
        if row is None:
            raise RelatedRecordNotFoundError(
                f"Record ontbreekt: {table_name} id={record_id}."
            )
        return mapper(row)

    def _fetchall(self, sql: str, parameters: tuple[Any, ...]) -> list[sqlite3.Row]:
        connection = open_database(self.database_path)
        try:
            return list(connection.execute(sql, parameters).fetchall())
        except sqlite3.Error as exc:
            raise StorageError("De databasequery is mislukt.") from exc
        finally:
            connection.close()

    # ------------------------------------------------------------------
    # Row → immutable model.
    # ------------------------------------------------------------------

    @staticmethod
    def _row_component_model(row: sqlite3.Row) -> ComponentModel:
        return ComponentModel(**dict(row))

    @classmethod
    def _row_component_sample(cls, row: sqlite3.Row) -> ComponentSample:
        values = dict(row)
        values["sample_state"] = cls._sample_state_from_storage(values["sample_state"])
        return ComponentSample(**values)

    @staticmethod
    def _row_measurement_session(row: sqlite3.Row) -> MeasurementSession:
        return MeasurementSession(**dict(row))

    @classmethod
    def _row_measurement(cls, row: sqlite3.Row) -> Measurement:
        values = {key: row[key] for key in Measurement.__dataclass_fields__}
        values["measurement_method"] = cls._measurement_method_from_storage(
            values["measurement_method"]
        )
        for key in (
            "power_off_confirmed", "discharged_confirmed", "out_of_range",
            "open_suspected", "short_suspected", "unstable_reading",
        ):
            if values[key] is not None:
                values[key] = bool(values[key])
        return Measurement(**values)

    @staticmethod
    def _row_assessment_snapshot(row: sqlite3.Row) -> AssessmentSnapshot:
        values = {key: row[key] for key in AssessmentSnapshot.__dataclass_fields__}
        return AssessmentSnapshot(**values)

    @staticmethod
    def _row_reference_snapshot(row: sqlite3.Row) -> ReferenceSnapshot:
        values = {key: row[key] for key in ReferenceSnapshot.__dataclass_fields__}
        return ReferenceSnapshot(**values)

    # ------------------------------------------------------------------
    # Structurele validatie. Geen assessment-/diagnostische regels.
    # ------------------------------------------------------------------

    def _now_ms(self) -> int:
        return self._epoch_ms("clock", self._clock())

    @staticmethod
    def _positive_id(name: str, value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise StorageValidationError(f"{name} moet een positieve integer zijn.")
        return value

    @staticmethod
    def _epoch_ms(name: str, value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise StorageValidationError(
                f"{name} moet een niet-negatieve Unix epoch-ms integer zijn."
            )
        return value

    @classmethod
    def _epoch_ms_optional(cls, name: str, value: Any) -> int | None:
        if value is None:
            return None
        return cls._epoch_ms(name, value)

    @staticmethod
    def _finite_optional(name: str, value: Any) -> float | None:
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise StorageValidationError(f"{name} moet numeriek zijn.")
        numeric = float(value)
        if not math.isfinite(numeric):
            raise StorageValidationError(f"{name} moet een eindige numerieke waarde zijn.")
        return numeric

    @classmethod
    def _finite_nonnegative(cls, name: str, value: Any) -> float | None:
        numeric = cls._finite_optional(name, value)
        if numeric is not None and numeric < 0:
            raise StorageValidationError(f"{name} mag niet negatief zijn.")
        return numeric

    @classmethod
    def _finite_positive(cls, name: str, value: Any) -> float | None:
        numeric = cls._finite_optional(name, value)
        if numeric is not None and numeric <= 0:
            raise StorageValidationError(f"{name} moet groter dan nul zijn.")
        return numeric

    @staticmethod
    def _bool_optional(name: str, value: Any) -> bool | None:
        if value is None:
            return None
        if not isinstance(value, bool):
            raise StorageValidationError(f"{name} moet bool of None zijn.")
        return value

    @staticmethod
    def _bool_required(name: str, value: Any) -> bool:
        if not isinstance(value, bool):
            raise StorageValidationError(f"{name} moet bool zijn.")
        return value

    @staticmethod
    def _sample_state(value: SampleState | str) -> SampleState:
        try:
            return value if isinstance(value, SampleState) else SampleState(value)
        except (TypeError, ValueError) as exc:
            raise StorageValidationError("Ongeldige sample_state.") from exc

    @staticmethod
    def _measurement_method(value: MeasurementMethod | str) -> MeasurementMethod:
        try:
            return (
                value
                if isinstance(value, MeasurementMethod)
                else MeasurementMethod(value)
            )
        except (TypeError, ValueError) as exc:
            raise StorageValidationError("Ongeldige measurement_method.") from exc

    @staticmethod
    def _sample_state_from_storage(value: Any) -> SampleState:
        try:
            return SampleState(value)
        except (TypeError, ValueError) as exc:
            raise StoredDataFormatError("Ongeldige sample_state in database.") from exc

    @staticmethod
    def _measurement_method_from_storage(value: Any) -> MeasurementMethod:
        try:
            return MeasurementMethod(value)
        except (TypeError, ValueError) as exc:
            raise StoredDataFormatError(
                "Ongeldige measurement_method in database."
            ) from exc

    @staticmethod
    def _tool_key(value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise StorageValidationError("tool_key moet een niet-lege tekstwaarde zijn.")
        key = value.strip().upper()
        if any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_" for ch in key):
            raise StorageValidationError("tool_key mag alleen A-Z, 0-9 en underscore bevatten.")
        return key

    @classmethod
    def _validated_measurement_values(cls, **values: Any) -> dict[str, Any]:
        values = dict(values)
        values["measurement_session_id"] = cls._positive_id(
            "measurement_session_id", values["measurement_session_id"]
        )
        values["measured_at_ms"] = cls._epoch_ms(
            "measured_at_ms", values["measured_at_ms"]
        )
        values["measurement_method"] = cls._measurement_method(
            values["measurement_method"]
        ).value
        values["tool_key"] = cls._tool_key(values.get("tool_key", DEFAULT_TOOL_KEY))
        values["frequency_hz"] = cls._finite_positive(
            "frequency_hz", values.get("frequency_hz")
        )
        values["test_voltage_vrms"] = cls._finite_nonnegative(
            "test_voltage_vrms", values.get("test_voltage_vrms")
        )
        for key in (
            "temperature_c", "residual_voltage_before_v", "residual_voltage_after_v",
            "dissipation_factor_d", "quality_factor_q", "impedance_z_ohm",
            "reactance_x_ohm",
        ):
            values[key] = cls._finite_optional(key, values.get(key))
        values["capacitance_f"] = cls._finite_nonnegative(
            "capacitance_f", values.get("capacitance_f")
        )
        values["esr_ohm"] = cls._finite_nonnegative("esr_ohm", values.get("esr_ohm"))
        values["power_off_confirmed"] = cls._bool_optional(
            "power_off_confirmed", values.get("power_off_confirmed")
        )
        values["discharged_confirmed"] = cls._bool_optional(
            "discharged_confirmed", values.get("discharged_confirmed")
        )
        for key in ("out_of_range", "open_suspected", "short_suspected", "unstable_reading"):
            values[key] = cls._bool_required(key, values.get(key, False))
        supersedes = values.get("supersedes_measurement_id")
        if supersedes is not None:
            values["supersedes_measurement_id"] = cls._positive_id(
                "supersedes_measurement_id", supersedes
            )
        values["created_at_ms"] = cls._epoch_ms(
            "created_at_ms", values["created_at_ms"]
        )
        return values

    @staticmethod
    def _reject_unknown_mapping_keys(
        mapping_name: str,
        data: Mapping[str, Any],
        allowed: set[str],
    ) -> None:
        unknown = set(data) - allowed
        if unknown:
            raise StorageValidationError(
                f"Onbekende velden in {mapping_name}: " + ", ".join(sorted(unknown))
            )


def model_to_dict(model: Any) -> dict[str, Any]:
    """Kleine expliciete helper voor controllers/tests die een modelmapping nodig hebben."""
    return asdict(model)
