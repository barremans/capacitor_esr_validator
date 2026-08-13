"""
================================================================================
Module:     main.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.0.1
Datum:      2026-08-12
Auteur:     Barre

Doel:       Entry point van de applicatie. Start de Qt6 GUI met donker thema.

Wijzigingen:
  v1.0.0 (2026-08-11)  Initiele versie. QApplication setup, donker thema,
                       MainWindow instantiatie.
  v1.0.1 (2026-08-12)  sys.path fix toegevoegd voor robuste module-import
                       op Windows. Lost ModuleNotFoundError op.
================================================================================
"""

import sys
from pathlib import Path

# Zorg dat het projectroot-pad in sys.path staat (robust voor Windows)
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication

from app.gui.main_window import MainWindow
from app.gui.styles import apply_dark_theme


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Condensator- en ESR-validator")
    app.setApplicationDisplayName("Condensator- en ESR-validator")

    apply_dark_theme(app)

    window = MainWindow(taal="nl_NL")
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()