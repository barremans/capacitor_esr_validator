"""
================================================================================
Module:     app/helpers/dialog_start_directory.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-16
Auteur:     Bart Bossuyt

Doel:       GUI-onafhankelijke helper voor de beste startmap van QFileDialog-
            aanroepen en het onthouden van de laatst gebruikte map per
            categorie (export, import, rapport).

            De helper leest en schrijft uitsluitend via laad_instellingen /
            sla_instellingen_op. Er wordt geen Qt geïmporteerd en er wordt
            geen database aangeraakt.

            Categorieën en hun velden:
              - export  -> laatste_exportmap  -> standaard_exportmap
              - import  -> laatste_importmap  -> standaard_importmap
              - rapport -> laatste_rapportmap -> standaard_exportmap

            De helper faalt stil bij onleesbare of onbeschrijfelijke
            settings.json: het kiezen van een startmap is een gemaksfunctie,
            geen kernfunctionaliteit.

Wijzigingen:
  v1.0.0 (2026-10-16)  Fase 11A.3: eerste versie. Centraliseert de
                        startmap-logica die voorheen in history_screen,
                        analysis_screen, report_dialog en import_wizard
                        gedupliceerd stond.
================================================================================
"""

from __future__ import annotations

from dataclasses import replace as _dc_replace
from pathlib import Path
from typing import Literal

from app.config.settings import (
    AppInstellingen,
    laad_instellingen,
    sla_instellingen_op,
)


Categorie = Literal["export", "import", "rapport"]

_GELDIGE_CATEGORIEEN: frozenset[str] = frozenset({"export", "import", "rapport"})


def _valideer_categorie(categorie: str) -> None:
    if categorie not in _GELDIGE_CATEGORIEEN:
        raise ValueError(
            f"Onbekende categorie: {categorie!r}. "
            f"Verwacht: {sorted(_GELDIGE_CATEGORIEEN)}."
        )


def _laatste_veld(instellingen: AppInstellingen, categorie: Categorie) -> str:
    if categorie == "export":
        return instellingen.algemeen.laatste_exportmap
    if categorie == "import":
        return instellingen.algemeen.laatste_importmap
    return instellingen.algemeen.laatste_rapportmap


def _standaard_veld(instellingen: AppInstellingen, categorie: Categorie) -> str:
    if categorie == "import":
        return instellingen.algemeen.standaard_importmap
    # Voor export én rapport valt de standaard terug op standaard_exportmap.
    return instellingen.algemeen.standaard_exportmap


def _map_bestaat(pad: str) -> bool:
    """True als pad een bestaande map is; False bij leeg/ongeldig pad."""
    if not pad:
        return False
    try:
        return Path(pad).expanduser().is_dir()
    except (OSError, ValueError):
        return False


def beste_startmap(categorie: Categorie) -> Path | None:
    """Beste startmap voor een QFileDialog per categorie.

    Voorkeur:
      1. laatste_<categorie>map als die bestaat
      2. standaard_<categorie>map als die bestaat
      3. None (Qt's standaard startlocatie)

    Faalt stil bij onleesbare settings.json en geeft dan None terug.
    """
    _valideer_categorie(categorie)
    try:
        instellingen = laad_instellingen()
    except (OSError, ValueError):
        return None

    for kandidaat in (
        _laatste_veld(instellingen, categorie),
        _standaard_veld(instellingen, categorie),
    ):
        if _map_bestaat(kandidaat):
            return Path(kandidaat).expanduser()
    return None


def startpad_voor_bestand(categorie: Categorie, bestandsnaam: str) -> str:
    """Beste volledige startpad voor een opslaan-dialoog.

    Geeft <beste_startmap>/<bestandsnaam> terug als een geldige map
    gevonden is, anders de bestandsnaam alleen (Qt's standaard).
    """
    map_ = beste_startmap(categorie)
    if map_ is None:
        return bestandsnaam
    return str(map_ / bestandsnaam)


def onthoud_startmap(categorie: Categorie, pad: Path) -> None:
    """Onthoud de map van een bestand of map voor de gegeven categorie.

    pad mag een bestand of een map zijn; voor een bestand wordt de parent
    opgeslagen. Faalt stil bij schrijf- of leesfouten en bij eenzelfde
    waarde als de bestaande (geen onnodige schrijfactie).
    """
    _valideer_categorie(categorie)
    try:
        if pad.is_dir():
            nieuwe_map = str(pad)
        else:
            nieuwe_map = str(pad.parent)
    except (OSError, ValueError):
        return

    if not nieuwe_map:
        return

    try:
        instellingen = laad_instellingen()
    except (OSError, ValueError):
        return

    if _laatste_veld(instellingen, categorie) == nieuwe_map:
        return

    if categorie == "export":
        nieuwe_algemeen = _dc_replace(
            instellingen.algemeen, laatste_exportmap=nieuwe_map
        )
    elif categorie == "import":
        nieuwe_algemeen = _dc_replace(
            instellingen.algemeen, laatste_importmap=nieuwe_map
        )
    else:
        nieuwe_algemeen = _dc_replace(
            instellingen.algemeen, laatste_rapportmap=nieuwe_map
        )

    bijgewerkt = _dc_replace(instellingen, algemeen=nieuwe_algemeen)
    try:
        sla_instellingen_op(bijgewerkt)
    except (OSError, ValueError):
        pass