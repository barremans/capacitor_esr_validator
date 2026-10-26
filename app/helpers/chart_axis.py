"""
================================================================================
Module:     app/helpers/chart_axis.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.1
Datum:      2026-10-26
Auteur:     Bart Bossuyt

Doel:       Pure, GUI- en Qt-onafhankelijke helpers voor slimme as-instellingen
            op meetreeksen met outliers (fase 5A) en voor leesbare X-as-labels
            op log-verdeelde bereiken (fase 5B).

Wijzigingen:
  v1.0.0 (2026-10-26)  Eerste versie: bereken_y_as_range() met Tukey-fence
                        (1.5 × IQR), fallbacks voor <4 punten, alle-gelijke
                        waarden en niet-eindige invoer. Retourneert
                        (y_min, y_max, n_outliers).
  v1.1.0 (2026-10-26)  Fase 5B: nieuwe pure helper bereken_x_as_ticks()
                        die op basis van het X-bereik een passend aantal
                        ticks, een labelformaat en een labelrotatie kiest.
                        Voorkomt dat Qt bij een log-verdeeld bereik (bv.
                        0,1 µF tot 1.160 µF) de labels afkapt tot "...".
  v1.1.1 (2026-10-26)  Fix 5B: drempel voor 4 ticks verschoven van 1000
                        naar 1500, zodat het representatieve bereik van
                        de historiek-CSV (0,1–1160 µF) 5 ticks krijgt.
================================================================================
"""

from __future__ import annotations

import math
from typing import Iterable


_TUKEY_FACTOR = 1.5
_MIN_MARGE_BIJ_GELIJK = 1.0
_MARGE_FRACTIE = 0.05


def _is_finite(value: object) -> bool:
    if value is None or isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _kwantiel_gesorteerd(sorted_values: list[float], q: float) -> float:
    """Lineair geïnterpoleerd kwantiel op een al gesorteerde lijst."""
    n = len(sorted_values)
    if n == 1:
        return sorted_values[0]
    positie = q * (n - 1)
    onder = int(math.floor(positie))
    boven = int(math.ceil(positie))
    if onder == boven:
        return sorted_values[onder]
    fractie = positie - onder
    return sorted_values[onder] + (sorted_values[boven] - sorted_values[onder]) * fractie


def bereken_y_as_range(
    values: Iterable[object],
) -> tuple[float, float, int]:
    """Bereken een leesbaar Y-as-bereik met outlier-detectie."""
    geldig: list[float] = []
    for value in values:
        if not _is_finite(value):
            continue
        geldig.append(float(value))

    if not geldig:
        return (0.0, 1.0, 0)

    geldig.sort()
    n = len(geldig)

    if n < 4:
        y_min = geldig[0]
        y_max = geldig[-1]
        if y_min == y_max:
            marge = abs(y_min) * 0.1 or _MIN_MARGE_BIJ_GELIJK
            y_min -= marge
            y_max += marge
        else:
            marge = (y_max - y_min) * _MARGE_FRACTIE
            y_min -= marge
            y_max += marge
        return (y_min, y_max, 0)

    q1 = _kwantiel_gesorteerd(geldig, 0.25)
    q3 = _kwantiel_gesorteerd(geldig, 0.75)
    iqr = q3 - q1

    if iqr <= 0.0:
        y_min = geldig[0]
        y_max = geldig[-1]
        if y_min == y_max:
            marge = abs(y_min) * 0.1 or _MIN_MARGE_BIJ_GELIJK
            y_min -= marge
            y_max += marge
        else:
            marge = (y_max - y_min) * _MARGE_FRACTIE
            y_min -= marge
            y_max += marge
        return (y_min, y_max, 0)

    fence_laag = q1 - _TUKEY_FACTOR * iqr
    fence_hoog = q3 + _TUKEY_FACTOR * iqr

    n_outliers = 0
    for value in geldig:
        if value < fence_laag or value > fence_hoog:
            n_outliers += 1

    if n_outliers == 0:
        y_min = geldig[0]
        y_max = geldig[-1]
    else:
        y_min = max(fence_laag, geldig[0])
        y_max = min(fence_hoog, geldig[-1])

    if y_min == y_max:
        marge = abs(y_min) * 0.1 or _MIN_MARGE_BIJ_GELIJK
        y_min -= marge
        y_max += marge
    else:
        marge = (y_max - y_min) * _MARGE_FRACTIE
        y_min -= marge
        y_max += marge

    return (y_min, y_max, n_outliers)


def bereken_x_as_ticks(
    x_min: float,
    x_max: float,
) -> tuple[int, str, int]:
    """Kies tick_count, label_format en labels_angle voor een lineaire X-as."""
    if (
        not _is_finite(x_min)
        or not _is_finite(x_max)
        or float(x_max) <= float(x_min)
    ):
        return (5, "%.0f", 0)

    breedte = float(x_max) - float(x_min)

    if breedte < 1.0:
        return (4, "%.2f", 0)
    if breedte < 10.0:
        return (5, "%.1f", 0)
    if breedte < 100.0:
        return (5, "%.0f", 0)
    # v1.1.1: drempel verschoven van 1000 naar 1500 zodat het representatieve
    # bereik van de historiek-CSV (0,1–1160 µF, na marge ~1276) 5 ticks krijgt.
    if breedte < 1500.0:
        return (5, "%.0f", -45)
    if breedte < 10000.0:
        return (4, "%.0f", -45)
    return (3, "%.3g", -45)