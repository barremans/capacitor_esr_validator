# Wat nu? — Electronics Diagnostic Tool Hub

**Versie:** 2.3.0
**Datum:** 2026-10-22
**Auteur:** Bart Bossuyt
**Doel:** beknopte gids voor "wat is de volgende stap" na een
afgeronde fase. Geen volledige overdracht — die staat in
`overdracht.md`.

---

## Huidige staat

- **Baseline tests:** 1548 passed.
- **Huidige versie:** `1.2.3`.
- **Laatste afgeronde fase:** 11I.5 — afronding fase 11I. Daarmee is
  **11I volledig afgerond** (11I.1 t/m 11I.5).
- **Volgende fase:** 12 — AI-extractie uit fabrikantdocumenten.

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
6. Noteer de fix in de header van het gewijzigde bestand
   (cumulatieve wijzigingshistoriek).

### Als je een nieuwe functie wilt toevoegen

1. Bepaal in welke **laag** de functie thuishoort:
   - GUI: `app/gui/`
   - Service: `app/services/`
   - Helper: `app/helpers/`
   - Storage: `app/storage/`
   - Documentatie: `app/documentation/`
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
- **`conftest.py` is een geaccepteerd onderdeel van de suite.** Houd
  hem minimaal: alleen `QT_QPA_PLATFORM=offscreen` en de
  autouse-opruimfixture. Geen projectimports.
- **Verwerk `deleteLater()` in GUI-tests** met
  `QApplication.processEvents()`.
- **De taalparameter van `ToolHubWindow` heeft voorrang op
  `settings.json`.** Hetzelfde geldt sinds 11H.3 voor de
  `theme`-parameter.
- **`setStyleSheet` op het venster, niet op de `QApplication`.**
  Enige uitzondering: `apply_theme(app, thema)` in `main.py` bij
  opstart, voor dialogen zonder parent.
- **Thema doorgeven aan schermen** met een keyword-only
  `theme`-parameter en een `apply_theme(theme)`-methode, zoals in
  `AnalysisScreen` (sinds 11H.4) en `HistoryScreen` (sinds 11H.5).
- **Voor leesbare PDF's:** `QT_QPA_FONTDIR` wordt sinds 9A automatisch
  gezet in `main.py`.
- **De ArticleSearch-flow is de bewezen build-flow.** Wijk daar niet
  meer van af.
- **Publiceren naar GitHub** gaat via `.\publish.ps1` vanuit de
  repo-root. De release-gate weigert ongesigneerde installers.
- **`QChart.zoomReset()` herstelt de range die actief was op het
  moment van de reset, niet de oorspronkelijke.** Bewaar de originele
  range per as en herstel die expliciet.
- **De `export_scope_combo` in `analysis_screen.py` stuurt zowel de
  grafiek als de export aan.** De attribuutnaam is ongewijzigd
  gebleven voor backward-compat.
- **Gebruik `_sluit_app()` voor expliciet afsluiten.**
  `closeEvent` accepteert het event alleen als `_force_close` True is;
  anders blijft het contextuele "terug naar hub"-gedrag voor de
  venster-X op een subpagina.
- **`icon_paths.py` gebruikt sinds 11I.2 een expliciete
  `sys._MEIPASS`-branch** vóór de omhoog-zoeklus.
- **`build_installer.bat` logt sinds 11I.3 de PyInstaller-stap [4] en
  de ISCC-stap [7]** naar `build_log.txt`; `build_log.txt` staat in
  `.gitignore`.
- **`build_and_publish.ps1` geeft sinds 11I.3 de bevestigingsvraag
  "Starten?" een expliciete standaardwaarde J.**
- **`signing-certs/` staat sinds 11I.4 in `.gitignore`.**

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
| Roadmap | `docs/future_tools.md` |
| Eindgebruikershelp | `docs/help/nl_NL.md`, `docs/help/en_US.md` |
| Packaging | `docs/packaging.md` |
| Signing-flow (CGK) | `05-signing-build-context.md` |
| Defender-indicator | `signingContext.md` |
| GitHub-repo | `https://github.com/barremans/capacitor_esr_validator` |
| Laatste release | `https://github.com/barremans/capacitor_esr_validator/releases/latest` |
| Update-check pointer | `https://raw.githubusercontent.com/barremans/capacitor_esr_validator/main/releases/latest/version.txt` |