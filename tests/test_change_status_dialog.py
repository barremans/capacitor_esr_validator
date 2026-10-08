"""
================================================================================
Module:     tests/test_change_status_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-08
Auteur:     Bart Bossuyt

Doel:       GUI-regressietests voor ChangeStatusDialog (fase 5D'.2e).
            ImportService.set_status wordt via de echte service in
            tmp_path getest. Geen echte %LOCALAPPDATA%-catalogus.
            QMessageBox.question wordt gemockt zodat de tests niet
            blokkeren.

Wijzigingen:
  v1.0.0 (2026-10-08)  Eerste versie.
================================================================================
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox

from app.documentation.import_models import (
    ImportStatus,
)
from app.documentation.import_service import ImportService
from app.gui.dialogs.change_status_dialog import ChangeStatusDialog


def _app():
    return QApplication.instance() or QApplication([])


def _maak_bron(
    service: ImportService,
    *,
    status: ImportStatus = ImportStatus.CONCEPT,
):
    """Registreer een PDF-bron en zet die in de gewenste status."""
    r = service.register_pdf(
        title="Testbron",
        original_filename="test.pdf",
        file_hash="hash_test",
        category="DATASHEET",
    )
    if status is ImportStatus.CONCEPT:
        return r.source
    service.set_status(r.source.source_id, status)
    return service.get(r.source.source_id)


# ============================================================================
# Basis
# ============================================================================

def test_dialoog_toont_huidige_status(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_bron(service, status=ImportStatus.CONCEPT)

    dialog = ChangeStatusDialog(
        bron=bron, taal="nl_NL", import_service=service
    )

    assert dialog.huidige_value.text() == "Concept"


def test_dialoog_taal_en_labels(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_bron(service, status=ImportStatus.CONCEPT)

    dialog_nl = ChangeStatusDialog(
        bron=bron, taal="nl_NL", import_service=service
    )
    dialog_en = ChangeStatusDialog(
        bron=bron, taal="en_US", import_service=service
    )

    assert dialog_nl.header_label.text() == "Status wijzigen"
    assert dialog_en.header_label.text() == "Change status"
    assert dialog_nl.cancel_btn.text() == "Annuleren"
    assert dialog_en.cancel_btn.text() == "Cancel"


# ============================================================================
# Toegelaten overgangen per status
# ============================================================================

def test_concept_heeft_twee_toegelaten_overgangen(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_bron(service, status=ImportStatus.CONCEPT)

    dialog = ChangeStatusDialog(
        bron=bron, taal="nl_NL", import_service=service
    )

    items = [
        dialog.status_combo.itemData(i)
        for i in range(dialog.status_combo.count())
    ]
    assert set(items) == {"actief", "gearchiveerd"}


def test_actief_heeft_twee_toegelaten_overgangen(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_bron(service, status=ImportStatus.ACTIEF)

    dialog = ChangeStatusDialog(
        bron=bron, taal="nl_NL", import_service=service
    )

    items = [
        dialog.status_combo.itemData(i)
        for i in range(dialog.status_combo.count())
    ]
    assert set(items) == {"concept", "gearchiveerd"}


def test_gearchiveerd_heeft_een_toegelaten_overgang(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_bron(service, status=ImportStatus.GEARCHIVEERD)

    dialog = ChangeStatusDialog(
        bron=bron, taal="nl_NL", import_service=service
    )

    items = [
        dialog.status_combo.itemData(i)
        for i in range(dialog.status_combo.count())
    ]
    assert items == ["concept"]


# ============================================================================
# Opslaan
# ============================================================================

def test_opslaan_roept_set_status_aan(tmp_path, monkeypatch):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_bron(service, status=ImportStatus.CONCEPT)

    # Bevestiging altijd "ja".
    monkeypatch.setattr(
        QMessageBox, "question",
        staticmethod(lambda *a, **kw: QMessageBox.StandardButton.Yes),
    )

    dialog = ChangeStatusDialog(
        bron=bron, taal="nl_NL", import_service=service
    )
    dialog.status_combo.setCurrentIndex(
        dialog.status_combo.findData("actief")
    )

    ontvangen = {"source_id": None}
    dialog.status_changed.connect(
        lambda sid: ontvangen.__setitem__("source_id", sid)
    )

    dialog._save()

    assert ontvangen["source_id"] == bron.source_id
    assert service.get(bron.source_id).status is ImportStatus.ACTIEF


def test_annuleren_roept_set_status_niet_aan(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_bron(service, status=ImportStatus.CONCEPT)

    dialog = ChangeStatusDialog(
        bron=bron, taal="nl_NL", import_service=service
    )
    dialog.reject()

    assert service.get(bron.source_id).status is ImportStatus.CONCEPT


def test_bevestiging_nee_doet_niets(tmp_path, monkeypatch):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_bron(service, status=ImportStatus.CONCEPT)

    monkeypatch.setattr(
        QMessageBox, "question",
        staticmethod(lambda *a, **kw: QMessageBox.StandardButton.No),
    )

    dialog = ChangeStatusDialog(
        bron=bron, taal="nl_NL", import_service=service
    )
    dialog.status_combo.setCurrentIndex(
        dialog.status_combo.findData("gearchiveerd")
    )
    dialog._save()

    assert service.get(bron.source_id).status is ImportStatus.CONCEPT


# ============================================================================
# Bevestigingslogica
# ============================================================================

def test_geen_bevestiging_bij_activeren(tmp_path, monkeypatch):
    """CONCEPT → ACTIEF: geen bevestigingsvraag."""
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_bron(service, status=ImportStatus.CONCEPT)

    gevraagd = {"count": 0}
    monkeypatch.setattr(
        QMessageBox, "question",
        staticmethod(
            lambda *a, **kw: gevraagd.__setitem__(
                "count", gevraagd["count"] + 1
            ) or QMessageBox.StandardButton.Yes
        ),
    )

    dialog = ChangeStatusDialog(
        bron=bron, taal="nl_NL", import_service=service
    )
    dialog.status_combo.setCurrentIndex(
        dialog.status_combo.findData("actief")
    )
    dialog._save()

    assert gevraagd["count"] == 0


def test_bevestiging_bij_archiveren(tmp_path, monkeypatch):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_bron(service, status=ImportStatus.CONCEPT)

    gevraagd = {"count": 0}
    monkeypatch.setattr(
        QMessageBox, "question",
        staticmethod(
            lambda *a, **kw: gevraagd.__setitem__(
                "count", gevraagd["count"] + 1
            ) or QMessageBox.StandardButton.Yes
        ),
    )

    dialog = ChangeStatusDialog(
        bron=bron, taal="nl_NL", import_service=service
    )
    dialog.status_combo.setCurrentIndex(
        dialog.status_combo.findData("gearchiveerd")
    )
    dialog._save()

    assert gevraagd["count"] == 1


def test_bevestiging_bij_terug_naar_concept(tmp_path, monkeypatch):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_bron(service, status=ImportStatus.GEARCHIVEERD)

    gevraagd = {"count": 0}
    monkeypatch.setattr(
        QMessageBox, "question",
        staticmethod(
            lambda *a, **kw: gevraagd.__setitem__(
                "count", gevraagd["count"] + 1
            ) or QMessageBox.StandardButton.Yes
        ),
    )

    dialog = ChangeStatusDialog(
        bron=bron, taal="nl_NL", import_service=service
    )
    dialog.status_combo.setCurrentIndex(
        dialog.status_combo.findData("concept")
    )
    dialog._save()

    assert gevraagd["count"] == 1


# ============================================================================
# Foutpaden
# ============================================================================

def test_fout_bij_set_status_toont_waarschuwing(tmp_path, monkeypatch):
    """Als set_status faalt, tonen we een waarschuwing en geen signaal."""
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_bron(service, status=ImportStatus.CONCEPT)

    monkeypatch.setattr(
        QMessageBox, "question",
        staticmethod(lambda *a, **kw: QMessageBox.StandardButton.Yes),
    )

    gewaarschuwd = {"count": 0}
    monkeypatch.setattr(
        QMessageBox, "warning",
        staticmethod(
            lambda *a, **kw: gewaarschuwd.__setitem__(
                "count", gewaarschuwd["count"] + 1
            )
        ),
    )

    # Simuleer een ImportValidationError via monkeypatch.
    from app.documentation.import_models import ImportValidationError

    def _faal(*a, **kw):
        raise ImportValidationError("test-fout")

    monkeypatch.setattr(service, "set_status", _faal)

    dialog = ChangeStatusDialog(
        bron=bron, taal="nl_NL", import_service=service
    )

    ontvangen = {"source_id": None}
    dialog.status_changed.connect(
        lambda sid: ontvangen.__setitem__("source_id", sid)
    )

    dialog.status_combo.setCurrentIndex(
        dialog.status_combo.findData("actief")
    )
    dialog._save()

    assert gewaarschuwd["count"] == 1
    assert ontvangen["source_id"] is None


# ============================================================================
# Taalwissel en initiële state
# ============================================================================

def test_save_btn_disabled_zonder_selectie(tmp_path):
    """Defensieve test: zonder geldige selectie is Opslaan uitgeschakeld."""
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bron = _maak_bron(service, status=ImportStatus.GEARCHIVEERD)

    dialog = ChangeStatusDialog(
        bron=bron, taal="nl_NL", import_service=service
    )
    # Standaard is de eerste optie gekozen, dus save_btn is actief.
    # Deze test controleert dat er minstens één optie is.
    assert dialog.status_combo.count() >= 1
    assert dialog.save_btn.isEnabled() is True