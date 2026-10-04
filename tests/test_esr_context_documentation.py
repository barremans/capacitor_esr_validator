"""
================================================================================
Module:     tests/test_esr_context_documentation.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-03
Auteur:     Bart Bossuyt

Doel:       Regressietests voor contextuele ESR-documentatie.

Wijzigingen:
  v1.0.0 (2026-10-03)  Basiscontextdocumentatie.
  v1.1.0 (2026-10-03)  Contextuele aanbeveling op meetmethode/instrument getest.
================================================================================
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.gui.esr_test_screen import EsrTestScreen
from app.services.assessment_service import Meetmethode


def _app():
    return QApplication.instance() or QApplication([])


class _PersistenceStub:
    pass


def _screen() -> EsrTestScreen:
    return EsrTestScreen(
        taal="nl_NL",
        persistence_service=_PersistenceStub(),
    )


def test_safety_button_requests_safe_discharge_document():
    _app()
    screen = _screen()
    requested = []
    screen.documentation_requested.connect(requested.append)

    screen.safety_help_btn.click()

    assert requested == ["esr-safe-discharge"]


def test_measurement_instruction_menu_contains_recommendation_plus_expected_documents():
    _app()
    screen = _screen()

    actions = screen.measurement_help_menu.actions()
    # 1 aanbevolen actie + separator + 7 vaste documenten
    assert len(actions) == 9
    assert actions[1].isSeparator() is True


def test_in_circuit_recommends_in_circuit_limitations():
    _app()
    screen = _screen()

    idx = screen.method_combo.findData(Meetmethode.IN_CIRCUIT.value)
    screen.method_combo.setCurrentIndex(idx)

    doc_id, _title_key = screen._recommended_documentation()
    assert doc_id == "esr-in-circuit-limitations"

    requested = []
    screen.documentation_requested.connect(requested.append)
    screen.measurement_help_menu.actions()[0].trigger()
    assert requested == ["esr-in-circuit-limitations"]


def test_lcr_instrument_recommends_lcr_document_when_not_in_circuit():
    _app()
    screen = _screen()

    method_idx = screen.method_combo.findData(Meetmethode.EX_SITU.value)
    screen.method_combo.setCurrentIndex(method_idx)

    # Zoek een bestaand profiel waarvan code of zichtbare naam LCR bevat.
    lcr_index = -1
    for index in range(screen.instrument_combo.count()):
        code = str(screen.instrument_combo.itemData(index) or "")
        name = screen.instrument_combo.itemText(index)
        if "LCR" in f"{code} {name}".upper():
            lcr_index = index
            break

    if lcr_index < 0:
        # Projectconfiguratie zonder LCR-profiel: test alleen de pure resolver
        # door de combo tijdelijk een contextitem te geven.
        screen.instrument_combo.addItem("LCR test instrument", "LCR_TEST")
        lcr_index = screen.instrument_combo.count() - 1

    screen.instrument_combo.setCurrentIndex(lcr_index)

    doc_id, _title_key = screen._recommended_documentation()
    assert doc_id == "esr-lcr-meter"


def test_esr_instrument_recommends_esr_meter_document_when_not_in_circuit():
    _app()
    screen = _screen()

    method_idx = screen.method_combo.findData(Meetmethode.ONE_LEG.value)
    screen.method_combo.setCurrentIndex(method_idx)

    esr_index = -1
    for index in range(screen.instrument_combo.count()):
        code = str(screen.instrument_combo.itemData(index) or "")
        name = screen.instrument_combo.itemText(index)
        hint = f"{code} {name}".upper()
        if "ESR" in hint and "LCR" not in hint:
            esr_index = index
            break

    if esr_index < 0:
        screen.instrument_combo.addItem("ESR test meter", "ESR_TEST")
        esr_index = screen.instrument_combo.count() - 1

    screen.instrument_combo.setCurrentIndex(esr_index)

    doc_id, _title_key = screen._recommended_documentation()
    assert doc_id == "esr-esr-meter"


def test_measurement_instruction_button_translates_live():
    _app()
    screen = _screen()

    assert screen.measurement_help_btn.text() == "Meetinstructies"

    screen.apply_language("en_US")

    assert screen.measurement_help_btn.text() == "Measurement instructions"
    first_action = screen.measurement_help_menu.actions()[0]
    assert first_action.text().startswith("Recommended:")
