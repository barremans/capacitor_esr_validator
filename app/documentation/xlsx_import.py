"""
================================================================================
Module:     app/documentation/xlsx_import.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-09
Auteur:     Bart Bossuyt

Doel:       GUI-onafhankelijke orkestratielaag die xlsx_extract en
            ImportService samenbrengt voor één Excel-import. Spiegel van
            pdf_import.py. Geen Qt, geen netwerk, geen assessment.

Wijzigingen:
  v1.0.0 (2026-10-09)  Eerste versie (fase 6A): import_xlsx() met hash
                       → metadata → registratie → kopie, en de drie
                       duplicate-acties KEEP / NEW_VERSION / OVERWRITE.
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
from app.documentation.xlsx_extract import (
    XlsxExtractError,
    compute_file_hash,
    copy_xlsx_to_sources,
    extract_xlsx_metadata,
    rename_existing_xlsx_to_old,
    restore_old_xlsx,
)


def _bepaal_titel(
    bron_pad: Path, expliciete_titel: Optional[str], xlsx_titel: Optional[str]
) -> str:
    """Titel-resolutie: expliciet argument → XLSX-metadata → bestandsnaam."""
    if expliciete_titel and expliciete_titel.strip():
        return expliciete_titel.strip()
    if xlsx_titel and xlsx_titel.strip():
        return xlsx_titel.strip()
    return bron_pad.stem


def _voeg_notitie_toe(bestaand: Optional[str], extra: str) -> str:
    """Voeg een foutnotitie toe zonder een bestaande notitie te verliezen."""
    if bestaand and bestaand.strip():
        return f"{bestaand.rstrip()}\n{extra}"
    return extra


def _format_timestamp() -> str:
    """Lokale timestamp voor de .oud-<timestamp> suffix."""
    return time.strftime("%Y%m%d%H%M%S", time.localtime())


def import_xlsx(
    bron_pad: Path,
    *,
    import_service: ImportService,
    title: Optional[str] = None,
    sources_dir: Optional[Path] = None,
    notes: Optional[str] = None,
    duplicate_action: DuplicateAction = DuplicateAction.NEW_VERSION,
    category: Optional[str] = None,
    manufacturer: Optional[str] = None,
    series: Optional[str] = None,
    part_number: Optional[str] = None,
    document_version: Optional[str] = None,
    document_date: Optional[str] = None,
) -> ImportResult:
    """Importeer één Excel-bestand als documentatiebron.

    Zelfde structuur als import_pdf. Faalt met XlsxExtractError bij
    Excel- of bestandsproblemen, en met ImportValidationError bij
    catalogusproblemen.
    """
    if not isinstance(duplicate_action, DuplicateAction):
        raise ImportValidationError(
            "duplicate_action moet een DuplicateAction zijn"
        )

    bron_pad = Path(bron_pad)

    if not bron_pad.exists():
        raise XlsxExtractError(f"Excel-bestand niet gevonden: {bron_pad}")
    if not bron_pad.is_file():
        raise XlsxExtractError(f"pad is geen bestand: {bron_pad}")

    if bron_pad.suffix.lower() == ".xls":
        raise XlsxExtractError(
            "Het oude .xls-formaat wordt niet ondersteund. "
            "Converteer naar .xlsx en probeer opnieuw."
        )

    file_hash = compute_file_hash(bron_pad)
    xlsx_meta = extract_xlsx_metadata(bron_pad)

    bestaande = import_service.find_by_file_hash(file_hash)

    if duplicate_action is DuplicateAction.KEEP and bestaande is not None:
        return ImportResult(
            source=bestaande,
            changed=False,
            message="Bestaande bron behouden; niets gewijzigd.",
        )

    if duplicate_action is DuplicateAction.OVERWRITE and bestaande is not None:
        return _overwrite_xlsx(
            bron_pad=bron_pad,
            file_hash=file_hash,
            bestaande=bestaande,
            import_service=import_service,
            title=title,
            xlsx_titel=xlsx_meta.title,
            sources_dir=sources_dir,
            notes=notes,
            category=category,
            manufacturer=manufacturer,
            series=series,
            part_number=part_number,
            document_version=document_version,
            document_date=document_date,
        )

    if bestaande is not None:
        import_service.archive(bestaande.source_id)

    effectieve_titel = _bepaal_titel(bron_pad, title, xlsx_meta.title)
    registratie = import_service.register_xlsx(
        title=effectieve_titel,
        original_filename=bron_pad.name,
        file_hash=file_hash,
        notes=notes,
        category=category,
        manufacturer=manufacturer,
        series=series,
        part_number=part_number,
        document_version=document_version,
        document_date=document_date,
    )

    try:
        copy_xlsx_to_sources(
            bron_pad,
            registratie.source.source_id,
            sources_dir=sources_dir,
        )
    except XlsxExtractError as exc:
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


def _overwrite_xlsx(
    *,
    bron_pad: Path,
    file_hash: str,
    bestaande,
    import_service: ImportService,
    title: Optional[str],
    xlsx_titel: Optional[str],
    sources_dir: Optional[Path],
    notes: Optional[str],
    category: Optional[str],
    manufacturer: Optional[str],
    series: Optional[str],
    part_number: Optional[str],
    document_version: Optional[str],
    document_date: Optional[str],
) -> ImportResult:
    """Overschrijf een bestaande Excel-bron atomair."""
    timestamp = _format_timestamp()

    from app.documentation.xlsx_extract import default_sources_dir

    bron_dir = Path(sources_dir) if sources_dir else default_sources_dir()
    bestaand_pad = bron_dir / f"{bestaande.source_id}.xlsx"

    oud_pad: Optional[Path] = None
    try:
        oud_pad = rename_existing_xlsx_to_old(bestaand_pad, timestamp=timestamp)
    except XlsxExtractError:
        raise

    try:
        copy_xlsx_to_sources(
            bron_pad,
            bestaande.source_id,
            sources_dir=sources_dir,
        )
    except XlsxExtractError:
        if oud_pad is not None:
            try:
                restore_old_xlsx(oud_pad, bestaand_pad)
            except XlsxExtractError:
                pass
        raise

    nieuwe_titel = _bepaal_titel(bron_pad, expliciete_titel=title, xlsx_titel=xlsx_titel)
    return import_service.replace_source(
        bestaande.source_id,
        title=nieuwe_titel,
        file_hash=file_hash,
        original_filename=bron_pad.name,
        notes=notes,
        imported_at=import_service._now_ms(),  # type: ignore[attr-defined]
        status=ImportStatus.CONCEPT,
        category=category,
        manufacturer=manufacturer,
        series=series,
        part_number=part_number,
        document_version=document_version,
        document_date=document_date,
    )


def _update_notes(
    import_service: ImportService, source_id: str, nieuwe_notes: str
) -> None:
    """Herschrijf de notitie van één bron."""
    items = list(import_service._read_all())  # type: ignore[attr-defined]
    for idx, source in enumerate(items):
        if source.source_id == source_id:
            items[idx] = replace(source, notes=nieuwe_notes)
            import_service._write_all(items)  # type: ignore[attr-defined]
            return
    raise ValueError(f"onbekende source_id: {source_id}")