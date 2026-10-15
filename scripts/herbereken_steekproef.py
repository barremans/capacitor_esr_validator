"""
================================================================================
Module:     scripts/herbereken_steekproef.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.1.0
Datum:      2026-10-15
Auteur:     Ontwikkelaar

Doel:       Fase 10B — herberekent de praktijkmetingen uit de historiek
            met de nieuwe frequentie-specifieke referentieprofielen. Toont
            per meting de oude status (tegen 100 kHz) en de nieuwe status
            (tegen 1 kHz / 10 kHz / 100 Hz), plus de nieuwe ESR-factor.

            Dit is een eenmalig analysedraaiboek, geen productiecode. Het
            schrijft niets naar de database; het leest alleen en print.

Wijzigingen:
  v1.0.0 (2026-10-15)  Eerste versie. Leest de detail-CSV, reconstrueert
                       de meetcontext en herberekent de beoordeling.
  v1.1.0 (2026-10-15)  Zoekt automatisch het meest recente
                       historiek_detail_*.csv-bestand in de projectroot
                       i.p.v. een vaste bestandsnaam. Ondersteunt ook
                       een expliciet pad als command-line-argument.

Gebruik:
  (.venv) PS C:\\PY\\capacitor_esr_validator> python scripts/herbereken_steekproef.py
  (.venv) PS C:\\PY\\capacitor_esr_validator> python scripts/herbereken_steekproef.py pad\\naar\\bestand.csv

Referentie: docs/phase10_analysis.md, docs/validation_rules.md.
================================================================================
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

# Voeg de projectroot toe aan sys.path zodat 'app' importeerbaar is.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.data.references import zoek_referentie
from app.services.assessment_service import (
    Meetmethode,
    beoordeel_meting,
)


def _vind_csv() -> Path | None:
    """Zoek het meest recente historiek_detail_*.csv-bestand in de projectroot."""
    kandidaten = sorted(
        PROJECT_ROOT.glob("historiek_detail_*.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return kandidaten[0] if kandidaten else None


def _float_of_none(waarde: str) -> float | None:
    waarde = (waarde or "").strip()
    if waarde in ("", "None", "NULL"):
        return None
    return float(waarde)


def _bool_of_str(waarde: str) -> bool:
    return (waarde or "").strip().lower() in ("true", "1", "ja", "yes")


def _converteer_capaciteit_naar_uf(waarde: float | None, eenheid: str | None) -> float | None:
    if waarde is None or not eenheid:
        return None
    factoren = {
        "pF": 1e-6,
        "nF": 1e-3,
        "µF": 1.0,
        "uF": 1.0,
        "mF": 1e3,
    }
    factor = factoren.get(eenheid)
    if factor is None:
        return None
    return waarde * factor


def main() -> None:
    if len(sys.argv) > 1:
        csv_pad = Path(sys.argv[1])
    else:
        csv_pad = _vind_csv()

    if csv_pad is None or not csv_pad.exists():
        print(
            "Geen historiek_detail_*.csv-bestand gevonden in "
            f"{PROJECT_ROOT}.",
            file=sys.stderr,
        )
        print(
            "Geef eventueel een expliciet pad mee als argument.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Gebruikte CSV: {csv_pad.name}")
    print()

    rijen: list[dict] = []
    with csv_pad.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            rijen.append(row)

    print(f"{'id':>4} | {'freq':>8} | {'C_nom':>8} | {'C_meas':>8} | "
          f"{'ESR_meas':>10} | {'ref_mohm':>9} | {'factor':>7} | "
          f"{'oud_status':<22} | {'nieuw_status':<22}")
    print("-" * 140)

    samenvatting: dict[str, int] = {}

    for row in rijen:
        meet_id = row.get("measurement_id", "?")
        freq = _float_of_none(row.get("frequency_hz"))
        c_nom = _float_of_none(row.get("esr_nominal_capacitance_value"))
        c_nom_unit = row.get("esr_nominal_capacitance_unit") or "µF"
        v_nom = _float_of_none(row.get("esr_rated_voltage_v"))
        c_meas = _float_of_none(row.get("esr_measured_capacitance_f"))
        esr_meas = _float_of_none(row.get("esr_measured_esr_ohm"))
        d_meas = _float_of_none(row.get("esr_dissipation_factor_d"))
        technologie = row.get("technology") or "Aluminium elektrolytisch"
        meetmethode = row.get("measurement_method") or "EX_SITU"
        temperatuur = _float_of_none(row.get("temperature_c"))
        oud_status = row.get("final_status") or "?"

        if freq is None or c_meas is None or esr_meas is None:
            continue

        # Converteer gemeten capaciteit (in F) naar de nominale eenheid
        if c_nom_unit == "µF":
            c_meas_in_eenheid = c_meas * 1e6
        elif c_nom_unit == "mF":
            c_meas_in_eenheid = c_meas * 1e3
        elif c_nom_unit == "nF":
            c_meas_in_eenheid = c_meas * 1e9
        elif c_nom_unit == "pF":
            c_meas_in_eenheid = c_meas * 1e12
        else:
            c_meas_in_eenheid = c_meas * 1e6

        c_nom_uf = _converteer_capaciteit_naar_uf(c_nom, c_nom_unit)

        referentie = None
        if technologie == "Aluminium elektrolytisch" and c_nom_uf and v_nom:
            referentie = zoek_referentie(
                c_nom_uf,
                v_nom,
                condensatortype=technologie,
                meetfrequentie_hz=freq,
            )

        try:
            resultaat = beoordeel_meting(
                nominale_capaciteit=c_nom if c_nom is not None else 0.0,
                eenheid_nominaal=c_nom_unit,
                tolerantie_percent=20.0,
                gemeten_capaciteit=c_meas_in_eenheid,
                eenheid_gemeten_capaciteit=c_nom_unit,
                gemeten_esr=esr_meas,
                eenheid_gemeten_esr="Ω",
                meetfrequentie_hz=freq,
                D=d_meas,
                condensatortype=technologie,
                meetmethode=meetmethode,
                omgevingstemperatuur_c=temperatuur,
                veiligheid_bevestigd=True,
                referentie=referentie,
                fabrikant_bekend=False,
                serie_bekend=False,
                meetwaarde_buiten_bereik=_bool_of_str(row.get("out_of_range")),
                taal="nl_NL",
            )
        except Exception as exc:
            print(f"{meet_id:>4} | fout bij herberekening: {exc}")
            continue

        nieuw_status = resultaat.eindstatus.value
        factor = resultaat.esr.factor
        ref_mohm = (
            resultaat.esr.referentie_esr_ohm * 1000
            if resultaat.esr.referentie_esr_ohm is not None
            else None
        )

        factor_str = f"{factor:.3f}" if factor is not None else "—"
        ref_str = f"{ref_mohm:.0f}" if ref_mohm is not None else "—"

        print(
            f"{meet_id:>4} | {freq:>8.0f} | {c_nom if c_nom else 0:>8.1f} | "
            f"{c_meas_in_eenheid:>8.1f} | {esr_meas * 1000:>9.2f}mΩ | "
            f"{ref_str:>9} | {factor_str:>7} | "
            f"{oud_status:<22} | {nieuw_status:<22}"
        )

        samenvatting[nieuw_status] = samenvatting.get(nieuw_status, 0) + 1

    print()
    print("Samenvatting nieuwe statussen:")
    for status, aantal in sorted(samenvatting.items()):
        print(f"  {status:<24}: {aantal}")


if __name__ == "__main__":
    main()