"""
================================================================================
Module:     tests/test_documentation_import_models.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-06
Auteur:     Bart Bossuyt

Doel:       Regressietests voor import_models: enums, frozen-gedrag,
            verplichte velden, serialisatie, statusovergangen.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie.
================================================================================
"""

from __future__ import annotations

import dataclasses

import pytest

from app.documentation.import_models import (
    ImportSource,
    ImportSourceType,
    ImportStatus,
    ImportValidationError,
    is_allowed_transition,
)


def _geldige_pdf_source(**overrides) -> ImportSource:
    basis = dict(
        source_id="src-1",
        source_type=ImportSourceType.PDF,
        title="Datasheet Panasonic FR",
        imported_at=1_700_000_000_000,
        imported_by="tester",
        status=ImportStatus.CONCEPT,
        original_filename="fr_series.pdf",
        source_url=None,
        file_hash=None,
        notes=None,
    )
    basis.update(overrides)
    return ImportSource(**basis)


def _geldige_url_source(**overrides) -> ImportSource:
    basis = dict(
        source_id="src-2",
        source_type=ImportSourceType.URL,
        title="Fabrikantpagina",
        imported_at=1_700_000_000_000,
        imported_by="tester",
        status=ImportStatus.CONCEPT,
        original_filename=None,
        source_url="https://example.com/doc",
        file_hash=None,
        notes=None,
    )
    basis.update(overrides)
    return ImportSource(**basis)


# ---------------------------------------------------------------- enums

def test_enum_waarden_vast():
    assert ImportSourceType.PDF.value == "pdf"
    assert ImportSourceType.URL.value == "url"
    assert ImportStatus.CONCEPT.value == "concept"
    assert ImportStatus.ACTIEF.value == "actief"
    assert ImportStatus.GEARCHIVEERD.value == "gearchiveerd"


# ---------------------------------------------------------------- frozen

def test_import_source_is_frozen():
    src = _geldige_pdf_source()
    with pytest.raises(dataclasses.FrozenInstanceError):
        src.title = "anders"  # type: ignore[misc]


# ---------------------------------------------------------------- validatie

def test_pdf_zonder_filename_faalt():
    with pytest.raises(ImportValidationError):
        _geldige_pdf_source(original_filename=None)


def test_url_zonder_url_faalt():
    with pytest.raises(ImportValidationError):
        _geldige_url_source(source_url=None)


def test_pdf_met_url_faalt():
    with pytest.raises(ImportValidationError):
        _geldige_pdf_source(source_url="https://example.com")


def test_url_met_filename_faalt():
    with pytest.raises(ImportValidationError):
        _geldige_url_source(original_filename="x.pdf")


def test_lege_titel_faalt():
    with pytest.raises(ImportValidationError):
        _geldige_pdf_source(title="   ")


def test_negatieve_imported_at_faalt():
    with pytest.raises(ImportValidationError):
        _geldige_pdf_source(imported_at=0)


def test_lege_imported_by_faalt():
    with pytest.raises(ImportValidationError):
        _geldige_pdf_source(imported_by="")


# ---------------------------------------------------------------- serialisatie

def test_to_dict_en_from_dict_rondrit_pdf():
    src = _geldige_pdf_source(file_hash="abc123", notes="test")
    hersteld = ImportSource.from_dict(src.to_dict())
    assert hersteld == src


def test_to_dict_en_from_dict_rondrit_url():
    src = _geldige_url_source(notes="url-notitie")
    hersteld = ImportSource.from_dict(src.to_dict())
    assert hersteld == src


def test_from_dict_met_ontbrekend_veld_faalt():
    data = _geldige_pdf_source().to_dict()
    del data["title"]
    with pytest.raises(ImportValidationError):
        ImportSource.from_dict(data)


def test_from_dict_met_ongeldige_status_faalt():
    data = _geldige_pdf_source().to_dict()
    data["status"] = "bestaat-niet"
    with pytest.raises(ImportValidationError):
        ImportSource.from_dict(data)


def test_from_dict_met_ongeldig_type_faalt():
    data = _geldige_pdf_source().to_dict()
    data["source_type"] = "onbekend"
    with pytest.raises(ImportValidationError):
        ImportSource.from_dict(data)


# ---------------------------------------------------------------- overgangen

@pytest.mark.parametrize(
    "huidige,nieuwe,verwacht",
    [
        (ImportStatus.CONCEPT, ImportStatus.ACTIEF, True),
        (ImportStatus.CONCEPT, ImportStatus.GEARCHIVEERD, True),
        (ImportStatus.ACTIEF, ImportStatus.CONCEPT, True),
        (ImportStatus.ACTIEF, ImportStatus.GEARCHIVEERD, True),
        (ImportStatus.GEARCHIVEERD, ImportStatus.CONCEPT, True),
        (ImportStatus.GEARCHIVEERD, ImportStatus.ACTIEF, False),
        (ImportStatus.CONCEPT, ImportStatus.CONCEPT, False),
        (ImportStatus.ACTIEF, ImportStatus.ACTIEF, False),
    ],
)
def test_statusovergangen(huidige, nieuwe, verwacht):
    assert is_allowed_transition(huidige, nieuwe) is verwacht


def test_overgang_met_verkeerd_type_faalt():
    with pytest.raises(ImportValidationError):
        is_allowed_transition("concept", ImportStatus.ACTIEF)  # type: ignore[arg-type]
    with pytest.raises(ImportValidationError):
        is_allowed_transition(ImportStatus.CONCEPT, "actief")  # type: ignore[arg-type]