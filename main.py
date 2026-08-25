"""
================================================================================
Module:     main.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.1.0
Datum:      2026-08-13
Auteur:     Bart Bossuyt

Doel:       Entry point. Start de Qt6 GUI met donker thema en ToolHubWindow.

Wijzigingen:
  v1.0.0 (2026-08-11)  Initiele versie.
  v1.1.0 (2026-08-13)  ToolHubWindow i.p.v. QMainWindow met centrale widget.
================================================================================
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication

from app.gui.main_window import ToolHubWindow
from app.gui.styles import apply_dark_theme
from app.config.settings import laad_instellingen


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Condensator- en ESR-validator")
    app.setApplicationDisplayName("Condensator- en ESR-validator")

    apply_dark_theme(app)

    instellingen = laad_instellingen()
    window = ToolHubWindow(taal=instellingen.taal)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()