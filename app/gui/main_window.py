"""
================================================================================
Module:     app/gui/main_window.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     2.6.0
Datum:      2026-10-02
Auteur:     Bart Bossuyt

Doel:       Hoofdvenster van de Tool Hub met één-venster-navigatie.
            ESR-test draait als interne pagina binnen hetzelfde hoofdvenster.

Wijzigingen:
  v2.2.1 (2026-09-27)  Settings-dialoog gekoppeld; Apply/OK bewaren alle
                       settings en taalwissel behoudt overige voorkeuren.
  v1.0.0 (2026-08-11)  Initiele versie — QMainWindow met centrale widget.
  v2.0.0 (2026-08-13)  Herontworpen naar ToolHubWindow. Knoppen-hub voor
                       meerdere tools. ESR-test opent als apart venster.
                       Menu: Bestand, Tools, Instellingen, Help.
                       Snelkoppelingen: Ctrl+Q, Ctrl+E, F1.
  v2.1.0 (2026-09-26)  Eén-venster-navigatie met QStackedWidget. ESR-tool
                       opent nu als interne pagina; terugkeer naar Tool Hub
                       zonder tweede top-level venster.
  v2.1.1 (2026-09-26)  Sluitknop (X) gedraagt zich contextueel: vanuit een
                       toolpagina terug naar Tool Hub; vanuit Tool Hub sluit
                       de applicatie wel volledig.
  v2.1.2 (2026-09-27)  Leesbaarheid van Tool Hub en markdown-dialogen verbeterd:
                       expliciete donkere achtergronden, contrastrijke tekst en
                       dialoogknoppen. Ontbrekend-bestandmelding eveneens leesbaar.
  v2.1.3 (2026-09-27)  Dubbele algemene dark-theme styling verwijderd; hoofdvenster
                       en markdown-dialogen gebruiken opnieuw het centrale thema
                       uit app/gui/styles.py. Tool-specifieke accenten behouden.
  v2.2.0 (2026-09-27)  Navigatie uitgebreid naar Hoofdmenu -> Diagnose -> ESR.
                       ESR-Terug/X keert terug naar Diagnose; Diagnose-Terug/X
                       keert terug naar Hoofdmenu. Documentatie is voorbereid.
  v2.3.0 (2026-10-01)  Read-only Historiek als interne pagina toegevoegd.
                       Hoofdmenu opent historiek; Terug/X keert terug naar
                       Hoofdmenu. Historiek ververst bij openen.
  v2.4.0 (2026-10-01)  Historiek "Herhaal meting" gekoppeld aan ESR-pagina.
                       Alleen component- en meetcontext wordt vooraf ingevuld.
  v2.4.1 (2026-10-01)  Live taalwissel vervolledigd voor Hoofdmenu, Diagnose,
                       ESR-pagina en de contextuele venstertitel.
  v2.6.0 (2026-10-03)  Dynamische taalontdekking voor het Talenmenu.
================================================================================
"""

from dataclasses import replace

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QMenuBar, QMenu,
    QMessageBox, QTextBrowser, QDialog, QDialogButtonBox,
    QScrollArea, QFrame, QStackedWidget,
)
from PySide6.QtGui import QAction, QKeySequence, QShortcut, QIcon, QPixmap
from PySide6.QtCore import Qt, QSize

from app.helpers.i18n import beschikbare_taalinfos, vertaal
from app.config.settings import laad_instellingen, sla_instellingen_op, AppInstellingen
from app.gui.dialogs.settings_dialog import SettingsDialog


class ToolHubWindow(QMainWindow):
    """Startscherm — hub met knoppen voor alle beschikbare tools."""

    def __init__(self, taal="nl_NL"):
        super().__init__()
        self.taal = taal
        self.instellingen = laad_instellingen()
        self.taal = self.instellingen.taal
        self._build_ui()
        self._apply_language()

    def _t(self, sleutel, **kwargs):
        return vertaal(sleutel, taal=self.taal, **kwargs)

    def _build_ui(self):
        self.setWindowTitle(self._t("app.titel"))
        self.setMinimumSize(900, 600)
        self.resize(1100, 700)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.hub_page = self._build_hub_page()
        self.stack.addWidget(self.hub_page)

        self.diagnose_page = self._build_diagnose_page()
        self.stack.addWidget(self.diagnose_page)

        from app.gui.esr_test_screen import EsrTestScreen
        self.esr_page = EsrTestScreen(taal=self.taal)
        self.esr_page.back_requested.connect(self._show_diagnose)
        self.stack.addWidget(self.esr_page)

        from app.gui.history_screen import HistoryScreen
        self.history_page = HistoryScreen(taal=self.taal)
        self.history_page.back_requested.connect(self._show_hub)
        self.history_page.repeat_requested.connect(self._repeat_measurement)
        self.stack.addWidget(self.history_page)

        from app.gui.documentation_screen import DocumentationScreen
        self.documentation_page = DocumentationScreen(taal=self.taal)
        self.documentation_page.back_requested.connect(self._show_hub)
        self.stack.addWidget(self.documentation_page)

        self.stack.setCurrentWidget(self.hub_page)
        self._build_menu()

    def _build_hub_page(self):
        """Bouwt het hoofdmenu van de Tool Hub."""
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self.hub_title_label = QLabel(self._t("app.titel"))
        self.hub_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hub_title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(self.hub_title_label)

        self.hub_subtitle_label = QLabel(self._t("scherm.hoofdmenu"))
        self.hub_subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hub_subtitle_label.setStyleSheet("font-size: 12px; color: #AAAAAA;")
        layout.addWidget(self.hub_subtitle_label)
        layout.addSpacing(20)

        menu_grid = QGridLayout()
        menu_grid.setSpacing(16)

        self.diagnose_btn = QPushButton(self._t("tool.diagnose"))
        self.diagnose_btn.setFixedSize(180, 120)
        self.diagnose_btn.setToolTip(self._t("tool.diagnose_omschrijving"))
        self.diagnose_btn.clicked.connect(self._show_diagnose)
        menu_grid.addWidget(
            self.diagnose_btn, 0, 0, Qt.AlignmentFlag.AlignCenter
        )

        self.history_btn = QPushButton(self._t("tool.historiek"))
        self.history_btn.setFixedSize(180, 120)
        self.history_btn.setToolTip(self._t("tool.historiek_omschrijving"))
        self.history_btn.clicked.connect(self._show_history)
        menu_grid.addWidget(
            self.history_btn, 0, 1, Qt.AlignmentFlag.AlignCenter
        )

        self.documentation_btn = QPushButton(self._t("tool.documentatie"))
        self.documentation_btn.setFixedSize(180, 120)
        self.documentation_btn.setToolTip(
            self._t("tool.documentatie_omschrijving")
        )
        self.documentation_btn.clicked.connect(self._show_documentation)
        menu_grid.addWidget(
            self.documentation_btn, 0, 2, Qt.AlignmentFlag.AlignCenter
        )

        menu_grid.setColumnStretch(3, 1)
        layout.addLayout(menu_grid)
        layout.addStretch()
        return central

    def _build_diagnose_page(self):
        """Bouwt de categoriepagina Diagnose."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        top_row = QHBoxLayout()
        self.diagnose_back_btn = QPushButton(self._t("knop.terug"))
        self.diagnose_back_btn.clicked.connect(self._show_hub)
        top_row.addWidget(self.diagnose_back_btn)
        top_row.addStretch()
        layout.addLayout(top_row)

        self.diagnose_title_label = QLabel(self._t("scherm.diagnose"))
        self.diagnose_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.diagnose_title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(self.diagnose_title_label)
        layout.addSpacing(12)

        tools_grid = QGridLayout()
        tools_grid.setSpacing(16)

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
            QPushButton:hover {
                background-color: #4C4C4C;
                border-color: #0078D7;
            }
            QPushButton:pressed { background-color: #2C2C2C; }
        """)
        self.esr_btn.setToolTip(self._t("tool.esr_omschrijving"))
        self.esr_btn.clicked.connect(self._open_esr_test)

        icon_path = "assets/icons/esr.png"
        if QPixmap(icon_path).isNull():
            self.esr_btn.setText(self._t("tool.esr"))
        else:
            self.esr_btn.setIcon(QIcon(icon_path))
            self.esr_btn.setIconSize(QSize(64, 64))
            self.esr_btn.setText(self._t("tool.esr"))

        tools_grid.addWidget(
            self.esr_btn, 0, 0, Qt.AlignmentFlag.AlignCenter
        )

        self.future_tool_placeholder = QPushButton("...")
        self.future_tool_placeholder.setFixedSize(140, 140)
        self.future_tool_placeholder.setStyleSheet("""
            QPushButton {
                background-color: #2C2C2C;
                border: 2px dashed #555;
                border-radius: 8px;
                color: #777;
                font-size: 24px;
            }
        """)
        self.future_tool_placeholder.setEnabled(False)
        self.future_tool_placeholder.setToolTip(self._t("tool.toekomstig"))
        tools_grid.addWidget(
            self.future_tool_placeholder, 0, 1, Qt.AlignmentFlag.AlignCenter
        )

        tools_grid.setColumnStretch(2, 1)
        layout.addLayout(tools_grid)
        layout.addStretch()
        return page

    def _show_hub(self):
        self.stack.setCurrentWidget(self.hub_page)
        self.setWindowTitle(self._t("app.titel"))

    def _show_diagnose(self):
        self.stack.setCurrentWidget(self.diagnose_page)
        self.setWindowTitle(
            self._t("app.titel") + " — " + self._t("scherm.diagnose")
        )

    def _show_history(self):
        self.history_page.refresh()
        self.stack.setCurrentWidget(self.history_page)
        self.setWindowTitle(
            self._t("app.titel") + " — " + self._t("scherm.historiek")
        )

    def _show_documentation(self):
        self.documentation_page.refresh()
        self.stack.setCurrentWidget(self.documentation_page)
        self.setWindowTitle(
            self._t("app.titel") + " — " + self._t("documentatie.titel")
        )

    def _build_menu(self):
        menubar = self.menuBar()

        # Bestand
        file_menu = menubar.addMenu(self._t("menu.bestand"))
        exit_action = QAction(self._t("menu.afsluiten"), self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Diagnose
        diagnose_menu = menubar.addMenu(self._t("menu.diagnose"))
        diagnose_action = QAction(self._t("menu.open_diagnose"), self)
        diagnose_action.triggered.connect(self._show_diagnose)
        diagnose_menu.addAction(diagnose_action)

        esr_action = QAction(self._t("menu.esr_test"), self)
        esr_action.setShortcut(QKeySequence("Ctrl+E"))
        esr_action.triggered.connect(self._open_esr_test)
        diagnose_menu.addAction(esr_action)

        # Instellingen
        settings_menu = menubar.addMenu(self._t("menu.instellingen"))

        settings_action = QAction(self._t("menu.instellingen") + "...", self)
        settings_action.triggered.connect(self._show_settings)
        settings_menu.addAction(settings_action)

        settings_menu.addSeparator()

        # Talen submenu — dynamisch uit i18n/locales/<taalcode>/language.json
        lang_menu = settings_menu.addMenu(self._t("menu.talen"))
        self.language_actions = {}
        for info in beschikbare_taalinfos():
            action = QAction(info.native_name, self, checkable=True)
            action.setData(info.code)
            action.triggered.connect(
                lambda checked=False, code=info.code: self._set_language(code)
            )
            lang_menu.addAction(action)
            self.language_actions[info.code] = action
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
        for code, action in getattr(self, "language_actions", {}).items():
            action.setChecked(self.taal == code)

    def _set_language(self, taal_code):
        self.taal = taal_code
        self.instellingen = replace(self.instellingen, taal=taal_code)
        sla_instellingen_op(self.instellingen)
        self._update_lang_checks()
        self._apply_language()

    def _apply_language(self):
        self.menuBar().clear()
        self._build_menu()

        if hasattr(self, "hub_title_label"):
            self.hub_title_label.setText(self._t("app.titel"))
        if hasattr(self, "hub_subtitle_label"):
            self.hub_subtitle_label.setText(self._t("scherm.hoofdmenu"))
        if hasattr(self, "diagnose_back_btn"):
            self.diagnose_back_btn.setText(self._t("knop.terug"))
        if hasattr(self, "diagnose_title_label"):
            self.diagnose_title_label.setText(self._t("scherm.diagnose"))

        if hasattr(self, "diagnose_btn"):
            self.diagnose_btn.setText(self._t("tool.diagnose"))
            self.diagnose_btn.setToolTip(self._t("tool.diagnose_omschrijving"))
        if hasattr(self, "history_btn"):
            self.history_btn.setText(self._t("tool.historiek"))
            self.history_btn.setToolTip(self._t("tool.historiek_omschrijving"))
        if hasattr(self, "documentation_btn"):
            self.documentation_btn.setText(self._t("tool.documentatie"))
            self.documentation_btn.setToolTip(
                self._t("tool.documentatie_omschrijving")
            )
        if hasattr(self, "future_tool_placeholder"):
            self.future_tool_placeholder.setToolTip(self._t("tool.toekomstig"))

        if hasattr(self, "history_page"):
            self.history_page.apply_language(self.taal)
            if self.stack.currentWidget() is self.history_page:
                self.history_page.refresh()
        if hasattr(self, "documentation_page"):
            self.documentation_page.apply_language(self.taal)
        if hasattr(self, "esr_page"):
            self.esr_page.apply_language(self.taal)
        if hasattr(self, "esr_btn"):
            self.esr_btn.setText(self._t("tool.esr"))
            self.esr_btn.setToolTip(self._t("tool.esr_omschrijving"))

        self._update_window_title_for_current_page()

    def _update_window_title_for_current_page(self):
        """Werk de venstertitel bij zonder de huidige pagina te wijzigen."""
        if not hasattr(self, "stack"):
            self.setWindowTitle(self._t("app.titel"))
            return

        current = self.stack.currentWidget()
        if current is getattr(self, "diagnose_page", None):
            suffix = self._t("scherm.diagnose")
        elif current is getattr(self, "esr_page", None):
            suffix = self._t("scherm.esr_test")
        elif current is getattr(self, "history_page", None):
            suffix = self._t("scherm.historiek")
        elif current is getattr(self, "documentation_page", None):
            suffix = self._t("documentatie.titel")
        else:
            suffix = None

        self.setWindowTitle(
            self._t("app.titel") if suffix is None
            else self._t("app.titel") + " — " + suffix
        )

    def _repeat_measurement(self, preset):
        """Open ESR als nieuwe meetrun met veilige historische contextpreset."""
        self.esr_page.apply_repeat_preset(preset)
        self._open_esr_test()

    def _open_esr_test(self):
        self.stack.setCurrentWidget(self.esr_page)
        self.setWindowTitle(
            self._t("app.titel") + " — " + self._t("scherm.esr_test")
        )

    def closeEvent(self, event):
        """Sluit contextueel.

        Vanuit ESR werkt de venster-X als 'Terug' naar Diagnose. Vanuit
        Diagnose, Historiek of Documentatie gaat de X terug naar het Hoofdmenu.
        Alleen op
        het Hoofdmenu sluit de venster-X de applicatie volledig.
        """
        if hasattr(self, "stack"):
            current = self.stack.currentWidget()
            if current is self.esr_page:
                self._show_diagnose()
                event.ignore()
                return
            if current is self.diagnose_page:
                self._show_hub()
                event.ignore()
                return
            if current is self.history_page:
                self._show_hub()
                event.ignore()
                return
            if current is self.documentation_page:
                self._show_hub()
                event.ignore()
                return

        event.accept()

    def _show_settings(self):
        dialog = SettingsDialog(self.instellingen, taal=self.taal, parent=self)
        dialog.settings_applied.connect(self._apply_settings)
        dialog.exec()

    def _apply_settings(self, instellingen):
        vorige_taal = self.taal
        self.instellingen = instellingen
        self.taal = instellingen.taal
        sla_instellingen_op(self.instellingen)

        if self.taal != vorige_taal:
            self._update_lang_checks()
            self._apply_language()

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
            browser.setHtml(
                f'<body style="font-family: Segoe UI; color: #F0F0F0; '
                f'background-color: #2D2D30;">{html}</body>'
            )
        except FileNotFoundError:
            browser.setHtml(
                f'<body style="font-family: Segoe UI; color: #F0F0F0; '
                f'background-color: #2D2D30;"><p>Bestand niet gevonden: '
                f'{filepath}</p></body>'
            )

        layout.addWidget(browser)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()

    def _show_about(self):
        QMessageBox.about(self, self._t("dialog.over_titel"), self._t("dialog.over_tekst"))