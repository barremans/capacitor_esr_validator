"""
================================================================================
Module:     tests/test_exchange_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.2
Datum:      2026-10-26
Auteur:     Bart Bossuyt

Doel:       GUI-regressietests voor ExchangeDialog (fase 28F).
            Geen qtbot; lokale QApplication via de bestaande pattern.

Wijzigingen:
  v1.0.0 (2026-10-23)  Eerste versie.
  v1.0.1 (2026-10-23)  Fix: de drie import-tests gebruikten
                       _laad_plan(Path("dummy...")) op een niet-
                       bestaand bestand. _laad_plan valideert via
                       read_envelope en stopt met een foutmelding.
                       De tests gebruiken nu _toon_plan(envelope)
                       rechtstreeks, wat de eigenlijke GUI-logica is.
  v1.0.2 (2026-10-26)  Chat 3B (masterplan A4): drie tests voor de
                       standaard-scope. Bewijst dat een selectie
                       voorrang heeft op filters (de oude code koos
                       FILTERED), dat filters de fallback zijn zonder
                       selectie, en dat een altijd-niet-lege filters-
                       dict (zoals AnalysisScreen die geeft) de
                       selectie niet overstemt.
================================================================================
"""

from __future__ import annotations

import os
from enum import Enum
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from app.gui.dialogs.exchange_dialog import ExchangeDialog
from app.services.exchange.models import ImportDecision


@pytest.fixture(scope="module", autouse=True)
def qapplication():
    app = QApplication.instance() or QApplication([])
    yield app


class _StubExportService:
    def __init__(self, envelope=None):
        self.envelope = envelope

    def export_measurements(self, ids):
        return self.envelope

    def export_filters(self, filters):
        return self.envelope

    def write_envelope(self, envelope, path):
        pass


class _StubImportPlanner:
    def __init__(self, plan):
        self._plan = plan

    def plan(self, envelope):
        return self._plan


class _StubImportService:
    def __init__(self, result):
        self._result = result
        self.plans: list = []

    def apply_plan(self, plan, *, on_conflict="conflict_copy"):
        self.plans.append(plan)
        return self._result


def _envelope_met_1_chain():
    from app.services.exchange.models import (
        ExportEnvelope,
        ExportedMeasurementChain,
    )
    from app.services.exchange.export_service import bereken_natural_key

    component_model = {"manufacturer": "Test"}
    component_sample = {"sample_state": "NEW"}
    measurement_session = {"started_at_ms": 1_700_000_000_000}
    measurement = {
        "measured_at_ms": 1_700_000_001_000,
        "measurement_method": "EX_SITU",
        "tool_key": "ESR_CAPACITOR",
        "out_of_range": False,
        "open_suspected": False,
        "short_suspected": False,
        "unstable_reading": False,
    }
    natural_key = bereken_natural_key(
        component_model=component_model,
        component_sample=component_sample,
        measurement_session=measurement_session,
        measurement=measurement,
        assessment_snapshots=(),
        reference_snapshots_by_assessment_index=(),
    )

    chain = ExportedMeasurementChain(
        source_measurement_id=42,
        source_machine_id="3f2504e0-4f89-41d3-9a0c-0305e82c3301",
        natural_key=natural_key,
        component_model=component_model,
        component_sample=component_sample,
        measurement_session=measurement_session,
        measurement=measurement,
        assessment_snapshots=(),
        reference_snapshots_by_assessment_index=(),
    )
    return ExportEnvelope(
        format_version="1.0",
        app_version="1.3.0",
        schema_version=3,
        exported_at_ms=1_792_651_200_000,
        source_machine_id="3f2504e0-4f89-41d3-9a0c-0305e82c3301",
        chains=(chain,),
    )


def _plan_met(decision):
    from app.services.exchange.models import ImportPlan

    return ImportPlan(
        envelope=_envelope_met_1_chain(),
        decisions=(decision,),
    )


# ---------------------------------------------------------------- basis

def test_dialoog_heeft_twee_tabs():
    dialog = ExchangeDialog(taal="nl_NL")
    assert dialog.tabs.count() == 2
    assert dialog.tabs.tabText(0) == "Exporteren"
    assert dialog.tabs.tabText(1) == "Importeren"


def test_dialoog_start_op_export_tab():
    dialog = ExchangeDialog(taal="nl_NL")
    assert dialog.tabs.currentIndex() == 0


def test_dialoog_start_op_import_tab_als_gevraagd():
    dialog = ExchangeDialog(taal="nl_NL", initial_tab="import")
    assert dialog.tabs.currentIndex() == 1


def test_dialoog_taal_en():
    dialog = ExchangeDialog(taal="en_US")
    assert dialog.tabs.tabText(0) == "Export"
    assert dialog.tabs.tabText(1) == "Import"


# ---------------------------------------------------------------- exporteren

def test_export_zonder_selectie_meldt_geen_selectie():
    dialog = ExchangeDialog(
        taal="nl_NL",
        selected_measurement_ids=[],
        active_filters={},
    )
    dialog.export_scope_combo.setCurrentIndex(0)  # SELECTED
    dialog._do_export()
    assert "selecteer" in dialog.state_label.text().lower() or "Selecteer" in dialog.state_label.text()


def test_export_met_selectie_roept_service_aan(monkeypatch, tmp_path):
    envelope = _envelope_met_1_chain()
    service = _StubExportService(envelope=envelope)
    dialog = ExchangeDialog(
        taal="nl_NL",
        export_service=service,
        selected_measurement_ids=[42],
        active_filters={},
    )
    dialog.export_scope_combo.setCurrentIndex(0)  # SELECTED

    target = tmp_path / "export.esrexchange.json"
    monkeypatch.setattr(
        "app.gui.dialogs.exchange_dialog.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(target), ""),
    )
    dialog._do_export()
    assert "geëxporteerd" in dialog.state_label.text()


# ---------------------------------------------------------------- importeren

def test_import_toont_plan_in_tabel():
    plan = _plan_met(ImportDecision.IMPORT_NEW)
    planner = _StubImportPlanner(plan=plan)
    dialog = ExchangeDialog(
        taal="nl_NL",
        import_planner=planner,
        import_service=_StubImportService(result=None),
    )
    dialog._toon_plan(plan.envelope, pad="dummy.esrexchange.json")
    assert dialog.import_table.rowCount() == 1


def test_import_als_kopie_vinkje_wordt_gerespecteerd():
    plan = _plan_met(ImportDecision.SKIP_DUPLICATE)
    planner = _StubImportPlanner(plan=plan)

    from app.services.exchange.models import ImportResult

    import_service = _StubImportService(
        result=ImportResult(
            imported_measurement_ids=(1,),
            skipped_duplicate_count=0,
            conflict_copy_measurement_ids=(1,),
        )
    )

    dialog = ExchangeDialog(
        taal="nl_NL",
        import_planner=planner,
        import_service=import_service,
    )
    dialog._toon_plan(plan.envelope, pad="dummy.esrexchange.json")
    # Vink "als kopie" aan.
    dialog.import_table.item(0, 4).setCheckState(
        __import__("PySide6.QtCore", fromlist=["Qt"]).Qt.CheckState.Checked
    )
    dialog._do_import()

    assert len(import_service.plans) == 1
    plan_uit_service = import_service.plans[0]
    assert plan_uit_service.decisions == (ImportDecision.IMPORT_AS_CONFLICT_COPY,)


def test_import_zonder_vinkje_blijft_skip():
    plan = _plan_met(ImportDecision.SKIP_DUPLICATE)
    planner = _StubImportPlanner(plan=plan)

    from app.services.exchange.models import ImportResult

    import_service = _StubImportService(
        result=ImportResult(skipped_duplicate_count=1)
    )

    dialog = ExchangeDialog(
        taal="nl_NL",
        import_planner=planner,
        import_service=import_service,
    )
    dialog._toon_plan(plan.envelope, pad="dummy.esrexchange.json")
    dialog._do_import()

    assert len(import_service.plans) == 1
    assert import_service.plans[0].decisions == (ImportDecision.SKIP_DUPLICATE,)


# ---------------------------------------------------------------- thema

def test_apply_theme_wijzigt_state_label_kleur():
    dialog = ExchangeDialog(taal="nl_NL", theme="dark")
    donker = dialog.state_label.styleSheet()
    dialog.apply_theme("light")
    licht = dialog.state_label.styleSheet()
    assert donker != licht


def test_apply_theme_idempotent():
    dialog = ExchangeDialog(taal="nl_NL", theme="dark")
    stijl_voor = dialog.state_label.styleSheet()
    dialog.apply_theme("dark")
    assert dialog.state_label.styleSheet() == stijl_voor


# ---------------------------------------------------------------- 3B: standaard-scope (A4)

def test_scope_default_is_selectie_bij_selectie_en_filters():
    """3B (A4): een selectie heeft voorrang op filters.

    Vóór de fix bleef de scope op FILTERED staan wanneer zowel een
    selectie als filters aanwezig waren. De selectie werd daardoor
    genegeerd. Deze test faalt op de oude code en slaagt op v1.0.2.
    """
    dialog = ExchangeDialog(
        taal="nl_NL",
        selected_measurement_ids=[42, 43],
        active_filters={"manufacturer": "Panasonic"},
    )
    assert dialog.export_scope_combo.currentData() == "SELECTED"


def test_scope_default_is_filters_zonder_selectie():
    """3B (A4): zonder selectie is FILTERED de fallback."""
    dialog = ExchangeDialog(
        taal="nl_NL",
        selected_measurement_ids=[],
        active_filters={"manufacturer": "Panasonic"},
    )
    assert dialog.export_scope_combo.currentData() == "FILTERED"


def test_analysis_screen_achtige_filters_overstemmen_selectie_niet():
    """3B (A4): de altijd-niet-lege filters van AnalysisScreen.

    AnalysisScreen._active_filters() bevat altijd minstens
    {"tool_key": "ESR_CAPACITOR"}. Vóór de fix zorgde dat ervoor dat
    de scope ALTIJD op FILTERED stond, ook bij een selectie. Deze
    test bewijst dat de selectie nu voorrang krijgt, ongeacht de
    inhoud van de filters-dict.
    """
    dialog = ExchangeDialog(
        taal="nl_NL",
        selected_measurement_ids=[42],
        active_filters={"tool_key": "ESR_CAPACITOR"},
    )
    assert dialog.export_scope_combo.currentData() == "SELECTED"