"""
================================================================================
Module:     tests/test_chart_axis.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.1.0
Datum:      2026-10-26
Auteur:     Bart Bossuyt

Doel:       Regressietests voor de pure Y-as-clamping-helper (fase 5A)
            en de X-as-tick-helper (fase 5B).

Wijzigingen:
  v1.0.0 (2026-10-26)  Eerste versie: Tukey-fence op normale data,
                        op de echte outlier-CSV, op <4 punten, op
                        alle-gelijke waarden, op niet-eindige invoer,
                        en op de n_outliers-telling.
  v1.1.0 (2026-10-26)  Fase 5B: vijf tests voor bereken_x_as_ticks().
                        Dekt kleine, middelgrote en grote bereiken,
                        ongeldige grenzen en de return-tuple. Import
                        van bereken_x_as_ticks toegevoegd.
================================================================================
"""

from __future__ import annotations

import pytest

from app.helpers.chart_axis import bereken_x_as_ticks, bereken_y_as_range


def test_lege_invoer_geeft_veilige_fallback():
    y_min, y_max, n_outliers = bereken_y_as_range([])
    assert y_min == 0.0
    assert y_max == 1.0
    assert n_outliers == 0


def test_een_tot_drie_punten_geen_outlier_detectie():
    """<4 punten: te weinig voor IQR. Fallback op min/max met marge."""
    for waarden in ([100.0], [100.0, 200.0], [100.0, 200.0, 300.0]):
        y_min, y_max, n_outliers = bereken_y_as_range(waarden)
        assert n_outliers == 0
        assert y_min < min(waarden)
        assert y_max > max(waarden)


def test_alle_waarden_gelijk_geeft_marge():
    y_min, y_max, n_outliers = bereken_y_as_range([42.0] * 10)
    assert n_outliers == 0
    assert y_min < 42.0 < y_max
    assert y_max - y_min >= 1.0


def test_normale_verdeling_zonder_outliers_gebruikt_min_max():
    """Bij afwezigheid van outliers valt de helper terug op min/max."""
    waarden = [float(v) for v in range(1, 21)]  # 1..20
    y_min, y_max, n_outliers = bereken_y_as_range(waarden)
    assert n_outliers == 0
    assert y_min < 1.0
    assert y_max > 20.0


def test_echte_outlier_csv_waarde_wordt_gedetecteerd():
    """De 109.500 mΩ-piek uit historiek_overzicht_2026-10-15 valt buiten de as."""
    # Representatieve steekproef uit de CSV: 75 normale + 3 outliers.
    normaal = [
        1.446, 1.455, 1.519, 1.548, 1.565, 1.578, 1.579, 1.580,
        1.638, 1.679, 1.718, 1.852, 1.917, 2.007, 2.046, 2.934,
        3.441, 3.498, 5.591, 5.603, 5.736, 5.736, 4.97, 4.97,
        6.129, 27.61, 75.7, 75.7, 78.1, 81.6, 82.9, 91.6,
        95.1, 96.4, 98.5, 98.7, 98.8, 99.9, 102.4, 109.5,
        113.8, 114.4, 115.4, 121.5, 128.0, 139.3, 139.3, 147.6,
        149.3, 151.1, 151.2, 152.3, 152.4, 153.1, 158.5, 165.5,
        176.6, 179.7, 182.5, 189.5, 189.9, 192.8, 192.8, 200.0,
        208.3, 216.8, 255.0, 290.5, 305.5, 306.6, 366.1, 386.2,
        405.1,
    ]
    # Drie extreme uitschieters (Ω-waarden die per ongeluk als mΩ zijn
    # opgeslagen; precies het soort dat de as onleesbaar maakte).
    outliers = [109500.0, 7473.0, 4059.0]
    y_min, y_max, n_outliers = bereken_y_as_range(normaal + outliers)
    assert n_outliers >= 1, (
        f"Verwacht minstens 1 outlier, kreeg {n_outliers}. "
        f"As-bereik: {y_min}–{y_max}"
    )
    # De as toont niet de 109.500-piek.
    assert y_max < 109500.0, f"As-max {y_max} toont de piek"


def test_niet_eindige_waarden_worden_genegeerd():
    waarden = [100.0, float("nan"), 200.0, float("inf"), 300.0, None, True, "x", 400.0]
    y_min, y_max, n_outliers = bereken_y_as_range(waarden)
    assert n_outliers == 0
    assert y_min < 100.0
    assert y_max > 400.0


def test_n_outliers_is_consistent_met_fence():
    """De telling klopt: elk punt buiten de fence telt precies één keer."""
    normaal = [90.0 + i for i in range(20)]  # 90..109
    waarden = normaal + [10000.0]
    y_min, y_max, n_outliers = bereken_y_as_range(waarden)
    assert n_outliers == 1
    assert y_max < 10000.0


# ============================================================================
# v1.1.0 — X-as-ticks voor leesbare labels (fase 5B)
# ============================================================================

def test_x_ticks_klein_bereik_gebruikt_decimalen():
    """Bereik < 1 µF: 4 ticks, %.2f, geen rotatie."""
    tick_count, label_format, labels_angle = bereken_x_as_ticks(0.1, 0.9)
    assert tick_count == 4
    assert label_format == "%.2f"
    assert labels_angle == 0


def test_x_ticks_middelgroot_bereik_gebruikt_een_decimal():
    """Bereik 1–10 µF: 5 ticks, %.1f, geen rotatie."""
    tick_count, label_format, labels_angle = bereken_x_as_ticks(1.0, 9.0)
    assert tick_count == 5
    assert label_format == "%.1f"
    assert labels_angle == 0


def test_x_ticks_echte_csv_bereik_gebruikt_rotatie():
    """Het echte bereik 0,1–1.160 µF: 5 ticks, %.0f, -45°."""
    tick_count, label_format, labels_angle = bereken_x_as_ticks(0.1, 1160.0)
    assert tick_count == 5
    assert label_format == "%.0f"
    assert labels_angle == -45


def test_x_ticks_groot_bereik_gebruikt_compacte_notatie():
    """Bereik >= 10.000 µF: 3 ticks, %.3g, -45°."""
    tick_count, label_format, labels_angle = bereken_x_as_ticks(0.1, 20000.0)
    assert tick_count == 3
    assert label_format == "%.3g"
    assert labels_angle == -45


def test_x_ticks_ongeldige_grenzen_geven_veilige_fallback():
    """Omgekeerde of niet-eindige grenzen: veilige fallback."""
    for x_min, x_max in [(1.0, 0.5), (float("nan"), 1.0), (0.0, float("inf"))]:
        tick_count, label_format, labels_angle = bereken_x_as_ticks(x_min, x_max)
        assert tick_count == 5
        assert label_format == "%.0f"
        assert labels_angle == 0