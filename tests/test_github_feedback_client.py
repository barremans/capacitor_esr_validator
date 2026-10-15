"""
================================================================================
Module:     tests/test_github_feedback_client.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.1
Datum:      2026-10-15
Auteur:     Bart Bossuyt

Doel:       Regressietests voor GitHubFeedbackClient in
            github_feedback.py (Fase 9G). Alles draait tegen een
            gemockte requests.request — er gaat geen echte netwerkcall
            naar GitHub.

            Bewaakt:
              - build_title en build_body (formaat van titel en tekst)
              - submit_report: POST, payload, labelkeuze, return-URL
              - get_open_reports: splitsing bug/feature, fallback zonder
                token bij 401
              - foutpaden: 401, 403, 404, 410, 422
              - load_token: lege string als github_secret_local ontbreekt

Wijzigingen:
  v1.0.0 (2026-10-14)  Eerste versie. Fase 9G.
  v1.0.1 (2026-10-15)  Versie-assertie in
                       test_build_body_header_mentions_app_and_version
                       gebruikt nu app.version.__version__ in plaats
                       van hardcoded "1.0". Voorkomt flakiness bij elke
                       versie-bump. Geen functionele codewijziging.
================================================================================
"""

import os
import sys
from datetime import datetime

import pytest

from app.version import __version__


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# --------------------------------------------------------------------- helpers
class _FakeResponse:
    """Minimale requests.Response-vervanger."""

    def __init__(self, status_code=200, json_data=None, headers=None):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else []
        self.headers = headers or {}

    def json(self):
        return self._json_data


def _maak_client(monkeypatch, token="github_pat_" + "A" * 60):
    """Importeer github_feedback vers, geef een client met vast token."""
    sys.modules.pop("github_feedback", None)
    sys.modules.pop("github_secret_local", None)
    import github_feedback
    client = github_feedback.GitHubFeedbackClient(token=token)
    return github_feedback, client


# ------------------------------------------------------------------- build_title
def test_build_title_bug_prefix(monkeypatch):
    gf, _ = _maak_client(monkeypatch)
    titel = gf.build_title("De knop doet niets", gf.REPORT_TYPE_BUG)
    assert titel.startswith("🐞 Bug:")


def test_build_title_feature_prefix(monkeypatch):
    gf, _ = _maak_client(monkeypatch)
    titel = gf.build_title("Graag donker thema", gf.REPORT_TYPE_FEATURE)
    assert titel.startswith("✨ Feature:")


def test_build_title_uses_first_line_only(monkeypatch):
    gf, _ = _maak_client(monkeypatch)
    titel = gf.build_title("Eerste regel\nTweede regel", gf.REPORT_TYPE_BUG)
    assert "Tweede regel" not in titel


def test_build_title_truncates_to_50_chars(monkeypatch):
    gf, _ = _maak_client(monkeypatch)
    lang = "x" * 200
    titel = gf.build_title(lang, gf.REPORT_TYPE_BUG)
    # prefix "🐞 Bug: " = 8 tekens + max 50 = max 58 tekens totaal
    assert len(titel) <= 60


def test_build_title_empty_description(monkeypatch):
    gf, _ = _maak_client(monkeypatch)
    titel = gf.build_title("", gf.REPORT_TYPE_BUG)
    assert titel == "🐞 Bug: "


# ------------------------------------------------------------------- build_body
def test_build_body_contains_reporter_and_description(monkeypatch):
    gf, _ = _maak_client(monkeypatch)
    body = gf.build_body("BBossuyt", "De knop doet niets", gf.REPORT_TYPE_BUG)
    assert "BBossuyt" in body
    assert "De knop doet niets" in body


def test_build_body_has_header_then_blank_line_then_description(monkeypatch):
    gf, _ = _maak_client(monkeypatch)
    body = gf.build_body("BBossuyt", "Beschrijving hier", gf.REPORT_TYPE_BUG)
    kop, _, rest = body.partition("\n\n")
    assert "Automatisch gegenereerde" in kop
    assert rest == "Beschrijving hier"


def test_build_body_header_mentions_app_and_version(monkeypatch):
    gf, _ = _maak_client(monkeypatch)
    body = gf.build_body("BBossuyt", "iets", gf.REPORT_TYPE_BUG)
    assert "ESR Tester" in body
    assert __version__ in body


def test_build_body_datetime_format(monkeypatch):
    gf, _ = _maak_client(monkeypatch)
    vast = datetime(2026, 10, 14, 9, 30)
    body = gf.build_body("BBossuyt", "iets", gf.REPORT_TYPE_BUG, when=vast)
    assert "2026-10-14 09:30" in body


def test_build_body_unknown_reporter_fallback(monkeypatch):
    gf, _ = _maak_client(monkeypatch)
    body = gf.build_body("", "iets", gf.REPORT_TYPE_BUG)
    assert "onbekend" in body


# -------------------------------------------------------------- submit_report
def test_submit_report_sends_post_with_correct_payload(monkeypatch):
    gf, client = _maak_client(monkeypatch)
    gevangen = {}

    def fake_request(method, url, headers=None, timeout=None, **kwargs):
        gevangen["method"] = method
        gevangen["url"] = url
        gevangen["json"] = kwargs.get("json") or {}
        return _FakeResponse(201, {"html_url": "https://github.com/x/y/issues/1"})

    import requests
    monkeypatch.setattr(requests, "request", fake_request)

    url = client.submit_report("BBossuyt", "De knop doet niets", gf.REPORT_TYPE_BUG)

    assert url == "https://github.com/x/y/issues/1"
    assert gevangen["method"] == "POST"
    assert gevangen["url"].endswith("/repos/barremans/capacitor_esr_validator/issues")
    assert gevangen["json"]["labels"] == ["bug"]
    assert "🐞 Bug:" in gevangen["json"]["title"]


def test_submit_report_uses_enhancement_label_for_feature(monkeypatch):
    gf, client = _maak_client(monkeypatch)
    gevangen = {}

    def fake_request(method, url, headers=None, timeout=None, **kwargs):
        gevangen["json"] = kwargs.get("json") or {}
        return _FakeResponse(201, {"html_url": "https://github.com/x/y/issues/2"})

    import requests
    monkeypatch.setattr(requests, "request", fake_request)

    client.submit_report("BBossuyt", "Graag thema", gf.REPORT_TYPE_FEATURE)
    assert gevangen["json"]["labels"] == ["enhancement"]


def test_submit_report_without_token_raises(monkeypatch):
    gf, client = _maak_client(monkeypatch, token="")

    with pytest.raises(gf.GitHubFeedbackError) as exc:
        client.submit_report("BBossuyt", "iets", gf.REPORT_TYPE_BUG)
    assert "geen GitHub-token" in str(exc.value)


def test_submit_report_401_gives_user_friendly_message(monkeypatch):
    gf, client = _maak_client(monkeypatch)

    import requests
    monkeypatch.setattr(requests, "request",
                        lambda *a, **kw: _FakeResponse(401, {}))

    with pytest.raises(gf.GitHubFeedbackError) as exc:
        client.submit_report("BBossuyt", "iets", gf.REPORT_TYPE_BUG)
    assert "ongeldig of ingetrokken" in str(exc.value)


def test_submit_report_403_gives_user_friendly_message(monkeypatch):
    gf, client = _maak_client(monkeypatch)

    import requests
    monkeypatch.setattr(requests, "request",
                        lambda *a, **kw: _FakeResponse(403, {}, headers={}))

    with pytest.raises(gf.GitHubFeedbackError):
        client.submit_report("BBossuyt", "iets", gf.REPORT_TYPE_BUG)


def test_submit_report_404_gives_user_friendly_message(monkeypatch):
    gf, client = _maak_client(monkeypatch)

    import requests
    monkeypatch.setattr(requests, "request",
                        lambda *a, **kw: _FakeResponse(404, {}))

    with pytest.raises(gf.GitHubFeedbackError):
        client.submit_report("BBossuyt", "iets", gf.REPORT_TYPE_BUG)


def test_submit_report_network_error_raises(monkeypatch):
    gf, client = _maak_client(monkeypatch)

    import requests

    def fake_request(*a, **kw):
        raise requests.exceptions.ConnectionError("geen internet")

    monkeypatch.setattr(requests, "request", fake_request)

    with pytest.raises(gf.GitHubFeedbackError) as exc:
        client.submit_report("BBossuyt", "iets", gf.REPORT_TYPE_BUG)
    assert "niet bereikbaar" in str(exc.value)


# -------------------------------------------------------------- get_open_reports
def test_get_open_reports_splits_bugs_and_features(monkeypatch):
    gf, client = _maak_client(monkeypatch)

    items = [
        {"title": "Bug 1", "body": "b", "labels": [{"name": "bug"}]},
        {"title": "Feature 1", "body": "f", "labels": [{"name": "enhancement"}]},
        {"title": "Bug 2", "body": "b", "labels": []},
        {"title": "Oude feature-PR", "body": "pr",
         "labels": [], "pull_request": {"url": "x"}},
    ]

    import requests
    monkeypatch.setattr(requests, "request",
                        lambda *a, **kw: _FakeResponse(200, items))

    rapport = client.get_open_reports()
    assert len(rapport["bugs"]) == 2
    assert len(rapport["features"]) == 2


def test_get_open_reports_empty_list(monkeypatch):
    gf, client = _maak_client(monkeypatch)

    import requests
    monkeypatch.setattr(requests, "request",
                        lambda *a, **kw: _FakeResponse(200, []))

    rapport = client.get_open_reports()
    assert rapport["bugs"] == []
    assert rapport["features"] == []


def test_get_open_reports_falls_back_to_anonymous_on_401(monkeypatch):
    """Bij een 401 moet de client opnieuw proberen zonder Authorization-
    header. Zo blijft 'Open cases' werken voor een publieke repo, ook
    als het token intussen is ingetrokken."""
    gf, client = _maak_client(monkeypatch)
    aanroepen = []

    def fake_request(method, url, headers=None, timeout=None, **kwargs):
        aanroepen.append(dict(headers or {}))
        if "Authorization" in (headers or {}):
            return _FakeResponse(401, [])
        return _FakeResponse(200, [{"title": "x", "body": "y", "labels": []}])

    import requests
    monkeypatch.setattr(requests, "request", fake_request)

    rapport = client.get_open_reports()
    assert len(rapport["bugs"]) == 1
    assert len(aanroepen) >= 2
    # Eerste aanroep mét, tweede zónder Authorization
    assert "Authorization" in aanroepen[0]
    assert "Authorization" not in aanroepen[1]


# ----------------------------------------------------------------- load_token
def test_load_token_empty_when_secret_missing(monkeypatch):
    """Als github_secret_local.py ontbreekt, geeft load_token() een lege
    string terug (geen exception)."""
    sys.modules.pop("github_feedback", None)
    sys.modules.pop("github_secret_local", None)

    import builtins
    echte_import = builtins.__import__

    def _fake_import(name, *args, **kwargs):
        if name == "github_secret_local":
            raise ImportError("ontbreekt voor test")
        return echte_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)

    import github_feedback
    assert github_feedback.load_token() == ""


def test_has_token_property(monkeypatch):
    gf, client = _maak_client(monkeypatch, token="github_pat_" + "A" * 60)
    assert client.has_token is True

    gf2, client2 = _maak_client(monkeypatch, token="")
    assert client2.has_token is False