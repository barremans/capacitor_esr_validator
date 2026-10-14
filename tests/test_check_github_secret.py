"""
================================================================================
Module:     tests/test_check_github_secret.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.1
Datum:      2026-10-14
Auteur:     Bart Bossuyt

Doel:       Regressietests voor check_github_secret.py (Fase 9G).
            Elke test draait in een eigen tijdelijke map met een eigen
            git init, zodat de echte repo niet geraakt wordt.

            BELANGRIJK: check_github_secret.py bepaalt ROOT via
            os.path.dirname(os.path.abspath(__file__)) — dat is de map
            waar het script staat, niet de CWD. Daarom kopiëren we het
            script naar de tijdelijke map vóór we het uitvoeren. Anders
            keek de test naar de echte repo in plaats van naar tmp_path.

            Bewaakt:
              - de .gitignore-regel *_secret_local.py
              - de detectie van een token in getrackte bestanden
              - de detectie van een token in een nog niet gepushte commit
              - het --skip-token-pad (zonder token, enkel de git-controles)
              - het --skip-online-pad (token niet online testen)
              - het lege-token-pad
              - het ontbrekende-bestand-pad

Wijzigingen:
  v1.0.1 (2026-10-14)  Fix: _run_check kopieert check_github_secret.py
                       naar de tijdelijke map en voert het daar uit.
                       Zonder deze fix gebruikte het script ROOT = de map
                       van het originele script (de echte repo), niet de
                       testmap. Daardoor zagen alle tests de echte repo
                       en niet de nep-repo in tmp_path.
  v1.0.0 (2026-10-14)  Eerste versie. Fase 9G.
================================================================================
"""

import os
import shutil
import subprocess
import sys

import pytest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK_SCRIPT = os.path.join(PROJECT_ROOT, "check_github_secret.py")


# --------------------------------------------------------------------- helpers
def _git(cwd, *args):
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True,
        encoding="utf-8", errors="replace"
    )


def _init_repo(tmp_path):
    """Zet een minimale git-repo op met user.name/user.email."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.name", "Test")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "checkout", "-q", "-b", "main")


def _run_check(tmp_path, *extra):
    """Kopieer check_github_secret.py naar tmp_path en voer het daar uit.

    Het script bepaalt ROOT via __file__, dus het moet in de map staan
    waar het naar moet kijken — anders kijkt het naar de echte repo.
    """
    script_in_tmp = tmp_path / "check_github_secret.py"
    shutil.copyfile(CHECK_SCRIPT, script_in_tmp)
    return subprocess.run(
        [sys.executable, str(script_in_tmp), *extra],
        cwd=tmp_path, capture_output=True, text=True,
        encoding="utf-8", errors="replace"
    )


def _maak_config(tmp_path):
    (tmp_path / "github_feedback_config.py").write_text(
        'APP_NAME = "Test"\n'
        'GITHUB_OWNER = "barremans"\n'
        'GITHUB_REPO = "test_repo"\n',
        encoding="utf-8",
    )


# ------------------------------------------------------------------ testgevallen
def test_skip_token_zonder_gitignore_regel_faalt(tmp_path):
    """Zonder *_secret_local.py in .gitignore moet de controle falen."""
    _init_repo(tmp_path)
    _maak_config(tmp_path)
    (tmp_path / ".gitignore").write_text("# leeg\n", encoding="utf-8")

    result = _run_check(tmp_path, "--skip-token")
    assert result.returncode == 1
    assert "staat NIET in .gitignore" in result.stdout


def test_skip_token_met_gitignore_regel_slaagt(tmp_path):
    """Met *_secret_local.py in .gitignore én geen token in git: in orde."""
    _init_repo(tmp_path)
    _maak_config(tmp_path)
    (tmp_path / ".gitignore").write_text(
        "*_secret_local.py\n", encoding="utf-8"
    )
    _git(tmp_path, "add", ".gitignore", "github_feedback_config.py")
    _git(tmp_path, "commit", "-q", "-m", "init")

    result = _run_check(tmp_path, "--skip-token")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "RESULTAAT: in orde" in result.stdout


def test_skip_token_detecteert_token_in_getrackt_bestand(tmp_path):
    """Een klassiek token in een getrackt bestand moet gedetecteerd worden."""
    _init_repo(tmp_path)
    _maak_config(tmp_path)
    (tmp_path / ".gitignore").write_text(
        "*_secret_local.py\n", encoding="utf-8"
    )
    (tmp_path / "verdacht.py").write_text(
        'TOKEN = "ghp_' + "A" * 40 + '"\n', encoding="utf-8"
    )
    _git(tmp_path, "add", ".gitignore", "github_feedback_config.py", "verdacht.py")
    _git(tmp_path, "commit", "-q", "-m", "init")

    result = _run_check(tmp_path, "--skip-token")
    assert result.returncode == 1
    assert "Token gevonden" in result.stdout
    # Volledig token mag nooit in de output staan
    assert "ghp_" + "A" * 40 not in result.stdout


def test_skip_token_detecteert_fine_grained_token(tmp_path):
    _init_repo(tmp_path)
    _maak_config(tmp_path)
    (tmp_path / ".gitignore").write_text(
        "*_secret_local.py\n", encoding="utf-8"
    )
    (tmp_path / "verdacht.py").write_text(
        'TOKEN = "github_pat_' + "A" * 60 + '"\n', encoding="utf-8"
    )
    _git(tmp_path, "add", ".gitignore", "github_feedback_config.py", "verdacht.py")
    _git(tmp_path, "commit", "-q", "-m", "init")

    result = _run_check(tmp_path, "--skip-token")
    assert result.returncode == 1
    assert "Token gevonden" in result.stdout


def test_skip_token_lege_commit_boodschap(tmp_path):
    """Met een schone repo en correcte gitignore: 'Geen nog niet gepushte
    commits' of 'Geen upstream-branch ingesteld'."""
    _init_repo(tmp_path)
    _maak_config(tmp_path)
    (tmp_path / ".gitignore").write_text(
        "*_secret_local.py\n", encoding="utf-8"
    )
    _git(tmp_path, "add", ".gitignore", "github_feedback_config.py")
    _git(tmp_path, "commit", "-q", "-m", "init")

    result = _run_check(tmp_path, "--skip-token")
    assert result.returncode == 0
    assert ("Geen nog niet gepushte commits" in result.stdout
            or "Geen upstream-branch ingesteld" in result.stdout)


def test_zonder_skip_token_en_zonder_secret_faalt(tmp_path):
    """Zonder github_secret_local.py moet de volledige controle falen."""
    _init_repo(tmp_path)
    _maak_config(tmp_path)
    (tmp_path / ".gitignore").write_text(
        "*_secret_local.py\n", encoding="utf-8"
    )
    _git(tmp_path, "add", ".gitignore", "github_feedback_config.py")
    _git(tmp_path, "commit", "-q", "-m", "init")

    result = _run_check(tmp_path, "--skip-online")
    assert result.returncode == 1
    assert "ontbreekt" in result.stdout


def test_leeg_token_faalt(tmp_path):
    """Een leeg GITHUB_TOKEN moet falen."""
    _init_repo(tmp_path)
    _maak_config(tmp_path)
    (tmp_path / ".gitignore").write_text(
        "*_secret_local.py\n", encoding="utf-8"
    )
    (tmp_path / "github_secret_local.py").write_text(
        'GITHUB_TOKEN = ""\n', encoding="utf-8"
    )
    _git(tmp_path, "add", ".gitignore", "github_feedback_config.py")
    _git(tmp_path, "commit", "-q", "-m", "init")

    result = _run_check(tmp_path, "--skip-online")
    assert result.returncode == 1
    assert "is leeg" in result.stdout


def test_verkeerd_token_formaat_faalt(tmp_path):
    """Een token dat niet op github_pat_ of ghp_ begint, moet falen."""
    _init_repo(tmp_path)
    _maak_config(tmp_path)
    (tmp_path / ".gitignore").write_text(
        "*_secret_local.py\n", encoding="utf-8"
    )
    (tmp_path / "github_secret_local.py").write_text(
        'GITHUB_TOKEN = "niet-een-token"\n', encoding="utf-8"
    )
    _git(tmp_path, "add", ".gitignore", "github_feedback_config.py")
    _git(tmp_path, "commit", "-q", "-m", "init")

    result = _run_check(tmp_path, "--skip-online")
    assert result.returncode == 1
    assert "ziet er niet uit als een GitHub-token" in result.stdout


def test_geldig_token_formaat_met_skip_online_slaagt(tmp_path):
    """Een geldig uitziend token met --skip-online: in orde."""
    _init_repo(tmp_path)
    _maak_config(tmp_path)
    (tmp_path / ".gitignore").write_text(
        "*_secret_local.py\n", encoding="utf-8"
    )
    (tmp_path / "github_secret_local.py").write_text(
        'GITHUB_TOKEN = "github_pat_' + "A" * 60 + '"\n', encoding="utf-8"
    )
    _git(tmp_path, "add", ".gitignore", "github_feedback_config.py")
    _git(tmp_path, "commit", "-q", "-m", "init")

    result = _run_check(tmp_path, "--skip-online")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "fine-grained token" in result.stdout
    assert "Online test overgeslagen" in result.stdout


def test_klassiek_token_geeft_waarschuwing_maar_slaagt(tmp_path):
    """Een klassiek ghp_-token is geldig van vorm, maar geeft een
    waarschuwing dat een fine-grained token veiliger is."""
    _init_repo(tmp_path)
    _maak_config(tmp_path)
    (tmp_path / ".gitignore").write_text(
        "*_secret_local.py\n", encoding="utf-8"
    )
    (tmp_path / "github_secret_local.py").write_text(
        'GITHUB_TOKEN = "ghp_' + "A" * 40 + '"\n', encoding="utf-8"
    )
    _git(tmp_path, "add", ".gitignore", "github_feedback_config.py")
    _git(tmp_path, "commit", "-q", "-m", "init")

    result = _run_check(tmp_path, "--skip-online")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "klassiek token" in result.stdout


def test_secret_bestand_in_repo_faalt(tmp_path):
    """Als github_secret_local.py per ongeluk getrackt wordt, moet de
    controle falen."""
    _init_repo(tmp_path)
    _maak_config(tmp_path)
    # Let op: .gitignore ZONDER de regel, en het bestand geforceerd tracken.
    (tmp_path / ".gitignore").write_text("# leeg\n", encoding="utf-8")
    (tmp_path / "github_secret_local.py").write_text(
        'GITHUB_TOKEN = ""\n', encoding="utf-8"
    )
    _git(tmp_path, "add", ".gitignore", "github_feedback_config.py")
    _git(tmp_path, "add", "-f", "github_secret_local.py")
    _git(tmp_path, "commit", "-q", "-m", "init")

    result = _run_check(tmp_path, "--skip-token")
    assert result.returncode == 1
    # Minstens één van beide fouten moet er staan
    assert ("NIET in .gitignore" in result.stdout
            or "wordt door git gevolgd" in result.stdout)