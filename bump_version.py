"""
================================================================================
Module:     bump_version.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-13
Auteur:     Bart Bossuyt

Doel:       Verhoogt het patch-, minor- of major-deel van de centrale
            applicatieversie in app/version.py.

            Wordt aangeroepen door build_installer.bat en
            build_and_publish.ps1, en kan ook handmatig worden gebruikt:

                python bump_version.py patch
                python bump_version.py minor
                python bump_version.py major

            De regex accepteert exact drie getallen, gescheiden door punten.
            Dat sluit aan bij de SemVer-achtige afspraak in app/version.py.

Wijzigingen:
  v1.0.0 (2026-10-13)  Fase 9B.1 van de packaging-fase. Eerste versie,
                        afgeleid van het ArticleSearch-patroon, maar met
                        app/version.py als centrale bron in plaats van
                        version.py in de root.
================================================================================
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


VERSION_FILE = Path("app") / "version.py"
VALID_PARTS = ("patch", "minor", "major")

# Match: __version__ = "1.2.3"
_VERSION_RE = re.compile(
    r'(__version__\s*=\s*")(\d+\.\d+\.\d+)(")'
)


def bump_version(version: str, part: str = "patch") -> str:
    """Verhoogt het opgegeven deel van een MAJOR.MINOR.PATCH-versie."""
    major, minor, patch = map(int, version.split("."))

    if part == "patch":
        patch += 1
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "major":
        major += 1
        minor = 0
        patch = 0
    else:
        raise ValueError(f"Onbekend versiedeel: {part!r}")

    return f"{major}.{minor}.{patch}"


def _lees_huidige_versie(pad: Path) -> tuple[str, str]:
    """Leest app/version.py en geeft (inhoud, huidige_versie) terug."""
    if not pad.exists():
        raise FileNotFoundError(f"Bestand niet gevonden: {pad}")

    inhoud = pad.read_text(encoding="utf-8")
    match = _VERSION_RE.search(inhoud)
    if not match:
        raise ValueError(
            f"Kon __version__ niet vinden in {pad}. "
            f"Verwacht: __version__ = \"MAJOR.MINOR.PATCH\""
        )
    return inhoud, match.group(2)


def _schrijf_nieuwe_versie(pad: Path, inhoud: str, nieuwe_versie: str) -> None:
    """Vervangt de versie in de bestandsinhoud en schrijft terug."""
    nieuwe_inhoud = _VERSION_RE.sub(
        lambda m: f"{m.group(1)}{nieuwe_versie}{m.group(3)}",
        inhoud,
        count=1,
    )
    pad.write_text(nieuwe_inhoud, encoding="utf-8")


def main() -> int:
    if len(sys.argv) < 2:
        print(
            f"❌ Geef op welk deel je wil verhogen: {', '.join(VALID_PARTS)}"
        )
        print("Voorbeeld: python bump_version.py minor")
        return 1

    part = sys.argv[1].lower()
    if part not in VALID_PARTS:
        print(f"❌ Ongeldige optie '{part}'. Kies uit: {', '.join(VALID_PARTS)}")
        return 1

    try:
        inhoud, oude_versie = _lees_huidige_versie(VERSION_FILE)
        nieuwe_versie = bump_version(oude_versie, part=part)
        _schrijf_nieuwe_versie(VERSION_FILE, inhoud, nieuwe_versie)
    except (FileNotFoundError, ValueError) as exc:
        print(f"❌ {exc}")
        return 1

    print(f"✅ Versie verhoogd van {oude_versie} naar {nieuwe_versie}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())