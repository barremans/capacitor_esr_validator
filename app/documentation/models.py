"""
================================================================================
Module:     app/documentation/models.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.2.1
Datum:      2026-10-02
Auteur:     Bart Bossuyt

Doel:       Immutable modellen en vaste enumwaarden voor documentmetadata.

            Deze module bevat geen GUI-, database-, assessment- of
            extractielogica. De oorspronkelijke bronverwijzing blijft als
            metadata bewaard.

Wijzigingen:
  v1.0.0 (2026-10-02)  Eerste read-only documentatiemodel.
  v1.1.0 (2026-10-02)  Gestructureerde bronverwijzingen toegevoegd voor
                        fijnmazige provenance per handleiding.
  v1.2.0 (2026-10-03)  Optionele title_key toegevoegd voor vertaalbare
                        interne documenttitels; officiële brontitels blijven intact.
  v1.2.1 (2026-10-03)  Backward compatibility hersteld: title_key is echt
                        optioneel en heeft standaardwaarde None.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DocumentCategory(str, Enum):
    """Ondersteunde documentcategorieën van de centrale bibliotheek."""

    DATASHEET = "DATASHEET"
    APPLICATION_NOTE = "APPLICATION_NOTE"
    MEASUREMENT_TECHNIQUE = "MEASUREMENT_TECHNIQUE"
    MANUAL = "MANUAL"
    SAFETY = "SAFETY"
    REFERENCE_TABLE = "REFERENCE_TABLE"
    INTERNAL_INSTRUCTION = "INTERNAL_INSTRUCTION"


class DocumentSourceType(str, Enum):
    """Wijze waarop het oorspronkelijke document traceerbaar is."""

    FILE = "FILE"
    URL = "URL"
    FILE_AND_URL = "FILE_AND_URL"


@dataclass(frozen=True, slots=True)
class DocumentProvenanceRef:
    """Eén traceerbare bronverwijzing voor een document of documentsectie."""

    source_id: str
    source_title: str
    source_kind: str
    source_path: str | None
    source_url: str | None
    locator: str | None
    supports: tuple[str, ...]
    note: str | None


@dataclass(frozen=True, slots=True)
class DocumentMetadata:
    """Read-only metadata van één documentbron."""

    document_id: str
    title: str
    category: DocumentCategory
    source_type: DocumentSourceType
    source_path: str | None
    source_url: str | None
    tool_key: str | None
    manufacturer: str | None
    series: str | None
    part_number: str | None
    document_version: str | None
    document_date: str | None
    notes: str | None
    title_key: str | None = None
    provenance: tuple[DocumentProvenanceRef, ...] = ()
