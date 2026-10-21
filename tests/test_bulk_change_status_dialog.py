"""
================================================================================
Module:     tests/test_bulk_change_status_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-20
Auteur:     Bart Bossuyt

Doel:       GUI-regressietests voor BulkChangeStatusDialog (fase 11F.3).
            Geen echte ImportService met %LOCALAPPDATA%; de service
            wordt in tmp_path geïsoleerd. QMessageBox.question wordt
            gemockt zodat de tests niet blokkeren.

Wijzigingen:
  v1.0.0 (2026-10-20)  Eerste versie.
================================================================================
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox

from app.documentation.import_models import (
    ImportSource,
    ImportSourceType,
    ImportStatus,
)
from app.documentation.import_service import ImportService
from app.gui.dialogs.bulk_change_status_dialog import (
    BulkChangeStatusDialog,
)


def _app():
    return QApplication.instance() or QApplication([])


def _maak_bron(*, source_id: str = "abc-1") -> ImportSource:
    return ImportSource(
        source_id=source_id,
        source_type=ImportSourceType.PDF,
        title="Test",
        imported_at=1_700_000_000_000,
        imported_by="tester",
        status=ImportStatus.CONCEPT,
        original_filename="t.pdf",
    )


# ============================================================================
# Basis
# ============================================================================

def test_dialoog_vereist_minstens_een_bron(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    try:
        BulkChangeStatusDialog(
            bronnen=[], taal="nl_NL", import_service=service
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Verwachtte ValueError bij lege bronnen")


def test_dialoog_toont_alle_doelstatussen(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bronnen = [_maak_bron()]
    dialog = BulkChangeStatusDialog(
        bronnen=bronnen, taal="nl_NL", import_service=service
    )

    items = [
        dialog.status_combo.itemData(i)
        for i in range(dialog.status_combo.count())
    ]
    assert set(items) == {"concept", "actief", "gearchiveerd"}


def test_redenveld_verborgen_bij_actief(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bronnen = [_maak_bron()]
    dialog = BulkChangeStatusDialog(
        bronnen=bronnen, taal="nl_NL", import_service=service
    )

    index = dialog.status_combo.findData("actief")
    dialog.status_combo.setCurrentIndex(index)

    assert dialog.reden_edit.isHidden() is True


def test_redenveld_zichtbaar_bij_gearchiveerd(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bronnen = [_maak_bron()]
    dialog = BulkChangeStatusDialog(
        bronnen=bronnen, taal="nl_NL", import_service=service
    )

    index = dialog.status_combo.findData("gearchiveerd")
    dialog.status_combo.setCurrentIndex(index)

    assert dialog.reden_edit.isHidden() is False


# ============================================================================
# Opslaan
# ============================================================================

def test_save_concept_vraagt_bevestiging(tmp_path, monkeypatch):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bronnen = [_maak_bron()]
    dialog = BulkChangeStatusDialog(
        bronnen=bronnen, taal="nl_NL", import_service=service
    )

    gevraagd = {"count": 0}
    monkeypatch.setattr(
        QMessageBox, "question",
        staticmethod(
            lambda *a, **kw: gevraagd.__setitem__(
                "count", gevraagd["count"] + 1
            ) or QMessageBox.StandardButton.Yes
        ),
    )

    index = dialog.status_combo.findData("concept")
    dialog.status_combo.setCurrentIndex(index)
    dialog._save()

    assert gevraagd["count"] == 1
    assert dialog.resultaat is not None
    assert dialog.resultaat["doelstatus"] is ImportStatus.CONCEPT


def test_save_actief_vraagt_geen_bevestiging(tmp_path, monkeypatch):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bronnen = [_maak_bron()]
    dialog = BulkChangeStatusDialog(
        bronnen=bronnen, taal="nl_NL", import_service=service
    )

    gevraagd = {"count": 0}
    monkeypatch.setattr(
        QMessageBox, "question",
        staticmethod(
            lambda *a, **kw: gevraagd.__setitem__(
                "count", gevraagd["count"] + 1
            ) or QMessageBox.StandardButton.Yes
        ),
    )

    index = dialog.status_combo.findData("actief")
    dialog.status_combo.setCurrentIndex(index)
    dialog._save()

    assert gevraagd["count"] == 0
    assert dialog.resultaat is not None
    assert dialog.resultaat["doelstatus"] is ImportStatus.ACTIEF
    assert dialog.resultaat["reason"] is None


def test_save_gearchiveerd_bewaart_reden(tmp_path, monkeypatch):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bronnen = [_maak_bron()]
    dialog = BulkChangeStatusDialog(
        bronnen=bronnen, taal="nl_NL", import_service=service
    )

    monkeypatch.setattr(
        QMessageBox, "question",
        staticmethod(lambda *a, **kw: QMessageBox.StandardButton.Yes),
    )

    index = dialog.status_combo.findData("gearchiveerd")
    dialog.status_combo.setCurrentIndex(index)
    dialog.reden_edit.setText("Achterhaald door v2")
    dialog._save()

    assert dialog.resultaat is not None
    assert dialog.resultaat["doelstatus"] is ImportStatus.GEARCHIVEERD
    assert dialog.resultaat["reason"] == "Achterhaald door v2"


def test_save_bevestiging_nee_doet_niets(tmp_path, monkeypatch):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bronnen = [_maak_bron()]
    dialog = BulkChangeStatusDialog(
        bronnen=bronnen, taal="nl_NL", import_service=service
    )

    monkeypatch.setattr(
        QMessageBox, "question",
        staticmethod(lambda *a, **kw: QMessageBox.StandardButton.No),
    )

    index = dialog.status_combo.findData("gearchiveerd")
    dialog.status_combo.setCurrentIndex(index)
    dialog._save()

    assert dialog.resultaat is None


# ============================================================================
# Taalwissel
# ============================================================================

def test_labels_nl(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bronnen = [_maak_bron()]
    dialog = BulkChangeStatusDialog(
        bronnen=bronnen, taal="nl_NL", import_service=service
    )

    assert dialog.header_label.text() == "Status van meerdere imports wijzigen"
    assert dialog.save_btn.text() == "Toepassen"
    assert dialog.cancel_btn.text() == "Annuleren"


def test_labels_en(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bronnen = [_maak_bron()]
    dialog = BulkChangeStatusDialog(
        bronnen=bronnen, taal="en_US", import_service=service
    )

    assert dialog.header_label.text() == "Change status of multiple imports"
    assert dialog.save_btn.text() == "Apply"
    assert dialog.cancel_btn.text() == "Cancel"