"""
================================================================================
Module:     app/services/history_import_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-27
Auteur:     Bart Bossuyt

Doel:       GUI-onafhankelijke import-service voor de historiek (C1).

            Neemt een lijst ImportKeten-objecten (uit history_import.py) en
            schrijft ze naar de database via StorageService. Dedup gebeurt
            op de natural key: bestaat de keten al, dan wordt hij
            overgeslagen. Met aanvullen=True wordt een duplicate als
            nieuwe meting opgeslagen (nooit een update — StorageService
            heeft bewust geen update-API).

            De service vult source_machine_id / source_measurement_id NIET:
            C1 is een ruwe-data-import, geen exchange-import (§2.28).

            De service maakt geen database aan als die niet bestaat: dat
            is consistent met MeasurementHistoryService.

Wijzigingen:
  v1.0.0 (2026-10-27)  Eerste versie. Dedup op natural key, optioneel
                        aanvullen, strikte foutafhandeling per keten.
================================================================================
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.helpers.history_import import ImportKeten
from app.storage import PathService, StorageService


@dataclass(frozen=True, slots=True)
class ImportUitkomst:
    """Samenvatting van één import-operatie."""

    toegevoegd: int
    overgeslagen: int
    fouten: int
    fout_details: tuple[str, ...]


class HistoryImportService:
    """Schrijft gevalideerde ImportKeten-objecten naar de lokale historiek."""

    def __init__(
        self,
        *,
        path_service_factory: Callable[[], PathService] = PathService,
        storage_service_factory: Callable[[object], StorageService] = StorageService,
    ) -> None:
        self._path_service_factory = path_service_factory
        self._storage_service_factory = storage_service_factory

    def _bestaande_natural_keys(self, storage: StorageService) -> set[str]:
        """Verzamelt de natural keys van alle bestaande metingen.

        We gebruiken dezelfde canonieke berekening als de parser, maar
        op de detail-data uit de database. Dat is de enige betrouwbare
        dedup: source_* is bij C1-import altijd NULL.
        """
        from app.helpers.history_import import ImportKeten, bereken_natural_key

        keys: set[str] = set()
        offset = 0
        chunk = 500
        while True:
            rows = storage.list_measurements(limit=chunk, offset=offset)
            if not rows:
                break
            for row in rows:
                measurement_id = row["measurement"].id
                detail = storage.get_measurement_detail(measurement_id)
                if detail is None:
                    continue
                keten = _detail_naar_keten_voor_key(detail)
                if keten is not None:
                    keys.add(bereken_natural_key(keten))
            if len(rows) < chunk:
                break
            offset += len(rows)
        return keys

    def importeer(
        self,
        ketens: Iterable[ImportKeten],
        *,
        aanvullen: bool = False,
    ) -> ImportUitkomst:
        """Schrijft ketens naar de database; dedup op natural key."""
        paths = self._path_service_factory()
        database_path = paths.database_path
        if not database_path.exists():
            return ImportUitkomst(
                toegevoegd=0,
                overgeslagen=0,
                fouten=0,
                fout_details=("Database bestaat nog niet.",),
            )

        storage = self._storage_service_factory(database_path)
        storage.initialize()
        bestaande = self._bestaande_natural_keys(storage)

        toegevoegd = 0
        overgeslagen = 0
        fouten = 0
        details: list[str] = []

        for keten in ketens:
            if keten.natural_key in bestaande and not aanvullen:
                overgeslagen += 1
                continue
            try:
                _schrijf_keten(storage, keten)
            except Exception as exc:  # noqa: BLE001 - per keten isoleren
                fouten += 1
                details.append(f"{keten.natural_key[:12]}…: {exc}")
                continue
            bestaande.add(keten.natural_key)
            toegevoegd += 1

        return ImportUitkomst(
            toegevoegd=toegevoegd,
            overgeslagen=overgeslagen,
            fouten=fouten,
            fout_details=tuple(details),
        )


def _schrijf_keten(storage: StorageService, keten: ImportKeten) -> None:
    """Schrijft één keten atomair via save_new_measurement_chain."""
    assessment = keten.assessment_snapshot
    if assessment is None:
        raise ValueError("Keten zonder assessment kan niet worden opgeslagen.")
    storage.save_new_measurement_chain(
        component_model=keten.component_model,
        component_sample=keten.component_sample,
        measurement_session=keten.measurement_session,
        measurement=keten.measurement,
        assessment_snapshot=assessment,
        reference_snapshots=keten.reference_snapshots,
    )


def _detail_naar_keten_voor_key(detail: dict[str, Any]) -> ImportKeten | None:
    """Bouwt een ImportKeten uit een DB-detail, alleen voor de natural key.

    Gebruikt dezelfde velden als de parser, zodat de sleutel exact
    overeenkomt met wat de parser zou berekenen voor dezelfde data.
    """
    from app.helpers.history_import import ImportKeten, bereken_natural_key

    measurement = detail["measurement"]
    model = detail["component_model"]
    sample = detail["component_sample"]
    session = detail["measurement_session"]
    assessments = detail.get("assessment_snapshots") or []
    assessment = assessments[0] if assessments else None
    references = []
    if assessment is not None:
        references = list(
            (detail.get("reference_snapshots_by_assessment_id") or {}).get(
                assessment.id, []
            )
        )

    keten = ImportKeten(
        natural_key="",
        tool_key=measurement.tool_key,
        component_model={
            "manufacturer": model.manufacturer,
            "series": model.series,
            "part_number": model.part_number,
            "technology": model.technology,
            "nominal_capacitance_f": model.nominal_capacitance_f,
            "nominal_capacitance_value": model.nominal_capacitance_value,
            "nominal_capacitance_unit": model.nominal_capacitance_unit,
            "rated_voltage_v": model.rated_voltage_v,
            "voltage_type": model.voltage_type,
            "tolerance_lower_pct": model.tolerance_lower_pct,
            "tolerance_upper_pct": model.tolerance_upper_pct,
        },
        component_sample={
            "sample_code": sample.sample_code,
            "sample_state": sample.sample_state.value,
        },
        measurement_session={
            "started_at_ms": session.started_at_ms,
            "ended_at_ms": session.ended_at_ms,
            "operator_name": session.operator_name,
            "customer": session.customer,
            "project": session.project,
            "installation": session.installation,
            "module_board": session.module_board,
            "component_reference": session.component_reference,
            "notes": session.notes,
        },
        measurement={
            "measured_at_ms": measurement.measured_at_ms,
            "measurement_method": measurement.measurement_method.value,
            "tool_key": measurement.tool_key,
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
            "capacitance_f": measurement.capacitance_f,
            "esr_ohm": measurement.esr_ohm,
            "dissipation_factor_d": measurement.dissipation_factor_d,
            "quality_factor_q": measurement.quality_factor_q,
            "impedance_z_ohm": measurement.impedance_z_ohm,
            "reactance_x_ohm": measurement.reactance_x_ohm,
            "out_of_range": measurement.out_of_range,
            "open_suspected": measurement.open_suspected,
            "short_suspected": measurement.short_suspected,
            "unstable_reading": measurement.unstable_reading,
            "parallel_components_notes": measurement.parallel_components_notes,
            "mechanical_condition_notes": measurement.mechanical_condition_notes,
            "notes": measurement.notes,
            "record_status": measurement.record_status,
            "invalid_reason": measurement.invalid_reason,
        },
        assessment_snapshot=(
            {
                "assessed_at_ms": assessment.assessed_at_ms,
                "engine_version": assessment.engine_version,
                "capacitance_status": assessment.capacitance_status,
                "capacitance_deviation_pct": assessment.capacitance_deviation_pct,
                "esr_status": assessment.esr_status,
                "esr_factor": assessment.esr_factor,
                "consistency_status": assessment.consistency_status,
                "derived_esr_from_d_ohm": assessment.derived_esr_from_d_ohm,
                "reliability_level": assessment.reliability_level,
                "final_status": assessment.final_status,
                "reasons_json": assessment.reasons_json,
                "warnings_json": assessment.warnings_json,
                "advice_json": assessment.advice_json,
            }
            if assessment is not None
            else None
        ),
        reference_snapshots=tuple(
            {
                "reference_role": ref.reference_role,
                "reference_level": ref.reference_level,
                "reference_type": ref.reference_type,
                "manufacturer": ref.manufacturer,
                "series": ref.series,
                "part_number": ref.part_number,
                "reference_value": ref.reference_value,
                "reference_unit": ref.reference_unit,
                "frequency_hz": ref.frequency_hz,
                "temperature_c": ref.temperature_c,
                "test_voltage_vrms": ref.test_voltage_vrms,
                "dc_bias_v": ref.dc_bias_v,
                "value_kind": ref.value_kind,
                "source_name": ref.source_name,
                "source_document": ref.source_document,
                "source_version": ref.source_version,
                "source_data_version": ref.source_data_version,
                "source_entry_id": ref.source_entry_id,
                "source_hash": ref.source_hash,
                "snapshot_json": ref.snapshot_json,
            }
            for ref in references
        ),
    )
    return keten