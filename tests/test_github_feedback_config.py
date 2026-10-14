"""
================================================================================
Module:     tests/test_github_feedback_config.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-14
Auteur:     Bart Bossuyt

Doel:       Regressietests voor github_feedback_config.py (Fase 9G):
            de app-specifieke waarden (APP_NAME, GITHUB_OWNER,
            GITHUB_REPO) en de twee functies get_reporter_name() en
            get_app_version().

            Deze tests bewaken dat een latere wijziging aan de config
            niet stilzwijgend de verkeerde repo of een lege naam
            doorgeeft aan het feedbackpakket.

Wijzigingen:
  v1.0.0 (2026-10-14)  Eerste versie. Fase 9G.
================================================================================
"""

import importlib
import os
import sys

import pytest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def _fresh_config():
    """Importeer github_feedback_config opnieuw, zodat we zeker zijn dat
    we de echte module uit de projectroot gebruiken (niet een oude
    variant die toevallig al in sys.modules zit)."""
    sys.modules.pop("github_feedback_config", None)
    return importlib.import_module("github_feedback_config")


def test_app_name_is_esr_tester():
    cfg = _fresh_config()
    assert cfg.APP_NAME == "ESR Tester"


def test_github_owner():
    cfg = _fresh_config()
    assert cfg.GITHUB_OWNER == "barremans"


def test_github_repo():
    cfg = _fresh_config()
    assert cfg.GITHUB_REPO == "capacitor_esr_validator"


def test_owner_and_repo_not_empty():
    cfg = _fresh_config()
    assert cfg.GITHUB_OWNER.strip()
    assert cfg.GITHUB_REPO.strip()


def test_reporter_name_is_non_empty_string():
    """get_reporter_name() moet een string teruggeven. In deze app komt
    die via getpass.getuser(); op de build-/testmachine is dat altijd
    een niet-lege Windows-gebruikersnaam. Als dat ooit leeg terugkomt,
    blijft het veld in de BugDialog bewerkbaar — dat is acceptabel, maar
    het is nuttig om te weten dat het in deze omgeving niet leeg is."""
    cfg = _fresh_config()
    naam = cfg.get_reporter_name()
    assert isinstance(naam, str)
    # We verwachten op Windows een niet-lege naam; als dat niet zo is,
    # mag de test niet hard falen — de fallback in BugDialog vangt het op.
    if not naam:
        pytest.skip("getpass.getuser() gaf een lege naam op deze machine")


def test_reporter_name_has_no_surrounding_whitespace():
    cfg = _fresh_config()
    naam = cfg.get_reporter_name()
    if naam:
        assert naam == naam.strip()


def test_app_version_matches_version_module():
    cfg = _fresh_config()
    from app.version import __version__ as echte_versie
    assert cfg.get_app_version() == echte_versie


def test_app_version_is_semver_like():
    """Drie getallen, gescheiden door punten — dat formaat verwachten
    bump_version.py en publish.ps1 ook."""
    cfg = _fresh_config()
    versie = cfg.get_app_version()
    delen = versie.split(".")
    assert len(delen) == 3
    for d in delen:
        assert d.isdigit()


def test_get_app_version_falls_back_to_empty_on_import_error(monkeypatch):
    """Als app.version niet importeerbaar is, moet de functie een lege
    string teruggeven (geen exception). Dat is het contract met
    github_feedback.py, dat de versie optioneel in de kopregel zet."""
    cfg = _fresh_config()
    originele = sys.modules.pop("app.version", None)
    try:
        # Blokkeer app.version tijdelijk door een ImportError te forceren.
        import builtins
        echte_import = builtins.__import__

        def _fake_import(name, *args, **kwargs):
            if name == "app.version":
                raise ImportError("geblokkeerd voor test")
            return echte_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", _fake_import)
        assert cfg.get_app_version() == ""
    finally:
        if originele is not None:
            sys.modules["app.version"] = originele


def test_get_reporter_name_falls_back_to_empty_on_error(monkeypatch):
    """Als getpass.getuser() een fout geeft, moet de functie een lege
    string teruggeven (geen exception)."""
    cfg = _fresh_config()
    import getpass
    monkeypatch.setattr(getpass, "getuser", lambda: (_ for _ in ()).throw(RuntimeError("geen user")))
    assert cfg.get_reporter_name() == ""