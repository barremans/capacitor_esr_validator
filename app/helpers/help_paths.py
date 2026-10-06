"""
================================================================================
Module:     app/helpers/help_paths.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-06
Auteur:     Bart Bossuyt

Doel:       GUI-onafhankelijke resolutie van het juiste help-markdownbestand
            per taal, met veilige fallback-keten.

            Fallback-keten (in volgorde):
              1. docs/help/<taal>.md        (bv. docs/help/en_US.md)
              2. docs/help/<fallback>.md    (standaard docs/help/nl_NL.md)
              3. docs/help.md               (legacy, één bestand voor alle talen)
              4. FileNotFoundError          (dialoog toont "Bestand niet gevonden")

            De helper kent geen GUI en geen Qt. Hij is bewust taal-agnostisch:
            elke taalcode die in i18n/locales/ bestaat kan een eigen help-bestand
            krijgen zonder codewijziging.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie (Fase 4H).
================================================================================
"""

from __future__ import annotations

from pathlib import Path


STANDAARD_FALLBACK_TAAL = "nl_NL"


def _docs_root_default() -> Path:
    """Bepaal de docs/-map vanuit de projectroot.

    We zoeken vanaf dit bestand omhoog naar de map die zowel 'docs' als 'app'
    bevat. Dat is robuuster dan een vast relatief pad, want tests en GUI
    kunnen vanuit verschillende working directories starten.
    """
    current = Path(__file__).resolve().parent
    for _ in range(6):
        kandidaat = current / "docs"
        if kandidaat.is_dir() and (current / "app").is_dir():
            return kandidaat
        parent = current.parent
        if parent == current:
            break
        current = parent

    # Laatste redmiddel: het cwd-gebonden relatieve pad (bestaand gedrag).
    return Path("docs")


def help_pad_voor_taal(
    taal: str,
    *,
    docs_root: Path | None = None,
    fallback_taal: str = STANDAARD_FALLBACK_TAAL,
    legacy_bestandsnaam: str = "help.md",
    submaps: str = "help",
) -> Path:
    """Los het help-markdownbestand op voor de opgegeven taal.

    Parameters
    ----------
    taal:
        Taalcode zoals gebruikt in i18n/locales/ (bv. "nl_NL", "en_US").
        Wordt niet gevalideerd tegen een vaste lijst: nieuwe talen werken
        automatisch zodra een bestand bestaat.
    docs_root:
        Optioneel om de docs/-map expliciet te zetten (voor tests).
        Wanneer None, wordt de map automatisch bepaald.
    fallback_taal:
        Taal die gebruikt wordt wanneer het taalbestand ontbreekt.
        Standaard "nl_NL".
    legacy_bestandsnaam:
        Naam van het oude, taal-onafhankelijke help-bestand binnen docs_root.
        Standaard "help.md".
    submaps:
        Naam van de submap onder docs_root met de taalbestanden.
        Standaard "help".

    Returns
    -------
    Path
        Pad naar het eerst gevonden bestaande bestand in de fallback-keten.

    Raises
    ------
    FileNotFoundError
        Wanneer geen van de kandidaten bestaat. De boodschap somt alle
        geprobeerde paden op, zodat de dialoog dit zinvol kan tonen.
    """
    root = docs_root if docs_root is not None else _docs_root_default()
    taalmap = root / submaps

    kandidaten: list[Path] = []
    if taal:
        kandidaten.append(taalmap / f"{taal}.md")
    if fallback_taal and fallback_taal != taal:
        kandidaten.append(taalmap / f"{fallback_taal}.md")
    kandidaten.append(root / legacy_bestandsnaam)

    for kandidaat in kandidaten:
        if kandidaat.is_file():
            return kandidaat

    geprobeerd = ", ".join(str(p) for p in kandidaten)
    raise FileNotFoundError(
        f"Geen help-bestand gevonden voor taal '{taal}'. "
        f"Geprobeerd: {geprobeerd}"
    )


def help_pad_bestaat_voor_taal(
    taal: str,
    *,
    docs_root: Path | None = None,
    fallback_taal: str = STANDAARD_FALLBACK_TAAL,
    legacy_bestandsnaam: str = "help.md",
    submaps: str = "help",
) -> bool:
    """True als er voor deze taal een bruikbaar help-bestand bestaat.

    Handig voor tests en voor toekomstige UI die een taal als 'niet
    ondersteund' wil markeren zonder de fallback te gebruiken.
    """
    try:
        help_pad_voor_taal(
            taal,
            docs_root=docs_root,
            fallback_taal=fallback_taal,
            legacy_bestandsnaam=legacy_bestandsnaam,
            submaps=submaps,
        )
    except FileNotFoundError:
        return False
    return True