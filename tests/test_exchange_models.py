"""
================================================================================
Module:     tests/test_exchange_models.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.1
Datum:      2026-10-22
Auteur:     Bart Bossuyt

Doel:       Regressietests voor app/services/exchange/models.py
            (fase 28A). Puur, geen Qt, geen netwerk, geen database.

Wijzigingen:
  v1.0.0 (2026-10-22)  Eerste versie.
  v1.0.1 (2026-10-22)  Fix: test_chain_assessment_snapshots_worden_gekopieerd
                       gaf één assessment-snapshot zonder bijbehorende
                       referentie-lijst. De invariant
                       len(reference_snapshots_by_assessment_index) ==
                       len(assessment_snapshots) is correct en blijft
                       staan; de test is aangevuld met een lege
                       referentie-tuple per assessment.
================================================================================
"""

from __future__ import annotations

import pytest

from app.services.exchange.models import (
    FORMAT_VERSION,
    ExchangeError,
    ExportEnvelope,
    ExportedMeasurementChain,
    ImportConflict,
    ImportDecision,
    ImportPlan,
    ImportResult,
)


# ---------------------------------------------------------------- helpers

def _lege_chain_dicts():
    return {
        "component_model": {"manufacturer": "Test"},
        "component_sample": {"sample_state": "NEW"},
        "measurement_session": {"started_at_ms": 1_700_000_000_000},
        "measurement": {
            "measured_at_ms": 1_700_000_001_000,
            "measurement_method": "EX_SITU",
            "tool_key": "ESR_CAPACITOR",
        },
        "assessment_snapshots": (),
        "reference_snapshots_by_assessment_index": (),
    }


def _chain(**overrides):
    basis = {
        "source_measurement_id": 42,
        "source_machine_id": "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
        "natural_key": "a" * 64,
        **_lege_chain_dicts(),
    }
    basis.update(overrides)
    return ExportedMeasurementChain(**basis)


def _envelope(**overrides):
    basis = {
        "format_version": FORMAT_VERSION,
        "app_version": "1.3.0",
        "schema_version": 2,
        "exported_at_ms": 1_792_651_200_000,
        "source_machine_id": "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
        "chains": (),
    }
    basis.update(overrides)
    return ExportEnvelope(**basis)


# ---------------------------------------------------------------- enum

def test_import_decision_heeft_vier_waarden():
    waarden = {d.value for d in ImportDecision}
    assert waarden == {
        "IMPORT_NEW",
        "SKIP_DUPLICATE",
        "IMPORT_AS_CONFLICT_COPY",
        "NEEDS_USER_CHOICE",
    }


def test_import_decision_is_str_enum():
    assert ImportDecision.IMPORT_NEW == "IMPORT_NEW"


def test_format_version_constante():
    assert FORMAT_VERSION == "1.0"


# ---------------------------------------------------------------- ExportedMeasurementChain

def test_chain_gelukkig_pad():
    chain = _chain()
    assert chain.source_measurement_id == 42
    assert chain.source_machine_id.startswith("3f2504e0")
    assert chain.natural_key == "a" * 64
    assert chain.component_model == {"manufacturer": "Test"}
    assert chain.assessment_snapshots == ()
    assert chain.reference_snapshots_by_assessment_index == ()


def test_chain_metadata_wordt_gekopieerd():
    bron = {"manufacturer": "Test"}
    chain = _chain(component_model=bron)
    bron["manufacturer"] = "Gewijzigd"
    assert chain.component_model == {"manufacturer": "Test"}


def test_chain_assessment_snapshots_worden_gekopieerd():
    """Eén assessment-snapshot vereist één lege referentie-tuple."""
    assessment = ({"final_status": "GOOD"},)
    referenties = ((),)  # evenveel items als assessment_snapshots
    chain = _chain(
        assessment_snapshots=assessment,
        reference_snapshots_by_assessment_index=referenties,
    )
    assert chain.assessment_snapshots == ({"final_status": "GOOD"},)
    assert chain.reference_snapshots_by_assessment_index == ((),)


def test_chain_source_measurement_id_moet_positief_zijn():
    with pytest.raises(ExchangeError):
        _chain(source_measurement_id=0)
    with pytest.raises(ExchangeError):
        _chain(source_measurement_id=-1)
    with pytest.raises(ExchangeError):
        _chain(source_measurement_id=True)


def test_chain_source_machine_id_moet_tekst_zijn():
    with pytest.raises(ExchangeError):
        _chain(source_machine_id="")
    with pytest.raises(ExchangeError):
        _chain(source_machine_id="   ")
    with pytest.raises(ExchangeError):
        _chain(source_machine_id=None)


def test_chain_natural_key_mag_niet_leeg_zijn():
    with pytest.raises(ExchangeError):
        _chain(natural_key="")


def test_chain_component_model_moet_dict_zijn():
    with pytest.raises(ExchangeError):
        _chain(component_model=["a"])


def test_chain_assessment_snapshots_moet_tuple_zijn():
    with pytest.raises(ExchangeError):
        _chain(assessment_snapshots=[{"final_status": "GOOD"}])


def test_chain_reference_index_lengte_moet_kloppen():
    with pytest.raises(ExchangeError):
        _chain(
            assessment_snapshots=({"final_status": "GOOD"},),
            reference_snapshots_by_assessment_index=(),
        )


def test_chain_reference_index_gelukkig_pad():
    chain = _chain(
        assessment_snapshots=({"final_status": "GOOD"},),
        reference_snapshots_by_assessment_index=(
            ({"reference_role": "ESR"},),
        ),
    )
    assert len(chain.reference_snapshots_by_assessment_index) == 1


def test_chain_to_dict_roundtrip():
    chain = _chain()
    data = chain.to_dict()
    assert data["source_measurement_id"] == 42
    assert data["component_model"] == {"manufacturer": "Test"}
    assert data["assessment_snapshots"] == []


def test_chain_to_dict_is_herhaalbaar():
    chain = _chain()
    a = chain.to_dict()
    b = chain.to_dict()
    a["component_model"]["manufacturer"] = "Gewijzigd"
    assert b["component_model"]["manufacturer"] == "Test"


# ---------------------------------------------------------------- ExportEnvelope

def test_envelope_gelukkig_pad():
    env = _envelope()
    assert env.format_version == FORMAT_VERSION
    assert env.app_version == "1.3.0"
    assert env.schema_version == 2
    assert env.chains == ()


def test_envelope_met_ketens():
    env = _envelope(chains=(_chain(),))
    assert len(env.chains) == 1


def test_envelope_format_version_onbekend_faalt():
    with pytest.raises(ExchangeError):
        _envelope(format_version="2.0")
    with pytest.raises(ExchangeError):
        _envelope(format_version="")


def test_envelope_schema_version_moet_positief_zijn():
    with pytest.raises(ExchangeError):
        _envelope(schema_version=0)


def test_envelope_exported_at_ms_mag_nul_zijn():
    env = _envelope(exported_at_ms=0)
    assert env.exported_at_ms == 0
    with pytest.raises(ExchangeError):
        _envelope(exported_at_ms=-1)


def test_envelope_chains_moet_tuple_zijn():
    with pytest.raises(ExchangeError):
        _envelope(chains=[_chain()])


def test_envelope_chains_moet_chain_objecten_bevatten():
    with pytest.raises(ExchangeError):
        _envelope(chains=({"source_measurement_id": 1},))


def test_envelope_to_dict():
    env = _envelope(chains=(_chain(),))
    data = env.to_dict()
    assert data["format_version"] == FORMAT_VERSION
    assert data["schema_version"] == 2
    assert len(data["chains"]) == 1
    assert data["chains"][0]["source_measurement_id"] == 42


# ---------------------------------------------------------------- ImportConflict

def test_conflict_gelukkig_pad():
    conflict = ImportConflict(
        chain_index=0,
        natural_key="a" * 64,
        source_measurement_id=42,
        source_machine_id="3f2504e0-4f89-41d3-9a0c-0305e82c3301",
        bestaande_measurement_id=99,
        reden="inhoudelijke match",
    )
    assert conflict.chain_index == 0
    assert conflict.bestaande_measurement_id == 99


def test_conflict_chain_index_mag_nul_zijn():
    conflict = ImportConflict(
        chain_index=0,
        natural_key="a" * 64,
        source_measurement_id=42,
        source_machine_id="m",
        bestaande_measurement_id=99,
        reden="r",
    )
    assert conflict.chain_index == 0


def test_conflict_reden_mag_niet_leeg_zijn():
    with pytest.raises(ExchangeError):
        ImportConflict(
            chain_index=0,
            natural_key="a" * 64,
            source_measurement_id=42,
            source_machine_id="m",
            bestaande_measurement_id=99,
            reden="",
        )


# ---------------------------------------------------------------- ImportPlan

def test_plan_gelukkig_pad():
    env = _envelope(chains=(_chain(),))
    plan = ImportPlan(
        envelope=env,
        decisions=(ImportDecision.IMPORT_NEW,),
    )
    assert plan.decisions == (ImportDecision.IMPORT_NEW,)
    assert plan.conflicts == ()


def test_plan_decisions_lengte_moet_kloppen():
    env = _envelope(chains=(_chain(),))
    with pytest.raises(ExchangeError):
        ImportPlan(
            envelope=env,
            decisions=(),
        )


def test_plan_decisions_moeten_enum_zijn():
    env = _envelope(chains=(_chain(),))
    with pytest.raises(ExchangeError):
        ImportPlan(
            envelope=env,
            decisions=("IMPORT_NEW",),
        )


def test_plan_met_conflict():
    env = _envelope(chains=(_chain(),))
    conflict = ImportConflict(
        chain_index=0,
        natural_key="a" * 64,
        source_measurement_id=42,
        source_machine_id="m",
        bestaande_measurement_id=99,
        reden="r",
    )
    plan = ImportPlan(
        envelope=env,
        decisions=(ImportDecision.NEEDS_USER_CHOICE,),
        conflicts=(conflict,),
    )
    assert plan.conflicts == (conflict,)


# ---------------------------------------------------------------- ImportResult

def test_result_leeg():
    result = ImportResult()
    assert result.imported_count == 0
    assert result.conflict_copy_count == 0
    assert result.skipped_duplicate_count == 0
    assert result.has_errors is False


def test_result_met_imports():
    result = ImportResult(
        imported_measurement_ids=(1, 2, 3),
        skipped_duplicate_count=1,
        conflict_copy_measurement_ids=(4,),
    )
    assert result.imported_count == 3
    assert result.conflict_copy_count == 1
    assert result.skipped_duplicate_count == 1


def test_result_errors_moet_tuple_van_strings_zijn():
    with pytest.raises(ExchangeError):
        ImportResult(errors=["fout"])
    with pytest.raises(ExchangeError):
        ImportResult(errors=(1, 2))


def test_result_imported_ids_moeten_positief_zijn():
    with pytest.raises(ExchangeError):
        ImportResult(imported_measurement_ids=(0,))