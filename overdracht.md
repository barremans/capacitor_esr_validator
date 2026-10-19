# OVERDRACHT — Electronics Diagnostic Tool Hub / ESR Tester

**Versie overdracht:** 5.7.0
**Datum:** 2026-10-16
**Auteur:** Bart Bossuyt
**Vorige versie:** 5.6.0 (2026-10-16)
**Doel:** volledig overdrachtsdocument voor een nieuwe ChatGPT-sessie of
nieuwe ontwikkelaar. Bevat projectstaat, architectuur, regels, changelog,
teststructuur en startprompt. Alles in één bestand.

**Huidige baseline:** 1395 passed
**Laatste afgeronde fase:** 11E — async netwerk
**Volgende fase:** 11F — documentatie-uitbreiding

---

## INHOUD

1. Startprompt (lees dit eerst)
2. Context — projectstaat en architectuur
3. Kernregels — bindende afspraken
4. Stappenplan — chronologisch overzicht
5. Wat is nieuw sinds versie 5.6.0
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
- Baseline: **1395 passed**.
- Laatste afgeronde fase: **11E — async netwerk** (2026-10-16).
- Volgende fase: **11F — documentatie-uitbreiding**.

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

**Wat ik nu van je vraag:**

1. Bevestig dat je de context hebt gelezen en dat je de baseline en
   de volgende fase correct begrijpt.
2. Geef een korte samenvatting (max 10 regels) van de huidige
   projectstaat en de eerstvolgende fase.
3. Vraag om de bestanden uit sectie 8 van dit document **vóór** je
   begint met implementeren.
4. Wacht daarna op mijn instructie. Onderneem nog geen actie, behalve
   als ik expliciet zeg: "start <sub-fase>".

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
| Huidige versie | `1.2.0` |
| Huidige baseline | **1395 passed** |
| Laatste afgeronde fase | 11E — async netwerk |
| Volgende fase | 11F — documentatie-uitbreiding |

### 2.2 Huidige applicatiearchitectuur

**Eén-venster-navigatie (ToolHubWindow):** QStackedWidget met pagina's
hub, diagnose, ESR, historiek, documentatie, analyse.

**Nieuwe module sinds 11A.3:**
- `app/helpers/dialog_start_directory.py` (v1.0.0) — pure helper voor
  QFileDialog-startmappen en het onthouden van de laatst gebruikte map
  per categorie (`export`, `import`, `rapport`).

**Gewijzigd in 11B:**
- `app/services/assessment_service.py` (v1.4.0 → v1.5.0) — onderscheid
  tussen inhoudelijke en administratieve betrouwbaarheidsverlagers.

**Nieuw in 11C:**
- `app/helpers/icon_paths.py` (v1.0.0) — pure padresolutie plus dunne
  Qt-wrappers voor alle iconen. Fallback-keten: `app.png` → `logo.ico`
  → `None`. Geen harde Qt-import op moduleniveau.
- `scripts/genereer_placeholders.py` (v1.0.0) — genereert alle PNG's en
  `logo.ico` met `QPainter`.
- `assets/icons/` bevat nu: `app.png`, `logo.ico`, en 11 thematische
  iconen (`diagnose`, `esr`, `history`, `documentation`, `analysis`,
  `report`, `settings`, `help`, `bug`, `update`, `exit`).

**Gewijzigd in 11D:**
- `app/services/assessment_service.py` (v1.5.0 → v1.6.0) — `Beoordeling`
  krijgt het veld `taal`, gevuld door `beoordeel_meting`.
- `app/gui/esr_test_screen.py` (v1.13.0 → v1.14.0) — `_show_result` en
  `_build_result_html` gebruiken `resultaat.taal`; banner
  `result_language_banner` voor taal-mismatch; bugfix in
  `apply_language` (`_laatste_resultaat is not None`).

**Nieuw in 11E:**
- `app/helpers/async_worker.py` (v2.0.0) — generieke `AsyncWorker` +
  `run_async()`. **Eigenaarsconventie:** de aanroeper bewaart de worker.
- `app/helpers/updater.py` (v1.2.0) — async-varianten
  `check_for_update_async()` en `fetch_release_notes_async()`.
- `app/documentation/url_fetch.py` (v1.2.0) — async-varianten
  `fetch_url_metadata_async()` en `fetch_url_content_async()`.
- `app/gui/main_window.py` (v2.19.1) — async update-check, QA-modus,
  dubbele `getattr`-fix.
- `app/gui/dialogs/import_wizard_dialog.py` (v2.0.0) — async URL-flow;
  PDF/Word/Excel blijven synchroon.
- `app/config/settings.py` (v1.7.0) — `qa_modus`.

Zie v5.0.0 en v5.1.0 van dit document voor de volledige
architectuurbeschrijving.

### 2.3 Belangrijke recente bugfixes

Zie v5.0.0, v5.1.0, v5.2.0. Nieuw sinds v5.6.0:
- **"Signal source has been deleted" in `async_worker.py`.** Opgelost
  in 11E.1 v2.0.0: `WorkerSignals` als sterk Python-attribuut op de
  `AsyncWorker`, `setAutoDelete(False)`, geen registry; de aanroeper
  is eigenaar.
- **`AttributeError` bij ontbrekende `algemeen`-namespace in
  `main_window.py`.** Opgelost in 11E.3 v2.19.1 met dubbele `getattr`.

### 2.4 Openstaande werkpunten en fase 11-indeling

Volgende fase is **11F — documentatie-uitbreiding**. De scope staat in
`docs/openvragen.md` §2.6 en §2.14.

Sub-fase-indeling fase 11 (geactualiseerd):

| Sub-fase | Onderwerp | Status |
|---|---|---|
| **11A** | Export, import en selectie | ✅ afgerond |
| **11B** | Betrouwbaarheidsregel herzien (§2.26) | ✅ afgerond |
| **11C** | Iconen voor alle vensters (§2.27) | ✅ afgerond |
| **11D** | i18n-menging in Diagnose/Result en Resultaatdetails (§2.21) | ✅ afgerond |
| **11E** | Async netwerk: async URL-fetch, async `fetch_release_notes()`, drie-knoppenmelding forceren voor QA | **✅ afgerond** |
| **11F** | Documentatie-uitbreiding: reden bij archiveren, filter gearchiveerde, bulk-edit, bulk-statuswijziging, datum-parsing verfijnen, cosmetische opruiming i18n-keys (§2.6, §2.14) | **Volgende** |
| 11G | Visueel donker thema: checkbox-zichtbaarheid, scrollbar Word-samenvatting, Analyse-pagina cosmetica | Gepland |
| 11H | Light theme | Gepland |
| 11I | Build en cosmetica: `Architecture identifier "x64"`, `[rename] Fallback via robocopy`, `build_log.txt`, externe links changelog, release-notes tabellen, certificaten opruimen, pandas/numpy pins heroverwegen | Gepland |

Daarna volgen fase 12 (AI-extractie), 13 (menselijke validatie),
14 (fabrikantdata koppelen) en 15 (Resistor).

### 2.5 Werkafspraken voor een nieuwe sessie

Onveranderd t.o.v. v5.6.0. Zie §9.

---

## 3. KERNREGELS — BINDENDE AFSPRAKEN

Onveranderd t.o.v. v5.6.0. Zie §3.1 t/m §3.4 van dat document.

---

## 4. STAPPENPLAN — CHRONOLOGISCH OVERZICHT

| Fase | Onderwerp | Status |
|---|---|---|
| 0 t/m 8E | (zie changelog en eerdere overdrachten) | ✅ |
| 9A t/m 9H | Build, GitHub-feedback, update-check | ✅ |
| 10A | Referentie-architectuur met profielen | ✅ |
| 10B | Drempelvalidatie | ✅ (v1.1.2) |
| 11A.1 | Selectie-export in Analyse + menu-item disabled zonder selectie | ✅ |
| 11A.2 | Rapport-scope "selectie" in ReportDialog en MainWindow | ✅ |
| 11A.3 | Mapvoorkeuren centraliseren in dialog_start_directory | ✅ |
| 11B | Betrouwbaarheidsregel herzien | ✅ |
| 11C | Iconen voor alle vensters | ✅ |
| 11D | i18n-menging oplossen | ✅ |
| **11E** | **Async netwerk** | **✅ afgerond** |
| **11F** | **Documentatie-uitbreiding** | **Volgende** |
| 11G | Visueel donker thema | Gepland |
| 11H | Light theme | Gepland |
| 11I | Build en cosmetica | Gepland |
| 12 | AI-extractie uit fabrikantdocumenten | Gepland |
| 13 | Menselijke validatie van AI-output | Gepland |
| 14 | Goedgekeurde fabrikantdata koppelen aan assessment | Gepland |
| 15 | Tweede diagnosetool — Resistor | Gepland |

---

## 5. WAT IS NIEUW SINDS VERSIE 5.6.0

### 5.1 Fase 11E — Async netwerk

**Aanleiding:** update-check, release-notes-fetch en URL-import deden
netwerkverkeer synchroon in de GUI-thread. Bij trage servers bevroor
de GUI even.

**Oplossing in drie sub-fases:**

- **11E.1 — Async update-check.** Nieuwe module
  `app/helpers/async_worker.py` (v2.0.0). `app/helpers/updater.py`
  (v1.2.0) krijgt `check_for_update_async()` en
  `fetch_release_notes_async()`. `app/gui/main_window.py` (v2.18.0)
  gebruikt die.
- **11E.2 — Async URL-fetch in de wizard.**
  `app/documentation/url_fetch.py` (v1.2.0) krijgt
  `fetch_url_metadata_async()` en `fetch_url_content_async()`.
  `app/gui/dialogs/import_wizard_dialog.py` (v2.0.0) gebruikt die;
  knoppen worden disabled, "Bezig…"-tekst verschijnt.
- **11E.3 — Drie-knoppenmelding forceren voor QA.**
  `app/config/settings.py` (v1.7.0) krijgt `algemeen.qa_modus`
  (default `False`). `app/gui/main_window.py` (v2.19.0) toont een
  verborgen QA-menu-item in het Help-menu.

**Bugfix 11E.1:** `RuntimeError: Signal source has been deleted` is
opgelost door `WorkerSignals` als sterk Python-attribuut op de
`AsyncWorker` te houden, `setAutoDelete(False)`, geen registry, en de
aanroeper eigenaar te maken.

**Bugfix 11E.3:** `AttributeError` bij ontbrekende `algemeen`-namespace
in `main_window.py`. Opgelost met dubbele `getattr` (v2.19.1).

### 5.2 Baselinecorrectie 11E

Baseline vóór 11E: **1366**. Baseline ná 11E: **1395**. Toename:
**+29 tests** (9 in `test_async_worker.py`, 4 in `test_updater.py`,
3 in `test_main_window_update_menu.py`, 6 in
`test_documentation_url_fetch.py`, 3 in `test_import_wizard_dialog.py`,
plus herschreven tests in `test_startup_update_check.py`).

### 5.3 Gewijzigde bestanden sinds 5.6.0

| Bestand | Versie / status |
|---|---|
| `app/helpers/async_worker.py` | **nieuw** (v2.0.0) |
| `app/helpers/updater.py` | v1.1.0 → v1.2.0 |
| `app/documentation/url_fetch.py` | v1.1.0 → v1.2.0 |
| `app/gui/main_window.py` | v2.17.0 → v2.19.1 |
| `app/gui/dialogs/import_wizard_dialog.py` | v1.9.0 → v2.0.0 |
| `app/config/settings.py` | v1.6.0 → v1.7.0 |
| `i18n/locales/nl_NL/app.json` | +1 key (`menu.qa_toon_update_melding`) |
| `i18n/locales/en_US/app.json` | +1 key |
| `i18n/locales/nl_NL/documentation.json` | +2 keys (`documentatie.import.bezig_*`) |
| `i18n/locales/en_US/documentation.json` | +2 keys |
| `tests/test_async_worker.py` | **nieuw** (9 tests) |
| `tests/test_updater.py` | v1.2.1 → v1.2.2, +4 async-tests |
| `tests/test_startup_update_check.py` | v1.0.0 → v1.1.0 (async) |
| `tests/test_main_window_update_menu.py` | v1.2.0 → v1.3.0, +3 QA-tests |
| `tests/test_documentation_url_fetch.py` | v1.0.0 → v1.1.0, +6 async-tests |
| `tests/test_import_wizard_dialog.py` | v1.7.0 → v1.8.0, +3 async-tests |
| `tests/test_gui_language_switch.py` | v1.2.0 (alleen `sys.modules`-fix in `test_main_window_update_menu.py`) |
| `docs/changelog/nl_NL.md` | 11E-sectie toegevoegd |
| `docs/changelog/en_US.md` | 11E-sectie toegevoegd |
| `docs/openvragen.md` | v2.9.0 → v3.0.0 |

### 5.4 Teststatus

**Baseline: 1395 passed.** Was 1366 vóór 11E. De toename is +29 tests,
alle additief of herschreven-zonder-vermindering.

### 5.5 Bekende beperkingen (bijgewerkt)

- De icoonbestanden zijn **placeholders** (zie 11C).
- `test_icon_paths.py` gebruikt een **lokale `_app`-fixture** met
  `@pytest.fixture(scope="module")`. Afwijkend van de projectafspraak;
  opruimen in een latere cosmetische fase (11F of 11I).
- `_fake_translate` in `tests/test_gui_language_switch.py` plakt
  kwargs achter de sleutel als `[k=v,...]` in plaats van de echte
  format-vervanging te doen. Cosmetisch; opruimen in 11F of 11I.
- **Async-eigenaarsconventie** is nu expliciet (zie §1 werkafspraken
  en `docs/openvragen.md` §4.25). Nieuwe async-modules moeten de
  worker bewaren in `self._xxx_worker` of `_bewaarde_workers`.

---

## 6. OPENSTAANDE VRAGEN VOOR DE NIEUWE CHAT

Zie `docs/openvragen.md` v3.0.0 voor de volledige, levende lijst.
Samenvatting van de belangrijkste punten voor fase 11F:

- §2.6 — resterende documentatie- en UX-punten (async URL-fetch is
  opgelost in 11E).
- §2.14 — Rapportage: scope "filters" in de Rapportage-GUI;
  cosmetische opruiming i18n-keys.
- §2.20 — relatief `icon_path` verfijnen, `Architecture identifier "x64"`,
  `[rename] Fallback via robocopy`, `build_log.txt`, certificaten
  opruimen.
- §2.9 — cosmetische scrollbar in Word-samenvatting.
- §2.11 — Analyse-pagina: as-schaling, tickformaat, zoom/pan.
- §2.16 — pandas/numpy pins heroverwegen.
- §2.28 — export/import tussen toestellen.
- §4.4 — light theme.

Opgelost in 11B: §2.26.
Opgelost in 11C: §2.27.
Opgelost in 11D: §2.21.
Opgelost in 11E: §2.6 (async URL-fetch), §2.24 (async
release-notes, drie-knoppenmelding forceren).

---

## 7. TESTSTATUS — BASELINE EN TESTSTRUCTUUR

**Datum:** 2026-10-16
**Baseline:** 1395 passed
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
twee `processEvents()`-rondes.

**Belangrijk:** gebruik `isHidden()`, niet `isVisible()`, om de
`setVisible()`-status van een kind te controleren in een test waarin
het scherm nooit `show()` krijgt.

**Belangrijk (sinds 11E):** async-workers worden bewaard in
`_bewaarde_workers` (module-level lijst) tot het einde van de sessie.
In de GUI: `self._xxx_worker`.

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

**Voor fase 11F (documentatie-uitbreiding):**

- `app/documentation/import_service.py` — statuswijzigingen,
  archiveren, bulk-operaties
- `app/documentation/import_models.py` — `DuplicateAction`,
  `ImportStatus`, `ImportSource`
- `app/gui/documentation_screen.py` — de documentatiebibliotheek-GUI
- `app/gui/dialogs/change_status_dialog.py` — statuswijzigingsdialoog
- `app/gui/dialogs/edit_metadata_dialog.py` — metadata-editor
- `app/gui/dialogs/import_wizard_dialog.py` — sinds 11E.2 v2.0.0
- `i18n/locales/nl_NL/documentation.json`
- `i18n/locales/en_US/documentation.json`
- `tests/test_documentation_import_service.py`
- `tests/test_documentation_edit_metadata_service.py`
- `tests/test_documentation_screen.py`
- `tests/test_change_status_dialog.py`
- `tests/test_edit_metadata_dialog.py`

Enzovoort, afhankelijk van de gekozen sub-fase.

---

## 9. WERKAFSPRAKEN IN EEN NIEUWE SESSIE

Onveranderd t.o.v. v5.6.0. Toevoeging:

- **Offscreen GUI-tests en `isVisible()`:** in een test waarin het
  scherm nooit `show()` krijgt, is `isVisible()` altijd `False`, ook
  als `setVisible(True)` op een kind is aangeroepen. Gebruik
  `isHidden()` voor "is dit kind zichtbaar binnen zijn ouder?".
- **Gebruik in productie nooit `isVisible()` als conditie voor "is er
  ooit iets gebeurd?".** Gebruik daarvoor een expliciet statusveld.
  `isVisible()` is alleen betrouwbaar als het hele venster zichtbaar
  is, wat in offscreen tests en in niet-actieve
  `QStackedWidget`-pagina's niet zo is.
- **Async-eigenaarsconventie (sinds 11E):** de aanroeper van
  `run_async()` is eigenaar van de teruggegeven `AsyncWorker` en moet
  die bewaren zolang de worker bezig is. In de GUI via
  `self._xxx_worker`; in tests via `_bewaarde_workers`. Zonder die
  referentie kan de `WorkerSignals` worden opgeruimd en faalt de emit
  met `Signal source has been deleted`.