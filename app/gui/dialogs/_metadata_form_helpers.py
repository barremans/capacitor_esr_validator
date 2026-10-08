"""
================================================================================
Module:     app/gui/dialogs/_metadata_form_helpers.py
Project:    Electronics Diagnostic Tool Hub / ESR Tester (Windows)
Versie:     1.0.0
Datum:      2026-10-07
Auteur:     Bart Bossuyt

Doel:       Kleine, gedeelde helpers voor de metadata-formulieren in de
            import-wizard (import_wizard_dialog.py) en de metadata-editor
            (edit_metadata_dialog.py). Bewust privé-module (underscore)
            zodat duidelijk is dat dit geen publieke API is.

            Bevat:
              - CATEGORIE_VOLGORDE: vaste dropdown-volgorde van
                DocumentCategory-waarden.
              - naar_uppercase(line_edit): converteert de inhoud van een
                QLineEdit naar uppercase met behoud van cursorpositie.
              - vul_categorie_combo(combo, t): vult een QComboBox met de
                categorieën en hun i18n-labels. De callable t vertaalt
                een i18n-key naar de juiste taal.

Wijzigingen:
  v1.0.0 (2026-10-07)  Eerste versie (fase 5D'.2c). Verplaatst uit
                       import_wizard_dialog.py om duplicatie tussen
                       wizard en editor te voorkomen.
================================================================================
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import QComboBox, QLineEdit

from app.documentation.models import DocumentCategory


# Vaste dropdown-volgorde. Bewust expliciet, niet afgeleid van de enum-
# declaratievolgorde: de meest voorkomende importcategorie (DATASHEET)
# hoort eerst, en nieuwe categorieën moeten bewust worden toegevoegd.
CATEGORIE_VOLGORDE: tuple[DocumentCategory, ...] = (
    DocumentCategory.DATASHEET,
    DocumentCategory.APPLICATION_NOTE,
    DocumentCategory.MANUAL,
    DocumentCategory.MEASUREMENT_TECHNIQUE,
    DocumentCategory.REFERENCE_TABLE,
    DocumentCategory.SAFETY,
    DocumentCategory.INTERNAL_INSTRUCTION,
)


def naar_uppercase(line_edit: QLineEdit) -> None:
    """Converteer de inhoud van een QLineEdit naar uppercase.

    Behoudt de cursorpositie zodat de gebruiker normaal verder kan typen.
    Wordt aangesloten op textEdited, dat alleen vuurt bij echte
    gebruikersinvoer — niet bij programmatische setText. Daardoor geen
    recursie en geen onbedoelde conversie van bestaande waarden.

    Doet niets als de tekst al uppercase is: dat voorkomt onnodige
    setText-aanroepen die de cursorpositie zouden kunnen beïnvloeden.
    """
    tekst = line_edit.text()
    boven = tekst.upper()
    if tekst == boven:
        return
    cursor = line_edit.cursorPosition()
    line_edit.setText(boven)
    line_edit.setCursorPosition(min(cursor, len(boven)))


def vul_categorie_combo(
    combo: QComboBox,
    t: Callable[[str], str],
) -> None:
    """Vul een QComboBox met de categorieën en hun i18n-labels.

    De itemData bewaart de DocumentCategory.value (bijv. "DATASHEET").
    Het label komt uit i18n via de callable t: t("documentatie.categorieen.DATASHEET").

    Bestaande items worden eerst verwijderd. De selectie wordt NIET
    hersteld: de aanroeper is verantwoordelijk voor het bewaren en
    terugzetten van de selectie bij een taalwissel. Dit is bewust
    eenvoudig gehouden; de wizard en editor regelen dat zelf.

    Als de combo leeg is (geen selectie), kiest de aanroeper de default.
    """
    combo.blockSignals(True)
    try:
        combo.clear()
        for categorie in CATEGORIE_VOLGORDE:
            label = t(f"documentatie.categorieen.{categorie.value}")
            combo.addItem(label, categorie.value)
    finally:
        combo.blockSignals(False)