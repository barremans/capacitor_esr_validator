"""
================================================================================
Module:     app/helpers/i18n.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     2.0.0
Datum:      2026-10-03
Auteur:     Bart Bossuyt

Doel:       Modulaire vertaalmodule met dynamische taalontdekking.

            Nieuwe structuur:
            i18n/locales/<taalcode>/language.json
            i18n/locales/<taalcode>/<module>.json

            De bestaande vertaalaanroep vertaal("sleutel", taal=...) blijft
            compatibel. Ontbrekende sleutels vallen terug op nl_NL. Oude
            i18n/locales/<taalcode>.json-bestanden blijven als legacy fallback
            ondersteund wanneer geen modulaire taalmap bestaat.

Wijzigingen:
  v1.0.0 (2026-08-11)  Initiële versie.
  v1.0.1 (2026-08-12)  Robuustere pad-detectie.
  v1.0.2 (2026-08-12)  Pad berekend vanuit projectroot via sys.path.
  v1.1.0 (2026-08-12)  Extra fallback voor PyInstaller; betere foutmeldingen.
  v2.0.0 (2026-10-03)  Vertalingen opgesplitst per module; language.json-
                        metadata en dynamische taalontdekking toegevoegd.
                        Dubbele vertaalsleutels worden expliciet geweigerd.
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import sys
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class TaalInfo:
    """Metadata van één beschikbare UI-taal."""

    code: str
    name: str
    native_name: str
    enabled: bool = True
    sort_order: int = 100


def _bepaal_i18n_root() -> Path:
    """Bepaalt het pad naar i18n/locales/ op basis van de projectroot."""
    if sys.path:
        for p in sys.path:
            candidate = Path(p) / "i18n" / "locales"
            if candidate.exists() and candidate.is_dir():
                return candidate

    candidate = Path(__file__).resolve().parent.parent.parent / "i18n" / "locales"
    if candidate.exists():
        return candidate

    candidate = Path.cwd() / "i18n" / "locales"
    if candidate.exists():
        return candidate

    current = Path.cwd()
    for _ in range(5):
        candidate = current / "i18n" / "locales"
        if candidate.exists():
            return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent

    candidate = Path(sys.executable).parent / "i18n" / "locales"
    if candidate.exists():
        return candidate

    return Path(__file__).resolve().parent.parent.parent / "i18n" / "locales"


I18N_ROOT = _bepaal_i18n_root()
STANDAARD_TAAL = "nl_NL"

_cache: dict[str, dict[str, str]] = {}
_taalinfo_cache: tuple[TaalInfo, ...] | None = None


def _plat_maken(data: dict, prefix: str = "") -> dict[str, str]:
    """Zet geneste JSON om naar platte 'a.b.c'-sleutels."""
    resultaat: dict[str, str] = {}
    for key, value in data.items():
        if str(key).startswith("_"):
            continue
        volledige_sleutel = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            resultaat.update(_plat_maken(value, volledige_sleutel))
        else:
            resultaat[volledige_sleutel] = value
    return resultaat


def _lees_json_object(pad: Path) -> dict:
    try:
        with pad.open("r", encoding="utf-8") as bestand:
            data = json.load(bestand)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Ongeldige JSON in vertaalbestand: {pad}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Vertaalbestand moet een JSON-object zijn: {pad}")
    return data


def _lees_taalinfo_map(taalmap: Path) -> TaalInfo:
    metadata_pad = taalmap / "language.json"
    data = _lees_json_object(metadata_pad)
    meta = data.get("_meta")

    if not isinstance(meta, dict):
        raise ValueError(f"language.json mist '_meta': {metadata_pad}")

    code = meta.get("code")
    name = meta.get("name")
    native_name = meta.get("native_name")
    enabled = meta.get("enabled", True)
    sort_order = meta.get("sort_order", 100)

    if not isinstance(code, str) or not code.strip():
        raise ValueError(f"language.json mist geldige code: {metadata_pad}")
    if code != taalmap.name:
        raise ValueError(
            f"Taalcode '{code}' komt niet overeen met mapnaam '{taalmap.name}'."
        )
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"language.json mist geldige name: {metadata_pad}")
    if not isinstance(native_name, str) or not native_name.strip():
        raise ValueError(f"language.json mist geldige native_name: {metadata_pad}")
    if not isinstance(enabled, bool):
        raise ValueError(f"language.json veld enabled moet boolean zijn: {metadata_pad}")
    if not isinstance(sort_order, int):
        raise ValueError(f"language.json veld sort_order moet integer zijn: {metadata_pad}")

    return TaalInfo(
        code=code.strip(),
        name=name.strip(),
        native_name=native_name.strip(),
        enabled=enabled,
        sort_order=sort_order,
    )


def beschikbare_taalinfos() -> list[TaalInfo]:
    """Ontdek alle ingeschakelde talen uit taaldirectories en legacy JSON."""
    global _taalinfo_cache

    if _taalinfo_cache is not None:
        return list(_taalinfo_cache)

    if not I18N_ROOT.exists():
        _taalinfo_cache = ()
        return []

    infos: dict[str, TaalInfo] = {}

    for taalmap in sorted(p for p in I18N_ROOT.iterdir() if p.is_dir()):
        metadata_pad = taalmap / "language.json"
        if not metadata_pad.is_file():
            continue
        info = _lees_taalinfo_map(taalmap)
        if info.enabled:
            infos[info.code] = info

    # Legacy fallback: alleen als voor die code geen modulaire taalmap bestaat.
    for pad in sorted(I18N_ROOT.glob("*.json")):
        code = pad.stem
        if code in infos:
            continue
        infos[code] = TaalInfo(
            code=code,
            name=code,
            native_name=code,
            enabled=True,
            sort_order=1000,
        )

    sorted_infos = tuple(
        sorted(
            infos.values(),
            key=lambda info: (
                info.sort_order,
                info.native_name.casefold(),
                info.code.casefold(),
            ),
        )
    )
    _taalinfo_cache = sorted_infos
    return list(sorted_infos)


def beschikbare_talen() -> list[str]:
    """Backward-compatible lijst met beschikbare taalcodes."""
    return [info.code for info in beschikbare_taalinfos()]


def _laad_modulaire_taal(taalcode: str, taalmap: Path) -> dict[str, str]:
    resultaat: dict[str, str] = {}
    sleutel_bron: dict[str, Path] = {}

    module_bestanden = sorted(
        pad
        for pad in taalmap.glob("*.json")
        if pad.name != "language.json"
    )

    for pad in module_bestanden:
        data = _lees_json_object(pad)
        plat = _plat_maken(data)

        for sleutel, waarde in plat.items():
            if sleutel in resultaat:
                vorige = sleutel_bron[sleutel]
                raise ValueError(
                    "Dubbele vertaalsleutel "
                    f"'{sleutel}' in '{vorige.name}' en '{pad.name}' "
                    f"voor taal {taalcode}."
                )
            if not isinstance(waarde, str):
                raise ValueError(
                    f"Vertaalwaarde voor '{sleutel}' in {pad} moet tekst zijn."
                )
            resultaat[sleutel] = waarde
            sleutel_bron[sleutel] = pad

    return resultaat


def _laad_legacy_taal(taalcode: str, pad: Path) -> dict[str, str]:
    data = _lees_json_object(pad)
    plat = _plat_maken(data)
    for sleutel, waarde in plat.items():
        if not isinstance(waarde, str):
            raise ValueError(
                f"Vertaalwaarde voor '{sleutel}' in {pad} moet tekst zijn."
            )
    return plat


def _laad_taalbestand(taalcode: str) -> dict[str, str]:
    if taalcode in _cache:
        return _cache[taalcode]

    taalmap = I18N_ROOT / taalcode
    legacy_pad = I18N_ROOT / f"{taalcode}.json"

    if taalmap.is_dir() and (taalmap / "language.json").is_file():
        data = _laad_modulaire_taal(taalcode, taalmap)
    elif legacy_pad.is_file():
        data = _laad_legacy_taal(taalcode, legacy_pad)
    else:
        print(
            f"[i18n WAARSCHUWING] Geen vertaling gevonden voor taal: {taalcode}",
            file=sys.stderr,
        )
        print(f"[i18n WAARSCHUWING] I18N_ROOT = {I18N_ROOT}", file=sys.stderr)
        raise FileNotFoundError(
            f"Vertaling niet gevonden voor taalcode: {taalcode}"
        )

    _cache[taalcode] = data
    return data


def wis_cache() -> None:
    """Forceert herontdekking en herinlezing; vooral nuttig voor tests."""
    global _taalinfo_cache
    _cache.clear()
    _taalinfo_cache = None


def vertaal(
    sleutel: str,
    taal: str = STANDAARD_TAAL,
    **interpolatie: Any,
) -> str:
    """Vertaal een sleutel met fallback naar Nederlands en daarna de sleutel."""
    try:
        vertalingen = _laad_taalbestand(taal)
    except FileNotFoundError:
        vertalingen = {}

    sjabloon = vertalingen.get(sleutel)

    if sjabloon is None and taal != STANDAARD_TAAL:
        try:
            standaard = _laad_taalbestand(STANDAARD_TAAL)
            sjabloon = standaard.get(sleutel)
        except FileNotFoundError:
            pass

    if sjabloon is None:
        return sleutel

    try:
        return sjabloon.format(**interpolatie)
    except (KeyError, IndexError):
        return sjabloon


t = vertaal
