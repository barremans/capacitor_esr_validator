"""
================================================================================
Module:     tests/test_icon_paths.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.2.0
Datum:      2026-10-22
Auteur:     Bart Bossuyt

Doel:       Regressietests voor app/helpers/icon_paths.py (fase 11C).
            Test de pure padresolutie zonder Qt, en de dunne Qt-wrappers
            met een offscreen QApplication. Geen pytest-qt, geen qtbot.

Wijzigingen:
  v1.0.0 (2026-10-16)  Eerste versie. Dekt: icoon_pad, applicatie_icoon_pad,
                        laad_icoon, applicatie_icoon, zet_venster_icoon,
                        en de fallback-keten.
  v1.1.0 (2026-10-20)  Fase 11F.4 (§4.21): de lokale _app-fixture
                        (scope=module) is vervangen door de
                        projectafspraak _app()-helper. De Qt-tests
                        roepen _app() nu zelf aan; de testinhoud is
                        ongewijzigd.
  v1.2.0 (2026-10-22)  Fase 11I.2: twee nieuwe tests voor de
                        sys._MEIPASS-branch in _projectroot_default():
                        test_projectroot_gebruikt_meipass_als_aanwezig
                        en test_icoon_pad_met_meipass. Bestaande tests
                        ongewijzigd (17 -> 19 tests).
================================================================================
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from app.helpers import icon_paths


def _app():
    """Lokale QApplication-helper, conform projectafspraak (geen qtbot)."""
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


# ---------------------------------------------------------------------------
# Pure padresolutie — geen Qt
# ---------------------------------------------------------------------------

def test_iconenmap_bestaat():
    """De iconenmap moet bestaan in de projectroot."""
    pad = icon_paths.iconenmap()
    assert pad.is_dir(), f"Verwachtte bestaande map: {pad}"
    assert pad.name == "icons"
    assert pad.parent.name == "assets"


def test_icoon_pad_bestaand_icoon():
    """Een bestaand icoon geeft een bestaand pad terug."""
    pad = icon_paths.icoon_pad("app")
    assert pad is not None
    assert pad.is_file()
    assert pad.name == "app.png"


def test_icoon_pad_onbekend_icoon():
    """Een onbekend icoon geeft None terug."""
    pad = icon_paths.icoon_pad("bestaat_niet_zzz")
    assert pad is None


def test_icoon_pad_lege_naam():
    """Een lege naam geeft None terug."""
    assert icon_paths.icoon_pad("") is None
    assert icon_paths.icoon_pad(None) is None  # type: ignore[arg-type]


def test_icoon_pad_andere_extensie():
    """De extensie-parameter werkt."""
    pad = icon_paths.icoon_pad("logo", extensie="ico")
    assert pad is not None
    assert pad.is_file()
    assert pad.suffix == ".ico"


def test_icoon_pad_met_expliciete_projectroot(tmp_path):
    """Met een expliciete projectroot wordt die gebruikt."""
    nep = tmp_path / "assets" / "icons"
    nep.mkdir(parents=True)
    (nep / "test.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    pad = icon_paths.icoon_pad(
        "test", projectroot=tmp_path, extensie="png"
    )
    assert pad is not None
    assert pad == nep / "test.png"


def test_applicatie_icoon_pad_volgt_fallback():
    """Applicatie-icoon: app.png heeft voorrang op logo.ico."""
    pad = icon_paths.applicatie_icoon_pad()
    assert pad is not None
    assert pad.name == "app.png"


def test_applicatie_icoon_pad_fallback_op_logo(tmp_path):
    """Zonder app.png valt het applicatie-icoon terug op logo.ico."""
    nep = tmp_path / "assets" / "icons"
    nep.mkdir(parents=True)
    (nep / "logo.ico").write_bytes(b"\x00\x00\x01\x00")

    pad = icon_paths.applicatie_icoon_pad(projectroot=tmp_path)
    assert pad is not None
    assert pad.name == "logo.ico"


def test_applicatie_icoon_pad_geen_enkel_icoon(tmp_path):
    """Zonder enig icoon geeft de fallback None terug."""
    nep = tmp_path / "assets" / "icons"
    nep.mkdir(parents=True)
    pad = icon_paths.applicatie_icoon_pad(projectroot=tmp_path)
    assert pad is None


# ---------------------------------------------------------------------------
# PyInstaller-bundel: sys._MEIPASS (fase 11I.2)
# ---------------------------------------------------------------------------

def test_projectroot_gebruikt_meipass_als_aanwezig(tmp_path, monkeypatch):
    """Met sys._MEIPASS geeft _projectroot_default die map terug.

    In een PyInstaller-bundel staat assets/ in _MEIPASS/assets/. De
    expliciete _MEIPASS-branch moet vóór de omhoog-zoeklus winnen,
    anders zou de lus in de bundel ook kunnen slagen -- maar pas ná
    een aantal iteraties, en niet deterministisch.
    """
    nep = tmp_path / "bundle"
    (nep / "assets" / "icons").mkdir(parents=True)
    (nep / "assets" / "icons" / "app.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    monkeypatch.setattr(sys, "_MEIPASS", str(nep), raising=False)

    root = icon_paths._projectroot_default()
    assert root == nep
    assert icon_paths.iconenmap() == nep / "assets" / "icons"


def test_icoon_pad_met_meipass(tmp_path, monkeypatch):
    """icoon_pad() gebruikt _MEIPASS als dat bestaat en assets/icons bevat."""
    nep = tmp_path / "bundle"
    (nep / "assets" / "icons").mkdir(parents=True)
    (nep / "assets" / "icons" / "app.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    monkeypatch.setattr(sys, "_MEIPASS", str(nep), raising=False)

    pad = icon_paths.icoon_pad("app")
    assert pad is not None
    assert pad == nep / "assets" / "icons" / "app.png"
    assert pad.is_file()


# ---------------------------------------------------------------------------
# Qt-wrappers — offscreen QApplication via _app()-helper
# ---------------------------------------------------------------------------

def test_laad_icoon_bestaand():
    """Een bestaand icoon levert een niet-lege QIcon."""
    _app()
    icoon = icon_paths.laad_icoon("app")
    assert icoon is not None
    assert not icoon.isNull()


def test_laad_icoon_onbekend():
    """Een onbekend icoon levert None."""
    _app()
    assert icon_paths.laad_icoon("bestaat_niet_zzz") is None


def test_applicatie_icoon_laadt():
    """Het applicatie-icoon laadt correct."""
    _app()
    icoon = icon_paths.applicatie_icoon()
    assert icoon is not None
    assert not icoon.isNull()


def test_zet_venster_icoon_op_qdialog():
    """zet_venster_icoon werkt op een QDialog."""
    _app()
    from PySide6.QtWidgets import QDialog

    dialoog = QDialog()
    resultaat = icon_paths.zet_venster_icoon(dialoog)
    assert resultaat is True
    assert not dialoog.windowIcon().isNull()


def test_zet_venster_icoon_none():
    """zet_venster_icoon met None faalt niet, geeft False."""
    _app()
    assert icon_paths.zet_venster_icoon(None) is False


def test_alle_thematische_iconen_bestaan():
    """Alle iconen uit de README moeten bestaan."""
    namen = [
        "diagnose",
        "esr",
        "history",
        "documentation",
        "analysis",
        "report",
        "settings",
        "help",
        "bug",
        "update",
        "exit",
    ]
    ontbrekend = [
        naam for naam in namen if icon_paths.icoon_pad(naam) is None
    ]
    assert not ontbrekend, f"Ontbrekende iconen: {ontbrekend}"


def test_bestanden_zijn_kleine_letters():
    """Alle icoonbestanden gebruiken kleine letters (case-sensitive FS)."""
    map_ = icon_paths.iconenmap()
    for bestand in map_.iterdir():
        if bestand.is_file() and bestand.suffix in (".png", ".ico"):
            assert bestand.name == bestand.name.lower(), (
                f"Bestandsnaam moet kleine letters zijn: {bestand.name}"
            )