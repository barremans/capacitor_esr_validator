"""
================================================================================
Module:     app/gui/styles.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.2.0
Datum:      2026-09-27
Auteur:     Ontwikkelaar

Doel:       Centrale stijldefinities voor de Qt6 GUI.
            Donker thema, statuskleuren, en hulpfuncties voor thematoepassing.

Wijzigingen:
  v1.0.0 (2026-08-11)  Initiele versie. Donker palet, statuskleuren per
                       eindstatus, Segoe UI font.
  v1.1.0 (2026-09-26)  Consistente donkere invoervelden, comboboxen,
                       tekstweergave en checkboxen toegevoegd voor beter
                       contrast in het volledige donkere thema.
  v1.2.0 (2026-09-27)  Centrale dark-theme styling uitgebreid voor hoofdvenster,
                       widgets, dialogen, labels, knoppen, group boxes en
                       disabled states. Tooltips blijven bewust licht.
================================================================================
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette, QFont


def apply_dark_theme(app):
    """Past een donker thema toe op de QApplication."""

    palette = QPalette()

    palette.setColor(
        QPalette.ColorRole.Window,
        QColor(45, 45, 48),
    )
    palette.setColor(
        QPalette.ColorRole.WindowText,
        QColor(240, 240, 240),
    )
    palette.setColor(
        QPalette.ColorRole.Base,
        QColor(30, 30, 30),
    )
    palette.setColor(
        QPalette.ColorRole.AlternateBase,
        QColor(45, 45, 48),
    )
    palette.setColor(
        QPalette.ColorRole.ToolTipBase,
        QColor(255, 255, 255),
    )
    palette.setColor(
        QPalette.ColorRole.ToolTipText,
        QColor(0, 0, 0),
    )
    palette.setColor(
        QPalette.ColorRole.Text,
        QColor(240, 240, 240),
    )
    palette.setColor(
        QPalette.ColorRole.Button,
        QColor(45, 45, 48),
    )
    palette.setColor(
        QPalette.ColorRole.ButtonText,
        QColor(240, 240, 240),
    )
    palette.setColor(
        QPalette.ColorRole.BrightText,
        QColor(255, 0, 0),
    )
    palette.setColor(
        QPalette.ColorRole.Highlight,
        QColor(0, 120, 215),
    )
    palette.setColor(
        QPalette.ColorRole.HighlightedText,
        QColor(255, 255, 255),
    )

    app.setPalette(palette)

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Globale stylesheet voor de applicatie
    app.setStyleSheet("""
        QMainWindow, QWidget, QDialog {
            background-color: #2D2D30;
            color: #F0F0F0;
        }

        QLabel {
            color: #F0F0F0;
            background-color: transparent;
        }

        QMenuBar {
            background-color: #2D2D30;
            color: #F0F0F0;
        }

        QMenuBar::item {
            background-color: transparent;
            color: #F0F0F0;
            padding: 4px 12px;
        }

        QMenuBar::item:selected {
            background-color: #0078D7;
            color: #FFFFFF;
        }

        QMenu {
            background-color: #2D2D30;
            color: #F0F0F0;
            border: 1px solid #555555;
        }

        QMenu::item {
            color: #F0F0F0;
            padding: 4px 20px 4px 8px;
        }

        QMenu::item:selected {
            background-color: #0078D7;
            color: #FFFFFF;
        }

        QPushButton {
            background-color: #3C3C3C;
            color: #F0F0F0;
            border: 1px solid #666666;
            border-radius: 4px;
            padding: 6px 12px;
        }

        QPushButton:hover {
            background-color: #4C4C4C;
            border-color: #0078D7;
        }

        QPushButton:pressed {
            background-color: #2C2C2C;
        }

        QPushButton:disabled {
            background-color: #333333;
            color: #8A8A8A;
            border-color: #4A4A4A;
        }

        QLineEdit, QComboBox, QTextBrowser {
            background-color: #1E1E1E;
            color: #F0F0F0;
            border: 1px solid #666666;
            border-radius: 4px;
            padding: 4px 6px;
            selection-background-color: #0078D7;
            selection-color: #FFFFFF;
        }

        QLineEdit:focus, QComboBox:focus, QTextBrowser:focus {
            border: 1px solid #4AA3FF;
        }

        QLineEdit:disabled, QComboBox:disabled, QTextBrowser:disabled {
            background-color: #333333;
            color: #A0A0A0;
            border-color: #555555;
        }

        QComboBox QAbstractItemView {
            background-color: #252526;
            color: #F0F0F0;
            selection-background-color: #0078D7;
            selection-color: #FFFFFF;
            border: 1px solid #555555;
        }

        QCheckBox {
            color: #F0F0F0;
            spacing: 8px;
            background-color: transparent;
        }

        QCheckBox:disabled {
            color: #8A8A8A;
        }

        QGroupBox {
            color: #F0F0F0;
            font-weight: bold;
            border: 1px solid #555555;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 8px;
            background-color: transparent;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px;
            color: #F0F0F0;
        }

        QDialogButtonBox {
            background-color: transparent;
        }

        QToolTip {
            background-color: #F4F4F4;
            color: #202020;
            border: 1px solid #777777;
            padding: 3px;
        }
    """)


# Kleuren per eindstatus — consistent over de hele app
STATUS_COLORS = {
    "waarschijnlijk_goed": "#4CAF50",      # groen
    "aandachtspunt": "#FF9800",            # oranje
    "twijfelachtig": "#FF5722",            # donkeroranje
    "waarschijnlijk_defect": "#F44336",    # rood
    "niet_beoordeeld": "#9E9E9E",          # grijs
    "niet_te_beoordelen": "#9E9E9E",       # grijs
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

    QPushButton:hover {
        background-color: #14A085;
    }

    QPushButton:pressed {
        background-color: #0A5C5F;
    }
"""


# Stijl voor veiligheidswaarschuwingen
SAFETY_WARNING_STYLE = """
    color: #FF9800;
    font-size: 11px;
"""


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