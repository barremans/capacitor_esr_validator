"""
================================================================================
Module:     tests/test_documentation_pdf_import.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-07
Auteur:     Bart Bossuyt

Doel:       Regressietests voor pdf_import: gelukkig pad, titel-resolutie,
            hash-integratie, kopieerfout-gedrag (optie B), en de drie
            duplicate-acties (KEEP / NEW_VERSION / OVERWRITE) van fase
            5D'.2a.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie.
  v1.1.0 (2026-10-07)  Tests voor duplicate_action en atomair
                        overschrijven met rollback.
================================================================================
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.documentation.import_models import (
    DuplicateAction,
    ImportStatus,
)
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
    bron = _maak_eenvoudige_pdf(tmp_path / "doc.pdf")
    sources_dir.write_text("ik ben een bestand, geen map", encoding="utf-8")

    result = import_pdf(
        bron,
        import_service=service,
        sources_dir=sources_dir,
    )

    assert result.source.status is ImportStatus.CONCEPT
    assert result.message is not None
    assert "Kopi" in result.message
    assert result.source.notes is not None
    assert "Kopi" in result.source.notes

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


# ============================================================================
# NIEUW IN v1.1.0 — duplicate_action (KEEP / NEW_VERSION / OVERWRITE)
# ============================================================================

def _hash_van(pad: Path) -> str:
    import hashlib

    return hashlib.sha256(pad.read_bytes()).hexdigest()


def test_duplicate_action_ongeldig_type_faalt(tmp_path, service, sources_dir):
    from app.documentation.import_models import ImportValidationError

    bron = _maak_eenvoudige_pdf(tmp_path / "doc.pdf")
    with pytest.raises(ImportValidationError):
        import_pdf(
            bron,
            import_service=service,
            sources_dir=sources_dir,
            duplicate_action="keep",  # type: ignore[arg-type]
        )


# ------------------------------------------------------------------ KEEP

def test_keep_zonder_match_registreert_normaal(tmp_path, service, sources_dir):
    bron = _maak_eenvoudige_pdf(tmp_path / "doc.pdf")
    result = import_pdf(
        bron,
        import_service=service,
        sources_dir=sources_dir,
        duplicate_action=DuplicateAction.KEEP,
    )
    assert result.changed is True
    assert len(service.list_sources()) == 1


def test_keep_met_match_doet_niets(tmp_path, service, sources_dir):
    bron = _maak_eenvoudige_pdf(tmp_path / "doc.pdf")

    eerste = import_pdf(
        bron, import_service=service, sources_dir=sources_dir
    )

    result = import_pdf(
        bron,
        import_service=service,
        sources_dir=tmp_path / "sources2",
        duplicate_action=DuplicateAction.KEEP,
    )

    assert result.changed is False
    assert result.source.source_id == eerste.source.source_id
    assert len(service.list_sources()) == 1


# ------------------------------------------------------------------ NEW_VERSION

def test_new_version_met_match_archiveert_oude(tmp_path, service, sources_dir):
    bron = _maak_eenvoudige_pdf(tmp_path / "doc.pdf")

    eerste = import_pdf(
        bron, import_service=service, sources_dir=sources_dir
    )

    tweede = import_pdf(
        bron,
        import_service=service,
        sources_dir=tmp_path / "sources2",
        duplicate_action=DuplicateAction.NEW_VERSION,
    )

    assert eerste.source.source_id != tweede.source.source_id
    # Oude bron gearchiveerd
    opnieuw = service.get(eerste.source.source_id)
    assert opnieuw.status is ImportStatus.GEARCHIVEERD
    # Nieuwe bron concept
    assert tweede.source.status is ImportStatus.CONCEPT
    assert len(service.list_sources()) == 2


def test_new_version_zonder_match_registreert_normaal(tmp_path, service, sources_dir):
    bron = _maak_eenvoudige_pdf(tmp_path / "doc.pdf")
    result = import_pdf(
        bron,
        import_service=service,
        sources_dir=sources_dir,
        duplicate_action=DuplicateAction.NEW_VERSION,
    )
    assert result.changed is True
    assert len(service.list_sources()) == 1


# ------------------------------------------------------------------ OVERWRITE

def test_overwrite_met_match_behoudt_source_id(tmp_path, service, sources_dir):
    # Maak twee PDF's met DEZELFDE inhoud (en dus dezelfde hash).
    bron1 = _maak_eenvoudige_pdf(tmp_path / "doc.pdf", titel="Versie 1")
    eerste = import_pdf(
        bron1, import_service=service, sources_dir=sources_dir
    )

    # Zelfde hash, dus duplicate. We maken een nieuw bestand met dezelfde
    # bytes (kopie) en importeren met OVERWRITE.
    bron2 = tmp_path / "doc2.pdf"
    bron2.write_bytes(bron1.read_bytes())

    result = import_pdf(
        bron2,
        import_service=service,
        sources_dir=sources_dir,
        title="Versie 2",
        duplicate_action=DuplicateAction.OVERWRITE,
    )

    assert result.source.source_id == eerste.source.source_id
    assert result.source.title == "Versie 2"
    assert result.source.status is ImportStatus.CONCEPT
    assert len(service.list_sources()) == 1


def test_overwrite_bewaart_oud_bestand(tmp_path, service, sources_dir):
    bron1 = _maak_eenvoudige_pdf(tmp_path / "doc.pdf", titel="Versie 1")
    eerste = import_pdf(
        bron1, import_service=service, sources_dir=sources_dir
    )

    bron2 = tmp_path / "doc2.pdf"
    bron2.write_bytes(bron1.read_bytes())

    import_pdf(
        bron2,
        import_service=service,
        sources_dir=sources_dir,
        duplicate_action=DuplicateAction.OVERWRITE,
    )

    # Er moet nu een .oud-* bestand zijn
    oude = list(sources_dir.glob(f"{eerste.source.source_id}.pdf.oud-*"))
    assert len(oude) == 1


def test_overwrite_rollback_bij_kopieerfout(tmp_path, service, sources_dir):
    bron1 = _maak_eenvoudige_pdf(tmp_path / "doc.pdf", titel="Versie 1")
    eerste = import_pdf(
        bron1, import_service=service, sources_dir=sources_dir
    )

    # bron2 wordt een ongeldige PDF met dezelfde hash? Dat kan niet, want
    # de hash komt juist uit de bytes. We gebruiken daarom een andere
    # methode: we zorgen dat copy faalt door de sources_dir te blokkeren
    # NA de eerste import. Maar de eerste import heeft de map al gemaakt.
    #
    # We testen het rollback-pad door de bron te verwijderen vóór de
    # tweede import: compute_file_hash faalt dan al vroeg. Dat is geen
    # rollback-test. Daarom gebruiken we een truc: we zorgen dat de
    # rename naar .oud lukt, maar de copy daarna faalt, door de bron te
    # verplaatsen naar een niet-bestaand pad? Dat kan niet, want bron_pad
    # wordt gevalideerd.
    #
    # Simpelere rollback-test: monkeypatch copy_pdf_to_sources zodat het
    # faalt, en controleer dat het oude bestand terugstaat en de
    # catalogus ongewijzigd is.
    import app.documentation.pdf_import as pdf_import_module

    bron2 = tmp_path / "doc2.pdf"
    bron2.write_bytes(bron1.read_bytes())

    originele_pad = sources_dir / f"{eerste.source.source_id}.pdf"
    assert originele_pad.exists()

    def _kapotte_copy(*args, **kwargs):
        raise PdfExtractError("test-copy-fout")

    originele_copy = pdf_import_module.copy_pdf_to_sources
    pdf_import_module.copy_pdf_to_sources = _kapotte_copy
    try:
        with pytest.raises(PdfExtractError):
            import_pdf(
                bron2,
                import_service=service,
                sources_dir=sources_dir,
                duplicate_action=DuplicateAction.OVERWRITE,
            )
    finally:
        pdf_import_module.copy_pdf_to_sources = originele_copy

    # Oud bestand moet terug op zijn plaats staan
    assert originele_pad.exists()
    # Geen .oud-bestand meer
    oude = list(sources_dir.glob(f"{eerste.source.source_id}.pdf.oud-*"))
    assert oude == []
    # Catalogus ongewijzigd
    ongewijzigd = service.get(eerste.source.source_id)
    assert ongewijzigd.title == eerste.source.title


def test_overwrite_zonder_match_registreert_normaal(tmp_path, service, sources_dir):
    bron = _maak_eenvoudige_pdf(tmp_path / "doc.pdf")
    result = import_pdf(
        bron,
        import_service=service,
        sources_dir=sources_dir,
        duplicate_action=DuplicateAction.OVERWRITE,
    )
    assert result.changed is True
    assert len(service.list_sources()) == 1