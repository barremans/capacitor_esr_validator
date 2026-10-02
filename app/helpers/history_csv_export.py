"""
================================================================================
Module:     app/helpers/history_csv_export.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-01
Auteur:     Bart Bossuyt

Doel:       Kleine GUI- en database-onafhankelijke CSV-writer voor Historiek.

            De helper schrijft reeds geformatteerde kolomkoppen en rijen naar
            UTF-8 met BOM, met puntkomma als scheidingsteken voor praktische
            compatibiliteit met Europese spreadsheetinstellingen.

Wijzigingen:
  v1.0.0 (2026-10-01)  Eerste read-only CSV-exporthelper.
================================================================================
"""

from __future__ import annotations

import csv
from pathlib import Path
from collections.abc import Iterable, Sequence


def write_history_csv(
    file_path: str | Path,
    headers: Sequence[str],
    rows: Iterable[Sequence[str]],
) -> None:
    """Schrijf geformatteerde historiekdata naar CSV zonder brondata te wijzigen."""
    path = Path(file_path)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        writer.writerow([str(value) for value in headers])
        for row in rows:
            writer.writerow([str(value) for value in row])
