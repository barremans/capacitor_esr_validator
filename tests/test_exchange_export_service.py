"""
================================================================================
Module:     tests/test_exchange_export_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.3
Datum:      2026-10-23
Auteur:     Bart Bossuyt

Doel:       Regressietests voor app/services/exchange/export_service.py
            (fase 28B). Puur, geen Qt. Gebruikt een stub-history om
            database-onafhankelijk te testen.

Wijzigingen:
  v1.0.0 (2026-10-23)  Eerste versie.
  v1.0.1 (2026-10-23)  Fix: de stub gebruikt nu echte SampleState- en
                       MeasurementMethod-enums uit app.storage.models
                       in plaats van SimpleNamespace(value=...). Dat
                       is wat StorageService.get_measurement_detail()
                       in productie teruggeeft; de vorige versie was
                       niet representatief en faalde op json.dumps.
  v1.0.2 (2026-10-23)  Fix: _service() gebruikte `details or {...}`,
                       waardoor een expliciet lege dict (details={})
                       werd vervangen door de default. Daardoor kon
                       test_export_filters_leeg_faalt nooit een lege
                       database simuleren. Nu expliciet `if details
                       is None`.
  v1.0.3 (2026-10-23)  Fix: test_export_measurements_gelukkig_pad
                       controleerde schema_version == 2 (hardcoded).
                       Na 28E is CURRENT_SCHEMA_VERSION 3. De test
                       gebruikt nu CURRENT_SCHEMA_VERSION, zodat
                       toekomstige schema-migraties deze test niet
                       opnieuw breken.
================================================================================
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services.exchange.export_service import (
    ExportService,
    bereken_natural_key,
    verkrijg_machine_id,
)
from app.services.exchange.models import (
    ExchangeError,
    ExportEnvelope,
)
from app.storage.models import MeasurementMethod, SampleState
from app.storage.schema import CURRENT_SCHEMA_VERSION


_MACHINE_A = "3f2504e0-4f89-41d3-9a0c-0305e82c3301"


def _detail(measurement_id: int = 42, *, manufacturer: str = "Test") -> dict:
    model = SimpleNamespace(
        id=1,
        manufacturer=manufacturer,
        series="S1",
        part_number="P1",
        technology="ALUMINIUM",
        nominal_capacitance_f=470e-6,
        nominal_capacitance_value=470.0,
        nominal_capacitance_unit="µF",
        rated_voltage_v=25.0,
        voltage_type="DC",
        tolerance_lower_pct=-20.0,
        tolerance_upper_pct=20.0,
        temperature_min_c=None,
        temperature_max_c=None,
        case_size=None,
        notes=None,
        created_at_ms=1_700_000_000_000,
    )
    sample = SimpleNamespace(
        id=2,
        component_model_id=1,
        sample_code=None,
        sample_state=SampleState.NEW,
        source=None,
        batch_lot_code=None,
        date_code=None,
        visual_condition=None,
        notes=None,
        created_at_ms=1_700_000_000_000,
    )
    session = SimpleNamespace(
        id=10,
        component_sample_id=2,
        started_at_ms=1_700_000_000_000,
        ended_at_ms=None,
        operator_name=None,
        customer=None,
        project=None,
        installation=None,
        module_board=None,
        component_reference=None,
        notes=None,
        created_at_ms=1_700_000_000_000,
    )
    measurement = SimpleNamespace(
        id=measurement_id,
        measurement_session_id=10,
        measured_at_ms=1_700_000_001_000,
        measurement_method=MeasurementMethod.EX_SITU,
        tool_key="ESR_CAPACITOR",
        instrument_key="LCR_ST1",
        instrument_name=None,
        instrument_profile_version=None,
        frequency_hz=1000.0,
        test_voltage_vrms=0.6,
        temperature_c=20.0,
        power_off_confirmed=True,
        discharged_confirmed=True,
        residual_voltage_before_v=None,
        residual_voltage_after_v=None,
        capacitance_f=465e-6,
        esr_ohm=0.2,
        dissipation_factor_d=None,
        quality_factor_q=None,
        impedance_z_ohm=None,
        reactance_x_ohm=None,
        out_of_range=False,
        open_suspected=False,
        short_suspected=False,
        unstable_reading=False,
        parallel_components_notes=None,
        mechanical_condition_notes=None,
        notes=None,
        record_status=None,
        supersedes_measurement_id=None,
        invalid_reason=None,
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


class _StubHistory:
    def __init__(self, details: dict[int, dict]):
        self._details = details
        self.detail_calls: list[int] = []
        self.list_calls: list[dict] = []

    def get_measurement_detail(self, measurement_id: int):
        self.detail_calls.append(int(measurement_id))
        return self._details.get(int(measurement_id))

    def list_measurements(self, filters=None, *, limit=100, offset=0):
        self.list_calls.append(
            {"filters": dict(filters or {}), "limit": limit, "offset": offset}
        )
        rijen = [
            {"measurement": SimpleNamespace(id=mid)}
            for mid in sorted(self._details)
        ]
        if offset >= len(rijen):
            return []
        return rijen[offset : offset + limit]


def _service(details=None, *, machine_id=_MACHINE_A):
    if details is None:
        details = {42: _detail(42)}
    return ExportService(
        history_service=_StubHistory(details),
        machine_id=machine_id,
        clock=lambda: 1_792_651_200_000,
    )


# ---------------------------------------------------------------- export_measurements

def test_export_measurements_gelukkig_pad():
    service = _service()
    envelope = service.export_measurements([42])

    assert isinstance(envelope, ExportEnvelope)
    assert envelope.source_machine_id == _MACHINE_A
    assert envelope.schema_version == CURRENT_SCHEMA_VERSION
    assert len(envelope.chains) == 1
    chain = envelope.chains[0]
    assert chain.source_measurement_id == 42
    assert chain.component_model["manufacturer"] == "Test"
    assert chain.measurement["tool_key"] == "ESR_CAPACITOR"
    assert chain.natural_key and len(chain.natural_key) == 64


def test_export_measurements_leeg_faalt():
    service = _service()
    with pytest.raises(ExchangeError):
        service.export_measurements([])


def test_export_measurements_ongeldige_id_faalt():
    service = _service()
    with pytest.raises(ExchangeError):
        service.export_measurements([0])
    with pytest.raises(ExchangeError):
        service.export_measurements([True])


def test_export_measurements_ontbrekend_detail_faalt():
    service = _service(details={42: _detail(42)})
    with pytest.raises(ExchangeError):
        service.export_measurements([42, 999])


def test_export_measurements_dubbele_id_wordt_genegeerd():
    stub = _StubHistory({42: _detail(42)})
    service = ExportService(
        history_service=stub, machine_id=_MACHINE_A, clock=lambda: 0
    )
    envelope = service.export_measurements([42, 42, 42])
    assert len(envelope.chains) == 1
    assert stub.detail_calls == [42]


# ---------------------------------------------------------------- export_filters

def test_export_filters_gelukkig_pad():
    service = _service()
    envelope = service.export_filters({"manufacturer": "Test"})
    assert len(envelope.chains) == 1


def test_export_filters_leeg_faalt():
    service = _service(details={})
    with pytest.raises(ExchangeError):
        service.export_filters(None)


# ---------------------------------------------------------------- natural_key

def test_natural_key_is_deterministisch():
    chain = _service().export_measurements([42]).chains[0]
    a = bereken_natural_key(
        component_model=chain.component_model,
        component_sample=chain.component_sample,
        measurement_session=chain.measurement_session,
        measurement=chain.measurement,
        assessment_snapshots=chain.assessment_snapshots,
        reference_snapshots_by_assessment_index=chain.reference_snapshots_by_assessment_index,
    )
    b = bereken_natural_key(
        component_model=chain.component_model,
        component_sample=chain.component_sample,
        measurement_session=chain.measurement_session,
        measurement=chain.measurement,
        assessment_snapshots=chain.assessment_snapshots,
        reference_snapshots_by_assessment_index=chain.reference_snapshots_by_assessment_index,
    )
    assert a == b == chain.natural_key


def test_natural_key_verandert_met_inhoud():
    chain = _service().export_measurements([42]).chains[0]
    andere_measurement = dict(chain.measurement)
    andere_measurement["esr_ohm"] = 0.999
    andere_key = bereken_natural_key(
        component_model=chain.component_model,
        component_sample=chain.component_sample,
        measurement_session=chain.measurement_session,
        measurement=andere_measurement,
        assessment_snapshots=chain.assessment_snapshots,
        reference_snapshots_by_assessment_index=chain.reference_snapshots_by_assessment_index,
    )
    assert andere_key != chain.natural_key


# ---------------------------------------------------------------- write_envelope

def test_write_envelope_schrijft_utf8_zonder_bom(tmp_path: Path):
    envelope = _service().export_measurements([42])
    doel = tmp_path / "export.esrexchange.json"
    _service().write_envelope(envelope, doel)

    data = doel.read_bytes()
    assert not data.startswith(b"\xef\xbb\xbf")
    tekst = data.decode("utf-8")
    parsed = json.loads(tekst)
    assert parsed["format_version"] == "1.0"
    assert parsed["source_machine_id"] == _MACHINE_A
    assert len(parsed["chains"]) == 1


def test_write_envelope_is_pretty_printed(tmp_path: Path):
    envelope = _service().export_measurements([42])
    doel = tmp_path / "export.esrx.json"
    _service().write_envelope(envelope, doel)

    tekst = doel.read_text(encoding="utf-8")
    assert any(line.startswith("  ") for line in tekst.splitlines())
    assert tekst.endswith("\n")


def test_write_envelope_ongeldig_object_faalt(tmp_path: Path):
    with pytest.raises(ExchangeError):
        _service().write_envelope("geen-envelope", tmp_path / "x.json")


# ---------------------------------------------------------------- machine_id

def test_verkrijg_machine_id_genereert_en_bewaart(
    tmp_path: Path, monkeypatch
):
    from app.config import settings as settings_module

    fake_settings = tmp_path / "settings.json"
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", fake_settings)

    eerste = verkrijg_machine_id()
    assert eerste
    tweede = verkrijg_machine_id()
    assert eerste == tweede
    assert fake_settings.is_file()


def test_verkrijg_machine_id_hergebruikt_bestaande(
    tmp_path: Path, monkeypatch
):
    from app.config import settings as settings_module

    fake_settings = tmp_path / "settings.json"
    fake_settings.write_text(
        '{"language": "nl_NL", "algemeen": {"machine_id": "abc"}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", fake_settings)

    assert verkrijg_machine_id() == "abc"


def test_export_gebruikt_machine_id_uit_settings(
    tmp_path: Path, monkeypatch
):
    from app.config import settings as settings_module

    fake_settings = tmp_path / "settings.json"
    fake_settings.write_text(
        '{"language": "nl_NL", "algemeen": {"machine_id": "from-settings"}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", fake_settings)

    service = ExportService(
        history_service=_StubHistory({42: _detail(42)}),
        clock=lambda: 0,
    )
    envelope = service.export_measurements([42])
    assert envelope.source_machine_id == "from-settings"