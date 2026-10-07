"""
================================================================================
Module:     app/documentation/duplicate_check.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.3
Datum:      2026-10-07
Auteur:     Bart Bossuyt

Doel:       GUI-onafhankelijke helper om te bepalen of een geïmporteerde
            bron al bestaat in de gebruikerscatalogus. Wordt gebruikt door
            de import-wizard (fase 5D'.2a) om de bestaand-document-popup
            te tonen. Geen Qt, geen netwerk, geen assessment.

Wijzigingen:
  v1.0.0 (2026-10-07)  Eerste versie.
  v1.0.1 (2026-10-07)  Validatie versoepeld voor lege strings.
  v1.0.2 (2026-10-07)  Onderscheid None vs "" bij validatie.
  v1.0.3 (2026-10-07)  _find_by_normalized_url kiest nu de beste match
                       (ACTIEF > CONCEPT > GEARCHIVEERD, dan meest
                       recente) in plaats van de eerste. Consistent met
                       ImportService.find_by_*.
================================================================================
"""

from __future__ import annotations

from typing import Optional
from urllib.parse import urlparse, urlunparse

from app.documentation.import_models import (
    DuplicateMatch,
    ImportSource,
    ImportStatus,
    ImportValidationError,
)
from app.documentation.import_service import ImportService


# Status-prioriteit voor duplicate-detectie: lager = beter.
_STATUS_PRIORITEIT: dict[ImportStatus, int] = {
    ImportStatus.ACTIEF: 0,
    ImportStatus.CONCEPT: 1,
    ImportStatus.GEARCHIVEERD: 2,
}


def normalize_url(url: str) -> str:
    """Lichte normalisatie van een URL voor duplicate-vergelijking."""

    if not isinstance(url, str):
        return ""
    schoon = url.strip()
    if not schoon:
        return ""

    try:
        parsed = urlparse(schoon)
    except ValueError:
        return schoon

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    pad = parsed.path.rstrip("/") if parsed.path != "/" else ""
    query = parsed.query

    genormaliseerd = urlunparse(
        (scheme, netloc, pad, parsed.params, query, "")
    )
    return genormaliseerd


def find_duplicate(
    import_service: ImportService,
    *,
    file_hash: Optional[str] = None,
    source_url: Optional[str] = None,
) -> Optional[DuplicateMatch]:
    """Zoek een bestaande bron die exact overeenkomt met deze import.

    Precies één van file_hash of source_url moet een niet-lege waarde
    hebben. Retourneert een DuplicateMatch met de BESTE match (ACTIEF >
    CONCEPT > GEARCHIVEERD, dan meest recente) of None.

    Faalt met ImportValidationError als beide parameters None zijn of als
    beide een niet-lege waarde hebben.
    """

    if not isinstance(import_service, ImportService):
        raise ImportValidationError(
            "import_service moet een ImportService zijn"
        )

    if file_hash is None and source_url is None:
        raise ImportValidationError(
            "geef precies één van file_hash of source_url mee"
        )

    heeft_hash = bool(file_hash and str(file_hash).strip())
    heeft_url = bool(source_url and str(source_url).strip())

    if heeft_hash and heeft_url:
        raise ImportValidationError(
            "geef precies één van file_hash of source_url mee"
        )

    if not heeft_hash and not heeft_url:
        return None

    if heeft_hash:
        bestaande: Optional[ImportSource] = import_service.find_by_file_hash(
            str(file_hash)
        )
        if bestaande is None:
            return None
        return DuplicateMatch(bestaande=bestaande, match_type="file_hash")

    genormaliseerd = normalize_url(str(source_url))
    if not genormaliseerd:
        return None

    bestaande = _find_by_normalized_url(import_service, genormaliseerd)
    if bestaande is None:
        return None
    return DuplicateMatch(bestaande=bestaande, match_type="source_url")


def _find_by_normalized_url(
    import_service: ImportService,
    genormaliseerde_url: str,
) -> Optional[ImportSource]:
    """Interne helper: kies de beste match op genormaliseerde URL.

    Beste = ACTIEF > CONCEPT > GEARCHIVEERD, dan hoogste imported_at.
    """

    kandidaten: list[ImportSource] = []
    for source in import_service.list_sources():
        if not source.source_url:
            continue
        if normalize_url(source.source_url) == genormaliseerde_url:
            kandidaten.append(source)

    if not kandidaten:
        return None

    return min(
        kandidaten,
        key=lambda s: (
            _STATUS_PRIORITEIT.get(s.status, 99),
            -s.imported_at,
        ),
    )