"""
================================================================================
Module:     app/documentation/models.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-02
Auteur:     Bart Bossuyt

Doel:       Immutable modellen en vaste enumwaarden voor documentmetadata.

            Deze module bevat geen GUI-, database-, assessment- of
            extractielogica. De oorspronkelijke bronverwijzing blijft als
            metadata bewaard.

Wijzigingen:
  v1.0.0 (2026-10-02)  Eerste read-only documentatiemodel.
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
