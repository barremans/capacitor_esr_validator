# OVERDRACHT — Electronics Diagnostic Tool Hub / ESR Tester

**Versie overdracht:** 4.3.0
**Datum:** 2026-10-14
**Auteur:** Bart Bossuyt
**Vorige versie:** 4.2.0 (2026-10-14)
**Doel:** volledig overdrachtsdocument voor een nieuwe ChatGPT-sessie of
nieuwe ontwikkelaar. Bevat projectstaat, architectuur, regels, changelog,
teststructuur en startprompt. Alles in één bestand.

**Huidige baseline:** 1203 passed
**Laatste afgeronde fase:** 9G — Bug/feature-rapportage naar GitHub
**Volgende fase:** 9H — Update-check bij opstarten + via Help

---

## INHOUD

1. Startprompt (lees dit eerst)
2. Context — projectstaat en architectuur
3. Kernregels — bindende afspraken
4. Stappenplan — chronologisch overzicht
5. Wat is nieuw sinds versie 4.2.0
6. Openstaande vragen voor de nieuwe chat
7. Teststatus — baseline en teststructuur
8. Bestanden die de nieuwe chat moet opvragen
9. Werkafspraken in een nieuwe sessie

---

## 1. STARTPROMPT

Je bent een ervaren Python/PySide6-ontwikkelaar en werkt mee aan het
project **Electronics Diagnostic Tool Hub / ESR Tester**.

Dit document bevat de volledige context. Lees het volledig voordat je
iets doet.

**Samenvatting van de huidige staat:**

- Projectmap: `C:\PY\capacitor_esr_validator`.
- Technologie: Python 3.12 + PySide6 (Qt6, Fusion-stijl), volledig offline.
- Baseline: **1203 passed**.
- Laatste afgeronde fase: **9G — Bug/feature-rapportage naar GitHub**
  (2026-10-14).
- Volgende fase: **9H — Update-check bij opstarten + via Help**.

**Werkafspraken die je strikt volgt:**

- Vraag altijd om de **volledige huidige inhoud** van een bestand
  voordat je het vervangt. Je hebt geen toegang tot de schijf van de
  gebruiker.
- **Uitzondering:** als een bestand in **deze sessie** al is geleverd of
  gezien, en er is geen reden om te twijfelen, mag je het hergebruiken
  zonder opnieuw op te vragen. Meld wel dat je dat doet.
- Lever altijd **volledige bestanden**, nooit secties met
  `# ... ongewijzigd ...` of een `"import": {...}`-fragment in een
  JSON-bestand.
- **JSON-bestanden altijd volledig leveren**, nooit fragmenten.
- Leg elke stap eerst kort uit, dan implementeren.
- Draai altijd eerst **gerichte tests**, dan **volledige `pytest -q`**.
- Een fase is pas afgerond wanneer **beide groen** zijn.
- Nieuwe GUI-tekst en tooltips lopen via **NL/EN i18n**; meld nieuwe
  keys expliciet met beide waarden.
- Python-bestanden krijgen een **header** met bestandsnaam, project,
  versie, datum, auteur, doel en **cumulatieve wijzigingshistoriek**.
  Zie `docs/python_header_standard.md`.
- **`pytest-qt` is geen dependency van dit project.** GUI-tests
  gebruiken `os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")` en
  een lokale `_app()`-helper (`QApplication.instance() or QApplication([])`).
  Er is geen `conftest.py`. Gebruik geen `qtbot`-fixture.
- **Verwerk `deleteLater()` in GUI-tests** met
  `QApplication.processEvents()` vóór je de menubar of andere
  QObject-hiërarchieën inspecteert. **Bewaar nooit een QMenu- of
  QAction-pointer tussen twee `processEvents()`-rondes**: die kan
  ongeldig worden. Lees altijd alles in één keer uit.
- **De taalparameter van `ToolHubWindow` heeft voorrang op
  `settings.json`.**
- **Voor leesbare PDF-rapporten:** sinds fase 9A zet `main.py`
  automatisch `QT_QPA_FONTDIR=C:\Windows\Fonts` op Windows.
- **Bij het leveren van `.md`-bestanden die zelf codeblokken bevatten:**
  gebruik **viervoudige backticks**.
- **De ArticleSearch-flow is de bewezen build-flow.**
- **Geen aannames over de volgende fase:** vraag het na.
- **Nooit een GitHub-token in een getrackt bestand, chat of
  context-document zetten.**

**Wat ik nu van je vraag:**

1. Bevestig dat je de context hebt gelezen en dat je de baseline en
   de volgende fase correct begrijpt.
2. Geef een korte samenvatting (max 10 regels) van de huidige
   projectstaat en de eerstvolgende fase.
3. Vraag om de bestanden uit sectie 8 van dit document **vóór** je
   begint met implementeren.
4. Wacht daarna op mijn instructie. Onderneem nog geen actie, behalve
   als ik expliciet zeg: "start <fase>".

**Belangrijk:** als iets in de context onduidelijk is, vraag het
eerst. Geen aannames.

---

## 2. CONTEXT — PROJECTSTAAT EN ARCHITECTUUR

### 2.1 Projectidentiteit

| | |
|---|---|
| Naam | Electronics Diagnostic Tool Hub / ESR Tester |
| Projectmap | `C:\PY\capacitor_esr_validator` |
| Platform | Windows 10 / 11 |
| Technologie | Python 3.12 + PySide6 (Qt6, Fusion) |
| Primaire tool | ESR / Condensator-validator |
| Toekomstige tools | Resistor (en andere diagnosetools) |
| Taal GUI | Nederlands + Engels (via i18n) |
| Werkmodus | Volledig offline, lokale opslag |
| Database | SQLite op `%LOCALAPPDATA%\ElectronicsDiagnosticToolHub\measurements.sqlite3` |
| GitHub-repo | `https://github.com/barremans/capacitor_esr_validator` |
| Huidige versie | `1.0.3` (gepubliceerd als GitHub-release `v1.0.3`) |
| Huidige baseline | **1203 passed** |
| Laatste afgeronde fase | 9G — Bug/feature-rapportage naar GitHub |
| Volgende fase | 9H — Update-check bij opstarten + via Help |

### 2.2 Huidige applicatiearchitectuur

**Eén-venster-navigatie (ToolHubWindow):**

- `QStackedWidget` met pagina's: hub, diagnose, ESR, historiek,
  documentatie, **analyse** (sinds 7B).
- Contextueel X-gedrag: binnen een pagina terug naar de bovenliggende
  pagina; op de hub sluit de applicatie.
- Menu: Bestand, Diagnose, **Rapporteren (sinds 9G)**, Instellingen,
  Help.
- **Belangrijk (v2.11.3):** `ToolHubWindow.__init__(taal=None)`
  respecteert de parameter `taal`. Valt alleen terug op `settings.json`
  als de parameter leeg is.

**Sneltoetsen:**

- **Globaal:** `Ctrl+Q`, `Ctrl+E`, `Ctrl+I`, `Ctrl+A`, `Ctrl+P`, `F1`.
- **ESR-scherm:** `Esc`, `Ctrl+Return`, `Ctrl+S`, `Ctrl+W`, `Ctrl+I`.
- **Historiek:** `Esc`, `Ctrl+R`, `Ctrl+F`, `Ctrl+D`, `Ctrl+H`.
- **Hoofdmenu:** `Ctrl+D`, `Ctrl+H`, `Ctrl+K`, `Ctrl+A`, `Esc`.
- **Diagnose:** `Esc`.
- **Documentatie:** `Esc`, `Return`, `Ctrl+F`, `Ctrl+L`, `Ctrl+O`, `F1`.
- **Analyse:** `Esc`, `Ctrl+R`, `Ctrl+F`.
- **Rapport:** `Ctrl+P` (Bestand-menu).
- **Import-wizard:** `Ctrl+D` (datum op vandaag).
- **Metadata-editor:** `Ctrl+D` (datum op vandaag).

Alle lokale sneltoetsen gebruiken `WidgetWithChildrenShortcut`.

**Storage:**

- SQLite op `%LOCALAPPDATA%\ElectronicsDiagnosticToolHub\measurements.sqlite3`.
- Schema v1: 7 tabellen. Schema v2: `measurements.tool_key`.
- Migratieframework transactioneel en sequentieel.

**Analyse-laag (fase 7):**

- `app/helpers/analysis_series.py` — pure functies.
- `app/services/analysis_service.py` — read-only service.
- `app/gui/analysis_screen.py` (v1.0.6) — QtCharts-pagina.

**Rapportage-laag (fase 8):**

- `app/services/report_service.py` (v1.2.0) — read-only service.
- `app/helpers/report_render.py` (v1.4.0) — pure HTML-renderer.
- `app/helpers/report_pdf.py` (v1.0.0) — Qt-specifiek.
- `app/helpers/report_chart.py` (v1.0.3) — Qt-specifiek.
- `app/gui/dialogs/report_dialog.py` (v1.2.0) — modale dialoog.

**Documentatie (read-only viewer + editor):**

- Service met 8 meertalige documenten in de ingebouwde catalogus.
- Zoektaal met operatoren: `,` (AND), `|` (OR), `-` (exact),
  `!` (uitsluiten), `%` (wildcard).
- Bewerken-knop voor eigen imports (5D'.2c).
- Status wijzigen-knop voor eigen imports, Toon gearchiveerde-checkbox,
  Status-kolom (5D'.2e).

**Documentatie-import (fase 5, 5D', 6):**

- Wizard voor PDF-, Word-, Excel- en URL-import.
- Twee cataloguslagen: ingebouwde en gebruikerscatalogus.
- Statusmachine: `CONCEPT → ACTIEF → GEARCHIVEERD`, met `revoke`.

**i18n:**

- Alle GUI-teksten via `app/helpers/i18n.py` en JSON-bestanden onder
  `i18n/locales/<taal>/`.
- Modules: `app.json`, `esr.json`, `history.json`, `documentation.json`,
  `settings.json`, `language.json`, `analysis.json`, `report.json`.
- Ontbrekende EN-key valt terug op NL.
- Live taalwissel behoudt state.

**Qt-stijl:**

- `main.py` zet `app.setStyle("Fusion")` vóór `apply_dark_theme(app)`.
- `styles.py` bevat expliciete `QCheckBox::indicator` en
  `QRadioButton::indicator`.

**Buildstraat (fase 9A–9F):**

- `app/version.py` — centrale versie, momenteel `1.0.3`.
- `main.py` — `QT_QPA_FONTDIR` automatisch, `setApplicationVersion`.
- `bump_version.py` — verhoogt patch/minor/major in `app/version.py`.
- `ESR_Tester.spec` (v2.1.0) — PyInstaller-specificatie met `icon=`
  actief. Sinds 9G: controleblok + `hiddenimports` voor
  `github_feedback_config` en `github_secret_local`.
- `build_installer.bat` (v2.0.1) — volgt de ArticleSearch-flow.
- `build_and_publish.ps1` (v1.0.0) — orchestrator met signing-preflight.
- `publish.ps1` (v1.0.0) — GitHub-release met release-gate.
- `Export-SigningCertificate.ps1` (v1.0.1) — exporteert het
  Authenticode-certificaat als `.cer`.
- **Certificaat:** subject `CN=CGK Local Signing`, actief thumbprint
  `BD1DC390D56E3392836FD6E39470D5F766346509`, geldig tot 2028-09-17.

**GitHub-feedbacklaag (fase 9G):**

- Vijf identieke pakketbestanden in de projectroot:
  `github_feedback.py` (v1.0.0), `bug_report_dialog.py` (v2.0.0),
  `github_cases.py` (v2.0.0), `check_github_secret.py` (v1.0.0),
  `github_secret_local.example.py` (v1.0.0).
- Eén app-specifieke `github_feedback_config.py` (v1.0.0) met
  `APP_NAME = "ESR Tester"`, `GITHUB_OWNER = "barremans"`,
  `GITHUB_REPO = "capacitor_esr_validator"`, `get_reporter_name()` via
  `getpass`, `get_app_version()` via `app.version`.
- `github_secret_local.py` — het token, in `.gitignore` via
  `*_secret_local.py`. **Nooit committen.**
- Nieuw menu "Rapporteren" in `main_window.py` v2.12.0 met twee acties:
  "🐞 Bug of feature melden…" en "Open cases tonen".
- Nieuwe i18n-keys: `menu.rapporteren`, `menu.bug_melden`,
  `menu.open_cases` (NL + EN).
- De melding wordt een GitHub Issue met label `bug` of `enhancement`.
  De kopregel van de Issue bevat de naam van de melder, de datum en de
  app-versie.
- `check_github_secret.py` controleert vóór elke build dat er geen
  token in git staat, dat `github_secret_local.py` genegeerd wordt, en
  dat het token nog door GitHub aanvaard wordt.

### 2.3 Belangrijke recente bugfixes (8D+, 9A–9G)

- **`algemeen.ja` / `algemeen.nee` lekten in rapport-HTML** (v1.3.0 van
  `report_render.py`): vervangen door `app.ja` / `app.nee`.
- **Enum-codes in rapport niet vertaald** (v1.4.0 van
  `report_render.py`): nu via `_status_code_label`.
- **Grafiek-checkbox in `ReportDialog` niet deterministisch** (v1.2.0):
  vervangen door een expliciete `grafiek_default`-parameter.
- **`SettingsDialog` overschreef `laatste_exportmap` en
  `laatste_importmap`** (v1.3.0): nu via `replace()`.
- **`QT_QPA_FONTDIR` probleem op Windows:** sinds 9A zet `main.py` de
  variabele automatisch.
- **Venstertitels van Help- en Wijzigingslog-vensters** gebruikten
  verkeerde keys (v2.11.6): nu `dialog.help_title` en
  `dialog.changelog_title`.
- **ESR-knop in Diagnose-pagina** toonde de ruwe key `tool.esr`: nu
  vertaald.
- **Pandas/numpy ABI-conflict** in de build: opgelost met pins.
- **`: was unexpected at this time.`** in `build_installer.bat` blok
  `[6]`: vervangen door een `if defined`-check (v2.0.1).
- **LF/CRLF-waarschuwing** bij `git add releases/latest/version.txt`:
  opgelost in 9F via `.gitattributes`.
- **`ESR_Tester.spec` in `.gitignore`**: opgelost in 9F via
  `!ESR_Tester.spec`.
- **`RuntimeError: Internal C++ object (QMenu) already deleted`** in
  GUI-tests (v1.0.1 van `test_main_window_reporting_menu.py`):
  oorzaak was dat een `QMenu`-pointer tussen twee
  `processEvents()`-rondes bewaard werd. `_apply_language()` ruimt de
  menu's op met `menubar.clear()` + `deleteLater()`. Oplossing: alle
  helpers lezen de menu-inhoud in één keer uit en geven strings terug,
  nooit `QMenu`-objecten die bewaard worden.

### 2.4 Openstaande werkpunten

Volgens het stappenplan:

- **9G** — Bug/feature-rapportage naar GitHub. **Afgerond 2026-10-14.**
- **9H** — Update-check bij opstarten + via Help. **Volgende fase.**
  De "latest"-pointer op `releases/latest/version.txt` is sinds 9E
  beschikbaar. ArticleSearch heeft een `updater.py` (v1.3.0) als
  voorbeeld.
- **10** — Praktische ESR-validatie.
- **11** — Laatste UX/documentatie-afwerking (incl. light theme,
  async URL-fetch, cosmetische punten, visuele selectie in Analyse,
  checkbox-zichtbaarheid donker thema, i18n-menging in Diagnose/Result).
- **12** — AI-extractie uit fabrikantdocumenten.
- **13** — Menselijke validatie van AI-output.
- **14** — Goedgekeurde fabrikantdata koppelen aan assessment.
- **15** — Tweede diagnosetool — Resistor.

### 2.5 Werkafspraken voor een nieuwe sessie

- Vraag altijd om de huidige bestandsinhoud voordat je een bestaand
  bestand vervangt.
- Uitzondering: als je het bestand in deze sessie al hebt geleverd
  of gezien en er is geen tegenspraak, mag je het direct hergebruiken.
- Lever altijd volledige bestanden, nooit secties met
  `# ... ongewijzigd ...`.
- Lever volledige JSON-bestanden, nooit fragmenten.
- Draai eerst gerichte tests, dan volledige `pytest -q`.
- Meld nieuwe i18n-keys expliciet, met de waarde voor NL én EN.
- Python-headers zijn cumulatief.
- **Geen `qtbot` gebruiken in tests.** Er is geen `pytest-qt`.
- **Verwerk `deleteLater()` in GUI-tests** met
  `QApplication.processEvents()`. **Bewaar nooit een QMenu- of
  QAction-pointer tussen twee `processEvents()`-rondes.**
- De taalparameter van `ToolHubWindow` heeft voorrang op
  `settings.json`.
- Bij het leveren van `.md`-bestanden met codeblokken: viervoudige
  backticks.
- De ArticleSearch-flow is de bewezen build-flow.
- **Nooit een GitHub-token in een getrackt bestand, chat of
  context-document zetten.**
- Geen aannames over de eerstvolgende fase — vraag het na.

---

## 3. KERNREGELS — BINDENDE AFSPRAKEN

### 3.1 Werkwijze

1. **Kleine, controleerbare fasen.**
2. **Eerst kort uitleggen wat de stap doet; daarna implementeren.**
3. **Volledige bestanden leveren**, geen losse patches als eindresultaat.
4. **Python-bestanden houden versie, datum en wijzigingshistoriek bij.**
5. **Nieuwe GUI-tekst en tooltips lopen via NL/EN i18n.**
6. **GUI, storage, documentatie en assessmentlogica blijven gescheiden.**
7. **Geen stille database-reset.**
8. **Historische metingen worden nooit automatisch opnieuw beoordeeld.**
9. **Originele bronnen worden nooit stil vervangen.**
10. **Provenance / bronherkomst blijft traceerbaar.**
11. **Fabrikantdata wordt niet automatisch actief.**
12. **Gerichte tests eerst, daarna volledige `pytest -q`.**
13. **Een fase is pas afgerond wanneer gerichte tests én volledige
    suite groen zijn.**
14. **Geen verborgen correcties of stilzwijgende omrekeningen.**
15. **Backward-compatible waar redelijk mogelijk.**
16. **Multitool-architectuur mag de ESR-tool niet destabiliseren.**
17. **Documentatie-import, -viewer en -assessment zijn afzonderlijke
    verantwoordelijkheden.**
18. **AI-extractie staat laat in de roadmap.**
19. **Grafieken en trends lezen bestaande data, ze wijzigen niets.**
20. **Rapporten lezen bestaande data, ze wijzigen niets.**
21. **Bij het leveren van `.md`-bestanden met codeblokken: viervoudige
    backticks.**
22. **De ArticleSearch-flow is de bewezen build-flow.**
23. **Nooit een GitHub-token in een getrackt bestand, chat of
    context-document zetten.**

### 3.2 Architectuur

- **Assessment-service** bevat beoordelingslogica — geen GUI, geen database.
- **Storage-service** kent structurele validatie — geen beoordelingslogica.
- **Documentatie-service** is read-only — geen import, geen AI,
  geen assessment.
- **Import-service** schrijft alleen in de gebruikerscatalogus.
- **GUI** verzamelt invoer, roept services aan, toont resultaat.
- **Analyse-laag** (fase 7) leest de storage read-only.
- **Rapportage-laag** (fase 8) leest de storage en de analyse-laag
  read-only.
- **Buildstraat** (fase 9) is gescheiden van de applicatiecode.
- **GitHub-feedbacklaag** (fase 9G) is eveneens gescheiden van de
  applicatiecode: vijf identieke pakketbestanden in de projectroot,
  plus een app-specifieke `github_feedback_config.py`, plus een
  niet-getrackte `github_secret_local.py`. De meldschermen zijn GUI;
  `github_feedback.py` is puur; `check_github_secret.py` is een
  build-controle.

### 3.3 ESR-technische kernregels

1. **Datasheet vóór algemene ESR-tabel.**
2. **Geen verborgen ESR-frequentieconversie.**
3. **Ruwe meetdata bewaren.**
4. **Status en betrouwbaarheid zijn afzonderlijke concepten.**
5. **Referentiebron, referentiefrequentie en type zichtbaar houden.**
6. **Elektrolytische ESR-tabel niet toepassen op ander type zonder
   type-match.**
7. **Testspanning registreren; niet automatisch corrigeren.**
8. **`EX_SITU` > `ONE_LEG` > `IN_CIRCUIT`.**
9. **C-ESR-D-consistentie is plausibiliteitscontrole, geen afkeurregel.**
10. **Eerst praktijkdata verzamelen; daarna referenties/drempels
    aanpassen.**
11. **OL/out-of-range nooit als 0 interpreteren.**

### 3.4 Verboden handelingen zonder expliciete toestemming

- Een database verwijderen of opnieuw aanmaken.
- Een historische meting opnieuw beoordelen.
- Een originele bron (document, referentie) vervangen zonder
  gebruikersbevestiging.
- Een `# ... ongewijzigd ...`-sectie inleveren.
- Een fase als "afgerond" bestempelen zonder groene testsuite.
- Een `.md`-bestand met codeblokken leveren zonder viervoudige
  backticks.
- De ArticleSearch-flow vervangen door een eigen variant.
- **Een GitHub-token in een getrackt bestand, chat, of
  context-document zetten.**
- **Een QMenu- of QAction-pointer bewaren tussen twee
  `processEvents()`-rondes in een GUI-test.**

---

## 4. STAPPENPLAN — CHRONOLOGISCH OVERZICHT

| Fase | Onderwerp | Status |
|---|---|---|
| 0 t/m 8E | (zie changelog en eerdere overdrachten) | ✅ |
| 9A | Versie, `QT_QPA_FONTDIR`, `setApplicationVersion`, icoonmap | ✅ |
| 9A.1 | Over-dialoog met versie + bugfix help/changelog-titels | ✅ |
| 9B.1 | `bump_version.py` | ✅ |
| 9B.2 | `ESR_Tester.spec` + `build_installer.bat` | ✅ |
| 9C | Inno Setup installer | ✅ |
| 9D | Signing | ✅ |
| 9E | GitHub Release | ✅ |
| 9F | Intune/Defender/CFA-testmatrix + `docs/packaging.md` | ✅ |
| **9G** | **Bug/feature-rapportage naar GitHub** | **✅** |
| **9H** | **Update-check bij opstarten + via Help** | **Volgende** |
| 10 | Praktische ESR-validatie | Gepland |
| 11 | Laatste UX/documentatie-afwerking | Gepland |
| 12 | AI-extractie uit fabrikantdocumenten | Gepland |
| 13 | Menselijke validatie van AI-output | Gepland |
| 14 | Goedgekeurde fabrikantdata koppelen aan assessment | Gepland |
| 15 | Tweede diagnosetool — Resistor | Gepland |

---

## 5. WAT IS NIEUW SINDS VERSIE 4.2.0

### 5.1 Fase 9G — Bug/feature-rapportage naar GitHub

- **Uniform pakket uitgerold** volgens `GITHUB_FEEDBACK_UITROL.md`:
  vijf identieke bestanden in de projectroot, één app-specifieke
  config, één niet-getrackt tokenbestand.
- **Nieuwe bestanden:**
  - `github_feedback.py` (v1.0.0) — GitHubFeedbackClient, geen Qt,
    geen token.
  - `bug_report_dialog.py` (v2.0.0) — BugDialog.
  - `github_cases.py` (v2.0.0) — show_github_cases.
  - `check_github_secret.py` (v1.0.0) — build-controle.
  - `github_secret_local.example.py` (v1.0.0) — sjabloon.
  - `github_feedback_config.py` (v1.0.0) — app-specifiek.
  - `tests/test_github_feedback_config.py` (v1.0.0) — 10 tests.
  - `tests/test_github_feedback_client.py` (v1.0.0) — 22 tests.
  - `tests/test_check_github_secret.py` (v1.0.1) — 11 tests.
  - `tests/test_main_window_reporting_menu.py` (v1.0.1) — 10 tests.
- **Gewijzigde bestanden:**
  - `.gitignore` — `*_secret_local.py` toegevoegd.
  - `app/gui/main_window.py` — v2.11.6 → v2.12.0. Nieuw menu
    "Rapporteren" tussen Diagnose en Instellingen. Nieuwe methoden
    `_show_bug_report_dialog()` en `_show_open_cases()`.
  - `i18n/locales/nl_NL/app.json` — 3 nieuwe keys.
  - `i18n/locales/en_US/app.json` — 3 nieuwe keys.
  - `ESR_Tester.spec` — v2.0.0 → v2.1.0. Controleblok + twee
    `hiddenimports`.
- **Nieuwe i18n-keys:**

  | Key | NL | EN |
  |---|---|---|
  | `menu.rapporteren` | `Rapporteren` | `Report` |
  | `menu.bug_melden` | `🐞 Bug of feature melden…` | `🐞 Report a bug or feature…` |
  | `menu.open_cases` | `Open cases tonen` | `Show open cases` |

- **Bewezen op 2026-10-14:** een testbug en een testfeature zijn
  succesvol aangemaakt als GitHub Issues met de juiste labels, en
  worden correct getoond in het "Open cases"-scherm.
- **Baseline:** van 1150 naar **1203 passed** (+53 tests).

### 5.2 Gewijzigde bestanden sinds 4.2.0

| Bestand | Versie / status |
|---|---|
| `.gitignore` | `*_secret_local.py` toegevoegd |
| `app/gui/main_window.py` | v2.12.0 (was v2.11.6) |
| `ESR_Tester.spec` | v2.1.0 (was v2.0.0) |
| `i18n/locales/nl_NL/app.json` | 3 nieuwe keys |
| `i18n/locales/en_US/app.json` | 3 nieuwe keys |
| `github_feedback.py` | **nieuw** (v1.0.0) |
| `bug_report_dialog.py` | **nieuw** (v2.0.0) |
| `github_cases.py` | **nieuw** (v2.0.0) |
| `check_github_secret.py` | **nieuw** (v1.0.0) |
| `github_secret_local.example.py` | **nieuw** (v1.0.0) |
| `github_feedback_config.py` | **nieuw** (v1.0.0) |
| `github_secret_local.py` | **nieuw** (niet in git) |
| `tests/test_github_feedback_config.py` | **nieuw** (v1.0.0) |
| `tests/test_github_feedback_client.py` | **nieuw** (v1.0.0) |
| `tests/test_check_github_secret.py` | **nieuw** (v1.0.1) |
| `tests/test_main_window_reporting_menu.py` | **nieuw** (v1.0.1) |
| `docs/changelog.md` | Versie 1.10 toegevoegd |
| `docs/openvragen.md` | v2.2.0 (was v2.1.0) |
| `overdracht.md` | v4.3.0 (dit bestand) |

### 5.3 Teststatus

**Baseline: 1203 passed.** Was 1150 in v4.2.0. De 53 nieuwe tests:

| Bestand | Aantal |
|---|---|
| `tests/test_github_feedback_config.py` | 10 |
| `tests/test_github_feedback_client.py` | 22 |
| `tests/test_check_github_secret.py` | 11 |
| `tests/test_main_window_reporting_menu.py` | 10 |
| **Totaal** | **53** |

Volledige suite: **1203 passed in 32.26s**.

### 5.4 Bekende beperkingen (ongewijzigd t.o.v. 4.2.0, plus nieuwe)

- Geen OCR voor gescande PDF's.
- `.doc` en `.xls` worden geweigerd.
- Geen async URL-fetch.
- Datum-parsing bij bewerken accepteert alleen ISO-formaat.
- Geen bulk-edit / bulk-statuswijziging.
- Geen reden bij archiveren.
- Cosmetische scrollbar in Word-samenvatting.
- Analyse-pagina: geen zoom/pan, geen PNG/PDF-export, geen visuele
  selectie.
- Rapportage: alleen "één meting" in de GUI.
- **Geen update-check** — volgt in 9H. De "latest"-pointer is sinds
  9E beschikbaar.
- Pandas-pin `<3`, numpy als directe dependency.
- Defender-indicator op Intune-pc's vereist eenmalige `.cer`-upload.
- WDAC/AppLocker: bevestigd **niet actief** (2026-10-13).
- **GitHub-token per app.** Elk token heeft alleen toegang tot één
  repo (fine-grained). Eén token per app, niet delen.
- **Meldingen zijn publiek leesbaar** — de repo is publiek. Houd
  testtekst neutraal.

---

## 6. OPENSTAANDE VRAGEN VOOR DE NIEUWE CHAT

### 6.1 Overige openstaande punten

- **`Architecture identifier "x64" is deprecated`** — oplossen door
  `x64compatible` in de batch te schrijven.
- **LF/CRLF-waarschuwing** — **opgelost in 9F**.
- **`ESR_Tester.spec` in `.gitignore`** — **opgelost in 9F**.
- **Reden opgeven bij archiveren.**
- **Filter voor alleen gearchiveerde documenten.**
- **Bulk-edit en bulk-statuswijziging.**
- **OCR voor gescande PDF's.**
- **Async URL-fetch.**
- **Light theme.**
- **AI-tekstextractie uit docx/xlsx.**
- **Cosmetische scrollbar in Word-samenvatting.**
- **Analyse-pagina:** automatische as-schaling,
  `QDateTimeAxis`-tickformaat, zoom/pan, **visuele selectie**.
- **Rapportage:** GUI voor scope "selectie" en "filters".
- **Rapportage:** menu-item disabled maken als er geen selectie is.
- **Pandas-pin `<3`:** wanneer losser maken?
- **Numpy als directe dependency:** blijft dat zo?
- **`[rename] Fallback via robocopy...`-melding:** opruimen.
- **`build_log.txt` blijft leeg:** volledige output loggen?
- **Relatief `icon_path` in `main_window.py`:** verfijnen.
- **Twee verlopen certificaten in `CurrentUser\My`** —
  `4DA652...`, `13B90D...`.
- **Checkbox-zichtbaarheid in donker thema** (Analyse + History).
- **i18n-menging in Diagnose/Result en Resultaatdetails.**

---

## 7. TESTSTATUS — BASELINE EN TESTSTRUCTUUR

**Datum:** 2026-10-14
**Baseline:** 1203 passed
**Werkwijze:** eerst gerichte tests, dan volledige `pytest -q`.

### 7.1 Commando's

```powershell
# Eerst gerichte tests van de fase
pytest tests/test_<fase>.py -q

# Daarna volledige suite
pytest -q
```

### 7.2 GUI-tests

GUI-tests gebruiken:

```python
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
```

en een lokale `_app()`-helper:

```python
def _app():
    return QApplication.instance() or QApplication([])
```

**Geen `pytest-qt`, geen `qtbot`.**

**Belangrijk:** bewaar nooit een `QMenu`- of `QAction`-pointer tussen
twee `processEvents()`-rondes. `_apply_language()` ruimt de menu's op
met `menubar.clear()` + `deleteLater()`. Lees altijd alles in één keer
uit en geef strings terug.

### 7.3 Voor leesbare PDF's

Sinds fase 9A zet `main.py` de variabele automatisch.

### 7.4 Build testen

```powershell
# Volledige build + optioneel publiceren
.\build_and_publish.ps1

# Of alleen de build, zonder publiceren:
$env:AS_BUMP_PART = "patch"
$env:AS_MAKE_INSTALLER = "J"
$env:AS_DO_SIGN = "J"
.\build_installer.bat
```

Resultaat:

- `dist\ESR_Tester_<versie>\ESR_Tester.exe` (gesigned)
- `dist\ESR_TesterSetup_<versie>.exe` (gesigned)

**Let op sinds 9G:** `ESR_Tester.spec` roept `check_github_secret.py`
aan vóór de build. Zonder geldig token stopt de build. Zorg dus dat
`github_secret_local.py` bestaat en gevuld is.

### 7.5 Publiceren (fase 9E)

```powershell
.\publish.ps1
```

### 7.6 GitHub-token controleren (fase 9G)

```powershell
# Volledige controle
python check_github_secret.py

# Zonder token (enkel git-controles)
python check_github_secret.py --skip-token

# Zonder online test
python check_github_secret.py --skip-online
```

---

## 8. BESTANDEN DIE DE NIEUWE CHAT MOET OPVRAGEN

Voor een nieuwe sessie heeft de chat meestal nodig:

- `overdracht.md` (dit bestand) — primaire bron
- `docs/context.md` — architectuur en ontwerpprincipes
- `docs/openvragen.md` — levende lijst
- `docs/changelog.md` — versiegeschiedenis voor de gebruiker
- `PROJECT_STRUCTURE.md` — automatisch gegenereerde mappenstructuur

Bij een specifieke fase vraagt de chat om de bestanden die de fase raakt.

**Voor fase 9H (update-check bij opstarten + via Help):**

- `releases/latest/version.txt` — de "latest"-pointer
- `publish.ps1` — om te zien welk formaat de pointer heeft
- `main.py` — waar de check moet komen
- `app/gui/main_window.py` — huidige versie (v2.12.0) — voor het
  Help-menu-item
- `app/version.py` — huidige versie (1.0.3) — om te vergelijken
- `updater.py` — als die bestaat in ArticleSearch (`C:\searcharticle_code`),
  als voorbeeld (v1.3.0)
- `i18n/locales/nl_NL/app.json` — voor nieuwe i18n-keys
- `i18n/locales/en_US/app.json` — idem

---

## 9. WERKAFSPRAKEN IN EEN NIEUWE SESSIE

- Vraag altijd om de huidige bestandsinhoud voordat je een bestaand
  bestand vervangt.
- Uitzondering: als je het bestand in deze sessie al hebt geleverd
  of gezien en er is geen tegenspraak, mag je het direct hergebruiken.
- Lever altijd volledige bestanden, nooit secties met
  `# ... ongewijzigd ...`.
- Lever volledige JSON-bestanden, nooit fragmenten.
- Draai eerst gerichte tests, dan volledige `pytest -q`.
- Meld nieuwe i18n-keys expliciet, met de waarde voor NL én EN.
- Python-headers zijn cumulatief.
- **Bij het leveren van `.md`-bestanden die zelf codeblokken bevatten:
  gebruik viervoudige backticks.**
- **De ArticleSearch-flow is de bewezen build-flow.**
- **Nooit een GitHub-token in een getrackt bestand, chat of
  context-document zetten.**
- **Bewaar nooit een QMenu- of QAction-pointer tussen twee
  `processEvents()`-rondes in een GUI-test.**
- Geen aannames over de eerstvolgende fase — vraag het na.