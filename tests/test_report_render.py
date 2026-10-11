"""
================================================================================
Module:     tests/test_report_render.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.2.1
Datum:      2026-10-10
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de pure HTML-renderer. Geen Qt, geen
            database. Bewijst dat de renderer read-only is, dat alle vaste
            secties aanwezig zijn, en dat de renderer multitool werkt
            (specifieke secties voor ESR_CAPACITOR, generieke fallback
            voor andere tools).

Wijzigingen:
  v1.0.0 (2026-10-10)  Eerste versie.
  v1.1.0 (2026-10-10)  Multitool: meerdere metingen, generieke fallback,
                        chart_png_base64_per_meting parameter.
  v1.2.0 (2026-10-10)  Extra tests voor gemengde tools, meerdere metingen
                        en scopelabel.
  v1.2.1 (2026-10-10)  Fix: generieke-fallback-tests gebruiken nu
                        vertaal("report.geen_renderer", ...) in plaats van
                        een letterlijke string. De vorige assertie zocht
                        "Geen gespecialiseerde rapportweergave" (hoofdletter),
                        terwijl de werkelijke NL-vertaling begint met "Voor
                        dit tooltype is nog geen gespecialiseerde...". De
                        test koppelt nu aan de i18n-laag en is robuust
                        tegen kleine formuleringwijzigingen.
================================================================================
"""

from __future__ import annotations

import json
from enum import Enum
from types import SimpleNamespace

import pytest

from app.helpers.i18n import vertaal
from app.helpers.report_render import render_measurement_report_html
from app.services.report_service import ReportBundle


class _EnumValue(str, Enum):
    VALUE = "VALUE"


def _detail(measurement_id: int = 42, *, tool_key: str = "ESR_CAPACITOR", measured_at_ms: int | None = None):
    assessment = SimpleNamespace(
        id=50 + measurement_id,
        assessed_at_ms=1_700_000_100_000 + measurement_id,
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
        warnings_json=json.dumps(
            ["frequentie wijkt af", "generieke referentie"], ensure_ascii=False
        ),
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
    measurement = SimpleNamespace(
        id=measurement_id,
        measurement_session_id=10,
        measured_at_ms=measured_at_ms if measured_at_ms is not None else 1_700_000_000_000,
        tool_key=tool_key,
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
            started_at_ms=1_700_000_000_000,
            ended_at_ms=1_700_000_100_000,
            operator_name=None,
            customer=None,
            project=None,
            installation=None,
            module_board=None,
            component_reference=None,
            notes=None,
        ),
        "measurement": measurement,
        "assessment_snapshots": [assessment],
        "reference_snapshots_by_assessment_id": {50 + measurement_id: [reference]},
    }


def _bundle(
    *details,
    taal: str = "nl_NL",
    scope: str = "",
    werkplaats: str = "Labo A",
) -> ReportBundle:
    if not details:
        details = (_detail(),)
    return ReportBundle(
        details=tuple(details),
        taal=taal,
        rapportdatum="2026-10-10 09:00:00",
        app_versie="0.1.0-dev",
        werkplaats=werkplaats,
        scope=scope,
    )


# ---------------------------------------------------------------------------
# Structuur
# ---------------------------------------------------------------------------

def test_render_returns_full_html_document():
    html = render_measurement_report_html(_bundle())

    assert html.startswith("<!DOCTYPE html>")
    assert "<html>" in html
    assert "</html>" in html
    assert "<style>" in html


def test_render_contains_all_fixed_sections_in_dutch():
    html = render_measurement_report_html(_bundle(taal="nl_NL"))

    assert "Meetrapport" in html
    assert "Componentidentificatie" in html
    assert "Meetcontext" in html
    assert "Ruwe meetwaarden" in html
    assert "Assessment-snapshot" in html
    assert "Referentie-snapshot" in html
    assert "read-only" in html


def test_render_contains_all_fixed_sections_in_english():
    html = render_measurement_report_html(_bundle(taal="en_US"))

    assert "Measurement report" in html
    assert "Component identification" in html
    assert "Measurement context" in html
    assert "Raw measurement values" in html
    assert "Assessment snapshot" in html
    assert "Reference snapshot" in html
    assert "read-only" in html


def test_render_includes_rapportdatum_and_werkplaats():
    html = render_measurement_report_html(_bundle())

    assert "2026-10-10 09:00:00" in html
    assert "Labo A" in html


def test_render_omits_werkplaats_when_empty():
    html = render_measurement_report_html(_bundle(werkplaats=""))

    assert "Werkplaats" not in html


def test_render_includes_scope_when_set():
    html = render_measurement_report_html(_bundle(scope="selectie"))

    assert "selectie" in html


# ---------------------------------------------------------------------------
# Inhoud (ESR_CAPACITOR)
# ---------------------------------------------------------------------------

def test_render_contains_measurement_values():
    html = render_measurement_report_html(_bundle())

    assert "465" in html
    assert "200" in html
    assert "LCR-ST1" in html


def test_render_contains_assessment_reasons_warnings_advice():
    html = render_measurement_report_html(_bundle())

    assert "capaciteit binnen tolerantie" in html
    assert "frequentie wijkt af" in html
    assert "generieke referentie" in html
    assert "controleer datasheet" in html


def test_render_contains_reference_snapshot():
    html = render_measurement_report_html(_bundle())

    assert "ESR_REFERENCE" in html
    assert "Peak ESR70" in html
    assert "MAXIMUM" in html


def test_render_handles_no_assessment_gracefully():
    detail = _detail()
    detail["assessment_snapshots"] = []
    detail["reference_snapshots_by_assessment_id"] = {}
    html = render_measurement_report_html(_bundle(detail))

    assert "Geen assessment-snapshot" in html


def test_render_handles_missing_references_gracefully():
    detail = _detail()
    detail["reference_snapshots_by_assessment_id"] = {}
    html = render_measurement_report_html(_bundle(detail))

    assert "Geen referentie-snapshots" in html


# ---------------------------------------------------------------------------
# Multitool
# ---------------------------------------------------------------------------

def test_render_uses_generic_fallback_for_unknown_tool():
    """Voor een onbekende tool_key gebruikt de renderer de generieke fallback.

    De test koppelt aan de i18n-laag (report.geen_renderer) in plaats van
    aan een letterlijke string, zodat kleine formuleringwijzigingen in de
    vertaling de test niet breken.
    """
    detail = _detail(measurement_id=1, tool_key="RESISTOR")
    html = render_measurement_report_html(_bundle(detail))

    verwachte_tekst = vertaal("report.geen_renderer", taal="nl_NL")
    assert verwachte_tekst in html
    # Geen ESR-specifieke secties:
    assert "Ruwe meetwaarden" not in html
    assert "Assessment-snapshot" not in html
    # Maar wel de generieke kop:
    assert "Componentidentificatie" in html


def test_render_multiple_measurements_in_one_report():
    d1 = _detail(measurement_id=1, measured_at_ms=1000)
    d2 = _detail(measurement_id=2, measured_at_ms=2000)
    html = render_measurement_report_html(_bundle(d1, d2))

    assert "2 metingen in dit rapport" in html
    assert "Meting 1" in html
    assert "Meting 2" in html


def test_render_single_measurement_has_no_meting_kop():
    html = render_measurement_report_html(_bundle(_detail()))

    assert "Meting 1" not in html
    assert "1 metingen" not in html


def test_render_mixed_tools_dispatch_per_measurement():
    """ESR_CAPACITOR en een onbekende tool in één rapport: per meting dispatch.

    De test koppelt aan de i18n-laag (report.geen_renderer) in plaats van
    aan een letterlijke string.
    """
    esr = _detail(measurement_id=1, tool_key="ESR_CAPACITOR", measured_at_ms=1000)
    res = _detail(measurement_id=2, tool_key="RESISTOR", measured_at_ms=2000)
    html = render_measurement_report_html(_bundle(esr, res))

    assert "ESR / Condensator" in html or "ESR_CAPACITOR" in html
    verwachte_tekst = vertaal("report.geen_renderer", taal="nl_NL")
    assert verwachte_tekst in html
    assert "Meting 1" in html
    assert "Meting 2" in html


# ---------------------------------------------------------------------------
# Grafiek (parameter)
# ---------------------------------------------------------------------------

def test_render_includes_chart_when_provided():
    detail = _detail(measurement_id=42)
    html = render_measurement_report_html(
        _bundle(detail),
        chart_png_base64_per_meting={42: "aGVsbG8="},
    )

    assert "Grafiek" in html
    assert "data:image/png;base64,aGVsbG8=" in html


def test_render_omits_chart_when_not_provided():
    html = render_measurement_report_html(_bundle())

    assert "Grafiek" not in html


# ---------------------------------------------------------------------------
# Read-only
# ---------------------------------------------------------------------------

def test_render_is_pure_and_does_not_mutate_details():
    detail = _detail()
    before = {k: id(v) for k, v in detail.items()}
    html = render_measurement_report_html(_bundle(detail))

    after = {k: id(v) for k, v in detail.items()}
    assert before == after
    assert html


def test_render_requires_details():
    class _ZonderDetails:
        taal = "nl_NL"
        rapportdatum = "2026-10-10 09:00:00"
        app_versie = "0.1.0-dev"
        werkplaats = ""
        scope = ""

    with pytest.raises(ValueError):
        render_measurement_report_html(_ZonderDetails())