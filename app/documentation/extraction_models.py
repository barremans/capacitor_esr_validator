"""
================================================================================
Module:     app/documentation/extraction_models.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-22
Auteur:     Bart Bossuyt

Doel:       Uniform resultaatmodel voor tekst- en metadata-extractie uit
            geïmporteerde documentatiebronnen (PDF / DOCX / XLSX / URL).
            GUI-onafhankelijk, geen Qt, geen netwerk, geen AI.

            Dit model is de ENIGE vorm waarin fase 12 (AI-extractie)
            tekst en metadata van een bron ontvangt, ongeacht het
            brontype. De bestaande extractors (pdf_extract,
            docx_extract, xlsx_extract, url_fetch) blijven ongewijzigd;
            extraction_service.py vertaalt hun resultaten naar dit model.

            Bewust GEEN paginanummering per zin, GEEN tokenisatie, GEEN
            prompting: dat hoort in 12B/12C. Dit model draagt alleen wat
            een extractor feitelijk kan leveren.

Wijzigingen:
  v1.0.0 (2026-10-22)  Eerste versie (fase 12A.1): ExtractionSourceKind,
                       ExtractionResult, ExtractionError. Frozen en
                       slots, met expliciete validatie in __post_init__.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ExtractionSourceKind(str, Enum):
    """Het brontype waaruit geëxtraheerd is.

    Bewust een eigen enum, los van ImportSourceType: extraction_models
    mag niet afhankelijk zijn van import_models, zodat 12B/12C dit model
    kunnen gebruiken zonder de import-laag te importeren.
    """

    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    URL = "url"


class ExtractionError(ValueError):
    """Uniforme fout bij tekst- of metadata-extractie.

    De originele exceptie van de betreffende extractor blijft als
    ``__cause__`` bewaard, zodat een debugger of log de bron van de
    fout kan achterhalen zonder dat 12B/12C alle vier de extractor-
    specifieke exceptietypes hoeven te kennen.
    """


def _normaliseer_optionele_tekst(
    waarde: Optional[str], veldnaam: str
) -> Optional[str]:
    """Valideer en normaliseer een optioneel tekstveld.

    - None blijft None.
    - Een lege of whitespace-only string wordt None.
    - Een niet-string, niet-None waarde is een fout.
    """
    if waarde is None:
        return None
    if not isinstance(waarde, str):
        raise ExtractionError(
            f"{veldnaam} moet een string of None zijn, kreeg {type(waarde)!r}"
        )
    gestript = waarde.strip()
    return gestript or None


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    """Uniform resultaat van één tekst- en metadata-extractie.

    Velden:

    - ``source_kind``: het brontype (PDF/DOCX/XLSX/URL).
    - ``source_id``: het source_id uit de importcatalogus, of None als
      de extractie niet aan een catalogusbron gekoppeld is (bv. een
      losse PDF die nog niet geïmporteerd is).
    - ``text``: de geëxtraheerde tekst. Mag leeg zijn (bv. een
      ingescande PDF zonder OCR); nooit None.
    - ``pages``: optionele tuple met per-pagina (PDF) of per-werkblad
      (XLSX) tekst. Leeg als de extractor geen paginascheiding levert.
    - ``metadata``: optioneel dict met brontype-specifieke metadata
      (titel, auteur, paginanummer, sheet_names, http_status, ...).
      De sleutels zijn bewust niet genormaliseerd: 12B/12C weten per
      brontype welke sleutels te verwachten. Een lege dict is geldig.
    - ``warnings``: optionele tuple met niet-fatale opmerkingen (bv.
      "PDF bevatte geen tekst", "URL-snapshot bevatte geen body").
    - ``origin``: optioneel pad of URL waaruit geëxtraheerd is. Puur
      voor herkomst-tracking (fase 12D); niet gebruikt door 12A zelf.

    Onveranderlijk (frozen) en slots. Geen verborgen correcties.
    """

    source_kind: ExtractionSourceKind
    source_id: Optional[str]
    text: str
    pages: tuple[str, ...] = ()
    metadata: dict = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    origin: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.source_kind, ExtractionSourceKind):
            raise ExtractionError(
                "source_kind moet ExtractionSourceKind zijn"
            )

        object.__setattr__(
            self,
            "source_id",
            _normaliseer_optionele_tekst(self.source_id, "source_id"),
        )

        if not isinstance(self.text, str):
            raise ExtractionError(
                f"text moet een string zijn, kreeg {type(self.text)!r}"
            )

        if not isinstance(self.pages, tuple):
            raise ExtractionError(
                f"pages moet een tuple zijn, kreeg {type(self.pages)!r}"
            )
        for index, pagina in enumerate(self.pages):
            if not isinstance(pagina, str):
                raise ExtractionError(
                    f"pages[{index}] moet een string zijn, "
                    f"kreeg {type(pagina)!r}"
                )

        if not isinstance(self.metadata, dict):
            raise ExtractionError(
                f"metadata moet een dict zijn, kreeg {type(self.metadata)!r}"
            )
        # Kopieer defensief: het object is frozen, maar de dict zelf is
        # dat niet. We willen niet dat een aanroeper de metadata van een
        # ExtractionResult achteraf nog muteert.
        object.__setattr__(self, "metadata", dict(self.metadata))

        if not isinstance(self.warnings, tuple):
            raise ExtractionError(
                f"warnings moet een tuple zijn, kreeg "
                f"{type(self.warnings)!r}"
            )
        for index, waarschuwing in enumerate(self.warnings):
            if not isinstance(waarschuwing, str):
                raise ExtractionError(
                    f"warnings[{index}] moet een string zijn, "
                    f"kreeg {type(waarschuwing)!r}"
                )

        object.__setattr__(
            self,
            "origin",
            _normaliseer_optionele_tekst(self.origin, "origin"),
        )

    @property
    def is_empty(self) -> bool:
        """True als er geen tekst geëxtraheerd is.

        Bedoeld als snelle check voor 12B/12C: een leeg ExtractionResult
        is geen fout (een ingescande PDF is een legitiem geval), maar
        de AI-laag moet er niet op loslaten zonder waarschuwing.
        """
        return not self.text.strip()

    def to_dict(self) -> dict:
        """Serialiseer naar een JSON-vriendelijk dict.

        Niet gebruikt door 12A zelf; wel handig voor logging, tests en
        latere herkomst-tracking (12D). Alle velden zijn JSON-safe:
        source_kind wordt zijn .value, tuples worden lists.
        """
        return {
            "source_kind": self.source_kind.value,
            "source_id": self.source_id,
            "text": self.text,
            "pages": list(self.pages),
            "metadata": dict(self.metadata),
            "warnings": list(self.warnings),
            "origin": self.origin,
        }