"""
================================================================================
Module:     app/helpers/technology.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-26
Auteur:     Bart Bossuyt

Doel:       Eén bron van waarheid voor de vraag "hoort dit condensatortype
            bij de aluminium-elektrolytische familie?" en "behoren twee
            condensatortypes tot dezelfde technologie-familie?".

            Deze helpers werden in 4A lokaal in assessment_service.py
            gedefinieerd en in 4C verplaatst naar deze module, omdat
            ook app/data/references en app/gui/esr_test_screen ze
            nodig hebben. Zonder gedeelde module zou dezelfde logica
            op drie plekken staan, met het risico op drift.

Wijzigingen:
  v1.0.0 (2026-10-26)  Eerste versie. Verplaatst uit assessment_service
                        v1.7.0 (is_elektrolytisch_type, _zelfde_
                        technologie_familie) en breidt uit met
                        technologie_familie() voor toekomstige
                        technologieën.

Referentie: docs/validation_rules.md §14 (type-match),
            docs/context.md §14.
================================================================================
"""

from __future__ import annotations

from typing import Optional


# Prefix van de elektrolytische familie in CONDENSATORTYPES. Eén bron
# van waarheid voor de semantische check of een condensatortype
# elektrolytisch is. "Low ESR" en "Bipolair/NP" zijn geldige varianten;
# "Tantaal elektrolytisch" en "Tantaal polymer" beginnen niet met deze
# prefix en vallen dus terecht buiten de familie.
ELEKTROLYTISCHE_FAMILIE_PREFIX = "Aluminium elektrolytisch"


def is_elektrolytisch_type(condensatortype: Optional[str]) -> bool:
    """Bepaalt of een condensatortype tot de aluminium-elektrolytische
    familie hoort.

    De familie omvat alle varianten die met de vaste prefix beginnen
    ("Aluminium elektrolytisch", "— Low ESR", "— Bipolair/NP", en
    toekomstige subtypen). Tantaal, polymer, film, keramisch,
    supercondensator en onbekend vallen er bewust buiten: die mogen
    niet met de elektrolytische ESR-referentietabel worden vergeleken
    (§14 validation_rules.md).
    """
    if not isinstance(condensatortype, str):
        return False
    return condensatortype.startswith(ELEKTROLYTISCHE_FAMILIE_PREFIX)


def technologie_familie(condensatortype: Optional[str]) -> Optional[str]:
    """Geeft de technologie-familie van een condensatortype terug.

    - Elektrolytisch (welke variant dan ook): ``"elektrolytisch"``
    - Tantaal (elektrolytisch of polymer): ``"tantaal"``
    - Polymer (conductive/hybrid): ``"polymer"``
    - Film: ``"film"``
    - Keramisch / MLCC: ``"keramisch"``
    - Supercondensator: ``"supercondensator"``
    - Onbekend, Anders, leeg, None: ``None``

    Twee types horen bij dezelfde familie als hun familie-strings
    gelijk zijn. ``None`` matcht alleen ``None``.
    """
    if not isinstance(condensatortype, str) or not condensatortype.strip():
        return None
    type_lower = condensatortype.strip().lower()
    if is_elektrolytisch_type(condensatortype):
        return "elektrolytisch"
    if type_lower.startswith("tantaal"):
        return "tantaal"
    if "polymer" in type_lower:
        return "polymer"
    if type_lower == "film":
        return "film"
    if type_lower.startswith("keramisch"):
        return "keramisch"
    if type_lower == "supercondensator":
        return "supercondensator"
    return None


def zelfde_technologie_familie(
    a: Optional[str],
    b: Optional[str],
) -> bool:
    """Bepaalt of twee condensatortypes tot dezelfde technologie-familie
    behoren.

    - Twee elektrolytische types (welke variant dan ook) → True.
    - Twee tantaal-types → True.
    - Twee polymer-types → True.
    - Twee onbekende/Anders/lege types → alleen True als ze exact gelijk
      zijn (dus "Anders" == "Anders" is True, "Anders" == "Onbekend" niet).
    - Een elektrolytisch en een tantaal type → False.
    """
    if a is None or b is None:
        return a == b
    fam_a = technologie_familie(a)
    fam_b = technologie_familie(b)
    if fam_a is None or fam_b is None:
        # Val terug op exacte string-gelijkheid voor onbekende types.
        return a == b
    return fam_a == fam_b