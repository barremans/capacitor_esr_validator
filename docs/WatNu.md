# Wat nu? — Electronics Diagnostic Tool Hub

**Versie:** 2.4.0
**Datum:** 2026-10-23
**Auteur:** Bart Bossuyt
**Doel:** beknopte gids voor "wat is de volgende stap" na een
afgeronde fase. Geen volledige overdracht — die staat in
`overdracht.md`.

---

## Huidige staat

- **Baseline tests:** 1700 passed.
- **Huidige versie:** `1.3.0`.
- **Database-schema:** v3 (herkomst-kolommen sinds §2.28).
- **Laatste afgeronde fase:** §2.28 — export/import tussen toestellen
  (zes sub-fases: 28A, 28B, 28C, 28E, 28D, 28F; +102 tests).
- **Volgende fase:** 12B — AI-model-keuze en API-koppeling
  (**op hold**, wacht op provider/model-keuze).

Dit bestand wordt bijgewerkt na elke fase.

---

## Waar te beginnen

### Als je een nieuwe chat start

1. Lees `overdracht.md` volledig.
2. Lees `docs/openvragen.md` voor de openstaande punten.
3. Vraag de bestanden op die de overdracht in **sectie 8** noemt.
4. Wacht op instructie "start <fase>".

### Als je zelf verder werkt

1. Open `overdracht.md` en kijk naar **sectie 4 (stappenplan)** om
   te zien wat de volgende fase is.
2. Lees de bijbehorende sectie in **sectie 6 (openstaande vragen)**.
3. Draai eerst `pytest -q` om te bevestigen dat de baseline klopt.
4. Begin met een **kleine, controleerbare** deelfase.

### Als je een bug hebt gevonden

1. Voeg een test toe die de bug reproduceert (in `tests/`).
2. Draai de test — die moet falen.
3. Fix de bug.
4. Draai de test — die moet slagen.
5. Draai de volledige suite.
6. Noteer de fix in de header van het gewijzigde bestand.

### Als je een nieuwe functie wilt toevoegen

1. Bepaal in welke **laag** de functie thuishoort:
   - GUI: `app/gui/`
   - Service: `app/services/`
   - Helper: `app/helpers/`
   - Storage: `app/storage/`
   - Documentatie: `app/documentation/`
   - Exchange: `app/services/exchange/`
2. Voeg nooit logica toe aan een laag die er niet voor bedoeld is.
3. Voeg een **pure** test toe waar mogelijk (geen Qt).
4. Voeg een **GUI**-test toe waar nodig (offscreen, geen `qtbot`).
5. Werk de i18n bij (NL + EN) voor nieuwe GUI-teksten.

---

## Belangrijke afspraken

- **Lever volledige bestanden**, nooit secties met
  `# ... ongewijzigd ...`.
- **JSON altijd volledig**, nooit fragmenten.
- **Eerst gerichte tests, dan volledige `pytest -q`.**
- **Een fase is pas afgerond als beide groen zijn.**
- **Meld nieuwe i18n-keys expliciet**, met NL én EN.
- **Python-headers zijn cumulatief.**
- **Geen `qtbot`** — er is geen `pytest-qt`.
- **`conftest.py` is een geaccepteerd onderdeel van de suite.**
- **Verwerk `deleteLater()` in GUI-tests** met
  `QApplication.processEvents()`.
- **De taalparameter van `ToolHubWindow` heeft voorrang op
  `settings.json`.** Idem voor `theme`.
- **`setStyleSheet` op het venster, niet op de `QApplication`.**
- **Thema doorgeven aan schermen** met een keyword-only
  `theme`-parameter en een `apply_theme(theme)`-methode.
- **Voor leesbare PDF's:** `QT_QPA_FONTDIR` wordt sinds 9A automatisch
  gezet in `main.py`.
- **De ArticleSearch-flow is de bewezen build-flow.**
- **Publiceren naar GitHub** gaat via `.\publish.ps1`.
- **`icon_paths.py` gebruikt sinds 11I.2 een expliciete
  `sys._MEIPASS`-branch** vóór de omhoog-zoeklus.
- **`build_installer.bat` logt sinds 11I.3 de PyInstaller-stap [4] en
  de ISCC-stap [7]** naar `build_log.txt`.
- **`build_and_publish.ps1` geeft sinds 11I.3 de bevestigingsvraag
  "Starten?" een expliciete standaardwaarde J.**
- **`signing-certs/` staat sinds 11I.4 in `.gitignore`.**
- **`app/services/exchange/` is sinds §2.28 de uniforme
  export/import-ingang.**
- **`docs/export_import_format.md` is bindend voor alle code in
  `app/services/exchange/`.**
- **Versie-bump bij de build, niet per sub-fase.** Bij de afronding
  van een fase mag de versie in `app/version.py` mee omhoog.

---

## Snelle links

| Doel | Bestand |
|---|---|
| Actuele projectstaat | `overdracht.md` |
| Architectuur | `docs/context.md` |
| Versiegeschiedenis | `docs/changelog/nl_NL.md`, `docs/changelog/en_US.md` |
| Open vragen | `docs/openvragen.md` |
| Header-standaard | `docs/python_header_standard.md` |
| Zoektaal | `docs/search_syntax.md` |
| Import-laag | `docs/documentation_import.md` |
| **Exchange-formaat** | **`docs/export_import_format.md`** |
| Roadmap | `docs/future_tools.md` |
| Eindgebruikershelp | `docs/help/nl_NL.md`, `docs/help/en_US.md` |
| Packaging | `docs/packaging.md` |
| Signing-flow (CGK) | `05-signing-build-context.md` |
| Defender-indicator | `signingContext.md` |
| GitHub-repo | `https://github.com/barremans/capacitor_esr_validator` |
| Laatste release | `https://github.com/barremans/capacitor_esr_validator/releases/latest` |
| Update-check pointer | `https://raw.githubusercontent.com/barremans/capacitor_esr_validator/main/releases/latest/version.txt` |