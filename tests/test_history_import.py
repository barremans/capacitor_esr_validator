"""
================================================================================
Module:     tests/test_history_import.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-27
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de pure parser en validator van de
            historiek-import (C1). Geen Qt, geen database.
================================================================================
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from app.helpers.history_detail_export import DETAIL_EXPORT_HEADERS
from app.helpers.history_import import (
    ImportValidatieFout,
    bereken_natural_key,
    lees_csv_rijen,
    lees_xlsx_rijen,
    parse_bestand,
    parse_rijen,
)


def _basis_rij(**overrides):
    rij = {kolom: "" for kolom in DETAIL_EXPORT_HEADERS}
    rij.update(
        {
            "measurement_id": "1",
            "tool_key": "ESR_CAPACITOR",
            "measured_at_ms": "1700000000000",
            "measurement_method": "EX_SITU",
            "sample_state": "NEW",
            "manufacturer": "TEST",
            "series": "S1",
            "part_number": "P1",
            "technology": "ALUMINIUM",
            "esr_nominal_capacitance_value": "470",
            "esr_nominal_capacitance_unit": "µF",
            "esr_nominal_capacitance_f": "0.00047",
            "esr_rated_voltage_v": "25",
            "esr_voltage_type": "DC",
            "esr_measured_capacitance_f": "0.000465",
            "esr_measured_esr_ohm": "0.2",
            "frequency_hz": "1000",
            "test_voltage_vrms": "0.6",
            "temperature_c": "20",
            "out_of_range": "False",
            "open_suspected": "False",
            "short_suspected": "False",
            "unstable_reading": "False",
            "assessed_at_ms": "1700000100000",
            "assessment_engine_version": "1.0",
            "final_status": "GOOD",
            "reliability_level": "HIGH",
            "esr_capacitance_status": "goed",
            "esr_esr_status": "goed",
        }
    )
    rij.update(overrides)
    return rij


def _rijen(*rijen):
    kop = list(DETAIL_EXPORT_HEADERS)
    return [kop] + [[rij.get(kolom, "") for kolom in kop] for rij in rijen]


def test_parse_rijen_accepts_valid_row():
    resultaat = parse_rijen(_rijen(_basis_rij()))

    assert len(resultaat.ketens) == 1
    assert resultaat.fouten == ()
    keten = resultaat.ketens[0]
    assert keten.tool_key == "ESR_CAPACITOR"
    assert keten.component_model["manufacturer"] == "TEST"
    assert keten.measurement["esr_ohm"] == pytest.approx(0.2)
    assert keten.assessment_snapshot is not None
    assert keten.assessment_snapshot["final_status"] == "GOOD"
    assert len(keten.natural_key) == 64


def test_parse_rijen_rejects_missing_columns():
    kop = list(DETAIL_EXPORT_HEADERS)
    kop.remove("tool_key")
    with pytest.raises(ImportValidatieFout):
        parse_rijen([kop, [""] * len(kop)])


def test_parse_rijen_reports_invalid_enum_values():
    resultaat = parse_rijen(
        _rijen(_basis_rij(measurement_method="ONBEKEND", sample_state="NEW"))
    )

    assert resultaat.ketens == ()
    assert any(fout.kolom == "measurement_method" for fout in resultaat.fouten)


def test_parse_rijen_rejects_negative_measured_at_ms():
    resultaat = parse_rijen(_rijen(_basis_rij(measured_at_ms="-5")))

    assert resultaat.ketens == ()
    assert any(fout.kolom == "measured_at_ms" for fout in resultaat.fouten)


def test_parse_rijen_rejects_non_finite_numeric():
    resultaat = parse_rijen(_rijen(_basis_rij(frequency_hz="nan")))

    assert resultaat.ketens == ()
    assert any(fout.kolom == "frequency_hz" for fout in resultaat.fouten)


def test_parse_rijen_rejects_corrupt_json():
    resultaat = parse_rijen(_rijen(_basis_rij(reasons_json="{niet json")))

    assert resultaat.ketens == ()
    assert any(fout.kolom == "reasons_json" for fout in resultaat.fouten)


def test_parse_rijen_skips_unknown_tool_key_with_message():
    resultaat = parse_rijen(_rijen(_basis_rij(tool_key="ANDER_TOOL")))

    assert resultaat.ketens == ()
    assert any(
        fout.kolom == "tool_key" and "niet ondersteund" in fout.bericht
        for fout in resultaat.fouten
    )


def test_parse_rijen_dedups_identical_rows_in_same_file():
    rij = _basis_rij()
    resultaat = parse_rijen(_rijen(rij, rij))

    assert len(resultaat.ketens) == 1
    assert any(
        fout.kolom == "natural_key" for fout in resultaat.fouten
    )


def test_natural_key_is_stable_for_equal_content():
    keten_a = parse_rijen(_rijen(_basis_rij())).ketens[0]
    keten_b = parse_rijen(_rijen(_basis_rij())).ketens[0]

    assert bereken_natural_key(keten_a) == keten_b.natural_key


def test_parse_csv_file_roundtrip(tmp_path):
    pad = tmp_path / "import.csv"
    kop = list(DETAIL_EXPORT_HEADERS)
    rij = _basis_rij()
    with pad.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(kop)
        writer.writerow([rij.get(kolom, "") for kolom in kop])

    resultaat = parse_bestand(pad)

    assert len(resultaat.ketens) == 1
    assert resultaat.ketens[0].measurement["esr_ohm"] == pytest.approx(0.2)


def test_parse_xlsx_file_roundtrip(tmp_path):
    from openpyxl import Workbook

    pad = tmp_path / "import.xlsx"
    kop = list(DETAIL_EXPORT_HEADERS)
    rij = _basis_rij()
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(kop)
    sheet.append([rij.get(kolom, "") for kolom in kop])
    workbook.save(pad)
    workbook.close()

    resultaat = parse_bestand(pad)

    assert len(resultaat.ketens) == 1
    assert resultaat.ketens[0].measurement["esr_ohm"] == pytest.approx(0.2)


def test_parse_bestand_rejects_unknown_extension(tmp_path):
    pad = tmp_path / "import.txt"
    pad.write_text("x", encoding="utf-8")

    with pytest.raises(ImportValidatieFout):
        parse_bestand(pad)


def test_references_json_is_split_into_reference_snapshots():
    refs = [
        {
            "reference_role": "ESR_REFERENCE",
            "reference_level": "algemeen",
            "reference_value": 0.12,
            "reference_unit": "ohm",
        }
    ]
    resultaat = parse_rijen(_rijen(_basis_rij(references_json=json.dumps(refs))))

    keten = resultaat.ketens[0]
    assert len(keten.reference_snapshots) == 1
    assert keten.reference_snapshots[0]["reference_value"] == pytest.approx(0.12)