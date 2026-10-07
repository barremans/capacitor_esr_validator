"""
================================================================================
Module:     app/documentation/import_models.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-07
Auteur:     Bart Bossuyt

Doel:       Immutable modellen en vaste enumwaarden voor de import van
            externe documentatiebronnen (PDF / URL). GUI-onafhankelijk.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie: ImportSourceType, ImportStatus,
                       ImportSource, ImportResult, ImportValidationError.
  v1.1.0 (2026-10-07)  DuplicateAction en DuplicateMatch toegevoegd voor
                       de bestaand-document-popup (fase 5D'.2a). Geen
                       wijziging aan bestaande modellen.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ImportValidationError(ValueError):
    """Ongeldige importmetadata of ongeldige statusovergang."""


class ImportSourceType(str, Enum):
    """Type van de geïmporteerde bron."""

    PDF = "pdf"
    URL = "url"


class ImportStatus(str, Enum):
    """Levenscyclus van een geïmporteerde bron.

    CONCEPT       Pas geregistreerd, nog niet gekoppeld aan viewer of
                  assessment.
    ACTIEF        Expliciet door de gebruiker bevestigd als bruikbaar.
    GEARCHIVEERD  Niet meer in standaardlijsten, maar blijft bewaard.
    """

    CONCEPT = "concept"
    ACTIEF = "actief"
    GEARCHIVEERD = "gearchiveerd"


class DuplicateAction(str, Enum):
    """Keuze van de gebruiker bij een exact bestaande bron.

    Wordt gebruikt door de wizard-popup (fase 5D'.2a) en door de
    orkestratielaag (pdf_import / url_import) om te bepalen wat er met
    een duplicate gebeurt.

    KEEP          Niets doen. Bestaande bron blijft ongewijzigd, geen
                  nieuwe registratie.
    NEW_VERSION   Nieuwe bron registreren; oude bron op GEARCHIVEERD.
    OVERWRITE     Bestaande bron bijwerken met hetzelfde source_id;
                  bronbestand wordt vervangen (oude versie bewaard als
                  .oud-<timestamp>).
    """

    KEEP = "keep"
    NEW_VERSION = "new_version"
    OVERWRITE = "overwrite"


# Toegelaten statusovergangen. Alle andere overgangen zijn ongeldig.
_ALLOWED_TRANSITIONS: dict[ImportStatus, frozenset[ImportStatus]] = {
    ImportStatus.CONCEPT: frozenset(
        {ImportStatus.ACTIEF, ImportStatus.GEARCHIVEERD}
    ),
    ImportStatus.ACTIEF: frozenset(
        {ImportStatus.CONCEPT, ImportStatus.GEARCHIVEERD}
    ),
    ImportStatus.GEARCHIVEERD: frozenset({ImportStatus.CONCEPT}),
}


def is_allowed_transition(
    huidige: ImportStatus, nieuwe: ImportStatus
) -> bool:
    """Controleer of een statusovergang is toegelaten."""

    if not isinstance(huidige, ImportStatus):
        raise ImportValidationError(
            f"huidige status moet ImportStatus zijn, kreeg {type(huidige)!r}"
        )
    if not isinstance(nieuwe, ImportStatus):
        raise ImportValidationError(
            f"nieuwe status moet ImportStatus zijn, kreeg {type(nieuwe)!r}"
        )
    if huidige == nieuwe:
        return False
    return nieuwe in _ALLOWED_TRANSITIONS[huidige]


@dataclass(frozen=True, slots=True)
class ImportSource:
    """Onveranderlijke metadata van één geïmporteerde bron.

    Een ImportSource beschrijft uitsluitend de bron en zijn provenance.
    Er wordt geen assessment, geen koppeling aan meetgegevens en geen
    interpretatie van de inhoud in dit model opgeslagen.
    """

    source_id: str
    source_type: ImportSourceType
    title: str
    imported_at: int
    imported_by: str
    status: ImportStatus
    original_filename: Optional[str] = None
    source_url: Optional[str] = None
    file_hash: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.source_type, ImportSourceType):
            raise ImportValidationError(
                "source_type moet ImportSourceType zijn"
            )
        if not isinstance(self.status, ImportStatus):
            raise ImportValidationError("status moet ImportStatus zijn")
        if not isinstance(self.source_id, str) or not self.source_id:
            raise ImportValidationError("source_id mag niet leeg zijn")
        if not isinstance(self.title, str) or not self.title.strip():
            raise ImportValidationError("title mag niet leeg zijn")
        if not isinstance(self.imported_at, int) or self.imported_at <= 0:
            raise ImportValidationError(
                "imported_at moet een positieve Unix-ms waarde zijn"
            )
        if not isinstance(self.imported_by, str) or not self.imported_by:
            raise ImportValidationError("imported_by mag niet leeg zijn")

        if self.source_type is ImportSourceType.PDF:
            if not self.original_filename:
                raise ImportValidationError(
                    "PDF-bron vereist original_filename"
                )
            if self.source_url:
                raise ImportValidationError(
                    "PDF-bron mag geen source_url hebben"
                )
        elif self.source_type is ImportSourceType.URL:
            if not self.source_url:
                raise ImportValidationError("URL-bron vereist source_url")
            if self.original_filename:
                raise ImportValidationError(
                    "URL-bron mag geen original_filename hebben"
                )

    def to_dict(self) -> dict:
        """Serialiseer naar een JSON-vriendelijk dict."""

        return {
            "source_id": self.source_id,
            "source_type": self.source_type.value,
            "title": self.title,
            "imported_at": self.imported_at,
            "imported_by": self.imported_by,
            "status": self.status.value,
            "original_filename": self.original_filename,
            "source_url": self.source_url,
            "file_hash": self.file_hash,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ImportSource":
        """Lees een ImportSource uit een JSON-dict met validatie."""

        if not isinstance(data, dict):
            raise ImportValidationError("bron-item moet een object zijn")

        try:
            source_type = ImportSourceType(data["source_type"])
        except (KeyError, ValueError) as exc:
            raise ImportValidationError(
                f"ongeldige of ontbrekende source_type: {exc}"
            ) from exc

        try:
            status = ImportStatus(data["status"])
        except (KeyError, ValueError) as exc:
            raise ImportValidationError(
                f"ongeldige of ontbrekende status: {exc}"
            ) from exc

        try:
            return cls(
                source_id=data["source_id"],
                source_type=source_type,
                title=data["title"],
                imported_at=data["imported_at"],
                imported_by=data["imported_by"],
                status=status,
                original_filename=data.get("original_filename"),
                source_url=data.get("source_url"),
                file_hash=data.get("file_hash"),
                notes=data.get("notes"),
            )
        except KeyError as exc:
            raise ImportValidationError(
                f"verplicht veld ontbreekt: {exc}"
            ) from exc


@dataclass(frozen=True, slots=True)
class ImportResult:
    """Resultaat van een registratie- of statusoperatie."""

    source: ImportSource
    changed: bool = True
    message: Optional[str] = None


@dataclass(frozen=True, slots=True)
class DuplicateMatch:
    """Beschrijving van een gevonden duplicate bij import.

    Wordt door de wizard gebruikt om de popup te tonen en door de
    orkestratielaag om de gekozen actie uit te voeren. Bevat de volledige
    bestaande ImportSource, zodat de GUI titel, status en importdatum kan
    tonen zonder extra queries.
    """

    bestaande: ImportSource
    match_type: str  # "file_hash" of "source_url"

    def __post_init__(self) -> None:
        if not isinstance(self.bestaande, ImportSource):
            raise ImportValidationError(
                "bestaande moet een ImportSource zijn"
            )
        if self.match_type not in ("file_hash", "source_url"):
            raise ImportValidationError(
                "match_type moet 'file_hash' of 'source_url' zijn"
            )