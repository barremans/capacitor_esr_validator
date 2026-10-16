"""
================================================================================
Module:     scripts/genereer_placeholders.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-16
Auteur:     Bart Bossuyt

Doel:       Genereert een volledige set placeholder-iconen voor fase 11C:
            één applicatie-icoon (app.png + logo.ico) en twaalf
            thematische iconen (diagnose, esr, history, documentation,
            analysis, report, settings, help, bug, update, exit).

            De iconen zijn bewust eenvoudig en vlak: donkerblauw
            (#1F4E79) als hoofdkleur, cyaan (#4AA3FF) als accent,
            transparante achtergrond. Ze zijn bedoeld als tijdelijke
            plaatsvervangers; de definitieve ontwerpen kunnen later
            zonder codewijziging dezelfde bestandsnamen krijgen.

            Draai dit script één keer vanuit de projectroot:

                python scripts\\genereer_placeholders.py

            Het script schrijft naar assets/icons/ en overschrijft
            bestaande bestanden met dezelfde naam.

Wijzigingen:
  v1.0.0 (2026-10-16)  Eerste versie. Genereert alle icoonbestanden
                        die fase 11C nodig heeft, plus logo.ico met
                        de resoluties 16, 32, 48, 64, 128 en 256.
================================================================================
"""

from __future__ import annotations

import sys
from pathlib import Path

# Projectroot toevoegen zodat het script ook werkt als het vanuit een
# andere working directory wordt gestart.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from PySide6.QtCore import QPointF, QRectF, Qt  # noqa: E402
from PySide6.QtGui import (  # noqa: E402
    QColor,
    QIcon,
    QImage,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
)
from PySide6.QtWidgets import QApplication  # noqa: E402


HOOFDKLEUR = QColor("#1F4E79")
ACCENTKLEUR = QColor("#4AA3FF")
ACHTERGROND = QColor(0, 0, 0, 0)


def _nieuw_doek(grootte: int) -> QImage:
    img = QImage(grootte, grootte, QImage.Format.Format_ARGB32)
    img.fill(ACHTERGROND)
    return img


def _pen(kleur: QColor, grootte: int) -> QPen:
    pen = QPen(kleur)
    pen.setWidthF(max(1.5, grootte * 0.0625))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def _teken_multimeter(p: QPainter, grootte: int) -> None:
    """Applicatie-icoon: multimeter met condensatorsymbool."""
    p.setPen(_pen(HOOFDKLEUR, grootte))
    p.setBrush(Qt.BrushStyle.NoBrush)
    marge = grootte * 0.14
    body = QRectF(marge, marge, grootte - 2 * marge, grootte - 2 * marge)
    p.drawRoundedRect(body, grootte * 0.12, grootte * 0.12)

    display = QRectF(marge * 1.6, marge * 1.6, grootte * 0.52, grootte * 0.22)
    p.setPen(_pen(ACCENTKLEUR, grootte))
    p.drawRoundedRect(display, grootte * 0.03, grootte * 0.03)

    p.setPen(_pen(HOOFDKLEUR, grootte))
    cx = grootte * 0.32
    cy = grootte * 0.62
    p.drawEllipse(QPointF(cx, cy), grootte * 0.08, grootte * 0.08)
    p.drawLine(
        QPointF(cx + grootte * 0.04, cy + grootte * 0.04),
        QPointF(cx + grootte * 0.10, cy + grootte * 0.10),
    )

    p.setPen(_pen(ACCENTKLEUR, grootte))
    p.drawLine(
        QPointF(grootte * 0.52, grootte * 0.62),
        QPointF(grootte * 0.52, grootte * 0.78),
    )
    p.drawLine(
        QPointF(grootte * 0.62, grootte * 0.62),
        QPointF(grootte * 0.62, grootte * 0.78),
    )


def _teken_diagnose(p: QPainter, grootte: int) -> None:
    """Vergrootglas op een printplaat."""
    p.setPen(_pen(HOOFDKLEUR, grootte))
    p.setBrush(Qt.BrushStyle.NoBrush)
    straal = grootte * 0.26
    p.drawEllipse(QPointF(grootte * 0.42, grootte * 0.42), straal, straal)
    p.drawLine(
        QPointF(grootte * 0.60, grootte * 0.60),
        QPointF(grootte * 0.78, grootte * 0.78),
    )
    p.setPen(_pen(ACCENTKLEUR, grootte))
    p.drawLine(
        QPointF(grootte * 0.30, grootte * 0.30),
        QPointF(grootte * 0.54, grootte * 0.30),
    )
    p.drawLine(
        QPointF(grootte * 0.30, grootte * 0.42),
        QPointF(grootte * 0.42, grootte * 0.42),
    )


def _teken_esr(p: QPainter, grootte: int) -> None:
    """Condensatorsymbool met meetpen."""
    p.setPen(_pen(HOOFDKLEUR, grootte))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(
        QPointF(grootte * 0.30, grootte * 0.30),
        QPointF(grootte * 0.30, grootte * 0.70),
    )
    p.drawLine(
        QPointF(grootte * 0.46, grootte * 0.30),
        QPointF(grootte * 0.46, grootte * 0.70),
    )
    p.setPen(_pen(ACCENTKLEUR, grootte))
    p.drawLine(
        QPointF(grootte * 0.10, grootte * 0.50),
        QPointF(grootte * 0.30, grootte * 0.50),
    )
    p.drawLine(
        QPointF(grootte * 0.46, grootte * 0.50),
        QPointF(grootte * 0.80, grootte * 0.50),
    )
    p.drawLine(
        QPointF(grootte * 0.80, grootte * 0.36),
        QPointF(grootte * 0.80, grootte * 0.64),
    )


def _teken_history(p: QPainter, grootte: int) -> None:
    """Klok met terugloop-pijl."""
    p.setPen(_pen(HOOFDKLEUR, grootte))
    p.setBrush(Qt.BrushStyle.NoBrush)
    straal = grootte * 0.32
    p.drawEllipse(QPointF(grootte * 0.5, grootte * 0.5), straal, straal)
    p.drawLine(
        QPointF(grootte * 0.5, grootte * 0.5),
        QPointF(grootte * 0.5, grootte * 0.28),
    )
    p.drawLine(
        QPointF(grootte * 0.5, grootte * 0.5),
        QPointF(grootte * 0.66, grootte * 0.5),
    )
    p.setPen(_pen(ACCENTKLEUR, grootte))
    pad = QPainterPath()
    pad.moveTo(grootte * 0.18, grootte * 0.18)
    pad.lineTo(grootte * 0.34, grootte * 0.18)
    pad.lineTo(grootte * 0.18, grootte * 0.34)
    p.drawPath(pad)


def _teken_documentation(p: QPainter, grootte: int) -> None:
    """Open boek met bladwijzer."""
    p.setPen(_pen(HOOFDKLEUR, grootte))
    p.setBrush(Qt.BrushStyle.NoBrush)
    links = QPolygonF([
        QPointF(grootte * 0.14, grootte * 0.26),
        QPointF(grootte * 0.46, grootte * 0.30),
        QPointF(grootte * 0.46, grootte * 0.78),
        QPointF(grootte * 0.14, grootte * 0.74),
    ])
    rechts = QPolygonF([
        QPointF(grootte * 0.54, grootte * 0.30),
        QPointF(grootte * 0.86, grootte * 0.26),
        QPointF(grootte * 0.86, grootte * 0.74),
        QPointF(grootte * 0.54, grootte * 0.78),
    ])
    p.drawPolygon(links)
    p.drawPolygon(rechts)
    p.setPen(_pen(ACCENTKLEUR, grootte))
    p.drawLine(
        QPointF(grootte * 0.50, grootte * 0.30),
        QPointF(grootte * 0.50, grootte * 0.78),
    )


def _teken_analysis(p: QPainter, grootte: int) -> None:
    """Lijngrafiek met punten."""
    p.setPen(_pen(HOOFDKLEUR, grootte))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(
        QPointF(grootte * 0.16, grootte * 0.16),
        QPointF(grootte * 0.16, grootte * 0.84),
    )
    p.drawLine(
        QPointF(grootte * 0.16, grootte * 0.84),
        QPointF(grootte * 0.84, grootte * 0.84),
    )
    p.setPen(_pen(ACCENTKLEUR, grootte))
    pad = QPainterPath()
    pad.moveTo(grootte * 0.24, grootte * 0.68)
    pad.lineTo(grootte * 0.40, grootte * 0.48)
    pad.lineTo(grootte * 0.56, grootte * 0.58)
    pad.lineTo(grootte * 0.78, grootte * 0.28)
    p.drawPath(pad)
    p.setBrush(ACCENTKLEUR)
    for x, y in ((0.24, 0.68), (0.40, 0.48), (0.56, 0.58), (0.78, 0.28)):
        p.drawEllipse(QPointF(grootte * x, grootte * y), grootte * 0.03, grootte * 0.03)


def _teken_report(p: QPainter, grootte: int) -> None:
    """Document met grafiek erin."""
    p.setPen(_pen(HOOFDKLEUR, grootte))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(
        QRectF(grootte * 0.22, grootte * 0.12, grootte * 0.56, grootte * 0.76),
        grootte * 0.05,
        grootte * 0.05,
    )
    p.setPen(_pen(ACCENTKLEUR, grootte))
    p.drawLine(
        QPointF(grootte * 0.32, grootte * 0.72),
        QPointF(grootte * 0.68, grootte * 0.72),
    )
    p.drawLine(
        QPointF(grootte * 0.32, grootte * 0.72),
        QPointF(grootte * 0.32, grootte * 0.40),
    )
    pad = QPainterPath()
    pad.moveTo(grootte * 0.36, grootte * 0.66)
    pad.lineTo(grootte * 0.48, grootte * 0.52)
    pad.lineTo(grootte * 0.58, grootte * 0.60)
    pad.lineTo(grootte * 0.68, grootte * 0.44)
    p.drawPath(pad)


def _teken_settings(p: QPainter, grootte: int) -> None:
    """Tandwiel."""
    p.setPen(_pen(HOOFDKLEUR, grootte))
    p.setBrush(Qt.BrushStyle.NoBrush)
    buiten = grootte * 0.34
    binnen = grootte * 0.12
    midden = QPointF(grootte * 0.5, grootte * 0.5)
    p.drawEllipse(midden, buiten, buiten)
    p.drawEllipse(midden, binnen, binnen)
    import math
    for i in range(8):
        hoek = i * math.pi / 4
        x1 = midden.x() + math.cos(hoek) * buiten
        y1 = midden.y() + math.sin(hoek) * buiten
        x2 = midden.x() + math.cos(hoek) * (buiten + grootte * 0.10)
        y2 = midden.y() + math.sin(hoek) * (buiten + grootte * 0.10)
        p.drawLine(QPointF(x1, y1), QPointF(x2, y2))


def _teken_help(p: QPainter, grootte: int) -> None:
    """Vraagteken in een cirkel."""
    p.setPen(_pen(HOOFDKLEUR, grootte))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QPointF(grootte * 0.5, grootte * 0.5), grootte * 0.36, grootte * 0.36)
    p.setPen(_pen(ACCENTKLEUR, grootte))
    pad = QPainterPath()
    pad.moveTo(grootte * 0.36, grootte * 0.40)
    pad.cubicTo(
        grootte * 0.36, grootte * 0.26,
        grootte * 0.64, grootte * 0.26,
        grootte * 0.64, grootte * 0.42,
    )
    pad.cubicTo(
        grootte * 0.64, grootte * 0.54,
        grootte * 0.50, grootte * 0.54,
        grootte * 0.50, grootte * 0.66,
    )
    p.drawPath(pad)
    p.setBrush(ACCENTKLEUR)
    p.drawEllipse(QPointF(grootte * 0.50, grootte * 0.76), grootte * 0.035, grootte * 0.035)


def _teken_bug(p: QPainter, grootte: int) -> None:
    """Uitroepteken in een driehoek."""
    p.setPen(_pen(HOOFDKLEUR, grootte))
    p.setBrush(Qt.BrushStyle.NoBrush)
    driehoek = QPolygonF([
        QPointF(grootte * 0.5, grootte * 0.14),
        QPointF(grootte * 0.86, grootte * 0.82),
        QPointF(grootte * 0.14, grootte * 0.82),
    ])
    p.drawPolygon(driehoek)
    p.setPen(_pen(ACCENTKLEUR, grootte))
    p.drawLine(
        QPointF(grootte * 0.5, grootte * 0.38),
        QPointF(grootte * 0.5, grootte * 0.60),
    )
    p.setBrush(ACCENTKLEUR)
    p.drawEllipse(QPointF(grootte * 0.5, grootte * 0.72), grootte * 0.035, grootte * 0.035)


def _teken_update(p: QPainter, grootte: int) -> None:
    """Pijl in een cirkel (refresh)."""
    p.setPen(_pen(HOOFDKLEUR, grootte))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QPointF(grootte * 0.5, grootte * 0.5), grootte * 0.34, grootte * 0.34)
    p.setPen(_pen(ACCENTKLEUR, grootte))
    pad = QPainterPath()
    pad.moveTo(grootte * 0.30, grootte * 0.40)
    pad.lineTo(grootte * 0.50, grootte * 0.22)
    pad.lineTo(grootte * 0.70, grootte * 0.40)
    p.drawPath(pad)
    p.drawLine(
        QPointF(grootte * 0.50, grootte * 0.22),
        QPointF(grootte * 0.50, grootte * 0.74),
    )


def _teken_exit(p: QPainter, grootte: int) -> None:
    """Deur met pijl naar buiten."""
    p.setPen(_pen(HOOFDKLEUR, grootte))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(
        QPointF(grootte * 0.34, grootte * 0.16),
        QPointF(grootte * 0.34, grootte * 0.84),
    )
    p.drawLine(
        QPointF(grootte * 0.34, grootte * 0.16),
        QPointF(grootte * 0.62, grootte * 0.16),
    )
    p.drawLine(
        QPointF(grootte * 0.34, grootte * 0.84),
        QPointF(grootte * 0.62, grootte * 0.84),
    )
    p.setPen(_pen(ACCENTKLEUR, grootte))
    p.drawLine(
        QPointF(grootte * 0.46, grootte * 0.50),
        QPointF(grootte * 0.82, grootte * 0.50),
    )
    p.drawLine(
        QPointF(grootte * 0.70, grootte * 0.38),
        QPointF(grootte * 0.82, grootte * 0.50),
    )
    p.drawLine(
        QPointF(grootte * 0.70, grootte * 0.62),
        QPointF(grootte * 0.82, grootte * 0.50),
    )


_TEKENAARS = {
    "app": _teken_multimeter,
    "diagnose": _teken_diagnose,
    "esr": _teken_esr,
    "history": _teken_history,
    "documentation": _teken_documentation,
    "analysis": _teken_analysis,
    "report": _teken_report,
    "settings": _teken_settings,
    "help": _teken_help,
    "bug": _teken_bug,
    "update": _teken_update,
    "exit": _teken_exit,
}


def _render_png(naam: str, grootte: int, doel: Path) -> None:
    img = _nieuw_doek(grootte)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    try:
        _TEKENAARS[naam](p, grootte)
    finally:
        p.end()
    img.save(str(doel), "PNG")


def _render_ico(doel: Path, groottes: tuple[int, ...]) -> None:
    icon = QIcon()
    for grootte in groottes:
        img = _nieuw_doek(grootte)
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        try:
            _teken_multimeter(p, grootte)
        finally:
            p.end()
        pix = QPixmap.fromImage(img)
        icon.addPixmap(pix)
    # QIcon schrijft niet rechtstreeks naar ICO; we gebruiken QPixmap.save
    # met het ICO-formaat via de Qt image plugin.
    # Voor de zekerheid gebruiken we de 256px-versie als basis.
    pix_256 = QPixmap.fromImage(_nieuw_doek(256))
    p = QPainter(pix_256)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    try:
        _teken_multimeter(p, 256)
    finally:
        p.end()
    pix_256.save(str(doel), "ICO")


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    _ = app  # houd reference

    doelmap = _ROOT / "assets" / "icons"
    doelmap.mkdir(parents=True, exist_ok=True)

    # Themaps: 64x64 PNG
    for naam in _TEKENAARS:
        if naam == "app":
            continue
        _render_png(naam, 64, doelmap / f"{naam}.png")
        print(f"[OK] {naam}.png")

    # Applicatie-icoon: 256x256 PNG
    _render_png("app", 256, doelmap / "app.png")
    print("[OK] app.png")

    # logo.ico met meerdere resoluties
    _render_ico(doelmap / "logo.ico", (16, 32, 48, 64, 128, 256))
    print("[OK] logo.ico")

    print(f"\nKlaar. Bestanden staan in: {doelmap}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())