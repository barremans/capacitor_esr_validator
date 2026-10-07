"""
================================================================================
Module:     app/documentation/pdf_import.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-07
Auteur:     Bart Bossuyt

Doel:       GUI-onafhankelijke orkestratielaag die pdf_extract en
            ImportService samenbrengt voor één PDF-import. Geen Qt, geen
            netwerk, geen assessment.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie: import_pdf() met hash → metadata →
                       registratie → kopie. Registratie blijft behouden bij
                       kopieerfout (optie B), met foutnotitie in notes.
  v1.1.0 (2026-10-07)  duplicate_action parameter toegevoegd voor fase
                       5D'.2a: KEEP / NEW_VERSION / OVERWRITE. Bestaande
                       aanroepen zonder duplicate_action gedragen zich
                       ongewijzigd (default = NEW_VERSION). Bij OVERWRITE
                       wordt het oude bronbestand bewaard als
                       .oud-<timestamp> en is de operatie atomair met
                       rollback bij kopieerfout.
================================================================================
"""

from __future__ import annotations

import time
from dataclasses import replace
from pathlib import Path
from typing import Optional

from app.documentation.import_models import (
    DuplicateAction,
    ImportResult,
    ImportStatus,
    ImportValidationError,
)
from app.documentation.import_service import ImportService
from app.documentation.pdf_extract import (
    PdfExtractError,
    compute_file_hash,
    copy_pdf_to_sources,
    extract_pdf_metadata,
    rename_existing_pdf_to_old,
    restore_old_pdf,
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


def _format_timestamp() -> str:
    """Lokale timestamp voor de .oud-<timestamp> suffix.

    Bewust lokaal (geen UTC) zodat de gebruiker de bestandsnaam herkent.
    Formaat: YYYYMMDDHHMMSS.
    """
    return time.strftime("%Y%m%d%H%M%S", time.localtime())


def import_pdf(
    bron_pad: Path,
    *,
    import_service: ImportService,
    title: Optional[str] = None,
    sources_dir: Optional[Path] = None,
    notes: Optional[str] = None,
    duplicate_action: DuplicateAction = DuplicateAction.NEW_VERSION,
) -> ImportResult:
    """Importeer één PDF als documentatiebron.

    Volgorde (NEW_VERSION en OVERWRITE zonder match):
      1. Valideer dat bron_pad bestaat en een bestand is.
      2. Bereken SHA-256 van het bronbestand.
      3. Lees PDF-metadata (titel, auteur, pagina's, ...).
      4. Bepaal of er al een bron met dezelfde hash bestaat.
      5. Registreer of vervang de bron in de gebruikerscatalogus.
      6. Kopieer het PDF-bestand naar sources_dir/<source_id>.pdf.

    duplicate_action bepaalt wat er gebeurt bij een bestaande match:
      - KEEP:         geen registratie; bestaande bron blijft ongewijzigd.
      - NEW_VERSION:  bestaande bron wordt gearchiveerd; nieuwe bron wordt
                      geregistreerd in CONCEPT (huidig gedrag).
      - OVERWRITE:    bestaande bron wordt bijgewerkt met hetzelfde
                      source_id, bronbestand vervangen, oud bestand
                      bewaard als .oud-<timestamp>, status terug naar
                      CONCEPT.

    Bij KEEP zonder match of NEW_VERSION zonder match: gewone registratie
    (identiek aan v1.0.0).

    Bij NEW_VERSION of OVERWRITE met kopieerfout:
      - NEW_VERSION: registratie blijft bestaan in CONCEPT met foutnotitie
        (optie B, ongewijzigd gedrag).
      - OVERWRITE:   PdfExtractError; rollback van het oude bronbestand;
        catalogus ongewijzigd.

    Faalt met PdfExtractError bij PDF- of bestandsproblemen, en met
    ImportValidationError bij catalogusproblemen.
    """
    if not isinstance(duplicate_action, DuplicateAction):
        raise ImportValidationError(
            "duplicate_action moet een DuplicateAction zijn"
        )

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

    # Stap 4 — duplicate-detectie
    bestaande = import_service.find_by_file_hash(file_hash)

    # Stap 5 — KEEP
    if duplicate_action is DuplicateAction.KEEP and bestaande is not None:
        return ImportResult(
            source=bestaande,
            changed=False,
            message="Bestaande bron behouden; niets gewijzigd.",
        )

    # Stap 6 — OVERWRITE
    if duplicate_action is DuplicateAction.OVERWRITE and bestaande is not None:
        return _overwrite_pdf(
            bron_pad=bron_pad,
            file_hash=file_hash,
            bestaande=bestaande,
            import_service=import_service,
            title=title,
            pdf_titel=pdf_meta.title,
            sources_dir=sources_dir,
            notes=notes,
        )

    # Stap 7 — NEW_VERSION (of KEEP zonder match): archiveer bestaande
    # bron indien aanwezig, dan gewone registratie.
    if bestaande is not None:
        import_service.archive(bestaande.source_id)

    effectieve_titel = _bepaal_titel(bron_pad, title, pdf_meta.title)
    registratie = import_service.register_pdf(
        title=effectieve_titel,
        original_filename=bron_pad.name,
        file_hash=file_hash,
        notes=notes,
    )

    # Stap 8 — kopiëren
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
        _update_notes(
            import_service,
            registratie.source.source_id,
            foutnotitie,
        )
        bijgewerkt = import_service.get(registratie.source.source_id)
        return ImportResult(
            source=bijgewerkt,
            changed=True,
            message=f"Kopiëren faalde: {exc}",
        )

    return registratie


def _overwrite_pdf(
    *,
    bron_pad: Path,
    file_hash: str,
    bestaande,
    import_service: ImportService,
    title: Optional[str],
    pdf_titel: Optional[str],
    sources_dir: Optional[Path],
    notes: Optional[str],
) -> ImportResult:
    """Overschrijf een bestaande PDF-bron atomair.

    Volgorde:
      1. Hernoem het bestaande bronbestand naar .oud-<timestamp>.
      2. Kopieer het nieuwe bestand naar dezelfde <source_id>.pdf.
      3. Werk de catalogus bij via replace_source (status = CONCEPT).
    Bij een fout in stap 2: rollback van het oude bestand, geen
    cataloguswijziging.
    """
    timestamp = _format_timestamp()

    # Bepaal het pad van het bestaande bronbestand.
    from app.documentation.pdf_extract import default_sources_dir

    bron_dir = Path(sources_dir) if sources_dir else default_sources_dir()
    bestaand_pad = bron_dir / f"{bestaande.source_id}.pdf"

    oud_pad: Optional[Path] = None
    try:
        oud_pad = rename_existing_pdf_to_old(bestaand_pad, timestamp=timestamp)
    except PdfExtractError:
        # Als rename faalt (bv. rechten, of .oud bestaat al), stoppen we.
        # We hebben nog niets in de catalogus gewijzigd.
        raise

    try:
        copy_pdf_to_sources(
            bron_pad,
            bestaande.source_id,
            sources_dir=sources_dir,
        )
    except PdfExtractError:
        # Rollback: zet het oude bestand terug.
        if oud_pad is not None:
            try:
                restore_old_pdf(oud_pad, bestaand_pad)
            except PdfExtractError:
                # Rollback zelf faalde; laat de oorspronkelijke fout zien.
                # De .oud-versie blijft op schijf staan zodat de gebruiker
                # niets kwijt is. De catalogus is nog niet gewijzigd.
                pass
        raise

    # Catalogus bijwerken: status terug naar CONCEPT (kernregel 11).
    nieuwe_titel = _bepaal_titel(bron_pad, title, pdf_titel)
    return import_service.replace_source(
        bestaande.source_id,
        title=nieuwe_titel,
        file_hash=file_hash,
        original_filename=bron_pad.name,
        notes=notes,
        imported_at=import_service._now_ms(),  # type: ignore[attr-defined]
        status=ImportStatus.CONCEPT,
    )


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