"""
================================================================================
Module:     app/helpers/i18n.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.1.0
Datum:      2026-08-12
Auteur:     Ontwikkelaar

Doel:       Eenvoudige vertaalmodule. Leest JSON-vertaalbestanden uit
            i18n/locales/<taalcode>.json.

Wijzigingen:
  v1.0.0 (2026-08-11)  Initiele versie.
  v1.0.1 (2026-08-12)  Robuustere pad-detectie.
  v1.0.2 (2026-08-12)  Pad berekend vanuit projectroot via sys.path.
  v1.1.0 (2026-08-12)  Extra fallback voor PyInstaller; betere foutmeldingen.
================================================================================
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _bepaal_i18n_root() -> Path:
    """Bepaalt het pad naar i18n/locales/ op basis van de projectroot."""
    # Strategie 1: gebruik sys.path[0] (toegevoegd door main.py)
    if sys.path and len(sys.path) > 0:
        for p in sys.path:
            candidate = Path(p) / "i18n" / "locales"
            if candidate.exists() and candidate.is_dir():
                return candidate

    # Strategie 2: relatief aan dit bestand (3 niveaus omhoog)
    candidate = Path(__file__).resolve().parent.parent.parent / "i18n" / "locales"
    if candidate.exists():
        return candidate

    # Strategie 3: relatief aan de huidige working directory
    candidate = Path.cwd() / "i18n" / "locales"
    if candidate.exists():
        return candidate

    # Strategie 4: zoek omhoog vanaf cwd
    current = Path.cwd()
    for _ in range(5):
        candidate = current / "i18n" / "locales"
        if candidate.exists():
            return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent

    # Strategie 5: PyInstaller-bundles (sys.executable is de .exe)
    candidate = Path(sys.executable).parent / "i18n" / "locales"
    if candidate.exists():
        return candidate

    # Fallback: relatief aan dit bestand
    return Path(__file__).resolve().parent.parent.parent / "i18n" / "locales"


I18N_ROOT = _bepaal_i18n_root()
STANDAARD_TAAL = "nl_NL"

_cache: dict[str, dict[str, str]] = {}


def _plat_maken(data: dict, prefix: str = "") -> dict[str, str]:
    """Zet een geneste JSON-structuur om naar platte 'a.b.c'-sleutels."""
    resultaat: dict[str, str] = {}
    for key, value in data.items():
        volledige_sleutel = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            resultaat.update(_plat_maken(value, volledige_sleutel))
        else:
            resultaat[volledige_sleutel] = value
    return resultaat


def _laad_taalbestand(taalcode: str) -> dict[str, str]:
    if taalcode in _cache:
        return _cache[taalcode]

    pad = I18N_ROOT / f"{taalcode}.json"

    if not pad.exists():
        print(f"[i18n WAARSCHUWING] Vertaalbestand niet gevonden: {pad}", file=sys.stderr)
        print(f"[i18n WAARSCHUWING] I18N_ROOT = {I18N_ROOT}", file=sys.stderr)
        print(f"[i18n WAARSCHUWING] sys.path[0] = {sys.path[0] if sys.path else 'leeg'}", file=sys.stderr)
        print(f"[i18n WAARSCHUWING] cwd = {Path.cwd()}", file=sys.stderr)
        raise FileNotFoundError(f"Vertaalbestand niet gevonden: {pad}")

    with pad.open("r", encoding="utf-8") as bestand:
        ruwe_data = json.load(bestand)

    zonder_commentaar = {k: v for k, v in ruwe_data.items() if not k.startswith("_")}
    platte_data = _plat_maken(zonder_commentaar)
    _cache[taalcode] = platte_data
    return platte_data


def beschikbare_talen() -> list[str]:
    """Geeft de taalcodes terug van alle JSON-bestanden in i18n/locales/."""
    if not I18N_ROOT.exists():
        return []
    return sorted(pad.stem for pad in I18N_ROOT.glob("*.json"))


def wis_cache() -> None:
    """Enkel nuttig voor tests: forceert een herinlezing van de taalbestanden."""
    _cache.clear()


def vertaal(sleutel: str, taal: str = STANDAARD_TAAL, **interpolatie: Any) -> str:
    """Vertaalt `sleutel` naar `taal`, met optionele interpolatiewaarden.

    Valt terug op de standaardtaal (nl_NL) als de sleutel ontbreekt in de
    gevraagde taal, en op de sleutel zelf als ook dat ontbreekt.
    """
    try:
        vertalingen = _laad_taalbestand(taal)
    except FileNotFoundError:
        return sleutel

    sjabloon = vertalingen.get(sleutel)

    if sjabloon is None and taal != STANDAARD_TAAL:
        try:
            vertalingen_standaard = _laad_taalbestand(STANDAARD_TAAL)
            sjabloon = vertalingen_standaard.get(sleutel)
        except FileNotFoundError:
            pass

    if sjabloon is None:
        return sleutel

    try:
        return sjabloon.format(**interpolatie)
    except (KeyError, IndexError):
        return sjabloon


# Korte, gangbare alias.
t = vertaal