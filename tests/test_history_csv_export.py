"""
================================================================================
Module:     tests/test_history_csv_export.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.2
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Regressietests voor read-only CSV-export van de volledige
            gefilterde centrale Historiek.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste CSV-exporttests.
  v1.0.1 (2026-10-02)  BOM-assertie gecorrigeerd: echte UTF-8 BOM-bytes
                        controleren i.p.v. letterlijk ge-escapete tekstbytes.
================================================================================
"""

from __future__ import annotations

import csv
import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

import app.gui.history_screen as history_module
from app.gui.history_screen import HistoryScreen
from app.helpers.history_csv_export import write_history_csv


@pytest.fixture(scope="module", autouse=True)
def qapplication():
    app = QApplication.instance() or QApplication([])
    yield app


def _fake_translate(key: str, taal: str = "nl_NL", **kwargs) -> str:
    mapping = {
        "historiek.export.leeg": "geen exportdata",
        "historiek.export.fout": "exportfout: {bericht}",
        "historiek.export.geslaagd": "export ok {aantal} {pad}",
        "historiek.export.knop": "Exporteren",
        "historiek.export.dialoog_titel": "CSV",
        "historiek.export.standaard_bestandsnaam": "historiek.csv",
        "historiek.export.bestandsfilter": "CSV (*.csv)",
    }
    template = mapping.get(key, key)
    return template.format(**kwargs) if kwargs else template


def _measurement(measurement_id: int):
    return SimpleNamespace(
        id=measurement_id,
        measured_at_ms=1_700_000_000_000 + measurement_id,
        tool_key="ESR_CAPACITOR",
        measurement_method="EX_SITU",
        instrument_name="LCR-ST1",
        instrument_key="LCR_ST1",
        capacitance_f=470e-6,
        esr_ohm=0.12,
    )


def _row(measurement_id: int):
    return {
        "measurement": _measurement(measurement_id),
        "manufacturer": "TEST",
        "series": "SERIES",
        "part_number": None,
        "final_status": "waarschijnlijk_goed",
        "reliability_level": "hoog",
    }


class _ExportHistoryService:
    def __init__(self, total: int):
        self.rows = [_row(index + 1) for index in range(total)]
        self.calls = []

    def list_measurements(self, filters=None, *, limit=100, offset=0):
        self.calls.append(
            {
                "filters": dict(filters or {}),
                "limit": limit,
                "offset": offset,
            }
        )
        return self.rows[offset: offset + limit]

    def get_measurement_detail(self, measurement_id):
        return None


def test_csv_writer_uses_utf8_bom_and_semicolon(tmp_path):
    path = tmp_path / "history.csv"

    write_history_csv(
        path,
        ["Kolom A", "Kolom B"],
        [["µF", "120 mΩ"], ["TEST", "ok"]],
    )

    raw = path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle, delimiter=";"))

    assert rows == [
        ["Kolom A", "Kolom B"],
        ["µF", "120 mΩ"],
        ["TEST", "ok"],
    ]


def test_export_uses_all_filtered_rows_not_current_page(monkeypatch, tmp_path):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    service = _ExportHistoryService(total=205)
    screen = HistoryScreen(taal="nl_NL", history_service=service)

    screen.filter_manufacturer.setText("TEST")
    target = tmp_path / "all_rows.csv"
    monkeypatch.setattr(
        screen,
        "_choose_export_csv_path",
        lambda: str(target),
    )

    screen._export_csv()

    export_calls = [call for call in service.calls if call["limit"] == 500]
    assert export_calls
    assert export_calls[0]["offset"] == 0
    assert export_calls[0]["filters"]["manufacturer"] == "TEST"

    with target.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle, delimiter=";"))

    assert len(rows) == 206
    assert rows[0][0] == "historiek.kolom.datum_tijd"
    assert "export ok 205" in screen.state_label.text()


def test_export_reads_multiple_chunks(monkeypatch, tmp_path):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    service = _ExportHistoryService(total=550)
    screen = HistoryScreen(taal="nl_NL", history_service=service)

    target = tmp_path / "chunked.csv"
    monkeypatch.setattr(screen, "_choose_export_csv_path", lambda: str(target))

    screen._export_csv()

    export_calls = [call for call in service.calls if call["limit"] == 500]
    assert [call["offset"] for call in export_calls] == [0, 500]

    with target.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle, delimiter=";"))
    assert len(rows) == 551


def test_empty_export_does_not_open_save_dialog(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    service = _ExportHistoryService(total=0)
    screen = HistoryScreen(taal="nl_NL", history_service=service)

    opened = []
    monkeypatch.setattr(
        screen,
        "_choose_export_csv_path",
        lambda: opened.append(True),
    )

    screen._export_csv()

    assert opened == []
    assert screen.state_label.text() == "geen exportdata"


def test_write_error_is_shown_without_database_change(monkeypatch, tmp_path):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    service = _ExportHistoryService(total=1)
    screen = HistoryScreen(taal="nl_NL", history_service=service)

    target = tmp_path / "cannot_write.csv"
    monkeypatch.setattr(screen, "_choose_export_csv_path", lambda: str(target))

    def _raise(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(history_module, "write_history_csv", _raise)

    screen._export_csv()

    assert "exportfout: disk full" in screen.state_label.text()
    assert not target.exists()


def test_language_switch_updates_export_button(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    service = _ExportHistoryService(total=0)
    screen = HistoryScreen(taal="nl_NL", history_service=service)

    screen.apply_language("en_US")

    assert screen.export_btn.text() == "Exporteren"
