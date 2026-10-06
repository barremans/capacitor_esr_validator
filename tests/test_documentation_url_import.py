"""
================================================================================
Module:     tests/test_documentation_url_import.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.1
Datum:      2026-10-06
Auteur:     Bart Bossuyt

Doel:       Regressietests voor url_import: gelukkig pad, titel-resolutie,
            foutpaden, optie B bij snapshot-fout.
            Netwerk en fetch worden gemockt.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie.
  v1.0.1 (2026-10-06)  SyntaxError hersteld: walrus-expressie in een
                        keyword-argument vervangen door een gewone variabele.
================================================================================
"""

from __future__ import annotations

from pathlib import Path

import pytest

import app.documentation.url_import as url_import_module
from app.documentation.import_models import ImportStatus
from app.documentation.import_service import ImportService
from app.documentation.url_fetch import UrlFetchError, UrlMetadata
from app.documentation.url_import import import_url


@pytest.fixture()
def service(tmp_path):
    return ImportService(catalog_path=tmp_path / "imported_catalog.json")


@pytest.fixture()
def snapshots_dir(tmp_path):
    return tmp_path / "snapshots"


def _fake_meta(
    url: str,
    *,
    titel: str = "Meta Titel",
    og_titel: str | None = None,
) -> UrlMetadata:
    return UrlMetadata(
        url=url,
        fetched_at=1_700_000_000_000,
        http_status=200,
        title=titel,
        description="Meta beschrijving",
        og_title=og_titel,
        og_description="OG beschrijving",
        language="nl",
        content_type="text/html",
    )


def _installeer_fake_fetch(
    monkeypatch, meta, html="<html><body>inhoud</body></html>"
):
    monkeypatch.setattr(
        url_import_module, "fetch_url_metadata", lambda url: meta
    )
    monkeypatch.setattr(
        url_import_module, "fetch_url_content", lambda url: html
    )


# ------------------------------------------------------------------ gelukkig pad

def test_import_url_gelukkig_pad(monkeypatch, service, snapshots_dir):
    _installeer_fake_fetch(
        monkeypatch,
        _fake_meta("https://example.com", titel="Meta Titel"),
    )

    result = import_url(
        "https://example.com",
        import_service=service,
        title="Expliciete titel",
        snapshots_dir=snapshots_dir,
    )

    assert result.changed is True
    assert result.source.status is ImportStatus.CONCEPT
    assert result.source.source_type.value == "url"
    assert result.source.source_url == "https://example.com"
    assert result.source.title == "Expliciete titel"
    assert result.source.original_filename is None
    assert result.source.file_hash is None

    snapshot = snapshots_dir / f"{result.source.source_id}.html"
    assert snapshot.exists()
    assert "inhoud" in snapshot.read_text(encoding="utf-8")


def test_titel_resolutie_expliciet_eerst(monkeypatch, service, snapshots_dir):
    _installeer_fake_fetch(
        monkeypatch, _fake_meta("https://x.com", titel="Meta", og_titel="OG")
    )
    result = import_url(
        "https://x.com",
        import_service=service,
        title="Expliciet",
        snapshots_dir=snapshots_dir,
    )
    assert result.source.title == "Expliciet"


def test_titel_resolutie_og_titel_tweede(monkeypatch, service, snapshots_dir):
    _installeer_fake_fetch(
        monkeypatch, _fake_meta("https://x.com", titel="Meta", og_titel="OG")
    )
    result = import_url(
        "https://x.com",
        import_service=service,
        snapshots_dir=snapshots_dir,
    )
    assert result.source.title == "OG"


def test_titel_resolutie_title_derde(monkeypatch, service, snapshots_dir):
    _installeer_fake_fetch(
        monkeypatch, _fake_meta("https://x.com", titel="Meta", og_titel=None)
    )
    result = import_url(
        "https://x.com",
        import_service=service,
        snapshots_dir=snapshots_dir,
    )
    assert result.source.title == "Meta"


def test_titel_resolutie_host_fallback(monkeypatch, service, snapshots_dir):
    _installeer_fake_fetch(
        monkeypatch,
        UrlMetadata(
            url="https://x.com",
            fetched_at=1,
            http_status=200,
            title=None,
            og_title=None,
        ),
    )
    result = import_url(
        "https://x.com",
        import_service=service,
        snapshots_dir=snapshots_dir,
    )
    assert result.source.title == "x.com"


# ------------------------------------------------------------------ foutpaden

def test_import_url_metadata_fout_propageert(monkeypatch, service, snapshots_dir):
    def _faal(url):
        raise UrlFetchError("netwerk kapot")

    monkeypatch.setattr(url_import_module, "fetch_url_metadata", _faal)

    with pytest.raises(UrlFetchError):
        import_url(
            "https://example.com",
            import_service=service,
            snapshots_dir=snapshots_dir,
        )
    # Geen registratie gebeurd
    assert service.list_sources() == []


def test_import_url_content_fout_propageert(monkeypatch, service, snapshots_dir):
    monkeypatch.setattr(
        url_import_module,
        "fetch_url_metadata",
        lambda url: _fake_meta(url),
    )

    def _faal(url):
        raise UrlFetchError("inhoud kapot")

    monkeypatch.setattr(url_import_module, "fetch_url_content", _faal)

    with pytest.raises(UrlFetchError):
        import_url(
            "https://example.com",
            import_service=service,
            snapshots_dir=snapshots_dir,
        )
    assert service.list_sources() == []


# ------------------------------------------------------------------ optie B

def test_snapshot_fout_behoudt_registratie(monkeypatch, service, snapshots_dir):
    _installeer_fake_fetch(monkeypatch, _fake_meta("https://example.com"))

    # Maak snapshots_dir onbruikbaar: een bestand waar een map moet komen.
    snapshots_dir.write_text("blokkerend bestand", encoding="utf-8")

    result = import_url(
        "https://example.com",
        import_service=service,
        snapshots_dir=snapshots_dir,
    )

    assert result.source.status is ImportStatus.CONCEPT
    assert result.message is not None
    assert "snapshot" in result.message.lower()
    assert result.source.notes is not None
    assert "snapshot" in result.source.notes.lower()

    # Bron is opvraagbaar
    opnieuw = service.get(result.source.source_id)
    assert opnieuw.notes is not None


def test_snapshot_fout_behoudt_bestaande_notes(monkeypatch, service, snapshots_dir):
    _installeer_fake_fetch(monkeypatch, _fake_meta("https://example.com"))
    snapshots_dir.write_text("blokkerend", encoding="utf-8")

    result = import_url(
        "https://example.com",
        import_service=service,
        snapshots_dir=snapshots_dir,
        notes="Belangrijke gebruikersnotitie",
    )

    assert "Belangrijke gebruikersnotitie" in result.source.notes
    assert "snapshot" in result.source.notes.lower()


# ------------------------------------------------------------------ idempotentie

def test_twee_keer_importeren_zelfde_url(monkeypatch, service, snapshots_dir):
    _installeer_fake_fetch(monkeypatch, _fake_meta("https://example.com"))

    tweede_snapshots = snapshots_dir.parent / "snapshots2"

    eerste = import_url(
        "https://example.com",
        import_service=service,
        snapshots_dir=snapshots_dir,
    )
    tweede = import_url(
        "https://example.com",
        import_service=service,
        snapshots_dir=tweede_snapshots,
    )

    assert eerste.source.source_id != tweede.source.source_id
    assert len(service.list_sources()) == 2