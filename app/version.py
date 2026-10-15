"""
================================================================================
Module:     app/version.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-13
Auteur:     Bart Bossuyt

Doel:       Centrale versie-informatie van de applicatie. Eén bron van
            waarheid voor de versie, gebruikt door:
              - main.py (setApplicationVersion)
              - de Over-dialoog in main_window.py
              - buildstraat (bump_version.py, publish.ps1)

            Formaat: MAJOR.MINOR.PATCH (SemVer-achtig).
            De regex in bump_version.py en publish.ps1 verwacht exact
            drie getallen, gescheiden door punten.

Wijzigingen:
  v0.1.0-dev (2026-08-11)  Placeholder, nooit gebruikt in een release.
  v1.0.0     (2026-10-13)  Eerste echte release-versie. Fase 9A van de
                            packaging-fase. Vanaf nu bumpt de buildstraat
                            patch/minor/major.

Versiebeheer:
  - MAJOR: incompatibele architectuur- of API-wijziging.
  - MINOR: nieuwe functionaliteit die compatibel blijft.
  - PATCH: bugfix, kleine optimalisatie of interne refactor.
================================================================================
"""

__version__ = "1.1.2"