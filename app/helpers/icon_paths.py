"""
================================================================================
Module:     app/helpers/icon_paths.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-22
Auteur:     Bart Bossuyt

Doel:       GUI-onafhankelijke resolutie van het juiste icoonpad, met
            veilige fallback. Biedt zowel pure padfuncties (voor tests
            zonder Qt) als dunne Qt-wrappers (voor de GUI).

            Alle iconen staan in assets/icons/. De bestandsnamen zijn
            bewust in kleine letters, ook op Windows, zodat een clone
            op een case-sensitive bestandssysteem (Linux, macOS, CI)
            dezelfde bestanden vindt.

            Fallback-keten voor het applicatie-icoon:
              1. assets/icons/app.png   (Qt, hoge resolutie)
              2. assets/icons/logo.ico  (Qt, Windows-icoon)
              3. None                   (Qt gebruikt dan het standaardicoon)

            Voor thematische iconen (diagnose, esr, history, ...) geldt:
              1. assets/icons/<naam>.png
              2. None                   (de GUI laat het icoon dan weg)

Wijzigingen:
  v1.0.0 (2026-10-16)  Eerste versie (fase 11C). Pure padresolutie
                        plus dunne Qt-wrappers. Geen harde Qt-import
                        op moduleniveau, zodat pure tests geen GUI
                        nodig hebben.
  v1.1.0 (2026-10-22)  Fase 11I.2. Nieuwe sys._MEIPASS-branch in
                        _projectroot_default(), vóór de omhoog-zoeklus.
                        In een PyInstaller-bundel staat de code onder
                        _internal/app/helpers/, maar assets/ staat als
                        Tree(...) in de bundelroot (_internal/assets/).
                        Zonder deze branch zou de omhoog-zoeklus in de
                        bundel ook kunnen slagen -- maar pas ná een
                        aantal iteraties, en niet deterministisch als er
                        toevallig een assets/-map hoger in de boom staat.
                        De expliciete _MEIPASS-branch maakt de resolutie
                        deterministisch en onafhankelijk van de CWD.
                        Geen wijziging aan de publieke API.
================================================================================
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Pure padresolutie — geen Qt nodig
# ---------------------------------------------------------------------------

def _projectroot_default() -> Path:
    """Bepaal de projectroot vanuit dit bestand.

    Volgorde:

    1. **PyInstaller-bundel.** Als ``sys._MEIPASS`` bestaat, is dat de
       tijdelijke uitpakmap van de bundel. De PyInstaller-``Tree(...)``
       zet ``assets/`` in de bundelroot (``_MEIPASS/assets``). We
       controleren dat de map ook echt bestaat voordat we hem
       gebruiken, zodat een onverwachte ``_MEIPASS`` zonder
       ``assets/icons`` niet stil de verkeerde root teruggeeft.

    2. **Ontwikkel-/testomgeving.** We zoeken vanaf dit bestand omhoog
       naar de map die zowel ``assets`` als ``app`` bevat. Dat is
       robuuster dan een vast relatief pad, want tests en GUI kunnen
       vanuit verschillende working directories starten.

    3. **Laatste redmiddel.** Het cwd-gebonden relatieve pad
       (bestaand gedrag).
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        kandidaat = Path(meipass)
        if (kandidaat / "assets" / "icons").is_dir():
            return kandidaat

    current = Path(__file__).resolve().parent
    for _ in range(6):
        kandidaat = current / "assets" / "icons"
        if kandidaat.is_dir() and (current / "app").is_dir():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent

    # Laatste redmiddel: het cwd-gebonden relatieve pad (bestaand gedrag).
    return Path(".")


def iconenmap(*, projectroot: Path | None = None) -> Path:
    """Geef het pad naar de iconenmap.

    Parameters
    ----------
    projectroot:
        Optioneel om de projectroot expliciet te zetten (voor tests).
        Wanneer None, wordt de root automatisch bepaald.

    Returns
    -------
    Path
        Pad naar assets/icons/. Bestaat niet gegarandeerd: de aanroeper
        moet zelf controleren of het bestand bestaat.
    """
    root = projectroot if projectroot is not None else _projectroot_default()
    return root / "assets" / "icons"


def icoon_pad(
    naam: str,
    *,
    projectroot: Path | None = None,
    extensie: str = "png",
) -> Path | None:
    """Geef het pad naar één icoon, of None als het niet bestaat.

    Parameters
    ----------
    naam:
        Bestandsnaam zonder extensie, bv. "diagnose" of "app".
    projectroot:
        Optioneel om de projectroot expliciet te zetten (voor tests).
    extensie:
        Bestandsextensie zonder punt. Standaard "png".

    Returns
    -------
    Path | None
        Het pad naar het icoon als het bestaat, anders None.
    """
    if not naam or not isinstance(naam, str):
        return None
    bestand = iconenmap(projectroot=projectroot) / f"{naam}.{extensie}"
    return bestand if bestand.is_file() else None


def applicatie_icoon_pad(*, projectroot: Path | None = None) -> Path | None:
    """Pad naar het applicatie-icoon volgens de fallback-keten.

    Volgorde: app.png -> logo.ico -> None.
    """
    for naam, extensie in (("app", "png"), ("logo", "ico")):
        pad = icoon_pad(naam, projectroot=projectroot, extensie=extensie)
        if pad is not None:
            return pad
    return None


# ---------------------------------------------------------------------------
# Dunne Qt-wrappers — importeren Qt pas bij gebruik
# ---------------------------------------------------------------------------

def laad_icoon(
    naam: str,
    *,
    projectroot: Path | None = None,
) -> Any | None:
    """Laad een QIcon voor één icoon, of None als het ontbreekt.

    Qt wordt pas geïmporteerd wanneer deze functie daadwerkelijk wordt
    aangeroepen. Zo kunnen pure tests de padfuncties gebruiken zonder
    een QApplication te maken.
    """
    pad = icoon_pad(naam, projectroot=projectroot)
    if pad is None:
        return None
    try:
        from PySide6.QtGui import QIcon
    except ImportError:
        return None
    icoon = QIcon(str(pad))
    return icoon if not icoon.isNull() else None


def applicatie_icoon(*, projectroot: Path | None = None) -> Any | None:
    """Laad het QIcon van de applicatie volgens de fallback-keten.

    Volgorde: app.png -> logo.ico -> None.
    """
    try:
        from PySide6.QtGui import QIcon
    except ImportError:
        return None

    for naam, extensie in (("app", "png"), ("logo", "ico")):
        pad = icoon_pad(naam, projectroot=projectroot, extensie=extensie)
        if pad is None:
            continue
        icoon = QIcon(str(pad))
        if not icoon.isNull():
            return icoon
    return None


def zet_venster_icoon(widget: Any, *, projectroot: Path | None = None) -> bool:
    """Zet het applicatie-icoon op een QWidget (venster of dialoog).

    Geeft True terug als het icoon gezet is, anders False. Faalt nooit:
    als er geen icoon is, blijft het venster zonder expliciet icoon en
    erft het het icoon van de QApplication.
    """
    if widget is None:
        return False
    icoon = applicatie_icoon(projectroot=projectroot)
    if icoon is None:
        return False
    try:
        widget.setWindowIcon(icoon)
        return True
    except (AttributeError, RuntimeError):
        return False