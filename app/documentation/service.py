"""
================================================================================
Module:     app/documentation/service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-02
Auteur:     Bart Bossuyt

Doel:       Read-only service voor de centrale documentatiebibliotheek.

            Laadt en valideert een versieerbare JSON-catalogus en ondersteunt
            zoeken en filteren. Schrijft geen bestanden, gebruikt geen SQLite
            en bevat geen assessment-, import- of AI-logica.

Wijzigingen:
  v1.0.0 (2026-10-02)  Eerste catalogusloader, validatie en zoek/filter-API.
================================================================================
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .models import DocumentCategory, DocumentMetadata, DocumentSourceType


CATALOG_SCHEMA_VERSION = 1
DEFAULT_CATALOG_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "documentation"
    / "catalog.json"
)


class DocumentationError(RuntimeError):
    """Basisklasse voor fouten in de read-only documentatiebibliotheek."""


class DocumentationValidationError(DocumentationError):
    """De documentcatalogus of documentmetadata is structureel ongeldig."""


class DocumentationService:
    """Read-only toegang tot versieerbare documentmetadata."""

    def __init__(self, catalog_path: Path | str | None = None) -> None:
        self.catalog_path = (
            Path(catalog_path) if catalog_path is not None else DEFAULT_CATALOG_PATH
        )

    def load_documents(self) -> list[DocumentMetadata]:
        """Laad en valideer alle documenten uit de catalogus."""
        try:
            raw_text = self.catalog_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise DocumentationError(
                f"Documentcatalogus kon niet worden gelezen: {self.catalog_path}"
            ) from exc

        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise DocumentationValidationError(
                "Documentcatalogus bevat ongeldige JSON."
            ) from exc

        if not isinstance(payload, dict):
            raise DocumentationValidationError(
                "Documentcatalogus moet een JSON-object zijn."
            )

        schema_version = payload.get("schema_version")
        if schema_version != CATALOG_SCHEMA_VERSION:
            raise DocumentationValidationError(
                "Niet-ondersteunde schema_version in documentcatalogus: "
                f"{schema_version!r}."
            )

        data_version = payload.get("data_version")
        if not isinstance(data_version, str) or not data_version.strip():
            raise DocumentationValidationError(
                "Documentcatalogus mist een geldige data_version."
            )

        raw_documents = payload.get("documents")
        if not isinstance(raw_documents, list):
            raise DocumentationValidationError(
                "Documentcatalogusveld 'documents' moet een lijst zijn."
            )

        documents: list[DocumentMetadata] = []
        seen_ids: set[str] = set()

        for index, raw_document in enumerate(raw_documents):
            document = self._document_from_mapping(raw_document, index=index)
            if document.document_id in seen_ids:
                raise DocumentationValidationError(
                    f"Dubbele document_id in catalogus: {document.document_id}."
                )
            seen_ids.add(document.document_id)
            documents.append(document)

        return documents

    def list_documents(
        self,
        *,
        search_text: str | None = None,
        category: DocumentCategory | str | None = None,
        tool_key: str | None = None,
    ) -> list[DocumentMetadata]:
        """Geef documenten terug met optionele vrije-tekst- en metadatafilters."""
        documents = self.load_documents()

        selected_category = self._category_optional(category)
        selected_tool_key = self._normalize_tool_key_optional(tool_key)
        needle = (search_text or "").strip().casefold()

        result: list[DocumentMetadata] = []
        for document in documents:
            if selected_category is not None and document.category != selected_category:
                continue

            if selected_tool_key is not None:
                document_tool = self._normalize_tool_key_optional(document.tool_key)
                if document_tool != selected_tool_key:
                    continue

            if needle and needle not in self._search_blob(document):
                continue

            result.append(document)

        return sorted(
            result,
            key=lambda item: (
                item.title.casefold(),
                item.document_id.casefold(),
            ),
        )

    @staticmethod
    def _search_blob(document: DocumentMetadata) -> str:
        values = (
            document.document_id,
            document.title,
            document.category.value,
            document.source_type.value,
            document.source_path,
            document.source_url,
            document.tool_key,
            document.manufacturer,
            document.series,
            document.part_number,
            document.document_version,
            document.document_date,
            document.notes,
        )
        return "\n".join(
            value.casefold()
            for value in values
            if isinstance(value, str) and value
        )

    @classmethod
    def _document_from_mapping(
        cls,
        data: Any,
        *,
        index: int,
    ) -> DocumentMetadata:
        if not isinstance(data, Mapping):
            raise DocumentationValidationError(
                f"Document op index {index} moet een object zijn."
            )

        allowed = {
            "document_id",
            "title",
            "category",
            "source_type",
            "source_path",
            "source_url",
            "tool_key",
            "manufacturer",
            "series",
            "part_number",
            "document_version",
            "document_date",
            "notes",
        }
        unknown = set(data) - allowed
        if unknown:
            raise DocumentationValidationError(
                "Onbekende documentvelden op index "
                f"{index}: {', '.join(sorted(unknown))}."
            )

        document_id = cls._required_text(data, "document_id", index=index)
        title = cls._required_text(data, "title", index=index)

        try:
            category = DocumentCategory(
                cls._required_text(data, "category", index=index).upper()
            )
        except ValueError as exc:
            raise DocumentationValidationError(
                f"Ongeldige documentcategorie op index {index}."
            ) from exc

        try:
            source_type = DocumentSourceType(
                cls._required_text(data, "source_type", index=index).upper()
            )
        except ValueError as exc:
            raise DocumentationValidationError(
                f"Ongeldig source_type op index {index}."
            ) from exc

        source_path = cls._optional_text(data.get("source_path"))
        source_url = cls._optional_text(data.get("source_url"))

        if source_type is DocumentSourceType.FILE and not source_path:
            raise DocumentationValidationError(
                f"Document {document_id} vereist source_path."
            )
        if source_type is DocumentSourceType.URL and not source_url:
            raise DocumentationValidationError(
                f"Document {document_id} vereist source_url."
            )
        if source_type is DocumentSourceType.FILE_AND_URL and (
            not source_path or not source_url
        ):
            raise DocumentationValidationError(
                f"Document {document_id} vereist source_path en source_url."
            )

        return DocumentMetadata(
            document_id=document_id,
            title=title,
            category=category,
            source_type=source_type,
            source_path=source_path,
            source_url=source_url,
            tool_key=cls._normalize_tool_key_optional(data.get("tool_key")),
            manufacturer=cls._optional_text(data.get("manufacturer")),
            series=cls._optional_text(data.get("series")),
            part_number=cls._optional_text(data.get("part_number")),
            document_version=cls._optional_text(data.get("document_version")),
            document_date=cls._optional_text(data.get("document_date")),
            notes=cls._optional_text(data.get("notes")),
        )

    @staticmethod
    def _required_text(
        data: Mapping[str, Any],
        key: str,
        *,
        index: int,
    ) -> str:
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            raise DocumentationValidationError(
                f"Document op index {index} mist geldige tekst voor '{key}'."
            )
        return value.strip()

    @staticmethod
    def _optional_text(value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise DocumentationValidationError(
                "Optionele documentmetadata moet tekst of null zijn."
            )
        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _normalize_tool_key_optional(value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise DocumentationValidationError(
                "tool_key moet tekst of null zijn."
            )
        normalized = value.strip().upper()
        if not normalized:
            return None
        if any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_" for ch in normalized):
            raise DocumentationValidationError(
                "tool_key mag alleen A-Z, 0-9 en underscore bevatten."
            )
        return normalized

    @staticmethod
    def _category_optional(
        value: DocumentCategory | str | None,
    ) -> DocumentCategory | None:
        if value is None:
            return None
        if isinstance(value, DocumentCategory):
            return value
        try:
            return DocumentCategory(str(value).strip().upper())
        except ValueError as exc:
            raise DocumentationValidationError(
                f"Ongeldige documentcategorie-filter: {value!r}."
            ) from exc
