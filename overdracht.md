# OVERDRACHT — Electronics Diagnostic Tool Hub / ESR Tester

**Versie overdracht:** 5.1.0
**Datum:** 2026-10-15
**Auteur:** Bart Bossuyt
**Vorige versie:** 5.0.0 (2026-10-15)
**Doel:** volledig overdrachtsdocument voor een nieuwe ChatGPT-sessie of
nieuwe ontwikkelaar. Bevat projectstaat, architectuur, regels, changelog,
teststructuur en startprompt. Alles in één bestand.

**Huidige baseline:** 1297 passed
**Laatste afgeronde fase:** 10B — drempelvalidatie
**Volgende fase:** 11 — Laatste UX/documentatie-afwerking

---

## INHOUD

1. Startprompt (lees dit eerst)
2. Context — projectstaat en architectuur
3. Kernregels — bindende afspraken
4. Stappenplan — chronologisch overzicht
5. Wat is nieuw sinds versie 5.0.0
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
- Baseline: **1297 passed**.
- Laatste afgeronde fase: **10B — drempelvalidatie** (2026-10-15).
- Volgende fase: **11 — Laatste UX/documentatie-afwerking**.

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
| Huidige versie | `1.1.2` (gepubliceerd als GitHub-release `v1.1.2`) |
| Huidige baseline | **1297 passed** |
| Laatste afgeronde fase | 10B — drempelvalidatie |
| Volgende fase | 11 — Laatste UX/documentatie-afwerking |

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
- **Belangrijk (v2.13.0):** `ToolHubWindow.__init__(taal=None,
  check_on_startup=True)` plant een eenmalige, niet-blokkerende
  update-check via `QTimer.singleShot(0, …)`. De waarde komt uit
  `main.py`, die `algemeen.controleer_updates_bij_opstarten` uit
  `settings.json` leest.

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

**Help en changelog (sinds 4H en 9H):**

- Help: `docs/help/<taal>.md`, met fallback via `help_pad_voor_taal()`.
- Changelog: `docs/changelog/<taal>.md`, met dezelfde fallback via
  `changelog_pad_voor_taal()`.
- Beide resolvers leven in `app/helpers/help_paths.py`.
- Fallback-keten: taal → `nl_NL` → legacy (`docs/help.md` resp.
  `docs/changelog.md`).

**Qt-stijl:**

- `main.py` zet `app.setStyle("Fusion")` vóór `apply_dark_theme(app)`.
- `styles.py` bevat expliciete `QCheckBox::indicator` en
  `QRadioButton::indicator`.

**Buildstraat (fase 9A–9F):**

- `app/version.py` — centrale versie, momenteel `1.1.2`.
- `main.py` — `QT_QPA_FONTDIR` automatisch, `setApplicationVersion`,
  geeft `check_on_startup` door.
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

**Update-check-laag (fase 9H):**

- `app/helpers/updater.py` (v1.1.0) — pure, GUI-onafhankelijke
  update-check. Geen Qt, geen token.
  - `check_for_update(current_version)` → `UpdateInfo`
  - `fetch_version_txt()` — raw-URL + Contents API-fallback
  - `fetch_release_notes()` — GitHub Releases API
- `ToolHubWindow` v2.14.0 — opstartcheck via `QTimer.singleShot`,
  Help-menu-item "Controleren op updates…", drie-knoppenmelding
  (Downloaden / Wat is er nieuw? / Later), release-notes-dialoog.
- `app/config/settings.py` v1.6.0 — `algemeen.controleer_updates_bij_opstarten`
  (default `True`), backward-compatible.
- `app/gui/dialogs/settings_dialog.py` v1.4.0 — checkbox op tab Algemeen.
- Nieuwe i18n-keys: `menu.controleren_op_updates`, `update.*`,
  `dialog.sluiten`, `settings.algemeen.controleer_updates`,
  `settings.algemeen.controleer_updates_tooltip` (NL + EN).
- Changelog meertalig: `docs/changelog/nl_NL.md` +
  `docs/changelog/en_US.md`, via `changelog_pad_voor_taal()`.

**Referentie-architectuur (fase 10A + 10B):**

- `app/data/references/esr_references.json` — meerdere profielen per
  frequentie. Officiële ESR70-tabel op 100 kHz (`esr70_100khz`,
  `is_schatting: false`) plus geschatte profielen op 100 Hz, 1 kHz en
  10 kHz (`algemeen_100hz_geschat`, `algemeen_1khz_geschat`,
  `algemeen_10khz_geschat`, alle `is_schatting: true`).
- Schattingsfactoren t.o.v. 100 kHz: 100 Hz × 2,00, 1 kHz × 1,50,
  10 kHz × 1,15 (Nichicon-frequentiecoëfficiënten).
- `app/data/references/__init__.py` v2.0.0 — `zoek_referentie` accepteert
  `meetfrequentie_hz` en kiest het dichtstbijzijnde profiel met regels.
- `assessment_service.Beoordeling` heeft sinds 10B het veld
  `referentiefrequentie_hz: Optional[float]`, gevuld vanuit de
  gekozen `ReferentieContext`.
- `esr_test_screen.py` v1.12.0 roept `zoek_referentie` aan met
  `meetfrequentie_hz=freq_hz` en toont de werkelijke referentiefrequentie.

### 2.3 Belangrijke recente bugfixes (8D+, 9A–9H, 10A–10B)

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
- **Frequentie-mismatch 100 kHz vs 1/10 kHz** in de referentie-
  vergelijking: opgelost in 10A/10B met frequentie-specifieke profielen.
  De oude drempels `≤1,0 / ≤2,0 / ≤3,0` blijven zinvol omdat de
  factoren voor goede condensatoren nu 0,09–0,41 zijn (steekproef 72
  metingen).

### 2.4 Openstaande werkpunten

Volgens het stappenplan:

- **9G** — Bug/feature-rapportage naar GitHub. **Afgerond 2026-10-14.**
- **9H** — Update-check bij opstarten + via Help. **Afgerond en
  gepubliceerd als v1.1.1 op 2026-10-15.**
- **10A** — Referentie-architectuur met profielen. **Afgerond
  2026-10-15.**
- **10B** — Drempelvalidatie. **Afgerond 2026-10-15** (v1.1.2).
- **11** — Laatste UX/documentatie-afwerking (incl. light theme,
  async URL-fetch, cosmetische punten, visuele selectie in Analyse,
  checkbox-zichtbaarheid donker thema, i18n-menging in Diagnose/Result,
  **export respecteert selectie**, **betrouwbaarheidsregel herzien**,
  en de nieuwe cosmetische punten uit §2.24–§2.26 van `openvragen.md`).
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
24. **Een update-check mag de applicatie nooit laten crashen.**
25. **De changelog-resolver gebruikt dezelfde fallback-keten als Help.**
26. **Referenties zijn frequentie-specifiek; geen automatische
    frequentieconversie in de beoordelingsketen.**
27. **Geschatte referentieprofielen blijven expliciet als schatting
    gemarkeerd (`is_schatting: true`).**

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
  niet-getrackte `github_secret_local.py`.
- **Update-check-laag** (fase 9H) is puur en GUI-onafhankelijk:
  `app/helpers/updater.py` bevat de logica, `main_window.py` bevat
  de presentatie.
- **Referentie-laag** (fase 10A/10B) leeft in
  `app/data/references/` en is puur data + selectielogica; de
  assessment-service past ze enkel toe.

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
12. **Frequentie-specifieke referenties: kies het profiel dat het
    dichtst bij de meetfrequentie ligt. Geen 100 kHz-referentie op
    1 kHz-meting zonder markering.**
13. **Geschatte profielen dragen `is_schatting: true` en een
    `betrouwbaarheidsniveau: "laag"`.**
14. **Drempels `≤1,0 / ≤2,0 / ≤3,0` blijven ongewijzigd tot een
    grotere dataset beschikbaar is.**

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
| 9G | Bug/feature-rapportage naar GitHub | ✅ |
| 9H | Update-check bij opstarten + via Help | ✅ (v1.1.1) |
| 10A | Referentie-architectuur met profielen | ✅ |
| **10B** | **Drempelvalidatie** | **✅ (v1.1.2)** |
| **11** | **Laatste UX/documentatie-afwerking** | **Volgende** |
| 12 | AI-extractie uit fabrikantdocumenten | Gepland |
| 13 | Menselijke validatie van AI-output | Gepland |
| 14 | Goedgekeurde fabrikantdata koppelen aan assessment | Gepland |
| 15 | Tweede diagnosetool — Resistor | Gepland |

---

## 5. WAT IS NIEUW SINDS VERSIE 5.0.0

### 5.1 Fase 10B — Drempelvalidatie

**Nieuwe referentieprofielen:**

- `algemeen_100hz_geschat` — volledige ESR70-tabel × 2,00.
- `algemeen_1khz_geschat` — volledige ESR70-tabel × 1,50.
- `algemeen_10khz_geschat` — volledige ESR70-tabel × 1,15.

Alle drie `is_schatting: true`, `referentieniveau: 5`,
`betrouwbaarheidsniveau: "laag"`, bron-omschrijving vermeldt de
schattingsfactor.

**`assessment_service.py` v1.3.0 → v1.4.0:**

- `Beoordeling` krijgt `referentiefrequentie_hz: Optional[float]`.
- Geen wijziging aan drempels of logica.

**`esr_test_screen.py` v1.11.0 → v1.12.0:**

- `_on_assess` roept `zoek_referentie(..., meetfrequentie_hz=freq_hz)`.
- `_show_result` en `_build_result_html` tonen de werkelijke
  referentiefrequentie uit `resultaat.referentiefrequentie_hz`.

**`i18n/locales/*/esr.json`:**

- Nieuwe key `resultaat.referentiefrequentie` (NL: "Referentiefrequentie",
  EN: "Reference frequency").

**`tests/test_references.py` v1.0.0 → v1.1.0:**

- Tests aangepast: 1 kHz, 10 kHz en 100 Hz vallen niet meer terug op
  100 kHz.
- Nieuwe tests voor de schalingsfactoren (bijv. 470 µF / 25 V → 600 mΩ
  op 1 kHz, 460 mΩ op 10 kHz, 800 mΩ op 100 Hz).

**`tests/test_assessment.py` v1.3.0 → v1.4.0:**

- Nieuwe testklasse `TestReferentiefrequentieInResultaat` met drie
  tests voor het nieuwe veld.

**`scripts/herbereken_steekproef.py` (nieuw, v1.1.0):**

- Eenmalig analysedraaiboek dat de praktijkmetingen uit de historiek
  herberekent met de nieuwe profielen. Read-only. Zoekt automatisch
  het meest recente `historiek_detail_*.csv` in de projectroot, of
  accepteert een expliciet pad.

### 5.2 Resultaten van de steekproef (72 metingen)

Met de nieuwe referenties:

| Frequentie | Situatie | Oude factor (100 kHz) | Nieuwe factor |
|---|---|---|---|
| 1 kHz | 220 µF / 25 V | 1,05–1,07 | 0,15–0,20 |
| 1 kHz | 470 µF / 25 V | 1,47–1,52 | 0,25–0,31 |
| 1 kHz | 1000 µF / 16 V | 1,42–1,44 | 0,36–0,37 |
| 10 kHz | 330 µF / 35 V | 0,42–0,45 | 0,09–0,10 |
| 10 kHz | 470 µF / 25 V | 1,23–1,28 | 0,32–0,33 |
| 10 kHz | 1000 µF / 16 V | 1,15–1,23 | 0,38–0,41 |

**Conclusies:**

1. De drempels `≤1,0 / ≤2,0 / ≤3,0` blijven ongewijzigd. Goede
   condensatoren zitten nu structureel onder 0,5; er is ruimte voor
   verslechtering voordat "aandachtspunt" wordt bereikt.
2. De statussen in de steekproef veranderen weinig. Dat komt omdat de
   betrouwbaarheid en de capaciteitsafwijking nu de bepalende factoren
   zijn, niet meer de ESR-factor.
3. **Open UX-punt:** de regel "betrouwbaarheid laag → minstens
   aandachtspunt" verbergt goede resultaten wanneer alleen
   administratieve gegevens ontbreken (fabrikant/serie onbekend).
   Zie `docs/openvragen.md` §2.26.

### 5.3 Gewijzigde bestanden sinds 5.0.0

| Bestand | Versie / status |
|---|---|
| `app/data/references/esr_references.json` | gevulde geschatte profielen |
| `app/services/assessment_service.py` | v1.4.0 (was v1.3.0) |
| `app/gui/esr_test_screen.py` | v1.12.0 (was v1.11.0) |
| `i18n/locales/nl_NL/esr.json` | nieuwe key `referentiefrequentie` |
| `i18n/locales/en_US/esr.json` | nieuwe key `referentiefrequentie` |
| `tests/test_references.py` | v1.1.0 (was v1.0.0) |
| `tests/test_assessment.py` | v1.4.0 (was v1.3.0) |
| `scripts/herbereken_steekproef.py` | **nieuw** (v1.1.0) |
| `app/version.py` | 1.1.2 |
| `overdracht.md` | v5.1.0 (dit bestand) |
| `docs/phase10_analysis.md` | v1.1.0 |
| `docs/openvragen.md` | v2.4.0 |

### 5.4 Teststatus

**Baseline: 1297 passed.** Was 1286 in v5.0.0. De 11 nieuwe tests:

| Bestand | Aantal |
|---|---|
| `tests/test_references.py` (nieuwe tests voor schalingsfactoren en profielselectie) | 8 |
| `tests/test_assessment.py` (`TestReferentiefrequentieInResultaat`) | 3 |
| **Totaal** | **11** |

Volledige suite: **1297 passed in 53.05s**.

### 5.5 Bekende beperkingen (ongewijzigd t.o.v. 5.0.0, plus nieuwe)

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
- Pandas-pin `<3`, numpy als directe dependency.
- Defender-indicator op Intune-pc's vereist eenmalige `.cer`-upload.
- WDAC/AppLocker: bevestigd **niet actief** (2026-10-13).
- **GitHub-token per app.** Elk token heeft alleen toegang tot één
  repo (fine-grained). Eén token per app, niet delen.
- **Meldingen zijn publiek leesbaar** — de repo is publiek. Houd
  testtekst neutraal.
- **De drie-knoppenmelding is niet testbaar zonder nieuwe versie** —
  zie `openvragen.md` §2.24.
- **`fetch_release_notes()` blokkeert kort bij netwerk-timeout** —
  zie `openvragen.md` §2.24.
- **Export respecteert selectie niet** — zie `openvragen.md` §2.25.
- **Betrouwbaarheidsregel verbergt goede resultaten bij ontbrekende
  administratieve gegevens** — zie `openvragen.md` §2.26.

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
- **Drie-knoppenmelding forceren voor QA** (§2.24).
- **`fetch_release_notes()` async maken** (§2.24).
- **`docs/changelog.md` verwijderd — controleer externe links**
  (§2.24).
- **Export respecteert selectie niet** (§2.25).
- **Betrouwbaarheidsregel verbergt goede resultaten** (§2.26).

---

## 7. TESTSTATUS — BASELINE EN TESTSTRUCTUUR

**Datum:** 2026-10-15
**Baseline:** 1297 passed
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

### 7.7 Update-check handmatig testen (fase 9H)

De drie-knoppenmelding (**Downloaden** / **Wat is er nieuw?** / **Later**)
verschijnt alleen wanneer `is_newer` True is. In een normale
ontwikkelomgeving is dat nooit het geval. Om het toch te testen:

```powershell
# Tijdelijk de lokale versie verlagen (NIET vergeten terug te zetten)
python bump_version.py patch --dry-run    # bekijk wat er zou gebeuren
# Of pas app\version.py manueel aan naar een lagere versie, start de
# app, en zet daarna terug.
```

De pytest-dekking in `tests/test_main_window_update_menu.py` en
`tests/test_updater.py` dekt de logica zonder echt netwerk.

### 7.8 Steekproef herberekenen (fase 10B)

```powershell
python scripts/herbereken_steekproef.py
# of met een expliciet pad:
python scripts/herbereken_steekproef.py pad\naar\historiek_detail_*.csv
```

Het script zoekt automatisch het meest recente `historiek_detail_*.csv`
in de projectroot. Kopieer het CSV-bestand dus eerst vanuit Downloads
naar de projectroot, of geef een expliciet pad mee.

---

## 8. BESTANDEN DIE DE NIEUWE CHAT MOET OPVRAGEN

Voor een nieuwe sessie heeft de chat meestal nodig:

- `overdracht.md` (dit bestand) — primaire bron
- `docs/context.md` — architectuur en ontwerpprincipes
- `docs/openvragen.md` — levende lijst
- `docs/changelog/nl_NL.md` — versiegeschiedenis voor de gebruiker
- `PROJECT_STRUCTURE.md` — automatisch gegenereerde mappenstructuur

Bij een specifieke fase vraagt de chat om de bestanden die de fase raakt.

**Voor fase 11 (Laatste UX/documentatie-afwerking):**

Deze fase raakt veel schermen tegelijk. Vraag in elk geval op:

- `app/gui/history_screen.py`
- `app/gui/analysis_screen.py`
- `app/gui/esr_test_screen.py`
- `app/services/history_service.py`
- `app/services/analysis_service.py`
- `app/helpers/history_csv_export.py`
- `app/helpers/history_detail_export.py`
- `app/services/assessment_service.py`
- `app/gui/styles.py`
- `i18n/locales/nl_NL/*.json` en `i18n/locales/en_US/*.json`
- `docs/openvragen.md` (voor de actuele puntenlijst)

**Voor fase 12–15:** zie de betreffende specificaties in `docs/future_tools.md`.

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