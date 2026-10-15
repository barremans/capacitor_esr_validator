"""
================================================================================
Module:     tests/test_updater.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-15
Auteur:     Bart Bossuyt

Doel:       Regressietests voor app/helpers/updater.py (fase 9H).
            Puur: geen Qt, geen echte netwerkcall. requests.get wordt
            gemonkeypatcht.

Wijzigingen:
  v1.0.0 (2026-10-14)  Fase 9H. Eerste versie.
  v1.1.0 (2026-10-15)  Fase 9H-afronding: tests voor fetch_release_notes()
                        (GitHub Releases API).
================================================================================
"""

from __future__ import annotations

import pytest
import requests

from app.helpers import updater


# ---------------------------------------------------------------------------
# parse_version_file
# ---------------------------------------------------------------------------
def test_parse_version_file_met_url():
    version, url = updater.parse_version_file(
        "1.0.4\nhttps://example.com/setup.exe\n"
    )
    assert version == "1.0.4"
    assert url == "https://example.com/setup.exe"


def test_parse_version_file_zonder_url():
    version, url = updater.parse_version_file("1.0.4\n")
    assert version == "1.0.4"
    assert url is None


def test_parse_version_file_stript_v_prefix():
    version, _ = updater.parse_version_file("v1.0.4\n")
    assert version == "1.0.4"


def test_parse_version_file_negeert_lege_regels():
    version, url = updater.parse_version_file(
        "\n\n1.0.4\n\nhttps://example.com/setup.exe\n\n"
    )
    assert version == "1.0.4"
    assert url == "https://example.com/setup.exe"


def test_parse_version_file_leeg_werpt_valueerror():
    with pytest.raises(ValueError):
        updater.parse_version_file("")


def test_parse_version_file_tweede_regel_geen_url():
    version, url = updater.parse_version_file("1.0.4\ngeen url hier\n")
    assert version == "1.0.4"
    assert url is None


# ---------------------------------------------------------------------------
# _is_newer
# ---------------------------------------------------------------------------
def test_is_newer_hoger():
    assert updater._is_newer("1.0.5", "1.0.4") is True


def test_is_newer_gelijk():
    assert updater._is_newer("1.0.4", "1.0.4") is False


def test_is_newer_lager():
    assert updater._is_newer("1.0.3", "1.0.4") is False


def test_is_newer_minor():
    assert updater._is_newer("1.1.0", "1.0.99") is True


def test_is_newer_major():
    assert updater._is_newer("2.0.0", "1.99.99") is True


def test_is_newer_ongeldig_werpt_valueerror():
    with pytest.raises(ValueError):
        updater._is_newer("geen-versie", "1.0.4")


# ---------------------------------------------------------------------------
# _asset_url
# ---------------------------------------------------------------------------
def test_asset_url_formaat():
    url = updater._asset_url("1.0.4")
    assert url == (
        "https://github.com/barremans/capacitor_esr_validator/"
        "releases/download/v1.0.4/ESR_TesterSetup_1.0.4.exe"
    )


# ---------------------------------------------------------------------------
# check_for_update — met monkeypatch op fetch_version_txt
# ---------------------------------------------------------------------------
def test_check_for_update_uitkomst_nieuwer(monkeypatch):
    monkeypatch.setattr(
        updater,
        "fetch_version_txt",
        lambda timeout=5: "1.0.5\nhttps://example.com/setup_1.0.5.exe\n",
    )
    info = updater.check_for_update("1.0.4")
    assert info.is_newer is True
    assert info.current_version == "1.0.4"
    assert info.remote_version == "1.0.5"
    assert info.download_url == "https://example.com/setup_1.0.5.exe"


def test_check_for_update_uitkomst_gelijk(monkeypatch):
    monkeypatch.setattr(
        updater,
        "fetch_version_txt",
        lambda timeout=5: "1.0.4\nhttps://example.com/setup_1.0.4.exe\n",
    )
    info = updater.check_for_update("1.0.4")
    assert info.is_newer is False
    assert info.remote_version == "1.0.4"


def test_check_for_update_zonder_url_gebruikt_asset_url(monkeypatch):
    monkeypatch.setattr(
        updater,
        "fetch_version_txt",
        lambda timeout=5: "1.0.5\n",
    )
    info = updater.check_for_update("1.0.4")
    assert info.is_newer is True
    assert info.download_url == updater._asset_url("1.0.5")


def test_check_for_update_netwerkfout_geeft_geen_update(monkeypatch):
    def _raise(timeout=5):
        raise requests.ConnectionError("geen netwerk")

    monkeypatch.setattr(updater, "fetch_version_txt", _raise)
    info = updater.check_for_update("1.0.4")
    assert info.is_newer is False
    assert info.remote_version == "1.0.4"
    assert info.download_url is None


def test_check_for_update_ongeldige_remote_versie(monkeypatch):
    monkeypatch.setattr(
        updater,
        "fetch_version_txt",
        lambda timeout=5: "geen-versie\n",
    )
    info = updater.check_for_update("1.0.4")
    assert info.is_newer is False
    assert info.remote_version == "1.0.4"


# ---------------------------------------------------------------------------
# fetch_version_txt — raw lukt
# ---------------------------------------------------------------------------
class _FakeResponse:
    def __init__(self, ok: bool, text: str, status_code: int = 200):
        self.ok = ok
        self.text = text
        self.status_code = status_code


def test_fetch_version_txt_raw_lukt(monkeypatch):
    def _fake_get(url, headers=None, timeout=None):
        return _FakeResponse(True, "1.0.5\nhttps://example.com/setup.exe\n")

    monkeypatch.setattr(updater.requests, "get", _fake_get)
    txt = updater.fetch_version_txt()
    assert "1.0.5" in txt


def test_fetch_version_txt_raw_faalt_contents_lukt(monkeypatch):
    calls = {"n": 0}

    def _fake_get(url, headers=None, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return _FakeResponse(False, "", status_code=404)
        return _FakeResponse(True, "1.0.5\n")

    monkeypatch.setattr(updater.requests, "get", _fake_get)
    txt = updater.fetch_version_txt()
    assert txt.strip() == "1.0.5"
    assert calls["n"] == 2


def test_fetch_version_txt_beide_falen_werpt_httperror(monkeypatch):
    def _fake_get(url, headers=None, timeout=None):
        return _FakeResponse(False, "nope", status_code=500)

    monkeypatch.setattr(updater.requests, "get", _fake_get)
    with pytest.raises(requests.HTTPError):
        updater.fetch_version_txt()


def test_fetch_version_txt_raw_exception_contents_lukt(monkeypatch):
    calls = {"n": 0}

    def _fake_get(url, headers=None, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise requests.ConnectionError("raw kapot")
        return _FakeResponse(True, "1.0.5\n")

    monkeypatch.setattr(updater.requests, "get", _fake_get)
    txt = updater.fetch_version_txt()
    assert txt.strip() == "1.0.5"


# ---------------------------------------------------------------------------
# v1.1.0 — fetch_release_notes (fase 9H-afronding)
# ---------------------------------------------------------------------------
class _FakeJsonResponse:
    """Response met een .json()-methode voor de Releases API."""

    def __init__(self, ok: bool, data: dict | None = None,
                 status_code: int = 200, text: str = ""):
        self.ok = ok
        self._data = data or {}
        self.status_code = status_code
        self.text = text

    def json(self):
        return self._data


def test_fetch_release_notes_geeft_tag_body_url(monkeypatch):
    data = {
        "tag_name": "v1.1.0",
        "body": "## Nieuwe functies\n\n- Update-check\n",
        "html_url": (
            "https://github.com/barremans/capacitor_esr_validator/"
            "releases/tag/v1.1.0"
        ),
    }

    def _fake_get(url, headers=None, timeout=None):
        return _FakeJsonResponse(True, data)

    monkeypatch.setattr(updater.requests, "get", _fake_get)
    notes = updater.fetch_release_notes()
    assert notes["tag_name"] == "v1.1.0"
    assert "Update-check" in notes["body"]
    assert notes["html_url"].endswith("/v1.1.0")


def test_fetch_release_notes_lege_body_wordt_leeg(monkeypatch):
    data = {"tag_name": "v1.1.0", "body": None, "html_url": "https://x"}

    monkeypatch.setattr(
        updater.requests, "get",
        lambda *a, **k: _FakeJsonResponse(True, data),
    )
    notes = updater.fetch_release_notes()
    assert notes["body"] == ""


def test_fetch_release_notes_ontbrekende_html_url_gebruikt_fallback(monkeypatch):
    data = {"tag_name": "v1.1.0", "body": "x"}

    monkeypatch.setattr(
        updater.requests, "get",
        lambda *a, **k: _FakeJsonResponse(True, data),
    )
    notes = updater.fetch_release_notes()
    assert "/releases/latest" in notes["html_url"]


def test_fetch_release_notes_http_fout_werpt_httperror(monkeypatch):
    def _fake_get(url, headers=None, timeout=None):
        return _FakeJsonResponse(False, status_code=404, text="not found")

    monkeypatch.setattr(updater.requests, "get", _fake_get)
    with pytest.raises(requests.HTTPError):
        updater.fetch_release_notes()


def test_fetch_release_notes_netwerkfout_werpt_requestexception(monkeypatch):
    def _raise(*a, **k):
        raise requests.ConnectionError("geen netwerk")

    monkeypatch.setattr(updater.requests, "get", _raise)
    with pytest.raises(requests.ConnectionError):
        updater.fetch_release_notes()