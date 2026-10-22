# OVERDRACHT — Electronics Diagnostic Tool Hub / ESR Tester

**Versie overdracht:** 6.5.0
**Datum:** 2026-10-22
**Auteur:** Bart Bossuyt
**Vorige versie:** 6.4.0 (2026-10-21)
**Doel:** volledig overdrachtsdocument voor een nieuwe ChatGPT-sessie of
nieuwe ontwikkelaar. Bevat projectstaat, architectuur, regels, changelog,
teststructuur en startprompt. Alles in één bestand.

**Huidige baseline:** 1548 passed
**Laatste afgeronde fase:** 11I.5 — Afronding fase 11I
**Volgende fase:** 12 — AI-extractie uit fabrikantdocumenten

---

## INHOUD

1. Startprompt (lees dit eerst)
2. Context — projectstaat en architectuur
3. Kernregels — bindende afspraken
4. Stappenplan — chronologisch overzicht
5. Wat is nieuw sinds versie 6.4.0
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
- Baseline: **1548 passed**.
- Huidige versie: `1.2.3`.
- Laatste afgeronde fase: **11I — Build en cosmetica** (2026-10-22),
  met 11I.1 t/m 11I.5.
- Volgende fase: **12 — AI-extractie uit fabrikantdocumenten**.

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
| Huidige versie | `1.2.3` |
| Huidige baseline | **1548 passed** |
| Laatste afgeronde fase | 11I — Build en cosmetica (11I.1 t/m 11I.5) |
| Volgende fase | 12 — AI-extractie uit fabrikantdocumenten |

### 2.2 Huidige applicatiearchitectuur

Zie v6.0.0 §2.2 voor de volledige architectuurbeschrijving. Nieuw
sinds v6.4.0:

**Gewijzigd in 11I.1:**
- `requirements.txt` (v1.0.0 → **v1.1.0**) — commentaar dat uitlegt
  waarom `numpy` en `pandas` een bovengrens `<3` hebben. Geen
  pin-wijziging.
- `docs/future_tools.md` §5 — gelijkgetrokken met de werkelijke pins.
- `docs/packaging.md` (v1.0.0 → **v1.1.0**) — nieuwe subsectie §2.1
  "Dependency-pins".

**Gewijzigd in 11I.2:**
- `app/helpers/icon_paths.py` (v1.0.0 → **v1.1.0**) — nieuwe
  `sys._MEIPASS`-branch in `_projectroot_default()`, vóór de
  omhoog-zoeklus. Deterministische resolutie in de
  PyInstaller-bundel. Geen wijziging aan de publieke API.
- `tests/test_icon_paths.py` (v1.1.0 → **v1.2.0**, +2 tests).

**Gewijzigd in 11I.3:**
- `build_installer.bat` (v2.0.1 → **v2.0.3**) — `x64compatible`,
  robocopy-melding verduidelijkt (één regel, geen meerregelige echo
  binnen `(...)`), logging van [4] en [7] naar `build_log.txt`.
- `build_and_publish.ps1` (v1.0.0 → **v1.1.0**) — standaard J bij
  "Starten?".
- `.gitignore` — `build_log.txt`.
- `docs/packaging.md` (v1.1.0 → **v1.3.0**) — §2-tabel bijgewerkt,
  §11 bijgewerkt.

**Gewijzigd in 11I.4:**
- `.gitignore` — `signing-certs/`.
- `docs/packaging.md` (v1.3.0 → **v1.4.0**) — nieuwe subsectie §4.1
  "Certificaatstore-hygiëne"; §11 bijgewerkt.

**Gewijzigd in 11I.5:**
- `docs/changelog/nl_NL.md` (→ **v1.3.0**) — nieuwe sectie "Fase 11I".
- `docs/changelog/en_US.md` (→ **v1.3.0**) — idem in het Engels.
- `overdracht.md` (→ **v6.5.0**) — dit document.
- `WatNu.md` (→ **v2.3.0**) — bijgewerkt.
- `docs/openvragen.md` (→ **v3.6.0**) — §2.16 en §2.20 gemarkeerd,
  nieuwe subsectie 4.39.
- `docs/packaging.md` (v1.4.0 → **v1.5.0**) — alleen de
  changelog-regel in de header.

**Samenvatting van 11I.1 t/m 11I.5 (allemaal afgerond):**

| Onderdeel | Bestand | Versie |
|---|---|---|
| Pins gedocumenteerd | `requirements.txt` | v1.1.0 |
| `icon_path` via `sys._MEIPASS` | `app/helpers/icon_paths.py` | v1.1.0 |
| Build-orchestratie opgeschoond | `build_installer.bat` | v2.0.3 |
| "Starten?"-standaard | `build_and_publish.ps1` | v1.1.0 |
| Certificaatstore-hygiëne | `docs/packaging.md` | v1.5.0 |

### 2.3 Belangrijke recente bugfixes

Zie v6.0.0 §2.3. Nieuw sinds v6.4.0:

- **11I.3:** de meerregelige echo in de `[rename]`-fallback van
  `build_installer.bat` brak de cmd-parser (`. was unexpected at this
  time.`). Opgelost in v2.0.3 door de melding tot één regel terug te
  brengen (met `^`-escaping voor de haakjes).

Zie v6.3.0 §2.3 voor de bugfixes uit 11H.3 (v2.21.1, v2.21.2,
v2.21.3, v2.22.0).

### 2.4 Openstaande werkpunten en fase 12-indeling

Volgende fase is **12 — AI-extractie uit fabrikantdocumenten**.

Sub-fase-indeling fase 12 (voorstel, nog niet uitgewerkt):

| Sub-fase | Onderwerp | Status |
|---|---|---|
| **12A** | Documenttype-detectie en extractie-orkestratie | **Volgende** |
| **12B** | AI-model-keuze en API-koppeling | Gepland |
| **12C** | Prompt-engineering en output-validatie | Gepland |
| **12D** | Resultaatopslag en herkomst-tracking | Gepland |

De exacte indeling wordt bij de start van fase 12 bepaald. Vraag het
na.

Daarna volgen fase 13 (menselijke validatie), 14 (fabrikantdata
koppelen) en 15 (Resistor).

### 2.5 Werkafspraken voor een nieuwe sessie

Onveranderd t.o.v. v6.0.0, aangevuld met de `conftest.py`-regel uit §1.

---

## 3. KERNREGELS — BINDENDE AFSPRAKEN

Onveranderd t.o.v. v6.4.0, behalve:

- **`icon_paths.py` gebruikt sinds 11I.2 een expliciete
  `sys._MEIPASS`-branch** vóór de omhoog-zoeklus.
- **`build_installer.bat` logt sinds 11I.3 de PyInstaller-stap [4] en
  de ISCC-stap [7]** naar `build_log.txt`; `build_log.txt` staat in
  `.gitignore`.
- **`build_and_publish.ps1` geeft sinds 11I.3 de bevestigingsvraag
  "Starten?" een expliciete standaardwaarde J** bij Enter.
- **`signing-certs/` staat sinds 11I.4 in `.gitignore`.**

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
| **11I.1 t/m 11I.5** | **Build en cosmetica** | ✅ |
| **12** | **AI-extractie uit fabrikantdocumenten** | **Volgende** |
| 13 | Menselijke validatie van AI-output | Gepland |
| 14 | Goedgekeurde fabrikantdata koppelen aan assessment | Gepland |
| 15 | Tweede diagnosetool — Resistor | Gepland |

---

## 5. WAT IS NIEUW SINDS VERSIE 6.4.0

### 5.1 Fase 11I.1 — Pins documenteren

**Aanleiding:** de pandas/numpy-pins in `requirements.txt` waren niet
gedocumenteerd. `docs/future_tools.md` §5 noemde een verouderde set.

**Oplossing:**
- `requirements.txt` v1.1.0 — commentaar dat uitlegt waarom `numpy` en
  `pandas` een bovengrens `<3` hebben. Geen pin-wijziging.
- `docs/packaging.md` v1.1.0 — nieuwe §2.1 "Dependency-pins".
- `docs/future_tools.md` §5 — gelijkgetrokken.

### 5.2 Fase 11I.2 — `icon_path` via `sys._MEIPASS`

**Aanleiding:** het icoonpad was niet deterministisch in de
PyInstaller-bundel.

**Oplossing:**
- `app/helpers/icon_paths.py` v1.1.0 — nieuwe `sys._MEIPASS`-branch
  vóór de omhoog-zoeklus.
- `tests/test_icon_paths.py` v1.2.0 — +2 tests.

### 5.3 Fase 11I.3 — Build-orchestratie opschonen

**Aanleiding:** drie cosmetische punten.

**Oplossing:**
- `build_installer.bat` v2.0.3 — `x64compatible`, robocopy-melding
  verduidelijkt, logging van [4] en [7] naar `build_log.txt`.
- `build_and_publish.ps1` v1.1.0 — standaard J bij "Starten?".
- `.gitignore` — `build_log.txt`.
- `docs/packaging.md` v1.3.0 — §2-tabel en §11 bijgewerkt.

### 5.4 Fase 11I.4 — Certificaatstore-hygiëne

**Aanleiding:** de twee verlopen certificaten in de certificaatstore
waren niet gedocumenteerd.

**Oplossing:**
- `docs/packaging.md` v1.4.0 — nieuwe §4.1 "Certificaatstore-hygiëne".
- `.gitignore` — `signing-certs/`.

### 5.5 Fase 11I.5 — Afronding

- `docs/changelog/nl_NL.md` v1.3.0.
- `docs/changelog/en_US.md` v1.3.0.
- `overdracht.md` v6.5.0 (dit document).
- `WatNu.md` v2.3.0.
- `docs/openvragen.md` v3.6.0.
- `docs/packaging.md` v1.5.0 (alleen changelog-regel).

### 5.6 Baseline

| Sub-fase | Baseline vóór | Baseline ná | Nieuw |
|---|---|---|---|
| 11I.1 | 1546 | 1546 | 0 |
| 11I.2 | 1546 | 1548 | +2 |
| 11I.3 | 1548 | 1548 | 0 |
| 11I.4 | 1548 | 1548 | 0 |
| 11I.5 | 1548 | **1548** | 0 |

**Totaal 11I.1 t/m 11I.5:** 1546 → 1548 (+2 tests).

### 5.7 Gewijzigde bestanden sinds 6.4.0

| Bestand | Versie / status |
|---|---|
| `requirements.txt` | v1.0.0 → **v1.1.0** |
| `app/helpers/icon_paths.py` | v1.0.0 → **v1.1.0** |
| `tests/test_icon_paths.py` | v1.1.0 → **v1.2.0** (+2 tests) |
| `build_installer.bat` | v2.0.1 → **v2.0.3** |
| `build_and_publish.ps1` | v1.0.0 → **v1.1.0** |
| `.gitignore` | bijgewerkt |
| `docs/future_tools.md` | §5 bijgewerkt |
| `docs/packaging.md` | v1.0.0 → **v1.5.0** |
| `docs/changelog/nl_NL.md` | → **v1.3.0** |
| `docs/changelog/en_US.md` | → **v1.3.0** |
| `overdracht.md` | → **v6.5.0** |
| `WatNu.md` | → **v2.3.0** |
| `docs/openvragen.md` | → **v3.6.0** |

### 5.8 Teststatus

**Baseline: 1548 passed.** Was 1546 vóór 11I.2. De toename is +2
tests in `test_icon_paths.py`. De suite draait in ~200 s.

### 5.9 Bekende beperkingen (bijgewerkt)

Onveranderd t.o.v. v6.4.0, maar de hardcoded kleuren in
`analysis_screen.py` en `history_screen.py` zijn **opgelost** in
11H.4 en 11H.5. Wat nog rest:

- **`QApplication.setStyleSheet` is verboden** behalve in `main.py`
  bij opstart. Gebruik `self.setStyleSheet(...)` op het venster.
- **`esr_test_screen.py` en `documentation_screen.py`** bevatten nog
  geen thema-afhankelijke kleuren. Als een latere fase daar iets aan
  verandert, krijgen die schermen dezelfde `theme`-parameter als
  `AnalysisScreen` en `HistoryScreen`.
- **Publiek vertrouwd (EV-)certificaat** — structurele oplossing.
- **Fallback timestamp-server** — single point of failure.

---

## 6. OPENSTAANDE VRAGEN VOOR DE NIEUWE CHAT

Zie `docs/openvragen.md` v3.6.0 voor de volledige, levende lijst.
Samenvatting van de belangrijkste punten voor fase 12:

- §2.28 — export/import tussen toestellen.
- §2.14 — Rapportage: scope "filters" in de Rapportage-GUI.
- §11 packaging — publiek vertrouwd (EV-)certificaat;
  fallback timestamp-server.

Opgelost in 11I.1: §2.16 (pandas/numpy pins heroverwegen).
Opgelost in 11I.2: §2.20 (deel: relatief `icon_path`).
Opgelost in 11I.3: §2.20 (deel: `Architecture identifier "x64"`,
`[rename] Fallback via robocopy`, `build_log.txt`).
Opgelost in 11I.4: §2.20 (deel: certificaten opruimen).

**§2.16 en §2.20 zijn nu volledig opgelost.**

---

## 7. TESTSTATUS — BASELINE EN TESTSTRUCTUUR

**Datum:** 2026-10-22
**Baseline:** 1548 passed
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

**Voor fase 12 (AI-extractie uit fabrikantdocumenten):**

De exacte bestanden hangen af van de sub-fase-indeling van fase 12.
Vraag die eerst na. Waarschijnlijk betrokken:

- `app/documentation/pdf_extract.py`, `docx_extract.py`,
  `xlsx_extract.py`, `url_fetch.py`
- `app/documentation/import_service.py`
- `app/documentation/import_models.py`
- `docs/documentation_import.md`
- Nieuwe AI-module (naam nog te bepalen)

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