"""
================================================================================
Module:     app/gui/styles.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.7.0
Datum:      2026-10-21
Auteur:     Ontwikkelaar

Doel:       Centrale stijldefinities voor de Qt6 GUI.
            Donker en licht thema, statuskleuren, en hulpfuncties voor
            thematoepassing.

Wijzigingen:
  v1.0.0 (2026-08-11)  Initiele versie. Donker palet, statuskleuren per
                       eindstatus, Segoe UI font.
  v1.1.0 (2026-09-26)  Consistente donkere invoervelden, comboboxen,
                       tekstweergave en checkboxen toegevoegd voor beter
                       contrast in het volledige donkere thema.
  v1.2.0 (2026-09-27)  Centrale dark-theme styling uitgebreid voor hoofdvenster,
                       widgets, dialogen, labels, knoppen, group boxes en
                       disabled states. Tooltips blijven bewust licht.
  v1.3.0 (2026-10-08)  Fase 5D'.2f: expliciete styling voor
                       QCheckBox::indicator en QRadioButton::indicator.
  v1.4.0 (2026-10-20)  Fase 11G.1: focus-states voor QCheckBox::indicator
                       en QRadioButton::indicator. QTableView::indicator
                       toegevoegd. QGroupBox::indicator voor checkable
                       group boxes. QComboBox::drop-down:hover.
                       Stylesheet-string verplaatst naar module-level
                       constante DARK_THEME_STYLESHEET.
  v1.5.0 (2026-10-20)  Fase 11G.2: donkere QScrollBar:vertical en
                       QScrollBar:horizontal voor alle scrollbare widgets.
                       Pijl-knoppen (add-line/sub-line) uitgeschakeld.
  v1.6.0 (2026-10-20)  Fase 11G.7: QGroupBox::indicator duidelijker
                       zichtbaar in donker thema. Unchecked-state krijgt
                       een lichtere achtergrond (#3C3C3C) en een dikkere
                       rand (2px #B0B0B0), zodat het indicator-vierkantje
                       niet wegvalt tegen de groupbox-rand. Checked-state
                       is blauw met duidelijke rand; hover en disabled
                       consistent. Lost het visuele probleem op waarbij
                       de checkbox links van "Filters" nauwelijks
                       zichtbaar was. Geen wijziging aan de GUI-bestanden.
  v1.7.0 (2026-10-21)  Fase 11H.1: light theme.
                       - Nieuwe LIGHT_THEME_STYLESHEET met dezelfde
                         structuur als DARK_THEME_STYLESHEET, maar lichte
                         kleuren: witte invoervelden, donkere tekst,
                         lichte groupbox-randen, lichte scrollbar.
                       - QGroupBox::indicator:unchecked in licht thema
                         krijgt een witte achtergrond met 2px #5A5A5A-rand,
                         consistent met de 11G.7-fix in donker thema, zodat
                         de checkbox niet wegvalt tegen de groupbox-rand.
                       - Nieuwe THEME_STYLESHEETS-dict en
                         apply_theme(app, thema="dark")-API.
                       - apply_dark_theme(app) blijft als dunne wrapper
                         voor backward-compat (main.py en bestaande tests
                         blijven werken tot 11H.3).
                       - Onbekende thema-waarde valt terug op "dark".
                       - Geen wijziging aan STATUS_COLORS,
                         RESULT_STATUS_STYLE, ASSESS_BUTTON_STYLE,
                         SAFETY_WARNING_STYLE of GROUP_BOX_STYLE.
================================================================================
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette, QFont


DARK_THEME_STYLESHEET = """
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

    QComboBox::drop-down {
        border: none;
        width: 18px;
    }

    QComboBox::drop-down:hover {
        background-color: #3C3C3C;
    }

    QCheckBox {
        color: #F0F0F0;
        spacing: 8px;
        background-color: transparent;
    }

    QCheckBox:disabled {
        color: #8A8A8A;
    }

    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border: 1px solid #8A8A8A;
        border-radius: 3px;
        background-color: #2A2A2A;
    }

    QCheckBox::indicator:unchecked {
        background-color: #2A2A2A;
        border: 1px solid #8A8A8A;
    }

    QCheckBox::indicator:unchecked:hover {
        background-color: #333333;
        border: 1px solid #B0B0B0;
    }

    QCheckBox::indicator:checked {
        background-color: #0078D7;
        border: 1px solid #4AA3FF;
    }

    QCheckBox::indicator:checked:hover {
        background-color: #1A88E7;
        border: 1px solid #6ABAFF;
    }

    QCheckBox::indicator:disabled {
        background-color: #1E1E1E;
        border: 1px solid #4A4A4A;
    }

    QCheckBox::indicator:focus {
        border: 2px solid #4AA3FF;
    }

    QRadioButton {
        color: #F0F0F0;
        spacing: 8px;
        background-color: transparent;
    }

    QRadioButton:disabled {
        color: #8A8A8A;
    }

    QRadioButton::indicator {
        width: 16px;
        height: 16px;
        border: 1px solid #8A8A8A;
        border-radius: 8px;
        background-color: #2A2A2A;
    }

    QRadioButton::indicator:unchecked {
        background-color: #2A2A2A;
        border: 1px solid #8A8A8A;
    }

    QRadioButton::indicator:unchecked:hover {
        background-color: #333333;
        border: 1px solid #B0B0B0;
    }

    QRadioButton::indicator:checked {
        background-color: #0078D7;
        border: 1px solid #4AA3FF;
    }

    QRadioButton::indicator:checked:hover {
        background-color: #1A88E7;
        border: 1px solid #6ABAFF;
    }

    QRadioButton::indicator:disabled {
        background-color: #1E1E1E;
        border: 1px solid #4A4A4A;
    }

    QRadioButton::indicator:focus {
        border: 2px solid #4AA3FF;
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

    QGroupBox::indicator {
        width: 16px;
        height: 16px;
        border: 2px solid #B0B0B0;
        border-radius: 3px;
        background-color: #3C3C3C;
    }

    QGroupBox::indicator:unchecked {
        background-color: #3C3C3C;
        border: 2px solid #B0B0B0;
    }

    QGroupBox::indicator:unchecked:hover {
        background-color: #4C4C4C;
        border: 2px solid #D0D0D0;
    }

    QGroupBox::indicator:checked {
        background-color: #0078D7;
        border: 2px solid #4AA3FF;
    }

    QGroupBox::indicator:checked:hover {
        background-color: #1A88E7;
        border: 2px solid #6ABAFF;
    }

    QGroupBox::indicator:disabled {
        background-color: #1E1E1E;
        border: 2px solid #4A4A4A;
    }

    QGroupBox::indicator:focus {
        border: 2px solid #4AA3FF;
    }

    QTableView::indicator {
        width: 16px;
        height: 16px;
        border: 1px solid #8A8A8A;
        border-radius: 3px;
        background-color: #2A2A2A;
    }

    QTableView::indicator:unchecked {
        background-color: #2A2A2A;
        border: 1px solid #8A8A8A;
    }

    QTableView::indicator:unchecked:hover {
        background-color: #333333;
        border: 1px solid #B0B0B0;
    }

    QTableView::indicator:checked {
        background-color: #0078D7;
        border: 1px solid #4AA3FF;
    }

    QTableView::indicator:checked:hover {
        background-color: #1A88E7;
        border: 1px solid #6ABAFF;
    }

    QTableView::indicator:focus {
        border: 2px solid #4AA3FF;
    }

    QScrollBar:vertical {
        background: #1E1E1E;
        width: 12px;
        margin: 0;
        border: none;
    }

    QScrollBar::handle:vertical {
        background: #4A4A4A;
        min-height: 24px;
        border-radius: 4px;
        margin: 1px;
    }

    QScrollBar::handle:vertical:hover {
        background: #5A5A5A;
    }

    QScrollBar::handle:vertical:pressed {
        background: #0078D7;
    }

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0;
        background: none;
        border: none;
    }

    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {
        background: none;
        border: none;
    }

    QScrollBar:horizontal {
        background: #1E1E1E;
        height: 12px;
        margin: 0;
        border: none;
    }

    QScrollBar::handle:horizontal {
        background: #4A4A4A;
        min-width: 24px;
        border-radius: 4px;
        margin: 1px;
    }

    QScrollBar::handle:horizontal:hover {
        background: #5A5A5A;
    }

    QScrollBar::handle:horizontal:pressed {
        background: #0078D7;
    }

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {
        width: 0;
        background: none;
        border: none;
    }

    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {
        background: none;
        border: none;
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
"""


LIGHT_THEME_STYLESHEET = """
    QMainWindow, QWidget, QDialog {
        background-color: #F4F4F4;
        color: #202020;
    }

    QLabel {
        color: #202020;
        background-color: transparent;
    }

    QMenuBar {
        background-color: #F4F4F4;
        color: #202020;
    }

    QMenuBar::item {
        background-color: transparent;
        color: #202020;
        padding: 4px 12px;
    }

    QMenuBar::item:selected {
        background-color: #0078D7;
        color: #FFFFFF;
    }

    QMenu {
        background-color: #FFFFFF;
        color: #202020;
        border: 1px solid #B0B0B0;
    }

    QMenu::item {
        color: #202020;
        padding: 4px 20px 4px 8px;
    }

    QMenu::item:selected {
        background-color: #0078D7;
        color: #FFFFFF;
    }

    QPushButton {
        background-color: #E8E8E8;
        color: #202020;
        border: 1px solid #B0B0B0;
        border-radius: 4px;
        padding: 6px 12px;
    }

    QPushButton:hover {
        background-color: #DCDCDC;
        border-color: #0078D7;
    }

    QPushButton:pressed {
        background-color: #C8C8C8;
    }

    QPushButton:disabled {
        background-color: #EDEDED;
        color: #8A8A8A;
        border-color: #CCCCCC;
    }

    QLineEdit, QComboBox, QTextBrowser {
        background-color: #FFFFFF;
        color: #202020;
        border: 1px solid #B0B0B0;
        border-radius: 4px;
        padding: 4px 6px;
        selection-background-color: #0078D7;
        selection-color: #FFFFFF;
    }

    QLineEdit:focus, QComboBox:focus, QTextBrowser:focus {
        border: 1px solid #4AA3FF;
    }

    QLineEdit:disabled, QComboBox:disabled, QTextBrowser:disabled {
        background-color: #EDEDED;
        color: #8A8A8A;
        border-color: #CCCCCC;
    }

    QComboBox QAbstractItemView {
        background-color: #FFFFFF;
        color: #202020;
        selection-background-color: #0078D7;
        selection-color: #FFFFFF;
        border: 1px solid #B0B0B0;
    }

    QComboBox::drop-down {
        border: none;
        width: 18px;
    }

    QComboBox::drop-down:hover {
        background-color: #E8E8E8;
    }

    QCheckBox {
        color: #202020;
        spacing: 8px;
        background-color: transparent;
    }

    QCheckBox:disabled {
        color: #8A8A8A;
    }

    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border: 1px solid #5A5A5A;
        border-radius: 3px;
        background-color: #FFFFFF;
    }

    QCheckBox::indicator:unchecked {
        background-color: #FFFFFF;
        border: 1px solid #5A5A5A;
    }

    QCheckBox::indicator:unchecked:hover {
        background-color: #F0F0F0;
        border: 1px solid #0078D7;
    }

    QCheckBox::indicator:checked {
        background-color: #0078D7;
        border: 1px solid #005A9E;
    }

    QCheckBox::indicator:checked:hover {
        background-color: #1A88E7;
        border: 1px solid #005A9E;
    }

    QCheckBox::indicator:disabled {
        background-color: #EDEDED;
        border: 1px solid #CCCCCC;
    }

    QCheckBox::indicator:focus {
        border: 2px solid #4AA3FF;
    }

    QRadioButton {
        color: #202020;
        spacing: 8px;
        background-color: transparent;
    }

    QRadioButton:disabled {
        color: #8A8A8A;
    }

    QRadioButton::indicator {
        width: 16px;
        height: 16px;
        border: 1px solid #5A5A5A;
        border-radius: 8px;
        background-color: #FFFFFF;
    }

    QRadioButton::indicator:unchecked {
        background-color: #FFFFFF;
        border: 1px solid #5A5A5A;
    }

    QRadioButton::indicator:unchecked:hover {
        background-color: #F0F0F0;
        border: 1px solid #0078D7;
    }

    QRadioButton::indicator:checked {
        background-color: #0078D7;
        border: 1px solid #005A9E;
    }

    QRadioButton::indicator:checked:hover {
        background-color: #1A88E7;
        border: 1px solid #005A9E;
    }

    QRadioButton::indicator:disabled {
        background-color: #EDEDED;
        border: 1px solid #CCCCCC;
    }

    QRadioButton::indicator:focus {
        border: 2px solid #4AA3FF;
    }

    QGroupBox {
        color: #202020;
        font-weight: bold;
        border: 1px solid #B0B0B0;
        border-radius: 4px;
        margin-top: 8px;
        padding-top: 8px;
        background-color: transparent;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        left: 8px;
        padding: 0 4px;
        color: #202020;
    }

    QGroupBox::indicator {
        width: 16px;
        height: 16px;
        border: 2px solid #5A5A5A;
        border-radius: 3px;
        background-color: #FFFFFF;
    }

    QGroupBox::indicator:unchecked {
        background-color: #FFFFFF;
        border: 2px solid #5A5A5A;
    }

    QGroupBox::indicator:unchecked:hover {
        background-color: #F0F0F0;
        border: 2px solid #0078D7;
    }

    QGroupBox::indicator:checked {
        background-color: #0078D7;
        border: 2px solid #005A9E;
    }

    QGroupBox::indicator:checked:hover {
        background-color: #1A88E7;
        border: 2px solid #005A9E;
    }

    QGroupBox::indicator:disabled {
        background-color: #EDEDED;
        border: 2px solid #CCCCCC;
    }

    QGroupBox::indicator:focus {
        border: 2px solid #4AA3FF;
    }

    QTableView::indicator {
        width: 16px;
        height: 16px;
        border: 1px solid #5A5A5A;
        border-radius: 3px;
        background-color: #FFFFFF;
    }

    QTableView::indicator:unchecked {
        background-color: #FFFFFF;
        border: 1px solid #5A5A5A;
    }

    QTableView::indicator:unchecked:hover {
        background-color: #F0F0F0;
        border: 1px solid #0078D7;
    }

    QTableView::indicator:checked {
        background-color: #0078D7;
        border: 1px solid #005A9E;
    }

    QTableView::indicator:checked:hover {
        background-color: #1A88E7;
        border: 1px solid #005A9E;
    }

    QTableView::indicator:focus {
        border: 2px solid #4AA3FF;
    }

    QScrollBar:vertical {
        background: #E0E0E0;
        width: 12px;
        margin: 0;
        border: none;
    }

    QScrollBar::handle:vertical {
        background: #B0B0B0;
        min-height: 24px;
        border-radius: 4px;
        margin: 1px;
    }

    QScrollBar::handle:vertical:hover {
        background: #909090;
    }

    QScrollBar::handle:vertical:pressed {
        background: #0078D7;
    }

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0;
        background: none;
        border: none;
    }

    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {
        background: none;
        border: none;
    }

    QScrollBar:horizontal {
        background: #E0E0E0;
        height: 12px;
        margin: 0;
        border: none;
    }

    QScrollBar::handle:horizontal {
        background: #B0B0B0;
        min-width: 24px;
        border-radius: 4px;
        margin: 1px;
    }

    QScrollBar::handle:horizontal:hover {
        background: #909090;
    }

    QScrollBar::handle:horizontal:pressed {
        background: #0078D7;
    }

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {
        width: 0;
        background: none;
        border: none;
    }

    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {
        background: none;
        border: none;
    }

    QDialogButtonBox {
        background-color: transparent;
    }

    QToolTip {
        background-color: #202020;
        color: #F4F4F4;
        border: 1px solid #777777;
        padding: 3px;
    }
"""


THEME_STYLESHEETS = {
    "dark": DARK_THEME_STYLESHEET,
    "light": LIGHT_THEME_STYLESHEET,
}


def _dark_palette() -> QPalette:
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
    return palette


def _light_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(244, 244, 244))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(32, 32, 32))
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(244, 244, 244))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(32, 32, 32))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(244, 244, 244))
    palette.setColor(QPalette.ColorRole.Text, QColor(32, 32, 32))
    palette.setColor(QPalette.ColorRole.Button, QColor(232, 232, 232))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(32, 32, 32))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(200, 0, 0))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    return palette


def apply_theme(app, thema: str = "dark") -> None:
    """Past het opgegeven thema toe op de QApplication.

    Onbekende waarden vallen terug op "dark" (backward-compat: de app
    ondersteunde tot 11H.1 uitsluitend het donkere thema).
    """
    if thema == "light":
        palette = _light_palette()
    else:
        thema = "dark"
        palette = _dark_palette()

    app.setPalette(palette)

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    app.setStyleSheet(THEME_STYLESHEETS[thema])


def apply_dark_theme(app) -> None:
    """Backward-compat-wrapper. Gebruik in nieuwe code apply_theme()."""
    apply_theme(app, "dark")


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