"""
================================================================================
Module:     app/helpers/updater.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.2.0
Datum:      2026-10-16
Auteur:     Bart Bossuyt

Doel:       Pure, GUI-onafhankelijke update-check tegen GitHub.
            Leest de "latest"-pointer op releases/latest/version.txt
            (raw-URL, met Contents API als fallback) en vergelijkt die
            met de lokale app/version.__version__.

            Formaat van version.txt (geschreven door publish.ps1):
              regel 1: <versie>          bv. 1.0.4
              regel 2: <download-URL>    bv. https://github.com/.../ESR_TesterSetup_1.0.4.exe

            Sinds v1.1.0 ook fetch_release_notes(): haalt de release notes
            (body) van de laatste gepubliceerde GitHub Release op via de
            Releases API, zodat de GUI een "Wat is er nieuw?"-venster kan
            tonen. Die tekst vult de gebruiker manueel in op GitHub.

            Sinds v1.2.0 ook async-varianten:
              - check_for_update_async(...)
              - fetch_release_notes_async(...)
            Die draaien de bestaande synchrone functies in een
            achtergrondthread via app/helpers/async_worker. De synchrone
            functies blijven ongewijzigd en blijven de primaire API voor
            pure tests en niet-GUI-gebruik.

            Geen Qt-imports op moduleniveau in de synchrone laag. De
            async-varianten importeren Qt pas bij gebruik (via
            async_worker), zodat pure tests zonder QApplication blijven
            werken.

Wijzigingen:
  v1.0.0 (2026-10-14)  Fase 9H. Eerste versie, afgeleid van
                        ArticleSearch updater.py v1.3.0, maar:
                          - geen Qt, geen QMessageBox;
                          - geen hardcoded token (stond al niet meer in
                            de bron, maar expliciet bevestigd);
                          - parse_version via packaging;
                          - duidelijke dataclass UpdateInfo als resultaat;
                          - aparte functies fetch_version_txt(),
                            parse_version_file() en check_for_update()
                            zodat elke laag afzonderlijk testbaar is.
  v1.1.0 (2026-10-15)  Fase 9H-afronding: fetch_release_notes() toegevoegd
                        (1-op-1 naar ArticleSearch updater.py v1.3.0).
                        Haalt tag_name/body/html_url van de laatste
                        gepubliceerde Release via de GitHub Releases API.
                        Geen token, geen Qt, geen try/except — de GUI
                        vangt fouten af en toont een nette fallback.
                        Nieuwe constanten RELEASES_API_LATEST en
                        _headers_releases_api().
  v1.2.0 (2026-10-16)  Fase 11E.1: async-varianten toegevoegd:
                        check_for_update_async() en
                        fetch_release_notes_async(). Beide draaien de
                        bestaande synchrone functies in een
                        achtergrondthread via app/helpers/async_worker.
                        De synchrone functies blijven ongewijzigd.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

import requests
from packaging.version import InvalidVersion, parse as parse_version


OWNER = "barremans"
REPO = "capacitor_esr_validator"
BRANCH = "main"
REL_DIR = "releases/latest"
VERSION_FILENAME = "version.txt"

RAW_VERSION_URL = (
    f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/"
    f"{REL_DIR}/{VERSION_FILENAME}"
)
CONTENTS_VERSION_URL = (
    f"https://api.github.com/repos/{OWNER}/{REPO}/contents/"
    f"{REL_DIR}/{VERSION_FILENAME}?ref={BRANCH}"
)

# v1.1.0: officiële GitHub Releases API — geeft de laatste gepubliceerde
# (niet-draft, niet-pre-release) Release terug, inclusief release notes
# (body). De body is de Markdown-tekst die de gebruiker manueel invult
# bij het publiceren van de Release op GitHub.
RELEASES_API_LATEST = (
    f"https://api.github.com/repos/{OWNER}/{REPO}/releases/latest"
)

DEFAULT_TIMEOUT = 5


@dataclass(frozen=True, slots=True)
class UpdateInfo:
    """Resultaat van een update-check."""

    current_version: str
    remote_version: str
    is_newer: bool
    download_url: str | None = None


def _headers_raw() -> dict[str, str]:
    return {"Accept": "text/plain"}


def _headers_api() -> dict[str, str]:
    # v1.0.0: geen Authorization-header. De repo is Public; de Contents API
    # werkt anoniem. Zelfde keuze als ArticleSearch updater.py v1.3.0.
    return {"Accept": "application/vnd.github.v3.raw"}


def _headers_releases_api() -> dict[str, str]:
    """Headers voor de Releases API.

    v1.1.0: bewust GEEN Authorization-header. Een publieke release ophalen
    is puur leesverkeer en werkt bij GitHub altijd anoniem. Een (kapot)
    token zou de hele request onnodig laten falen met 401. Mocht de repo
    ooit Private worden, dan moet hier weer een geldig token komen — uit
    github_secret_local.py, nooit hardcoded.
    """
    return {"Accept": "application/vnd.github+json"}


def fetch_version_txt(timeout: int = DEFAULT_TIMEOUT) -> str:
    """Haalt de inhoud van releases/latest/version.txt op.

    Eerst via raw.githubusercontent.com (snel, geen API-limiet), dan via
    de Contents API als fallback. Werpt requests.RequestException of
    requests.HTTPError bij een netwerk- of API-fout.
    """
    # 1) Raw
    try:
        r = requests.get(
            RAW_VERSION_URL, headers=_headers_raw(), timeout=timeout
        )
        if r.ok:
            return r.text
    except requests.RequestException:
        pass

    # 2) Contents API (fallback)
    r = requests.get(
        CONTENTS_VERSION_URL, headers=_headers_api(), timeout=timeout
    )
    if not r.ok:
        raise requests.HTTPError(
            f"{r.status_code} for {CONTENTS_VERSION_URL}: {r.text[:200]}"
        )
    return r.text


def fetch_release_notes(timeout: int = DEFAULT_TIMEOUT) -> dict:
    """v1.1.0: haalt de release notes op van de laatste GitHub Release.

    Retourneert: {"tag_name": str, "body": str, "html_url": str}
    - "body" is de Markdown-tekst zoals ingevuld bij het publiceren van
      de Release op GitHub (kan leeg zijn als er niets werd ingevuld).
    - "html_url" wijst naar de releasepagina zelf — bruikbaar als
      fallback-link wanneer "body" leeg is of het ophalen faalt.

    Werpt requests.HTTPError / requests.RequestException bij netwerk- of
    API-fouten — de aanroeper (GUI) vangt dit af en toont een nette
    fallback. Draft- en pre-release-Releases worden door dit endpoint
    automatisch genegeerd.
    """
    r = requests.get(
        RELEASES_API_LATEST,
        headers=_headers_releases_api(),
        timeout=timeout,
    )
    if not r.ok:
        raise requests.HTTPError(
            f"{r.status_code} for {RELEASES_API_LATEST}: {r.text[:200]}"
        )
    data = r.json()
    return {
        "tag_name": data.get("tag_name", ""),
        "body": (data.get("body") or "").strip(),
        "html_url": data.get("html_url")
        or f"https://github.com/{OWNER}/{REPO}/releases/latest",
    }


def parse_version_file(txt: str) -> tuple[str, str | None]:
    """Leest versie en optionele download-URL uit version.txt.

    Regel 1 = versie (eventueel met 'v'-prefix, wordt gestript).
    Regel 2 = download-URL als die met http(s):// begint, anders None.
    """
    lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]
    if not lines:
        raise ValueError("version.txt is leeg")

    version = lines[0].lstrip("vV")
    url: str | None = None
    if len(lines) >= 2 and lines[1].startswith(("http://", "https://")):
        url = lines[1]
    return version, url


def _asset_url(version: str) -> str:
    return (
        f"https://github.com/{OWNER}/{REPO}/releases/download/"
        f"v{version}/ESR_TesterSetup_{version}.exe"
    )


def _is_newer(remote: str, current: str) -> bool:
    """Vergelijkt twee versiestrings. Werpt ValueError bij ongeldige input."""
    try:
        return parse_version(remote) > parse_version(current)
    except InvalidVersion as exc:
        raise ValueError(f"Ongeldige versie: {exc}") from exc


def check_for_update(
    current_version: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> UpdateInfo:
    """Vergelijkt de remote versie met current_version.

    Retourneert altijd een UpdateInfo. Bij een netwerkfout of ongeldige
    remote versie komt er een UpdateInfo met is_newer=False en
    remote_version == current_version — de aanroeper hoeft geen
    exception af te vangen. Dat is bewust: een update-check mag de
    applicatie nooit laten crashen.
    """
    try:
        txt = fetch_version_txt(timeout=timeout)
        remote_version, url = parse_version_file(txt)
        if not url:
            url = _asset_url(remote_version)
        newer = _is_newer(remote_version, current_version)
        return UpdateInfo(
            current_version=current_version,
            remote_version=remote_version,
            is_newer=newer,
            download_url=url,
        )
    except (requests.RequestException, ValueError, OSError):
        return UpdateInfo(
            current_version=current_version,
            remote_version=current_version,
            is_newer=False,
            download_url=None,
        )


# ---------------------------------------------------------------------------
# v1.2.0 — async-varianten (fase 11E.1)
# ---------------------------------------------------------------------------
# Deze functies draaien de bestaande synchrone functies in een
# achtergrondthread via app/helpers/async_worker. De synchrone functies
# hierboven blijven ongewijzigd en blijven de primaire API voor pure
# tests en niet-GUI-gebruik.
#
# Belangrijk: check_for_update() vangt zelf alle fouten af en retourneert
# altijd een UpdateInfo. Voor de async-variant betekent dat: on_error
# wordt alleen aangeroepen bij een fout die check_for_update() zelf niet
# afvangt — in de praktijk gebeurt dat niet, maar de aanroeper mag er
# niet op vertrouwen dat on_error nooit komt. fetch_release_notes()
# werpt wél exceptions; daar is on_error functioneel.

def check_for_update_async(
    current_version: str,
    *,
    on_success: Callable[[UpdateInfo], None],
    on_error: Optional[Callable[[str, str], None]] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> Any:
    """Asynchrone variant van check_for_update().

    Roept on_success(info) aan in de GUI-thread met het UpdateInfo-object.
    on_error is optioneel en wordt in de praktijk niet aangeroepen, omdat
    check_for_update() zelf alle fouten afvangt.

    Retourneert de gestarte AsyncWorker. De aanroeper hoeft die normaal
    niet te bewaren.
    """
    from app.helpers.async_worker import run_async

    return run_async(
        check_for_update,
        current_version,
        timeout=timeout,
        on_success=on_success,
        on_error=on_error,
    )


def fetch_release_notes_async(
    *,
    on_success: Callable[[dict], None],
    on_error: Optional[Callable[[str, str], None]] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> Any:
    """Asynchrone variant van fetch_release_notes().

    Roept on_success(notes) aan in de GUI-thread met het dict-resultaat
    van fetch_release_notes(). Roept on_error(kort, traceback) aan als
    het ophalen faalt — dat is hier functioneel, want
    fetch_release_notes() werpt wél exceptions.

    Retourneert de gestarte AsyncWorker. De aanroeper hoeft die normaal
    niet te bewaren.
    """
    from app.helpers.async_worker import run_async

    return run_async(
        fetch_release_notes,
        timeout=timeout,
        on_success=on_success,
        on_error=on_error,
    )