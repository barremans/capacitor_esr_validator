"""
================================================================================
Module:     app/gui/main_window.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     2.17.0
Datum:      2026-10-16
Auteur:     Bart Bossuyt

Doel:       Hoofdvenster van de Tool Hub met één-venster-navigatie.
            ESR-test draait als interne pagina binnen hetzelfde hoofdvenster.

Wijzigingen:
  v2.2.1 (2026-09-27)  Settings-dialoog gekoppeld; Apply/OK bewaren alle
                       settings en taalwissel behoudt overige voorkeuren.
  v1.0.0 (2026-08-11)  Initiele versie — QMainWindow met centrale widget.
  v2.0.0 (2026-08-13)  Herontworpen naar ToolHubWindow.
  v2.1.0 (2026-09-26)  Eén-venster-navigatie met QStackedWidget.
  v2.1.1 (2026-09-26)  Sluitknop (X) gedraagt zich contextueel.
  v2.1.2 (2026-09-27)  Leesbaarheid van Tool Hub en markdown-dialogen verbeterd.
  v2.1.3 (2026-09-27)  Dubbele algemene dark-theme styling verwijderd.
  v2.2.0 (2026-09-27)  Navigatie uitgebreid naar Hoofdmenu -> Diagnose -> ESR.
  v2.3.0 (2026-10-01)  Read-only Historiek als interne pagina toegevoegd.
  v2.4.0 (2026-10-01)  Historiek "Herhaal meting" gekoppeld aan ESR-pagina.
  v2.4.1 (2026-10-01)  Live taalwissel vervolledigd.
  v2.6.0 (2026-10-03)  Dynamische taalontdekking voor het Talenmenu.
  v2.7.0 (2026-10-03)  ESR-contextdocumentatie gekoppeld aan centrale viewer.
  v2.7.1 (2026-10-05)  Globale F1 (Help-menu) expliciet op WindowShortcut.
  v2.7.2 (2026-10-05)  Help-menu uitgebreid met "Documentatie zoeken…".
  v2.7.3 (2026-10-05)  Fix: _apply_language() lekte menu's.
  v2.8.0 (2026-10-05)  Sneltoetsen op het Hoofdmenu (Fase 4F).
  v2.8.1 (2026-10-05)  Fase 4F.1: Esc op Diagnose-pagina.
  v2.8.2 (2026-10-05)  Fase 4F.2: Esc op Hoofdmenu vraagt bevestiging.
  v2.8.3 (2026-10-06)  Fase 4H: Help splitsen per taal.
  v2.9.0 (2026-10-06)  Fase 5E: "Document importeren…" (Ctrl+I).
  v2.10.0 (2026-10-09) Fase 7B: Analyse-pagina.
  v2.10.1 (2026-10-10) Fase 8B.2a: analysis_page.apply_language() doet geen
                        refresh meer.
  v2.11.0 (2026-10-10) Fase 8C: menu-item "Rapport maken…" (Ctrl+P).
  v2.11.1 (2026-10-10) Poging QActions op te ruimen vóór menu's.
  v2.11.2 (2026-10-10) QActions krijgen het menu als parent.
  v2.11.3 (2026-10-10) Fix: __init__ respecteert parameter taal.
  v2.11.4 (2026-10-11) Fase 8D: auteur mee aan ReportDialog.
  v2.11.5 (2026-10-11) Fase 8D: grafiek_default mee aan ReportDialog.
  v2.11.6 (2026-10-13) Fase 9A.1: Over-dialoog toont versie; bugfix
                        help/changelog titel-keys.
  v2.12.0 (2026-10-14) Fase 9G: bug/feature-rapportage naar GitHub.
  v2.13.0 (2026-10-14) Fase 9H: update-check.
  v2.14.0 (2026-10-15) Fase 9H-afronding.
  v2.15.0 (2026-10-16) Fase 11A.1: menu-item "Rapport maken…" wordt
                        disabled zonder selectie op Historiek.
  v2.16.0 (2026-10-16) Fase 11A.2: menu-item wordt ook enabled op Analyse
                        met een checkbox-selectie. _open_report_dialog()
                        bepaalt de scope op basis van de actieve pagina:
                          - Historiek + checkbox-selectie -> scope 'selectie'
                          - Historiek + rij-selectie -> scope 'enkel'
                          - Analyse + checkbox-selectie -> scope 'selectie'
                        De bestaande informatieve melding blijft voor de
                        gevallen waarin geen selectie is.
  v2.17.0 (2026-10-16) Fase 11C (iconen):
                        - Hub-knoppen (Diagnose, Historiek, Documentatie,
                          Analyse) krijgen een icoon.
                        - Diagnose-ESR-knop gebruikt esr.png (kleine
                          letter) in plaats van ESR.png.
                        - Menu-items krijgen een icoon via de centrale
                          helper app/helpers/icon_paths.
                        - Elke dialoog krijgt een venstericoon via
                          _zet_dialoog_icoon().
                        - Geen wijziging aan bestaande navigatie, taalwissel
                          of selectielogica.
================================================================================
"""

from dataclasses import replace
import webbrowser

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QMenuBar, QMenu,
    QMessageBox, QTextBrowser, QDialog, QDialogButtonBox,
    QScrollArea, QFrame, QStackedWidget,
)
from PySide6.QtGui import QAction, QKeySequence, QShortcut, QIcon, QPixmap
from PySide6.QtCore import Qt, QSize, QTimer

from app.helpers.i18n import beschikbare_taalinfos, vertaal
from app.helpers.help_paths import help_pad_voor_taal, changelog_pad_voor_taal
from app.helpers.icon_paths import laad_icoon, zet_venster_icoon
from app.config.settings import laad_instellingen, sla_instellingen_op, AppInstellingen
from app.gui.dialogs.settings_dialog import SettingsDialog
from app.gui.dialogs.search_help_dialog import SearchHelpDialog
from app.version import __version__


class ToolHubWindow(QMainWindow):
    """Startscherm — hub met knoppen voor alle beschikbare tools."""

    def __init__(self, taal: str | None = None, check_on_startup: bool = True):
        super().__init__()
        self.instellingen = laad_instellingen()
        self.taal = taal if taal else self.instellingen.taal
        self.rapport_action: QAction | None = None
        self._build_ui()
        self._apply_language()

        if check_on_startup:
            QTimer.singleShot(0, self._run_startup_update_check)

    def _t(self, sleutel, **kwargs):
        return vertaal(sleutel, taal=self.taal, **kwargs)

    # ------------------------------------------------------------------
    # Iconen (11C)
    # ------------------------------------------------------------------
    @staticmethod
    def _zet_icoon_op_knop(knop: QPushButton, naam: str, grootte: int = 32) -> None:
        """Zet een icoon op een knop als het bestaat; anders niets."""
        icoon = laad_icoon(naam)
        if icoon is not None:
            knop.setIcon(icoon)
            knop.setIconSize(QSize(grootte, grootte))

    @staticmethod
    def _zet_icoon_op_action(action: QAction, naam: str) -> None:
        """Zet een icoon op een QAction als het bestaat; anders niets."""
        icoon = laad_icoon(naam)
        if icoon is not None:
            action.setIcon(icoon)

    @staticmethod
    def _zet_dialoog_icoon(dialoog: QDialog) -> None:
        """Zet het applicatie-icoon op een dialoog."""
        zet_venster_icoon(dialoog)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
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
        self.esr_page.documentation_requested.connect(
            self._open_context_documentation
        )
        self.stack.addWidget(self.esr_page)

        from app.gui.history_screen import HistoryScreen
        self.history_page = HistoryScreen(taal=self.taal)
        self.history_page.back_requested.connect(self._show_hub)
        self.history_page.repeat_requested.connect(self._repeat_measurement)
        self.history_page.selection_changed.connect(
            self._update_report_action_state
        )
        self.stack.addWidget(self.history_page)

        from app.gui.documentation_screen import DocumentationScreen
        self.documentation_page = DocumentationScreen(taal=self.taal)
        self.documentation_page.back_requested.connect(self._show_hub)
        self.documentation_page.import_requested.connect(self._show_import_wizard)
        self.stack.addWidget(self.documentation_page)

        from app.gui.analysis_screen import AnalysisScreen
        self.analysis_page = AnalysisScreen(taal=self.taal)
        self.analysis_page.back_requested.connect(self._show_hub)
        self.analysis_page.selection_changed.connect(
            self._update_report_action_state
        )
        self.stack.addWidget(self.analysis_page)

        self.stack.setCurrentWidget(self.hub_page)

    def _build_hub_page(self):
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
        self._zet_icoon_op_knop(self.diagnose_btn, "diagnose", 48)
        self.diagnose_btn.clicked.connect(self._show_diagnose)
        menu_grid.addWidget(
            self.diagnose_btn, 0, 0, Qt.AlignmentFlag.AlignCenter
        )

        self.history_btn = QPushButton(self._t("tool.historiek"))
        self.history_btn.setFixedSize(180, 120)
        self.history_btn.setToolTip(self._t("tool.historiek_omschrijving"))
        self._zet_icoon_op_knop(self.history_btn, "history", 48)
        self.history_btn.clicked.connect(self._show_history)
        menu_grid.addWidget(
            self.history_btn, 0, 1, Qt.AlignmentFlag.AlignCenter
        )

        self.documentation_btn = QPushButton(self._t("tool.documentatie"))
        self.documentation_btn.setFixedSize(180, 120)
        self.documentation_btn.setToolTip(
            self._t("tool.documentatie_omschrijving")
        )
        self._zet_icoon_op_knop(self.documentation_btn, "documentation", 48)
        self.documentation_btn.clicked.connect(self._show_documentation)
        menu_grid.addWidget(
            self.documentation_btn, 0, 2, Qt.AlignmentFlag.AlignCenter
        )

        self.analysis_btn = QPushButton(self._t("tool.analyse"))
        self.analysis_btn.setFixedSize(180, 120)
        self.analysis_btn.setToolTip(self._t("tool.analyse_omschrijving"))
        self._zet_icoon_op_knop(self.analysis_btn, "analysis", 48)
        self.analysis_btn.clicked.connect(self._show_analysis)
        menu_grid.addWidget(
            self.analysis_btn, 0, 3, Qt.AlignmentFlag.AlignCenter
        )

        menu_grid.setColumnStretch(4, 1)
        layout.addLayout(menu_grid)
        layout.addStretch()

        self._install_hub_shortcuts(central)
        return central

    def _install_hub_shortcuts(self, hub_widget: QWidget) -> None:
        ctx = Qt.ShortcutContext.WidgetWithChildrenShortcut

        self.sc_hub_diagnose = QShortcut(QKeySequence("Ctrl+D"), hub_widget)
        self.sc_hub_diagnose.setContext(ctx)
        self.sc_hub_diagnose.activated.connect(self._show_diagnose)

        self.sc_hub_history = QShortcut(QKeySequence("Ctrl+H"), hub_widget)
        self.sc_hub_history.setContext(ctx)
        self.sc_hub_history.activated.connect(self._show_history)

        self.sc_hub_documentation = QShortcut(QKeySequence("Ctrl+K"), hub_widget)
        self.sc_hub_documentation.setContext(ctx)
        self.sc_hub_documentation.activated.connect(self._show_documentation)

        self.sc_hub_analysis = QShortcut(QKeySequence("Ctrl+A"), hub_widget)
        self.sc_hub_analysis.setContext(ctx)
        self.sc_hub_analysis.activated.connect(self._show_analysis)

        self.sc_hub_close = QShortcut(QKeySequence("Esc"), hub_widget)
        self.sc_hub_close.setContext(ctx)
        self.sc_hub_close.activated.connect(self._confirm_close_from_hub)

    def _confirm_close_from_hub(self) -> None:
        antwoord = QMessageBox.question(
            self,
            self._t("dialog.afsluiten_titel"),
            self._t("dialog.afsluiten_tekst"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if antwoord == QMessageBox.StandardButton.Yes:
            self.close()

    def _build_diagnose_page(self):
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

        # 11C: gebruik esr.png (kleine letter) via de centrale helper.
        esr_icoon = laad_icoon("esr")
        if esr_icoon is None:
            self.esr_btn.setText(self._t("tool.esr"))
        else:
            self.esr_btn.setIcon(esr_icoon)
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

        self._install_diagnose_shortcuts(page)
        return page

    def _install_diagnose_shortcuts(self, diagnose_widget: QWidget) -> None:
        ctx = Qt.ShortcutContext.WidgetWithChildrenShortcut

        self.sc_diagnose_back = QShortcut(QKeySequence("Esc"), diagnose_widget)
        self.sc_diagnose_back.setContext(ctx)
        self.sc_diagnose_back.activated.connect(self._show_hub)

    def _show_hub(self):
        self.stack.setCurrentWidget(self.hub_page)
        self.setWindowTitle(self._t("app.titel"))
        self._update_report_action_state()

    def _show_diagnose(self):
        self.stack.setCurrentWidget(self.diagnose_page)
        self.setWindowTitle(
            self._t("app.titel") + " — " + self._t("scherm.diagnose")
        )
        self._update_report_action_state()

    def _show_history(self):
        self.history_page.refresh()
        self.stack.setCurrentWidget(self.history_page)
        self.setWindowTitle(
            self._t("app.titel") + " — " + self._t("scherm.historiek")
        )
        self._update_report_action_state()

    def _show_documentation(self):
        self.documentation_page.refresh()
        self.stack.setCurrentWidget(self.documentation_page)
        self.setWindowTitle(
            self._t("app.titel") + " — " + self._t("documentatie.titel")
        )
        self._update_report_action_state()

    def _show_analysis(self):
        self.analysis_page.refresh()
        self.stack.setCurrentWidget(self.analysis_page)
        self.setWindowTitle(
            self._t("app.titel") + " — " + self._t("analyse.titel")
        )
        self._update_report_action_state()

    def _build_menu(self):
        """Bouwt alle menu's op."""
        menubar = self.menuBar()

        file_menu = menubar.addMenu(self._t("menu.bestand"))

        import_action = QAction(self._t("menu.document_importeren"), file_menu)
        import_action.setShortcut(QKeySequence("Ctrl+I"))
        import_action.triggered.connect(self._show_import_wizard)
        self._zet_icoon_op_action(import_action, "documentation")
        file_menu.addAction(import_action)

        self.rapport_action = QAction(self._t("menu.rapport"), file_menu)
        self.rapport_action.setShortcut(QKeySequence("Ctrl+P"))
        self.rapport_action.triggered.connect(self._open_report_dialog)
        self.rapport_action.setToolTip(self._t("menu.rapport_tooltip"))
        self.rapport_action.setEnabled(False)
        self._zet_icoon_op_action(self.rapport_action, "report")
        file_menu.addAction(self.rapport_action)

        file_menu.addSeparator()

        exit_action = QAction(self._t("menu.afsluiten"), file_menu)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        self._zet_icoon_op_action(exit_action, "exit")
        file_menu.addAction(exit_action)

        diagnose_menu = menubar.addMenu(self._t("menu.diagnose"))

        diagnose_action = QAction(self._t("menu.open_diagnose"), diagnose_menu)
        diagnose_action.triggered.connect(self._show_diagnose)
        self._zet_icoon_op_action(diagnose_action, "diagnose")
        diagnose_menu.addAction(diagnose_action)

        esr_action = QAction(self._t("menu.esr_test"), diagnose_menu)
        esr_action.setShortcut(QKeySequence("Ctrl+E"))
        esr_action.triggered.connect(self._open_esr_test)
        self._zet_icoon_op_action(esr_action, "esr")
        diagnose_menu.addAction(esr_action)

        analysis_action = QAction(self._t("menu.analyse"), diagnose_menu)
        analysis_action.setShortcut(QKeySequence("Ctrl+A"))
        analysis_action.triggered.connect(self._show_analysis)
        self._zet_icoon_op_action(analysis_action, "analysis")
        diagnose_menu.addAction(analysis_action)

        report_menu = menubar.addMenu(self._t("menu.rapporteren"))

        bug_report_action = QAction(self._t("menu.bug_melden"), report_menu)
        bug_report_action.triggered.connect(self._show_bug_report_dialog)
        self._zet_icoon_op_action(bug_report_action, "bug")
        report_menu.addAction(bug_report_action)

        open_cases_action = QAction(self._t("menu.open_cases"), report_menu)
        open_cases_action.triggered.connect(self._show_open_cases)
        report_menu.addAction(open_cases_action)

        settings_menu = menubar.addMenu(self._t("menu.instellingen"))

        settings_action = QAction(
            self._t("menu.instellingen") + "...", settings_menu
        )
        settings_action.triggered.connect(self._show_settings)
        self._zet_icoon_op_action(settings_action, "settings")
        settings_menu.addAction(settings_action)

        settings_menu.addSeparator()

        lang_menu = settings_menu.addMenu(self._t("menu.talen"))
        self.language_actions = {}
        for info in beschikbare_taalinfos():
            action = QAction(info.native_name, lang_menu, checkable=True)
            action.setData(info.code)
            action.triggered.connect(
                lambda checked=False, code=info.code: self._set_language(code)
            )
            lang_menu.addAction(action)
            self.language_actions[info.code] = action
        self._update_lang_checks()

        help_menu = menubar.addMenu(self._t("menu.help"))

        help_action = QAction(self._t("menu.help"), help_menu)
        help_action.setShortcut(QKeySequence("F1"))
        help_action.setShortcutContext(Qt.ShortcutContext.WindowShortcut)
        help_action.triggered.connect(self._show_help)
        self._zet_icoon_op_action(help_action, "help")
        help_menu.addAction(help_action)

        search_help_action = QAction(
            self._t("menu.documentatie_zoeken"), help_menu
        )
        search_help_action.triggered.connect(self._show_search_help)
        self._zet_icoon_op_action(search_help_action, "documentation")
        help_menu.addAction(search_help_action)

        changelog_action = QAction(self._t("menu.changelog"), help_menu)
        changelog_action.triggered.connect(self._show_changelog)
        help_menu.addAction(changelog_action)

        help_menu.addSeparator()

        update_action = QAction(
            self._t("menu.controleren_op_updates"), help_menu
        )
        update_action.triggered.connect(self._check_for_updates_manually)
        self._zet_icoon_op_action(update_action, "update")
        help_menu.addAction(update_action)

        help_menu.addSeparator()

        about_action = QAction(self._t("menu.over"), help_menu)
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
        menubar = self.menuBar()
        menubar.clear()
        for oude_menu in menubar.findChildren(QMenu):
            oude_menu.setParent(None)
            oude_menu.deleteLater()

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
        if hasattr(self, "analysis_btn"):
            self.analysis_btn.setText(self._t("tool.analyse"))
            self.analysis_btn.setToolTip(self._t("tool.analyse_omschrijving"))
        if hasattr(self, "future_tool_placeholder"):
            self.future_tool_placeholder.setToolTip(self._t("tool.toekomstig"))

        if hasattr(self, "history_page"):
            self.history_page.apply_language(self.taal)
            if self.stack.currentWidget() is self.history_page:
                self.history_page.refresh()
        if hasattr(self, "documentation_page"):
            self.documentation_page.apply_language(self.taal)
        if hasattr(self, "analysis_page"):
            self.analysis_page.apply_language(self.taal)
        if hasattr(self, "esr_page"):
            self.esr_page.apply_language(self.taal)
        if hasattr(self, "esr_btn"):
            self.esr_btn.setText(self._t("tool.esr"))
            self.esr_btn.setToolTip(self._t("tool.esr_omschrijving"))

        self._update_window_title_for_current_page()
        self._update_report_action_state()

    def _update_window_title_for_current_page(self):
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
        elif current is getattr(self, "analysis_page", None):
            suffix = self._t("analyse.titel")
        else:
            suffix = None

        self.setWindowTitle(
            self._t("app.titel") if suffix is None
            else self._t("app.titel") + " — " + suffix
        )

    # ------------------------------------------------------------------
    # Rapport-menu-item state (11A.1 + 11A.2)
    # ------------------------------------------------------------------

    def _update_report_action_state(self) -> None:
        """Zet het menu-item 'Rapport maken…' enabled/disabled.

        Enabled als:
          - Historiek actief is met een rij-selectie, of
          - Analyse actief is met een checkbox-selectie.
        Alle andere pagina's: disabled.
        """
        if self.rapport_action is None:
            return
        current = self.stack.currentWidget() if hasattr(self, "stack") else None

        enabled = False
        if current is getattr(self, "history_page", None):
            try:
                enabled = self.history_page._selected_measurement_id() is not None
            except Exception:
                enabled = False
        elif current is getattr(self, "analysis_page", None):
            try:
                enabled = bool(self.analysis_page._selected_measurement_ids())
            except Exception:
                enabled = False

        self.rapport_action.setEnabled(enabled)

    def _repeat_measurement(self, preset):
        self.esr_page.apply_repeat_preset(preset)
        self._open_esr_test()

    def _open_context_documentation(self, document_id: str) -> None:
        self.documentation_page.open_document_by_id(document_id)

    def _open_esr_test(self):
        self.stack.setCurrentWidget(self.esr_page)
        self.setWindowTitle(
            self._t("app.titel") + " — " + self._t("scherm.esr_test")
        )
        self._update_report_action_state()

    def _show_import_wizard(self) -> None:
        from app.gui.dialogs.import_wizard_dialog import ImportWizardDialog

        dialog = ImportWizardDialog(taal=self.taal, parent=self)
        self._zet_dialoog_icoon(dialog)
        dialog.import_completed.connect(self._on_import_completed)
        dialog.exec()

    def _on_import_completed(self, source_id: str) -> None:
        self.documentation_page.refresh()
        self.documentation_page.select_document_by_id(source_id)

    def _open_report_dialog(self) -> None:
        """Open de rapport-dialoog met de juiste scope.

        Bepaalt de scope op basis van de actieve pagina en de actieve
        selectie:
          - Historiek met checkbox-selectie -> scope 'selectie'.
          - Historiek met rij-selectie -> scope 'enkel'.
          - Analyse met checkbox-selectie -> scope 'selectie'.
          - Anders -> informatieve melding (bestaand gedrag).
        """
        current = self.stack.currentWidget() if hasattr(self, "stack") else None

        # Historiek
        if current is getattr(self, "history_page", None):
            checkbox_ids = self.history_page._selected_measurement_ids()
            if checkbox_ids:
                self._open_multi_report_dialog(checkbox_ids)
                return
            measurement_id = self.history_page._selected_measurement_id()
            if measurement_id is None:
                QMessageBox.information(
                    self,
                    self._t("report.dialoog.titel"),
                    self._t("report.dialoog.geen_selectie"),
                )
                return
            self._open_single_report_dialog(measurement_id)
            return

        # Analyse
        if current is getattr(self, "analysis_page", None):
            ids = self.analysis_page._selected_measurement_ids()
            if not ids:
                QMessageBox.information(
                    self,
                    self._t("report.dialoog.titel"),
                    self._t("analyse.rapport.geen_selectie"),
                )
                return
            self._open_multi_report_dialog(ids)
            return

        # Andere pagina's: geen selectie mogelijk.
        QMessageBox.information(
            self,
            self._t("report.dialoog.titel"),
            self._t("report.dialoog.geen_selectie"),
        )

    def _open_single_report_dialog(self, measurement_id: int) -> None:
        from app.gui.dialogs.report_dialog import ReportDialog

        dialog = ReportDialog(
            measurement_id,
            taal=self.taal,
            werkplaats=self.instellingen.rapportage.werkplaats_bedrijf,
            auteur=self.instellingen.rapportage.auteur,
            grafiek_default=self.instellingen.rapportage.grafiek_opnemen,
            scope=self._t("report.scope.enkel"),
            parent=self,
        )
        self._zet_dialoog_icoon(dialog)
        dialog.exec()

    def _open_multi_report_dialog(self, measurement_ids: list[int]) -> None:
        from app.gui.dialogs.report_dialog import ReportDialog

        dialog = ReportDialog.for_measurements(
            list(measurement_ids),
            scope=self._t("report.scope.selectie"),
            taal=self.taal,
            werkplaats=self.instellingen.rapportage.werkplaats_bedrijf,
            auteur=self.instellingen.rapportage.auteur,
            grafiek_default=False,
            parent=self,
        )
        self._zet_dialoog_icoon(dialog)
        dialog.exec()

    def _huidige_meting_id(self) -> int | None:
        page = getattr(self, "history_page", None)
        if page is None:
            return None
        selector = getattr(page, "_selected_measurement_id", None)
        if selector is None:
            return None
        try:
            return selector()
        except Exception:
            return None

    def _show_bug_report_dialog(self) -> None:
        from bug_report_dialog import BugDialog

        dialog = BugDialog(self)
        self._zet_dialoog_icoon(dialog)
        dialog.exec()

    def _show_open_cases(self) -> None:
        from github_cases import show_github_cases

        show_github_cases(self)

    # ------------------------------------------------------------------
    # Update-check (9H)
    # ------------------------------------------------------------------
    def _run_startup_update_check(self) -> None:
        info = self._do_update_check()
        if info is not None and info.is_newer:
            self._toon_update_melding(info)

    def _check_for_updates_manually(self) -> None:
        info = self._do_update_check()
        if info is None:
            QMessageBox.warning(
                self,
                self._t("update.fout_titel"),
                self._t("update.fout_bericht"),
            )
            return

        if info.is_newer:
            self._toon_update_melding(info)
        else:
            QMessageBox.information(
                self,
                self._t("update.titel"),
                self._t(
                    "update.geen_update",
                    versie=info.current_version,
                ),
            )

    def _do_update_check(self):
        try:
            from app.helpers.updater import check_for_update
        except ImportError:
            return None
        try:
            return check_for_update(__version__)
        except Exception:
            return None

    def _toon_update_melding(self, info) -> None:
        box = QMessageBox(self)
        box.setWindowTitle(self._t("update.titel"))
        box.setIcon(QMessageBox.Icon.Information)
        box.setText(
            self._t(
                "update.nieuwer_bericht",
                huidig=info.current_version,
                nieuw=info.remote_version,
            )
        )
        download_btn = box.addButton(
            self._t("update.downloaden"),
            QMessageBox.ButtonRole.AcceptRole,
        )
        whatsnew_btn = box.addButton(
            self._t("update.wat_is_er_nieuw"),
            QMessageBox.ButtonRole.ActionRole,
        )
        box.addButton(
            self._t("update.later"),
            QMessageBox.ButtonRole.RejectRole,
        )
        box.exec()

        geklikt = box.clickedButton()
        if geklikt is download_btn and info.download_url:
            webbrowser.open(info.download_url)
        elif geklikt is whatsnew_btn:
            self._toon_release_notes()

    def _toon_release_notes(self) -> None:
        fallback_url = (
            "https://github.com/barremans/capacitor_esr_validator/"
            "releases/latest"
        )
        try:
            from app.helpers.updater import fetch_release_notes
        except ImportError:
            self._toon_release_notes_fout(fallback_url)
            return

        try:
            notes = fetch_release_notes()
        except Exception:
            self._toon_release_notes_fout(fallback_url)
            return

        body = (notes.get("body") or "").strip()
        html_url = notes.get("html_url") or fallback_url

        if not body:
            self._toon_release_notes_fout(html_url)
            return

        self._toon_release_notes_dialoog(body, html_url)

    def _toon_release_notes_fout(self, html_url: str) -> None:
        box = QMessageBox(self)
        box.setWindowTitle(self._t("update.release_notes_titel"))
        box.setIcon(QMessageBox.Icon.Information)
        box.setText(self._t("update.release_notes_fout"))
        open_btn = box.addButton(
            self._t("update.open_op_github"),
            QMessageBox.ButtonRole.AcceptRole,
        )
        box.addButton(
            self._t("update.later"),
            QMessageBox.ButtonRole.RejectRole,
        )
        box.exec()
        if box.clickedButton() is open_btn:
            webbrowser.open(html_url)

    def _toon_release_notes_dialoog(self, body: str, html_url: str) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(self._t("update.release_notes_titel"))
        dialog.resize(720, 560)
        self._zet_dialoog_icoon(dialog)
        layout = QVBoxLayout(dialog)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setReadOnly(True)
        browser.setStyleSheet(
            "QTextBrowser { background-color: #1E1E1E; color: #F0F0F0; "
            "border: 1px solid #4A4A4A; padding: 12px; }"
        )
        browser.setHtml(self._markdown_naar_html(body))
        layout.addWidget(browser, 1)

        button_row = QHBoxLayout()
        button_row.addStretch()

        github_btn = QPushButton(self._t("update.open_op_github"))
        github_btn.clicked.connect(lambda: webbrowser.open(html_url))
        button_row.addWidget(github_btn)

        sluiten_btn = QPushButton(self._t("dialog.sluiten"))
        sluiten_btn.setDefault(True)
        sluiten_btn.clicked.connect(dialog.accept)
        button_row.addWidget(sluiten_btn)

        layout.addLayout(button_row)
        dialog.exec()

    def _markdown_naar_html(self, markdown_tekst: str) -> str:
        import re

        html = markdown_tekst
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.M)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.M)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.M)
        html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', html)
        html = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', html)
        html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
        html = re.sub(r'^- (.+)$', r'&bull; \1', html, flags=re.M)
        html = html.replace('\n', '<br>')

        return (
            '<body style="font-family: Segoe UI; color: #F0F0F0; '
            'background-color: #1E1E1E; font-size: 10.5pt; line-height: 1.4;">'
            f'{html}</body>'
        )

    def closeEvent(self, event):
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
            if current is getattr(self, "analysis_page", None):
                self._show_hub()
                event.ignore()
                return

        event.accept()

    def _show_settings(self):
        dialog = SettingsDialog(self.instellingen, taal=self.taal, parent=self)
        self._zet_dialoog_icoon(dialog)
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
        pad = help_pad_voor_taal(self.taal)
        self._show_markdown_dialog(self._t("dialog.help_title"), str(pad))

    def _show_search_help(self):
        dialog = SearchHelpDialog(taal=self.taal, parent=self)
        self._zet_dialoog_icoon(dialog)
        dialog.exec()

    def _show_changelog(self):
        try:
            pad = changelog_pad_voor_taal(self.taal)
            pad_str = str(pad)
        except FileNotFoundError:
            pad_str = "docs/changelog.md"
        self._show_markdown_dialog(
            self._t("dialog.changelog_title"), pad_str
        )

    def _show_markdown_dialog(self, title, filepath):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(700, 500)
        self._zet_dialoog_icoon(dialog)
        layout = QVBoxLayout(dialog)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
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
        QMessageBox.about(
            self,
            self._t("dialog.over_title"),
            vertaal("dialog.over_tekst", taal=self.taal, versie=__version__),
        )