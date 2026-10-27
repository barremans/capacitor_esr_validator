"""
================================================================================
Module:     tests/test_history_screen_import.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-27
Auteur:     Bart Bossuyt

Doel:       GUI-regressietests voor de C1-importknop in HistoryScreen.
            Geen qtbot; QT_QPA_PLATFORM=offscreen via conftest.py.
================================================================================
"""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

import app.gui.history_screen as history_module
from app.gui.history_screen import HistoryScreen
from app.helpers.history_import import ImportResultaat


@pytest.fixture(scope="module", autouse=True)
def qapplication():
    app = QApplication.instance() or QApplication([])
    yield app


def _fake_translate(key: str, taal: str = "nl_NL", **kwargs) -> str:
    mapping = {
        "historiek.import.knop": "Importeren",
        "historiek.import.dialoog_titel": "Importeer",
        "historiek.import.bestandsfilter": "CSV (*.csv *.xlsx)",
        "historiek.import.validatiefout": "geweigerd: {bericht}",
        "historiek.import.fout": "fout: {bericht}",
        "historiek.import.geen_ketens": "geen ketens ({totaal}, {fouten})",
        "historiek.import.bevestig_titel": "bevestig",
        "historiek.import.bevestig_tekst": "{geldig}/{fouten}",
        "historiek.import.geslaagd": "{toegevoegd}/{overgeslagen}/{fouten}",
        "historiek.import.details_titel": "details",
        "historiek.import.foutregel": "rij {rij} kolom {kolom}: {bericht}",
        "historiek.import.foutregel_zonder_rij": "{bericht}",
        "historiek.import.meer_fouten": "…",
        "historiek.import.ongeldig_type": "type {extensie}",
        "historiek.aantal": "{aantal}",
        "historiek.leeg": "leeg",
    }
    template = mapping.get(key, key)
    return template.format(**kwargs) if kwargs else template


class _EmptyService:
    def list_measurements(self, filters=None, *, limit=100, offset=0):
        return []

    def get_measurement_detail(self, measurement_id):
        return None


class _FakeImportService:
    def __init__(self, *, uitkomst=None):
        self.calls = []
        self.uitkomst = uitkomst or SimpleNamespace(
            toegevoegd=1, overgeslagen=0, fouten=0, fout_details=()
        )

    def importeer(self, ketens, *, aanvullen=False):
        self.calls.append({"ketens": list(ketens), "aanvullen": aanvullen})
        return self.uitkomst


def test_import_button_exists_and_has_label(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    screen = HistoryScreen(taal="nl_NL", history_service=_EmptyService())

    assert screen.import_btn.text() == "Importeren"


def test_import_from_file_rejects_unknown_extension(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    screen = HistoryScreen(taal="nl_NL", history_service=_EmptyService())

    monkeypatch.setattr(
        screen, "_choose_import_file", lambda: None
    )
    # Als _choose_import_file None teruggeeft (gebruiker annuleert of
    # extensie ongeldig), gebeurt er niets.
    screen._import_from_file()
    assert screen.state_label.text() in ("", "leeg")


def test_import_from_file_validatiefout_toont_melding(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    screen = HistoryScreen(taal="nl_NL", history_service=_EmptyService())

    monkeypatch.setattr(screen, "_choose_import_file", lambda: "x.csv")

    def _raise(_pad):
        raise history_module.ImportValidatieFout("kapot")

    monkeypatch.setattr(history_module, "parse_bestand", _raise)

    screen._import_from_file()

    assert "geweigerd: kapot" in screen.state_label.text()


def test_import_from_file_roept_importservice_aan(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    import_service = _FakeImportService()
    screen = HistoryScreen(
        taal="nl_NL",
        history_service=_EmptyService(),
        import_service=import_service,
    )
    monkeypatch.setattr(screen, "_choose_import_file", lambda: "x.csv")

    keten = SimpleNamespace(natural_key="a" * 64)
    monkeypatch.setattr(
        history_module,
        "parse_bestand",
        lambda _pad: ImportResultaat(
            ketens=(keten,),
            fouten=(),
            totaal_rijen=1,
        ),
    )

    # Bevestigingsdialoog automatisch "Yes".
    monkeypatch.setattr(
        history_module.QMessageBox,
        "question",
        staticmethod(lambda *a, **k: history_module.QMessageBox.StandardButton.Yes),
    )
    monkeypatch.setattr(
        history_module.QMessageBox,
        "information",
        staticmethod(lambda *a, **k: None),
    )

    screen._import_from_file()

    assert import_service.calls == [{"ketens": [keten], "aanvullen": False}]
    assert "1/0/0" in screen.state_label.text()


def test_import_annuleren_doet_niets(monkeypatch):
    monkeypatch.setattr(history_module, "vertaal", _fake_translate)
    import_service = _FakeImportService()
    screen = HistoryScreen(
        taal="nl_NL",
        history_service=_EmptyService(),
        import_service=import_service,
    )
    monkeypatch.setattr(screen, "_choose_import_file", lambda: "x.csv")
    keten = SimpleNamespace(natural_key="a" * 64)
    monkeypatch.setattr(
        history_module,
        "parse_bestand",
        lambda _pad: ImportResultaat(
            ketens=(keten,), fouten=(), totaal_rijen=1
        ),
    )
    monkeypatch.setattr(
        history_module.QMessageBox,
        "question",
        staticmethod(lambda *a, **k: history_module.QMessageBox.StandardButton.No),
    )

    screen._import_from_file()

    assert import_service.calls == []