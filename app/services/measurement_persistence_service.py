"""
================================================================================
Module:     app/services/measurement_persistence_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.1
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Applicatielaag tussen de ESR-GUI en StorageService.

            Zet één reeds uitgevoerde ESR-beoordeling plus de bijbehorende ruwe
            gebruikersinvoer om naar de goedgekeurde storageketen
            model -> sample -> sessie -> meting -> assessment -> referentie.
            Deze service voert geen assessment uit en kiest geen referentie.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste koppellaag voor transactioneel opslaan van een
                        beoordeelde ESR-meting. OL/out-of-range met lege C/ESR
                        wordt als NULL bewaard, nooit als kunstmatige 0,0.
  v1.0.1 (2026-10-01)  Capaciteitsnormalisatie naar farad gecorrigeerd: gebruikt
                        rechtstreeks CAPACITEIT_FACTOR_NAAR_FARAD omdat de
                        bestaande unit-helper F niet als doeleenheid accepteert.
================================================================================
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
import json
from typing import Any

from app.config.settings import CAPACITEIT_FACTOR_NAAR_FARAD
from app.helpers.units import converteer_esr
from app.storage.database import utc_now_ms
from app.storage.models import SampleState
from app.storage.paths import PathService
from app.storage.service import StorageService


ASSESSMENT_ENGINE_VERSION = "1.3.0"


@dataclass(frozen=True)
class EsrMeasurementSaveData:
    """Onveranderlijke invoer voor één beoordeelde ESR-meetrun."""

    nominal_capacitance_value: float
    nominal_capacitance_unit: str
    tolerance_percent: float | None
    rated_voltage_v: float | None
    technology: str
    manufacturer: str | None
    series: str | None

    measurement_method: str
    instrument_key: str | None
    instrument_name: str | None
    frequency_hz: float
    test_voltage_vrms: float | None
    temperature_c: float | None

    safety_confirmed: bool

    measured_capacitance_value: float | None
    measured_capacitance_unit: str
    measured_esr_value: float | None
    measured_esr_unit: str
    dissipation_factor_d: float | None

    out_of_range: bool
    open_suspected: bool

    assessment: Any
    reference: Any | None


class MeasurementPersistenceService:
    """Slaat een reeds beoordeelde ESR-meetrun op zonder domeinlogica te wijzigen."""

    def __init__(
        self,
        *,
        path_service_factory: Callable[[], PathService] = PathService,
        storage_factory: Callable[..., StorageService] = StorageService,
        clock: Callable[[], int] = utc_now_ms,
    ) -> None:
        self._path_service_factory = path_service_factory
        self._storage_factory = storage_factory
        self._clock = clock

    def save_esr_measurement(
        self,
        data: EsrMeasurementSaveData,
    ) -> dict[str, Any]:
        """Sla exact één assessmentketen transactioneel op."""
        now_ms = int(self._clock())

        paths = self._path_service_factory()
        paths.ensure_runtime_directories()

        storage = self._storage_factory(paths.database_path, clock=self._clock)
        storage.initialize()

        measured_capacitance_f = self._capacitance_to_farad(
            data.measured_capacitance_value,
            data.measured_capacitance_unit,
        )
        measured_esr_ohm = self._esr_to_ohm(
            data.measured_esr_value,
            data.measured_esr_unit,
        )

        tolerance = data.tolerance_percent
        tolerance_lower = -abs(tolerance) if tolerance is not None else None
        tolerance_upper = abs(tolerance) if tolerance is not None else None

        assessment = data.assessment

        component_model = {
            "manufacturer": data.manufacturer or None,
            "series": data.series or None,
            "part_number": None,
            "technology": data.technology or None,
            "nominal_capacitance_f": self._capacitance_to_farad(
                data.nominal_capacitance_value,
                data.nominal_capacitance_unit,
            ),
            "nominal_capacitance_value": data.nominal_capacitance_value,
            "nominal_capacitance_unit": data.nominal_capacitance_unit,
            "rated_voltage_v": data.rated_voltage_v,
            "voltage_type": None,
            "tolerance_lower_pct": tolerance_lower,
            "tolerance_upper_pct": tolerance_upper,
            "temperature_min_c": None,
            "temperature_max_c": None,
            "case_size": None,
            "notes": None,
        }

        component_sample = {
            "sample_code": None,
            "sample_state": SampleState.UNKNOWN,
            "source": None,
            "batch_lot_code": None,
            "date_code": None,
            "visual_condition": None,
            "notes": None,
        }

        measurement_session = {
            "started_at_ms": now_ms,
            "ended_at_ms": now_ms,
            "operator_name": None,
            "customer": None,
            "project": None,
            "installation": None,
            "module_board": None,
            "component_reference": None,
            "notes": None,
        }

        measurement = {
            "measured_at_ms": now_ms,
            "measurement_method": data.measurement_method,
            "instrument_key": data.instrument_key,
            "instrument_name": data.instrument_name,
            "instrument_profile_version": None,
            "frequency_hz": data.frequency_hz,
            "test_voltage_vrms": data.test_voltage_vrms,
            "temperature_c": data.temperature_c,
            "power_off_confirmed": data.safety_confirmed,
            "discharged_confirmed": data.safety_confirmed,
            "residual_voltage_before_v": None,
            "residual_voltage_after_v": None,
            "capacitance_f": measured_capacitance_f,
            "esr_ohm": measured_esr_ohm,
            "dissipation_factor_d": data.dissipation_factor_d,
            "quality_factor_q": None,
            "impedance_z_ohm": None,
            "reactance_x_ohm": None,
            "out_of_range": data.out_of_range,
            "open_suspected": data.open_suspected,
            "short_suspected": False,
            "unstable_reading": False,
            "parallel_components_notes": None,
            "mechanical_condition_notes": None,
            "notes": None,
            "record_status": None,
            "supersedes_measurement_id": None,
            "invalid_reason": None,
        }

        assessment_snapshot = {
            "assessed_at_ms": now_ms,
            "engine_version": ASSESSMENT_ENGINE_VERSION,
            "capacitance_status": assessment.capaciteit.status.value,
            "capacitance_deviation_pct": assessment.capaciteit.afwijking_percent,
            "esr_status": assessment.esr.status.value,
            "esr_factor": assessment.esr.factor,
            "consistency_status": assessment.consistentie.status.value,
            "derived_esr_from_d_ohm": assessment.consistentie.esr_verwacht_ohm,
            "reliability_level": assessment.betrouwbaarheid.niveau.value,
            "final_status": assessment.eindstatus.value,
            "reasons_json": self._json(list(assessment.redenen)),
            "warnings_json": self._json(list(assessment.waarschuwingen)),
            "advice_json": self._json([assessment.aanbevolen_vervolgstap]),
        }

        reference_snapshots: tuple[dict[str, Any], ...]
        if data.reference is None:
            reference_snapshots = ()
        else:
            reference_snapshots = (self._reference_snapshot(data.reference),)

        return storage.save_new_measurement_chain(
            component_model=component_model,
            component_sample=component_sample,
            measurement_session=measurement_session,
            measurement=measurement,
            assessment_snapshot=assessment_snapshot,
            reference_snapshots=reference_snapshots,
        )

    @staticmethod
    def _capacitance_to_farad(value: float | None, unit: str) -> float | None:
        if value is None:
            return None
        try:
            factor = CAPACITEIT_FACTOR_NAAR_FARAD[unit]
        except KeyError as exc:
            opties = ", ".join(CAPACITEIT_FACTOR_NAAR_FARAD.keys())
            raise ValueError(
                f"Onbekende capaciteitseenheid '{unit}'. Toegelaten waarden: {opties}."
            ) from exc
        return float(value) * factor

    @staticmethod
    def _esr_to_ohm(value: float | None, unit: str) -> float | None:
        if value is None:
            return None
        return float(converteer_esr(value, unit, "Ω"))

    @classmethod
    def _reference_snapshot(cls, reference: Any) -> dict[str, Any]:
        kind = {
            "typisch": "TYPICAL",
            "maximaal": "MAXIMUM",
        }.get(reference.typisch_of_maximaal, "OTHER")

        try:
            snapshot_payload = asdict(reference)
        except TypeError:
            snapshot_payload = {
                "esr_waarde": reference.esr_waarde,
                "eenheid": reference.eenheid,
                "bron": reference.bron,
                "referentieniveau": reference.referentieniveau,
                "frequentie_hz": reference.frequentie_hz,
                "typisch_of_maximaal": reference.typisch_of_maximaal,
                "temperatuur_c": getattr(reference, "temperatuur_c", None),
                "condensatortype": getattr(reference, "condensatortype", None),
                "fabrikant": getattr(reference, "fabrikant", None),
                "serie": getattr(reference, "serie", None),
            }

        return {
            "reference_role": "ESR_REFERENCE",
            "reference_level": str(reference.referentieniveau),
            "reference_type": "ESR",
            "manufacturer": getattr(reference, "fabrikant", None),
            "series": getattr(reference, "serie", None),
            "part_number": None,
            "reference_value": reference.esr_waarde,
            "reference_unit": reference.eenheid,
            "frequency_hz": reference.frequentie_hz,
            "temperature_c": getattr(reference, "temperatuur_c", None),
            "test_voltage_vrms": None,
            "dc_bias_v": None,
            "value_kind": kind,
            "source_name": reference.bron,
            "source_document": None,
            "source_version": None,
            "source_data_version": None,
            "source_entry_id": None,
            "source_hash": None,
            "snapshot_json": cls._json(snapshot_payload),
        }

    @staticmethod
    def _json(value: Any) -> str:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
