# OVERDRACHT — Electronics Diagnostic Tool Hub / ESR Tester

**Versie overdracht:** 6.1.0
**Datum:** 2026-10-20
**Auteur:** Bart Bossuyt
**Vorige versie:** 6.0.0 (2026-10-20)
**Doel:** volledig overdrachtsdocument voor een nieuwe ChatGPT-sessie of
nieuwe ontwikkelaar. Bevat projectstaat, architectuur, regels, changelog,
teststructuur en startprompt. Alles in één bestand.

**Huidige baseline:** 1494 passed
**Laatste afgeronde fase:** 11G.7 — filter-checkbox zichtbaarheid
**Volgende fase:** 11H — light theme

---

## INHOUD

1. Startprompt (lees dit eerst)
2. Context — projectstaat en architectuur
3. Kernregels — bindende afspraken
4. Stappenplan — chronologisch overzicht
5. Wat is nieuw sinds versie 6.0.0
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
- Baseline: **1494 passed**.
- Laatste afgeronde fase: **11G.7 — filter-checkbox zichtbaarheid**
  (2026-10-20). Daarmee is **11G volledig afgerond** (11G.1 t/m 11G.7).
- Volgende fase: **11H — light theme**.

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
- **Testtelling bijhouden per fase:** tel nieuwe tests per bestand
  (gerichte `pytest --collect-only -q`), niet op basis van een schatting.
  De som van de betrokken bestanden moet overeenkomen met de
  volledige `pytest -q`. Bij afwijking: eerst uitzoeken, dan doorgaan.
- **Bij het herschrijven van een test-sectie: `Compare-Object` tegen
  de vorige versie.** Dit heeft in 11F.2 twee per ongeluk verwijderde
  tests opgespoord.

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
| Huidige baseline | **1494 passed** |
| Laatste afgeronde fase | 11G.7 — filter-checkbox zichtbaarheid |
| Volgende fase | 11H — light theme |

### 2.2 Huidige applicatiearchitectuur

Zie v6.0.0 §2.2 voor de volledige architectuurbeschrijving. Nieuw
sinds v6.0.0:

**Gewijzigd in 11G.7:**
- `app/gui/styles.py` (v1.5.0 → **v1.6.0**) — `QGroupBox::indicator`
  duidelijker zichtbaar in donker thema. Unchecked-state: achtergrond
  `#3C3C3C` (was `#2A2A2A`), rand 2px `#B0B0B0` (was 1px `#8A8A8A`).
  Checked-state: blauw `#0078D7` met 2px rand `#4AA3FF`. Hover en
  disabled consistent. Lost het visuele probleem op waarbij de
  checkbox links van "Filters" nauwelijks zichtbaar was.
- `tests/test_styles.py` (v1.1.0 → **v1.2.0**) — drie nieuwe tests.

### 2.3 Belangrijke recente bugfixes

Zie v6.0.0 §2.3. Nieuw sinds v6.0.0: geen functionele bugfixes,
alleen de visuele verbetering in 11G.7.

### 2.4 Openstaande werkpunten en fase 11-indeling

Volgende fase is **11H — light theme**.

Sub-fase-indeling fase 11 (geactualiseerd):

| Sub-fase | Onderwerp | Status |
|---|---|---|
| **11A** | Export, import en selectie | ✅ afgerond |
| **11B** | Betrouwbaarheidsregel herzien (§2.26) | ✅ afgerond |
| **11C** | Iconen voor alle vensters (§2.27) | ✅ afgerond |
| **11D** | i18n-menging in Diagnose/Result en Resultaatdetails (§2.21) | ✅ afgerond |
| **11E** | Async netwerk | ✅ afgerond |
| **11F.1** | Archiefreden | ✅ afgerond |
| **11F.2** | Statusfilter | ✅ afgerond |
| **11F.3** | Bulk-edit en bulk-statuswijziging | ✅ afgerond |
| **11F.4** | Datum-parsing + cosmetische punten + i18n-opruiming | ✅ afgerond |
| **11G.1** | Checkbox- en radio-zichtbaarheid in donker thema | ✅ afgerond |
| **11G.2** | Donkere scrollbar in Word-samenvatting | ✅ afgerond |
| **11G.3** | Analyse: as-schaling en tickformaat | ✅ afgerond |
| **11G.4** | Analyse: zoom/pan | ✅ afgerond |
| **11G.5** | Analyse: klikbare datapunten + selectie-gedreven analyse | ✅ afgerond |
| **11G.6** | Afsluiten via menu sluit de app, niet het venster | ✅ afgerond |
| **11G.7** | Filter-checkbox zichtbaarheid | ✅ afgerond |
| **11H** | Light theme | **Volgende** |
| 11I | Build en cosmetica | Gepland |

Daarna volgen fase 12 (AI-extractie), 13 (menselijke validatie),
14 (fabrikantdata koppelen) en 15 (Resistor).

### 2.5 Werkafspraken voor een nieuwe sessie

Onveranderd t.o.v. v6.0.0.

---

## 3. KERNREGELS — BINDENDE AFSPRAKEN

Onveranderd t.o.v. v5.9.0. Zie §3.1 t/m §3.4 van dat document.

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
| 11E | Async netwerk | ✅ afgerond |
| 11F.1 t/m 11F.4 | Documentatie-uitbreiding | ✅ afgerond |
| 11G.1 t/m 11G.7 | Visueel donker thema | ✅ afgerond |
| **11H** | **Light theme** | **Volgende** |
| 11I | Build en cosmetica | Gepland |
| 12 | AI-extractie uit fabrikantdocumenten | Gepland |
| 13 | Menselijke validatie van AI-output | Gepland |
| 14 | Goedgekeurde fabrikantdata koppelen aan assessment | Gepland |
| 15 | Tweede diagnosetool — Resistor | Gepland |

---

## 5. WAT IS NIEUW SINDS VERSIE 6.0.0

### 5.1 Fase 11G.7 — Filter-checkbox zichtbaarheid

**Aanleiding:** de checkbox links van het woord "Filters" in de
Analyse- en Historiek-pagina (de checkable `QGroupBox`) was nauwelijks
zichtbaar in het donkere thema. Het indicator-vierkantje had een
achtergrond (`#2A2A2A`) die bijna gelijk was aan de groupbox-
achtergrond (`#2D2D30`), en een dunne rand (1px `#8A8A8A`) die wegviel
naast de groupbox-rand.

**Oplossing:**

- `styles.py` v1.6.0 — `QGroupBox::indicator` krijgt een lichtere
  achtergrond (`#3C3C3C`) en een dikkere rand (2px `#B0B0B0`) in
  unchecked-state. Checked-state is blauw (`#0078D7`) met 2px rand
  (`#4AA3FF`). Hover en disabled zijn consistent. Geen wijziging aan
  de GUI-bestanden — alleen `styles.py`.
- `tests/test_styles.py` v1.2.0 — drie nieuwe tests.

### 5.2 Baselinecorrectie 11G.7

| Sub-fase | Baseline vóór | Baseline ná | Nieuw |
|---|---|---|---|
| 11G.7 | 1491 | **1494** | +3 |

**Totaal 11G.1 t/m 11G.7:** 1462 → 1494 (+32 tests).

### 5.3 Gewijzigde bestanden sinds 6.0.0

| Bestand | Versie / status |
|---|---|
| `app/gui/styles.py` | v1.5.0 → **v1.6.0** |
| `tests/test_styles.py` | v1.1.0 → **v1.2.0** (9 → 12 tests) |

### 5.4 Teststatus

**Baseline: 1494 passed.** Was 1491 vóór 11G.7. De toename is +3 tests.

### 5.5 Bekende beperkingen (bijgewerkt)

Onveranderd t.o.v. v6.0.0.

---

## 6. OPENSTAANDE VRAGEN VOOR DE NIEUWE CHAT

Zie `docs/openvragen.md` v3.4.0 voor de volledige, levende lijst.
Samenvatting van de belangrijkste punten voor fase 11H:

- §4.4 — light theme (11H).
- §2.14 — Rapportage: scope "filters" in de Rapportage-GUI.
- §2.16 — pandas/numpy pins heroverwegen (11I).
- §2.20 — relatief `icon_path`, `Architecture identifier "x64"`,
  `[rename] Fallback via robocopy`, `build_log.txt`, certificaten
  opruimen (11I).
- §2.28 — export/import tussen toestellen.

Opgelost in 11B: §2.26.
Opgelost in 11C: §2.27.
Opgelost in 11D: §2.21 (i18n-menging).
Opgelost in 11E: §2.6 (async URL-fetch), §2.24 (async release-notes).
Opgelost in 11F.1: §2.6 (archiefreden).
Opgelost in 11F.2: §2.14 (statusfilter).
Opgelost in 11F.3: bulk-edit en bulk-status.
Opgelost in 11F.4: §4.21, §4.23, i18n-opruiming.
Opgelost in 11G.1: §2.21 (checkbox-zichtbaarheid, focus-states).
Opgelost in 11G.2: §2.9 (scrollbar Word-samenvatting).
Opgelost in 11G.3: §2.11 (as-schaling, tickformaat).
Opgelost in 11G.4: §2.11 (zoom/pan).
Opgelost in 11G.5: §2.21 (klikbare datapunten in Analyse).
Opgelost in 11G.6: nieuwe todo (afsluiten via menu sluit de app).
Opgelost in 11G.7: §2.30 (filter-checkbox zichtbaarheid).

---

## 7. TESTSTATUS — BASELINE EN TESTSTRUCTUUR

**Datum:** 2026-10-20
**Baseline:** 1494 passed
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

Onveranderd t.o.v. v6.0.0 §7.2.

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

**Voor fase 11H (light theme):**

- `app/gui/styles.py` — centrale stijldefinities (v1.6.0)
- `app/gui/main_window.py` — thema-aanpassing (v2.20.0)
- `app/config/settings.py` — `algemeen.thema` (v1.7.0)
- `app/gui/dialogs/settings_dialog.py` — thema-keuze (v1.6.0)
- `tests/test_styles.py` — pure stylesheet-tests (v1.2.0)
- `tests/test_settings.py` — thema-instelling
- `tests/test_settings_dialog.py` — thema-keuze in de dialoog
- `i18n/locales/nl_NL/settings.json`, `i18n/locales/en_US/settings.json`
  — labels voor de thema-keuze

De exacte bestanden hangen af van de sub-fase-indeling van 11H. Vraag
die eerst na.

---

## 9. WERKAFSPRAKEN IN EEN NIEUWE SESSIE

Onveranderd t.o.v. v6.0.0 §9.