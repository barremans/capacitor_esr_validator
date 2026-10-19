"""
================================================================================
Module:     tests/test_documentation_url_fetch.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-16
Auteur:     Bart Bossuyt

Doel:       Regressietests voor url_fetch: metadata-parsing, snapshot opslaan,
            foutpaden. Netwerk wordt gemockt via een fake requests.get.
            Geen echte HTTP-verzoeken in deze tests.

            Sinds v1.1.0 (fase 11E.2) ook tests voor de async-varianten
            fetch_url_metadata_async() en fetch_url_content_async().
            De async-tests bewaren hun worker in _bewaarde_workers,
            zodat de WorkerSignals blijft leven tot de callback is
            aangeroepen.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie.
  v1.1.0 (2026-10-16)  Fase 11E.2: async-varianten.
================================================================================
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
import requests

import app.documentation.url_fetch as url_fetch_module
from app.documentation.url_fetch import (
    UrlFetchError,
    UrlMetadata,
    default_snapshots_dir,
    fetch_url_content,
    fetch_url_metadata,
    save_url_snapshot,
)


# ------------------------------------------------------------------ fake response

class _FakeResponse:
    """Minimale requests.Response-vervanger voor tests."""

    def __init__(
        self,
        *,
        status_code: int = 200,
        inhoud: bytes = b"",
        encoding: str = "utf-8",
        content_type: str = "text/html; charset=utf-8",
    ) -> None:
        self.status_code = status_code
        self.encoding = encoding
        self.headers = {"Content-Type": content_type}
        self._inhoud = inhoud
        self.closed = False

    def iter_content(self, chunk_size: int = 65536):
        for i in range(0, len(self._inhoud), chunk_size):
            yield self._inhoud[i : i + chunk_size]

    def close(self) -> None:
        self.closed = True


def _installeer_fake_get(monkeypatch, response_of_exception):
    """Vervang requests.get door een functie die het gegeven antwoord of
    de gegeven exception retourneert/gooit."""

    def _fake_get(url, **kwargs):
        if isinstance(response_of_exception, Exception):
            raise response_of_exception
        return response_of_exception

    monkeypatch.setattr(url_fetch_module.requests, "get", _fake_get)


def _maak_html(titel: str = "Testpagina", taal: str = "nl") -> bytes:
    return (
        f"<!DOCTYPE html>"
        f"<html lang='{taal}'>"
        f"<head>"
        f"<title>{titel}</title>"
        f"<meta name='description' content='Beschrijving hier'>"
        f"<meta property='og:title' content='OG Titel'>"
        f"<meta property='og:description' content='OG Beschrijving'>"
        f"</head>"
        f"<body><p>Inhoud</p></body>"
        f"</html>"
    ).encode("utf-8")


# ------------------------------------------------------------------ validatie

@pytest.mark.parametrize(
    "url",
    ["", "   ", "geen-url", "ftp://example.com", "file:///etc/passwd"],
)
def test_ongeldige_url_faalt(url):
    with pytest.raises(UrlFetchError):
        fetch_url_metadata(url)
    with pytest.raises(UrlFetchError):
        fetch_url_content(url)


# ------------------------------------------------------------------ metadata

def test_metadata_gelukkig_pad(monkeypatch):
    response = _FakeResponse(inhoud=_maak_html(titel="Mijn titel", taal="nl"))
    _installeer_fake_get(monkeypatch, response)

    meta = fetch_url_metadata("https://example.com/pagina")

    assert isinstance(meta, UrlMetadata)
    assert meta.url == "https://example.com/pagina"
    assert meta.http_status == 200
    assert meta.title == "Mijn titel"
    assert meta.description == "Beschrijving hier"
    assert meta.og_title == "OG Titel"
    assert meta.og_description == "OG Beschrijving"
    assert meta.language == "nl"
    assert meta.fetched_at > 0


def test_metadata_zonder_titel_geeft_none(monkeypatch):
    html = b"<html><body>Geen titel</body></html>"
    _installeer_fake_get(monkeypatch, _FakeResponse(inhoud=html))

    meta = fetch_url_metadata("https://example.com")

    assert meta.title is None
    assert meta.description is None
    assert meta.og_title is None


# ------------------------------------------------------------------ foutpaden

def test_timeout_faalt(monkeypatch):
    _installeer_fake_get(
        monkeypatch, requests.exceptions.Timeout("te langzaam")
    )
    with pytest.raises(UrlFetchError) as excinfo:
        fetch_url_metadata("https://example.com")
    assert "timeout" in str(excinfo.value).lower()


def test_verbindingsfout_faalt(monkeypatch):
    _installeer_fake_get(
        monkeypatch, requests.exceptions.ConnectionError("DNS faalde")
    )
    with pytest.raises(UrlFetchError) as excinfo:
        fetch_url_metadata("https://example.com")
    assert "verbinding" in str(excinfo.value).lower()


def test_ssl_fout_faalt(monkeypatch):
    _installeer_fake_get(
        monkeypatch, requests.exceptions.SSLError("cert ongeldig")
    )
    with pytest.raises(UrlFetchError) as excinfo:
        fetch_url_metadata("https://example.com")
    assert "tls" in str(excinfo.value).lower()


def test_http_404_faalt(monkeypatch):
    _installeer_fake_get(
        monkeypatch,
        _FakeResponse(status_code=404, inhoud=b"niet gevonden"),
    )
    with pytest.raises(UrlFetchError) as excinfo:
        fetch_url_metadata("https://example.com")
    assert "404" in str(excinfo.value)


def test_http_500_faalt(monkeypatch):
    _installeer_fake_get(
        monkeypatch,
        _FakeResponse(status_code=500, inhoud=b"server fout"),
    )
    with pytest.raises(UrlFetchError):
        fetch_url_metadata("https://example.com")


def test_inhoud_groter_dan_max_faalt(monkeypatch):
    # 6 MB aan data, boven de limiet van 5 MB
    grote_inhoud = b"x" * (6 * 1024 * 1024)
    _installeer_fake_get(monkeypatch, _FakeResponse(inhoud=grote_inhoud))
    with pytest.raises(UrlFetchError) as excinfo:
        fetch_url_metadata("https://example.com")
    assert "groter" in str(excinfo.value).lower()


# ------------------------------------------------------------------ content

def test_content_geeft_ruwe_html(monkeypatch):
    html = _maak_html(titel="Hallo")
    _installeer_fake_get(monkeypatch, _FakeResponse(inhoud=html))

    tekst = fetch_url_content("https://example.com")

    assert "Hallo" in tekst
    assert tekst.startswith("<!DOCTYPE html>")


# ------------------------------------------------------------------ snapshot opslaan

def test_snapshot_wordt_opgeslagen(tmp_path):
    snapshots = tmp_path / "snaps"
    html = "<html><body>inhoud</body></html>"

    pad = save_url_snapshot(html, "src-abc", snapshots_dir=snapshots)

    assert pad.exists()
    assert pad.name == "src-abc.html"
    assert pad.read_text(encoding="utf-8") == html


def test_snapshot_weigert_overschrijven(tmp_path):
    snapshots = tmp_path / "snaps"
    save_url_snapshot("eerste", "src-abc", snapshots_dir=snapshots)

    with pytest.raises(UrlFetchError):
        save_url_snapshot("tweede", "src-abc", snapshots_dir=snapshots)


def test_snapshot_maakt_map_aan(tmp_path):
    snapshots = tmp_path / "diep" / "genest"
    assert not snapshots.exists()

    save_url_snapshot("<html></html>", "src-1", snapshots_dir=snapshots)

    assert snapshots.exists()


def test_snapshot_lege_source_id_faalt(tmp_path):
    with pytest.raises(UrlFetchError):
        save_url_snapshot("<html></html>", "", snapshots_dir=tmp_path)


def test_snapshot_map_is_bestand_faalt(tmp_path):
    blokkerend = tmp_path / "snaps"
    blokkerend.write_text("ik ben een bestand", encoding="utf-8")

    with pytest.raises(UrlFetchError):
        save_url_snapshot("<html></html>", "src-1", snapshots_dir=blokkerend)


# ------------------------------------------------------------------ defaults

def test_default_snapshots_dir_onder_localappdata(monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", "C:\\TestLocal")
    pad = default_snapshots_dir()
    assert str(pad).startswith("C:\\TestLocal")
    assert "ElectronicsDiagnosticToolHub" in str(pad)
    assert "snapshots" in str(pad)


# ===========================================================================
# v1.1.0 — async-varianten (fase 11E.2)
# ===========================================================================
# Deze tests draaien de async-varianten in een echte QThreadPool. Ze
# gebruiken een lokale _app() en wachten met processEvents() tot de
# specifieke callback is aangeroepen. De aanroeper is eigenaar van de
# worker; we bewaren de worker in _bewaarde_workers zodat de
# WorkerSignals blijft leven tot de callback is aangeroepen.

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


# Bewaar de async-workers tot het einde van de sessie. Zonder deze
# referentie kan de WorkerSignals worden opgeruimd voordat de callback
# is aangeroepen.
_bewaarde_workers: list = []


@pytest.fixture(scope="session", autouse=True)
def _ruim_workers_op_aan_einde():
    yield
    _bewaarde_workers.clear()


def _app():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def _wacht_op(conditie, timeout_s: float = 3.0, wat: str = "callback") -> None:
    """Laat de event loop draaien tot `conditie()` True teruggeeft."""
    app = _app()
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        app.processEvents()
        if conditie():
            return
        time.sleep(0.005)
    raise AssertionError(f"{wat} werd niet klaar binnen de timeout")


def test_fetch_url_metadata_async_gelukkig_pad(monkeypatch):
    _app()
    response = _FakeResponse(inhoud=_maak_html(titel="Async Titel"))
    _installeer_fake_get(monkeypatch, response)

    ontvangen: list[UrlMetadata] = []

    worker = url_fetch_module.fetch_url_metadata_async(
        "https://example.com/async",
        on_success=lambda meta: ontvangen.append(meta),
    )
    _bewaarde_workers.append(worker)
    _wacht_op(lambda: len(ontvangen) == 1, wat="on_success")

    meta = ontvangen[0]
    assert meta.url == "https://example.com/async"
    assert meta.title == "Async Titel"
    assert meta.http_status == 200


def test_fetch_url_metadata_async_roept_on_error(monkeypatch):
    _app()
    _installeer_fake_get(
        monkeypatch, requests.exceptions.Timeout("te langzaam")
    )

    fouten: list[tuple[str, str]] = []

    worker = url_fetch_module.fetch_url_metadata_async(
        "https://example.com/async",
        on_success=lambda meta: None,
        on_error=lambda kort, tb: fouten.append((kort, tb)),
    )
    _bewaarde_workers.append(worker)
    _wacht_op(lambda: len(fouten) == 1, wat="on_error")

    kort, tb = fouten[0]
    assert "UrlFetchError" in kort
    assert "timeout" in kort.lower()


def test_fetch_url_metadata_async_ongeldige_url_roept_on_error():
    _app()
    fouten: list[tuple[str, str]] = []

    worker = url_fetch_module.fetch_url_metadata_async(
        "",
        on_success=lambda meta: None,
        on_error=lambda kort, tb: fouten.append((kort, tb)),
    )
    _bewaarde_workers.append(worker)
    _wacht_op(lambda: len(fouten) == 1, wat="on_error")

    assert "UrlFetchError" in fouten[0][0]


def test_fetch_url_content_async_gelukkig_pad(monkeypatch):
    _app()
    html = _maak_html(titel="Async Inhoud")
    _installeer_fake_get(monkeypatch, _FakeResponse(inhoud=html))

    ontvangen: list[str] = []

    worker = url_fetch_module.fetch_url_content_async(
        "https://example.com/content",
        on_success=lambda tekst: ontvangen.append(tekst),
    )
    _bewaarde_workers.append(worker)
    _wacht_op(lambda: len(ontvangen) == 1, wat="on_success")

    assert "Async Inhoud" in ontvangen[0]
    assert ontvangen[0].startswith("<!DOCTYPE html>")


def test_fetch_url_content_async_roept_on_error(monkeypatch):
    _app()
    _installeer_fake_get(
        monkeypatch, requests.exceptions.ConnectionError("DNS faalde")
    )

    fouten: list[tuple[str, str]] = []

    worker = url_fetch_module.fetch_url_content_async(
        "https://example.com/content",
        on_success=lambda tekst: None,
        on_error=lambda kort, tb: fouten.append((kort, tb)),
    )
    _bewaarde_workers.append(worker)
    _wacht_op(lambda: len(fouten) == 1, wat="on_error")

    kort, tb = fouten[0]
    assert "UrlFetchError" in kort
    assert "verbinding" in kort.lower()


def test_fetch_url_metadata_async_zonder_on_error_werkt(monkeypatch):
    """on_error is optioneel. Bij succes wordt on_success gewoon
    aangeroepen."""
    _app()
    response = _FakeResponse(inhoud=_maak_html(titel="Zonder Fout"))
    _installeer_fake_get(monkeypatch, response)

    ontvangen: list[UrlMetadata] = []

    worker = url_fetch_module.fetch_url_metadata_async(
        "https://example.com/ok",
        on_success=lambda meta: ontvangen.append(meta),
    )
    _bewaarde_workers.append(worker)
    _wacht_op(lambda: len(ontvangen) == 1, wat="on_success")

    assert ontvangen[0].title == "Zonder Fout"