"""
================================================================================
Module:     tests/test_history_export_settings.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-07
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de koppeling tussen algemene bestandsvoorkeuren
            en de Historiek-export.

Wijzigingen:
  v1.0.1 (2026-10-02)  Windows-padvergelijking platformonafhankelijk gemaakt;
                        QUrl gebruikt forward slashes bij toLocalFile().
  v1.1.0 (2026-10-07)  Fase 5D'.3: tests voor laatste_exportmap en
                        _onthoud_laatste_exportmap. sla_instellingen_op
                        wordt gemockt zodat settings.json niet vervuilt.
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


# ============================================================================
# v1.0.0 — standaard_exportmap
# ============================================================================

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


# ============================================================================
# v1.1.0 — laatste_exportmap (fase 5D'.3)
# ============================================================================

def test_start_path_gebruikt_laatste_exportmap_indien_geldig(
    tmp_path, monkeypatch
):
    """laatste_exportmap wint van standaard_exportmap als die bestaat."""
    _app()
    laatste = tmp_path / "laatste"
    laatste.mkdir()
    standaard = tmp_path / "standaard"
    standaard.mkdir()

    basis = AppInstellingen()
    instellingen = replace(
        basis,
        algemeen=replace(
            basis.algemeen,
            laatste_exportmap=str(laatste),
            standaard_exportmap=str(standaard),
        ),
    )
    monkeypatch.setattr(history_module, "laad_instellingen", lambda: instellingen)

    screen = HistoryScreen(taal="nl_NL", history_service=_Service())

    assert screen._export_start_path("historiek.csv") == str(
        laatste / "historiek.csv"
    )


def test_start_path_valt_terug_op_standaard_bij_ongeldige_laatste(
    tmp_path, monkeypatch
):
    """Ongeldige laatste_exportmap valt terug op standaard_exportmap."""
    _app()
    standaard = tmp_path / "standaard"
    standaard.mkdir()

    basis = AppInstellingen()
    instellingen = replace(
        basis,
        algemeen=replace(
            basis.algemeen,
            laatste_exportmap=str(tmp_path / "bestaat-niet"),
            standaard_exportmap=str(standaard),
        ),
    )
    monkeypatch.setattr(history_module, "laad_instellingen", lambda: instellingen)

    screen = HistoryScreen(taal="nl_NL", history_service=_Service())

    assert screen._export_start_path("historiek.csv") == str(
        standaard / "historiek.csv"
    )


def test_start_path_valt_terug_op_leeg_bij_geen_geldige_mappen(
    tmp_path, monkeypatch
):
    """Beide mappen ongeldig: geen map-prefix in de startpath."""
    _app()
    basis = AppInstellingen()
    instellingen = replace(
        basis,
        algemeen=replace(
            basis.algemeen,
            laatste_exportmap=str(tmp_path / "bestaat-niet-1"),
            standaard_exportmap=str(tmp_path / "bestaat-niet-2"),
        ),
    )
    monkeypatch.setattr(history_module, "laad_instellingen", lambda: instellingen)

    screen = HistoryScreen(taal="nl_NL", history_service=_Service())

    assert screen._export_start_path("historiek.csv") == "historiek.csv"


def test_beste_export_start_directory_kiest_laatste(
    tmp_path, monkeypatch
):
    """_beste_export_start_directory geeft laatste_exportmap terug."""
    _app()
    laatste = tmp_path / "laatste"
    laatste.mkdir()

    basis = AppInstellingen()
    instellingen = replace(
        basis,
        algemeen=replace(
            basis.algemeen,
            laatste_exportmap=str(laatste),
            standaard_exportmap=str(tmp_path / "standaard"),
        ),
    )
    monkeypatch.setattr(history_module, "laad_instellingen", lambda: instellingen)

    screen = HistoryScreen(taal="nl_NL", history_service=_Service())

    assert screen._beste_export_start_directory() == laatste


def test_onthoud_laatste_exportmap_werkt_bij_voor_bestand(
    tmp_path, monkeypatch
):
    """_onthoud_laatste_exportmap schrijft de parent van een bestand."""
    _app()
    basis = AppInstellingen()
    monkeypatch.setattr(history_module, "laad_instellingen", lambda: basis)

    opgeslagen = {"instellingen": None}

    def _fake_opslaan(inst):
        opgeslagen["instellingen"] = inst

    monkeypatch.setattr(history_module, "sla_instellingen_op", _fake_opslaan)

    screen = HistoryScreen(taal="nl_NL", history_service=_Service())
    doel_bestand = tmp_path / "exports" / "historiek.csv"
    doel_bestand.parent.mkdir()
    screen._onthoud_laatste_exportmap(doel_bestand)

    assert opgeslagen["instellingen"] is not None
    assert (
        opgeslagen["instellingen"].algemeen.laatste_exportmap
        == str(doel_bestand.parent)
    )


def test_onthoud_laatste_exportmap_werkt_bij_voor_map(tmp_path, monkeypatch):
    """_onthoud_laatste_exportmap schrijft de map zelf."""
    _app()
    basis = AppInstellingen()
    monkeypatch.setattr(history_module, "laad_instellingen", lambda: basis)

    opgeslagen = {"instellingen": None}

    def _fake_opslaan(inst):
        opgeslagen["instellingen"] = inst

    monkeypatch.setattr(history_module, "sla_instellingen_op", _fake_opslaan)

    screen = HistoryScreen(taal="nl_NL", history_service=_Service())
    doel_map = tmp_path / "exports"
    doel_map.mkdir()
    screen._onthoud_laatste_exportmap(doel_map)

    assert opgeslagen["instellingen"] is not None
    assert (
        opgeslagen["instellingen"].algemeen.laatste_exportmap
        == str(doel_map)
    )


def test_onthoud_laatste_exportmap_slaat_niet_opnieuw_op_bij_zelfde_map(
    tmp_path, monkeypatch
):
    """Als de map al de laatste_exportmap is, niet opnieuw opslaan."""
    _app()
    basis = AppInstellingen()
    instellingen = replace(
        basis,
        algemeen=replace(
            basis.algemeen,
            laatste_exportmap=str(tmp_path),
        ),
    )
    monkeypatch.setattr(history_module, "laad_instellingen", lambda: instellingen)

    opgeslagen = {"count": 0}

    def _fake_opslaan(inst):
        opgeslagen["count"] += 1

    monkeypatch.setattr(history_module, "sla_instellingen_op", _fake_opslaan)

    screen = HistoryScreen(taal="nl_NL", history_service=_Service())
    screen._onthoud_laatste_exportmap(tmp_path / "historiek.csv")

    assert opgeslagen["count"] == 0


def test_onthoud_laatste_exportmap_faalt_stil_bij_opslaan_fout(
    tmp_path, monkeypatch
):
    """Als opslaan faalt, mag de export zelf niet blokkeren."""
    _app()
    basis = AppInstellingen()
    monkeypatch.setattr(history_module, "laad_instellingen", lambda: basis)

    def _fake_opslaan_faalt(inst):
        raise OSError("schijf vol")

    monkeypatch.setattr(
        history_module, "sla_instellingen_op", _fake_opslaan_faalt
    )

    screen = HistoryScreen(taal="nl_NL", history_service=_Service())
    # Mag geen exception opgooien
    screen._onthoud_laatste_exportmap(tmp_path / "historiek.csv")


def test_onthoud_laatste_exportmap_faalt_stil_bij_laad_fout(
    tmp_path, monkeypatch
):
    """Als laden faalt, mag de export zelf niet blokkeren."""
    _app()

    def _fake_laad_faalt():
        raise OSError("settings.json onleesbaar")

    monkeypatch.setattr(
        history_module, "laad_instellingen", _fake_laad_faalt
    )

    screen = HistoryScreen(taal="nl_NL", history_service=_Service())
    # Mag geen exception opgooien
    screen._onthoud_laatste_exportmap(tmp_path / "historiek.csv")