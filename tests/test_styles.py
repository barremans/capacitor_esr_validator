"""
================================================================================
Module:     tests/test_styles.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.3.0
Datum:      2026-10-21
Auteur:     Bart Bossuyt

Doel:       Pure regressietests op de donkere en lichte stylesheet-strings
            (DARK_THEME_STYLESHEET, LIGHT_THEME_STYLESHEET) en op de
            THEME_STYLESHEETS-dict. Geen QApplication, geen Qt-instantie:
            de tests inspecteren alleen de strings en de dict die
            apply_theme() op de app zet.

Wijzigingen:
  v1.0.0 (2026-10-20)  Eerste versie: focus-states, tabel-indicator,
                        groupbox-indicator, combobox-hover.
  v1.1.0 (2026-10-20)  Fase 11G.2: scrollbar-tests voor verticale en
                        horizontale QScrollBar, plus controle dat de
                        pijl-knoppen (add-line/sub-line) zijn uitgeschakeld.
  v1.2.0 (2026-10-20)  Fase 11G.7: drie tests voor de duidelijker
                        QGroupBox::indicator (lichtere achtergrond in
                        unchecked-state, 2px rand, blauwe checked-state,
                        focus-state). Lost het visuele probleem op
                        waarbij de checkbox links van "Filters" nauwelijks
                        zichtbaar was.
  v1.3.0 (2026-10-21)  Fase 11H.1: light theme.
                        - Nieuwe tests voor LIGHT_THEME_STYLESHEET.
                        - Tests voor THEME_STYLESHEETS-dict.
                        - Test voor de fallback van apply_theme() op een
                          onbekende thema-waarde (pure dict-lookup, geen
                          QApplication).
                        - Bestaande 12 tests blijven ongewijzigd.
================================================================================
"""

from __future__ import annotations

from app.gui.styles import (
    DARK_THEME_STYLESHEET,
    LIGHT_THEME_STYLESHEET,
    THEME_STYLESHEETS,
)


def test_stylesheet_is_niet_leeg() -> None:
    assert isinstance(DARK_THEME_STYLESHEET, str)
    assert DARK_THEME_STYLESHEET.strip() != ""


def test_checkbox_heeft_focus_state() -> None:
    """Tab-navigatie naar een checkbox moet zichtbaar zijn (11G.1)."""
    assert "QCheckBox::indicator:focus" in DARK_THEME_STYLESHEET


def test_radiobutton_heeft_focus_state() -> None:
    """Tab-navigatie naar een radiobutton moet zichtbaar zijn (11G.1)."""
    assert "QRadioButton::indicator:focus" in DARK_THEME_STYLESHEET


def test_tableview_heeft_indicator() -> None:
    """Selectie-checkboxen in analyse- en documentatietabellen (11G.1)."""
    assert "QTableView::indicator" in DARK_THEME_STYLESHEET
    assert "QTableView::indicator:checked" in DARK_THEME_STYLESHEET
    assert "QTableView::indicator:focus" in DARK_THEME_STYLESHEET


def test_groupbox_heeft_indicator() -> None:
    """Checkable QGroupBox (bv. filter_group in AnalysisScreen) (11G.1)."""
    assert "QGroupBox::indicator" in DARK_THEME_STYLESHEET
    assert "QGroupBox::indicator:checked" in DARK_THEME_STYLESHEET


def test_combobox_dropdown_heeft_hover() -> None:
    """Subtiele hover-feedback op de dropdown-pijl (11G.1)."""
    assert "QComboBox::drop-down:hover" in DARK_THEME_STYLESHEET


def test_scrollbar_vertical_bestaat() -> None:
    """Donkere verticale scrollbar voor QTextBrowser/QScrollArea (11G.2)."""
    assert "QScrollBar:vertical" in DARK_THEME_STYLESHEET
    assert "QScrollBar::handle:vertical" in DARK_THEME_STYLESHEET
    assert "QScrollBar::handle:vertical:hover" in DARK_THEME_STYLESHEET
    assert "QScrollBar::handle:vertical:pressed" in DARK_THEME_STYLESHEET


def test_scrollbar_horizontal_bestaat() -> None:
    """Donkere horizontale scrollbar voor QTextBrowser/QScrollArea (11G.2)."""
    assert "QScrollBar:horizontal" in DARK_THEME_STYLESHEET
    assert "QScrollBar::handle:horizontal" in DARK_THEME_STYLESHEET
    assert "QScrollBar::handle:horizontal:hover" in DARK_THEME_STYLESHEET
    assert "QScrollBar::handle:horizontal:pressed" in DARK_THEME_STYLESHEET


def test_scrollbar_geen_pijl_knoppen() -> None:
    """De pijl-knoppen (add-line/sub-line) zijn uitgeschakeld (11G.2)."""
    assert "QScrollBar::add-line:vertical" in DARK_THEME_STYLESHEET
    assert "QScrollBar::sub-line:vertical" in DARK_THEME_STYLESHEET
    assert "QScrollBar::add-line:horizontal" in DARK_THEME_STYLESHEET
    assert "QScrollBar::sub-line:horizontal" in DARK_THEME_STYLESHEET


# ============================================================================
# v1.2.0 — QGroupBox::indicator duidelijker (fase 11G.7)
# ============================================================================

def test_groupbox_indicator_heeft_duidelijk_contrast() -> None:
    """Unchecked-state heeft een lichtere achtergrond en dikkere rand (11G.7).

    Het indicator-vierkantje links van "Filters" viel weg tegen de
    groupbox-rand. Nu is de achtergrond #3C3C3C (lichter dan de
    groupbox-achtergrond #2D2D30) en de rand 2px #B0B0B0.
    """
    assert "QGroupBox::indicator:unchecked" in DARK_THEME_STYLESHEET
    # De unchecked-regel moet zowel de lichtere achtergrond als de
    # dikkere rand bevatten.
    unchecked_index = DARK_THEME_STYLESHEET.index(
        "QGroupBox::indicator:unchecked"
    )
    unchecked_blok = DARK_THEME_STYLESHEET[unchecked_index:unchecked_index + 200]
    assert "#3C3C3C" in unchecked_blok
    assert "2px" in unchecked_blok
    assert "#B0B0B0" in unchecked_blok


def test_groupbox_indicator_checked_is_blauw() -> None:
    """Checked-state is blauw met duidelijke rand (11G.7)."""
    assert "QGroupBox::indicator:checked" in DARK_THEME_STYLESHEET
    checked_index = DARK_THEME_STYLESHEET.index(
        "QGroupBox::indicator:checked"
    )
    checked_blok = DARK_THEME_STYLESHEET[checked_index:checked_index + 200]
    assert "#0078D7" in checked_blok
    assert "2px" in checked_blok


def test_groupbox_indicator_focus_bestaat() -> None:
    """Focus-state voor QGroupBox::indicator (11G.7)."""
    assert "QGroupBox::indicator:focus" in DARK_THEME_STYLESHEET


# ============================================================================
# v1.3.0 — light theme (fase 11H.1)
# ============================================================================

def test_light_stylesheet_is_niet_leeg() -> None:
    assert isinstance(LIGHT_THEME_STYLESHEET, str)
    assert LIGHT_THEME_STYLESHEET.strip() != ""


def test_light_mainwindow_heeft_lichte_achtergrond() -> None:
    """Het hoofdvenster in licht thema is licht, niet donker (11H.1)."""
    assert "QMainWindow, QWidget, QDialog" in LIGHT_THEME_STYLESHEET
    index = LIGHT_THEME_STYLESHEET.index("QMainWindow, QWidget, QDialog")
    blok = LIGHT_THEME_STYLESHEET[index:index + 200]
    assert "#F4F4F4" in blok
    assert "#202020" in blok


def test_light_lineedit_heeft_witte_achtergrond() -> None:
    """Invoervelden in licht thema zijn wit met donkere tekst (11H.1)."""
    assert "QLineEdit, QComboBox, QTextBrowser" in LIGHT_THEME_STYLESHEET
    index = LIGHT_THEME_STYLESHEET.index(
        "QLineEdit, QComboBox, QTextBrowser"
    )
    blok = LIGHT_THEME_STYLESHEET[index:index + 250]
    assert "#FFFFFF" in blok
    assert "#202020" in blok


def test_light_groupbox_indicator_heeft_duidelijk_contrast() -> None:
    """Ook in licht thema valt de groupbox-checkbox niet weg (11H.1).

    Consistent met de 11G.7-fix in donker thema: witte achtergrond met
    een 2px donkere rand.
    """
    assert "QGroupBox::indicator:unchecked" in LIGHT_THEME_STYLESHEET
    index = LIGHT_THEME_STYLESHEET.index("QGroupBox::indicator:unchecked")
    blok = LIGHT_THEME_STYLESHEET[index:index + 200]
    assert "#FFFFFF" in blok
    assert "2px" in blok
    assert "#5A5A5A" in blok


def test_light_scrollbar_vertical_bestaat() -> None:
    """Lichte verticale scrollbar voor QTextBrowser/QScrollArea (11H.1)."""
    assert "QScrollBar:vertical" in LIGHT_THEME_STYLESHEET
    assert "QScrollBar::handle:vertical" in LIGHT_THEME_STYLESHEET


def test_light_scrollbar_horizontal_bestaat() -> None:
    """Lichte horizontale scrollbar voor QTextBrowser/QScrollArea (11H.1)."""
    assert "QScrollBar:horizontal" in LIGHT_THEME_STYLESHEET
    assert "QScrollBar::handle:horizontal" in LIGHT_THEME_STYLESHEET


def test_theme_stylesheets_heeft_dark_en_light() -> None:
    """THEME_STYLESHEETS is de centrale lookup voor apply_theme (11H.1)."""
    assert set(THEME_STYLESHEETS.keys()) == {"dark", "light"}
    assert THEME_STYLESHEETS["dark"] is DARK_THEME_STYLESHEET
    assert THEME_STYLESHEETS["light"] is LIGHT_THEME_STYLESHEET


def test_apply_theme_onbekende_waarde_valt_terug_op_dark() -> None:
    """Backward-compat: onbekende thema-waarde gebruikt het donkere thema.

    Pure dict-lookup, geen QApplication nodig: we controleren dat de
    lookup-tabel precies twee keys heeft en dat een onbekende waarde
    niet als derde key bestaat (de fallback gebeurt in apply_theme()
    via ``if thema == "light": ... else: thema = "dark"``).
    """
    assert "light" in THEME_STYLESHEETS
    assert "dark" in THEME_STYLESHEETS
    assert "onbekend" not in THEME_STYLESHEETS
    assert "DARK" not in THEME_STYLESHEETS