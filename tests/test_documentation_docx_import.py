"""
================================================================================
Module:     tests/test_documentation_docx_import.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-09
Auteur:     Bart Bossuyt

Doel:       Regressietests voor docx_import: gelukkig pad, titel-resolutie,
            foutpaden, optie B bij kopieerfout, en de drie duplicate-acties
            (KEEP / NEW_VERSION / OVERWRITE) van fase 6A.

Wijzigingen:
  v1.0.0 (2026-10-09)  Eerste versie (fase 6A).
================================================================================
"""

from __future__ import annotations

from pathlib import Path

import pytest
from docx import Document

from app.documentation.import_models import (
    DuplicateAction,
    ImportStatus,
    ImportValidationError,
)
from app.documentation.import_service import ImportService
from app.documentation.docx_extract import DocxExtractError
from app.documentation.docx_import import import_docx


@pytest.fixture()
def service(tmp_path):
    return ImportService(catalog_path=tmp_path / "imported_catalog.json")


@pytest.fixture()
def sources_dir(tmp_path):
    return tmp_path / "sources"


def _maak_docx(pad: Path, *, titel: str | None = None) -> Path:
    document = Document()
    document.add_paragraph("Inhoud")
    if titel:
        document.core_properties.title = titel
    document.save(str(pad))
    return pad


# ---------------------------------------------------------------- gelukkig pad

def test_import_docx_gelukkig_pad(service, sources_dir, tmp_path):
    pad = _maak_docx(tmp_path / "doc.docx", titel="DOCX Titel")
    result = import_docx(
        pad,
        import_service=service,
        sources_dir=sources_dir,
        title="Expliciete titel",
    )

    assert result.changed is True
    assert result.source.status is ImportStatus.CONCEPT
    assert result.source.source_type.value == "docx"
    assert result.source.title == "Expliciete titel"
    assert result.source.original_filename == "doc.docx"

    doel = sources_dir / f"{result.source.source_id}.docx"
    assert doel.exists()


def test_titel_resolutie_metadata(service, sources_dir, tmp_path):
    pad = _maak_docx(tmp_path / "doc.docx", titel="DOCX Titel")
    result = import_docx(
        pad, import_service=service, sources_dir=sources_dir
    )
    assert result.source.title == "DOCX Titel"


def test_titel_resolutie_bestandsnaam(service, sources_dir, tmp_path):
    pad = _maak_docx(tmp_path / "mijn-document.docx")
    result = import_docx(
        pad, import_service=service, sources_dir=sources_dir
    )
    assert result.source.title == "mijn-document"


# ---------------------------------------------------------------- foutpaden

def test_import_docx_ontbrekend_bestand(service, sources_dir, tmp_path):
    with pytest.raises(DocxExtractError):
        import_docx(
            tmp_path / "bestaat-niet.docx",
            import_service=service,
            sources_dir=sources_dir,
        )
    assert service.list_sources() == []


def test_import_docx_weigert_oud_doc_formaat(service, sources_dir, tmp_path):
    """Het oude .doc-formaat wordt geweigerd met een duidelijke melding."""
    pad = tmp_path / "oud.doc"
    pad.write_bytes(b"fake doc content")

    with pytest.raises(DocxExtractError) as exc_info:
        import_docx(
            pad, import_service=service, sources_dir=sources_dir
        )
    assert ".doc-formaat" in str(exc_info.value)
    assert service.list_sources() == []


# ---------------------------------------------------------------- optie B

def test_kopieerfout_behoudt_registratie(service, sources_dir, tmp_path):
    """Bij een kopieerfout blijft de registratie bestaan met foutnotitie."""
    pad = _maak_docx(tmp_path / "doc.docx")
    sources_dir.write_text("blokkerend", encoding="utf-8")

    result = import_docx(
        pad, import_service=service, sources_dir=sources_dir
    )

    assert result.source.status is ImportStatus.CONCEPT
    assert result.message is not None
    assert "Kopiëren" in result.message
    assert result.source.notes is not None
    assert "Kopiëren" in result.source.notes


# ---------------------------------------------------------------- duplicate

def test_keep_met_match_doet_niets(service, sources_dir, tmp_path):
    pad = _maak_docx(tmp_path / "doc.docx")

    eerste = import_docx(
        pad, import_service=service, sources_dir=sources_dir
    )
    result = import_docx(
        pad,
        import_service=service,
        sources_dir=sources_dir.parent / "sources2",
        duplicate_action=DuplicateAction.KEEP,
    )

    assert result.changed is False
    assert result.source.source_id == eerste.source.source_id
    assert len(service.list_sources()) == 1


def test_new_version_archiveert_oude(service, sources_dir, tmp_path):
    pad = _maak_docx(tmp_path / "doc.docx")

    eerste = import_docx(
        pad, import_service=service, sources_dir=sources_dir
    )
    tweede = import_docx(
        pad,
        import_service=service,
        sources_dir=sources_dir.parent / "sources2",
        duplicate_action=DuplicateAction.NEW_VERSION,
    )

    assert eerste.source.source_id != tweede.source.source_id
    opnieuw = service.get(eerste.source.source_id)
    assert opnieuw.status is ImportStatus.GEARCHIVEERD
    assert tweede.source.status is ImportStatus.CONCEPT


def test_overwrite_behoudt_source_id(service, sources_dir, tmp_path):
    pad = _maak_docx(tmp_path / "doc.docx", titel="Oude titel")

    eerste = import_docx(
        pad, import_service=service, sources_dir=sources_dir
    )
    result = import_docx(
        pad,
        import_service=service,
        sources_dir=sources_dir,
        title="Nieuwe titel",
        duplicate_action=DuplicateAction.OVERWRITE,
    )

    assert result.source.source_id == eerste.source.source_id
    assert result.source.title == "Nieuwe titel"
    assert result.source.status is ImportStatus.CONCEPT
    assert len(service.list_sources()) == 1


def test_overwrite_bewaart_oude_bron(service, sources_dir, tmp_path):
    pad = _maak_docx(tmp_path / "doc.docx")

    eerste = import_docx(
        pad, import_service=service, sources_dir=sources_dir
    )
    import_docx(
        pad,
        import_service=service,
        sources_dir=sources_dir,
        duplicate_action=DuplicateAction.OVERWRITE,
    )

    oude = list(
        sources_dir.glob(f"{eerste.source.source_id}.docx.oud-*")
    )
    assert len(oude) == 1


def test_duplicate_action_ongeldig_type(service, sources_dir, tmp_path):
    pad = _maak_docx(tmp_path / "doc.docx")
    with pytest.raises(ImportValidationError):
        import_docx(
            pad,
            import_service=service,
            sources_dir=sources_dir,
            duplicate_action="keep",  # type: ignore[arg-type]
        )