"""
================================================================================
Module:     app/documentation/url_fetch.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-06
Auteur:     Bart Bossuyt

Doel:       GUI-onafhankelijke URL-hulpfuncties voor de import-wizard:
            metadata ophalen (titel, meta description, Open Graph),
            HTML-inhoud downloaden als snapshot en lokaal bewaren.
            Dit is de ENIGE module in het project die netwerktoegang doet.
            Geen Qt, geen assessment.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie: fetch_url_metadata, fetch_url_content,
                       save_url_snapshot, default_snapshots_dir.
================================================================================
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


class UrlFetchError(ValueError):
    """Fout bij het ophalen, parsen of opslaan van een URL-bron."""


# Beleidsconstanten — bewust expliciet en centraal.
_TIMEOUT_SECONDEN = 10
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_USER_AGENT = "ElectronicsDiagnosticToolHub/1.0 (import-wizard)"


@dataclass(frozen=True, slots=True)
class UrlMetadata:
    """Read-only metadata van een opgehaalde URL.

    Alle velden zijn optioneel behalve url en fetched_at: niet elke pagina
    heeft een titel, beschrijving of Open Graph-data.
    """

    url: str
    fetched_at: int
    http_status: int
    title: Optional[str] = None
    description: Optional[str] = None
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    language: Optional[str] = None
    content_type: Optional[str] = None


def default_snapshots_dir() -> Path:
    """Standaardmap voor HTML-snapshots.

    Zelfde hoofdniveau als sources/ en imported_catalog.json, onder
    %LOCALAPPDATA%. Buiten het standaardbereik van Windows Defender CFA.
    """
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        base = str(Path.home() / "AppData" / "Local")
    return (
        Path(base)
        / "ElectronicsDiagnosticToolHub"
        / "documentation"
        / "snapshots"
    )


def _valideer_url(url: str) -> str:
    """Controleer dat url een bruikbare http(s)-URL is."""
    if not isinstance(url, str) or not url.strip():
        raise UrlFetchError("URL mag niet leeg zijn")
    schoon = url.strip()
    parsed = urlparse(schoon)
    if parsed.scheme not in ("http", "https"):
        raise UrlFetchError(
            f"alleen http en https worden ondersteund, kreeg: {parsed.scheme!r}"
        )
    if not parsed.netloc:
        raise UrlFetchError(f"URL mist een host: {schoon}")
    return schoon


def _haal_html_op(url: str) -> tuple[str, requests.Response]:
    """Interne helper: doe het HTTP-verzoek en lees de HTML-string.

    Leest maximaal _MAX_BYTES. Strikte TLS-validatie. Duidelijke fouten
    bij timeout, verbindingsprobleem, HTTP-fout en te grote inhoud.
    """
    headers = {
        "User-Agent": _USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    }
    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=_TIMEOUT_SECONDEN,
            allow_redirects=True,
            stream=True,
        )
    except requests.exceptions.SSLError as exc:
        raise UrlFetchError(f"TLS-fout bij ophalen: {exc}") from exc
    except requests.exceptions.Timeout as exc:
        raise UrlFetchError(
            f"timeout na {_TIMEOUT_SECONDEN}s bij ophalen: {url}"
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        raise UrlFetchError(f"verbindingsfout: {exc}") from exc
    except requests.exceptions.RequestException as exc:
        raise UrlFetchError(f"verzoek mislukte: {exc}") from exc

    try:
        if response.status_code >= 400:
            raise UrlFetchError(
                f"HTTP {response.status_code} bij ophalen: {url}"
            )

        chunks: list[bytes] = []
        totaal = 0
        for chunk in response.iter_content(chunk_size=65536):
            if not chunk:
                continue
            totaal += len(chunk)
            if totaal > _MAX_BYTES:
                raise UrlFetchError(
                    f"inhoud groter dan {_MAX_BYTES // (1024 * 1024)} MB; "
                    f"import geweigerd"
                )
            chunks.append(chunk)
    finally:
        response.close()

    inhoud_bytes = b"".join(chunks)

    # Encoding bepalen: gebruik response.encoding als die gezet is, anders
    # utf-8 met fouten-tolerantie.
    encoding = response.encoding or "utf-8"
    try:
        html_tekst = inhoud_bytes.decode(encoding, errors="replace")
    except (LookupError, TypeError):
        html_tekst = inhoud_bytes.decode("utf-8", errors="replace")

    return html_tekst, response


def fetch_url_metadata(url: str) -> UrlMetadata:
    """Haal metadata op van een URL.

    Doet een volledige GET (geen HEAD), omdat veel servers HEAD weigeren
    of andere inhoud terugsturen. De HTML wordt tijdens deze aanroep
    volledig gelezen; de snapshot in save_url_snapshot is een aparte
    download. Voor de wizard is dat acceptabel: metadata en snapshot
    worden kort na elkaar opgehaald.
    """
    schone_url = _valideer_url(url)
    html_tekst, response = _haal_html_op(schone_url)

    soup = BeautifulSoup(html_tekst, "html.parser")

    def _meta(naam: str, *, attr: str = "name") -> Optional[str]:
        tag = soup.find("meta", attrs={attr: naam})
        if tag is None:
            return None
        inhoud = tag.get("content")
        if inhoud is None:
            return None
        tekst = str(inhoud).strip()
        return tekst or None

    titel_tag = soup.find("title")
    titel = titel_tag.get_text(strip=True) if titel_tag else None

    html_tag = soup.find("html")
    taal = None
    if html_tag is not None:
        taal_attr = html_tag.get("lang")
        if taal_attr:
            taal = str(taal_attr).strip() or None

    return UrlMetadata(
        url=schone_url,
        fetched_at=int(time.time() * 1000),
        http_status=response.status_code,
        title=titel or None,
        description=_meta("description"),
        og_title=_meta("og:title", attr="property"),
        og_description=_meta("og:description", attr="property"),
        language=taal,
        content_type=response.headers.get("Content-Type"),
    )


def fetch_url_content(url: str) -> str:
    """Haal de HTML-inhoud van een URL op als string.

    Gebruikt dezelfde grenzen als fetch_url_metadata (timeout, max grootte,
    strikte TLS). Geeft de ruwe HTML terug, niet geëxtraheerde tekst.
    """
    schone_url = _valideer_url(url)
    html_tekst, _response = _haal_html_op(schone_url)
    return html_tekst


def save_url_snapshot(
    html: str,
    source_id: str,
    *,
    snapshots_dir: Optional[Path] = None,
) -> Path:
    """Bewaar een HTML-snapshot lokaal als <source_id>.html.

    Weigert een bestaand doel te overschrijven. Maakt de doelmap aan indien
    nodig. Alle fouten worden als UrlFetchError doorgegeven.
    """
    if not source_id:
        raise UrlFetchError("source_id mag niet leeg zijn")
    if not isinstance(html, str):
        raise UrlFetchError("html moet een string zijn")

    doel_dir = Path(snapshots_dir) if snapshots_dir else default_snapshots_dir()

    try:
        doel_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise UrlFetchError(
            f"snapshotmap kon niet aangemaakt worden: {doel_dir} ({exc})"
        ) from exc

    doel_pad = doel_dir / f"{source_id}.html"

    if doel_pad.exists():
        raise UrlFetchError(
            f"snapshot bestaat al, weigert te overschrijven: {doel_pad}"
        )

    try:
        doel_pad.write_text(html, encoding="utf-8")
    except OSError as exc:
        raise UrlFetchError(f"snapshot kon niet geschreven worden: {exc}") from exc

    return doel_pad