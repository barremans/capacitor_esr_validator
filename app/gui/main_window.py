"""
================================================================================
Module:     app/gui/main_window.py
Project:    Condensator- en ESR-validator (Windows)
Versie:     2.0.0
Datum:      2026-08-13
Auteur:     Bart Bossuyt

Doel:       Tool-hub startscherm. Compact venster met knoppen voor elke tool.
            ESR-test opent als apart venster.

Wijzigingen:
  v1.0.0 (2026-08-11)  Initiele versie — QMainWindow met centrale widget.
  v2.0.0 (2026-08-13)  Herontworpen naar ToolHubWindow. Knoppen-hub voor
                       meerdere tools. ESR-test opent als apart venster.
                       Menu: Bestand, Tools, Instellingen, Help.
                       Snelkoppelingen: Ctrl+Q, Ctrl+E, F1.
================================================================================
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QMenuBar, QMenu,
    QMessageBox, QTextBrowser, QDialog, QDialogButtonBox,
    QScrollArea, QFrame,
)
from PySide6.QtGui import QAction, QKeySequence, QShortcut, QIcon, QPixmap
from PySide6.QtCore import Qt, QSize

from app.helpers.i18n import vertaal
from app.config.settings import laad_instellingen, sla_instellingen_op, AppInstellingen


class ToolHubWindow(QMainWindow):
    """Startscherm — hub met knoppen voor alle beschikbare tools."""

    def __init__(self, taal="nl_NL"):
        super().__init__()
        self.taal = taal
        self.instellingen = laad_instellingen()
        self.taal = self.instellingen.taal
        self.esr_window = None
        self._build_ui()
        self._apply_language()

    def _t(self, sleutel, **kwargs):
        return vertaal(sleutel, taal=self.taal, **kwargs)

    def _build_ui(self):
        self.setWindowTitle(self._t("app.titel"))
        self.setMinimumSize(500, 400)
        self.resize(500, 400)

        # Centrale widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Titel
        title = QLabel(self._t("app.titel"))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #F0F0F0;")
        layout.addWidget(title)

        # Subtitel
        subtitle = QLabel("Tool Hub")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 12px; color: #AAAAAA;")
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # Tool-knoppen grid
        tools_grid = QGridLayout()
        tools_grid.setSpacing(16)

        # ESR-tool knop
        self.esr_btn = QPushButton()
        self.esr_btn.setFixedSize(140, 140)
        self.esr_btn.setStyleSheet("""
            QPushButton {
                background-color: #3C3C3C;
                border: 2px solid #555;
                border-radius: 8px;
                color: #F0F0F0;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #4C4C4C; border-color: #0078D7; }
            QPushButton:pressed { background-color: #2C2C2C; }
        """)
        self.esr_btn.setToolTip(self._t("tool.esr_omschrijving"))
        self.esr_btn.clicked.connect(self._open_esr_test)

        # Icoon laden (fallback naar tekst als icoon ontbreekt)
        icon_path = "assets/icons/esr.png"
        if QPixmap(icon_path).isNull():
            self.esr_btn.setText("ESR")
        else:
            self.esr_btn.setIcon(QIcon(icon_path))
            self.esr_btn.setIconSize(QSize(64, 64))
            self.esr_btn.setText("ESR")

        tools_grid.addWidget(self.esr_btn, 0, 0, Qt.AlignmentFlag.AlignCenter)

        # Placeholder voor toekomstige tools
        placeholder = QPushButton("...")
        placeholder.setFixedSize(140, 140)
        placeholder.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2C;
                border: 2px dashed #555;
                border-radius: 8px;
                color: #777;
                font-size: 24px;
            }
        """)
        placeholder.setEnabled(False)
        placeholder.setToolTip("Toekomstige tool")
        tools_grid.addWidget(placeholder, 0, 1, Qt.AlignmentFlag.AlignCenter)

        tools_grid.setColumnStretch(2, 1)
        layout.addLayout(tools_grid)
        layout.addStretch()

        # Menubalk
        self._build_menu()

    def _build_menu(self):
        menubar = self.menuBar()

        # Bestand
        file_menu = menubar.addMenu(self._t("menu.bestand"))
        exit_action = QAction(self._t("menu.afsluiten"), self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools
        tools_menu = menubar.addMenu(self._t("menu.test"))
        esr_action = QAction(self._t("menu.esr_test"), self)
        esr_action.setShortcut(QKeySequence("Ctrl+E"))
        esr_action.triggered.connect(self._open_esr_test)
        tools_menu.addAction(esr_action)

        # Instellingen
        settings_menu = menubar.addMenu(self._t("menu.instellingen"))

        settings_action = QAction(self._t("menu.instellingen") + "...", self)
        settings_action.triggered.connect(self._show_settings)
        settings_menu.addAction(settings_action)

        settings_menu.addSeparator()

        # Talen submenu
        lang_menu = settings_menu.addMenu(self._t("menu.talen"))
        self.lang_nl = QAction("Nederlands", self, checkable=True)
        self.lang_en = QAction("English", self, checkable=True)
        self.lang_nl.triggered.connect(lambda: self._set_language("nl_NL"))
        self.lang_en.triggered.connect(lambda: self._set_language("en_US"))
        lang_menu.addAction(self.lang_nl)
        lang_menu.addAction(self.lang_en)
        self._update_lang_checks()

        # Help
        help_menu = menubar.addMenu(self._t("menu.help"))

        help_action = QAction(self._t("menu.help"), self)
        help_action.setShortcut(QKeySequence("F1"))
        help_action.triggered.connect(self._show_help)
        help_menu.addAction(help_action)

        changelog_action = QAction(self._t("menu.changelog"), self)
        changelog_action.triggered.connect(self._show_changelog)
        help_menu.addAction(changelog_action)

        help_menu.addSeparator()

        about_action = QAction(self._t("menu.over"), self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _update_lang_checks(self):
        self.lang_nl.setChecked(self.taal == "nl_NL")
        self.lang_en.setChecked(self.taal == "en_US")

    def _set_language(self, taal_code):
        self.taal = taal_code
        self.instellingen = AppInstellingen(taal=taal_code)
        sla_instellingen_op(self.instellingen)
        self._update_lang_checks()
        self._apply_language()

    def _apply_language(self):
        self.setWindowTitle(self._t("app.titel"))
        self.menuBar().clear()
        self._build_menu()

    def _open_esr_test(self):
        from app.gui.esr_test_screen import EsrTestScreen
        if self.esr_window is None or not self.esr_window.isVisible():
            self.esr_window = EsrTestScreen(taal=self.taal)
            self.esr_window.setWindowTitle(self._t("app.titel") + " — " + self._t("scherm.esr_test"))
            self.esr_window.show()
        else:
            self.esr_window.raise_()
            self.esr_window.activateWindow()

    def _show_settings(self):
        QMessageBox.information(self, self._t("menu.instellingen"), "Instellingen-dialoog (TODO)")

    def _show_help(self):
        self._show_markdown_dialog(self._t("dialog.help_titel"), "docs/help.md")

    def _show_changelog(self):
        self._show_markdown_dialog(self._t("dialog.changelog_titel"), "docs/changelog.md")

    def _show_markdown_dialog(self, title, filepath):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(700, 500)

        layout = QVBoxLayout(dialog)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            # Eenvoudige markdown naar HTML (kopjes)
            import re
            html = content
            html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.M)
            html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.M)
            html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.M)
            html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', html)
            html = re.sub(r'\*(.+?)\*', r'<i>\1</i>', html)
            html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
            html = re.sub(r'\|(.+?)\|', r'<tr><td>\1</td></tr>', html)
            html = html.replace('\n', '<br>')
            browser.setHtml(f'<body style="font-family: Segoe UI; color: #F0F0F0; background: #2D2D30;">{html}</body>')
        except FileNotFoundError:
            browser.setHtml(f"<p>Bestand niet gevonden: {filepath}</p>")

        layout.addWidget(browser)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()

    def _show_about(self):
        QMessageBox.about(self, self._t("dialog.over_titel"), self._t("dialog.over_tekst"))