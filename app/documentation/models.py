"""
================================================================================
Module:     app/documentation/models.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.6.0
Datum:      2026-10-08
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
  v1.3.0 (2026-10-03)  Multi-context basis toegevoegd: tool_keys bewaart
                        genormaliseerde koppelingen naast legacy tool_key.
  v1.4.0 (2026-10-03)  Overige multi-contextvelden toegevoegd voor component,
                        test, meetmethode, instrument en topics.
  v1.5.0 (2026-10-07)  is_user_import toegevoegd (fase 5D'.2c) zodat de
                        viewer kan weten of een document uit de
                        gebruikerscatalogus komt en dus bewerkbaar is.
                        Default False, backward-compatible.
  v1.6.0 (2026-10-08)  import_status toegevoegd (fase 5D'.2e) zodat de
                        viewer de levenscyclusstatus van een import kan
                        tonen in een Status-kolom. Default None,
                        backward-compatible.
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
    """Read-only metadata van één documentbron.

    Sinds v1.5.0 heeft elk document een ``is_user_import``-vlag:
      - False (default): het document komt uit de ingebouwde catalogus.
        De viewer toont het read-only en biedt geen Bewerken-knop.
      - True: het document komt uit de gebruikerscatalogus (een import).
        De viewer mag een Bewerken-knop tonen.

    Sinds v1.6.0 heeft elk document een optionele ``import_status``:
      - None (default): het document heeft geen importstatus (ingebouwd).
      - Een string (bv. "concept", "actief", "gearchiveerd"): de
        levenscyclusstatus van een import, bedoeld voor de Status-kolom.
    """

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
    tool_keys: tuple[str, ...] = ()
    component_types: tuple[str, ...] = ()
    test_keys: tuple[str, ...] = ()
    measurement_methods: tuple[str, ...] = ()
    instrument_keys: tuple[str, ...] = ()
    topics: tuple[str, ...] = ()
    is_user_import: bool = False
    import_status: str | None = None