# OVERDRACHT — Electronics Diagnostic Tool Hub / ESR Tester

**Versie overdracht:** 6.6.0
**Datum:** 2026-10-22
**Auteur:** Bart Bossuyt
**Vorige versie:** 6.5.0 (2026-10-22)
**Doel:** volledig overdrachtsdocument voor een nieuwe ChatGPT-sessie of
nieuwe ontwikkelaar. Bevat projectstaat, architectuur, regels, changelog,
teststructuur en startprompt. Alles in één bestand.

**Huidige baseline:** 1598 passed
**Laatste afgeronde sub-fase:** 12E — Scope "filters" in de Rapportage-GUI
**Volgende fase:** §2.28 — Export/import tussen toestellen
**Op hold:** 12B — AI-model-keuze en API-koppeling

---

## INHOUD

1. Startprompt (lees dit eerst)
2. Context — projectstaat en architectuur
3. Kernregels — bindende afspraken
4. Stappenplan — chronologisch overzicht
5. Wat is nieuw sinds versie 6.5.0
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
- Baseline: **1598 passed**.
- Huidige versie: `1.2.3`.
- Laatste afgeronde sub-fase: **12E — Scope "filters" in de
  Rapportage-GUI** (2026-10-22).
- Daarvoor afgerond: **12A — Documenttype-detectie en
  extractie-orkestratie** (2026-10-22).
- Op hold: **12B — AI-model-keuze en API-koppeling** (wacht op
  provider/model-keuze).
- Volgende opdracht: **§2.28 — Export/import tussen toestellen**.

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
- **Er is een minimale `conftest.py`** (sinds 11H.3). Die zet
  `QT_QPA_PLATFORM=offscreen` vóór PySide6 geïmporteerd wordt en
  ruimt na elke test alle widgets op via `deleteLater()` +
  `processEvents()`. **Gebruik geen `qtbot`-fixture**; `pytest-qt` is
  geen dependency van dit project. De lokale `_app()`-helper
  (`QApplication.instance() or QApplication([])`) blijft de standaard
  in GUI-tests. De `conftest.py` bevat **geen** projectimports en
  **geen** `qtbot`.
- **Verwerk `deleteLater()` in GUI-tests** met
  `QApplication.processEvents()` vóór je de menubar of andere
  QObject-hiërarchieën inspecteert. De autouse-fixture in
  `conftest.py` doet dit al na elke test, maar als een test
  **binnen** zijn eigen body een `deleteLater()` uitvoert (bv. na het
  sluiten van een dialoog), moet hij zelf `processEvents()` aanroepen.
  **Bewaar nooit een QMenu- of QAction-pointer tussen twee
  `processEvents()`-ronden**: die kan ongeldig worden. Lees altijd
  alles in één keer uit.
- **De taalparameter van `ToolHubWindow` heeft voorrang op
  `settings.json`. Hetzelfde geldt sinds 11H.3 voor de
  `theme`-parameter.**
- **`setStyleSheet` op een venster, niet op de `QApplication`.** Een
  venster beheert zijn eigen stijl via `self.setStyleSheet(...)`. De
  globale `apply_theme(app, thema)` in `main.py` is de enige
  uitzondering: die zet de default-look voor dialogen zonder parent
  (meldingsboxen, file-dialogs). Elke onvoorwaardelijke
  `QApplication.setStyleSheet` is verboden; die dwingt Qt bij elke
  widget-aanmaak en elke nieuwe `setStyleSheet` de volledige
  stylesheet opnieuw te matchen tegen alle bestaande widgets, wat in
  de testsuite opliep tot 50–170 seconden per test.
- **Thema doorgeven aan schermen**: schermen die thema-afhankelijke
  kleuren hebben, krijgen een **keyword-only** `theme`-parameter
  (default `"dark"`, genormaliseerd via `normaliseer_thema()`) en een
  `apply_theme(theme)`-methode. Sinds 11H.4 heeft `AnalysisScreen`
  die; sinds 11H.5 ook `HistoryScreen`. Andere schermen (ESR,
  Documentatie) hebben nog geen thema-afhankelijke kleuren en krijgen
  de parameter pas als ze die nodig hebben.
- **Voor leesbare PDF-rapporten:** sinds fase 9A zet `main.py`
  automatisch `QT_QPA_FONTDIR=C:\Windows\Fonts` op Windows.
- **Bij het leveren van `.md`-bestanden die zelf codeblokken bevatten:**
  gebruik **viervoudige backticks**. Bij twijfel: altijd viervoudig.
  **Lever nooit een `.md`-bestand in driedubbele backticks als het zelf
  ```markdown- of ```powershell-blokken bevat.** De omhullende
  afbakening moet langer zijn dan de langste interne afbakening, anders
  sluit een interne afsluiting het omhullende blok voortijdig.
- **De ArticleSearch-flow is de bewezen build-flow.**
- **Geen aannames over de volgende fase:** vraag het na.
- **Nooit een GitHub-token in een getrackt bestand, chat of
  context-document zetten.**
- **Bij een verschil tussen de gedocumenteerde baseline en de werkelijke
  `pytest -q`-uitvoer: eerst uitzoeken, dan pas doorgaan. Nooit stil
  een nieuwe fase starten op een ongeverifieerde baseline.**
- **Offscreen GUI-tests en `isVisible()`:** in een test waarin het
  scherm nooit `show()` krijgt, is `isVisible()` altijd `False`, ook
  als `setVisible(True)` op een kind is aangeroepen. Gebruik
  `isHidden()` voor "is dit kind zichtbaar binnen zijn ouder?" en
  gebruik in productie **nooit** `isVisible()` als conditie voor
  "is er ooit iets gebeurd?" — gebruik daarvoor een expliciet
  statusveld.
- **Async-eigenaarsconventie (sinds 11E):** de aanroeper van
  `run_async()` is eigenaar van de teruggegeven `AsyncWorker` en moet
  die bewaren zolang de worker bezig is. In de GUI via
  `self._xxx_worker`; in tests via `_bewaarde_workers`. Zonder die
  referentie kan de `WorkerSignals` worden opgeruimd en faalt de emit
  met `Signal source has been deleted`.
- **Testtelling bijhouden per fase:** tel nieuwe tests per bestand
  (gerichte `pytest --collect-only -q`), niet op basis van een schatting.
  De som van de betrokken bestanden moet overeenkomen met de
  volledige `pytest -q`. Bij afwijking: eerst uitzoeken, dan doorgaan.
- **Bij het herschrijven van een test-sectie: `Compare-Object` tegen
  de vorige versie.** Dit heeft in 11F.2 twee per ongeluk verwijderde
  tests opgespoord.
- **`icon_paths.py` gebruikt sinds 11I.2 een expliciete
  `sys._MEIPASS`-branch vóór de omhoog-zoeklus.** In de
  PyInstaller-bundel staat `assets/` in `_internal/assets/`; de
  branch maakt de resolutie deterministisch.
- **`build_installer.bat` logt sinds 11I.3 de PyInstaller-stap [4] en
  de ISCC-stap [7] met `>> "%LOGFILE%" 2>&1` naar `build_log.txt`.**
  De rest blijft naar de console. `build_log.txt` staat expliciet in
  `.gitignore`.
- **`build_and_publish.ps1` geeft sinds 11I.3 de bevestigingsvraag
  "Starten?" een expliciete standaardwaarde J bij Enter**, consistent
  met de vier vragen ervoor.

**Wat ik nu van je vraag:**

1. Bevestig dat je de context hebt gelezen en dat je de baseline en
   de volgende fase correct begrijpt.
2. Geef een korte samenvatting (max 10 regels) van de huidige
   projectstaat en de eerstvolgende fase.
3. Stel een sub-fase-indeling voor **§2.28 (export/import tussen
   toestellen)** voor, op basis van `docs/openvragen.md` §2.28 en de
   bestaande storage- en historiekarchitectuur (`storage/schema.py`,
   `storage/service.py`, `storage/models.py`,
   `services/history_service.py`, `helpers/history_csv_export.py`,
   `helpers/history_detail_export.py`). Vraag me om bevestiging van
   die indeling **vóór** je begint met implementeren.
4. Vraag om eventuele extra bestanden die je voor §2.28 nodig hebt en
   die nog niet in de bijlagen zitten.
5. Wacht daarna op mijn instructie "start 2.28" (of "start 2.28.x"
   als we sub-fase-per-sub-fase werken).

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
| Huidige versie | `1.2.3` |
| Huidige baseline | **1598 passed** |
| Laatste afgeronde sub-fase | 12E — Scope "filters" in de Rapportage-GUI |
| Op hold | 12B — AI-model-keuze en API-koppeling |
| Volgende opdracht | §2.28 — Export/import tussen toestellen |

### 2.2 Huidige applicatiearchitectuur

Zie v6.0.0 §2.2 voor de volledige architectuurbeschrijving. Nieuw
sinds v6.5.0:

**Gewijzigd in 12A:**
- `app/documentation/extraction_models.py` (nieuw, **v1.0.0**) —
  uniform `ExtractionResult`, `ExtractionError`,
  `ExtractionSourceKind` (PDF/DOCX/XLSX/URL). Frozen, slots,
  validatie in `__post_init__`. Geen Qt, geen netwerk, geen AI.
- `app/documentation/extraction_service.py` (nieuw, **v1.0.0**) —
  dispatcher `extract_for_source`, `extract_for_path`,
  `extract_for_url` die de bestaande extractors
  (`pdf_extract`, `docx_extract`, `xlsx_extract`, `url_fetch`)
  aanroept en hun resultaat vertaalt naar het uniforme model.
  Lokale URL-teksthepler via BeautifulSoup, zodat `url_fetch.py`
  niet gewijzigd hoefde te worden.
- `tests/test_documentation_extraction_models.py` (nieuw, **v1.0.0**,
  15 tests).
- `tests/test_documentation_extraction_service.py` (nieuw,
  **v1.0.0**, 22 tests).

**Gewijzigd in 12E:**
- `app/gui/dialogs/report_dialog.py` (v1.5.0 → **v1.6.1**) —
  classmethod `for_filters`, `_kop_tekst`-helper, kop-update in
  `_laad_bundle` voor de filters-modus.
- `app/gui/history_screen.py` (v1.18.0 → **v1.19.0**) —
  `_show_report_for_selected` kent drie modi (selectie / filters /
  enkelvoudig), nieuwe `_heeft_actieve_filters`-helper.
- `app/gui/analysis_screen.py` (v1.7.0 → **v1.7.2**) —
  `_open_report_for_selection` kent drie modi, nieuwe
  `_heeft_actieve_filters`-helper die uitsluitend naar de GUI-velden
  kijkt (de hardcoded `tool_key="ESR_CAPACITOR"` telt niet mee).
- `tests/test_report_dialog_scope_filters.py` (nieuw, **v1.0.1**,
  13 tests).

**Samenvatting van 12A en 12E (allemaal afgerond):**

| Onderdeel | Bestand | Versie |
|---|---|---|
| Uniform extractiemodel | `app/documentation/extraction_models.py` | v1.0.0 |
| Extractie-dispatcher | `app/documentation/extraction_service.py` | v1.0.0 |
| Scope "filters" dialoog | `app/gui/dialogs/report_dialog.py` | v1.6.1 |
| Scope "filters" historiek | `app/gui/history_screen.py` | v1.19.0 |
| Scope "filters" analyse | `app/gui/analysis_screen.py` | v1.7.2 |

### 2.3 Belangrijke recente bugfixes

Zie v6.0.0 §2.3 en v6.5.0 §2.3. Nieuw sinds v6.5.0:

- **12E:** `AnalysisScreen._heeft_actieve_filters()` gaf altijd
  `True` omdat `_active_filters()` altijd `tool_key="ESR_CAPACITOR"`
  bevat. Daardoor opende de rapport-knop op de Analyse-pagina altijd
  de filters-scope, ook zonder gebruikersfilter. Opgelost in
  `analysis_screen.py` v1.7.2: de helper kijkt nu uitsluitend naar
  de GUI-velden.
- **12E:** `ReportDialog.kop_label` toonde "0 metingen" voor de
  filters-modus, omdat `_build_ui()` vóór `_laad_bundle()` loopt.
  Opgelost in `report_dialog.py` v1.6.1: `_laad_bundle()` werkt de
  kop bij zodra het aantal bekend is.

### 2.4 Openstaande werkpunten en fase-indeling

**Op hold:** 12B — AI-model-keuze en API-koppeling. Wacht op een
ontwerpbeslissing: welke provider, welk model, offline-first of
cloud-API, en waar de API-key leeft (analoog aan
`github_secret_local.py`). Zonder die beslissing kan 12B niet
verantwoord ontworpen worden.

**Volgende opdracht:** **§2.28 — Export/import tussen toestellen**
(`docs/openvragen.md` v3.7.0). Dit is een aparte fase, geen restpost
van 12. De exacte sub-fase-indeling wordt bij de start van §2.28
bepaald. Vraag het na.

Daarna volgen (in deze volgorde, tenzij anders beslist):
- 12C — Prompt-engineering en output-validatie (na 12B).
- 12D — Resultaatopslag en herkomst-tracking (na 12C).
- Fase 13 — Menselijke validatie van AI-output.
- Fase 14 — Goedgekeurde fabrikantdata koppelen aan assessment.
- Fase 15 — Tweede diagnosetool — Resistor.

### 2.5 Werkafspraken voor een nieuwe sessie

Onveranderd t.o.v. v6.0.0, aangevuld met de `conftest.py`-regel uit §1.

---

## 3. KERNREGELS — BINDENDE AFSPRAKEN

Onveranderd t.o.v. v6.5.0, behalve:

- **`app/gui/dialogs/report_dialog.py` heeft sinds 12E een
  classmethod `for_filters(filters, *, scope, taal, ...)`.** De
  bestaande `ReportDialog(id, ...)` en `ReportDialog.for_measurements`
  blijven ongewijzigd. Nieuwe code die een rapport over de actieve
  filters wil, gebruikt `for_filters`.
- **`HistoryScreen._show_report_for_selected` en
  `AnalysisScreen._open_report_for_selection` kennen sinds 12E drie
  modi:** checkbox-selectie → "Selectie"; geen checkbox-selectie maar
  wél actieve filters → "Huidige filters"; anders → bestaand gedrag.
- **`extraction_models.py` en `extraction_service.py` zijn de uniforme
  ingang voor tekst- en metadata-extractie sinds 12A.** Nieuwe code
  die tekst uit een geïmporteerde bron nodig heeft, gebruikt
  `extract_for_source`, `extract_for_path` of `extract_for_url`, niet
  de onderliggende `pdf_extract`/`docx_extract`/`xlsx_extract`/
  `url_fetch` rechtstreeks.

---

## 4. STAPPENPLAN — CHRONOLOGISCH OVERZICHT

| Fase | Onderwerp | Status |
|---|---|---|
| 0 t/m 8E | (zie changelog en eerdere overdrachten) | ✅ |
| 9A t/m 9H | Build, GitHub-feedback, update-check | ✅ |
| 10A | Referentie-architectuur met profielen | ✅ |
| 10B | Drempelvalidatie | ✅ (v1.1.2) |
| 11A.1 t/m 11A.3 | Export, import en selectie | ✅ |
| 11B | Betrouwbaarheidsregel herzien | ✅ |
| 11C | Iconen voor alle vensters | ✅ |
| 11D | i18n-menging oplossen | ✅ |
| 11E | Async netwerk | ✅ |
| 11F.1 t/m 11F.4 | Documentatie-uitbreiding | ✅ |
| 11G.1 t/m 11G.7 | Visueel donker thema | ✅ |
| 11H.1 t/m 11H.5 | Light theme | ✅ |
| 11I.1 t/m 11I.5 | Build en cosmetica | ✅ |
| 12A | Documenttype-detectie en extractie-orkestratie | ✅ |
| 12B | AI-model-keuze en API-koppeling | **Op hold** |
| 12C | Prompt-engineering en output-validatie | Gepland (na 12B) |
| 12D | Resultaatopslag en herkomst-tracking | Gepland (na 12C) |
| 12E | Scope "filters" in de Rapportage-GUI | ✅ |
| **§2.28** | **Export/import tussen toestellen** | **Volgende** |
| 13 | Menselijke validatie van AI-output | Gepland |
| 14 | Goedgekeurde fabrikantdata koppelen aan assessment | Gepland |
| 15 | Tweede diagnosetool — Resistor | Gepland |

---

## 5. WAT IS NIEUW SINDS VERSIE 6.5.0

### 5.1 Fase 12A — Documenttype-detectie en extractie-orkestratie

**Aanleiding:** de bestaande `*_import.py`-orkestratoren deden de
import (hash → metadata → registratie → kopie), maar de tekstextractie
(`extract_pdf_text`, `extract_docx_text`, `extract_xlsx_text`) was
nirgens aangesloten. Voor fase 12 (AI-extractie) was er één uniforme
ingang nodig die per brontype dezelfde vorm teruggeeft.

**Oplossing:**
- `app/documentation/extraction_models.py` v1.0.0 —
  `ExtractionResult`, `ExtractionError`, `ExtractionSourceKind`.
- `app/documentation/extraction_service.py` v1.0.0 —
  `extract_for_source`, `extract_for_path`, `extract_for_url`.
- Nieuwe tests: 15 + 22 = 37.

Geen bestaande module gewijzigd: `pdf_extract.py`, `docx_extract.py`,
`xlsx_extract.py`, `url_fetch.py`, `import_service.py`,
`import_models.py` en de vier `*_import.py` zijn onaangeroerd.

### 5.2 Fase 12E — Scope "filters" in de Rapportage-GUI (§2.14)

**Aanleiding:** §2.14 was half opgelost in 11A.2 (scope "selectie"),
maar scope "filters" in de Rapportage-GUI stond nog open. De
`ReportService.build_bundle_from_filters(...)` bestond al sinds
11A.2; de GUI-koppeling ontbrak.

**Oplossing:**
- `app/gui/dialogs/report_dialog.py` v1.6.1 — classmethod
  `for_filters`.
- `app/gui/history_screen.py` v1.19.0 — `_show_report_for_selected`
  met drie modi.
- `app/gui/analysis_screen.py` v1.7.2 — `_open_report_for_selection`
  met drie modi.
- Nieuwe tests: 13.

Tijdens de implementatie gevonden en gefixt: `_heeft_actieve_filters`
in `AnalysisScreen` gaf altijd `True` door de hardcoded
`tool_key="ESR_CAPACITOR"`.

### 5.3 Baseline

| Sub-fase | Baseline vóór | Baseline ná | Nieuw |
|---|---|---|---|
| 11I.5 | 1548 | 1548 | 0 |
| 12A | 1548 | 1585 | +37 |
| 12E | 1585 | **1598** | +13 |

**Totaal sinds 11I.5:** 1548 → 1598 (+50 tests).

### 5.4 Gewijzigde bestanden sinds 6.5.0

| Bestand | Versie / status |
|---|---|
| `app/documentation/extraction_models.py` | **nieuw** v1.0.0 |
| `app/documentation/extraction_service.py` | **nieuw** v1.0.0 |
| `app/gui/dialogs/report_dialog.py` | v1.5.0 → **v1.6.1** |
| `app/gui/history_screen.py` | v1.18.0 → **v1.19.0** |
| `app/gui/analysis_screen.py` | v1.7.0 → **v1.7.2** |
| `tests/test_documentation_extraction_models.py` | **nieuw** v1.0.0 (15 tests) |
| `tests/test_documentation_extraction_service.py` | **nieuw** v1.0.0 (22 tests) |
| `tests/test_report_dialog_scope_filters.py` | **nieuw** v1.0.1 (13 tests) |
| `overdracht.md` | → **v6.6.0** |
| `docs/openvragen.md` | → **v3.7.0** |

### 5.5 Teststatus

**Baseline: 1598 passed.** Was 1548 vóór 12A. De toename is +37
(12A) + 13 (12E). De suite draait in ~208 s.

### 5.6 Bekende beperkingen (bijgewerkt)

Onveranderd t.o.v. v6.5.0. Wat nog rest:

- **`QApplication.setStyleSheet` is verboden** behalve in `main.py`
  bij opstart. Gebruik `self.setStyleSheet(...)` op het venster.
- **`esr_test_screen.py` en `documentation_screen.py`** bevatten nog
  geen thema-afhankelijke kleuren.
- **Publiek vertrouwd (EV-)certificaat** — structurele oplossing.
- **Fallback timestamp-server** — single point of failure.
- **12B op hold** — wacht op provider/model-keuze.

---

## 6. OPENSTAANDE VRAGEN VOOR DE NIEUWE CHAT

Zie `docs/openvragen.md` v3.7.0 voor de volledige, levende lijst.
Samenvatting van de belangrijkste punten voor §2.28:

- §2.28 — export/import tussen toestellen.
- §11 packaging — publiek vertrouwd (EV-)certificaat;
  fallback timestamp-server.

Opgelost in 12A: de extractie-orkestratie (geen open vraag, wel een
architectuurpunt).
Opgelost in 12E: §2.14 (scope "filters" in de Rapportage-GUI).

**§2.14 is nu volledig opgelost.**

---

## 7. TESTSTATUS — BASELINE EN TESTSTRUCTUUR

**Datum:** 2026-10-22
**Baseline:** 1598 passed
**Werkwijze:** eerst gerichte tests, dan volledige `pytest -q`.

### 7.1 Commando's

```powershell
# Eerst gerichte tests van de fase
pytest tests/test_<fase>.py -q

# Tel nieuwe tests per bestand
pytest tests/test_<fase>.py --collect-only -q

# Daarna volledige suite
pytest -q
```

### 7.2 GUI-tests

Sinds 11H.3 is er een **minimale `conftest.py`** die:

- `QT_QPA_PLATFORM=offscreen` zet vóór PySide6 geïmporteerd wordt.
- Na elke test alle widgets (`allWidgets()`) opruimt via
  `deleteLater()` + drie `processEvents()`-rondes.

De lokale `_app()`-helper blijft de standaard in GUI-tests. Er is
**geen** `qtbot`, **geen** `pytest-qt`.

### 7.3 Voor leesbare PDF's

Sinds fase 9A zet `main.py` de variabele automatisch.

### 7.4 Build testen

```powershell
.\build_and_publish.ps1
```

### 7.5 Publiceren (fase 9E)

```powershell
.\publish.ps1
```

### 7.6 GitHub-token controleren (fase 9G)

```powershell
python check_github_secret.py
```

---

## 8. BESTANDEN DIE DE NIEUWE CHAT MOET OPVRAGEN

Voor een nieuwe sessie heeft de chat meestal nodig:

- `overdracht.md` (dit bestand) — primaire bron
- `docs/openvragen.md` — levende lijst
- `docs/python_header_standard.md`
- `docs/markdown_levering.md`
- `conftest.py` — minimale autouse-fixture (sinds 11H.3)

**Voor §2.28 (export/import tussen toestellen):**

De volledige storage-laag en de historiek-service zijn nodig:

- `app/storage/schema.py` (v1.1.0)
- `app/storage/service.py` (v1.1.0)
- `app/storage/models.py` (v1.1.0)
- `app/storage/database.py`
- `app/storage/migrations.py`
- `app/storage/paths.py`
- `app/storage/exceptions.py`
- `app/services/history_service.py` (v1.1.1)
- `docs/data_model.md`
- `docs/context.md`

Sterk aanbevolen:

- `app/gui/main_window.py` (v2.22.2) — voor het menu-item.
- `app/gui/history_screen.py` (v1.19.0) — exportknop.
- `app/helpers/history_csv_export.py`, `history_detail_export.py` —
  bestaand exportpatroon.
- `tests/test_storage_schema.py`, `test_storage_service.py`,
  `test_storage_migrations.py`, `test_storage_v1_completion.py` —
  bestaande tests, zodat de nieuwe tests in dezelfde stijl passen.
- `app/version.py` — als §2.28 een nieuwe app-versie krijgt.

**Voor fase 13 (menselijke validatie) — nog niet nu:**

- `app/gui/documentation_screen.py`
- `app/gui/dialogs/edit_metadata_dialog.py`
- `app/gui/dialogs/bulk_edit_metadata_dialog.py`

---

## 9. WERKAFSPRAKEN IN EEN NIEUWE SESSIE

Onveranderd t.o.v. v6.0.0 §9, aangevuld met:

- **`conftest.py` is een geaccepteerd onderdeel van de suite** sinds
  11H.3. Houd hem minimaal: alleen `QT_QPA_PLATFORM=offscreen` en de
  autouse-opruimfixture. Geen projectimports, geen `qtbot`.
- **`setStyleSheet` nooit onvoorwaardelijk op de `QApplication`**
  aanroepen. Gebruik `self.setStyleSheet(...)` op het venster, of een
  gelijkwaardige check (`_apply_theme_if_needed()`).
- **Thema doorgeven aan schermen** met een keyword-only
  `theme`-parameter en een `apply_theme(theme)`-methode, zoals in
  `AnalysisScreen` (sinds 11H.4) en `HistoryScreen` (sinds 11H.5).
- **`icon_paths.py` gebruikt sinds 11I.2 een expliciete
  `sys._MEIPASS`-branch** vóór de omhoog-zoeklus.
- **`build_installer.bat` logt sinds 11I.3 de PyInstaller-stap [4] en
  de ISCC-stap [7]** naar `build_log.txt`.
- **`build_and_publish.ps1` geeft sinds 11I.3 de bevestigingsvraag
  "Starten?" een expliciete standaardwaarde J.**
- **`signing-certs/` staat sinds 11I.4 in `.gitignore`.**
- **`ReportDialog.for_filters` bestaat sinds 12E** en is de juiste
  ingang voor een rapport over de actieve filters.
- **`extraction_service.py` is sinds 12A de uniforme extractie-ingang.**
  Nieuwe code gebruikt die, niet de onderliggende extractors
  rechtstreeks.