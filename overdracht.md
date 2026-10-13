# OVERDRACHT — Electronics Diagnostic Tool Hub / ESR Tester

**Versie overdracht:** 4.1.0
**Datum:** 2026-10-13
**Auteur:** Bart Bossuyt
**Vorige versie:** 4.0.0 (2026-10-13)
**Doel:** volledig overdrachtsdocument voor een nieuwe ChatGPT-sessie of
nieuwe ontwikkelaar. Bevat projectstaat, architectuur, regels, changelog,
teststructuur en startprompt. Alles in één bestand.

**Huidige baseline:** 1150 passed
**Laatste afgeronde fase:** 9E — GitHub Release (eerste publicatie `v1.0.3`)
**Volgende fase:** 9F — Intune/Defender/CFA-testmatrix + `docs/packaging.md`

---

## INHOUD

1. Startprompt (lees dit eerst)
2. Context — projectstaat en architectuur
3. Kernregels — bindende afspraken
4. Stappenplan — chronologisch overzicht
5. Wat is nieuw sinds versie 4.0.0
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
- Baseline: **1150 passed**.
- Laatste afgeronde fase: **9E — GitHub Release** (eerste publicatie
  `v1.0.3` op 2026-10-13).
- Volgende fase: **9F — Intune/Defender/CFA-testmatrix +
  `docs/packaging.md`**.

**Werkafspraken die je strikt volgt:**

- Vraag altijd om de **volledige huidige inhoud** van een bestand
  voordat je het vervangt. Je hebt geen toegang tot de schijf van de
  gebruiker.
- **Uitzondering:** als een bestand in **deze sessie** al is geleverd of
  gezien, en er is geen reden om te twijfelen, mag je het hergebruiken
  zonder opnieuw op te vragen. Meld wel dat je dat doet.
- Lever altijd **volledige bestanden**, nooit secties met
  `# ... ongewijzigd ...` of een `"import": {...}`-fragment in een
  JSON-bestand. Dit is in een eerdere chat fout gelopen.
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
  QObject-hiërarchieën inspecteert. Zonder event loop blijven
  verwijderde QActions in half-opgeruimde toestand hangen en geeft
  `.text()` een `RuntimeError`.
- **De taalparameter van `ToolHubWindow` heeft voorrang op
  `settings.json`.** Sinds v2.11.3 respecteert de constructor de
  parameter `taal`; valt alleen terug op `settings.json` als de
  parameter leeg is.
- **Voor leesbare PDF-rapporten:** sinds fase 9A zet `main.py`
  automatisch `QT_QPA_FONTDIR=C:\Windows\Fonts` op Windows als de
  variabele nog niet gezet is. De handmatige stap is niet meer nodig,
  maar blijft geldig als je de variabele zelf wilt zetten.
- **Bij het leveren van `.md`-bestanden die zelf codeblokken bevatten:**
  gebruik **viervoudige backticks** (````markdown ... ````) zodat de
  driedubbele backticks binnenin het bestand het omhullende blok niet
  voortijdig sluiten. Zonder deze regel valt het systeem halverwege
  terug op gewone tekst.
- **De ArticleSearch-flow is de bewezen build-flow.** Wijk daar niet
  meer van af. Concreet: `build_installer.bat` genereert
  `dist\installer.iss` in de batch (geen vaste `.iss` in de root),
  roept `ISCC.exe` aan, en `build_and_publish.ps1` orkestreert de
  hele keten. Zie sectie 5 voor de details.
- Geen aannames over de volgende fase: vraag het na of verwijs naar
  sectie 4 van dit document.

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
| Huidige baseline | **1150 passed** |
| Laatste afgeronde fase | 9E — GitHub Release |
| Volgende fase | 9F — Intune/Defender/CFA-testmatrix |

### 2.2 Huidige applicatiearchitectuur

**Eén-venster-navigatie (ToolHubWindow):**

- `QStackedWidget` met pagina's: hub, diagnose, ESR, historiek,
  documentatie, **analyse** (sinds 7B).
- Contextueel X-gedrag: binnen een pagina terug naar de bovenliggende
  pagina; op de hub sluit de applicatie.
- Menu: Bestand, Diagnose (incl. Analyse), Instellingen (incl. Talen),
  Help.
- **Belangrijk (v2.11.3):** `ToolHubWindow.__init__(taal=None)`
  respecteert de parameter `taal`. Valt alleen terug op `settings.json`
  als de parameter leeg is. `main.py` roept zonder argument aan.

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
- Ruwe meetdata append-mostly; assessment en reference als snapshots.

**Analyse-laag (fase 7):**

- `app/helpers/analysis_series.py` — pure functies, geen Qt, geen
  database. Bouwt `TimeSeriesPoint`- en `ScatterPoint`-lijsten en
  aggregeert per dag/week/maand.
- `app/services/analysis_service.py` — read-only service bovenop
  `MeasurementHistoryService`. Leest in pagina's (default 500 per keer).
- `app/gui/analysis_screen.py` (v1.0.6) — QtCharts-pagina. Roept alleen
  de service aan. **NaN/Inf-verdediging** ingebouwd.
- Read-only bewijs: `tests/test_analysis_service.py::_ReadOnlyHistoryStub`.

**Rapportage-laag (fase 8):**

- `app/services/report_service.py` (v1.2.0) — read-only service. Bouwt
  `ReportBundle` met één of meerdere details. Methoden:
  `build_bundle(measurement_id)` (dunne wrapper),
  `build_bundle_for_measurements(ids)`,
  `build_bundle_from_filters(filters)`.
- `app/helpers/report_render.py` (v1.4.0) — pure HTML-renderer.
  Dispatcht per `tool_key`. Meerdere metingen in één rapport met
  `meting_kop`. Statuscodes worden vertaald via `_status_code_label`.
- `app/helpers/report_pdf.py` (v1.0.0) — Qt-specifiek. `QTextDocument`
  + `QPrinter` → PDF. A4-portret, 15 mm marges.
  **Vereist `QT_QPA_FONTDIR=C:\Windows\Fonts` op Windows.** Sinds 9A
  zet `main.py` deze variabele automatisch.
- `app/helpers/report_chart.py` (v1.0.3) — Qt-specifiek. `QChart` →
  base64-PNG voor `ESR_CAPACITOR`.
- `app/gui/dialogs/report_dialog.py` (v1.2.0) — modale dialoog met
  preview, grafiek-checkbox, opslaan-HTML, opslaan-PDF.
  Nieuwe parameter `grafiek_default` (sinds 8D).
- **i18n-module:** `report.json` in beide locales.
- **Nieuwe instellingen (sinds 8D):** `laatste_rapportmap` (in
  `Algemeen`), `auteur` (in `Rapportage`).

**Documentatie (read-only viewer + editor):**

- Service met 8 meertalige documenten in de ingebouwde catalogus.
- `catalog.json` met `schema_version=1` en `data_version`.
- Zoektaal met operatoren: `,` (AND), `|` (OR), `-` (exact),
  `!` (uitsluiten), `%` (wildcard).
- Bewerken-knop voor eigen imports (5D'.2c). Ingebouwde documenten
  blijven read-only.
- Status wijzigen-knop voor eigen imports, Toon gearchiveerde-checkbox,
  Status-kolom (5D'.2e).
- Checkbox- en radio-indicator zichtbaar in donker thema (5D'.2f).
- Doorzoekbare metadata van imports (5D'.1b).

**Documentatie-import (fase 5, 5D', 6):**

- Wizard voor **PDF-, Word-, Excel- en URL-import**.
- Twee cataloguslagen: ingebouwde
  `app/data/documentation/catalog.json` en gebruikerscatalogus
  `%LOCALAPPDATA%\ElectronicsDiagnosticToolHub\documentation\imported_catalog.json`.
- Statusmachine: `CONCEPT → ACTIEF → GEARCHIVEERD`, met `revoke` terug
  naar `CONCEPT`.

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

**QtCharts:**

- `PySide6.QtCharts` wordt gebruikt in `app/gui/analysis_screen.py` en
  `app/helpers/report_chart.py`. Geen aparte dependency.

**Buildstraat (fase 9A–9E):**

- `app/version.py` — centrale versie, momenteel `1.0.3`.
- `main.py` — `QT_QPA_FONTDIR` automatisch, `setApplicationVersion`.
- `bump_version.py` — verhoogt patch/minor/major in `app/version.py`.
- `ESR_Tester.spec` (v2.0.0) — PyInstaller-specificatie met `icon=`
  actief, `assets/icons/logo.ico`.
- `build_installer.bat` (v2.0.1) — volgt 1-op-1 de bewezen
  ArticleSearch-flow (`build_installer15.bat` v1.4.0):
  - genereert `dist\installer.iss` in de batch (geen vaste `.iss` in
    de root);
  - versie via `bump_version.py` → `app/version.py`;
  - PyInstaller → rename/robocopy → `dist\ESR_Tester_<versie>\`;
  - kopieert `assets` en `docs` via `xcopy`, `requirements.txt` en
    `settings.json` via `copy`;
  - schrijft `version.txt` met `> ... echo %NEW_VERSION%`;
  - signing van de app-EXE vóór Inno (blok `[5b]`);
  - `.iss` genereren via `>>`-regels (blok `[6b]`);
  - `ISCC.exe` compileren (blok `[7]`);
  - signing van de installer (blok `[7b]`);
  - `AS_BUMP_PART`, `AS_MAKE_INSTALLER`, `AS_DO_SIGN`,
    `AS_SIGN_THUMBPRINT` als env-vars.
- `build_and_publish.ps1` (v1.0.0) — orchestrator:
  - vraagt `bumpPart`, `makeInstaller`, `doSign`, `doPublish`;
  - signing-preflight: kiest het geldige certificaat met de verste
    `NotAfter` uit `Cert:\CurrentUser\My` + `Cert:\LocalMachine\My`
    (subject `CN=CGK Local Signing`);
  - blokkeert publiceren zonder signing;
  - schrijft `_build_wrapper.bat` met `AS_*`-vars en roept
    `build_installer.bat` aan;
  - roept `publish.ps1` aan als `doPublish=J`.
- `publish.ps1` (v1.0.0) — GitHub-release:
  - leest versie uit `app/version.py`;
  - **release-gate**: `Get-AuthenticodeSignature` op de installer, moet
    `Valid` zijn met een `SignerCertificate`;
  - maakt release via `gh release create` (tag `v<versie>`);
  - uploadt `dist\ESR_TesterSetup_<versie>.exe` via
    `gh release upload --clobber`;
  - schrijft `releases\latest\version.txt` (2 regels: versie + URL);
  - commit `app/version.py` + `version.txt` en pusht naar GitHub;
  - default `$Repo = "capacitor_esr_validator"`, `$Owner = "barremans"`.
- `Export-SigningCertificate.ps1` (v1.0.1) — exporteert het
  Authenticode-certificaat van één of meer `.exe`'s als `.cer` in
  `.\signing-certs\`. Dedupliceert op thumbprint, waarschuwt bij
  verlopen certificaat.
- **Certificaat:** subject `CN=CGK Local Signing`, actief thumbprint
  `BD1DC390D56E3392836FD6E39470D5F766346509`, geldig tot 2028-09-17.
  Twee oudere/verlopen certs staan nog in de store
  (`4DA652...`, `13B90D...`); de preflight slaat ze automatisch over
  (`NotAfter -gt now`).

### 2.3 Belangrijke recente bugfixes (8D+, 9A–9E)

- **`algemeen.ja` / `algemeen.nee` lekten in rapport-HTML** (v1.3.0 van
  `report_render.py`): keys bestonden niet; vervangen door
  `app.ja` / `app.nee`.
- **Enum-codes in rapport niet vertaald** (v1.4.0 van
  `report_render.py`): `capacitance_status`, `esr_status` en
  `consistency_status` werden als ruwe codes getoond
  (`binnen_tolerantie`). Nu vertaald via `_status_code_label` met
  dezelfde keys als de GUI.
- **Grafiek-checkbox in `ReportDialog` niet deterministisch**
  (v1.2.0 van `report_dialog.py`): startte met
  `laad_instellingen().grafiek_opnemen` en was daardoor afhankelijk van
  de globale `settings.json`. Vervangen door een expliciete
  `grafiek_default`-parameter, doorgegeven door `MainWindow`.
- **`laatste_rapportmap` en `auteur` bestonden nog niet** (v1.5.0 van
  `settings.py`): toegevoegd, met backward-compat tests.
- **`SettingsDialog` overschreef `laatste_exportmap` en
  `laatste_importmap`** (v1.3.0 van `settings_dialog.py`): bouwde een
  nieuwe `AlgemeneInstellingen` in plaats van `replace()`. Daardoor
  werden de automatisch bijgehouden mappen per ongeluk gewist bij een
  `Toepassen`-klik. Nu gefixt.
- **`QT_QPA_FONTDIR` probleem op Windows:** Qt kan in een PySide6-venv
  de systeemfonts niet vinden zonder deze variabele. Zonder de variabele
  worden PDF-rapporten gerenderd met **zwarte blokken** in plaats van
  tekst. Sinds 9A zet `main.py` deze variabele automatisch op Windows
  als hij nog niet bestaat en `C:\Windows\Fonts` aanwezig is.
- **Venstertitels van Help- en Wijzigingslog-vensters** gebruikten
  `dialog.help_titel` en `dialog.changelog_titel`, die niet bestaan.
  De juiste keys zijn `dialog.help_title` en `dialog.changelog_title`
  (v2.11.6 van `main_window.py`).
- **ESR-knop in Diagnose-pagina** toonde de ruwe key `tool.esr`.
  Toegevoegd aan beide `app.json`-bestanden (v1.9).
- **Pandas/numpy ABI-conflict** in de build: pandas 3.0.6 gaf
  `ModuleNotFoundError: No module named 'pandas._libs.pandas_parser'`.
  Opgelost door `numpy>=1.26,<3` en `pandas>=2.2,<3` in
  `requirements.txt`, plus numpy als directe dependency.
- **`: was unexpected at this time.`** in `build_installer.bat` blok
  `[6]`: `set /p` met vierkante haken en ronde haken in de prompttekst
  brak de cmd-parser. Vervangen door een simpele `if defined`-check
  (v2.0.1).
- **`PermissionError WinError 5` op `build\ESR_Tester\ESR_Tester.exe`**:
  PyInstaller kon het bestand niet overschrijven omdat een eerdere
  crash van de tussenproduct-EXE de handle vasthield. Oplossing:
  `Get-Process ESR_Tester | Stop-Process -Force` en `build\` verwijderen.
  **De EXE in `build\` is niet bedoeld om te draaien** — alleen
  `dist\...\ESR_Tester.exe` is de werkende applicatie.
- **`[rename] Fallback via robocopy...`-melding** in de batch: komt
  doordat de vorige `dist\<BUILD_FOLDER>` nog bestaat. Cosmetisch.
- **LF/CRLF-waarschuwing bij `git add releases/latest/version.txt`**:
  Git meldt "LF will be replaced by CRLF the next time Git touches it".
  Inhoudelijk geen probleem; de raw URL geeft exact de twee regels.
  Bewust nog niet aangepast; zie openvragen.

### 2.4 Openstaande werkpunten

Volgens het stappenplan:

- **9F** — Intune/Defender/CFA-testmatrix + `docs/packaging.md`.
  **Volgende fase.**
- **9G** — Icoon in `.spec` en `.iss` — **al gedaan in 9C+9D**; 9G
  kan vervallen of beperkt blijven tot het verifiëren van de
  installer-iconen op meerdere Windows-versies.
- **9H** — Update-check bij opstarten + via Help. De "latest"-pointer
  op `releases/latest/version.txt` is sinds 9E beschikbaar en kan
  direct gebruikt worden.
- **10** — Praktische ESR-validatie.
- **11** — Laatste UX/documentatie-afwerking (incl. light theme,
  async URL-fetch, cosmetische scrollbar in Word-samenvatting,
  refresh()-opsplitsing in AnalysisScreen, GUI-scope "selectie" en
  "filters" voor rapporten).
- **12** — AI-extractie uit fabrikantdocumenten.
- **13** — Menselijke validatie van AI-output.
- **14** — Goedgekeurde fabrikantdata koppelen aan assessment.
- **15** — Tweede diagnosetool — Resistor.

### 2.5 Werkafspraken voor een nieuwe sessie

- **Vraag altijd om de huidige bestandsinhoud** voordat je een bestaand
  bestand vervangt.
- **Uitzondering:** als je het bestand in deze sessie al hebt geleverd
  of gezien en er is geen tegenspraak, mag je het direct hergebruiken.
- **Lever altijd volledige bestanden**, nooit secties met
  `# ... ongewijzigd ...`.
- **Lever volledige JSON-bestanden**, nooit fragmenten.
- **Draai eerst gerichte tests, dan volledige `pytest -q`.**
- **Meld nieuwe i18n-keys expliciet**, met de waarde voor NL én EN.
- **Python-headers zijn cumulatief.**
- **Geen `qtbot` gebruiken in tests.** Er is geen `pytest-qt`.
- **Verwerk `deleteLater()` in GUI-tests** met
  `QApplication.processEvents()`.
- **De taalparameter van `ToolHubWindow` heeft voorrang op
  `settings.json`.**
- **Bij het leveren van `.md`-bestanden die zelf codeblokken bevatten:**
  gebruik viervoudige backticks.
- **De ArticleSearch-flow is de bewezen build-flow.** Wijk daar niet
  meer van af.
- **Geen aannames over de eerstvolgende fase** — vraag het na.

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
20. **Rapporten lezen bestaande data, ze wijzigen niets.** Ze gebruiken
    de opgeslagen snapshots; geen herberekening.
21. **Bij het leveren van `.md`-bestanden met codeblokken: viervoudige
    backticks.**
22. **De ArticleSearch-flow is de bewezen build-flow.** Geen eigen
    varianten meer.

### 3.2 Architectuur

- **Assessment-service** bevat beoordelingslogica — geen GUI, geen database.
- **Storage-service** kent structurele validatie — geen beoordelingslogica.
- **Documentatie-service** is read-only — geen import, geen AI,
  geen assessment.
- **Import-service** schrijft alleen in de gebruikerscatalogus — geen
  assessment, geen GUI, geen netwerk (behalve URL-fetch).
- **GUI** verzamelt invoer, roept services aan, toont resultaat.
- **Editor** (5D'.2c) wijzigt alleen metadata.
- **Status-editor** (5D'.2e) wijzigt alleen status.
- **Analyse-laag** (fase 7) leest de storage read-only.
- **Rapportage-laag** (fase 8) leest de storage en de analyse-laag
  read-only. `report_render` is puur; `report_pdf` en `report_chart`
  zijn Qt-specifiek; `report_dialog` is GUI.
- **Buildstraat** (fase 9) is gescheiden van de applicatiecode.
  `bump_version.py`, `ESR_Tester.spec`, `build_installer.bat`,
  `build_and_publish.ps1`, `publish.ps1` en
  `Export-SigningCertificate.ps1` staan in de root en worden niet
  meegebundeld in de EXE. De `.iss` wordt in de batch gegenereerd in
  `dist\` en is geen bronbestand. `publish.ps1` schrijft
  `releases\latest\version.txt` als stabiele "latest"-pointer voor de
  toekomstige update-check.

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

---

## 4. STAPPENPLAN — CHRONOLOGISCH OVERZICHT

| Fase | Onderwerp | Status |
|---|---|---|
| 0 | Structuur + regressiebaseline | ✅ |
| 1 | Tool Hub / één-venster-navigatie | ✅ |
| 2 | Donker thema + dialooggedrag | ✅ |
| 3 | Compact ESR-hoofdscherm | ✅ |
| 4 | Settings-architectuur | ✅ |
| 5 | Validatie + OL/out-of-range | ✅ |
| — | Storage/SQLite (schema v1, v2) | ✅ |
| — | Historiek (read-only, herhaal meting) | ✅ |
| — | Documentatiebasis (meertalig, 8 documenten) | ✅ |
| 3A | Contextuele documentatie vanuit ESR | ✅ |
| 3B | Slimme contextdocumentatie | ✅ |
| 4A | `tool_keys` (multi-tool metadata) | ✅ |
| 4B | Multi-contextvelden | ✅ |
| 4C | Productcatalogus gelabeld | ✅ |
| 4D | Zoektaal | ✅ |
| 4E | Help-integratie | ✅ |
| 4E.4 | Help-menu item "Documentatie zoeken…" | ✅ |
| 4F | Sneltoetsen in ESR, Historiek, Hoofdmenu | ✅ |
| 4F.1 | Esc op Diagnose-pagina | ✅ |
| 4F.2 | Esc op Hoofdmenu met bevestiging | ✅ |
| 4G | Changelog volledig bijwerken | ✅ |
| 4H | Help splitsen per taal | ✅ |
| 4I | `docs/search_syntax.md` | ✅ |
| 4I.1 | Observaties uit 4I afwerken | ✅ |
| 5A | Import-modellen + service | ✅ |
| 5B | PDF-extractie via `pypdf` | ✅ |
| 5C | Koppeling `pdf_extract` ↔ `ImportService` | ✅ |
| 5D | URL-fetch + metadata + snapshot | ✅ |
| 5E | Wizard-UI + i18n | ✅ |
| 5D'.1 | `documentation_service` leest tweede cataloguslaag | ✅ |
| 5E'.1 | Menu-vertaling fix | ✅ |
| 5E'.2 | Radio button-styling fix (Fusion) | ✅ |
| 5D'.2a | Bestaand-document-popup | ✅ |
| 5D'.3 | Wizard UX: laatste mappen + titel-fix | ✅ |
| 5D'.4 | Viewer fix: PDF extern openen | ✅ |
| 5D'.2b | Metadata-uitbreiding in wizard | ✅ |
| 5D'.2d | Wizard UX-verfijning (datum, uppercase) | ✅ |
| 5D'.2c | Metadata bewerken in de viewer | ✅ |
| 5D'.2e | Status wijzigen in de viewer | ✅ |
| 5D'.2f | Checkbox-indicator in donker thema | ✅ |
| 5D'.1b | Metadata van imports doorzoekbaar maken | ✅ |
| 6A | Datamodel + service + extractie + orkestratie (Word/Excel) | ✅ |
| 6B | Wizard-uitbreiding (Word/Excel) | ✅ |
| 6C | Fix `service.py` + succesmelding + i18n-fix | ✅ |
| 6F | Documentatie bijwerken (Word/Excel) | ✅ |
| 7A | Analyse-laag: reeksen, aggregatie, read-only service | ✅ |
| 7B | Analyse-pagina: QtCharts, filters, hub-knop, menu, i18n | ✅ |
| 7C | Documentatie bijwerken (changelog, openvragen, overdracht) | ✅ |
| 8A | Rapportdatamodel + service + pure HTML-renderer | ✅ |
| 8B.1 | Multitool-neutraliteit in service + renderer | ✅ |
| 8B.2 | PDF-export + optionele grafiek | ✅ |
| 8B.2a | Scatter-schaling vóór filteren + `apply_language` split | ✅ |
| 8B.2b | `applyNiceNumbers` weg + x-as-klem | ✅ |
| 8C | GUI: menu-item, knop in historiek, `ReportDialog` | ✅ |
| 8D | Settings-uitbreiding (auteur, rapportmap, grafiek_default) | ✅ |
| 8D+ | i18n-fix `app.ja`/`app.nee`, enum-vertaling in rapport, PDF-fonts | ✅ |
| 8E | Documentatie bijwerken (changelog 1.8, openvragen, overdracht) | ✅ |
| 9A | Versie, `QT_QPA_FONTDIR`, `setApplicationVersion`, icoonmap | ✅ |
| 9A.1 | Over-dialoog met versie + bugfix help/changelog-titels | ✅ |
| 9B.1 | `bump_version.py` | ✅ |
| 9B.2 | `ESR_Tester.spec` + `build_installer.bat` | ✅ |
| 9C | Inno Setup installer (`installer.iss` gegenereerd in batch) | ✅ |
| 9D | Signing (`signtool`, certificaatpreflight, verify) | ✅ |
| 9E | **GitHub Release (`publish.ps1`, `build_and_publish.ps1`)** | **✅** |
| **9F** | **Intune/Defender/CFA-testmatrix + `docs/packaging.md`** | **Volgende** |
| 9G | Icoon in `.spec` en `.iss` — **al gedaan in 9C+9D** | ✅ (kan vervallen) |
| 9H | Update-check bij opstarten + via Help | Gepland |
| 10 | Praktische ESR-validatie | Gepland |
| 11 | Laatste UX/documentatie-afwerking | Gepland |
| 12 | AI-extractie uit fabrikantdocumenten | Gepland |
| 13 | Menselijke validatie van AI-output | Gepland |
| 14 | Goedgekeurde fabrikantdata koppelen aan assessment | Gepland |
| 15 | Tweede diagnosetool — Resistor | Gepland |

---

## 5. WAT IS NIEUW SINDS VERSIE 4.0.0

### 5.1 Fase 9E — GitHub Release

- **Eerste publieke release.** Op **2026-10-13** is de GitHub-release
  `v1.0.3` aangemaakt in de repo `barremans/capacitor_esr_validator`.
  Dit is de eerste release van het project; er waren tot dan 0 tags.
- **Asset:** `dist\ESR_TesterSetup_1.0.3.exe` (≈63 MB),
  gesigned met `CN=CGK Local Signing`
  (`BD1DC390D56E3392836FD6E39470D5F766346509`, geldig tot 2028-09-17).
- **Download-URL:**
  `https://github.com/barremans/capacitor_esr_validator/releases/download/v1.0.3/ESR_TesterSetup_1.0.3.exe`
- **Stabiele "latest"-pointer:**
  `https://raw.githubusercontent.com/barremans/capacitor_esr_validator/main/releases/latest/version.txt`
  (twee regels: versie + download-URL). Deze URL is de basis voor de
  update-check in 9H.
- **`releases/latest/version.txt`** is nieuw in de repo en wordt door
  `publish.ps1` bij elke publicatie overschreven.
- **Release-gate bleef actief:** `publish.ps1` publiceert alleen als
  `Get-AuthenticodeSignature` op de installer `Valid` is met een
  `SignerCertificate`. Dat was ook zo.
- **Geen Python-code gewijzigd.** Baseline blijft 1150 passed.
- **Cosmetische waarschuwing:** Git meldde
  `LF will be replaced by CRLF the next time Git touches it` voor
  `releases/latest/version.txt`. Inhoudelijk geen probleem; staat in
  openvragen voor fase 11.

### 5.2 Bewezen eind-to-eind op 2026-10-13

Eerste volledig werkende publicatie in deze flow:

- Versie: `1.0.3`
- `dist\ESR_Tester_1.0.3\ESR_Tester.exe` — gesigned, geverifieerd
- `dist\ESR_TesterSetup_1.0.3.exe` — gesigned, geverifieerd
- Installer getest op gewone Windows-pc: geslaagd
- Icoon zichtbaar in wizard en snelkoppelingen
- **Release `v1.0.3` gepubliceerd op GitHub** (via `publish.ps1`)
- **`app/version.py` en `releases/latest/version.txt` gepusht** naar
  `origin/main` (commit `1614c9e`, "Release 1.0.3 - sync app/version.py
  and version.txt")

### 5.3 Bekende cosmetische punten

- **`Architecture identifier "x64" is deprecated`** tijdens ISCC.
  Oplossing: in `build_installer.bat` `ArchitecturesInstallIn64BitMode=x64compatible`
  i.p.v. `x64` schrijven. Niet blokkerend.
- **`[rename] Fallback via robocopy...`-melding** verschijnt omdat de
  vorige `dist\<BUILD_FOLDER>` nog bestaat. Cosmetisch.
- **`build_log.txt`** bevat alleen een starttijd, niet de volledige
  PyInstaller- of Inno-output. Cosmetisch.
- **LF/CRLF-waarschuwing** bij het committen van
  `releases/latest/version.txt`. Cosmetisch; inhoud klopt.

### 5.4 Gewijzigde bestanden sinds 4.0.0

| Bestand | Versie / status |
|---|---|
| `app/version.py` | 1.0.3 (gecommit via `publish.ps1`) |
| `releases/latest/version.txt` | **nieuw** — 2 regels (versie + URL) |
| Git-tag `v1.0.3` | **nieuw** op GitHub |
| GitHub-release `v1.0.3` | **nieuw** op GitHub (met asset) |

Geen wijzigingen aan Python-code. Geen wijzigingen aan de buildstraat.

### 5.5 Teststatus

**Baseline: 1150 passed** (ongewijzigd t.o.v. 4.0.0). De publicatie is
geen Python-code; er zijn geen nieuwe tests toegevoegd. `pytest -q` na
de publicatie: **1150 passed in 39.30s**.

### 5.6 Bekende beperkingen

- **Geen OCR** voor gescande PDF's.
- **`.doc` en `.xls` worden geweigerd.**
- **Geen async URL-fetch.** Blokkeert de GUI tot 10s.
- **Datum-parsing bij bewerken** accepteert alleen ISO-formaat.
- **Geen bulk-edit** van meerdere imports.
- **Geen bulk-statuswijziging** van meerdere imports.
- **Geen reden bij archiveren.**
- **Cosmetische scrollbar** in de Word-samenvatting.
- **Analyse-pagina: geen zoom/pan, geen PNG/PDF-export.**
- **Analyse-pagina: vaste as-schaling** (µF, mΩ).
- **Rapportage: alleen "één meting" in de GUI.** De service
  (`build_bundle_for_measurements`, `build_bundle_from_filters`)
  ondersteunt meerdere metingen, maar er is nog geen GUI voor de
  scopes "selectie" en "filters".
- **Geen Intune/Defender-testmatrix** — volgt in 9F.
- **Geen update-check** — volgt in 9H. De "latest"-pointer is sinds
  9E beschikbaar.
- **Pandas-pin `<3`** — bewust conservatief vanwege ABI-conflict.
- **Numpy als directe dependency** — bewust expliciet voor PyInstaller.
- **Defender-indicator op Intune-pc's** — vereist eenmalige
  `.cer`-upload in `security.microsoft.com` (zie `signingContext.md`).
  Op gewone Windows-pc's is er geen Defender-indicator; daar blijft
  SmartScreen actief. Zie ook `signingContext.md` §2 en §8.
- **WDAC/AppLocker** — als dat actief is op de doel-pc's, is de
  Defender-indicator niet voldoende; dan is uitrol van het certificaat
  naar `Trusted Publishers` of een publiek vertrouwd certificaat nodig.
  Open vraag bij IT; relevant voor 9F.

---

## 6. OPENSTAANDE VRAGEN VOOR DE NIEUWE CHAT

### 6.1 Overige openstaande punten

- **`Architecture identifier "x64" is deprecated`** — oplossen door
  `x64compatible` in de batch te schrijven.
- **LF/CRLF-waarschuwing** voor `releases/latest/version.txt` —
  oplossen via `.gitattributes`-regel `releases/latest/version.txt text eol=lf`.
- **Reden opgeven bij archiveren.**
- **Filter voor alleen gearchiveerde documenten.**
- **Bulk-edit en bulk-statuswijziging.**
- **OCR voor gescande PDF's.**
- **Async URL-fetch.**
- **Light theme.**
- **AI-tekstextractie uit docx/xlsx.**
- **Cosmetische scrollbar in Word-samenvatting.**
- **Analyse-pagina:** automatische as-schaling,
  `QDateTimeAxis`-tickformaat, zoom/pan.
- **Rapportage:** GUI voor scope "selectie" en "filters".
- **Rapportage:** menu-item disabled maken als er geen selectie is.
- **Pandas-pin `<3`:** wanneer losser maken?
- **Numpy als directe dependency:** blijft dat zo?
- **`[rename] Fallback via robocopy...`-melding:** opruimen in 9F?
- **`build_log.txt` blijft leeg:** volledige output loggen?
- **Relatief `icon_path` in `main_window.py`:** verfijnen in 9F?
- **Twee verlopen certificaten in `CurrentUser\My`** — storen de
  build niet, maar kunnen opgeruimd worden:
  `4DA652...`, `13B90D...`.
- **`ESR_Tester.spec` staat in `.gitignore`** (`*.spec`). Voor fase 9F
  of 11 nagaan of dat gewenst blijft: op een andere machine kan de
  `.spec` niet gecloned worden zonder manuele ingreep. In de
  ArticleSearch-flow werd de `.spec` wél meegecommit.

---

## 7. TESTSTATUS — BASELINE EN TESTSTRUCTUUR

**Datum:** 2026-10-13
**Baseline:** 1150 passed
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

### 7.3 Voor leesbare PDF's

Sinds fase 9A zet `main.py` de variabele automatisch. De handmatige
stap blijft geldig als je de variabele zelf wilt zetten:

```powershell
$env:QT_QPA_FONTDIR = "C:\Windows\Fonts"
python main.py
```

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

Verifieer:

```powershell
$v = (Select-String -Path "app\version.py" -Pattern '__version__\s*=\s*"(\d+\.\d+\.\d+)"').Matches.Groups[1].Value
& "C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe" verify /pa /v "dist\ESR_Tester_$v\ESR_Tester.exe"
& "C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe" verify /pa /v "dist\ESR_TesterSetup_$v.exe"
```

### 7.5 Publiceren (fase 9E)

```powershell
# Publiceert de installer uit dist\ naar GitHub.
# Leest de versie uit app/version.py, doet de release-gate,
# maakt de release, uploadt de asset, schrijft version.txt en pusht.
.\publish.ps1
```

Resultaat:

- GitHub-release `v<versie>` met asset `ESR_TesterSetup_<versie>.exe`
- `releases/latest/version.txt` met 2 regels (versie + URL)
- `app/version.py` en `releases/latest/version.txt` gepusht

---

## 8. BESTANDEN DIE DE NIEUWE CHAT MOET OPVRAGEN

Voor een nieuwe sessie heeft de chat meestal nodig:

- `overdracht.md` (dit bestand) — primaire bron
- `docs/context.md` — architectuur en ontwerpprincipes
- `docs/openvragen.md` — levende lijst
- `docs/changelog.md` — versiegeschiedenis voor de gebruiker
- `PROJECT_STRUCTURE.md` — automatisch gegenereerde mappenstructuur

Bij een specifieke fase vraagt de chat om de bestanden die de fase raakt.

Voor fase 9F (Intune/Defender/CFA-testmatrix + `docs/packaging.md`):

- `signingContext.md` — SmartScreen/Defender-uitzondering
- `05-signing-build-context.md` — signing-flow
- `Export-SigningCertificate.ps1` — huidige versie (v1.0.1)
- `docs/openvragen.md` — §2.18 met de Defender/WDAC-vraag
- `publish.ps1` — huidige versie (v1.0.0) — bevat de release-gate
- `build_and_publish.ps1` — huidige versie (v1.0.0)
- `build_installer.bat` — huidige versie (v2.0.1)
- `.gitattributes` — om de LF/CRLF-afspraak te kunnen toevoegen

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
- Python-headers zijn cumulatief. Nieuwe versies krijgen een nieuwe
  regel bovenaan de `Wijzigingen:`-lijst; oudere regels blijven staan.
- **Bij het leveren van `.md`-bestanden die zelf codeblokken bevatten:
  gebruik viervoudige backticks.**
- **De ArticleSearch-flow is de bewezen build-flow.** Wijk daar niet
  meer van af.
- Geen aannames over de eerstvolgende fase — vraag het na.