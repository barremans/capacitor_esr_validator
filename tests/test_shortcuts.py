"""
================================================================================
Module:     tests/test_shortcuts.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.2
Datum:      2026-10-05
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de lokale sneltoetsen van Fase 4F in
            ESR-scherm, Historiek-scherm en Hoofdmenu, plus Fase 4F.1
            (Esc op Diagnose) en Fase 4F.2 (Esc op hub met bevestiging).

Wijzigingen:
  v1.0.2 (2026-10-05)  Fase 4F.2: test dat Esc op hub géén directe close
                       veroorzaakt, maar de bevestigingsdialoog opent.
  v1.0.1 (2026-10-05)  Fase 4F.1: test toegevoegd voor Esc op Diagnose.
  v1.0.0 (2026-10-05)  Eerste versie.
================================================================================
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication

from app.gui import main_window as mw
from app.gui.main_window import ToolHubWindow


def _app():
    return QApplication.instance() or QApplication([])


def _shortcut_keys(widget) -> set[str]:
    """Verzamel alle QShortcut-sleutelsequenties die aan widget hangen."""
    result: set[str] = set()
    for sc in widget.findChildren(QShortcut):
        result.add(sc.key().toString())
    return result


# --- ESR-scherm --------------------------------------------------------------

def test_esr_screen_heeft_verwachte_sneltoetsen():
    _app()
    window = ToolHubWindow()
    keys = _shortcut_keys(window.esr_page)

    for verwacht in ("Esc", "Ctrl+Return", "Ctrl+S", "Ctrl+W", "Ctrl+I"):
        assert verwacht in keys, (
            f"ESR-scherm mist sneltoets {verwacht}. Aanwezig: {sorted(keys)}"
        )


def test_esr_escape_roept_back_requested_op():
    _app()
    window = ToolHubWindow()

    signal_ontvangen = {"aantal": 0}
    window.esr_page.back_requested.connect(
        lambda: signal_ontvangen.__setitem__("aantal", signal_ontvangen["aantal"] + 1)
    )
    window.esr_page.sc_back.activated.emit()
    assert signal_ontvangen["aantal"] == 1


def test_esr_ctrl_s_doet_niets_zonder_payload(monkeypatch):
    _app()
    window = ToolHubWindow()
    window.esr_page.save_btn.setEnabled(False)

    aangeroepen = {"aantal": 0}
    monkeypatch.setattr(
        window.esr_page,
        "_on_save_measurement",
        lambda: aangeroepen.__setitem__("aantal", aangeroepen["aantal"] + 1),
    )
    window.esr_page._on_save_shortcut()
    assert aangeroepen["aantal"] == 0


# --- Historiek ---------------------------------------------------------------

def test_historiek_heeft_verwachte_sneltoetsen():
    _app()
    window = ToolHubWindow()
    keys = _shortcut_keys(window.history_page)

    for verwacht in ("Esc", "Ctrl+R", "Ctrl+F", "Ctrl+D", "Ctrl+H"):
        assert verwacht in keys, (
            f"Historiek mist sneltoets {verwacht}. Aanwezig: {sorted(keys)}"
        )


def test_historiek_ctrl_f_opent_filterpaneel():
    _app()
    window = ToolHubWindow()
    hp = window.history_page

    hp.filter_group.setChecked(False)
    hp.filter_body.setVisible(False)

    hp._focus_filters()

    assert hp.filter_group.isChecked() is True


def test_historiek_ctrl_d_doet_niets_zonder_selectie():
    _app()
    window = ToolHubWindow()
    hp = window.history_page

    hp.detail_btn.setEnabled(False)
    geopend = {"aantal": 0}
    hp._show_selected_detail = lambda: geopend.__setitem__("aantal", geopend["aantal"] + 1)
    hp._on_detail_shortcut()
    assert geopend["aantal"] == 0


# --- Hoofdmenu ---------------------------------------------------------------

def test_hoofdmenu_heeft_verwachte_sneltoetsen():
    _app()
    window = ToolHubWindow()
    keys = _shortcut_keys(window.hub_page)

    for verwacht in ("Ctrl+D", "Ctrl+H", "Ctrl+K", "Esc"):
        assert verwacht in keys, (
            f"Hoofdmenu mist sneltoets {verwacht}. Aanwezig: {sorted(keys)}"
        )


def test_hoofdmenu_ctrl_d_gaat_naar_diagnose():
    _app()
    window = ToolHubWindow()
    window.sc_hub_diagnose.activated.emit()
    assert window.stack.currentWidget() is window.diagnose_page


def test_hoofdmenu_ctrl_h_gaat_naar_historiek():
    _app()
    window = ToolHubWindow()
    window.sc_hub_history.activated.emit()
    assert window.stack.currentWidget() is window.history_page


def test_hoofdmenu_ctrl_k_gaat_naar_documentatie():
    _app()
    window = ToolHubWindow()
    window.sc_hub_documentation.activated.emit()
    assert window.stack.currentWidget() is window.documentation_page


def test_hoofdmenu_escape_vraagt_bevestiging(monkeypatch):
    """Fase 4F.2: Esc op hub sluit niet direct; eerst bevestigingsdialoog."""
    _app()
    window = ToolHubWindow()

    # Blokkeer daadwerkelijke sluiting: als close() wordt aangeroepen, faalt de test.
    close_calls = {"aantal": 0}

    def _fake_close():
        close_calls["aantal"] += 1

    monkeypatch.setattr(window, "close", _fake_close)

    # Simuleer: gebruiker antwoordt "Nee".
    monkeypatch.setattr(
        mw.QMessageBox,
        "question",
        lambda *args, **kwargs: mw.QMessageBox.StandardButton.No,
    )

    window.sc_hub_close.activated.emit()
    assert close_calls["aantal"] == 0, (
        "Esc op hub mocht de applicatie niet direct sluiten."
    )

    # Simuleer: gebruiker antwoordt "Ja".
    monkeypatch.setattr(
        mw.QMessageBox,
        "question",
        lambda *args, **kwargs: mw.QMessageBox.StandardButton.Yes,
    )

    window.sc_hub_close.activated.emit()
    assert close_calls["aantal"] == 1, (
        "Esc op hub moest bij 'Ja' de applicatie sluiten."
    )


# --- Diagnose (Fase 4F.1) ---------------------------------------------------

def test_diagnose_heeft_escape_sneltoets():
    _app()
    window = ToolHubWindow()
    keys = _shortcut_keys(window.diagnose_page)

    assert "Esc" in keys, (
        f"Diagnose mist Esc. Aanwezig: {sorted(keys)}"
    )


def test_diagnose_escape_gaat_naar_hoofdmenu():
    _app()
    window = ToolHubWindow()
    window._show_diagnose()
    assert window.stack.currentWidget() is window.diagnose_page

    window.sc_diagnose_back.activated.emit()

    assert window.stack.currentWidget() is window.hub_page