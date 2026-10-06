"""
================================================================================
Module:     app/documentation/import_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-06
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


def default_catalog_path() -> Path:
    """Standaardpad van de gebruikerscatalogus.

    Bewust onder %LOCALAPPDATA%, op hetzelfde hoofdniveau als de bestaande
    SQLite-meetdatabase. Deze locatie valt buiten het standaard bereik van
    Windows Defender Controlled Folder Access en is de conventionele plaats
    voor applicatiegebonden data.
    """

    base = os.environ.get("LOCALAPPDATA")
    if not base:
        # Val terug op het gebruikersprofiel als LOCALAPPDATA ontbreekt
        # (bv. in een kale testomgeving). Geen crash, wel voorspelbaar pad.
        base = str(Path.home() / "AppData" / "Local")
    return Path(base) / "ElectronicsDiagnosticToolHub" / "documentation" / CATALOG_FILENAME


class ImportService:
    """Beheert de gebruikerscatalogus van geïmporteerde documentatiebronnen.

    De service is volledig GUI-onafhankelijk en doet geen netwerk- of
    PDF-operaties. Registratie betekent hier: metadata vastleggen. Het
    effectief lezen of downloaden van de bron gebeurt in latere deelfasen.
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

        # Atomair schrijven: naar een tijdelijk bestand in dezelfde map,
        # daarna os.replace. Voorkomt halve bestanden bij crash of
        # onderbroken schrijfactie.
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
            # Opruimen als het mislukt; laat originele bestand intact.
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise