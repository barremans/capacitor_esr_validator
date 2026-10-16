"""
================================================================================
Module:     tests/test_report_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.2.0
Datum:      2026-10-16
Auteur:     Bart Bossuyt

Doel:       GUI-regressietests voor ReportDialog.

Wijzigingen:
  v1.0.0 (2026-10-10)  Eerste versie.
  v1.1.0 (2026-10-11)  Fase 8D: test voor grafiek_default-parameter.
  v1.2.0 (2026-10-16)  Fase 11A.2: tests voor for_measurements classmethod,
                        scope-parameter, en het uitschakelen van de grafiek
                        bij meerdere metingen.
================================================================================
"""

from __future__ import annotations

import os
from enum import Enum
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from app.gui.dialogs.report_dialog import ReportDialog


@pytest.fixture(scope="module", autouse=True)
def qapplication():
    app = QApplication.instance() or QApplication([])
    yield app


class _EnumValue(str, Enum):
    VALUE = "VALUE"


def _detail(measurement_id: int = 42, *, tool_key: str = "ESR_CAPACITOR"):
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
        "measurement": SimpleNamespace(
            id=measurement_id,
            measurement_session_id=10,
            measured_at_ms=1_700_000_000_000 + measurement_id,
            tool_key=tool_key,
            measurement_method=_EnumValue.VALUE,
            instrument_key="LCR_ST1",
            instrument_name="LCR-ST1",
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
        ),
        "assessment_snapshots": [],
        "reference_snapshots_by_assessment_id": {},
    }


class _StubReportService:
    def __init__(self, detail=None, *, details_by_id=None):
        self._detail = detail or _detail()
        self._details_by_id = details_by_id or {self._detail["measurement"].id: self._detail}
        self.calls: list[tuple[str, object]] = []

    def build_bundle(self, measurement_id, *, taal, werkplaats="", auteur="", scope="", rapportdatum=None):
        from app.services.report_service import ReportBundle

        self.calls.append(("build_bundle", int(measurement_id)))
        return ReportBundle(
            details=(self._detail,),
            taal=taal,
            rapportdatum=rapportdatum or "2026-10-10 09:00:00",
            app_versie="0.1.0-dev",
            werkplaats=werkplaats,
            auteur=auteur,
            scope=scope,
        )

    def build_bundle_for_measurements(
        self, measurement_ids, *, taal, werkplaats="", auteur="",
        scope="", rapportdatum=None,
    ):
        from app.services.report_service import ReportBundle

        self.calls.append(("build_bundle_for_measurements", list(measurement_ids)))
        details = tuple(
            self._details_by_id[mid] for mid in measurement_ids
        )
        return ReportBundle(
            details=details,
            taal=taal,
            rapportdatum=rapportdatum or "2026-10-10 09:00:00",
            app_versie="0.1.0-dev",
            werkplaats=werkplaats,
            auteur=auteur,
            scope=scope,
        )


class _StubAnalysisService:
    def __init__(self, esr_reeks=None):
        from app.helpers.analysis_series import TimeSeriesPoint

        self._esr = esr_reeks or [
            TimeSeriesPoint(x_ms=1_700_000_000_000, y=0.1, measurement_id=1, tool_key="ESR_CAPACITOR"),
            TimeSeriesPoint(x_ms=1_700_000_100_000, y=0.2, measurement_id=2, tool_key="ESR_CAPACITOR"),
        ]

    def esr_series(self, filters=None, *, aggregation="raw"):
        return list(self._esr)

    def capacitance_series(self, filters=None, *, aggregation="raw"):
        return []

    def dissipation_series(self, filters=None, *, aggregation="raw"):
        return []

    def scatter_esr_vs_capacitance(self, filters=None):
        return []


def test_dialog_bouwt_preview():
    dialog = ReportDialog(
        42,
        taal="nl_NL",
        report_service=_StubReportService(),
        analysis_service=_StubAnalysisService(),
    )
    html = dialog.preview.toHtml()

    assert "Meetrapport" in html or "meetrapport" in html.lower()
    assert dialog._html


def test_dialog_toont_geen_grafiek_bij_niet_esr():
    detail = _detail(tool_key="RESISTOR")
    dialog = ReportDialog(
        42,
        taal="nl_NL",
        report_service=_StubReportService(detail),
        analysis_service=_StubAnalysisService(),
    )
    assert dialog._grafiek_beschikbaar is False
    assert not dialog.grafiek_checkbox.isEnabled()


# ============================================================================
# grafiek_default
# ============================================================================

def test_dialog_grafiek_checkbox_start_uit_default():
    dialog = ReportDialog(
        42,
        taal="nl_NL",
        report_service=_StubReportService(),
        analysis_service=_StubAnalysisService(),
        grafiek_default=False,
    )
    assert dialog.grafiek_checkbox.isChecked() is False
    assert dialog._chart_png_base64 is None


def test_dialog_grafiek_checkbox_start_aan_met_default():
    dialog = ReportDialog(
        42,
        taal="nl_NL",
        report_service=_StubReportService(),
        analysis_service=_StubAnalysisService(),
        grafiek_default=True,
    )
    assert dialog.grafiek_checkbox.isChecked() is True


def test_dialog_grafiek_checkbox_laadt_chart():
    dialog = ReportDialog(
        42,
        taal="nl_NL",
        report_service=_StubReportService(),
        analysis_service=_StubAnalysisService(),
        grafiek_default=False,
    )
    assert dialog._grafiek_beschikbaar is True
    assert dialog._chart_png_base64 is None

    dialog.grafiek_checkbox.setChecked(True)
    dialog._on_grafiek_toggled(2)

    assert dialog._chart_png_base64 is not None
    assert "data:image/png;base64," in dialog._html


# ============================================================================
# Opslaan
# ============================================================================

def test_dialog_opslaan_html(tmp_path, monkeypatch):
    dialog = ReportDialog(
        42,
        taal="nl_NL",
        report_service=_StubReportService(),
        analysis_service=_StubAnalysisService(),
    )
    doel = tmp_path / "rapport.html"
    monkeypatch.setattr(
        "app.gui.dialogs.report_dialog.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(doel), "HTML-bestanden (*.html)"),
    )
    monkeypatch.setattr(
        "app.gui.dialogs.report_dialog.QMessageBox.information",
        lambda *args, **kwargs: None,
    )

    dialog._opslaan_html()

    assert doel.exists()
    assert "Meetrapport" in doel.read_text(encoding="utf-8")


def test_dialog_opslaan_pdf(tmp_path, monkeypatch):
    dialog = ReportDialog(
        42,
        taal="nl_NL",
        report_service=_StubReportService(),
        analysis_service=_StubAnalysisService(),
    )
    doel = tmp_path / "rapport.pdf"
    monkeypatch.setattr(
        "app.gui.dialogs.report_dialog.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(doel), "PDF-bestanden (*.pdf)"),
    )
    monkeypatch.setattr(
        "app.gui.dialogs.report_dialog.QMessageBox.information",
        lambda *args, **kwargs: None,
    )

    dialog._opslaan_pdf()

    assert doel.exists()
    assert doel.read_bytes()[:5] == b"%PDF-"


def test_dialog_toont_fout_bij_service_fout(monkeypatch):
    class _FouteService:
        def build_bundle(self, *args, **kwargs):
            raise ValueError("kapot")
        def build_bundle_for_measurements(self, *args, **kwargs):
            raise ValueError("kapot")

    monkeypatch.setattr(
        "app.gui.dialogs.report_dialog.QMessageBox.warning",
        lambda *args, **kwargs: None,
    )

    dialog = ReportDialog(
        42,
        taal="nl_NL",
        report_service=_FouteService(),
        analysis_service=_StubAnalysisService(),
    )
    assert dialog._bundle is None
    assert dialog._html == ""


# ============================================================================
# Fase 11A.2 — for_measurements
# ============================================================================

def test_for_measurements_bouwt_bundle_met_meerdere_ids():
    detail_1 = _detail(measurement_id=1)
    detail_2 = _detail(measurement_id=2)
    service = _StubReportService(
        details_by_id={1: detail_1, 2: detail_2}
    )
    dialog = ReportDialog.for_measurements(
        [1, 2],
        scope="selectie",
        taal="nl_NL",
        report_service=service,
        analysis_service=_StubAnalysisService(),
    )
    assert dialog._bundle is not None
    assert dialog._bundle.aantal_metingen == 2
    assert dialog._bundle.scope == "selectie"
    assert service.calls[-1] == ("build_bundle_for_measurements", [1, 2])


def test_for_measurements_met_lege_lijst_faalt():
    with pytest.raises(ValueError):
        ReportDialog.for_measurements(
            [],
            taal="nl_NL",
            report_service=_StubReportService(),
            analysis_service=_StubAnalysisService(),
        )


def test_for_measurements_kop_toont_aantal():
    detail_1 = _detail(measurement_id=1)
    detail_2 = _detail(measurement_id=2)
    service = _StubReportService(
        details_by_id={1: detail_1, 2: detail_2}
    )
    dialog = ReportDialog.for_measurements(
        [1, 2],
        scope="selectie",
        taal="nl_NL",
        report_service=service,
        analysis_service=_StubAnalysisService(),
    )
    assert "2" in dialog.kop_label.text()


def test_for_measurements_grafiek_uitgeschakeld():
    detail_1 = _detail(measurement_id=1)
    detail_2 = _detail(measurement_id=2)
    service = _StubReportService(
        details_by_id={1: detail_1, 2: detail_2}
    )
    dialog = ReportDialog.for_measurements(
        [1, 2],
        scope="selectie",
        taal="nl_NL",
        report_service=service,
        analysis_service=_StubAnalysisService(),
    )
    assert dialog._grafiek_beschikbaar is False
    assert dialog.grafiek_checkbox.isEnabled() is False
    assert dialog.grafiek_hint.text() != ""


def test_for_measurements_html_bevat_scope_in_kop():
    detail_1 = _detail(measurement_id=1)
    detail_2 = _detail(measurement_id=2)
    service = _StubReportService(
        details_by_id={1: detail_1, 2: detail_2}
    )
    dialog = ReportDialog.for_measurements(
        [1, 2],
        scope="Selectie",
        taal="nl_NL",
        report_service=service,
        analysis_service=_StubAnalysisService(),
    )
    assert "Selectie" in dialog._html


def test_single_measurement_met_scope_enkel_gebruikt_build_bundle():
    service = _StubReportService()
    dialog = ReportDialog(
        42,
        taal="nl_NL",
        report_service=service,
        analysis_service=_StubAnalysisService(),
        scope="Eén meting",
    )
    assert dialog._bundle.scope == "Eén meting"
    assert service.calls[-1] == ("build_bundle", 42)