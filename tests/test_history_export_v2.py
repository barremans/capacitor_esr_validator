"""
================================================================================
Module:     tests/test_history_export_v2.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-02
Auteur:     Bart Bossuyt

Doel:       Regressietests voor analysewaardige detail-export, exportscope,
            checkboxselectie en definitieve export-UX.

Wijzigingen:
  v1.1.0 (2026-10-02)  Checkboxselectie, exporttype-DDL, gecombineerde export
                        en timestamp-bestandsnamen toegevoegd.
================================================================================
"""

from __future__ import annotations

from enum import Enum
import json
import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

import app.gui.history_screen as history_module
from app.gui.history_screen import HistoryScreen
from app.helpers.history_detail_export import (
    DETAIL_EXPORT_HEADERS,
    build_detail_export_row,
)


@pytest.fixture(scope="module", autouse=True)
def qapplication():
    app = QApplication.instance() or QApplication([])
    yield app


class _EnumValue(str, Enum):
    VALUE = "VALUE"


def _fake_translate(key: str, taal: str = "nl_NL", **kwargs) -> str:
    mapping = {
        "historiek.export.geen_selectie": "geen selectie",
        "historiek.export.leeg": "leeg",
        "historiek.export.detail_fout": "detailfout: {bericht}",
        "historiek.export.detail_geslaagd": "detail ok {aantal} {pad}",
        "historiek.export.detail_ontbreekt": "detail ontbreekt {measurement_id}",
        "historiek.export.scope_gefilterd": "filters",
        "historiek.export.scope_geselecteerd": "selectie",
        "historiek.export.scope_pagina": "pagina",
        "historiek.export.detail_knop": "detail",
        "historiek.export.knop": "export",
        "historiek.export.type_overzicht": "overzicht",
        "historiek.export.type_detail": "detail",
        "historiek.export.type_beide": "beide",
        "historiek.export.geselecteerd_aantal": "{aantal} geselecteerd",
        "historiek.export.bestandsnaam_overzicht": "historiek_overzicht_{timestamp}.csv",
        "historiek.export.bestandsnaam_detail": "historiek_detail_{timestamp}.csv",
        "historiek.export.beide_geslaagd": "beide ok {aantal} {pad}",
        "historiek.kolom.selectie": "kies",
    }
    template = mapping.get(key, key)
    return template.format(**kwargs) if kwargs else template


def _measurement(measurement_id: int):
    return SimpleNamespace(
        id=measurement_id,
        measurement_session_id=10,
        measured_at_ms=1_700_000_000_000 + measurement_id,
        tool_key="ESR_CAPACITOR",
        measurement_method=_EnumValue.VALUE,
        instrument_key="LCR_ST1",
        instrument_name="LCR-ST1 Smart Tweezer",
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
    )


def _overview_row(measurement_id: int):
    return {
        "measurement": _measurement(measurement_id),
        "manufacturer": "TEST",
        "series": "SYNTHETIC",
        "part_number": None,
        "final_status": "aandachtspunt",
        "reliability_level": "laag",
    }


def _detail(measurement_id: int):
    assessment = SimpleNamespace(
        id=50,
        assessed_at_ms=1_700_000_100_000,
        engine_version="1.3.0",
        capacitance_status="goed",
        capacitance_deviation_pct=-1.0638,
        esr_status="aandachtspunt",
        esr_factor=1.67,
        consistency_status="niet_beschikbaar",
        derived_esr_from_d_ohm=None,
        reliability_level="laag",
        final_status="aandachtspunt",
        reasons_json=json.dumps(["capaciteit binnen tolerantie"], ensure_ascii=False),
        warnings_json=json.dumps(["frequentie wijkt af", "generieke referentie"], ensure_ascii=False),
        advice_json=json.dumps(["controleer datasheet"], ensure_ascii=False),
    )
    reference = SimpleNamespace(
        reference_role="ESR_REFERENCE",
        reference_level="algemeen",
        reference_type="ESR",
        manufacturer=None,
        series=None,
        part_number=None,
        reference_value=0.12,
        reference_unit="ohm",
        frequency_hz=100000.0,
        temperature_c=20.0,
        test_voltage_vrms=None,
        dc_bias_v=None,
        value_kind="MAXIMUM",
        source_name="Peak ESR70",
        source_document=None,
        source_version=None,
        source_data_version=None,
        source_entry_id=None,
    )
    return {
        "component_model": SimpleNamespace(
            id=1,
            manufacturer="TEST",
            series="SYNTHETIC",
            part_number=None,
            technology="aluminium_elektrolytisch",
            nominal_capacitance_f=470e-6,
            nominal_capacitance_value=470.0,
            nominal_capacitance_unit="µF",
            rated_voltage_v=25.0,
            voltage_type="DC",
            tolerance_lower_pct=-20.0,
            tolerance_upper_pct=20.0,
        ),
        "component_sample": SimpleNamespace(
            id=2,
            component_model_id=1,
            sample_code=None,
            sample_state=_EnumValue.VALUE,
        ),
        "measurement_session": SimpleNamespace(
            id=10,
            component_sample_id=2,
            customer=None,
            project=None,
            installation=None,
            module_board=None,
            component_reference=None,
        ),
        "measurement": _measurement(measurement_id),
        "assessment_snapshots": [assessment],
        "reference_snapshots_by_assessment_id": {50: [reference]},
    }


class _Service:
    def __init__(self, total=3):
        self.rows = [_overview_row(i + 1) for i in range(total)]
        self.details = {i + 1: _detail(i + 1) for i in range(total)}
        self.calls = []

    def list_measurements(self, filters=None, *, limit=100, offset=0):
        self.calls.append((dict(filters or {}), limit, offset))
        return self.rows[offset: offset + limit]

    def get_measurement_detail(self, measurement_id):
        return self.details.get(measurement_id)


def test_detail_row_contains_raw_inputs_outputs_warnings_and_reference():
    row = build_detail_export_row(_detail(1))

    assert row["measurement_id"] == 1
    assert row["tool_key"] == "ESR_CAPACITOR"
    assert row["frequency_hz"] == 1000.0
    assert row["esr_nominal_capacitance_f"] == pytest.approx(470e-6)
    assert row["esr_measured_capacitance_f"] == pytest.approx(465e-6)
    assert row["esr_measured_esr_ohm"] == pytest.approx(0.2)
    assert row["final_status"] == "aandachtspunt"
    assert row["reliability_level"] == "laag"
    assert "frequentie wijkt af" in row["warnings_text"]
    assert row["reference_value"] == pytest.approx(0.12)
    assert row["reference_frequency_hz"] == pytest.approx(100000.0)
    assert "reference_value" in DETAIL_EXPORT_HEADERS


def test_detail_headers_are_stable_machine_names():
    assert "measurement_id" in DETAIL_EXPORT_HEADERS
    assert "tool_key" in DETAIL_EXPORT_HEADERS
    assert "warnings_text" in DETAIL_EXPORT_HEADERS
    assert "esr_measured_esr_ohm" in DETAIL_EXPORT_HEADERS
    assert "Datum / tijd" not in DETAIL_EXPORT_HEADERS


def test_filter_panel_starts_collapsed(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    screen = HistoryScreen(taal="nl_NL", history_service=_Service())

    assert screen.filter_group.isCheckable()
    assert not screen.filter_group.isChecked()
    assert not screen.filter_body.isVisible()


def test_export_scope_page_does_not_query_all_rows(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    service = _Service(total=3)
    screen = HistoryScreen(taal="nl_NL", history_service=service)
    screen.refresh()

    before = len(service.calls)
    screen.export_scope.setCurrentIndex(screen.export_scope.findData("PAGE"))
    rows = screen._rows_for_export(screen._active_filters())

    assert len(rows) == 3
    assert len(service.calls) == before


def test_export_scope_selection_uses_selected_rows(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    service = _Service(total=3)
    screen = HistoryScreen(taal="nl_NL", history_service=service)
    screen.refresh()

    screen.export_scope.setCurrentIndex(screen.export_scope.findData("SELECTED"))
    screen.table.item(1, 0).setCheckState(Qt.CheckState.Checked)
    rows = screen._rows_for_export(screen._active_filters())

    assert [row["measurement"].id for row in rows] == [2]
    assert screen.selection_count_label.text() == "1 geselecteerd"


def test_export_scope_selection_requires_selection(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    screen = HistoryScreen(taal="nl_NL", history_service=_Service())
    screen.refresh()
    screen.table.clearSelection()

    screen.export_scope.setCurrentIndex(screen.export_scope.findData("SELECTED"))
    rows = screen._rows_for_export(screen._active_filters())

    assert rows is None
    assert screen.state_label.text() == "geen selectie"


def test_detail_export_requests_full_details_only_for_scope(monkeypatch, tmp_path):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    service = _Service(total=3)
    screen = HistoryScreen(taal="nl_NL", history_service=service)
    screen.refresh()

    screen.export_scope.setCurrentIndex(screen.export_scope.findData("PAGE"))
    target = tmp_path / "detail.csv"
    monkeypatch.setattr(
        screen,
        "_choose_export_detail_csv_path",
        lambda: str(target),
    )

    requested = []
    original = service.get_measurement_detail

    def capture(measurement_id):
        requested.append(measurement_id)
        return original(measurement_id)

    service.get_measurement_detail = capture
    screen._export_detail_csv()

    assert requested == [1, 2, 3]
    assert target.exists()
    first_line = target.read_text(encoding="utf-8-sig").splitlines()[0]
    assert "measurement_id" in first_line
    assert "esr_measured_esr_ohm" in first_line


def test_language_switch_updates_detail_button_and_scope(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    screen = HistoryScreen(taal="nl_NL", history_service=_Service())

    screen.apply_language("en_US")

    assert screen.export_btn.text() == "export"
    assert screen.export_scope.itemText(0) == "filters"
    assert screen.export_type_combo.itemText(0) == "overzicht"
    assert screen.export_type_combo.itemText(2) == "beide"


def test_exporttype_dropdown_contains_overview_detail_and_both(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    screen = HistoryScreen(taal="nl_NL", history_service=_Service())

    assert [screen.export_type_combo.itemData(i) for i in range(3)] == [
        "OVERVIEW",
        "DETAIL",
        "BOTH",
    ]


def test_default_export_filename_uses_readable_timestamp(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    screen = HistoryScreen(taal="nl_NL", history_service=_Service())

    assert (
        screen._default_export_filename(
            "OVERVIEW",
            timestamp="2026-10-02_09-15-30",
        )
        == "historiek_overzicht_2026-10-02_09-15-30.csv"
    )
    assert (
        screen._default_export_filename(
            "DETAIL",
            timestamp="2026-10-02_09-15-30",
        )
        == "historiek_detail_2026-10-02_09-15-30.csv"
    )


def test_both_export_writes_matching_timestamp_pair(monkeypatch, tmp_path):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    service = _Service(total=2)
    screen = HistoryScreen(taal="nl_NL", history_service=service)
    screen.refresh()

    screen.export_scope.setCurrentIndex(screen.export_scope.findData("PAGE"))
    monkeypatch.setattr(
        screen,
        "_choose_export_both_directory",
        lambda: str(tmp_path),
    )
    monkeypatch.setattr(
        screen,
        "_export_timestamp",
        lambda: "2026-10-02_09-15-30",
    )
    monkeypatch.setattr(
        screen,
        "_open_export_directory_if_enabled",
        lambda _path: None,
    )

    screen._export_both_csv()

    overview = tmp_path / "historiek_overzicht_2026-10-02_09-15-30.csv"
    detail = tmp_path / "historiek_detail_2026-10-02_09-15-30.csv"
    assert overview.exists()
    assert detail.exists()
    assert "beide ok 2" in screen.state_label.text()
