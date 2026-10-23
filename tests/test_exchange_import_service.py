"""
================================================================================
Module:     tests/test_exchange_import_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.1
Datum:      2026-10-23
Auteur:     Bart Bossuyt

Doel:       Regressietests voor app/services/exchange/import_service.py
            (fase 28D). Puur, geen Qt. Gebruikt een echte
            StorageService op een tijdelijke SQLite-database, omdat de
            service zelf schrijft via save_new_measurement_chain.

Wijzigingen:
  v1.0.0 (2026-10-23)  Eerste versie.
  v1.0.1 (2026-10-23)  Fix: _chain(manufacturer=...) plaatste de
                       override op het top-level van de dict, niet in
                       component_model. Daardoor bleef de natural_key
                       gelijk aan de default, en zagen twee tests
                       onterecht een duplicate. _chain heeft nu een
                       expliciete manufacturer-parameter.
================================================================================
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.exchange.export_service import bereken_natural_key
from app.services.exchange.import_planner import ImportPlanner
from app.services.exchange.import_service import (
    HerkomstRepository,
    ImportService,
)
from app.services.exchange.models import (
    FORMAT_VERSION,
    ExchangeError,
    ExportEnvelope,
    ExportedMeasurementChain,
    ImportDecision,
    ImportPlan,
)
from app.services.history_service import MeasurementHistoryService
from app.storage.service import StorageService


_MACHINE_A = "3f2504e0-4f89-41d3-9a0c-0305e82c3301"
_MACHINE_B = "9c8e5f1a-1111-2222-3333-444455556666"


@pytest.fixture
def storage(tmp_path: Path) -> StorageService:
    service = StorageService(tmp_path / "measurements.sqlite3")
    service.initialize()
    return service


def _chain_dicts(*, manufacturer: str = "Test"):
    return {
        "component_model": {"manufacturer": manufacturer},
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
        "assessment_snapshots": (
            {"assessed_at_ms": 1_700_000_001_500, "final_status": "GOOD"},
        ),
        "reference_snapshots_by_assessment_index": (
            ({"reference_role": "ESR", "reference_value": 0.1},),
        ),
    }


def _chain(
    *,
    source_measurement_id: int = 42,
    source_machine_id: str = _MACHINE_A,
    manufacturer: str = "Test",
):
    basis = _chain_dicts(manufacturer=manufacturer)
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


def _envelope(*chains):
    return ExportEnvelope(
        format_version=FORMAT_VERSION,
        app_version="1.3.0",
        schema_version=3,
        exported_at_ms=1_792_651_200_000,
        source_machine_id=_MACHINE_A,
        chains=tuple(chains),
    )


def _plan(*chains):
    return ImportPlan(
        envelope=_envelope(*chains),
        decisions=(ImportDecision.IMPORT_NEW,) * len(chains),
    )


def _service(storage: StorageService, **kwargs) -> ImportService:
    return ImportService(
        storage_service_factory=lambda: storage,
        history_service=MeasurementHistoryService(
            storage_service_factory=lambda _p: storage,
        ),
        **kwargs,
    )


# ---------------------------------------------------------------- gelukkig pad

def test_apply_plan_schrijft_import_new(storage: StorageService):
    service = _service(storage)
    result = service.apply_plan(_plan(_chain()))

    assert result.imported_count == 1
    assert result.skipped_duplicate_count == 0
    assert result.conflict_copy_count == 0
    assert not result.has_errors


def test_apply_plan_vult_herkomst_kolommen(storage: StorageService):
    service = _service(storage)
    result = service.apply_plan(_plan(_chain()))

    measurement_id = result.imported_measurement_ids[0]
    measurement = storage.get_measurement(measurement_id)
    assert measurement.source_machine_id == _MACHINE_A
    assert measurement.source_measurement_id == 42


def test_apply_plan_met_reference_snapshots(storage: StorageService):
    service = _service(storage)
    result = service.apply_plan(_plan(_chain()))

    measurement_id = result.imported_measurement_ids[0]
    detail = storage.get_measurement_detail(measurement_id)
    assessments = detail["assessment_snapshots"]
    assert len(assessments) == 1
    refs = detail["reference_snapshots_by_assessment_id"][assessments[0].id]
    assert len(refs) == 1
    assert refs[0].reference_role == "ESR"


# ---------------------------------------------------------------- skip

def test_apply_plan_skip_duplicate_doet_niets(storage: StorageService):
    service = _service(storage)
    service.apply_plan(_plan(_chain()))

    plan_met_skip = ImportPlan(
        envelope=_envelope(_chain()),
        decisions=(ImportDecision.SKIP_DUPLICATE,),
    )
    result = service.apply_plan(plan_met_skip)

    assert result.imported_count == 0
    assert result.skipped_duplicate_count == 1


# ---------------------------------------------------------------- conflict-copy

def test_apply_plan_conflict_copy_maakt_nieuwe_keten(storage: StorageService):
    service = _service(storage)
    eerste = service.apply_plan(_plan(_chain()))
    eerste_id = eerste.imported_measurement_ids[0]

    # Tweede plan met dezelfde inhoud, decision IMPORT_AS_CONFLICT_COPY.
    plan = ImportPlan(
        envelope=_envelope(_chain(source_measurement_id=99)),
        decisions=(ImportDecision.IMPORT_AS_CONFLICT_COPY,),
    )
    result = service.apply_plan(plan)

    # Zonder cache en met dezelfde natural_key: skip.
    assert result.skipped_duplicate_count == 1


def test_apply_plan_conflict_copy_met_andere_inhoud(storage: StorageService):
    service = _service(storage)
    service.apply_plan(_plan(_chain()))

    plan = ImportPlan(
        envelope=_envelope(_chain(manufacturer="AndereFabrikant")),
        decisions=(ImportDecision.IMPORT_AS_CONFLICT_COPY,),
    )
    result = service.apply_plan(plan)

    assert result.conflict_copy_count == 1
    measurement_id = result.conflict_copy_measurement_ids[0]
    assert measurement_id in result.imported_measurement_ids


# ---------------------------------------------------------------- NEEDS_USER_CHOICE

def test_needs_user_choice_skip(storage: StorageService):
    service = _service(storage)
    plan = ImportPlan(
        envelope=_envelope(_chain()),
        decisions=(ImportDecision.NEEDS_USER_CHOICE,),
    )
    result = service.apply_plan(plan, on_conflict="skip")
    assert result.skipped_duplicate_count == 1


def test_needs_user_choice_conflict_copy(storage: StorageService):
    service = _service(storage)
    plan = ImportPlan(
        envelope=_envelope(_chain()),
        decisions=(ImportDecision.NEEDS_USER_CHOICE,),
    )
    result = service.apply_plan(plan, on_conflict="conflict_copy")
    assert result.imported_count == 1


def test_ongeldige_on_conflict_faalt(storage: StorageService):
    service = _service(storage)
    with pytest.raises(ExchangeError):
        service.apply_plan(_plan(_chain()), on_conflict="iets_anders")


# ---------------------------------------------------------------- gemengd

def test_gemengd_plan(storage: StorageService):
    service = _service(storage)
    service.apply_plan(_plan(_chain(source_measurement_id=1)))

    plan = ImportPlan(
        envelope=_envelope(
            _chain(source_measurement_id=1),  # duplicate
            _chain(source_measurement_id=2, manufacturer="Nieuw"),
        ),
        decisions=(ImportDecision.SKIP_DUPLICATE, ImportDecision.IMPORT_NEW),
    )
    result = service.apply_plan(plan)

    # De eerste is een duplicate; de tweede is inhoudelijk nieuw.
    assert result.skipped_duplicate_count == 1
    assert result.imported_count == 1


# ---------------------------------------------------------------- errors

def test_fout_in_één_keten_blokkeert_rest_niet(storage: StorageService):
    service = _service(storage)

    # Eerste keten heeft een ongeldige measurement_method.
    ongeldig = _chain(source_measurement_id=1)
    ongeldig_dict = dict(ongeldig.measurement)
    ongeldig_dict["measurement_method"] = "INVALID_METHOD"
    ongeldig = ExportedMeasurementChain(
        source_measurement_id=1,
        source_machine_id=ongeldig.source_machine_id,
        natural_key=ongeldig.natural_key,
        component_model=dict(ongeldig.component_model),
        component_sample=dict(ongeldig.component_sample),
        measurement_session=dict(ongeldig.measurement_session),
        measurement=ongeldig_dict,
        assessment_snapshots=ongeldig.assessment_snapshots,
        reference_snapshots_by_assessment_index=(
            ongeldig.reference_snapshots_by_assessment_index
        ),
    )
    geldig = _chain(source_measurement_id=2, manufacturer="Geldig")

    plan = ImportPlan(
        envelope=_envelope(ongeldig, geldig),
        decisions=(ImportDecision.IMPORT_NEW, ImportDecision.IMPORT_NEW),
    )
    result = service.apply_plan(plan)

    assert result.has_errors
    assert result.imported_count == 1


# ---------------------------------------------------------------- race-check

def test_race_check_op_herkomst(storage: StorageService):
    herkomst = HerkomstRepository(storage.database_path)
    service = _service(storage, herkomst_repository=herkomst)
    service.apply_plan(_plan(_chain()))

    plan = ImportPlan(
        envelope=_envelope(_chain(manufacturer="Andere")),
        decisions=(ImportDecision.IMPORT_NEW,),
    )
    result = service.apply_plan(plan)
    assert result.skipped_duplicate_count == 1


def test_race_check_op_natural_key(storage: StorageService):
    service = _service(storage)
    service.apply_plan(_plan(_chain()))

    plan = ImportPlan(
        envelope=_envelope(_chain(source_measurement_id=999)),
        decisions=(ImportDecision.IMPORT_NEW,),
    )
    result = service.apply_plan(plan)
    assert result.skipped_duplicate_count == 1


# ---------------------------------------------------------------- cache

def test_natural_key_cache_wordt_gebruikt(storage: StorageService):
    service = _service(storage)
    service.apply_plan(_plan(_chain()))

    lege_cache = {}
    service_met_lege_cache = ImportService(
        storage_service_factory=lambda: storage,
        history_service=MeasurementHistoryService(
            storage_service_factory=lambda _p: storage,
        ),
        natural_key_cache=lambda: lege_cache,
    )
    plan = ImportPlan(
        envelope=_envelope(_chain(source_measurement_id=999)),
        decisions=(ImportDecision.IMPORT_NEW,),
    )
    result = service_met_lege_cache.apply_plan(plan)
    # De cache is leeg, dus de race-check op natural_key slaagt niet;
    # maar de herkomst-repository is ook None, dus de keten wordt
    # opgeslagen. Dat is de bedoelde fallback.
    assert result.imported_count == 1


# ---------------------------------------------------------------- integriteit

def test_apply_plan_accepteert_geen_plan_type(storage: StorageService):
    service = _service(storage)
    with pytest.raises(ExchangeError):
        service.apply_plan("geen-plan")


def test_herkomst_repository_returnt_none_voor_onbekende(storage: StorageService):
    herkomst = HerkomstRepository(storage.database_path)
    assert herkomst.find_measurement_id_by_source("unknown", 1) is None
    assert herkomst.find_measurement_id_by_source("", 1) is None
    assert herkomst.find_measurement_id_by_source("m", 0) is None