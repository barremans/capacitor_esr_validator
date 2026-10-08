"""
================================================================================
Module:     app/documentation/url_import.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.2.0
Datum:      2026-10-07
Auteur:     Bart Bossuyt

Doel:       GUI-onafhankelijke orkestratielaag die url_fetch en
            ImportService samenbrengt voor één URL-import. Spiegel van
            pdf_import.py. Geen Qt, geen assessment.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie: import_url() met metadata → content
                       → registratie → snapshot. Registratie blijft behouden
                       bij snapshot-fout (optie B).
  v1.1.0 (2026-10-07)  duplicate_action parameter toegevoegd voor fase
                       5D'.2a: KEEP / NEW_VERSION / OVERWRITE. Bestaande
                       aanroepen zonder duplicate_action gedragen zich
                       ongewijzigd (default = NEW_VERSION). Bij OVERWRITE
                       wordt de oude snapshot bewaard als
                       .oud-<timestamp> en is de operatie atomair met
                       rollback bij snapshot-fout.
  v1.2.0 (2026-10-07)  Metadata-uitbreiding (fase 5D'.2b): optionele
                       parameters category, manufacturer, series,
                       part_number, document_version, document_date.
                       Worden doorgegeven aan register_url en
                       replace_source. Backward-compatible: defaults None.
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
from app.documentation.url_fetch import (
    UrlFetchError,
    UrlMetadata,
    fetch_url_content,
    fetch_url_metadata,
    rename_existing_snapshot_to_old,
    restore_old_snapshot,
    save_url_snapshot,
)


def _bepaal_titel(
    url: str, expliciete_titel: Optional[str], meta: UrlMetadata
) -> str:
    """Titel-resolutie: expliciet argument → og:title → title → hostnaam."""
    if expliciete_titel and expliciete_titel.strip():
        return expliciete_titel.strip()
    if meta.og_title and meta.og_title.strip():
        return meta.og_title.strip()
    if meta.title and meta.title.strip():
        return meta.title.strip()
    # Laatste redmiddel: de hostnaam uit de URL.
    from urllib.parse import urlparse

    host = urlparse(url).netloc or url
    return host


def _voeg_notitie_toe(bestaand: Optional[str], extra: str) -> str:
    """Voeg een foutnotitie toe zonder een bestaande notitie te verliezen."""
    if bestaand and bestaand.strip():
        return f"{bestaand.rstrip()}\n{extra}"
    return extra


def _format_timestamp() -> str:
    """Lokale timestamp voor de .oud-<timestamp> suffix."""
    return time.strftime("%Y%m%d%H%M%S", time.localtime())


def import_url(
    url: str,
    *,
    import_service: ImportService,
    title: Optional[str] = None,
    snapshots_dir: Optional[Path] = None,
    notes: Optional[str] = None,
    duplicate_action: DuplicateAction = DuplicateAction.NEW_VERSION,
    category: Optional[str] = None,
    manufacturer: Optional[str] = None,
    series: Optional[str] = None,
    part_number: Optional[str] = None,
    document_version: Optional[str] = None,
    document_date: Optional[str] = None,
) -> ImportResult:
    """Importeer één URL als documentatiebron met lokale snapshot.

    Volgorde (NEW_VERSION en OVERWRITE zonder match):
      1. Valideer de URL (via url_fetch).
      2. Haal metadata op (titel, description, og, taal).
      3. Haal de HTML-inhoud op.
      4. Bepaal of er al een bron met dezelfde URL bestaat.
      5. Registreer of vervang de bron in de gebruikerscatalogus.
      6. Bewaar de HTML als snapshot in snapshots_dir/<source_id>.html.

    duplicate_action bepaalt wat er gebeurt bij een bestaande match:
      - KEEP:         geen registratie; bestaande bron blijft ongewijzigd.
      - NEW_VERSION:  bestaande bron wordt gearchiveerd; nieuwe bron wordt
                      geregistreerd in CONCEPT (huidig gedrag).
      - OVERWRITE:    bestaande bron wordt bijgewerkt met hetzelfde
                      source_id, snapshot vervangen, oude snapshot
                      bewaard als .oud-<timestamp>, status terug naar
                      CONCEPT.

    Metadata-parameters (sinds 5D'.2b) zijn optioneel. Ze worden
    doorgegeven aan register_url of, bij OVERWRITE, aan replace_source.
    Lege strings worden door ImportSource genormaliseerd naar None.

    Bij KEEP zonder match of NEW_VERSION zonder match: gewone registratie.

    Bij NEW_VERSION of OVERWRITE met snapshot-fout:
      - NEW_VERSION: registratie blijft bestaan in CONCEPT met foutnotitie
        (optie B, ongewijzigd gedrag).
      - OVERWRITE:   UrlFetchError; rollback van de oude snapshot;
        catalogus ongewijzigd.

    Faalt met UrlFetchError bij netwerk- of opslagproblemen, en met
    ImportValidationError bij catalogusproblemen.
    """
    if not isinstance(duplicate_action, DuplicateAction):
        raise ImportValidationError(
            "duplicate_action moet een DuplicateAction zijn"
        )

    # Stap 1+2 — validatie en metadata
    meta = fetch_url_metadata(url)

    # Stap 3 — inhoud
    html = fetch_url_content(url)

    # Stap 4 — duplicate-detectie (op meta.url, want dat is wat we opslaan)
    bestaande = import_service.find_by_source_url(meta.url)

    # Stap 5 — KEEP
    if duplicate_action is DuplicateAction.KEEP and bestaande is not None:
        return ImportResult(
            source=bestaande,
            changed=False,
            message="Bestaande bron behouden; niets gewijzigd.",
        )

    # Stap 6 — OVERWRITE
    if duplicate_action is DuplicateAction.OVERWRITE and bestaande is not None:
        return _overwrite_url(
            html=html,
            meta=meta,
            bestaande=bestaande,
            import_service=import_service,
            title=title,
            snapshots_dir=snapshots_dir,
            notes=notes,
            category=category,
            manufacturer=manufacturer,
            series=series,
            part_number=part_number,
            document_version=document_version,
            document_date=document_date,
        )

    # Stap 7 — NEW_VERSION (of KEEP zonder match): archiveer bestaande
    # bron indien aanwezig, dan gewone registratie.
    if bestaande is not None:
        import_service.archive(bestaande.source_id)

    effectieve_titel = _bepaal_titel(meta.url, title, meta)
    registratie = import_service.register_url(
        title=effectieve_titel,
        source_url=meta.url,
        notes=notes,
        category=category,
        manufacturer=manufacturer,
        series=series,
        part_number=part_number,
        document_version=document_version,
        document_date=document_date,
    )

    # Stap 8 — snapshot
    try:
        save_url_snapshot(
            html,
            registratie.source.source_id,
            snapshots_dir=snapshots_dir,
        )
    except UrlFetchError as exc:
        foutnotitie = _voeg_notitie_toe(
            registratie.source.notes,
            f"Opslaan van snapshot faalde: {exc}",
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
            message=f"Snapshot opslaan faalde: {exc}",
        )

    return registratie


def _overwrite_url(
    *,
    html: str,
    meta: UrlMetadata,
    bestaande,
    import_service: ImportService,
    title: Optional[str],
    snapshots_dir: Optional[Path],
    notes: Optional[str],
    category: Optional[str],
    manufacturer: Optional[str],
    series: Optional[str],
    part_number: Optional[str],
    document_version: Optional[str],
    document_date: Optional[str],
) -> ImportResult:
    """Overschrijf een bestaande URL-bron atomair.

    Volgorde:
      1. Hernoem de bestaande snapshot naar .oud-<timestamp>.
      2. Schrijf de nieuwe snapshot naar dezelfde <source_id>.html.
      3. Werk de catalogus bij via replace_source (status = CONCEPT).
    Bij een fout in stap 2: rollback van de oude snapshot, geen
    cataloguswijziging.
    """
    timestamp = _format_timestamp()

    from app.documentation.url_fetch import default_snapshots_dir

    snap_dir = (
        Path(snapshots_dir) if snapshots_dir else default_snapshots_dir()
    )
    bestaand_pad = snap_dir / f"{bestaande.source_id}.html"

    oud_pad: Optional[Path] = None
    try:
        oud_pad = rename_existing_snapshot_to_old(
            bestaand_pad, timestamp=timestamp
        )
    except UrlFetchError:
        raise

    try:
        save_url_snapshot(
            html,
            bestaande.source_id,
            snapshots_dir=snapshots_dir,
        )
    except UrlFetchError:
        if oud_pad is not None:
            try:
                restore_old_snapshot(oud_pad, bestaand_pad)
            except UrlFetchError:
                pass
        raise

    # Catalogus bijwerken: status terug naar CONCEPT (kernregel 11).
    # Metadata wordt expliciet meegegeven: de wizard bepaalt de waarden.
    nieuwe_titel = _bepaal_titel(meta.url, title, meta)
    return import_service.replace_source(
        bestaande.source_id,
        title=nieuwe_titel,
        file_hash=None,
        original_filename=None,
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