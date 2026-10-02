"""
================================================================================
Module:     app/helpers/history_detail_export.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.1
Datum:      2026-10-02
Auteur:     Bart Bossuyt

Doel:       Zet één volledige opgeslagen meetketen om naar een stabiele,
            machineleesbare detail-exportregel.

            De export gebruikt vaste niet-vertaalde kolomnamen, bewaart numerieke
            SI-waarden als numerieke waarden en dispatcht tool-specifieke velden
            expliciet via tool_key. Er wordt geen assessment opnieuw uitgevoerd.

Wijzigingen:
  v1.0.0 (2026-10-02)  Eerste multitool-ready detail-export; ESR_CAPACITOR heeft
                        eigen velden, onbekende tools behouden de gemeenschappelijke
                        meet-, assessment- en referentievelden.
  v1.0.1 (2026-10-02)  JSON-normalisatie uitgebreid voor eenvoudige record-objecten
                        met __dict__ (o.a. test SimpleNamespace); dataclasses en enums
                        blijven ongewijzigd ondersteund.
================================================================================
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
import json
from typing import Any


COMMON_DETAIL_HEADERS = [
    "measurement_id",
    "tool_key",
    "measured_at_ms",
    "measurement_session_id",
    "component_sample_id",
    "component_model_id",
    "manufacturer",
    "series",
    "part_number",
    "technology",
    "sample_code",
    "sample_state",
    "customer",
    "project",
    "installation",
    "module_board",
    "component_reference",
    "measurement_method",
    "instrument_key",
    "instrument_name",
    "instrument_profile_version",
    "frequency_hz",
    "test_voltage_vrms",
    "temperature_c",
    "power_off_confirmed",
    "discharged_confirmed",
    "residual_voltage_before_v",
    "residual_voltage_after_v",
    "out_of_range",
    "open_suspected",
    "short_suspected",
    "unstable_reading",
    "parallel_components_notes",
    "mechanical_condition_notes",
    "measurement_notes",
    "record_status",
    "supersedes_measurement_id",
    "invalid_reason",
    "assessment_count",
    "latest_assessment_id",
    "assessed_at_ms",
    "assessment_engine_version",
    "final_status",
    "reliability_level",
    "reasons_text",
    "warnings_text",
    "advice_text",
    "reasons_json",
    "warnings_json",
    "advice_json",
    "reference_count",
    "reference_role",
    "reference_level",
    "reference_type",
    "reference_manufacturer",
    "reference_series",
    "reference_part_number",
    "reference_value",
    "reference_unit",
    "reference_frequency_hz",
    "reference_temperature_c",
    "reference_test_voltage_vrms",
    "reference_dc_bias_v",
    "reference_value_kind",
    "reference_source_name",
    "reference_source_document",
    "reference_source_version",
    "reference_source_data_version",
    "reference_source_entry_id",
    "references_json",
]

ESR_CAPACITOR_DETAIL_HEADERS = [
    "esr_nominal_capacitance_f",
    "esr_nominal_capacitance_value",
    "esr_nominal_capacitance_unit",
    "esr_rated_voltage_v",
    "esr_voltage_type",
    "esr_tolerance_lower_pct",
    "esr_tolerance_upper_pct",
    "esr_measured_capacitance_f",
    "esr_measured_esr_ohm",
    "esr_dissipation_factor_d",
    "esr_quality_factor_q",
    "esr_impedance_z_ohm",
    "esr_reactance_x_ohm",
    "esr_capacitance_status",
    "esr_capacitance_deviation_pct",
    "esr_esr_status",
    "esr_esr_factor",
    "esr_consistency_status",
    "esr_derived_esr_from_d_ohm",
]

DETAIL_EXPORT_HEADERS = COMMON_DETAIL_HEADERS + ESR_CAPACITOR_DETAIL_HEADERS


def _enum_value(value: Any) -> Any:
    return value.value if isinstance(value, Enum) else value


def _decode_json_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return [str(raw)]
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _join_json_list(raw: str | None) -> str:
    return " | ".join(_decode_json_list(raw))


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _plain(item) for key, item in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if hasattr(value, "__dict__"):
        return {
            str(key): _plain(item)
            for key, item in vars(value).items()
        }
    return value


def _latest_assessment(detail: dict[str, Any]) -> Any | None:
    assessments = detail.get("assessment_snapshots") or []
    return assessments[0] if assessments else None


def _latest_references(detail: dict[str, Any], assessment: Any | None) -> list[Any]:
    if assessment is None:
        return []
    mapping = detail.get("reference_snapshots_by_assessment_id") or {}
    return list(mapping.get(assessment.id, []))


def _common_row(detail: dict[str, Any]) -> dict[str, Any]:
    model = detail["component_model"]
    sample = detail["component_sample"]
    session = detail["measurement_session"]
    measurement = detail["measurement"]
    assessments = detail.get("assessment_snapshots") or []
    assessment = _latest_assessment(detail)
    references = _latest_references(detail, assessment)
    reference = references[0] if references else None

    row = {
        "measurement_id": measurement.id,
        "tool_key": measurement.tool_key,
        "measured_at_ms": measurement.measured_at_ms,
        "measurement_session_id": measurement.measurement_session_id,
        "component_sample_id": session.component_sample_id,
        "component_model_id": sample.component_model_id,
        "manufacturer": model.manufacturer,
        "series": model.series,
        "part_number": model.part_number,
        "technology": model.technology,
        "sample_code": sample.sample_code,
        "sample_state": _enum_value(sample.sample_state),
        "customer": session.customer,
        "project": session.project,
        "installation": session.installation,
        "module_board": session.module_board,
        "component_reference": session.component_reference,
        "measurement_method": _enum_value(measurement.measurement_method),
        "instrument_key": measurement.instrument_key,
        "instrument_name": measurement.instrument_name,
        "instrument_profile_version": measurement.instrument_profile_version,
        "frequency_hz": measurement.frequency_hz,
        "test_voltage_vrms": measurement.test_voltage_vrms,
        "temperature_c": measurement.temperature_c,
        "power_off_confirmed": measurement.power_off_confirmed,
        "discharged_confirmed": measurement.discharged_confirmed,
        "residual_voltage_before_v": measurement.residual_voltage_before_v,
        "residual_voltage_after_v": measurement.residual_voltage_after_v,
        "out_of_range": measurement.out_of_range,
        "open_suspected": measurement.open_suspected,
        "short_suspected": measurement.short_suspected,
        "unstable_reading": measurement.unstable_reading,
        "parallel_components_notes": measurement.parallel_components_notes,
        "mechanical_condition_notes": measurement.mechanical_condition_notes,
        "measurement_notes": measurement.notes,
        "record_status": measurement.record_status,
        "supersedes_measurement_id": measurement.supersedes_measurement_id,
        "invalid_reason": measurement.invalid_reason,
        "assessment_count": len(assessments),
        "latest_assessment_id": assessment.id if assessment else None,
        "assessed_at_ms": assessment.assessed_at_ms if assessment else None,
        "assessment_engine_version": assessment.engine_version if assessment else None,
        "final_status": assessment.final_status if assessment else None,
        "reliability_level": assessment.reliability_level if assessment else None,
        "reasons_text": _join_json_list(assessment.reasons_json) if assessment else "",
        "warnings_text": _join_json_list(assessment.warnings_json) if assessment else "",
        "advice_text": _join_json_list(assessment.advice_json) if assessment else "",
        "reasons_json": assessment.reasons_json if assessment else None,
        "warnings_json": assessment.warnings_json if assessment else None,
        "advice_json": assessment.advice_json if assessment else None,
        "reference_count": len(references),
        "reference_role": reference.reference_role if reference else None,
        "reference_level": reference.reference_level if reference else None,
        "reference_type": reference.reference_type if reference else None,
        "reference_manufacturer": reference.manufacturer if reference else None,
        "reference_series": reference.series if reference else None,
        "reference_part_number": reference.part_number if reference else None,
        "reference_value": reference.reference_value if reference else None,
        "reference_unit": reference.reference_unit if reference else None,
        "reference_frequency_hz": reference.frequency_hz if reference else None,
        "reference_temperature_c": reference.temperature_c if reference else None,
        "reference_test_voltage_vrms": reference.test_voltage_vrms if reference else None,
        "reference_dc_bias_v": reference.dc_bias_v if reference else None,
        "reference_value_kind": reference.value_kind if reference else None,
        "reference_source_name": reference.source_name if reference else None,
        "reference_source_document": reference.source_document if reference else None,
        "reference_source_version": reference.source_version if reference else None,
        "reference_source_data_version": (
            reference.source_data_version if reference else None
        ),
        "reference_source_entry_id": reference.source_entry_id if reference else None,
        "references_json": json.dumps(
            [_plain(item) for item in references],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
    }
    return row


def _apply_esr_capacitor_fields(
    row: dict[str, Any],
    detail: dict[str, Any],
) -> None:
    model = detail["component_model"]
    measurement = detail["measurement"]
    assessment = _latest_assessment(detail)

    row.update(
        {
            "esr_nominal_capacitance_f": model.nominal_capacitance_f,
            "esr_nominal_capacitance_value": model.nominal_capacitance_value,
            "esr_nominal_capacitance_unit": model.nominal_capacitance_unit,
            "esr_rated_voltage_v": model.rated_voltage_v,
            "esr_voltage_type": model.voltage_type,
            "esr_tolerance_lower_pct": model.tolerance_lower_pct,
            "esr_tolerance_upper_pct": model.tolerance_upper_pct,
            "esr_measured_capacitance_f": measurement.capacitance_f,
            "esr_measured_esr_ohm": measurement.esr_ohm,
            "esr_dissipation_factor_d": measurement.dissipation_factor_d,
            "esr_quality_factor_q": measurement.quality_factor_q,
            "esr_impedance_z_ohm": measurement.impedance_z_ohm,
            "esr_reactance_x_ohm": measurement.reactance_x_ohm,
            "esr_capacitance_status": (
                assessment.capacitance_status if assessment else None
            ),
            "esr_capacitance_deviation_pct": (
                assessment.capacitance_deviation_pct if assessment else None
            ),
            "esr_esr_status": assessment.esr_status if assessment else None,
            "esr_esr_factor": assessment.esr_factor if assessment else None,
            "esr_consistency_status": (
                assessment.consistency_status if assessment else None
            ),
            "esr_derived_esr_from_d_ohm": (
                assessment.derived_esr_from_d_ohm if assessment else None
            ),
        }
    )


def build_detail_export_row(detail: dict[str, Any]) -> dict[str, Any]:
    """Bouw één detailregel; tool-specifieke velden dispatchen via tool_key."""
    row = {header: None for header in DETAIL_EXPORT_HEADERS}
    row.update(_common_row(detail))

    tool_key = detail["measurement"].tool_key
    if tool_key == "ESR_CAPACITOR":
        _apply_esr_capacitor_fields(row, detail)

    return row


def detail_row_values(detail: dict[str, Any]) -> list[Any]:
    """Geef waarden in de vaste DETAIL_EXPORT_HEADERS-volgorde."""
    row = build_detail_export_row(detail)
    return [row.get(header) for header in DETAIL_EXPORT_HEADERS]
