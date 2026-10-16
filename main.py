"""
================================================================================
Module:     main.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.5.0
Datum:      2026-10-16
Auteur:     Bart Bossuyt

Doel:       Entry point. Start de Qt6 GUI met donker thema en ToolHubWindow.

Wijzigingen:
  v1.0.0 (2026-08-11)  Initiele versie.
  v1.1.0 (2026-08-13)  ToolHubWindow i.p.v. QMainWindow met centrale widget.
  v1.2.0 (2026-10-07)  Qt-stijl expliciet op "Fusion" gezet. De native
                        Windows 10/11-stijl negeert grotendeels CSS op
                        QRadioButton::indicator en QCheckBox::indicator,
                        waardoor radio buttons en checkboxes onzichtbaar
                        bleven in het donkere thema. Fusion respecteert
                        de centrale stylesheet volledig en geeft een
                        consistent donker thema op alle Windows-versies.
  v1.3.0 (2026-10-13)  Fase 9A (packaging):
                        - QT_QPA_FONTDIR wordt nu automatisch gezet op
                          Windows wanneer de variabele nog niet bestaat
                          en C:\\Windows\\Fonts aanwezig is. Zonder deze
                          variabele kan Qt in een PySide6-venv de
                          systeemfonts niet vinden, waardoor PDF-rapporten
                          zwarte blokken tonen in plaats van tekst.
                        - app.setApplicationVersion(__version__) toegevoegd
                          zodat de versie centraal beschikbaar is voor
                          QApplication (o.a. voor de Over-dialoog).
  v1.4.0 (2026-10-14)  Fase 9H (update-check):
                        - ToolHubWindow krijgt check_on_startup mee. De
                          waarde komt uit settings.json
                          (algemeen.controleer_updates_bij_opstarten,
                          default True). main.py geeft de waarde door;
                          de GUI plant daarna de niet-blokkerende check.
  v1.5.0 (2026-10-16)  Fase 11C (iconen):
                        - QApplication krijgt een applicatie-icoon via
                          app/helpers/icon_paths.applicatie_icoon().
                          Fallback-keten: assets/icons/app.png ->
                          assets/icons/logo.ico -> geen icoon (Qt
                          gebruikt dan het systeemstandaardicoon).
                        - Geen wijziging aan de bestaande opstartlogica.
================================================================================
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Fase 9A: Qt kan op Windows in een PySide6-venv de systeemfonts niet
# vinden zonder QT_QPA_FONTDIR. Dat uit zich in PDF-rapporten met zwarte
# blokken in plaats van tekst. We zetten de variabele alleen als:
#   - het platform Windows is, én
#   - de variabele nog niet gezet is, én
#   - C:\Windows\Fonts effectief bestaat.
# Zo overschrijven we nooit een expliciete gebruikerskeuze en doen we op
# andere platformen niets.
if sys.platform == "win32" and "QT_QPA_FONTDIR" not in os.environ:
    _windows_fonts = Path(r"C:\Windows\Fonts")
    if _windows_fonts.is_dir():
        os.environ["QT_QPA_FONTDIR"] = str(_windows_fonts)

from PySide6.QtWidgets import QApplication

from app.gui.main_window import ToolHubWindow
from app.gui.styles import apply_dark_theme
from app.config.settings import laad_instellingen
from app.helpers.icon_paths import applicatie_icoon
from app.version import __version__


def main():
    app = QApplication(sys.argv)

    # Fusion-stijl forceren: de native Windows-stijl negeert CSS op
    # radio buttons en checkboxes. Fusion respecteert de stylesheet.
    app.setStyle("Fusion")

    app.setApplicationName("Condensator- en ESR-validator")
    app.setApplicationDisplayName("Condensator- en ESR-validator")
    app.setApplicationVersion(__version__)

    # Fase 11C: applicatie-icoon. Valt stil terug op logo.ico of op
    # niets als geen van beide bestaat.
    icoon = applicatie_icoon()
    if icoon is not None:
        app.setWindowIcon(icoon)

    apply_dark_theme(app)

    instellingen = laad_instellingen()
    window = ToolHubWindow(
        taal=instellingen.taal,
        check_on_startup=instellingen.algemeen.controleer_updates_bij_opstarten,
    )
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()