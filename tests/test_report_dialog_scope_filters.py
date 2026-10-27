"""
================================================================================
Module:     tests/test_report_dialog_scope_filters.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.2
Datum:      2026-10-27
Auteur:     Bart Bossuyt

Doel:       Regressietests voor fase 12E (scope "Huidige filters",
            §2.14) in ReportDialog, HistoryScreen en AnalysisScreen.
            Geen qtbot; lokale _app() en processEvents() waar nodig.

Wijzigingen:
  v1.0.0 (2026-10-22)  Eerste versie.
  v1.0.1 (2026-10-22)  Fix: _FakeDialog.__init__ registreert niet meer
                       in recorder. Alleen de classmethods registreren.
                       De constructor-registratie was bedoeld voor de
                       enkelvoudige ReportDialog(id, ...)-flow, maar
                       werd ook aangeroepen door cls() in de
                       classmethods, waardoor elke aanroep twee keer
                       in recorder verscheen.
  v1.0.2 (2026-10-27)  Fase 5C: test_analysis_report_met_selectie_
                       blijft_for_measurements volgt nu de echte
                       GUI-flow (stub-service met een rij id=77,
                       refresh(), dan die rij aanvinken). De oude
                       variant zette handmatig een rij die niet uit
                       de service kwam; sinds AnalysisScreen v1.9.1
                       triggert setItem een refresh(preserve_selection=
                       True), waardoor die rij weer verdween en de
                       test op for_filters uitkwam. Nieuwe test
                       test_analysis_handmatige_rij_zonder_service_
                       gebruikt_for_filters legt het bewuste gedrag
                       vast: een rij die niet uit de service komt,
                       verdwijnt na de automatische refresh.
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


def _overview_row(measurement_id: int):
    """Rij zoals StorageService.list_measurements() die teruggeeft."""
    from app.helpers.analysis_series import TimeSeriesPoint  # noqa: F401

    return {
        "measurement": _detail(measurement_id)["measurement"],
        "manufacturer": "TEST",
        "series": "SYNTHETIC",
        "part_number": None,
        "final_status": None,
        "reliability_level": None,
    }


class _StubReportService:
    def __init__(self, *, details_by_id=None, filters_result_ids=None):
        self._details_by_id = details_by_id or {42: _detail(42)}
        self._filters_result_ids = filters_result_ids or [42]
        self.calls: list[tuple[str, object]] = []
        self.filters_seen: list[dict] = []

    def build_bundle(self, measurement_id, *, taal, werkplaats="", auteur="", scope="", rapportdatum=None):
        from app.services.report_service import ReportBundle

        self.calls.append(("build_bundle", int(measurement_id)))
        return ReportBundle(
            details=(self._details_by_id[int(measurement_id)],),
            taal=taal,
            rapportdatum=rapportdatum or "2026-10-22 09:00:00",
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
            rapportdatum=rapportdatum or "2026-10-22 09:00:00",
            app_versie="0.1.0-dev",
            werkplaats=werkplaats,
            auteur=auteur,
            scope=scope,
        )

    def build_bundle_from_filters(
        self, filters, *, taal, werkplaats="", auteur="",
        scope="", rapportdatum=None, max_metingen=500,
    ):
        from app.services.report_service import ReportBundle

        self.calls.append(("build_bundle_from_filters", dict(filters)))
        self.filters_seen.append(dict(filters))
        details = tuple(
            self._details_by_id[mid] for mid in self._filters_result_ids
        )
        return ReportBundle(
            details=details,
            taal=taal,
            rapportdatum=rapportdatum or "2026-10-22 09:00:00",
            app_versie="0.1.0-dev",
            werkplaats=werkplaats,
            auteur=auteur,
            scope=scope,
        )


class _StubAnalysisService:
    def __init__(self):
        from app.helpers.analysis_series import TimeSeriesPoint

        self._esr = [
            TimeSeriesPoint(
                x_ms=1_700_000_000_000,
                y=0.1,
                measurement_id=1,
                tool_key="ESR_CAPACITOR",
            ),
        ]

    def esr_series(self, filters=None, *, aggregation="raw", measurement_ids=None):
        return list(self._esr)

    def capacitance_series(self, filters=None, *, aggregation="raw", measurement_ids=None):
        return []

    def dissipation_series(self, filters=None, *, aggregation="raw", measurement_ids=None):
        return []

    def scatter_esr_vs_capacitance(self, filters=None, *, measurement_ids=None):
        return []


class _StubAnalysisServiceMetRij:
    """Stub die load_rows ondersteunt, zodat de selectietabel gevuld wordt.

    Wordt gebruikt in test_analysis_report_met_selectie_blijft_for_
    measurements: de test volgt de echte GUI-flow (refresh() vult de
    tabel, dan vinkt de test een bestaande rij aan) in plaats van
    handmatig een rij te zetten die niet uit de service komt.
    """

    def __init__(self, measurement_id: int = 77):
        from app.helpers.analysis_series import TimeSeriesPoint

        self._measurement_id = int(measurement_id)
        self._rows = [_overview_row(self._measurement_id)]
        self._esr = [
            TimeSeriesPoint(
                x_ms=1_700_000_000_000,
                y=0.1,
                measurement_id=self._measurement_id,
                tool_key="ESR_CAPACITOR",
            ),
        ]
        self.measurement_id_calls: list[list[int] | None] = []

    def load_rows(self, filters=None, *, measurement_ids=None):
        self.measurement_id_calls.append(
            list(measurement_ids) if measurement_ids is not None else None
        )
        return list(self._rows)

    def esr_series(self, filters=None, *, aggregation="raw", measurement_ids=None):
        return list(self._esr)

    def capacitance_series(self, filters=None, *, aggregation="raw", measurement_ids=None):
        return []

    def dissipation_series(self, filters=None, *, aggregation="raw", measurement_ids=None):
        return []

    def scatter_esr_vs_capacitance(self, filters=None, *, measurement_ids=None):
        return []


def _sample_filters() -> dict:
    return {
        "tool_key": "ESR_CAPACITOR",
        "manufacturer": "TEST",
        "measured_from_ms": 1_700_000_000_000,
    }


def _fake_dialog_klasse(recorder):
    """Fake ReportDialog die alleen classmethod-aanroepen registreert.

    De __init__ doet bewust NIETS met recorder. Bij de vorige versie
    registreerde __init__ een ('single', ...)-rij, waardoor elke
    classmethod-aanroep (die cls() aanroept) twee entries opleverde.
    """

    class _FakeDialog:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        def exec(self):
            return 0

        @classmethod
        def for_measurements(cls, ids, **kwargs):
            recorder.append(("for_measurements", list(ids), kwargs))
            return cls()

        @classmethod
        def for_filters(cls, filters, **kwargs):
            recorder.append(("for_filters", dict(filters), kwargs))
            return cls()

    return _FakeDialog


# ------------------------------------------------------------------ ReportDialog.for_filters

def test_for_filters_roept_build_bundle_from_filters_aan():
    service = _StubReportService()
    filters = _sample_filters()

    dialog = ReportDialog.for_filters(
        filters,
        scope="Huidige filters",
        taal="nl_NL",
        report_service=service,
        analysis_service=_StubAnalysisService(),
    )

    assert service.calls[-1][0] == "build_bundle_from_filters"
    assert service.filters_seen[-1] == filters
    assert dialog._bundle is not None


def test_for_filters_scope_wordt_doorgegeven():
    service = _StubReportService()
    dialog = ReportDialog.for_filters(
        _sample_filters(),
        scope="Huidige filters",
        taal="nl_NL",
        report_service=service,
        analysis_service=_StubAnalysisService(),
    )
    assert dialog._bundle.scope == "Huidige filters"


def test_for_filters_grafiek_uitgeschakeld():
    service = _StubReportService(filters_result_ids=[1, 2])
    service._details_by_id = {1: _detail(1), 2: _detail(2)}
    dialog = ReportDialog.for_filters(
        _sample_filters(),
        scope="Huidige filters",
        taal="nl_NL",
        report_service=service,
        analysis_service=_StubAnalysisService(),
    )
    assert dialog._grafiek_beschikbaar is False
    assert dialog.grafiek_checkbox.isEnabled() is False
    assert dialog.grafiek_hint.text() != ""


def test_for_filters_kop_toont_aantal():
    service = _StubReportService(filters_result_ids=[1, 2, 3])
    service._details_by_id = {
        1: _detail(1), 2: _detail(2), 3: _detail(3)
    }
    dialog = ReportDialog.for_filters(
        _sample_filters(),
        scope="Huidige filters",
        taal="nl_NL",
        report_service=service,
        analysis_service=_StubAnalysisService(),
    )
    assert "3" in dialog.kop_label.text()


def test_for_filters_ongeldige_filters_faalt():
    with pytest.raises(ValueError):
        ReportDialog.for_filters(
            "geen-mapping",  # type: ignore[arg-type]
            taal="nl_NL",
            report_service=_StubReportService(),
            analysis_service=_StubAnalysisService(),
        )


def test_for_filters_service_value_error_wordt_afgevangen(monkeypatch):
    class _FouteService:
        def build_bundle_from_filters(self, *args, **kwargs):
            raise ValueError("kapot")

    monkeypatch.setattr(
        "app.gui.dialogs.report_dialog.QMessageBox.warning",
        lambda *args, **kwargs: None,
    )

    dialog = ReportDialog.for_filters(
        _sample_filters(),
        taal="nl_NL",
        report_service=_FouteService(),
        analysis_service=_StubAnalysisService(),
    )
    assert dialog._bundle is None
    assert dialog._html == ""


def test_for_filters_html_bevat_scope_in_kop():
    service = _StubReportService()
    dialog = ReportDialog.for_filters(
        _sample_filters(),
        scope="Huidige filters",
        taal="nl_NL",
        report_service=service,
        analysis_service=_StubAnalysisService(),
    )
    assert "Huidige filters" in dialog._html


# ------------------------------------------------------------------ HistoryScreen

def _maak_history_screen(*, filters_actief: bool = False):
    from app.gui.history_screen import HistoryScreen

    screen = HistoryScreen(taal="nl_NL")
    if filters_actief:
        screen.filter_group.setChecked(True)
        screen.filter_manufacturer.setText("TEST")
        screen.filter_tool.setCurrentIndex(
            screen.filter_tool.findData("ESR_CAPACITOR")
        )
    return screen


def _patch_report_dialog_in_history(monkeypatch, recorder):
    monkeypatch.setattr(
        "app.gui.dialogs.report_dialog.ReportDialog",
        _fake_dialog_klasse(recorder),
    )


def test_history_report_zonder_selectie_met_filters_gebruikt_for_filters(
    monkeypatch,
):
    recorder: list = []
    _patch_report_dialog_in_history(monkeypatch, recorder)

    screen = _maak_history_screen(filters_actief=True)
    screen._show_report_for_selected()

    assert len(recorder) == 1
    soort, filters, kwargs = recorder[0]
    assert soort == "for_filters"
    assert filters["manufacturer"] == "TEST"
    assert filters["tool_key"] == "ESR_CAPACITOR"
    assert kwargs["scope"] == "Huidige filters"


def test_history_report_met_checkbox_selectie_blijft_for_measurements(
    monkeypatch,
):
    recorder: list = []
    _patch_report_dialog_in_history(monkeypatch, recorder)

    screen = _maak_history_screen(filters_actief=True)
    from PySide6.QtWidgets import QTableWidgetItem
    from PySide6.QtCore import Qt

    screen.table.setRowCount(1)
    item = QTableWidgetItem("")
    item.setFlags(
        Qt.ItemFlag.ItemIsEnabled
        | Qt.ItemFlag.ItemIsSelectable
        | Qt.ItemFlag.ItemIsUserCheckable
    )
    item.setCheckState(Qt.CheckState.Checked)
    item.setData(Qt.ItemDataRole.UserRole, 99)
    screen.table.setItem(0, 0, item)

    screen._show_report_for_selected()

    assert len(recorder) == 1
    soort, ids, kwargs = recorder[0]
    assert soort == "for_measurements"
    assert ids == [99]
    assert kwargs["scope"] == "Selectie"


def test_history_report_zonder_filters_en_zonder_selectie_doet_niets(
    monkeypatch,
):
    recorder: list = []
    _patch_report_dialog_in_history(monkeypatch, recorder)

    screen = _maak_history_screen(filters_actief=False)
    screen._show_report_for_selected()

    assert recorder == []


# ------------------------------------------------------------------ AnalysisScreen

def _maak_analysis_screen(
    *,
    filters_actief: bool = False,
    analysis_service=None,
):
    from app.gui.analysis_screen import AnalysisScreen

    screen = AnalysisScreen(
        taal="nl_NL", analysis_service=analysis_service
    )
    if filters_actief:
        screen.filter_group.setChecked(True)
        screen.filter_manufacturer.setText("TEST")
    return screen


def test_analysis_report_zonder_selectie_met_filters_gebruikt_for_filters(
    monkeypatch,
):
    recorder: list = []
    monkeypatch.setattr(
        "app.gui.dialogs.report_dialog.ReportDialog",
        _fake_dialog_klasse(recorder),
    )

    screen = _maak_analysis_screen(filters_actief=True)
    screen._open_report_for_selection()

    assert len(recorder) == 1
    soort, filters, kwargs = recorder[0]
    assert soort == "for_filters"
    assert filters["manufacturer"] == "TEST"
    assert filters["tool_key"] == "ESR_CAPACITOR"
    assert kwargs["scope"] == "Huidige filters"


def test_analysis_report_met_selectie_blijft_for_measurements(monkeypatch):
    """Volgt de echte GUI-flow: refresh() vult de tabel, dan vinkt de
    test een bestaande rij aan, dan opent de rapportdialoog.

    Sinds AnalysisScreen v1.9.1 triggert het aanvinken een refresh
    (preserve_selection=True). Een handmatig gezette rij die niet uit
    de service komt, zou daardoor weer verdwijnen; daarom gebruikt
    deze test een stub-service met een echte rij id=77.
    """
    recorder: list = []
    monkeypatch.setattr(
        "app.gui.dialogs.report_dialog.ReportDialog",
        _fake_dialog_klasse(recorder),
    )

    stub = _StubAnalysisServiceMetRij(measurement_id=77)
    screen = _maak_analysis_screen(
        filters_actief=True, analysis_service=stub
    )
    screen.refresh()
    assert screen.selection_table.rowCount() == 1

    from PySide6.QtCore import Qt

    item = screen.selection_table.item(0, 0)
    assert int(item.data(Qt.ItemDataRole.UserRole)) == 77
    item.setCheckState(Qt.CheckState.Checked)

    # De 5C-refresh heeft de rij hersteld; de selectie is nog steeds [77].
    assert screen._selected_measurement_ids() == [77]

    screen._open_report_for_selection()

    assert len(recorder) == 1
    soort, ids, kwargs = recorder[0]
    assert soort == "for_measurements"
    assert ids == [77]
    assert kwargs["scope"] == "Selectie"


def test_analysis_handmatige_rij_zonder_service_gebruikt_for_filters(
    monkeypatch,
):
    """Legt het bewuste gedrag van 5C vast: een rij die niet uit de
    service komt, verdwijnt na de automatische refresh.

    Deze test documenteert waarom de oude variant van
    test_analysis_report_met_selectie_blijft_for_measurements niet
    meer werkt: de 5C-refresh gooit een handmatig gezette rij weg
    (want die zit niet in de service-resultaten), waarna de
    rapportdialoog op de filters-tak terugvalt.
    """
    recorder: list = []
    monkeypatch.setattr(
        "app.gui.dialogs.report_dialog.ReportDialog",
        _fake_dialog_klasse(recorder),
    )

    # Lege service: geen rijen om te herstellen.
    screen = _maak_analysis_screen(
        filters_actief=True, analysis_service=_StubAnalysisService()
    )

    from PySide6.QtWidgets import QTableWidgetItem
    from PySide6.QtCore import Qt

    screen.selection_table.setRowCount(1)
    item = QTableWidgetItem("")
    item.setFlags(
        Qt.ItemFlag.ItemIsEnabled
        | Qt.ItemFlag.ItemIsSelectable
        | Qt.ItemFlag.ItemIsUserCheckable
    )
    item.setCheckState(Qt.CheckState.Checked)
    item.setData(Qt.ItemDataRole.UserRole, 77)
    screen.selection_table.setItem(0, 0, item)

    # De automatische refresh heeft de handmatige rij weggegooid.
    assert screen._selected_measurement_ids() == []

    screen._open_report_for_selection()

    assert len(recorder) == 1
    soort, _payload, kwargs = recorder[0]
    assert soort == "for_filters"
    assert kwargs["scope"] == "Huidige filters"


def test_analysis_report_zonder_selectie_en_zonder_filters_meldt_geen_selectie(
    monkeypatch,
):
    recorder: list = []
    monkeypatch.setattr(
        "app.gui.dialogs.report_dialog.ReportDialog",
        _fake_dialog_klasse(recorder),
    )

    screen = _maak_analysis_screen(filters_actief=False)
    screen._open_report_for_selection()

    assert recorder == []
    assert screen.state_label.text() != ""