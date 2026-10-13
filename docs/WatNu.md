# Wat nu? — Electronics Diagnostic Tool Hub

**Versie:** 1.3.0
**Datum:** 2026-10-13
**Auteur:** Bart Bossuyt
**Doel:** beknopte gids voor "wat is de volgende stap" na een
afgeronde fase. Geen volledige overdracht — die staat in
`overdracht.md`.

---

## Huidige staat

- **Baseline tests:** 1150 passed.
- **Huidige versie:** `1.0.3`, gepubliceerd als GitHub-release
  `v1.0.3` op 2026-10-13.
- **Laatste afgeronde fase:** 9E — GitHub Release.
- **Volgende fase:** 9F — Intune/Defender/CFA-testmatrix +
  `docs/packaging.md`.

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
- **Verwerk `deleteLater()` in GUI-tests** met
  `QApplication.processEvents()`.
- **De taalparameter van `ToolHubWindow` heeft voorrang op
  `settings.json`.**
- **Voor leesbare PDF's:** `QT_QPA_FONTDIR` wordt sinds 9A automatisch
  gezet in `main.py`.
- **De ArticleSearch-flow is de bewezen build-flow.** Wijk daar niet
  meer van af. Concreet:
  - `build_installer.bat` genereert `dist\installer.iss`.
  - `build_and_publish.ps1` orkestreert de hele keten.
  - `publish.ps1` doet de GitHub-release met release-gate op
    Authenticode-handtekening.
- **Publiceren naar GitHub** gaat via `.\publish.ps1` vanuit de
  repo-root. De release-gate weigert ongesigneerde installers.
  `publish.ps1` werkt `releases/latest/version.txt` bij en pusht
  `app/version.py` + `version.txt` naar `origin/main`.

---

## Snelle links

| Doel | Bestand |
|---|---|
| Actuele projectstaat | `overdracht.md` |
| Architectuur | `docs/context.md` |
| Versiegeschiedenis | `docs/changelog.md` |
| Open vragen | `docs/openvragen.md` |
| Header-standaard | `docs/python_header_standard.md` |
| Zoektaal | `docs/search_syntax.md` |
| Import-laag | `docs/documentation_import.md` |
| Roadmap | `docs/future_tools.md` |
| Eindgebruikershelp | `docs/help/nl_NL.md`, `docs/help/en_US.md` |
| Signing-flow (CGK) | `05-signing-build-context.md` |
| Defender-indicator | `signingContext.md` |
| GitHub-repo | `https://github.com/barremans/capacitor_esr_validator` |
| Laatste release | `https://github.com/barremans/capacitor_esr_validator/releases/tag/v1.0.3` |
| Update-check pointer | `https://raw.githubusercontent.com/barremans/capacitor_esr_validator/main/releases/latest/version.txt` |