"""
================================================================================
Module:     app/documentation/service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.6.0
Datum:      2026-10-03
Auteur:     Bart Bossuyt

Doel:       Read-only service voor de centrale documentatiebibliotheek.

            Laadt en valideert een versieerbare JSON-catalogus en ondersteunt
            zoeken en filteren. Schrijft geen bestanden, gebruikt geen SQLite
            en bevat geen assessment-, import- of AI-logica.

Wijzigingen:
  v1.0.0 (2026-10-02)  Eerste catalogusloader, validatie en zoek/filter-API.
  v1.1.0 (2026-10-02)  Veilige read-only bronresolutie, documentlookup en
                        tekstinhoud lezen voor interne handleidingen toegevoegd.
  v1.2.0 (2026-10-02)  Gestructureerde provenance per documentbron toegevoegd.
  v1.3.0 (2026-10-03)  Optionele title_key voor vertaalbare interne titels
                        gevalideerd en geladen; title blijft officiële fallback.
  v1.4.0 (2026-10-03)  Meertalige interne Markdown-inhoud toegevoegd met
                        taalvariantresolutie en fallback naar nl_NL.
  v1.5.0 (2026-10-03)  Backward-compatible multi-tool metadata toegevoegd:
                        tool_key en tool_keys worden centraal genormaliseerd.
  v1.6.0 (2026-10-03)  Multi-contextmetadata uitgebreid met component_types,
                        test_keys, measurement_methods, instrument_keys en topics.
================================================================================
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .models import (
    DocumentCategory,
    DocumentMetadata,
    DocumentProvenanceRef,
    DocumentSourceType,
)


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
        component_type: str | None = None,
        test_key: str | None = None,
        measurement_method: str | None = None,
        instrument_key: str | None = None,
        topic: str | None = None,
    ) -> list[DocumentMetadata]:
        """Geef documenten terug met optionele vrije-tekst- en metadatafilters."""
        documents = self.load_documents()

        selected_category = self._category_optional(category)
        selected_tool_key = self._normalize_tool_key_optional(tool_key)
        selected_component_type = self._normalize_context_key_optional(
            component_type,
            field_name="component_type",
        )
        selected_test_key = self._normalize_context_key_optional(
            test_key,
            field_name="test_key",
        )
        selected_measurement_method = self._normalize_context_key_optional(
            measurement_method,
            field_name="measurement_method",
        )
        selected_instrument_key = self._normalize_context_key_optional(
            instrument_key,
            field_name="instrument_key",
        )
        selected_topic = self._normalize_topic_optional(topic)
        needle = (search_text or "").strip().casefold()

        result: list[DocumentMetadata] = []
        for document in documents:
            if selected_category is not None and document.category != selected_category:
                continue

            if selected_tool_key is not None:
                if selected_tool_key not in document.tool_keys:
                    continue

            if (
                selected_component_type is not None
                and selected_component_type not in document.component_types
            ):
                continue

            if selected_test_key is not None and selected_test_key not in document.test_keys:
                continue

            if (
                selected_measurement_method is not None
                and selected_measurement_method not in document.measurement_methods
            ):
                continue

            if (
                selected_instrument_key is not None
                and selected_instrument_key not in document.instrument_keys
            ):
                continue

            if selected_topic is not None and selected_topic not in document.topics:
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

    def get_document(self, document_id: str) -> DocumentMetadata:
        """Zoek één document exact op stabiele document_id."""
        normalized_id = document_id.strip() if isinstance(document_id, str) else ""
        if not normalized_id:
            raise DocumentationValidationError(
                "document_id moet niet-lege tekst zijn."
            )

        for document in self.load_documents():
            if document.document_id == normalized_id:
                return document

        raise DocumentationError(
            f"Document niet gevonden in catalogus: {normalized_id}."
        )

    def read_document_text(
        self,
        document_id: str,
        *,
        language: str | None = None,
    ) -> str:
        """Lees een lokale UTF-8 tekstbron met taalvariant-fallback.

        Voor interne Markdown onder ``internal/<taalcode>/`` wordt eerst de
        gevraagde taal geprobeerd, daarna ``nl_NL``. Bestaande cataloguspaden
        buiten die structuur blijven backward-compatible en worden ongewijzigd
        gelezen. Externe PDF-bronnen vallen buiten deze tekstreader.
        """
        document = self.get_document(document_id)

        if document.source_type not in {
            DocumentSourceType.FILE,
            DocumentSourceType.FILE_AND_URL,
        } or not document.source_path:
            raise DocumentationError(
                f"Document {document.document_id} heeft geen lokale tekstbron."
            )

        source_path = Path(document.source_path)
        if source_path.is_absolute():
            raise DocumentationValidationError(
                f"Document {document.document_id} gebruikt een absoluut source_path."
            )

        if source_path.suffix.lower() not in {".md", ".txt"}:
            raise DocumentationError(
                f"Document {document.document_id} is geen leesbare tekstbron."
            )

        catalog_root = self.catalog_path.resolve().parent
        candidates = self._language_candidates(source_path, language=language)

        last_path: Path | None = None
        for candidate in candidates:
            resolved_source = (catalog_root / candidate).resolve()
            last_path = resolved_source

            try:
                resolved_source.relative_to(catalog_root)
            except ValueError as exc:
                raise DocumentationValidationError(
                    f"Document {document.document_id} verwijst buiten de documentatiemap."
                ) from exc

            if not resolved_source.is_file():
                continue

            try:
                return resolved_source.read_text(encoding="utf-8")
            except OSError as exc:
                raise DocumentationError(
                    f"Documentbron kon niet worden gelezen: {resolved_source}"
                ) from exc

        raise DocumentationError(
            f"Documentbron kon niet worden gelezen: {last_path or source_path}"
        )

    @staticmethod
    def _language_candidates(
        source_path: Path,
        *,
        language: str | None,
    ) -> tuple[Path, ...]:
        """Bepaal kandidaatpaden voor interne taalvarianten.

        Alleen paden met vorm ``internal/<taalcode>/...`` worden vertaald.
        Daardoor blijven bestaande en externe catalogusrecords onaangeroerd.
        """
        parts = source_path.parts
        if len(parts) < 3 or parts[0] != "internal":
            return (source_path,)

        relative_tail = Path(*parts[2:])
        requested = language.strip() if isinstance(language, str) else ""

        candidates: list[Path] = []
        if requested:
            candidates.append(Path("internal") / requested / relative_tail)

        fallback = Path("internal") / "nl_NL" / relative_tail
        if fallback not in candidates:
            candidates.append(fallback)

        original = source_path
        if original not in candidates:
            candidates.append(original)

        return tuple(candidates)

    @staticmethod
    def _search_blob(document: DocumentMetadata) -> str:
        values = (
            document.document_id,
            document.title,
            document.title_key,
            document.category.value,
            document.source_type.value,
            document.source_path,
            document.source_url,
            document.tool_key,
            *document.tool_keys,
            *document.component_types,
            *document.test_keys,
            *document.measurement_methods,
            *document.instrument_keys,
            *document.topics,
            document.manufacturer,
            document.series,
            document.part_number,
            document.document_version,
            document.document_date,
            document.notes,
            *(
                value
                for ref in document.provenance
                for value in (
                    ref.source_id,
                    ref.source_title,
                    ref.source_kind,
                    ref.source_path,
                    ref.source_url,
                    ref.locator,
                    ref.note,
                    *ref.supports,
                )
            ),
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
            "title_key",
            "category",
            "source_type",
            "source_path",
            "source_url",
            "tool_key",
            "tool_keys",
            "component_types",
            "test_keys",
            "measurement_methods",
            "instrument_keys",
            "topics",
            "manufacturer",
            "series",
            "part_number",
            "document_version",
            "document_date",
            "notes",
            "provenance",
        }
        unknown = set(data) - allowed
        if unknown:
            raise DocumentationValidationError(
                "Onbekende documentvelden op index "
                f"{index}: {', '.join(sorted(unknown))}."
            )

        document_id = cls._required_text(data, "document_id", index=index)
        title = cls._required_text(data, "title", index=index)
        title_key = cls._optional_text(data.get("title_key"))

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

        legacy_tool_key = cls._normalize_tool_key_optional(data.get("tool_key"))
        tool_keys = cls._normalize_tool_keys(
            data.get("tool_keys"),
            legacy_tool_key=legacy_tool_key,
        )
        # Backward-compatible alias: bestaande GUI/code kan tool_key blijven lezen.
        effective_tool_key = legacy_tool_key or (tool_keys[0] if tool_keys else None)

        component_types = cls._normalize_context_keys(
            data.get("component_types"),
            field_name="component_types",
        )
        test_keys = cls._normalize_context_keys(
            data.get("test_keys"),
            field_name="test_keys",
        )
        measurement_methods = cls._normalize_context_keys(
            data.get("measurement_methods"),
            field_name="measurement_methods",
        )
        instrument_keys = cls._normalize_context_keys(
            data.get("instrument_keys"),
            field_name="instrument_keys",
        )
        topics = cls._normalize_topics(data.get("topics"))

        return DocumentMetadata(
            document_id=document_id,
            title=title,
            title_key=title_key,
            category=category,
            source_type=source_type,
            source_path=source_path,
            source_url=source_url,
            tool_key=effective_tool_key,
            manufacturer=cls._optional_text(data.get("manufacturer")),
            series=cls._optional_text(data.get("series")),
            part_number=cls._optional_text(data.get("part_number")),
            document_version=cls._optional_text(data.get("document_version")),
            document_date=cls._optional_text(data.get("document_date")),
            notes=cls._optional_text(data.get("notes")),
            provenance=cls._provenance_refs(data.get("provenance"), index=index),
            tool_keys=tool_keys,
            component_types=component_types,
            test_keys=test_keys,
            measurement_methods=measurement_methods,
            instrument_keys=instrument_keys,
            topics=topics,
        )

    @classmethod
    def _provenance_refs(
        cls,
        value: Any,
        *,
        index: int,
    ) -> tuple[DocumentProvenanceRef, ...]:
        if value is None:
            return ()
        if not isinstance(value, list):
            raise DocumentationValidationError(
                f"provenance op documentindex {index} moet een lijst zijn."
            )

        refs: list[DocumentProvenanceRef] = []
        seen_ids: set[str] = set()
        allowed = {
            "source_id",
            "source_title",
            "source_kind",
            "source_path",
            "source_url",
            "locator",
            "supports",
            "note",
        }

        for ref_index, item in enumerate(value):
            if not isinstance(item, Mapping):
                raise DocumentationValidationError(
                    f"provenance-item {ref_index} op documentindex {index} moet een object zijn."
                )

            unknown = set(item) - allowed
            if unknown:
                raise DocumentationValidationError(
                    "Onbekende provenancevelden op documentindex "
                    f"{index}: {', '.join(sorted(unknown))}."
                )

            source_id = cls._required_text(item, "source_id", index=index)
            if source_id in seen_ids:
                raise DocumentationValidationError(
                    f"Dubbele provenance source_id '{source_id}' op documentindex {index}."
                )
            seen_ids.add(source_id)

            source_title = cls._required_text(item, "source_title", index=index)
            source_kind = cls._required_text(item, "source_kind", index=index).upper()
            source_path = cls._optional_text(item.get("source_path"))
            source_url = cls._optional_text(item.get("source_url"))
            locator = cls._optional_text(item.get("locator"))
            note = cls._optional_text(item.get("note"))

            supports_raw = item.get("supports", [])
            if not isinstance(supports_raw, list) or not all(
                isinstance(tag, str) and tag.strip() for tag in supports_raw
            ):
                raise DocumentationValidationError(
                    f"supports voor provenance '{source_id}' moet een lijst niet-lege teksten zijn."
                )
            supports = tuple(tag.strip() for tag in supports_raw)

            if source_kind == "FILE" and not source_path:
                raise DocumentationValidationError(
                    f"Provenancebron '{source_id}' vereist source_path."
                )
            if source_kind == "URL" and not source_url:
                raise DocumentationValidationError(
                    f"Provenancebron '{source_id}' vereist source_url."
                )
            if source_kind == "FILE_AND_URL" and (not source_path or not source_url):
                raise DocumentationValidationError(
                    f"Provenancebron '{source_id}' vereist source_path en source_url."
                )

            refs.append(
                DocumentProvenanceRef(
                    source_id=source_id,
                    source_title=source_title,
                    source_kind=source_kind,
                    source_path=source_path,
                    source_url=source_url,
                    locator=locator,
                    supports=supports,
                    note=note,
                )
            )

        return tuple(refs)

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

    @classmethod
    def _normalize_tool_keys(
        cls,
        value: Any,
        *,
        legacy_tool_key: str | None,
    ) -> tuple[str, ...]:
        """Normaliseer legacy tool_key en nieuw tool_keys naar één unieke tuple."""
        if value is None:
            raw_values: list[Any] = []
        elif isinstance(value, list):
            raw_values = value
        else:
            raise DocumentationValidationError(
                "tool_keys moet een lijst van niet-lege teksten zijn."
            )

        normalized: list[str] = []
        seen: set[str] = set()

        if legacy_tool_key is not None:
            normalized.append(legacy_tool_key)
            seen.add(legacy_tool_key)

        for raw in raw_values:
            key = cls._normalize_tool_key_optional(raw)
            if key is None:
                raise DocumentationValidationError(
                    "tool_keys mag geen lege of null-waarden bevatten."
                )
            if key not in seen:
                normalized.append(key)
                seen.add(key)

        return tuple(normalized)

    @classmethod
    def _normalize_context_keys(
        cls,
        value: Any,
        *,
        field_name: str,
    ) -> tuple[str, ...]:
        """Normaliseer structurele context-ID's naar unieke uppercase tuples."""
        if value is None:
            return ()
        if not isinstance(value, list):
            raise DocumentationValidationError(
                f"{field_name} moet een lijst van niet-lege teksten zijn."
            )

        normalized: list[str] = []
        seen: set[str] = set()
        for raw in value:
            key = cls._normalize_context_key_optional(
                raw,
                field_name=field_name,
            )
            if key is None:
                raise DocumentationValidationError(
                    f"{field_name} mag geen lege of null-waarden bevatten."
                )
            if key not in seen:
                normalized.append(key)
                seen.add(key)

        return tuple(normalized)

    @staticmethod
    def _normalize_context_key_optional(
        value: Any,
        *,
        field_name: str,
    ) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise DocumentationValidationError(
                f"{field_name} moet tekst of null zijn."
            )
        normalized = value.strip().upper()
        if not normalized:
            return None
        if any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_" for ch in normalized):
            raise DocumentationValidationError(
                f"{field_name} mag alleen A-Z, 0-9 en underscore bevatten."
            )
        return normalized

    @classmethod
    def _normalize_topics(cls, value: Any) -> tuple[str, ...]:
        """Normaliseer vrije tags naar unieke lowercase identifiers."""
        if value is None:
            return ()
        if not isinstance(value, list):
            raise DocumentationValidationError(
                "topics moet een lijst van niet-lege teksten zijn."
            )

        normalized: list[str] = []
        seen: set[str] = set()
        for raw in value:
            topic = cls._normalize_topic_optional(raw)
            if topic is None:
                raise DocumentationValidationError(
                    "topics mag geen lege of null-waarden bevatten."
                )
            if topic not in seen:
                normalized.append(topic)
                seen.add(topic)

        return tuple(normalized)

    @staticmethod
    def _normalize_topic_optional(value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise DocumentationValidationError(
                "topic moet tekst of null zijn."
            )
        normalized = value.strip().casefold()
        if not normalized:
            return None
        if any(
            not (ch.isalnum() or ch in "_-")
            for ch in normalized
        ):
            raise DocumentationValidationError(
                "topic mag alleen letters, cijfers, underscore en koppelteken bevatten."
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
