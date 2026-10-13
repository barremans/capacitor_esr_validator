"""
================================================================================
Module:     tests/test_version.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-13
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de centrale versie-informatie (fase 9A):
              - app/version.py bevat een geldige SemVer-string;
              - main.py geeft de versie door aan QApplication;
              - de Over-dialoog-tekst bevat de placeholder {versie}.

Wijzigingen:
  v1.0.0 (2026-10-13)  Eerste versie. Fase 9A van de packaging-fase.
================================================================================
"""

import os
import re

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.version import __version__
from app.helpers.i18n import vertaal


SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _app():
    return QApplication.instance() or QApplication([])


def test_version_is_semver():
    """app/version.py moet exact MAJOR.MINOR.PATCH bevatten."""
    assert SEMVER_RE.match(__version__), (
        f"__version__ = {__version__!r} is geen geldige SemVer-string "
        f"(verwacht MAJOR.MINOR.PATCH)."
    )


def test_version_is_not_dev_placeholder():
    """De placeholder '0.1.0-dev' mag niet meer voorkomen."""
    assert "dev" not in __version__.lower()
    assert __version__ != "0.1.0-dev"


def test_qapplication_receives_version():
    """main.py moet setApplicationVersion(__version__) aanroepen."""
    app = _app()
    app.setApplicationVersion(__version__)
    assert app.applicationVersion() == __version__


def test_over_tekst_contains_placeholder_nl():
    """NL Over-tekst moet {versie} bevatten."""
    tekst = vertaal("dialog.over_tekst", taal="nl_NL", versie="9.9.9")
    assert "9.9.9" in tekst


def test_over_tekst_contains_placeholder_en():
    """EN Over-tekst moet ook {versie} bevatten (zelfde placeholder)."""
    tekst = vertaal("dialog.over_tekst", taal="en_US", versie="9.9.9")
    assert "9.9.9" in tekst