"""
================================================================================
Module:     tests/test_exchange_import_planner.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.2
Datum:      2026-10-23
Auteur:     Bart Bossuyt

Doel:       Regressietests voor app/services/exchange/import_planner.py
            (fase 28C). Puur, geen Qt. Gebruikt een stub-history en een
            stub-herkomst-repository.

Wijzigingen:
  v1.0.0 (2026-10-23)  Eerste versie.
  v1.0.1 (2026-10-23)  Fix: _chain_dicts() bevat nu de vier verplichte
                       booleans out_of_range, open_suspected,
                       short_suspected en unstable_reading. Die staan
                       in de echte Measurement-dataclass altijd op een
                       expliciete False/True (nooit None), dus de
                       canonieke dict van een bestaande keten bevat ze
                       altijd. Zonder deze vier velden verschilden de
                       natural_keys van keten en detail, en faalde
                       test_duplicate_op_natural_key_wordt_skip_duplicate
                       onterecht.
  v1.0.2 (2026-10-23)  Fix: test_gemengd_nieuw_en_duplicate gaf de
                       tweede keten alleen een ander source_measurement_id
                       maar dezelfde inhoud. De natural_key is echter
                       inhoudelijk (spec §6), dus de tweede keten werd
                       terecht als duplicate gezien. De test geeft de
                       tweede keten nu een andere manufacturer, zodat
                       de inhoud echt verschilt.
================================================================================
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.exchange.export_service import bereken_natural_key
from app.services.exchange.import_planner import ImportPlanner
from app.services.exchange.models import (
    FORMAT_VERSION,
    ExchangeError,
    ExportEnvelope,
    ExportedMeasurementChain,
    ImportDecision,
)
from app.storage.models import MeasurementMethod, SampleState


_MACHINE_A = "3f2504e0-4f89-41d3-9a0c-0305e82c3301"
_MACHINE_B = "9c8e5f1a-1111-2222-3333-444455556666"


def _chain_dicts():
    """Canonieke keten-velden zoals StorageService ze altijd teruggeeft.

    De vier booleans in measurement staan in de echte Measurement-
    dataclass altijd op een expliciete False/True (nooit None), dus de
    canonieke dict van een bestaande keten bevat ze altijd.
    """
    return {
        "component_model": {"manufacturer": "Test"},
        "component_sample": {"sample_state": "NEW"},
        "measurement_session": {"started_at_ms": 1_700_000_000_000},
        "measurement": {
            "measured_at_ms": 1_700_000_001_000,
            "measurement_method": "EX_SITU",
            "tool_key": "ESR_CAPACITOR",
            "out_of_range": False,
            "open_suspected": False,
            "short_suspected": False,
            "unstable_reading": False,
        },
        "assessment_snapshots": (),
        "reference_snapshots_by_assessment_index": (),
    }


def _chain(
    *,
    source_measurement_id: int = 42,
    source_machine_id: str = _MACHINE_A,
    **overrides,
):
    basis = _chain_dicts()
    basis.update(overrides)
    natural_key = bereken_natural_key(
        component_model=basis["component_model"],
        component_sample=basis["component_sample"],
        measurement_session=basis["measurement_session"],
        measurement=basis["measurement"],
        assessment_snapshots=basis["assessment_snapshots"],
        reference_snapshots_by_assessment_index=basis[
            "reference_snapshots_by_assessment_index"
        ],
    )
    return ExportedMeasurementChain(
        source_measurement_id=source_measurement_id,
        source_machine_id=source_machine_id,
        natural_key=natural_key,
        component_model=basis["component_model"],
        component_sample=basis["component_sample"],
        measurement_session=basis["measurement_session"],
        measurement=basis["measurement"],
        assessment_snapshots=basis["assessment_snapshots"],
        reference_snapshots_by_assessment_index=basis[
            "reference_snapshots_by_assessment_index"
        ],
    )


def _envelope(*chains, schema_version: int = 2):
    return ExportEnvelope(
        format_version=FORMAT_VERSION,
        app_version="1.3.0",
        schema_version=schema_version,
        exported_at_ms=1_792_651_200_000,
        source_machine_id=_MACHINE_A,
        chains=tuple(chains),
    )


class _StubHistory:
    def __init__(self, details: dict[int, dict]):
        self._details = details
        self.list_calls: list[dict] = []
        self.detail_calls: list[int] = []

    def list_measurements(self, filters=None, *, limit=100, offset=0):
        self.list_calls.append({"limit": limit, "offset": offset})
        rijen = [
            {"measurement": SimpleNamespace(id=mid)}
            for mid in sorted(self._details)
        ]
        if offset >= len(rijen):
            return []
        return rijen[offset : offset + limit]

    def get_measurement_detail(self, measurement_id: int):
        self.detail_calls.append(int(measurement_id))
        return self._details.get(int(measurement_id))


def _detail_voor_chain(
    chain: ExportedMeasurementChain, measurement_id: int
) -> dict:
    """Bouw een get_measurement_detail()-vormig dict uit een keten."""
    model_dict = dict(chain.component_model)
    sample_dict = dict(chain.component_sample)
    session_dict = dict(chain.measurement_session)
    measurement_dict = dict(chain.measurement)

    model = SimpleNamespace(
        id=1,
        **{
            **{
                f: None
                for f in (
                    "manufacturer", "series", "part_number", "technology",
                    "nominal_capacitance_f", "nominal_capacitance_value",
                    "nominal_capacitance_unit", "rated_voltage_v",
                    "voltage_type", "tolerance_lower_pct",
                    "tolerance_upper_pct", "temperature_min_c",
                    "temperature_max_c", "case_size", "notes",
                )
            },
            **model_dict,
            "created_at_ms": 1_700_000_000_000,
        },
    )
    sample = SimpleNamespace(
        id=2,
        component_model_id=1,
        sample_state=SampleState(sample_dict.get("sample_state", "NEW")),
        sample_code=sample_dict.get("sample_code"),
        source=sample_dict.get("source"),
        batch_lot_code=sample_dict.get("batch_lot_code"),
        date_code=sample_dict.get("date_code"),
        visual_condition=sample_dict.get("visual_condition"),
        notes=sample_dict.get("notes"),
        created_at_ms=1_700_000_000_000,
    )
    session = SimpleNamespace(
        id=10,
        component_sample_id=2,
        started_at_ms=session_dict.get("started_at_ms", 0),
        ended_at_ms=session_dict.get("ended_at_ms"),
        operator_name=session_dict.get("operator_name"),
        customer=session_dict.get("customer"),
        project=session_dict.get("project"),
        installation=session_dict.get("installation"),
        module_board=session_dict.get("module_board"),
        component_reference=session_dict.get("component_reference"),
        notes=session_dict.get("notes"),
        created_at_ms=1_700_000_000_000,
    )
    measurement = SimpleNamespace(
        id=measurement_id,
        measurement_session_id=10,
        measured_at_ms=measurement_dict.get("measured_at_ms", 0),
        measurement_method=MeasurementMethod(
            measurement_dict.get("measurement_method", "EX_SITU")
        ),
        tool_key=measurement_dict.get("tool_key", "ESR_CAPACITOR"),
        instrument_key=measurement_dict.get("instrument_key"),
        instrument_name=measurement_dict.get("instrument_name"),
        instrument_profile_version=measurement_dict.get(
            "instrument_profile_version"
        ),
        frequency_hz=measurement_dict.get("frequency_hz"),
        test_voltage_vrms=measurement_dict.get("test_voltage_vrms"),
        temperature_c=measurement_dict.get("temperature_c"),
        power_off_confirmed=measurement_dict.get("power_off_confirmed"),
        discharged_confirmed=measurement_dict.get("discharged_confirmed"),
        residual_voltage_before_v=measurement_dict.get(
            "residual_voltage_before_v"
        ),
        residual_voltage_after_v=measurement_dict.get(
            "residual_voltage_after_v"
        ),
        capacitance_f=measurement_dict.get("capacitance_f"),
        esr_ohm=measurement_dict.get("esr_ohm"),
        dissipation_factor_d=measurement_dict.get("dissipation_factor_d"),
        quality_factor_q=measurement_dict.get("quality_factor_q"),
        impedance_z_ohm=measurement_dict.get("impedance_z_ohm"),
        reactance_x_ohm=measurement_dict.get("reactance_x_ohm"),
        out_of_range=measurement_dict.get("out_of_range", False),
        open_suspected=measurement_dict.get("open_suspected", False),
        short_suspected=measurement_dict.get("short_suspected", False),
        unstable_reading=measurement_dict.get("unstable_reading", False),
        parallel_components_notes=measurement_dict.get(
            "parallel_components_notes"
        ),
        mechanical_condition_notes=measurement_dict.get(
            "mechanical_condition_notes"
        ),
        notes=measurement_dict.get("notes"),
        record_status=measurement_dict.get("record_status"),
        supersedes_measurement_id=None,
        invalid_reason=measurement_dict.get("invalid_reason"),
        created_at_ms=1_700_000_001_000,
    )
    return {
        "component_model": model,
        "component_sample": sample,
        "measurement_session": session,
        "measurement": measurement,
        "assessment_snapshots": [],
        "reference_snapshots_by_assessment_id": {},
    }


class _StubHerkomst:
    def __init__(self):
        self._records: set[tuple[str, int]] = set()

    def voeg_toe(self, machine_id: str, measurement_id: int):
        self._records.add((machine_id, int(measurement_id)))

    def find_measurement_id_by_source(
        self, source_machine_id: str, source_measurement_id: int
    ) -> int | None:
        if (source_machine_id, int(source_measurement_id)) in self._records:
            return 1
        return None


# ---------------------------------------------------------------- lege envelope

def test_lege_envelope_geldig():
    planner = ImportPlanner(history_service=_StubHistory({}))
    plan = planner.plan(_envelope())
    assert plan.decisions == ()
    assert plan.conflicts == ()


# ---------------------------------------------------------------- nieuwe keten

def test_nieuwe_keten_wordt_import_new():
    planner = ImportPlanner(history_service=_StubHistory({}))
    plan = planner.plan(_envelope(_chain()))
    assert plan.decisions == (ImportDecision.IMPORT_NEW,)


# ---------------------------------------------------------------- duplicate op natural_key

def test_duplicate_op_natural_key_wordt_skip_duplicate():
    chain = _chain()
    detail = _detail_voor_chain(chain, measurement_id=1)
    stub = _StubHistory({1: detail})

    planner = ImportPlanner(history_service=stub)
    plan = planner.plan(_envelope(chain))
    assert plan.decisions == (ImportDecision.SKIP_DUPLICATE,)


# ---------------------------------------------------------------- duplicate op herkomst

def test_duplicate_op_herkomst_wordt_skip_duplicate():
    chain = _chain()
    herkomst = _StubHerkomst()
    herkomst.voeg_toe(_MACHINE_A, 42)

    planner = ImportPlanner(
        history_service=_StubHistory({}),
        herkomst_repository=herkomst,
    )
    plan = planner.plan(_envelope(chain))
    assert plan.decisions == (ImportDecision.SKIP_DUPLICATE,)


def test_herkomst_zonder_match_geeft_import_new():
    chain = _chain()
    herkomst = _StubHerkomst()
    herkomst.voeg_toe(_MACHINE_B, 999)

    planner = ImportPlanner(
        history_service=_StubHistory({}),
        herkomst_repository=herkomst,
    )
    plan = planner.plan(_envelope(chain))
    assert plan.decisions == (ImportDecision.IMPORT_NEW,)


# ---------------------------------------------------------------- gemengd

def test_gemengd_nieuw_en_duplicate():
    """Eén bestaande keten, één inhoudelijk nieuwe keten.

    De natural_key is inhoudelijk (spec §6); een ander
    source_measurement_id alleen is niet genoeg om een nieuwe keten
    te zijn. De tweede keten moet inhoudelijk verschillen, hier via
    een andere manufacturer.
    """
    bestaande = _chain(source_measurement_id=1)
    nieuwe = _chain(
        source_measurement_id=2,
        component_model={"manufacturer": "AndereFabrikant"},
    )
    detail = _detail_voor_chain(bestaande, measurement_id=1)
    stub = _StubHistory({1: detail})

    planner = ImportPlanner(history_service=stub)
    plan = planner.plan(_envelope(bestaande, nieuwe))
    assert plan.decisions == (
        ImportDecision.SKIP_DUPLICATE,
        ImportDecision.IMPORT_NEW,
    )


# ---------------------------------------------------------------- ongeldige envelope

def test_schema_version_te_hoog_faalt():
    planner = ImportPlanner(history_service=_StubHistory({}))
    with pytest.raises(ExchangeError):
        planner.plan(_envelope(schema_version=99))


def test_schema_version_ouder_is_toegestaan():
    planner = ImportPlanner(history_service=_StubHistory({}))
    plan = planner.plan(_envelope(_chain(), schema_version=1))
    assert plan.decisions == (ImportDecision.IMPORT_NEW,)


# ---------------------------------------------------------------- natural-key-mismatch

def test_natural_key_mismatch_faalt():
    chain = _chain()
    corrupt = ExportedMeasurementChain(
        source_measurement_id=chain.source_measurement_id,
        source_machine_id=chain.source_machine_id,
        natural_key="0" * 64,
        component_model=dict(chain.component_model),
        component_sample=dict(chain.component_sample),
        measurement_session=dict(chain.measurement_session),
        measurement=dict(chain.measurement),
        assessment_snapshots=chain.assessment_snapshots,
        reference_snapshots_by_assessment_index=(
            chain.reference_snapshots_by_assessment_index
        ),
    )

    planner = ImportPlanner(history_service=_StubHistory({}))
    with pytest.raises(ExchangeError):
        planner.plan(_envelope(corrupt))


# ---------------------------------------------------------------- cache

def test_natural_key_cache_wordt_gebruikt():
    chain = _chain()
    stub = _StubHistory({})
    cache_waarde = {chain.natural_key: 1}

    planner = ImportPlanner(
        history_service=stub,
        natural_key_cache=lambda: cache_waarde,
    )
    plan = planner.plan(_envelope(chain))
    assert plan.decisions == (ImportDecision.SKIP_DUPLICATE,)
    assert stub.list_calls == []


# ---------------------------------------------------------------- integriteit

def test_planner_schrijft_niets():
    """De planner gebruikt alleen read-methoden op de history-service."""
    chain = _chain()
    stub = _StubHistory({})

    planner = ImportPlanner(history_service=stub)
    planner.plan(_envelope(chain))

    assert stub.detail_calls == []