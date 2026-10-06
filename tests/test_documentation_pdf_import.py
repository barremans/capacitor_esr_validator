"""
================================================================================
Module:     tests/test_documentation_pdf_import.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-06
Auteur:     Bart Bossuyt

Doel:       Regressietests voor pdf_import: gelukkig pad, titel-resolutie,
            hash-integratie, kopieerfout-gedrag (optie B).

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie.
================================================================================
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.documentation.import_models import ImportStatus
from app.documentation.import_service import ImportService
from app.documentation.pdf_extract import PdfExtractError
from app.documentation.pdf_import import import_pdf


# ------------------------------------------------------------------ hulpfuncties

def _maak_eenvoudige_pdf(
    pad: Path, *, titel: str = "Testdocument", auteur: str = "Testauteur"
) -> Path:
    """Maak een minimale PDF met pypdf's eigen writer."""
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.add_metadata({
        "/Title": titel,
        "/Author": auteur,
    })
    with pad.open("wb") as handle:
        writer.write(handle)
    return pad


@pytest.fixture()
def service(tmp_path):
    return ImportService(catalog_path=tmp_path / "imported_catalog.json")


@pytest.fixture()
def sources_dir(tmp_path):
    return tmp_path / "sources"


# ------------------------------------------------------------------ gelukkig pad

def test_import_pdf_gelukkig_pad(tmp_path, service, sources_dir):
    bron = _maak_eenvoudige_pdf(tmp_path / "doc.pdf")

    result = import_pdf(
        bron,
        import_service=service,
        title="Expliciete titel",
        sources_dir=sources_dir,
    )

    assert result.changed is True
    assert result.source.status is ImportStatus.CONCEPT
    assert result.source.source_type.value == "pdf"
    assert result.source.original_filename == "doc.pdf"
    assert result.source.title == "Expliciete titel"
    assert result.source.file_hash is not None
    assert len(result.source.file_hash) == 64  # SHA-256 hex

    # Gekopieerd bestand bestaat en heeft juiste naam
    gekopieerd = sources_dir / f"{result.source.source_id}.pdf"
    assert gekopieerd.exists()
    assert gekopieerd.read_bytes() == bron.read_bytes()


def test_import_pdf_zonder_titel_gebruikt_pdf_metadata(tmp_path, service, sources_dir):
    bron = _maak_eenvoudige_pdf(tmp_path / "doc.pdf", titel="PDF-titel")

    result = import_pdf(
        bron,
        import_service=service,
        sources_dir=sources_dir,
    )

    assert result.source.title == "PDF-titel"


def test_import_pdf_zonder_pdf_titel_gebruikt_bestandsnaam(tmp_path, service, sources_dir):
    from pypdf import PdfWriter

    bron = tmp_path / "mijn_document.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    # Geen metadata
    with bron.open("wb") as handle:
        writer.write(handle)

    result = import_pdf(
        bron,
        import_service=service,
        sources_dir=sources_dir,
    )

    assert result.source.title == "mijn_document"


def test_import_pdf_hash_komt_overeen_met_bron(tmp_path, service, sources_dir):
    import hashlib

    bron = _maak_eenvoudige_pdf(tmp_path / "doc.pdf")
    verwachte_hash = hashlib.sha256(bron.read_bytes()).hexdigest()

    result = import_pdf(
        bron,
        import_service=service,
        sources_dir=sources_dir,
    )

    assert result.source.file_hash == verwachte_hash


def test_import_pdf_met_notes(tmp_path, service, sources_dir):
    bron = _maak_eenvoudige_pdf(tmp_path / "doc.pdf")

    result = import_pdf(
        bron,
        import_service=service,
        sources_dir=sources_dir,
        notes="Handmatige notitie",
    )

    assert result.source.notes == "Handmatige notitie"


# ------------------------------------------------------------------ fouten

def test_import_pdf_ontbrekend_bestand_faalt(tmp_path, service, sources_dir):
    with pytest.raises(PdfExtractError):
        import_pdf(
            tmp_path / "bestaat-niet.pdf",
            import_service=service,
            sources_dir=sources_dir,
        )


def test_import_pdf_map_faalt(tmp_path, service, sources_dir):
    map_pad = tmp_path / "map"
    map_pad.mkdir()
    with pytest.raises(PdfExtractError):
        import_pdf(
            map_pad,
            import_service=service,
            sources_dir=sources_dir,
        )


def test_import_pdf_ongeldige_pdf_faalt(tmp_path, service, sources_dir):
    bron = tmp_path / "geen.pdf"
    bron.write_text("dit is geen pdf", encoding="utf-8")
    with pytest.raises(PdfExtractError):
        import_pdf(
            bron,
            import_service=service,
            sources_dir=sources_dir,
        )


# ------------------------------------------------------------------ optie B

def test_kopieerfout_behoudt_registratie_met_foutnotitie(
    tmp_path, service, sources_dir
):
    """Als het kopiëren faalt, blijft de bron bestaan in CONCEPT."""
    bron = _maak_eenvoudige_pdf(tmp_path / "doc.pdf")

    # Maak sources_dir onbruikbaar: een bestand waar een map moet komen.
    sources_dir.write_text("ik ben een bestand, geen map", encoding="utf-8")

    result = import_pdf(
        bron,
        import_service=service,
        sources_dir=sources_dir,
    )

    # Registratie bestaat
    assert result.source.status is ImportStatus.CONCEPT
    assert result.message is not None
    assert "Kopi" in result.message

    # Foutnotitie aanwezig
    assert result.source.notes is not None
    assert "Kopi" in result.source.notes

    # Bron is opvraagbaar via de service
    opnieuw = service.get(result.source.source_id)
    assert opnieuw.notes is not None
    assert "Kopi" in opnieuw.notes


def test_kopieerfout_behoudt_bestaande_notes(tmp_path, service, sources_dir):
    bron = _maak_eenvoudige_pdf(tmp_path / "doc.pdf")
    sources_dir.write_text("blokkerend bestand", encoding="utf-8")

    result = import_pdf(
        bron,
        import_service=service,
        sources_dir=sources_dir,
        notes="Belangrijke gebruikersnotitie",
    )

    assert result.source.notes is not None
    assert "Belangrijke gebruikersnotitie" in result.source.notes
    assert "Kopi" in result.source.notes


# ------------------------------------------------------------------ idempotentie

def test_twee_keer_importeren_geeft_twee_bronnen(tmp_path, service, sources_dir):
    bron = _maak_eenvoudige_pdf(tmp_path / "doc.pdf")

    eerste = import_pdf(bron, import_service=service, sources_dir=sources_dir)

    # Voor de tweede import gebruiken we een andere sources_dir, want
    # copy_pdf_to_sources weigert een bestaand doel.
    tweede = import_pdf(
        bron,
        import_service=service,
        sources_dir=tmp_path / "sources2",
    )

    assert eerste.source.source_id != tweede.source.source_id
    items = service.list_sources()
    assert len(items) == 2


def test_import_pdf_verschillende_bestanden_verschillende_hash(
    tmp_path, service, sources_dir
):
    bron_a = _maak_eenvoudige_pdf(tmp_path / "a.pdf", titel="A")
    bron_b = _maak_eenvoudige_pdf(tmp_path / "b.pdf", titel="B")

    a = import_pdf(bron_a, import_service=service, sources_dir=sources_dir)
    b = import_pdf(
        bron_b,
        import_service=service,
        sources_dir=sources_dir,
    )

    assert a.source.file_hash != b.source.file_hash