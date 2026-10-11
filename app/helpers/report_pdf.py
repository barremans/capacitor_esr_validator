"""
================================================================================
Module:     app/helpers/report_pdf.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-10
Auteur:     Bart Bossuyt

Doel:       Qt-specifieke PDF-export voor meetrapporten.

            Gebruikt QTextDocument + QPrinter om een HTML-string om te zetten
            naar een PDF-bestand. Geen nieuwe dependency: QPrinter en
            QTextDocument zitten standaard bij PySide6.

            De HTML komt uit app/helpers/report_render.py; deze module
            rendert alleen naar PDF. Ze kent geen database en herberekent
            niets.

Wijzigingen:
  v1.0.0 (2026-10-10)  Eerste versie: write_html_to_pdf(), A4-portret,
                        15 mm marges, PDF-metadata (titel, auteur, maker).
================================================================================
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMarginsF
from PySide6.QtGui import QPageLayout, QPageSize, QTextDocument
from PySide6.QtPrintSupport import QPrinter


APP_AUTEUR = "Electronics Diagnostic Tool Hub"
APP_MAKER = "Electronics Diagnostic Tool Hub / ESR Tester"


def write_html_to_pdf(
    html: str,
    file_path: str | Path,
    *,
    titel: str = "",
    auteur: str = APP_AUTEUR,
) -> Path:
    """Schrijf een HTML-string naar een PDF-bestand.

    - A4, portret, 15 mm marges aan alle zijden.
    - PDF-metadata: titel, auteur, maker.
    - Geeft het uUiteindelijke Path terug.

    Gooit ValueError bij een lege HTML-string of een leeg pad.
    Gooit OSError als het bestand niet geschreven kan worden.
    """
    if not isinstance(html, str) or not html.strip():
        raise ValueError("HTML-string is leeg.")
    if file_path is None or str(file_path).strip() == "":
        raise ValueError("file_path is leeg.")

    pad = Path(file_path)

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(str(pad))
    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    printer.setPageOrientation(QPageLayout.Orientation.Portrait)
    printer.setPageMargins(
        QMarginsF(15.0, 15.0, 15.0, 15.0),
        QPageLayout.Unit.Millimeter,
    )
    printer.setDocName(titel or "rapport")
    printer.setCreator(APP_MAKER)

    document = QTextDocument()
    document.setHtml(html)
    if titel:
        document.setMetaInformation(QTextDocument.MetaInformation.DocumentTitle, titel)
    document.setMetaInformation(
        QTextDocument.MetaInformation.DocumentTitle,
        titel or "rapport",
    )
    document.print_(printer)

    if not pad.exists():
        raise OSError(f"PDF-bestand kon niet worden geschreven: {pad}")
    return pad