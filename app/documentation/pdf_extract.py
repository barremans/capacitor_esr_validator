"""
================================================================================
Module:     app/documentation/pdf_extract.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.1
Datum:      2026-10-06
Auteur:     Bart Bossuyt

Doel:       GUI-onafhankelijke PDF-hulpfuncties voor de import-wizard:
            metadata lezen, tekst extraheren, SHA-256 berekenen en het
            bronbestand kopiëren naar de gebruikersmap. Geen Qt, geen
            netwerk, geen assessment.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie: extract_pdf_metadata,
                       extract_pdf_text, compute_file_hash,
                       copy_pdf_to_sources, default_sources_dir.
  v1.0.1 (2026-10-06)  copy_pdf_to_sources: mkdir-fouten (OSError,
                       FileExistsError) worden nu ook als PdfExtractError
                       doorgegeven. Maakt de functie robuust tegen paden
                       die geen map zijn, rechtenproblemen en schijf vol.
================================================================================
"""

from __future__ import annotations

import hashlib
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class PdfExtractError(ValueError):
    """Fout bij het lezen, hashen of kopiëren van een PDF-bron."""


@dataclass(frozen=True, slots=True)
class PdfMetadata:
    """Read-only metadata van een PDF-bestand.

    Alle velden zijn optioneel behalve page_count: PDF's zijn niet verplicht
    om titel, auteur of aanmaakdatum te bevatten.
    """

    page_count: int
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    is_encrypted: bool = False


def default_sources_dir() -> Path:
    """Standaardmap voor gekopieerde PDF-bronbestanden.

    Bewust onder %LOCALAPPDATA%, op hetzelfde hoofdniveau als de SQLite-
    meetdatabase en de gebruikerscatalogus. Deze locatie valt buiten het
    standaardbereik van Windows Defender Controlled Folder Access.
    """

    base = os.environ.get("LOCALAPPDATA")
    if not base:
        base = str(Path.home() / "AppData" / "Local")
    return Path(base) / "ElectronicsDiagnosticToolHub" / "documentation" / "sources"


def extract_pdf_metadata(pad: Path) -> PdfMetadata:
    """Lees metadata uit een PDF-bestand.

    Faalt met PdfExtractError bij een ontbrekend, onleesbaar of versleuteld
    bestand. Een versleutelde PDF wordt gedetecteerd maar niet ontsleuteld:
    de aanroeper beslist wat te doen.
    """
    pad = Path(pad)
    if not pad.exists():
        raise PdfExtractError(f"PDF-bestand niet gevonden: {pad}")
    if not pad.is_file():
        raise PdfExtractError(f"pad is geen bestand: {pad}")

    try:
        reader = PdfReader(str(pad))
    except PdfReadError as exc:
        raise PdfExtractError(f"PDF onleesbaar: {exc}") from exc
    except OSError as exc:
        raise PdfExtractError(f"PDF kan niet geopend worden: {exc}") from exc

    is_encrypted = bool(reader.is_encrypted)

    try:
        page_count = len(reader.pages)
    except Exception as exc:  # noqa: BLE001 - pypdf gooit diverse types
        if is_encrypted:
            page_count = 0
        else:
            raise PdfExtractError(
                f"aantal pagina's kon niet bepaald worden: {exc}"
            ) from exc

    raw_meta = reader.metadata or {}

    def _get(naam: str) -> Optional[str]:
        waarde = raw_meta.get(naam) if hasattr(raw_meta, "get") else None
        if waarde is None:
            return None
        tekst = str(waarde).strip()
        return tekst or None

    return PdfMetadata(
        page_count=page_count,
        title=_get("/Title"),
        author=_get("/Author"),
        subject=_get("/Subject"),
        creator=_get("/Creator"),
        producer=_get("/Producer"),
        creation_date=_get("/CreationDate"),
        modification_date=_get("/ModDate"),
        is_encrypted=is_encrypted,
    )


def extract_pdf_text(pad: Path) -> str:
    """Extraheer de ruwe tekst van alle pagina's, gescheiden door lege regels.

    Geen OCR, geen Markdown-conversie, geen lay-outreconstructie. Voor
    ingescande PDF's levert dit een lege of bijna lege string op; dat is
    een bewuste beperking van deze deelfase.
    """
    pad = Path(pad)
    if not pad.exists():
        raise PdfExtractError(f"PDF-bestand niet gevonden: {pad}")
    if not pad.is_file():
        raise PdfExtractError(f"pad is geen bestand: {pad}")

    try:
        reader = PdfReader(str(pad))
    except PdfReadError as exc:
        raise PdfExtractError(f"PDF onleesbaar: {exc}") from exc
    except OSError as exc:
        raise PdfExtractError(f"PDF kan niet geopend worden: {exc}") from exc

    if reader.is_encrypted:
        raise PdfExtractError(
            "PDF is versleuteld; tekstextractie is niet uitgevoerd."
        )

    pagina_teksten: list[str] = []
    for index, page in enumerate(reader.pages):
        try:
            tekst = page.extract_text() or ""
        except Exception as exc:  # noqa: BLE001 - pypdf gooit diverse types
            raise PdfExtractError(
                f"tekstextractie faalde op pagina {index + 1}: {exc}"
            ) from exc
        pagina_teksten.append(tekst.strip())

    return "\n\n".join(pagina_teksten)


def compute_file_hash(pad: Path, *, blokgrootte: int = 65536) -> str:
    """Bereken de SHA-256 van een bestand, blok per blok."""
    pad = Path(pad)
    if not pad.exists():
        raise PdfExtractError(f"bestand niet gevonden: {pad}")
    if not pad.is_file():
        raise PdfExtractError(f"pad is geen bestand: {pad}")

    hasher = hashlib.sha256()
    try:
        with pad.open("rb") as handle:
            while True:
                blok = handle.read(blokgrootte)
                if not blok:
                    break
                hasher.update(blok)
    except OSError as exc:
        raise PdfExtractError(f"hash kon niet berekend worden: {exc}") from exc

    return hasher.hexdigest()


def copy_pdf_to_sources(
    bron_pad: Path,
    source_id: str,
    *,
    sources_dir: Optional[Path] = None,
) -> Path:
    """Kopieer een PDF naar de gebruikersmap en geef het doelpad terug.

    De doelnaam is <source_id>.pdf, zodat elke import onafhankelijk is van
    de oorspronkelijke bestandsnaam en er geen naamconflicten ontstaan.
    Een bestaand doelbestand wordt nooit stil overschreven: als het al
    bestaat, wordt PdfExtractError opgegooid.

    Alle fouten bij het aanmaken van de doelmap of het kopiëren worden
    als PdfExtractError doorgegeven, inclusief het geval waarin het
    doelpad een bestaand bestand is in plaats van een map.
    """
    bron_pad = Path(bron_pad)
    if not bron_pad.exists():
        raise PdfExtractError(f"bronbestand niet gevonden: {bron_pad}")
    if not bron_pad.is_file():
        raise PdfExtractError(f"bronpad is geen bestand: {bron_pad}")
    if not source_id:
        raise PdfExtractError("source_id mag niet leeg zijn")

    doel_dir = Path(sources_dir) if sources_dir else default_sources_dir()

    try:
        doel_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        # Dekt FileExistsError wanneer het pad een bestand is, plus
        # rechtenproblemen, schijf vol, enz.
        raise PdfExtractError(
            f"doelmap kon niet aangemaakt worden: {doel_dir} ({exc})"
        ) from exc

    doel_pad = doel_dir / f"{source_id}.pdf"

    if doel_pad.exists():
        raise PdfExtractError(
            f"doelbestand bestaat al, weigert te overschrijven: {doel_pad}"
        )

    try:
        shutil.copy2(bron_pad, doel_pad)
    except OSError as exc:
        raise PdfExtractError(f"kopiëren faalde: {exc}") from exc

    return doel_pad