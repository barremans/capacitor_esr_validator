# OVERDRACHT — Electronics Diagnostic Tool Hub / ESR Tester

**Versie overdracht:** 3.6.0
**Datum:** 2026-10-09
**Auteur:** Bart Bossuyt
**Vorige versie:** 3.5.0 (2026-10-09)
**Doel:** volledig overdrachtsdocument voor een nieuwe ChatGPT-sessie of
nieuwe ontwikkelaar. Bevat projectstaat, architectuur, regels, changelog,
teststructuur en startprompt. Alles in één bestand.

**Huidige baseline:** 1037 passed
**Laatste afgeronde fase:** 7C — Grafieken en trends (documentatie)
**Volgende fase:** 8 — Rapportage

---

## INHOUD

1. Startprompt (lees dit eerst)
2. Context — projectstaat en architectuur
3. Kernregels — bindende afspraken
4. Stappenplan — chronologisch overzicht
5. Wat is nieuw sinds versie 3.5.0
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
- Baseline: **1037 passed**.
- Laatste afgeronde fase: **7C — Grafieken en trends (documentatie)**.
- Volgende fase: **8 — Rapportage**.

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
| Huidige baseline | **1037 passed** |
| Laatste afgeronde fase | 7C — Grafieken en trends (documentatie) |
| Volgende fase | 8 — Rapportage |

### 2.2 Huidige applicatiearchitectuur

**Eén-venster-navigatie (ToolHubWindow):**

- `QStackedWidget` met pagina's: hub, diagnose, ESR, historiek,
  documentatie, **analyse** (nieuw in 7B).
- Contextueel X-gedrag: binnen een pagina terug naar de bovenliggende pagina;
  op de hub sluit de applicatie.
- Menu: Bestand, Diagnose (incl. Analyse), Instellingen (incl. Talen), Help.

**Sneltoetsen:**

- **Globaal:** `Ctrl+Q`, `Ctrl+E`, `Ctrl+I`, `Ctrl+A`, `F1`.
- **ESR-scherm:** `Esc`, `Ctrl+Return`, `Ctrl+S`, `Ctrl+W`, `Ctrl+I`.
- **Historiek:** `Esc`, `Ctrl+R`, `Ctrl+F`, `Ctrl+D`, `Ctrl+H`.
- **Hoofdmenu:** `Ctrl+D`, `Ctrl+H`, `Ctrl+K`, `Ctrl+A`, `Esc`.
- **Diagnose:** `Esc`.
- **Documentatie:** `Esc`, `Return`, `Ctrl+F`, `Ctrl+L`, `Ctrl+O`, `F1`.
- **Analyse:** `Esc`, `Ctrl+R`, `Ctrl+F`.
- **Import-wizard:** `Ctrl+D` (datum op vandaag).
- **Metadata-editor:** `Ctrl+D` (datum op vandaag).

Alle lokale sneltoetsen gebruiken `WidgetWithChildrenShortcut`.

**Storage:**

- SQLite op `%LOCALAPPDATA%\ElectronicsDiagnosticToolHub\measurements.sqlite3`.
- Schema v1: 7 tabellen. Schema v2: `measurements.tool_key`.
- Migratieframework transactioneel en sequentieel.
- Ruwe meetdata append-mostly; assessment en reference als snapshots.

**Analyse-laag (nieuw in fase 7):**

- `app/helpers/analysis_series.py` — pure functies, geen Qt, geen
  database. Bouwt `TimeSeriesPoint`- en `ScatterPoint`-lijsten en
  aggregeert per dag/week/maand.
- `app/services/analysis_service.py` — read-only service bovenop
  `MeasurementHistoryService`. Leest in pagina's (default 500 per keer).
  Schrijft nooit.
- `app/gui/analysis_screen.py` — QtCharts-pagina. Roept alleen de
  service aan; geen data-logica in de GUI.
- Read-only bewijs: `tests/test_analysis_service.py::_ReadOnlyHistoryStub`
  laat elke schrijfmethode-aanroep falen.
- Aggregatie gebeurt in `analysis_series.aggregate_time_series`, niet
  in de GUI. De GUI kiest alleen de aggregatie-dropdown.

**Documentatie (read-only viewer + editor):**

- Service met 8 meertalige documenten in de ingebouwde catalogus.
- `catalog.json` met `schema_version=1` en `data_version`.
- Multi-context metadata: `tool_keys`, `component_types`, `test_keys`,
  `measurement_methods`, `instrument_keys`, `topics`.
- Zoektaal met operatoren: `,` (AND), `|` (OR), `-` (exact),
  `!` (uitsluiten), `%` (wildcard).
- Help-dialoog via knop `?`, `F1`, en via Help-menu
  ("Documentatie zoeken…").
- Ontwikkelaarsreferentie: `docs/search_syntax.md`.
- Bewerken-knop voor eigen imports (5D'.2c). Ingebouwde documenten
  blijven read-only.
- Status wijzigen-knop voor eigen imports, Toon gearchiveerde-checkbox,
  Status-kolom (5D'.2e).
- Checkbox- en radio-indicator zichtbaar in donker thema (5D'.2f).
- Doorzoekbare metadata van imports (5D'.1b).

**Documentatie-import (fase 5, 5D', 6):**

- Wizard voor **PDF-, Word-, Excel- en URL-import** via
  `Bestand → Document importeren…` (`Ctrl+I`) en via knop "Importeren"
  op het Documentatie-scherm.
- Twee cataloguslagen: ingebouwde `app/data/documentation/catalog.json`
  en gebruikerscatalogus
  `%LOCALAPPDATA%\ElectronicsDiagnosticToolHub\documentation\imported_catalog.json`.
- Geïmporteerde PDF's/DOCX/XLSX in
  `...\documentation\sources\<source_id>.pdf|.docx|.xlsx`.
- HTML-snapshots van URL-imports in
  `...\documentation\snapshots\<source_id>.html`.
- Statusmachine: `CONCEPT → ACTIEF → GEARCHIVEERD`, met `revoke` terug
  naar `CONCEPT`.
- **Metadata in de wizard:** categorie (verplicht, default DATASHEET),
  fabrikant, serie, partnummer, documentversie (uppercase),
  documentdatum (`QDateEdit` + "Datum onbekend"-checkbox + `Ctrl+D`),
  notities.
- **Import is gescheiden van viewer en van assessment.**
- **Doorzoekbare metadata (5D'.1b):** titel, categorie, fabrikant,
  serie, partnummer, documentversie, documentdatum, notities en
  bron-URL zijn doorzoekbaar via `search_text`. `document_id`,
  `source_path` en `title_key` zijn dat niet.
- **Bevestiging na import (6C):** `QMessageBox.information` met
  "Import geslaagd — Het document '...' is geïmporteerd als Concept."
  Alleen bij `changed=True`.
- **Geweigerde formaten (6C):** `.doc` en `.xls` met duidelijke
  melding.

**Metadata-editor (fase 5D'.2c):**

- `EditMetadataDialog` in `app/gui/dialogs/edit_metadata_dialog.py`.
- Alleen voor `is_user_import=True` (eigen imports).
- Wijzigt alleen metadata; bronbestand, status en importdatum blijven
  ongewijzigd.
- Roept `ImportService.update_metadata` aan (sentinel-aanpak).
- Gedeelde helpers met de wizard in
  `app/gui/dialogs/_metadata_form_helpers.py`.

**Status-editor (fase 5D'.2e):**

- `ChangeStatusDialog` in `app/gui/dialogs/change_status_dialog.py`.
- Alleen voor `is_user_import=True`.
- Toont de toegelaten overgangen (afgeleid van `_ALLOWED_TRANSITIONS`).
- Bevestigingsvraag bij archiveren en bij terug naar Concept.
- Roept `ImportService.set_status` aan.
- Emit `status_changed(source_id)` bij succes.

**Word- en Excel-import (fase 6):**

- `app/documentation/docx_extract.py` — metadata, tekst, SHA-256,
  kopiëren, rollback-helpers.
- `app/documentation/docx_import.py` — orkestratie (hash → metadata →
  registratie → kopie, + 3 duplicate-acties).
- `app/documentation/xlsx_extract.py` — metadata, celinhoud, SHA-256,
  kopiëren, rollback-helpers.
- `app/documentation/xlsx_import.py` — orkestratie.
- `ImportSourceType.DOCX` en `.XLSX`.
- `ImportService.register_docx` en `register_xlsx`.
- `.doc` en `.xls` worden geweigerd met duidelijke melding.
- `python-docx>=1.1` toegevoegd aan `requirements.txt`.

**Help per taal:**

- `docs/help/<taal>.md` (bv. `nl_NL.md`, `en_US.md`).
- Fallback-keten: `<taal>.md` → `nl_NL.md` → `help.md` →
  `FileNotFoundError`.
- Resolutie in `app/helpers/help_paths.py`.

**i18n:**

- Alle GUI-teksten via `app/helpers/i18n.py` en JSON-bestanden onder
  `i18n/locales/<taal>/`.
- Modules: `app.json`, `esr.json`, `history.json`, `documentation.json`,
  `settings.json`, `language.json`, `analysis.json` (nieuw in 7B).
- Ontbrekende EN-key valt terug op NL.
- Live taalwissel behoudt state.

**Qt-stijl:**

- `main.py` zet `app.setStyle("Fusion")` vóór `apply_dark_theme(app)`.
- Zonder Fusion negeert Qt op Windows 10/11 CSS op
  `QRadioButton::indicator` en `QCheckBox::indicator`.
- Sinds 5D'.2f heeft `styles.py` expliciete `QCheckBox::indicator` en
  `QRadioButton::indicator`-regels.

**QtCharts:**

- `PySide6.QtCharts` wordt gebruikt in `app/gui/analysis_screen.py`.
  Geen aparte dependency.
- `matplotlib` en `pyqtgraph` zijn **niet** toegevoegd aan
  `requirements.txt`.

### 2.3 Belangrijke recente bugfixes

- **Menu-lek in `_apply_language()`** (v2.7.3): opgelost met
  `setParent(None)` + `deleteLater()`.
- **Access violation in volledige pytest-suite** (v5A): statische
  broncheck in plaats van `sys.modules`-manipulatie.
- **`user_catalog_path` default** (v1.8.1 van `service.py`): expliciete
  `catalog_path` schakelt nu de gebruikerscatalogus uit tenzij
  `user_catalog_path` expliciet is meegegeven.
- **Overschrijven koos de eerste match** (v1.1.1 van
  `import_service.py`): opgelost met `_beste_match`.
- **Titelveld in wizard werd niet bijgewerkt** bij tweede PDF-keuze:
  opgelost met `_titel_automatisch`.
- **Viewer crashte op PDF's** (v2.1.0 van `documentation_screen.py`):
  opgelost met dispatch op `source_kind`.
- **URL-viewer opende de snapshot** in plaats van de live site:
  opgelost in v2.1.1.
- **`service.py._import_source_to_document` gaf metadata niet door**
  (v1.8.2): opgelost in 5D'.2c.
- **`test_edit_selected_document_opent_editor`** (v1.10.1): fake
  editor is nu een `QObject`-subclass met klasse-niveau `Signal(str)`
  en een eigen `exec()`.
- **`test_import_wizard_dialog.py`** importeerde `_naar_uppercase`
  uit de wizard (v1.5.0 van de wizard): vervangen door
  `naar_uppercase` uit `_metadata_form_helpers`.
- **PermissionError [WinError 5] op Windows** (v1.3.1 van
  `import_service.py`): retry-lus in `_atomic_replace`.
- **`get_document` vond gearchiveerde imports niet** (v1.9.1 van
  `service.py`): zoekt nu altijd in beide cataloguslagen.
- **Checkbox-indicator onzichtbaar in donker thema** (v1.3.0 van
  `styles.py`): expliciete `QCheckBox::indicator`-styling.
- **Flaky beste-match-tests** (v1.2.1 van
  `test_documentation_import_service.py`): `time.sleep(0.01)` tussen
  twee registraties zodat `imported_at` gegarandeerd verschilt.
- **`DocumentationService` herkende `docx`/`xlsx` niet** (v1.10.0 van
  `service.py`): toegevoegd in fase 6C.
- **Testhelpers `_maak_xlsx` in xlsx-tests**: vervangen door
  `wb.active["A1"] = ...`.
- **`extract_xlsx_text` sloeg lege bladen over**: nu krijgt elk blad
  een header `# <bladnaam>`.
- **Hangende wizard-tests na 6C**: patch op `_toon_succesmelding`.
- **`aggregate_time_series` valideerde de aggregatie niet** bij een
  lege reeks (v1.0.1 van `analysis_series.py`): validatie nu vóór de
  lege-input-return.
- **`AnalysisScreen.__init__` zette de labels niet** (v1.0.1 van
  `analysis_screen.py`): `_apply_static_labels()` in `__init__`.
- **`AnalysisScreen.apply_language()` deed een refresh in `__init__`**
  (v1.0.2): gesplitst in `_apply_static_labels()` (init) en
  `apply_language()` (taalwissel + refresh).

### 2.4 Openstaande werkpunten

Volgens het stappenplan:

- **8** — Rapportage en export. **Volgende fase.**
- **9** — Packaging / installer / signing.
- **10** — Praktische ESR-validatie.
- **11** — Laatste UX/documentatie-afwerking (incl. light theme,
  async URL-fetch, cosmetische scrollbar in Word-samenvatting,
  refresh()-opsplitsing in AnalysisScreen).
- **12** — AI-extractie uit fabrikantdocumenten (docx/xlsx-tekst is
  al beschikbaar).
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
- **Python-headers zijn cumulatief.** Nieuwe versies krijgen een nieuwe
  regel bovenaan de `Wijzigingen:`-lijst; oudere regels blijven staan.
- **Geen `qtbot` gebruiken in tests.** Er is geen `pytest-qt`.
  Gebruik `QApplication.instance() or QApplication([])` en
  `QSignalSpy` uit `PySide6.QtTest`.
- **Geen aannames over de eerstvolgende fase** — vraag het na.

---

## 3. KERNREGELS — BINDENDE AFSPRAKEN

### 3.1 Werkwijze

1. **Kleine, controleerbare fasen.**
2. **Eerst kort uitleggen wat de stap doet; daarna implementeren.**
3. **Volledige bestanden leveren**, geen losse patches als eindresultaat.
4. **Python-bestanden houden versie, datum en wijzigingshistoriek bij**
   in de header.
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
18. **AI-extractie staat laat in de roadmap**; menselijke goedkeuring
    blijft verplicht.
19. **Grafieken en trends lezen bestaande data, ze wijzigen niets.**

### 3.2 Architectuur

- **Assessment-service** bevat beoordelingslogica — geen GUI, geen database.
- **Storage-service** kent structurele validatie — geen beoordelingslogica.
- **Documentatie-service** is read-only — geen import, geen AI,
  geen assessment.
- **Import-service** schrijft alleen in de gebruikerscatalogus — geen
  assessment, geen GUI, geen netwerk (behalve URL-fetch).
- **GUI** verzamelt invoer, roept services aan, toont resultaat.
- **Editor** (5D'.2c) wijzigt alleen metadata; nooit bronbestand, nooit
  status, nooit `imported_at`.
- **Status-editor** (5D'.2e) wijzigt alleen status; nooit metadata,
  nooit bronbestand.
- **Analyse-laag** (fase 7) leest de storage read-only en berekent
  aggregaties. Ze schrijft niet terug.

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
| **8** | **Rapportage** | **Volgende** |
| 9 | Packaging / installer / signing | Gepland |
| 10 | Praktische ESR-validatie | Gepland |
| 11 | Laatste UX/documentatie-afwerking | Gepland |
| 12 | AI-extractie uit fabrikantdocumenten | Gepland |
| 13 | Menselijke validatie van AI-output | Gepland |
| 14 | Goedgekeurde fabrikantdata koppelen aan assessment | Gepland |
| 15 | Tweede diagnosetool — Resistor | Gepland |

---

## 5. WAT IS NIEUW SINDS VERSIE 3.5.0

### 5.1 Fase 7 — Grafieken en trends

In drie deelfasen (7A, 7B, 7C) is een read-only analyse-laag en een
Analyse-pagina toegevoegd.

**Nieuwe bestanden:**

| Bestand | Versie |
|---|---|
| `app/helpers/analysis_series.py` | 1.0.1 |
| `app/services/analysis_service.py` | 1.0.0 |
| `app/gui/analysis_screen.py` | 1.0.2 |
| `i18n/locales/nl_NL/analysis.json` | 1.0.0 |
| `i18n/locales/en_US/analysis.json` | 1.0.0 |
| `tests/test_analysis_series.py` | 1.0.0 |
| `tests/test_analysis_service.py` | 1.0.0 |
| `tests/test_analysis_screen.py` | 1.0.2 |

**Gewijzigde bestanden:**

| Bestand | Versie |
|---|---|
| `app/gui/main_window.py` | 2.10.0 |
| `tests/test_gui_language_switch.py` | uitgebreid met Analyse-test |

**Geen wijziging aan `requirements.txt`.** `PySide6.QtCharts` zit
standaard bij PySide6. `matplotlib` en `pyqtgraph` zijn niet toegevoegd.

**Nieuwe i18n-module:** `analysis.json` in beide locales.

**Nieuwe i18n-keys:** zie de tabel in de chat bij fase 7B. Kort: `tool.analyse`,
`menu.analyse`, `scherm.analyse`, `analyse.*` (titels, labels,
grafiektypes, aggregaties, as-labels, status_onbekend).

**Belangrijkste bugs onderweg gefixt:**

- `aggregate_time_series` valideerde de aggregatie niet bij een lege
  reeks → `analysis_series.py` v1.0.1.
- `AnalysisScreen.__init__` zette de labels niet → v1.0.1.
- `AnalysisScreen.apply_language()` deed een refresh in `__init__`,
  wat de stub-calls onvoorspelbaar maakte → v1.0.2.

### 5.2 Fase 7C — Documentatie bijwerken

- `docs/changelog.md` — versie 1.7 toegevoegd.
- `docs/openvragen.md` — v1.5.0 met §2.10 en §2.11.
- `overdracht.md` — deze versie.

### 5.3 Teststatus

**Baseline: 1037 passed.** Dat is +38 ten opzichte van v3.5.0 (999).

Verdeling van de nieuwe tests:

- 20 tests in de analyse-laag (`test_analysis_series.py` +
  `test_analysis_service.py`) — fase 7A.
- 17 tests in `test_analysis_screen.py` + 1 in
  `test_gui_language_switch.py` — fase 7B.

### 5.4 Bekende beperkingen

- **Geen OCR** voor gescande PDF's.
- **`.doc` en `.xls` worden geweigerd** (oud formaat).
- **Geen async URL-fetch.** Blokkeert de GUI tot 10s.
- **Datum-parsing bij bewerken** accepteert alleen ISO-formaat.
- **Geen bulk-edit** van meerdere imports.
- **Geen bulk-statuswijziging** van meerdere imports.
- **Geen reden bij archiveren.** Bewust geaccepteerd in 5D'.2e.
- **Cosmetische scrollbar** in de Word-samenvatting.
- **`extract_docx_text` en `extract_xlsx_text`** zijn aanwezig maar
  worden niet gebruikt in fase 6. Ze zijn voorbereiding voor fase 12.
- **Analyse-pagina: geen zoom/pan, geen PNG/PDF-export.** Bewust
  buiten fase 7.
- **Analyse-pagina: vaste as-schaling** (µF, mΩ). Zie openvragen §2.11.
- **Analyse-pagina: `apply_language()` doet een refresh.** Zie
  openvragen §2.11.

---

## 6. OPENSTAANDE VRAGEN VOOR DE NIEUWE CHAT

### 6.1 Fase 8 — Rapportage

**Doel:** de gebruiker kan meetgegevens en beoordelingen omzetten in
een rapport dat gedeeld of afgedrukt kan worden.

**Belangrijke uitgangspunten:**

1. **Read-only.** Rapportage leest de storage en de analyse-laag,
   schrijft niets terug.
2. **Historische data niet herberekenen.** Gebruik de
   assessment-snapshots, niet de huidige regels.
3. **Backward-compatible.** Bestaande historiek en export blijven
   werken.
4. **Geen AI.**

### 6.2 Open vragen voor fase 8

De nieuwe chat moet eerst deze vragen met de gebruiker afstemmen
voordat er code wordt geschreven:

1. **Welk rapportformaat?** PDF, HTML, Markdown, of meerdere? PDF is
   het meest bruikbaar voor afdrukken, maar vereist een extra
   dependency (`reportlab`, `weasyprint`, of `QtPdf`). HTML is
   lichtgewicht en kan in een `QTextBrowser` getoond worden. Markdown
   sluit aan bij de bestaande documentatie.
2. **Eén rapport per meting, of een rapport over meerdere metingen?**
   Een meetrapport voor één component is de meest voorkomende vraag.
   Een samenvattend rapport over een filter of periode hoort er
   misschien ook bij.
3. **Wat komt er in een rapport?** Componentgegevens, meetcontext,
   ruwe meetwaarden, assessment, referenties, grafiek? Alles?
4. **Moet de grafiek uit fase 7 in het rapport?** Dat kan als de
   grafiek als afbeelding geëxporteerd wordt (`QChartView.grab()`),
   maar dan moet de analyse-laag ook door de rapportage gebruikt
   worden.
5. **Waar komen rapporten terecht?** Een vaste map
   (`%LOCALAPPDATA%\...\reports\`)? De laatste exportmap, zoals de
   historiek-export? Een dialoog waarin de gebruiker kiest?
6. **Moet een rapport ook de referentiesnapshots bevatten?** Dat is
   relevant voor traceerbaarheid.
7. **Welke taal?** Rapport in de actieve app-taal, of een vaste taal
   per rapport?

### 6.3 Overige openstaande punten

- **Reden opgeven bij archiveren.** Bewust niet gedaan in 5D'.2e.
- **Filter voor alleen gearchiveerde documenten.** Nog niet aanwezig.
- **Bulk-edit en bulk-statuswijziging.** Nog niet ondersteund.
- **OCR voor gescande PDF's.** Uitgesteld.
- **Async URL-fetch.** Fase 11.
- **Catalogusmigratie bij meerdere versies.** Nog niet nodig.
- **Light theme.** Uitgesteld naar fase 11.
- **AI-tekstextractie uit docx/xlsx.** Voorbereiding voor fase 12.
- **Cosmetische scrollbar** in Word-samenvatting. Fase 11.
- **Analyse-pagina:** refresh()-opsplitsing, automatische
  as-schaling, `QDateTimeAxis`-tickformaat, zoom/pan. Zie
  `docs/openvragen.md` §2.11.

---

## 7. TESTSTATUS — BASELINE EN TESTSTRUCTUUR

**Datum:** 2026-10-09
**Baseline:** 1037 passed
**Werkwijze:** eerst gerichte tests, dan volledige `pytest -q`.

### 7.1 Commando's

```powershell
# Eerst gerichte tests van de fase
pytest tests/test_<fase>.py -q

# Daarna volledige suite
pytest -q