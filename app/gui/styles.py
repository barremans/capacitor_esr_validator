"""
================================================================================
Module:     app/gui/styles.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.0.0
Datum:      2026-08-11
Auteur:     Ontwikkelaar

Doel:       Centrale stijldefinities voor de Qt6 GUI.
            Donker thema, statuskleuren, en hulpfuncties voor thematoepassing.

Wijzigingen:
  v1.0.0 (2026-08-11)  Initiele versie. Donker palet, statuskleuren per
                       eindstatus, Segoe UI font.
================================================================================
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette, QFont


def apply_dark_theme(app):
    """Past een donker thema toe op de QApplication."""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(45, 45, 48))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 48))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Text, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 48))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    font = QFont("Segoe UI", 10)
    app.setFont(font)


# Kleuren per eindstatus — consistent over de hele app
STATUS_COLORS = {
    "waarschijnlijk_goed": "#4CAF50",   # groen
    "aandachtspunt": "#FF9800",          # oranje
    "twijfelachtig": "#FF5722",          # donkeroranje
    "waarschijnlijk_defect": "#F44336",  # rood
    "niet_beoordeeld": "#9E9E9E",        # grijs
    "niet_te_beoordelen": "#9E9E9E",     # grijs
}

# CSS-stijl voor het resultaat-label
RESULT_STATUS_STYLE = """
    QLabel {{
        font-size: 24px;
        font-weight: bold;
        padding: 16px;
        border-radius: 8px;
        background-color: {color};
        color: white;
    }}
"""

# Stijl voor de beoordeel-knop
ASSESS_BUTTON_STYLE = """
    QPushButton {
        background-color: #0D7377;
        color: white;
        padding: 10px 24px;
        font-size: 14px;
        font-weight: bold;
        border-radius: 4px;
    }
    QPushButton:hover { background-color: #14A085; }
    QPushButton:pressed { background-color: #0A5C5F; }
"""

# Stijl voor veiligheidswaarschuwingen
SAFETY_WARNING_STYLE = "color: #FF9800; font-size: 11px;"

# Stijl voor group boxes
GROUP_BOX_STYLE = """
    QGroupBox {
        font-weight: bold;
        border: 1px solid #555;
        border-radius: 4px;
        margin-top: 8px;
        padding-top: 8px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 8px;
        padding: 0 4px;
    }
"""