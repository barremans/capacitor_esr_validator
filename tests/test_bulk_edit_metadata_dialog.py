"""
================================================================================
Module:     tests/test_bulk_edit_metadata_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-20
Auteur:     Bart Bossuyt

Doel:       GUI-regressietests voor BulkEditMetadataDialog (fase 11F.3).
            Geen echte ImportService met %LOCALAPPDATA%; de service
            wordt in tmp_path geïsoleerd.

Wijzigingen:
  v1.0.0 (2026-10-20)  Eerste versie.
================================================================================
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.documentation.import_models import (
    ImportSource,
    ImportSourceType,
    ImportStatus,
)
from app.documentation.import_service import ImportService
from app.gui.dialogs.bulk_edit_metadata_dialog import (
    BulkEditMetadataDialog,
)


def _app():
    return QApplication.instance() or QApplication([])


def _maak_bron(*, source_id: str = "abc-1", titel: str = "OUD") -> ImportSource:
    return ImportSource(
        source_id=source_id,
        source_type=ImportSourceType.PDF,
        title=titel,
        imported_at=1_700_000_000_000,
        imported_by="tester",
        status=ImportStatus.CONCEPT,
        original_filename="oud.pdf",
        file_hash="hash_abc",
        category="DATASHEET",
        manufacturer="PANASONIC",
    )


def _maak_bronnen(*aantallen: str) -> list[ImportSource]:
    return [
        _maak_bron(source_id=f"abc-{i}", titel=f"OUD-{i}")
        for i in range(1, len(aantallen) + 1)
    ]


# ============================================================================
# Basis
# ============================================================================

def test_dialoog_vereist_minstens_een_bron(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    try:
        BulkEditMetadataDialog(
            bronnen=[], taal="nl_NL", import_service=service
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Verwachtte ValueError bij lege bronnen")


def test_dialoog_opent_met_alle_velden_uitgevinkt(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bronnen = _maak_bronnen("a", "b", "c")
    dialog = BulkEditMetadataDialog(
        bronnen=bronnen, taal="nl_NL", import_service=service
    )

    assert dialog.titel_check.isChecked() is False
    assert dialog.categorie_check.isChecked() is False
    assert dialog.fabrikant_check.isChecked() is False
    assert dialog.serie_check.isChecked() is False
    assert dialog.partnummer_check.isChecked() is False
    assert dialog.documentversie_check.isChecked() is False
    assert dialog.documentdatum_check.isChecked() is False
    assert dialog.notities_check.isChecked() is False
    assert dialog.save_btn.isEnabled() is False


def test_save_btn_activeert_bij_een_veld(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bronnen = _maak_bronnen("a")
    dialog = BulkEditMetadataDialog(
        bronnen=bronnen, taal="nl_NL", import_service=service
    )

    dialog.fabrikant_check.setChecked(True)
    assert dialog.save_btn.isEnabled() is True


def test_veld_is_disabled_tot_checkbox_aan(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bronnen = _maak_bronnen("a")
    dialog = BulkEditMetadataDialog(
        bronnen=bronnen, taal="nl_NL", import_service=service
    )

    assert dialog.fabrikant_edit.isEnabled() is False
    dialog.fabrikant_check.setChecked(True)
    assert dialog.fabrikant_edit.isEnabled() is True


# ============================================================================
# Opslaan
# ============================================================================

def test_save_zonder_velden_doet_niets(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bronnen = _maak_bronnen("a")
    dialog = BulkEditMetadataDialog(
        bronnen=bronnen, taal="nl_NL", import_service=service
    )

    dialog._save()
    assert dialog.resultaat is None


def test_save_met_een_veld_levert_resultaat(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bronnen = _maak_bronnen("a")
    dialog = BulkEditMetadataDialog(
        bronnen=bronnen, taal="nl_NL", import_service=service
    )

    dialog.fabrikant_check.setChecked(True)
    dialog.fabrikant_edit.setText("TDK")
    dialog._save()

    assert dialog.resultaat is not None
    assert dialog.resultaat["source_ids"] == ["abc-1"]
    assert dialog.resultaat["wijzigingen"] == {"manufacturer": "TDK"}


def test_save_met_meerdere_velden(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bronnen = _maak_bronnen("a", "b")
    dialog = BulkEditMetadataDialog(
        bronnen=bronnen, taal="nl_NL", import_service=service
    )

    dialog.fabrikant_check.setChecked(True)
    dialog.fabrikant_edit.setText("TDK")
    dialog.serie_check.setChecked(True)
    dialog.serie_edit.setText("C-SERIES")
    dialog._save()

    assert dialog.resultaat is not None
    assert dialog.resultaat["source_ids"] == ["abc-1", "abc-2"]
    assert dialog.resultaat["wijzigingen"] == {
        "manufacturer": "TDK",
        "series": "C-SERIES",
    }


def test_titel_leeg_geeft_waarschuwing(tmp_path, monkeypatch):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bronnen = _maak_bronnen("a")
    dialog = BulkEditMetadataDialog(
        bronnen=bronnen, taal="nl_NL", import_service=service
    )

    from PySide6.QtWidgets import QMessageBox
    gewaarschuwd = {"count": 0}
    monkeypatch.setattr(
        QMessageBox, "warning",
        staticmethod(
            lambda *a, **kw: gewaarschuwd.__setitem__(
                "count", gewaarschuwd["count"] + 1
            )
        ),
    )

    dialog.titel_check.setChecked(True)
    dialog.title_edit.setText("   ")
    dialog._save()

    assert gewaarschuwd["count"] == 1
    assert dialog.resultaat is None


def test_save_zonder_veld_aangevinkt_doet_niets(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bronnen = _maak_bronnen("a")
    dialog = BulkEditMetadataDialog(
        bronnen=bronnen, taal="nl_NL", import_service=service
    )
    dialog._save()
    assert dialog.resultaat is None


# ============================================================================
# Taalwissel
# ============================================================================

def test_labels_nl(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bronnen = _maak_bronnen("a")
    dialog = BulkEditMetadataDialog(
        bronnen=bronnen, taal="nl_NL", import_service=service
    )

    assert dialog.header_label.text() == "Metadata van meerdere imports bewerken"
    assert dialog.save_btn.text() == "Toepassen"
    assert dialog.cancel_btn.text() == "Annuleren"


def test_labels_en(tmp_path):
    _app()
    service = ImportService(catalog_path=tmp_path / "cat.json")
    bronnen = _maak_bronnen("a")
    dialog = BulkEditMetadataDialog(
        bronnen=bronnen, taal="en_US", import_service=service
    )

    assert dialog.header_label.text() == "Edit metadata of multiple imports"
    assert dialog.save_btn.text() == "Apply"
    assert dialog.cancel_btn.text() == "Cancel"