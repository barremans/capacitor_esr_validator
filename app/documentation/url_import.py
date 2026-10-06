"""
================================================================================
Module:     app/documentation/url_import.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-06
Auteur:     Bart Bossuyt

Doel:       GUI-onafhankelijke orkestratielaag die url_fetch en
            ImportService samenbrengt voor één URL-import. Spiegel van
            pdf_import.py. Geen Qt, geen assessment.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie: import_url() met metadata → content
                       → registratie → snapshot. Registratie blijft behouden
                       bij snapshot-fout (optie B).
================================================================================
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Optional

from app.documentation.import_models import ImportResult
from app.documentation.import_service import ImportService
from app.documentation.url_fetch import (
    UrlFetchError,
    UrlMetadata,
    fetch_url_content,
    fetch_url_metadata,
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


def import_url(
    url: str,
    *,
    import_service: ImportService,
    title: Optional[str] = None,
    snapshots_dir: Optional[Path] = None,
    notes: Optional[str] = None,
) -> ImportResult:
    """Importeer één URL als nieuwe documentatiebron met lokale snapshot.

    Volgorde:
      1. Valideer de URL (via url_fetch).
      2. Haal metadata op (titel, description, og, taal).
      3. Haal de HTML-inhoud op.
      4. Registreer de bron als CONCEPT in de gebruikerscatalogus.
      5. Bewaar de HTML als snapshot in snapshots_dir/<source_id>.html.

    Als stap 5 faalt, blijft de registratie bestaan in CONCEPT-status met
    een foutnotitie in notes. De bron wordt niet stil verwijderd.

    Faalt met UrlFetchError bij netwerk- of opslagproblemen, en met
    ImportValidationError bij catalogusproblemen.
    """
    # Stap 1+2 — validatie en metadata
    meta = fetch_url_metadata(url)

    # Stap 3 — inhoud
    html = fetch_url_content(url)

    # Stap 4 — registratie
    effectieve_titel = _bepaal_titel(url, title, meta)
    registratie = import_service.register_url(
        title=effectieve_titel,
        source_url=url,
        notes=notes,
    )

    # Stap 5 — snapshot
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