"""
================================================================================
Module:     tests/test_history_export_settings.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.1
Datum:      2026-10-02
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de koppeling tussen algemene bestandsvoorkeuren
            en de Historiek-export.

Wijzigingen:
  v1.0.1 (2026-10-02)  Windows-padvergelijking platformonafhankelijk gemaakt;
                        QUrl gebruikt forward slashes bij toLocalFile().
================================================================================
"""

from dataclasses import replace
from pathlib import Path

from PySide6.QtWidgets import QApplication

import app.gui.history_screen as history_module
from app.config.settings import AppInstellingen
from app.gui.history_screen import HistoryScreen


def _app():
    return QApplication.instance() or QApplication([])


class _Service:
    def list_measurements(self, filters=None, *, limit=100, offset=0):
        return []

    def get_measurement_detail(self, measurement_id):
        return None


def test_export_start_path_gebruikt_bestaande_ingestelde_map(tmp_path, monkeypatch):
    _app()
    basis = AppInstellingen()
    instellingen = replace(
        basis,
        algemeen=replace(
            basis.algemeen,
            standaard_exportmap=str(tmp_path),
        ),
    )
    monkeypatch.setattr(history_module, "laad_instellingen", lambda: instellingen)

    screen = HistoryScreen(taal="nl_NL", history_service=_Service())

    assert screen._export_start_path("historiek.csv") == str(tmp_path / "historiek.csv")


def test_export_start_path_valt_veilig_terug_bij_ongeldige_map(monkeypatch):
    _app()
    basis = AppInstellingen()
    instellingen = replace(
        basis,
        algemeen=replace(
            basis.algemeen,
            standaard_exportmap=r"Z:\bestaat-niet\exports",
        ),
    )
    monkeypatch.setattr(history_module, "laad_instellingen", lambda: instellingen)

    screen = HistoryScreen(taal="nl_NL", history_service=_Service())

    assert screen._export_start_path("historiek.csv") == "historiek.csv"


def test_exportmap_wordt_alleen_geopend_wanneer_ingeschakeld(tmp_path, monkeypatch):
    _app()
    basis = AppInstellingen()
    opened = []
    monkeypatch.setattr(
        history_module.QDesktopServices,
        "openUrl",
        lambda url: opened.append(url.toLocalFile()) or True,
    )

    uit = replace(
        basis,
        algemeen=replace(
            basis.algemeen,
            exportmap_openen_na_export=False,
        ),
    )
    monkeypatch.setattr(history_module, "laad_instellingen", lambda: uit)

    screen = HistoryScreen(taal="nl_NL", history_service=_Service())
    target = tmp_path / "historiek.csv"
    screen._open_export_directory_if_enabled(str(target))
    assert opened == []

    aan = replace(
        basis,
        algemeen=replace(
            basis.algemeen,
            exportmap_openen_na_export=True,
        ),
    )
    monkeypatch.setattr(history_module, "laad_instellingen", lambda: aan)
    screen._open_export_directory_if_enabled(str(target))

    assert len(opened) == 1
    assert Path(opened[0]).resolve() == tmp_path.resolve()
