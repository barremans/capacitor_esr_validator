"""
================================================================================
Module:     app/gui/main_window.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     1.1.0
Datum:      2026-08-12
Auteur:     Ontwikkelaar

Doel:       Hoofdvenster van de applicatie met menubalk.
            Opzet voor meerdere test-schermen in de toekomst.
            Nu: ESR-test als eerste en enige testscherm.

Wijzigingen:
  v1.0.0 (2026-08-11)  Initiele versie.
  v1.1.0 (2026-08-12)  About-dialog teksten via vertaal(). Statusbar-tekst
                       via vertaal().
================================================================================
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QMenuBar, QMenu, QStatusBar,
)
from PySide6.QtGui import QAction

from app.helpers.i18n import vertaal
from app.gui.esr_test_screen import EsrTestScreen


class MainWindow(QMainWindow):
    """Hoofdvenster met menubalk en centrale widget voor testschermen."""

    def __init__(self, taal="nl_NL"):
        super().__init__()
        self.taal = taal
        self.setWindowTitle(vertaal("app.titel", taal=taal))
        self.setMinimumSize(900, 700)
        self._build_menu()
        self._build_central_widget()

    def _t(self, sleutel):
        return vertaal(sleutel, taal=self.taal)

    def _build_menu(self):
        menubar = self.menuBar()

        # Bestand menu
        file_menu = menubar.addMenu(self._t("menu.bestand"))
        exit_action = QAction(self._t("menu.afsluiten"), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Test menu
        test_menu = menubar.addMenu(self._t("menu.test"))
        esr_action = QAction(self._t("menu.esr_test"), self)
        esr_action.triggered.connect(self._show_esr_test)
        test_menu.addAction(esr_action)

        # Help menu
        help_menu = menubar.addMenu(self._t("menu.help"))
        about_action = QAction(self._t("menu.over"), self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _build_central_widget(self):
        self.central = QWidget()
        self.layout = QVBoxLayout(self.central)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(self.central)

        # Start met ESR-test scherm
        self._show_esr_test()

    def _show_esr_test(self):
        """Toont het ESR-testscherm."""
        self._clear_layout()
        self.esr_screen = EsrTestScreen(taal=self.taal)
        self.layout.addWidget(self.esr_screen)
        self.statusBar().showMessage(self._t("scherm.esr_test"))

    def _clear_layout(self):
        """Verwijdert alle widgets uit de centrale layout."""
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _show_about(self):
        """Toont het about-dialog."""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(
            self,
            self._t("menu.over"),
            f"<h2>{self._t('app.titel')}</h2>"
            "<p>Versie 1.0</p>"
            f"<p>{self._t('app.titel')}</p>"
            "<p>Geen formele veiligheidsvrijgave.</p>"
        )