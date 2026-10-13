# OVERDRACHT — Electronics Diagnostic Tool Hub / ESR Tester

**Versie overdracht:** 3.8.0
**Datum:** 2026-10-13
**Auteur:** Bart Bossuyt
**Vorige versie:** 3.7.0 (2026-10-12)
**Doel:** volledig overdrachtsdocument voor een nieuwe ChatGPT-sessie of
nieuwe ontwikkelaar. Bevat projectstaat, architectuur, regels, changelog,
teststructuur en startprompt. Alles in één bestand.

**Huidige baseline:** 1150 passed
**Laatste afgeronde fase:** 9B.2 — PyInstaller-buildstraat
**Volgende fase:** 9C — Inno Setup installer

---

## INHOUD

1. Startprompt (lees dit eerst)
2. Context — projectstaat en architectuur
3. Kernregels — bindende afspraken
4. Stappenplan — chronologisch overzicht
5. Wat is nieuw sinds versie 3.7.0
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
- Laatste afgeronde fase: **9B.2 — PyInstaller-buildstraat**.
- Volgende fase: **9C — Inno Setup installer**.

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
| Huidige baseline | **1150 passed** |
| Laatste afgeronde fase | 9B.2 — PyInstaller-buildstraat |
| Volgende fase | 9C — Inno Setup installer |

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

**Buildstraat (fase 9A en 9B):**

- `app/version.py` — centrale versie, momenteel `1.0.0`.
- `main.py` — `QT_QPA_FONTDIR` automatisch, `setApplicationVersion`.
- `bump_version.py` — verhoogt patch/minor/major in `app/version.py`.
- `ESR_Tester.spec` — PyInstaller-specificatie.
- `build_installer.bat` — bouwt de EXE, kopieert `settings.json`,
  schrijft `version.txt`.
- `assets/icons/` — `logo.ico` (nog niet in `.spec`), `ESR.png`
  (gebruikt in GUI), `README.md`.
- **Icoon in `.spec` en `.iss`:** uitgesteld naar fase 9G.

### 2.3 Belangrijke recente bugfixes (8D+ en 9A)

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

### 2.4 Openstaande werkpunten

Volgens het stappenplan:

- **9C** — Inno Setup installer (`installer.iss`). **Volgende fase.**
- **9D** — Signing (`signtool`, certificaatpreflight, verify).
- **9E** — `publish.ps1` + `build_and_publish.ps1` + GitHub Release.
- **9F** — Intune/Defender/CFA-testmatrix + `docs/packaging.md`.
- **9G** — Icoon toevoegen aan `.spec` en `.iss`.
- **9H** — Update-check bij opstarten + via Help.
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
  `bump_version.py`, `ESR_Tester.spec` en `build_installer.bat` staan
  in de root en worden niet meegebundeld in de EXE.

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
| **9C** | **Inno Setup installer (`installer.iss`)** | **Volgende** |
| 9D | Signing (`signtool`, certificaatpreflight, verify) | Gepland |
| 9E | `publish.ps1` + `build_and_publish.ps1` + GitHub Release | Gepland |
| 9F | Intune/Defender/CFA-testmatrix + `docs/packaging.md` | Gepland |
| 9G | Icoon toevoegen aan `.spec` en `.iss` | Gepland |
| 9H | Update-check bij opstarten + via Help | Gepland |
| 10 | Praktische ESR-validatie | Gepland |
| 11 | Laatste UX/documentatie-afwerking | Gepland |
| 12 | AI-extractie uit fabrikantdocumenten | Gepland |
| 13 | Menselijke validatie van AI-output | Gepland |
| 14 | Goedgekeurde fabrikantdata koppelen aan assessment | Gepland |
| 15 | Tweede diagnosetool — Resistor | Gepland |

---

## 5. WAT IS NIEUW SINDS VERSIE 3.7.0

### 5.1 Fase 9A — versie, `QT_QPA_FONTDIR`, icoonmap

- **`app/version.py`** op `1.0.0`. Eén centrale bron voor de versie.
- **`main.py`** zet `QT_QPA_FONTDIR` automatisch op Windows als de
  variabele nog niet bestaat en `C:\Windows\Fonts` aanwezig is.
- **`main.py`** roept `app.setApplicationVersion(__version__)` aan.
- **`assets/icons/`** aangemaakt met `logo.ico`, `ESR.png`, `README.md`.
- **i18n:** `dialog.over_tekst` uitgebreid met `{versie}`-placeholder.
- **Nieuwe test:** `tests/test_version.py` (5 tests).
- **Bugfix:** `dialog.help_titel` en `dialog.changelog_titel` bestonden
  niet; vervangen door `dialog.help_title` en `dialog.changelog_title`.

### 5.2 Fase 9A.1 — Over-dialoog met versie

- **`main_window.py`** vult `{versie}` in via `app.version.__version__`.
- De Over-dialoog toont nu **"Versie: 1.0.0"**.

### 5.3 Fase 9B.1 — `bump_version.py`

- **`bump_version.py`** leest `app/version.py`, verhoogt patch/minor/major,
  schrijft terug.
- Niet-interactief: `python bump_version.py patch`.
- Returncodes: 0 bij succes, 1 bij fout.

### 5.4 Fase 9B.2 — PyInstaller-buildstraat

- **`ESR_Tester.spec`** — PyInstaller-specificatie zonder `icon=`
  (icoon volgt in 9G).
- **`build_installer.bat`** — niet-interactieve build via
  omgevingsvariabelen `AS_BUMP_PART`, `AS_MAKE_INSTALLER`, `AS_DO_SIGN`.
- Output in `dist\ESR_Tester_<versie>\`.
- `settings.json` en `version.txt` worden meegekopieerd.
- **Eerste succesvolle build** met PyInstaller 6.11.1.
- **Nieuwe i18n-key:** `tool.esr` (NL "ESR-test", EN "ESR test").
- **Bugfix:** ESR-knop toonde de ruwe key `tool.esr`.
- **`requirements.txt`:** `numpy>=1.26,<3` toegevoegd als directe
  dependency; `pandas>=2.2,<3` gepind.

### 5.5 Gewijzigde bestanden sinds 3.7.0

| Bestand | Versie |
|---|---|
| `app/version.py` | 1.0.0 |
| `main.py` | 1.3.0 |
| `app/gui/main_window.py` | 2.11.6 |
| `i18n/locales/nl_NL/app.json` | 1.2.0 |
| `i18n/locales/en_US/app.json` | 1.2.0 |
| `requirements.txt` | — |
| `assets/icons/README.md` | nieuw |
| `ESR_Tester.spec` | 1.0.0 |
| `build_installer.bat` | 1.0.1 |
| `bump_version.py` | 1.0.0 |
| `tests/test_version.py` | 1.0.0 |
| `tests/test_i18n_app_translations.py` | 1.4.0 |

### 5.6 Teststatus

**Baseline: 1150 passed.** Dat is +6 ten opzichte van v3.7.0 (1144).

Verdeling:

- 9A: 5 nieuwe tests in `test_version.py`.
- 9A: 1 nieuwe test in `test_i18n_app_translations.py`.
- 9B.1 en 9B.2: geen nieuwe tests.

### 5.7 Bekende beperkingen

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
- **Geen Inno Setup installer** — volgt in 9C.
- **Geen signing** — volgt in 9D.
- **Geen icoon in `.spec` en `.iss`** — volgt in 9G.
- **Geen update-check** — volgt in 9H.
- **Pandas-pin `<3`** — bewust conservatief vanwege ABI-conflict.
- **Numpy als directe dependency** — bewust expliciet voor PyInstaller.

---

## 6. OPENSTAANDE VRAGEN VOOR DE NIEUWE CHAT

### 6.1 Overige openstaande punten

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
.\build_installer.bat
.\dist\ESR_Tester_1.0.0\ESR_Tester.exe
```

De EXE moet opstarten, de GUI moet werken, en de Over-dialoog moet
"Versie: 1.0.0" tonen.

---

## 8. BESTANDEN DIE DE NIEUWE CHAT MOET OPVRAGEN

Voor een nieuwe sessie heeft de chat meestal nodig:

- `overdracht.md` (dit bestand) — primaire bron
- `docs/context.md` — architectuur en ontwerpprincipes
- `docs/openvragen.md` — levende lijst
- `docs/changelog.md` — versiegeschiedenis voor de gebruiker
- `PROJECT_STRUCTURE.md` — automatisch gegenereerde mappenstructuur

Bij een specifieke fase vraagt de chat om de bestanden die de fase raakt.

Voor fase 9C (Inno Setup installer):

- `build_installer.bat` — huidige versie (om de Inno-stap toe te voegen)
- `installer.iss` — als die al bestaat (nog niet)
- `assets/icons/logo.ico` — voor `SetupIconFile` (in 9G)
- De ArticleSearch `installer.iss` als referentie
- De ArticleSearch `build_installer15.bat` als referentie

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
- Geen aannames over de eerstvolgende fase — vraag het na.