# bump_version.py
# =============================================================================
# Electronics Diagnostic Tool Hub / ESR Tester
# File:    bump_version.py
# Role:    Verhoogt het patch-, minor- of major-deel van de centrale versie
#          in app/version.py. Wordt aangeroepen door build_installer.bat
#          en build_and_publish.ps1. Kan ook handmatig:
#              python bump_version.py patch
#              python bump_version.py minor
#              python bump_version.py major
#
#          De regex verwacht exact drie getallen, gescheiden door punten.
#          De schrijfwijze blijft behouden: __version__ = "x.y.z".
#
# Version: 2.0.0
# Author:  Bart Bossuyt
# Changes: 2.0.0 (2026-10-13) - Fase 9C+9D. VERSION_FILE gewijzigd van
#                               "version.py" (root) naar "app/version.py",
#                               in lijn met de rest van het project. De
#                               regex en de bump-logica blijven identiek
#                               aan de ArticleSearch-versie.
# Changes: 1.0.0 (2026-10-13) - Fase 9B.1. Eerste versie, afgeleid van
#                               ArticleSearch bump_version.py, met
#                               VERSION_FILE=version.py in de root.
# =============================================================================

import re
import sys

VERSION_FILE = "app/version.py"
VALID_PARTS = ("patch", "minor", "major")


def bump_version(version, part="patch"):
    major, minor, patch = map(int, version.split("."))
    if part == "patch":
        patch += 1
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "major":
        major += 1
        minor = patch = 0
    return f"{major}.{minor}.{patch}"


def main():
    if len(sys.argv) < 2:
        print(f"[FOUT] Geef op welk deel van de versie je wil verhogen: {', '.join(VALID_PARTS)}")
        print("Voorbeeld: python bump_version.py minor")
        sys.exit(1)

    part = sys.argv[1].lower()
    if part not in VALID_PARTS:
        print(f"[FOUT] Ongeldige optie '{part}'. Kies uit: {', '.join(VALID_PARTS)}")
        sys.exit(1)

    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"[FOUT] Bestand '{VERSION_FILE}' niet gevonden.")
        sys.exit(1)

    match = re.search(r'(__version__\s*=\s*")(\d+\.\d+\.\d+)(")', content)
    if not match:
        print(f"[FOUT] Versieregel niet gevonden in {VERSION_FILE}")
        sys.exit(1)

    old_version = match.group(2)
    new_version = bump_version(old_version, part=part)

    new_content = re.sub(
        r'(__version__\s*=\s*")(\d+\.\d+\.\d+)(")',
        lambda m: f'{m.group(1)}{new_version}{m.group(3)}',
        content,
    )

    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"[OK] Versie verhoogd van {old_version} naar {new_version}")


if __name__ == "__main__":
    main()