"""
================================================================================
Module:     tests/test_duplicate_source_dialog.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-07
Auteur:     Bart Bossuyt

Doel:       GUI-regressietests voor de bestaand-document-popup (fase 5D'.2a).
            Geen echte ImportService, geen netwerk, geen I/O: alleen de
            dialoog zelf.

Wijzigingen:
  v1.0.0 (2026-10-07)  Eerste versie.
================================================================================
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QDialog, QMessageBox

from app.documentation.import_models import (
    DuplicateAction,
    DuplicateMatch,
    ImportSource,
    ImportSourceType,
    ImportStatus,
)
from app.gui.dialogs.duplicate_source_dialog import DuplicateSourceDialog


def _app():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def _maak_match(
    *,
    status: ImportStatus = ImportStatus.CONCEPT,
    source_type: ImportSourceType = ImportSourceType.PDF,
    match_type: str = "file_hash",
) -> DuplicateMatch:
    if source_type is ImportSourceType.PDF:
        bestaande = ImportSource(
            source_id="abc-123",
            source_type=ImportSourceType.PDF,
            title="Bestaand document",
            imported_at=1_700_000_000_000,
            imported_by="tester",
            status=status,
            original_filename="oud.pdf",
            file_hash="deadbeef",
        )
    else:
        bestaande = ImportSource(
            source_id="abc-456",
            source_type=ImportSourceType.URL,
            title="Bestaande URL",
            imported_at=1_700_000_000_000,
            imported_by="tester",
            status=status,
            source_url="https://example.com",
        )
    return DuplicateMatch(bestaande=bestaande, match_type=match_type)


# ------------------------------------------------------------------ standaardgedrag

def test_dialoog_opent_met_behouden_geselecteerd():
    _app()
    match = _maak_match()
    dialog = DuplicateSourceDialog(match=match, taal="nl_NL")
    assert dialog.radio_behouden.isChecked() is True
    assert dialog.radio_nieuwe_versie.isChecked() is False
    assert dialog.radio_overschrijven.isChecked() is False
    assert dialog.gekozen_actie is None


def test_keuze_behouden_geeft_keep():
    _app()
    match = _maak_match()
    dialog = DuplicateSourceDialog(match=match, taal="nl_NL")
    dialog._accept()
    assert dialog.gekozen_actie is DuplicateAction.KEEP


def test_keuze_nieuwe_versie_geeft_new_version():
    _app()
    match = _maak_match()
    dialog = DuplicateSourceDialog(match=match, taal="nl_NL")
    dialog.radio_nieuwe_versie.setChecked(True)
    dialog._accept()
    assert dialog.gekozen_actie is DuplicateAction.NEW_VERSION


def test_keuze_overschrijven_geeft_overwrite():
    _app()
    match = _maak_match()
    dialog = DuplicateSourceDialog(match=match, taal="nl_NL")
    dialog.radio_overschrijven.setChecked(True)
    dialog._accept()
    assert dialog.gekozen_actie is DuplicateAction.OVERWRITE


# ------------------------------------------------------------------ vraag_actie

def test_vraag_actie_annuleren_geeft_none(monkeypatch):
    _app()
    match = _maak_match()

    # Monkeypatch exec zodat we reject simuleren.
    def _reject(self):
        return QDialog.Rejected

    monkeypatch.setattr(DuplicateSourceDialog, "exec", _reject)
    assert DuplicateSourceDialog.vraag_actie(
        match=match, taal="nl_NL"
    ) is None


def test_vraag_actie_keuze_geeft_actie(monkeypatch):
    _app()
    match = _maak_match()

    def _accept_with_overwrite(self):
        self.radio_overschrijven.setChecked(True)
        self._accept()
        return QDialog.Accepted

    monkeypatch.setattr(DuplicateSourceDialog, "exec", _accept_with_overwrite)
    resultaat = DuplicateSourceDialog.vraag_actie(match=match, taal="nl_NL")
    assert resultaat is DuplicateAction.OVERWRITE


# ------------------------------------------------------------------ samenvatting

def test_samenvatting_toont_bestaande_titel():
    _app()
    match = _maak_match()
    dialog = DuplicateSourceDialog(match=match, taal="nl_NL")
    html = dialog.info_browser.toHtml()
    assert "Bestaand document" in html


def test_samenvatting_toont_url_bij_url_match():
    _app()
    match = _maak_match(
        source_type=ImportSourceType.URL, match_type="source_url"
    )
    dialog = DuplicateSourceDialog(match=match, taal="nl_NL")
    html = dialog.info_browser.toHtml()
    assert "https://example.com" in html


# ------------------------------------------------------------------ i18n

def test_titels_komen_uit_i18n():
    _app()
    match = _maak_match()
    nl = DuplicateSourceDialog(match=match, taal="nl_NL")
    en = DuplicateSourceDialog(match=match, taal="en_US")

    assert nl.radio_behouden.text().startswith("Behouden")
    assert en.radio_behouden.text().startswith("Keep")
    assert nl.cancel_btn.text() == "Annuleren"
    assert en.cancel_btn.text() == "Cancel"
    assert nl.ok_btn.text() == "Doorgaan"
    assert en.ok_btn.text() == "Continue"


# ------------------------------------------------------------------ detailtekst

def test_detailtekst_wisselt_met_keuze():
    _app()
    match = _maak_match()
    dialog = DuplicateSourceDialog(match=match, taal="nl_NL")

    detail_behouden = dialog.detail_label.text()
    assert "ongewijzigd" in detail_behouden

    dialog.radio_overschrijven.setChecked(True)
    detail_overschrijven = dialog.detail_label.text()
    assert "oud" in detail_overschrijven.lower()
    assert detail_overschrijven != detail_behouden