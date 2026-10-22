"""
================================================================================
Module:     app/documentation/extraction_service.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-22
Auteur:     Bart Bossuyt

Doel:       Uniforme dispatcher voor tekst- en metadata-extractie uit een
            geïmporteerde documentatiebron (PDF / DOCX / XLSX / URL).
            GUI-onafhankelijk, geen Qt, geen netwerk in deze module zelf.

            De vier bestaande extractors (pdf_extract, docx_extract,
            xlsx_extract, url_fetch) blijven ongewijzigd. Deze service
            kiest op basis van het brontype de juiste extractor, roept
            die aan en vertaalt het resultaat naar het uniforme
            ExtractionResult uit extraction_models.py.

            Voor URL-bronnen wordt de bestaande HTML-snapshot gelezen
            (snapshots/<source_id>.html). Er wordt GEEN nieuw
            netwerkverkeer gedaan: dat is de verantwoordelijkheid van
            url_import.py en url_fetch.py, niet van deze laag.

Wijzigingen:
  v1.0.0 (2026-10-22)  Eerste versie (fase 12A.2): extract_for_source,
                       extract_for_path, extract_for_url. Lokale
                       URL-teksthepler via BeautifulSoup, zodat
                       url_fetch.py niet gewijzigd hoeft te worden.
================================================================================
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from app.documentation.docx_extract import (
    DocxExtractError,
    extract_docx_metadata,
    extract_docx_text,
)
from app.documentation.extraction_models import (
    ExtractionError,
    ExtractionResult,
    ExtractionSourceKind,
)
from app.documentation.import_models import ImportSource, ImportSourceType
from app.documentation.pdf_extract import (
    PdfExtractError,
    extract_pdf_metadata,
    extract_pdf_text,
)
from app.documentation.url_fetch import (
    UrlFetchError,
    default_snapshots_dir,
)
from app.documentation.xlsx_extract import (
    XlsxExtractError,
    extract_xlsx_metadata,
    extract_xlsx_text,
)


# ---------------------------------------------------------------------------
# Interne helpers — pad-resolutie.
# ---------------------------------------------------------------------------

def _default_sources_dir() -> Path:
    """Standaardmap voor gekopieerde bronbestanden.

    Identiek aan pdf_extract.default_sources_dir() en de zustermodules.
    We dupliceren de constante hier bewust niet als string maar leiden
    hem af uit LOCALAPPDATA, zodat er één bron van waarheid blijft voor
    de mapnaam: de extractor-modules zelf. Deze functie bestaat zodat
    de dispatcher ook werkt als de extractor-modules hun default later
    zouden wijzigen; we roepen de extractor-default dus niet aan om
    cirkelimports te vermijden.

    In de praktijk levert dit exact dezelfde map op als de extractors.
    """
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        base = str(Path.home() / "AppData" / "Local")
    return (
        Path(base)
        / "ElectronicsDiagnosticToolHub"
        / "documentation"
        / "sources"
    )


def _bron_pad_voor_source(
    source: ImportSource,
    *,
    sources_dir: Optional[Path],
) -> Path:
    """Leid het pad van het bronbestand af uit source_id en brontype.

    De bestandsnaam in sources/ is altijd <source_id>.<extensie>, met
    de extensie bepaald door source_type. Dat is de afspraak van alle
    vier de *_extract-modules (copy_*_to_sources gebruikt dezelfde
    naam).
    """
    if source.source_type is ImportSourceType.PDF:
        extensie = "pdf"
    elif source.source_type is ImportSourceType.DOCX:
        extensie = "docx"
    elif source.source_type is ImportSourceType.XLSX:
        extensie = "xlsx"
    else:
        raise ExtractionError(
            f"_bron_pad_voor_source is niet bedoeld voor "
            f"source_type={source.source_type!r}"
        )

    bron_dir = Path(sources_dir) if sources_dir else _default_sources_dir()
    return bron_dir / f"{source.source_id}.{extensie}"


def _snapshot_pad_voor_source(
    source: ImportSource,
    *,
    snapshots_dir: Optional[Path],
) -> Path:
    """Leid het pad van de HTML-snapshot af uit source_id."""
    snap_dir = (
        Path(snapshots_dir) if snapshots_dir else default_snapshots_dir()
    )
    return snap_dir / f"{source.source_id}.html"


# ---------------------------------------------------------------------------
# Interne helpers — metadata naar dict.
# ---------------------------------------------------------------------------

def _pdf_metadata_dict(pad: Path) -> tuple[dict, tuple[str, ...]]:
    """Lees PDF-metadata als dict. Geeft (metadata, warnings) terug."""
    meta = extract_pdf_metadata(pad)
    warnings: list[str] = []

    if meta.is_encrypted:
        warnings.append(
            "PDF is versleuteld; tekstextractie is niet uitgevoerd."
        )

    metadata = {
        "page_count": meta.page_count,
        "title": meta.title,
        "author": meta.author,
        "subject": meta.subject,
        "creator": meta.creator,
        "producer": meta.producer,
        "creation_date": meta.creation_date,
        "modification_date": meta.modification_date,
        "is_encrypted": meta.is_encrypted,
    }
    return metadata, tuple(warnings)


def _docx_metadata_dict(pad: Path) -> tuple[dict, tuple[str, ...]]:
    """Lees DOCX-metadata als dict. Geeft (metadata, warnings) terug."""
    meta = extract_docx_metadata(pad)
    metadata = {
        "paragraph_count": meta.paragraph_count,
        "title": meta.title,
        "author": meta.author,
        "subject": meta.subject,
        "created": meta.created,
        "modified": meta.modified,
        "last_modified_by": meta.last_modified_by,
    }
    return metadata, ()


def _xlsx_metadata_dict(pad: Path) -> tuple[dict, tuple[str, ...]]:
    """Lees XLSX-metadata als dict. Geeft (metadata, warnings) terug."""
    meta = extract_xlsx_metadata(pad)
    metadata = {
        "sheet_count": meta.sheet_count,
        "sheet_names": list(meta.sheet_names),
        "title": meta.title,
        "author": meta.author,
        "subject": meta.subject,
        "created": meta.created,
        "modified": meta.modified,
    }
    return metadata, ()


# ---------------------------------------------------------------------------
# Interne helpers — paginascheiding.
# ---------------------------------------------------------------------------

def _pdf_pages(pad: Path) -> tuple[str, ...]:
    """Extraheer per pagina de tekst van een PDF.

    pypdf wordt hier rechtstreeks gebruikt in plaats van via
    extract_pdf_text(), omdat extract_pdf_text() de paginagrenzen
    weggooit. Deze functie levert dezelfde tekst, maar met behoud van
    paginascheiding, zodat 12C later per pagina kan citeren.

    Faalt met ExtractionError bij een ontbrekend/onleesbaar bestand of
    bij een versleutelde PDF, net als extract_pdf_text().
    """
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    pad = Path(pad)
    if not pad.exists():
        raise ExtractionError(f"PDF-bestand niet gevonden: {pad}")
    if not pad.is_file():
        raise ExtractionError(f"pad is geen bestand: {pad}")

    try:
        reader = PdfReader(str(pad))
    except PdfReadError as exc:
        raise ExtractionError(f"PDF onleesbaar: {exc}") from exc
    except OSError as exc:
        raise ExtractionError(
            f"PDF kan niet geopend worden: {exc}"
        ) from exc

    if reader.is_encrypted:
        raise ExtractionError(
            "PDF is versleuteld; paginatekst is niet geëxtraheerd."
        )

    pagina_teksten: list[str] = []
    for index, page in enumerate(reader.pages):
        try:
            tekst = page.extract_text() or ""
        except Exception as exc:  # noqa: BLE001 — pypdf gooit diverse types
            raise ExtractionError(
                f"tekstextractie faalde op pagina {index + 1}: {exc}"
            ) from exc
        pagina_teksten.append(tekst.strip())

    return tuple(pagina_teksten)


def _docx_pages(pad: Path) -> tuple[str, ...]:
    """DOCX heeft geen pagina's. We leveren een lege tuple.

    Bewust geen kunstmatige "pagina" van de hele tekst: de AI-laag moet
    weten dat DOCX geen paginascheiding heeft. De tekst zelf komt uit
    extract_docx_text(), die per paragraaf werkt.
    """
    return ()


def _xlsx_pages(pad: Path) -> tuple[str, ...]:
    """XLSX-paginascheiding = per werkblad.

    De bestaande extract_xlsx_text() levert al per werkblad een blok
    met header "# <bladnaam>". We splitsen dat resultaat niet opnieuw:
    de AI-laag kan de header zelf herkennen. We leveren hier alleen de
    metadata (sheet_names) en laten pages leeg, consistent met DOCX.
    """
    return ()


# ---------------------------------------------------------------------------
# Interne helpers — URL-tekst.
# ---------------------------------------------------------------------------

def _html_naar_tekst(html: str) -> str:
    """Pure HTML → platte tekst.

    Gebruikt BeautifulSoup met de html.parser (geen externe parser-
    dependency, al in requirements). Script- en style-inhoud wordt
    verwijderd; de rest wordt per blok samengevoegd met lege regels,
    zodat de AI-laag een leesbare tekst ziet in plaats van ruwe HTML.

    Geen normalisatie van witruimte binnen een blok: BeautifulSoup's
    get_text(strip=True) doet dat al per tekstknooppunt.
    """
    if not isinstance(html, str):
        raise ExtractionError(
            f"html moet een string zijn, kreeg {type(html)!r}"
        )

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    blokken: list[str] = []
    for element in soup.find_all(
        ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "td", "th", "pre"]
    ):
        tekst = element.get_text(separator=" ", strip=True)
        if tekst:
            blokken.append(tekst)

    if not blokken:
        # Geen herkenbare blokken: val terug op de volledige body-tekst.
        body = soup.body or soup
        fallback = body.get_text(separator="\n", strip=True)
        return fallback.strip()

    return "\n\n".join(blokken)


def _url_metadata_dict(
    html: str, url: str
) -> tuple[dict, tuple[str, ...]]:
    """Leid minimale metadata af uit een HTML-snapshot.

    De rijke metadata (title, description, og) is al opgehaald door
    url_fetch.fetch_url_metadata() tijdens de import en staat niet in
    de snapshot. We leveren hier alleen wat we uit de snapshot zelf
    kunnen halen: titel, taal en de bron-URL.
    """
    soup = BeautifulSoup(html, "html.parser")

    titel_tag = soup.find("title")
    titel = titel_tag.get_text(strip=True) if titel_tag else None

    html_tag = soup.find("html")
    taal = None
    if html_tag is not None:
        taal_attr = html_tag.get("lang")
        if taal_attr:
            taal = str(taal_attr).strip() or None

    metadata = {
        "url": url,
        "title": titel or None,
        "language": taal,
    }
    return metadata, ()


# ---------------------------------------------------------------------------
# Publieke API.
# ---------------------------------------------------------------------------

def extract_for_path(
    pad: Path,
    *,
    source_kind: ExtractionSourceKind,
    source_id: Optional[str] = None,
) -> ExtractionResult:
    """Extraheer tekst en metadata uit een lokaal bestand.

    ``source_kind`` bepaalt welke extractor gebruikt wordt; het bestand
    hoeft niet in sources/ te staan (een losse PDF mag ook). Voor URL
    is deze functie niet bedoeld: gebruik extract_for_url of
    extract_for_source.

    Faalt met ExtractionError als het bestand ontbreekt, onleesbaar is
    of als de onderliggende extractor een fout gooit. De originele
    exceptie blijft als __cause__ bewaard.
    """
    if not isinstance(source_kind, ExtractionSourceKind):
        raise ExtractionError(
            "source_kind moet ExtractionSourceKind zijn"
        )
    if source_kind is ExtractionSourceKind.URL:
        raise ExtractionError(
            "extract_for_path is niet bedoeld voor URL-bronnen; "
            "gebruik extract_for_url of extract_for_source."
        )

    pad = Path(pad)
    origin = str(pad)

    if source_kind is ExtractionSourceKind.PDF:
        return _extract_pdf(pad, source_id=source_id, origin=origin)
    if source_kind is ExtractionSourceKind.DOCX:
        return _extract_docx(pad, source_id=source_id, origin=origin)
    if source_kind is ExtractionSourceKind.XLSX:
        return _extract_xlsx(pad, source_id=source_id, origin=origin)

    # Onbereikbaar: alle enum-waarden zijn hierboven afgehandeld.
    raise ExtractionError(f"onbekende source_kind: {source_kind!r}")


def extract_for_url(
    *,
    url: str,
    html: Optional[str] = None,
    snapshot_pad: Optional[Path] = None,
    source_id: Optional[str] = None,
) -> ExtractionResult:
    """Extraheer tekst en metadata uit een URL-bron.

    Precies één van ``html`` of ``snapshot_pad`` moet meegegeven worden:

    - ``html``: de HTML-string (bv. vers uit url_fetch.fetch_url_content()).
    - ``snapshot_pad``: het pad naar een bestaande HTML-snapshot; de
      inhoud wordt gelezen zonder netwerkverkeer.

    ``url`` is verplicht en wordt alleen gebruikt voor herkomst en
    metadata, niet om opnieuw op te halen.
    """
    if not isinstance(url, str) or not url.strip():
        raise ExtractionError("url mag niet leeg zijn")

    if (html is None) == (snapshot_pad is None):
        raise ExtractionError(
            "geef precies één van html of snapshot_pad mee"
        )

    if html is not None:
        if not isinstance(html, str):
            raise ExtractionError(
                f"html moet een string zijn, kreeg {type(html)!r}"
            )
        ruwe_html = html
        origin = url.strip()
    else:
        snapshot_pad = Path(snapshot_pad)  # type: ignore[arg-type]
        if not snapshot_pad.exists():
            raise ExtractionError(
                f"HTML-snapshot niet gevonden: {snapshot_pad}"
            )
        if not snapshot_pad.is_file():
            raise ExtractionError(
                f"snapshot-pad is geen bestand: {snapshot_pad}"
            )
        try:
            ruwe_html = snapshot_pad.read_text(encoding="utf-8")
        except OSError as exc:
            raise ExtractionError(
                f"HTML-snapshot kon niet gelezen worden: {exc}"
            ) from exc
        origin = url.strip()

    tekst = _html_naar_tekst(ruwe_html)
    metadata, extra_warnings = _url_metadata_dict(ruwe_html, url.strip())

    warnings: list[str] = list(extra_warnings)
    if not tekst.strip():
        warnings.append(
            "HTML-snapshot bevatte geen herkenbare tekst."
        )

    return ExtractionResult(
        source_kind=ExtractionSourceKind.URL,
        source_id=source_id,
        text=tekst,
        pages=(),
        metadata=metadata,
        warnings=tuple(warnings),
        origin=origin,
    )


def extract_for_source(
    source: ImportSource,
    *,
    sources_dir: Optional[Path] = None,
    snapshots_dir: Optional[Path] = None,
) -> ExtractionResult:
    """Extraheer tekst en metadata voor een bestaande ImportSource.

    Voor PDF/DOCX/XLSX wordt het bestand in sources/<source_id>.<ext>
    gelezen. Voor URL wordt de snapshot in snapshots/<source_id>.html
    gelezen. Er wordt geen netwerkverkeer gedaan.

    Faalt met ExtractionError als het bronbestand of de snapshot
    ontbreekt, of als de onderliggende extractor een fout gooit.
    """
    if not isinstance(source, ImportSource):
        raise ExtractionError(
            f"source moet een ImportSource zijn, kreeg {type(source)!r}"
        )

    if source.source_type is ImportSourceType.URL:
        if not source.source_url:
            raise ExtractionError(
                "URL-bron heeft geen source_url; kan niet geëxtraheerd worden."
            )
        snapshot_pad = _snapshot_pad_voor_source(
            source, snapshots_dir=snapshots_dir
        )
        return extract_for_url(
            url=source.source_url,
            snapshot_pad=snapshot_pad,
            source_id=source.source_id,
        )

    if source.source_type is ImportSourceType.PDF:
        kind = ExtractionSourceKind.PDF
    elif source.source_type is ImportSourceType.DOCX:
        kind = ExtractionSourceKind.DOCX
    elif source.source_type is ImportSourceType.XLSX:
        kind = ExtractionSourceKind.XLSX
    else:
        raise ExtractionError(
            f"onbekende source_type: {source.source_type!r}"
        )

    bron_pad = _bron_pad_voor_source(source, sources_dir=sources_dir)
    return extract_for_path(
        bron_pad,
        source_kind=kind,
        source_id=source.source_id,
    )


# ---------------------------------------------------------------------------
# Per-brontype implementaties.
# ---------------------------------------------------------------------------

def _extract_pdf(
    pad: Path,
    *,
    source_id: Optional[str],
    origin: str,
) -> ExtractionResult:
    try:
        tekst = extract_pdf_text(pad)
    except PdfExtractError as exc:
        raise ExtractionError(
            f"PDF-tekstextractie faalde: {exc}"
        ) from exc

    try:
        metadata, extra_warnings = _pdf_metadata_dict(pad)
    except PdfExtractError as exc:
        raise ExtractionError(
            f"PDF-metadata-extractie faalde: {exc}"
        ) from exc

    try:
        pages = _pdf_pages(pad)
    except ExtractionError as exc:
        # Paginascheiding is een aanvulling; als die faalt maar de
        # volledige tekst wel gelukt is, degraderen we naar een
        # waarschuwing in plaats van de hele extractie te laten vallen.
        pages = ()
        extra_warnings = extra_warnings + (
            f"Paginascheiding niet beschikbaar: {exc}",
        )

    warnings: list[str] = list(extra_warnings)
    if not tekst.strip():
        warnings.append(
            "PDF bevatte geen selecteerbare tekst; "
            "mogelijk een ingescand document zonder OCR."
        )

    return ExtractionResult(
        source_kind=ExtractionSourceKind.PDF,
        source_id=source_id,
        text=tekst,
        pages=pages,
        metadata=metadata,
        warnings=tuple(warnings),
        origin=origin,
    )


def _extract_docx(
    pad: Path,
    *,
    source_id: Optional[str],
    origin: str,
) -> ExtractionResult:
    try:
        tekst = extract_docx_text(pad)
    except DocxExtractError as exc:
        raise ExtractionError(
            f"DOCX-tekstextractie faalde: {exc}"
        ) from exc

    try:
        metadata, extra_warnings = _docx_metadata_dict(pad)
    except DocxExtractError as exc:
        raise ExtractionError(
            f"DOCX-metadata-extractie faalde: {exc}"
        ) from exc

    warnings: list[str] = list(extra_warnings)
    if not tekst.strip():
        warnings.append(
            "DOCX bevatte geen tekst in de hoofdparagrafen."
        )

    return ExtractionResult(
        source_kind=ExtractionSourceKind.DOCX,
        source_id=source_id,
        text=tekst,
        pages=_docx_pages(pad),
        metadata=metadata,
        warnings=tuple(warnings),
        origin=origin,
    )


def _extract_xlsx(
    pad: Path,
    *,
    source_id: Optional[str],
    origin: str,
) -> ExtractionResult:
    try:
        tekst = extract_xlsx_text(pad)
    except XlsxExtractError as exc:
        raise ExtractionError(
            f"XLSX-tekstextractie faalde: {exc}"
        ) from exc

    try:
        metadata, extra_warnings = _xlsx_metadata_dict(pad)
    except XlsxExtractError as exc:
        raise ExtractionError(
            f"XLSX-metadata-extractie faalde: {exc}"
        ) from exc

    warnings: list[str] = list(extra_warnings)
    if not tekst.strip():
        warnings.append(
            "XLSX bevatte geen celwaarden in de werkbladen."
        )

    return ExtractionResult(
        source_kind=ExtractionSourceKind.XLSX,
        source_id=source_id,
        text=tekst,
        pages=_xlsx_pages(pad),
        metadata=metadata,
        warnings=tuple(warnings),
        origin=origin,
    )