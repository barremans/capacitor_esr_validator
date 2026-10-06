"""
================================================================================
Module:     app/documentation/pdf_import.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-06
Auteur:     Bart Bossuyt

Doel:       GUI-onafhankelijke orkestratielaag die pdf_extract en
            ImportService samenbrengt voor één PDF-import. Geen Qt, geen
            netwerk, geen assessment.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie: import_pdf() met hash → metadata →
                       registratie → kopie. Registratie blijft behouden bij
                       kopieerfout (optie B), met foutnotitie in notes.
================================================================================
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Optional

from app.documentation.import_models import ImportResult
from app.documentation.import_service import ImportService
from app.documentation.pdf_extract import (
    PdfExtractError,
    compute_file_hash,
    copy_pdf_to_sources,
    extract_pdf_metadata,
)


def _bepaal_titel(
    bron_pad: Path, expliciete_titel: Optional[str], pdf_titel: Optional[str]
) -> str:
    """Titel-resolutie: expliciet argument → PDF-metadata → bestandsnaam."""
    if expliciete_titel and expliciete_titel.strip():
        return expliciete_titel.strip()
    if pdf_titel and pdf_titel.strip():
        return pdf_titel.strip()
    return bron_pad.stem


def _voeg_notitie_toe(bestaand: Optional[str], extra: str) -> str:
    """Voeg een foutnotitie toe zonder een bestaande notitie te verliezen."""
    if bestaand and bestaand.strip():
        return f"{bestaand.rstrip()}\n{extra}"
    return extra


def import_pdf(
    bron_pad: Path,
    *,
    import_service: ImportService,
    title: Optional[str] = None,
    sources_dir: Optional[Path] = None,
    notes: Optional[str] = None,
) -> ImportResult:
    """Importeer één PDF als nieuwe documentatiebron.

    Volgorde:
      1. Valideer dat bron_pad bestaat en een bestand is.
      2. Bereken SHA-256 van het bronbestand.
      3. Lees PDF-metadata (titel, auteur, pagina's, ...).
      4. Registreer de bron als CONCEPT in de gebruikerscatalogus.
      5. Kopieer het PDF-bestand naar sources_dir/<source_id>.pdf.

    Als stap 5 faalt, blijft de registratie bestaan in CONCEPT-status met
    een foutnotitie in notes. De bron wordt niet stil verwijderd.

    Faalt met PdfExtractError bij PDF- of bestandsproblemen, en met
    ImportValidationError bij catalogusproblemen.
    """
    bron_pad = Path(bron_pad)

    # Stap 1 — validatie
    if not bron_pad.exists():
        raise PdfExtractError(f"PDF-bestand niet gevonden: {bron_pad}")
    if not bron_pad.is_file():
        raise PdfExtractError(f"pad is geen bestand: {bron_pad}")

    # Stap 2 — hash
    file_hash = compute_file_hash(bron_pad)

    # Stap 3 — metadata
    pdf_meta = extract_pdf_metadata(bron_pad)

    # Stap 4 — registratie
    effectieve_titel = _bepaal_titel(bron_pad, title, pdf_meta.title)
    registratie = import_service.register_pdf(
        title=effectieve_titel,
        original_filename=bron_pad.name,
        file_hash=file_hash,
        notes=notes,
    )

    # Stap 5 — kopiëren
    try:
        copy_pdf_to_sources(
            bron_pad,
            registratie.source.source_id,
            sources_dir=sources_dir,
        )
    except PdfExtractError as exc:
        foutnotitie = _voeg_notitie_toe(
            registratie.source.notes,
            f"Kopiëren van bronbestand faalde: {exc}",
        )
        # Werk de bron bij met de foutnotitie zonder de status te wijzigen.
        # De ImportService heeft geen algemene update-API, dus we schrijven
        # de notitie via een interne herschrijfactie van de catalogus.
        _update_notes(
            import_service,
            registratie.source.source_id,
            foutnotitie,
        )
        # Herlees de bron zodat de ImportResult de bijgewerkte notitie toont.
        bijgewerkt = import_service.get(registratie.source.source_id)
        return ImportResult(
            source=bijgewerkt,
            changed=True,
            message=f"Kopiëren faalde: {exc}",
        )

    return registratie


def _update_notes(
    import_service: ImportService, source_id: str, nieuwe_notes: str
) -> None:
    """Herschrijf de notitie van één bron.

    Kleine, expliciete helper. ImportService heeft geen publieke
    update-API; we hergebruiken de interne _read_all/_write_all om geen
    nieuwe publieke API toe te voegen vóór daar behoefte aan is.
    """
    items = list(import_service._read_all())  # type: ignore[attr-defined]
    for idx, source in enumerate(items):
        if source.source_id == source_id:
            items[idx] = replace(source, notes=nieuwe_notes)
            import_service._write_all(items)  # type: ignore[attr-defined]
            return
    raise ValueError(f"onbekende source_id: {source_id}")