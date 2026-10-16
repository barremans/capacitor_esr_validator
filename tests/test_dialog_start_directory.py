"""
================================================================================
Module:     tests/test_dialog_start_directory.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-16
Auteur:     Bart Bossuyt

Doel:       Regressietests voor app/helpers/dialog_start_directory.

            Bewijst dat beste_startmap de juiste voorkeur heeft, dat
            onthoud_startmap per categorie naar het juiste settings-veld
            schrijft, en dat beide functies stil falen bij lees- of
            schrijffouten.

Wijzigingen:
  v1.0.0 (2026-10-16)  Fase 11A.3: eerste tests.
================================================================================
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

import app.helpers.dialog_start_directory as helper_module
from app.config.settings import AppInstellingen
from app.helpers.dialog_start_directory import (
    beste_startmap,
    onthoud_startmap,
    startpad_voor_bestand,
)


def _met_mappen(
    *,
    laatste_export: str = "",
    standaard_export: str = "",
    laatste_import: str = "",
    standaard_import: str = "",
    laatste_rapport: str = "",
) -> AppInstellingen:
    basis = AppInstellingen()
    algemeen = replace(
        basis.algemeen,
        laatste_exportmap=laatste_export,
        standaard_exportmap=standaard_export,
        laatste_importmap=laatste_import,
        standaard_importmap=standaard_import,
        laatste_rapportmap=laatste_rapport,
    )
    return replace(basis, algemeen=algemeen)


# ============================================================================
# beste_startmap
# ============================================================================

def test_beste_startmap_export_kiest_laatste(tmp_path, monkeypatch):
    laatste = tmp_path / "laatste"
    laatste.mkdir()
    standaard = tmp_path / "standaard"
    standaard.mkdir()

    instellingen = _met_mappen(
        laatste_export=str(laatste), standaard_export=str(standaard)
    )
    monkeypatch.setattr(helper_module, "laad_instellingen", lambda: instellingen)

    assert beste_startmap("export") == laatste


def test_beste_startmap_export_valt_terug_op_standaard(tmp_path, monkeypatch):
    standaard = tmp_path / "standaard"
    standaard.mkdir()

    instellingen = _met_mappen(
        laatste_export=str(tmp_path / "bestaat-niet"),
        standaard_export=str(standaard),
    )
    monkeypatch.setattr(helper_module, "laad_instellingen", lambda: instellingen)

    assert beste_startmap("export") == standaard


def test_beste_startmap_export_geeft_none_zonder_geldige_map(
    tmp_path, monkeypatch
):
    instellingen = _met_mappen(
        laatste_export=str(tmp_path / "bestaat-niet-1"),
        standaard_export=str(tmp_path / "bestaat-niet-2"),
    )
    monkeypatch.setattr(helper_module, "laad_instellingen", lambda: instellingen)

    assert beste_startmap("export") is None


def test_beste_startmap_import_valt_terug_op_standaard_import(
    tmp_path, monkeypatch
):
    standaard = tmp_path / "import-standaard"
    standaard.mkdir()

    instellingen = _met_mappen(
        laatste_import=str(tmp_path / "bestaat-niet"),
        standaard_import=str(standaard),
    )
    monkeypatch.setattr(helper_module, "laad_instellingen", lambda: instellingen)

    assert beste_startmap("import") == standaard


def test_beste_startmap_rapport_valt_terug_op_standaard_export(
    tmp_path, monkeypatch
):
    """Voor 'rapport' is er geen standaard_rapportmap; de standaard komt
    uit standaard_exportmap, consistent met ReportDialog."""
    standaard = tmp_path / "export-standaard"
    standaard.mkdir()

    instellingen = _met_mappen(
        laatste_rapport=str(tmp_path / "bestaat-niet"),
        standaard_export=str(standaard),
    )
    monkeypatch.setattr(helper_module, "laad_instellingen", lambda: instellingen)

    assert beste_startmap("rapport") == standaard


def test_beste_startmap_onbekende_categorie_faalt():
    with pytest.raises(ValueError):
        beste_startmap("onbekend")  # type: ignore[arg-type]


def test_beste_startmap_faalt_stil_bij_laad_fout(monkeypatch):
    def _faal():
        raise OSError("kapot")

    monkeypatch.setattr(helper_module, "laad_instellingen", _faal)
    assert beste_startmap("export") is None


# ============================================================================
# startpad_voor_bestand
# ============================================================================

def test_startpad_voor_bestand_met_geldige_map(tmp_path, monkeypatch):
    map_ = tmp_path / "map"
    map_.mkdir()
    monkeypatch.setattr(
        helper_module,
        "laad_instellingen",
        lambda: _met_mappen(laatste_export=str(map_)),
    )

    assert startpad_voor_bestand("export", "historiek.csv") == str(
        map_ / "historiek.csv"
    )


def test_startpad_voor_bestand_zonder_map(tmp_path, monkeypatch):
    monkeypatch.setattr(
        helper_module,
        "laad_instellingen",
        lambda: _met_mappen(
            laatste_export=str(tmp_path / "x"),
            standaard_export=str(tmp_path / "y"),
        ),
    )

    assert startpad_voor_bestand("export", "historiek.csv") == "historiek.csv"


# ============================================================================
# onthoud_startmap
# ============================================================================

def test_onthoud_startmap_export_schrijft_laatste_exportmap(
    tmp_path, monkeypatch
):
    basis = _met_mappen()
    monkeypatch.setattr(helper_module, "laad_instellingen", lambda: basis)

    opgeslagen: dict = {}

    def _fake_opslaan(inst):
        opgeslagen["inst"] = inst

    monkeypatch.setattr(helper_module, "sla_instellingen_op", _fake_opslaan)

    doel = tmp_path / "exports" / "historiek.csv"
    doel.parent.mkdir()
    onthoud_startmap("export", doel)

    assert opgeslagen["inst"].algemeen.laatste_exportmap == str(doel.parent)
    # Andere velden blijven leeg.
    assert opgeslagen["inst"].algemeen.laatste_importmap == ""
    assert opgeslagen["inst"].algemeen.laatste_rapportmap == ""


def test_onthoud_startmap_import_schrijft_laatste_importmap(
    tmp_path, monkeypatch
):
    basis = _met_mappen()
    monkeypatch.setattr(helper_module, "laad_instellingen", lambda: basis)

    opgeslagen: dict = {}
    monkeypatch.setattr(
        helper_module,
        "sla_instellingen_op",
        lambda inst: opgeslagen.__setitem__("inst", inst),
    )

    doel = tmp_path / "imports" / "doc.pdf"
    doel.parent.mkdir()
    onthoud_startmap("import", doel)

    assert opgeslagen["inst"].algemeen.laatste_importmap == str(doel.parent)
    assert opgeslagen["inst"].algemeen.laatste_exportmap == ""
    assert opgeslagen["inst"].algemeen.laatste_rapportmap == ""


def test_onthoud_startmap_rapport_schrijft_laatste_rapportmap(
    tmp_path, monkeypatch
):
    basis = _met_mappen()
    monkeypatch.setattr(helper_module, "laad_instellingen", lambda: basis)

    opgeslagen: dict = {}
    monkeypatch.setattr(
        helper_module,
        "sla_instellingen_op",
        lambda inst: opgeslagen.__setitem__("inst", inst),
    )

    doel = tmp_path / "rapporten"
    doel.mkdir()
    onthoud_startmap("rapport", doel)

    assert opgeslagen["inst"].algemeen.laatste_rapportmap == str(doel)
    assert opgeslagen["inst"].algemeen.laatste_exportmap == ""


def test_onthoud_startmap_met_map_schrijft_map_zelf(tmp_path, monkeypatch):
    monkeypatch.setattr(
        helper_module, "laad_instellingen", lambda: _met_mappen()
    )
    opgeslagen: dict = {}
    monkeypatch.setattr(
        helper_module,
        "sla_instellingen_op",
        lambda inst: opgeslagen.__setitem__("inst", inst),
    )

    doel = tmp_path / "exports"
    doel.mkdir()
    onthoud_startmap("export", doel)

    assert opgeslagen["inst"].algemeen.laatste_exportmap == str(doel)


def test_onthoud_startmap_slaat_niet_opnieuw_op_bij_zelfde_map(
    tmp_path, monkeypatch
):
    instellingen = _met_mappen(laatste_export=str(tmp_path))
    monkeypatch.setattr(
        helper_module, "laad_instellingen", lambda: instellingen
    )

    aantal = {"count": 0}
    monkeypatch.setattr(
        helper_module,
        "sla_instellingen_op",
        lambda inst: aantal.__setitem__("count", aantal["count"] + 1),
    )

    onthoud_startmap("export", tmp_path / "historiek.csv")

    assert aantal["count"] == 0


def test_onthoud_startmap_faalt_stil_bij_opslaan_fout(tmp_path, monkeypatch):
    monkeypatch.setattr(
        helper_module, "laad_instellingen", lambda: _met_mappen()
    )

    def _faal(inst):
        raise OSError("schijf vol")

    monkeypatch.setattr(helper_module, "sla_instellingen_op", _faal)

    # Mag geen exception opgooien.
    onthoud_startmap("export", tmp_path / "historiek.csv")


def test_onthoud_startmap_faalt_stil_bij_laad_fout(tmp_path, monkeypatch):
    def _faal():
        raise OSError("kapot")

    monkeypatch.setattr(helper_module, "laad_instellingen", _faal)

    # Mag geen exception opgooien.
    onthoud_startmap("export", tmp_path / "historiek.csv")


def test_onthoud_startmap_onbekende_categorie_faalt(tmp_path):
    with pytest.raises(ValueError):
        onthoud_startmap("onbekend", tmp_path)  # type: ignore[arg-type]