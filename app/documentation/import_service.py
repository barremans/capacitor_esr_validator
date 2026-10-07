"""
================================================================================
Module:     app/documentation/import_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.1
Datum:      2026-10-07
Auteur:     Bart Bossuyt

Doel:       GUI-onafhankelijke service voor het registreren en beheren van
            geïmporteerde documentatiebronnen (PDF / URL). Schrijft naar een
            aparte gebruikerscatalogus in %LOCALAPPDATA%, los van de
            ingebouwde read-only catalogus. Geen Qt, geen netwerk, geen
            PDF-parsing.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie: register_pdf, register_url,
                       set_status, archive, revoke, list_sources, get,
                       JSON-persistentie met schema_version=1.
  v1.1.0 (2026-10-07)  Duplicate-detectie en vervanging toegevoegd:
                       find_by_file_hash, find_by_source_url,
                       replace_source.
  v1.1.1 (2026-10-07)  find_by_file_hash en find_by_source_url kiezen nu
                       de BESTE match in plaats van de eerste: status-
                       prioriteit ACTIEF > CONCEPT > GEARCHIVEERD, dan
                       meest recente imported_at. Lost bug op waarbij
                       Overschrijven de gearchiveerde bron koos in plaats
                       van de actieve/concept-bron.
================================================================================
"""

from __future__ import annotations

import getpass
import json
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Iterable, Optional

from app.documentation.import_models import (
    ImportResult,
    ImportSource,
    ImportSourceType,
    ImportStatus,
    ImportValidationError,
    is_allowed_transition,
)


CATALOG_SCHEMA_VERSION = 1
CATALOG_FILENAME = "imported_catalog.json"


# Status-prioriteit voor duplicate-detectie: lager = beter.
_STATUS_PRIORITEIT: dict[ImportStatus, int] = {
    ImportStatus.ACTIEF: 0,
    ImportStatus.CONCEPT: 1,
    ImportStatus.GEARCHIVEERD: 2,
}


def default_catalog_path() -> Path:
    """Standaardpad van de gebruikerscatalogus.

    Bewust onder %LOCALAPPDATA%, op hetzelfde hoofdniveau als de bestaande
    SQLite-meetdatabase. Deze locatie valt buiten het standaard bereik van
    Windows Defender Controlled Folder Access en is de conventionele plaats
    voor applicatiegebonden data.
    """

    base = os.environ.get("LOCALAPPDATA")
    if not base:
        base = str(Path.home() / "AppData" / "Local")
    return Path(base) / "ElectronicsDiagnosticToolHub" / "documentation" / CATALOG_FILENAME


class ImportService:
    """Beheert de gebruikerscatalogus van geïmporteerde documentatiebronnen.

    De service is volledig GUI-onafhankelijk en doet geen netwerk- of
    PDF-operaties. Registratie betekent hier: metadata vastleggen.
    """

    def __init__(
        self,
        catalog_path: Optional[Path] = None,
        imported_by: Optional[str] = None,
    ) -> None:
        self._catalog_path = Path(catalog_path) if catalog_path else default_catalog_path()
        self._imported_by = imported_by or self._default_user()

    # ------------------------------------------------------------------ publiek

    @property
    def catalog_path(self) -> Path:
        return self._catalog_path

    def register_pdf(
        self,
        *,
        title: str,
        original_filename: str,
        file_hash: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ImportResult:
        """Registreer een nieuwe PDF-bron in CONCEPT-status."""

        source = ImportSource(
            source_id=self._new_source_id(),
            source_type=ImportSourceType.PDF,
            title=title,
            imported_at=self._now_ms(),
            imported_by=self._imported_by,
            status=ImportStatus.CONCEPT,
            original_filename=original_filename,
            source_url=None,
            file_hash=file_hash,
            notes=notes,
        )
        self._append(source)
        return ImportResult(source=source, changed=True)

    def register_url(
        self,
        *,
        title: str,
        source_url: str,
        notes: Optional[str] = None,
    ) -> ImportResult:
        """Registreer een nieuwe URL-bron in CONCEPT-status."""

        source = ImportSource(
            source_id=self._new_source_id(),
            source_type=ImportSourceType.URL,
            title=title,
            imported_at=self._now_ms(),
            imported_by=self._imported_by,
            status=ImportStatus.CONCEPT,
            original_filename=None,
            source_url=source_url,
            file_hash=None,
            notes=notes,
        )
        self._append(source)
        return ImportResult(source=source, changed=True)

    def get(self, source_id: str) -> ImportSource:
        """Lees één bron. Faalt met ImportValidationError als die niet bestaat."""

        for source in self._read_all():
            if source.source_id == source_id:
                return source
        raise ImportValidationError(f"onbekende source_id: {source_id}")

    def list_sources(
        self, status: Optional[ImportStatus] = None
    ) -> list[ImportSource]:
        """Lijst alle bronnen, optioneel gefilterd op status."""

        items = list(self._read_all())
        if status is not None:
            if not isinstance(status, ImportStatus):
                raise ImportValidationError("status moet ImportStatus zijn")
            items = [s for s in items if s.status is status]
        return items

    def find_by_file_hash(self, file_hash: str) -> Optional[ImportSource]:
        """Zoek de BESTE bron met deze SHA-256 (case-insensitive).

        Beste = hoogste status-prioriteit (ACTIEF > CONCEPT > GEARCHIVEERD),
        en bij gelijke status de meest recente imported_at.

        Doorzoekt alle statussen. Retourneert None als er geen match is of
        als file_hash leeg is.
        """

        if not isinstance(file_hash, str) or not file_hash.strip():
            return None
        gezocht = file_hash.strip().lower()

        kandidaten: list[ImportSource] = [
            s
            for s in self._read_all()
            if s.file_hash and s.file_hash.lower() == gezocht
        ]
        return self._beste_match(kandidaten)

    def find_by_source_url(self, source_url: str) -> Optional[ImportSource]:
        """Zoek de BESTE bron met deze URL.

        Vergelijkt na lichte normalisatie: strip en trailing slash weg.
        Beste = hoogste status-prioriteit, dan meest recente imported_at.
        Doorzoekt alle statussen. Retourneert None als er geen match is.
        """

        if not isinstance(source_url, str) or not source_url.strip():
            return None
        gezocht = source_url.strip().rstrip("/")

        kandidaten: list[ImportSource] = [
            s
            for s in self._read_all()
            if s.source_url and s.source_url.strip().rstrip("/") == gezocht
        ]
        return self._beste_match(kandidaten)

    @staticmethod
    def _beste_match(
        kandidaten: list[ImportSource],
    ) -> Optional[ImportSource]:
        """Kies de beste match: status-prioriteit, dan meest recente.

        Status-prioriteit: ACTIEF > CONCEPT > GEARCHIVEERD.
        Bij gelijke status: hoogste imported_at (meest recente).
        """
        if not kandidaten:
            return None

        return min(
            kandidaten,
            key=lambda s: (
                _STATUS_PRIORITEIT.get(s.status, 99),
                -s.imported_at,
            ),
        )

    def replace_source(
        self,
        source_id: str,
        *,
        title: str,
        file_hash: Optional[str],
        original_filename: Optional[str],
        notes: Optional[str],
        imported_at: Optional[int] = None,
        status: Optional[ImportStatus] = None,
    ) -> ImportResult:
        """Vervang alle wijzigbare velden van één bestaande bron.

        Gebruikt door 'Overschrijven' in de wizard (fase 5D'.2a). Het
        source_id blijft ongewijzigd, net als source_type en imported_by.
        imported_at en status worden gezet zoals meegegeven; als ze None
        zijn, blijven de bestaande waarden behouden.

        Er wordt GEEN is_allowed_transition-check gedaan: 'Overschrijven'
        is een expliciete gebruikersactie.
        """

        items = list(self._read_all())
        for idx, source in enumerate(items):
            if source.source_id != source_id:
                continue

            nieuwe_imported_at = (
                imported_at if imported_at is not None else source.imported_at
            )
            nieuwe_status = status if status is not None else source.status

            vervangen = ImportSource(
                source_id=source.source_id,
                source_type=source.source_type,
                title=title,
                imported_at=nieuwe_imported_at,
                imported_by=source.imported_by,
                status=nieuwe_status,
                original_filename=original_filename,
                source_url=source.source_url,
                file_hash=file_hash,
                notes=notes,
            )
            items[idx] = vervangen
            self._write_all(items)
            return ImportResult(source=vervangen, changed=True)

        raise ImportValidationError(f"onbekende source_id: {source_id}")

    def set_status(
        self, source_id: str, nieuwe_status: ImportStatus
    ) -> ImportResult:
        """Wijzig de status volgens de toegelaten overgangen."""

        items = list(self._read_all())
        for idx, source in enumerate(items):
            if source.source_id != source_id:
                continue
            if not is_allowed_transition(source.status, nieuwe_status):
                raise ImportValidationError(
                    f"ongeldige overgang {source.status.value} -> "
                    f"{nieuwe_status.value}"
                )
            updated = self._replace_status(source, nieuwe_status)
            items[idx] = updated
            self._write_all(items)
            return ImportResult(source=updated, changed=True)
        raise ImportValidationError(f"onbekende source_id: {source_id}")

    def archive(self, source_id: str) -> ImportResult:
        """Archiveer een bron. De bron blijft bewaard."""

        return self.set_status(source_id, ImportStatus.GEARCHIVEERD)

    def revoke(self, source_id: str) -> ImportResult:
        """Trek een bron terug naar CONCEPT. De bron wordt niet verwijderd."""

        return self.set_status(source_id, ImportStatus.CONCEPT)

    # ----------------------------------------------------------------- intern

    @staticmethod
    def _default_user() -> str:
        try:
            return getpass.getuser() or "onbekend"
        except Exception:
            return "onbekend"

    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)

    @staticmethod
    def _new_source_id() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def _replace_status(
        source: ImportSource, nieuwe_status: ImportStatus
    ) -> ImportSource:
        return ImportSource(
            source_id=source.source_id,
            source_type=source.source_type,
            title=source.title,
            imported_at=source.imported_at,
            imported_by=source.imported_by,
            status=nieuwe_status,
            original_filename=source.original_filename,
            source_url=source.source_url,
            file_hash=source.file_hash,
            notes=source.notes,
        )

    def _read_all(self) -> Iterable[ImportSource]:
        if not self._catalog_path.exists():
            return []

        try:
            raw = self._catalog_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ImportValidationError(
                f"kan catalogus niet lezen: {exc}"
            ) from exc

        if not raw.strip():
            return []

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ImportValidationError(
                f"catalogus is geen geldige JSON: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise ImportValidationError("catalogus moet een JSON-object zijn")

        schema_version = data.get("schema_version")
        if schema_version != CATALOG_SCHEMA_VERSION:
            raise ImportValidationError(
                f"ongeveer schema_version: verwacht "
                f"{CATALOG_SCHEMA_VERSION}, kreeg {schema_version!r}"
            )

        raw_sources = data.get("sources", [])
        if not isinstance(raw_sources, list):
            raise ImportValidationError("'sources' moet een lijst zijn")

        return [ImportSource.from_dict(item) for item in raw_sources]

    def _append(self, source: ImportSource) -> None:
        items = list(self._read_all())
        items.append(source)
        self._write_all(items)

    def _write_all(self, sources: list[ImportSource]) -> None:
        payload = {
            "schema_version": CATALOG_SCHEMA_VERSION,
            "sources": [s.to_dict() for s in sources],
        }

        self._catalog_path.parent.mkdir(parents=True, exist_ok=True)

        fd, tmp_name = tempfile.mkstemp(
            prefix=".imported_catalog.",
            suffix=".tmp",
            dir=str(self._catalog_path.parent),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self._catalog_path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise