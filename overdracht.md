# OVERDRACHT — Electronics Diagnostic Tool Hub / ESR Tester

**Versie overdracht:** 6.4.0
**Datum:** 2026-10-21
**Auteur:** Bart Bossuyt
**Vorige versie:** 6.3.0 (2026-10-21)
**Doel:** volledig overdrachtsdocument voor een nieuwe ChatGPT-sessie of
nieuwe ontwikkelaar. Bevat projectstaat, architectuur, regels, changelog,
teststructuur en startprompt. Alles in één bestand.

**Huidige baseline:** 1546 passed
**Laatste afgeronde fase:** 11H.5 — detail-HTML en release-notes per thema
**Volgende fase:** 11I — Build en cosmetica

---

## INHOUD

1. Startprompt (lees dit eerst)
2. Context — projectstaat en architectuur
3. Kernregels — bindende afspraken
4. Stappenplan — chronologisch overzicht
5. Wat is nieuw sinds versie 6.3.0
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
- Baseline: **1546 passed**.
- Laatste afgeronde fase: **11H.5 — detail-HTML en release-notes per
  thema** (2026-10-21). Daarmee is **11H volledig afgerond**
  (11H.1 t/m 11H.5).
- Volgende fase: **11I — Build en cosmetica**.

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
| Huidige baseline | **1546 passed** |
| Laatste afgeronde fase | 11H.5 — detail-HTML en release-notes per thema |
| Volgende fase | 11I — Build en cosmetica |

### 2.2 Huidige applicatiearchitectuur

Zie v6.0.0 §2.2 voor de volledige architectuurbeschrijving. Nieuw
sinds v6.3.0:

**Gewijzigd in 11H.4:**
- `app/gui/analysis_screen.py` (v1.6.3 → **v1.7.0**) — nieuwe
  keyword-only parameter `theme` (default `"dark"`, genormaliseerd);
  nieuwe module-level dict `CHART_COLORS` met per thema alle
  voorheen hardcoded chart-kleuren (chart-achtergrond, as-labels,
  grid, lijn, scatter-rand, neutrale scatter, state-label); nieuwe
  `apply_theme(theme)`-methode; `_build_ui`, `_prepare_chart`,
  `_replace_chart_empty`, `_draw_time_series` en `_draw_scatter`
  halen alle kleuren uit `CHART_COLORS[self.theme]`.
- `app/gui/main_window.py` (v2.22.0 → **v2.22.1**) —
  `AnalysisScreen(taal=..., theme=self.theme, ...)` bij constructie;
  `_apply_settings` roept `analysis_page.apply_theme(self.theme)` aan
  bij een themawissel.
- `tests/test_analysis_screen_theme.py` (nieuw, **v1.0.0**) — 11 tests.

**Gewijzigd in 11H.5:**
- `app/gui/history_screen.py` (v1.17.1 → **v1.18.0**) — nieuwe
  keyword-only parameter `theme`; nieuwe module-level dict
  `DETAIL_HTML_COLORS` met per thema de detail-HTML-kleuren; nieuwe
  `apply_theme(theme)`-methode; `_show_detail_dialog` gebruikt de
  per-thema `QTextBrowser`-stylesheet; `state_label`-kleur volgt het
  thema.
- `app/gui/main_window.py` (v2.22.1 → **v2.22.2**) —
  `HistoryScreen(taal=..., theme=self.theme, ...)` bij constructie;
  `_apply_settings` roept `history_page.apply_theme(self.theme)` aan
  bij een themawissel; `_toon_release_notes_dialoog` gebruikt een
  thema-afhankelijke `QTextBrowser`-stijl; `_markdown_naar_html`
  krijgt optionele `body_bg`/`body_fg` (default donker,
  backward-compat).
- `tests/test_history_screen_theme.py` (nieuw, **v1.0.0**) — 11 tests.

**Samenvatting van 11H.1 t/m 11H.5 (allemaal afgerond):**

| Onderdeel | Bestand | Versie |
|---|---|---|
| Licht + donker stylesheet | `app/gui/styles.py` | v1.7.0 |
| Thema-validatie | `app/config/settings.py` | v1.8.0 |
| Thema-keuze in Settings | `app/gui/dialogs/settings_dialog.py` | v1.7.0 |
| Thema-parameter op ToolHubWindow | `app/gui/main_window.py` | v2.22.2 |
| Thema bij opstart | `main.py` | v1.6.0 |
| Chart-kleuren per thema | `app/gui/analysis_screen.py` | v1.7.0 |
| Detail-HTML per thema | `app/gui/history_screen.py` | v1.18.0 |

### 2.3 Belangrijke recente bugfixes

Zie v6.0.0 §2.3. Nieuw sinds v6.3.0: geen. 11H.4 en 11H.5 verliepen
zonder noemenswaardige problemen.

Zie v6.3.0 §2.3 voor de bugfixes uit 11H.3 (v2.21.1, v2.21.2,
v2.21.3, v2.22.0).

### 2.4 Openstaande werkpunten en fase 11-indeling

Volgende fase is **11I — Build en cosmetica**.

Sub-fase-indeling fase 11 (geactualiseerd):

| Sub-fase | Onderwerp | Status |
|---|---|---|
| **11A** | Export, import en selectie | ✅ afgerond |
| **11B** | Betrouwbaarheidsregel herzien (§2.26) | ✅ afgerond |
| **11C** | Iconen voor alle vensters (§2.27) | ✅ afgerond |
| **11D** | i18n-menging in Diagnose/Result en Resultaatdetails (§2.21) | ✅ afgerond |
| **11E** | Async netwerk | ✅ afgerond |
| **11F.1 t/m 11F.4** | Documentatie-uitbreiding | ✅ afgerond |
| **11G.1 t/m 11G.7** | Visueel donker thema | ✅ afgerond |
| **11H.1** | Light theme in styles.py | ✅ afgerond |
| **11H.2** | Thema-keuze in Settings | ✅ afgerond |
| **11H.3** | Thema-parameter op ToolHubWindow + live wissel | ✅ afgerond |
| **11H.4** | Chart-kleuren per thema in AnalysisScreen | ✅ afgerond |
| **11H.5** | Detail-HTML en release-notes per thema | ✅ afgerond |
| **11I** | Build en cosmetica | **Volgende** |

Daarna volgen fase 12 (AI-extractie), 13 (menselijke validatie),
14 (fabrikantdata koppelen) en 15 (Resistor).

### 2.5 Werkafspraken voor een nieuwe sessie

Onveranderd t.o.v. v6.0.0, aangevuld met de `conftest.py`-regel uit §1.

---

## 3. KERNREGELS — BINDENDE AFSPRAKEN

Onveranderd t.o.v. v5.9.0, behalve:

- **`conftest.py`**: sinds 11H.3 is er een minimale `conftest.py`
  toegestaan en verplicht voor GUI-tests. Die bevat uitsluitend de
  `QT_QPA_PLATFORM=offscreen`-registratie en de autouse-opruimfixture.
  Geen projectimports, geen `qtbot`, geen `pytest-qt`.
- **`setStyleSheet` op het venster, niet op de `QApplication`.** De
  enige uitzondering is de globale `apply_theme(app, thema)` in
  `main.py` bij opstart, voor dialogen zonder parent.
- **Thema doorgeven aan schermen**: schermen met thema-afhankelijke
  kleuren krijgen een keyword-only `theme`-parameter en een
  `apply_theme(theme)`-methode. Sinds 11H.4 heeft `AnalysisScreen`
  die; sinds 11H.5 ook `HistoryScreen`.

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
| **11I** | **Build en cosmetica** | **Volgende** |
| 12 | AI-extractie uit fabrikantdocumenten | Gepland |
| 13 | Menselijke validatie van AI-output | Gepland |
| 14 | Goedgekeurde fabrikantdata koppelen aan assessment | Gepland |
| 15 | Tweede diagnosetool — Resistor | Gepland |

---

## 5. WAT IS NIEUW SINDS VERSIE 6.3.0

### 5.1 Fase 11H.4 — Chart-kleuren per thema in AnalysisScreen

**Aanleiding:** `analysis_screen.py` bevatte nog hardcoded donkere
kleuren (`#1E1E1E`, `#F0F0F0`, `#3A3A3A`, `_LINE_COLOR = "#4AA3FF"`,
`QChart`-achtergrond, `chart_view`-stylesheet). Bij een licht thema
werd de chart donker op een licht venster.

**Oplossing:**

- `analysis_screen.py` v1.7.0 — nieuwe keyword-only parameter `theme`;
  nieuwe module-level dict `CHART_COLORS` met per thema alle
  chart-kleuren; nieuwe `apply_theme(theme)`-methode die het thema
  bijwerkt en de chart-kleuren toepast zonder de reeksen te wissen.
  Alle hardcoded kleuren in `_build_ui`, `_prepare_chart`,
  `_replace_chart_empty`, `_draw_time_series` en `_draw_scatter`
  komen nu uit `CHART_COLORS[self.theme]`. `_category_color` gebruikt
  `self._colors()["scatter_neutral"]` voor `None`-categorie.
- `main_window.py` v2.22.1 — `AnalysisScreen(taal=..., theme=...)` bij
  constructie; `analysis_page.apply_theme(self.theme)` bij een
  themawissel.
- `tests/test_analysis_screen_theme.py` (nieuw, 11 tests) — dekt
  thema-parameter, `CHART_COLORS`, chart-achtergrond, state-label,
  `apply_theme()`-gedrag en axis-kleuren.

### 5.2 Fase 11H.5 — Detail-HTML en release-notes per thema

**Aanleiding:** `history_screen.py` had in `_show_detail_dialog` een
hardcoded `QTextBrowser`-stylesheet (`#1E1E1E` / `#F0F0F0`) en
`state_label` `color: #C8C8C8`. `main_window._toon_release_notes_dialoog`
had hetzelfde probleem. Bij een licht thema werden deze tekstvakken
donker op een licht venster.

**Oplossing:**

- `history_screen.py` v1.18.0 — nieuwe keyword-only parameter `theme`;
  nieuwe module-level dict `DETAIL_HTML_COLORS` met per thema de
  detail-HTML-kleuren (achtergrond, tekst, heading, muted, tabel-rand,
  state-label); nieuwe `apply_theme(theme)`-methode;
  `_show_detail_dialog` gebruikt de per-thema `QTextBrowser`-stylesheet;
  `state_label`-kleur volgt het thema.
- `main_window.py` v2.22.2 — `HistoryScreen(taal=..., theme=...)` bij
  constructie; `history_page.apply_theme(self.theme)` bij een
  themawissel; `_toon_release_notes_dialoog` gebruikt een
  thema-afhankelijke `QTextBrowser`-stijl; `_markdown_naar_html` krijgt
  optionele `body_bg`/`body_fg` (default donker, backward-compat).
- `tests/test_history_screen_theme.py` (nieuw, 11 tests) — dekt
  thema-parameter, `DETAIL_HTML_COLORS`, state-label,
  `apply_theme()`-gedrag en de detail-HTML-stylesheet in beide thema's.

### 5.3 Baseline

| Sub-fase | Baseline vóór | Baseline ná | Nieuw |
|---|---|---|---|
| 11H.1 | 1494 | 1502 | +8 |
| 11H.2 | 1502 | 1514 | +6 |
| 11H.3 | 1514 | 1524 | +10 |
| 11H.4 | 1524 | 1535 | +11 |
| 11H.5 | 1535 | **1546** | +11 |

**Totaal 11H.1 t/m 11H.5:** 1494 → 1546 (+52 tests).

### 5.4 Gewijzigde bestanden sinds 6.3.0

| Bestand | Versie / status |
|---|---|
| `app/gui/analysis_screen.py` | v1.6.3 → **v1.7.0** |
| `app/gui/history_screen.py` | v1.17.1 → **v1.18.0** |
| `app/gui/main_window.py` | v2.22.0 → **v2.22.2** |
| `tests/test_analysis_screen_theme.py` | nieuw, **v1.0.0** (11 tests) |
| `tests/test_history_screen_theme.py` | nieuw, **v1.0.0** (11 tests) |

### 5.5 Teststatus

**Baseline: 1546 passed.** Was 1524 vóór 11H.4. De toename is +22
tests (11 in `test_analysis_screen_theme.py`, 11 in
`test_history_screen_theme.py`). De suite draait in ~200 s.

### 5.6 Bekende beperkingen (bijgewerkt)

Onveranderd t.o.v. v6.3.0, maar de hardcoded kleuren in
`analysis_screen.py` en `history_screen.py` zijn nu **opgelost**. Wat
nog rest:

- **`QApplication.setStyleSheet` is verboden** behalve in `main.py`
  bij opstart. Gebruik `self.setStyleSheet(...)` op het venster.
- **`esr_test_screen.py` en `documentation_screen.py`** bevatten nog
  geen thema-afhankelijke kleuren. Als 11I daar iets aan verandert,
  krijgen die schermen dezelfde `theme`-parameter als
  `AnalysisScreen` en `HistoryScreen`.

---

## 6. OPENSTAANDE VRAGEN VOOR DE NIEUWE CHAT

Zie `docs/openvragen.md` v3.5.0 voor de volledige, levende lijst.
Samenvatting van de belangrijkste punten voor fase 11I:

- §2.16 — pandas/numpy pins heroverwegen (11I).
- §2.20 — relatief `icon_path`, `Architecture identifier "x64"`,
  `[rename] Fallback via robocopy`, `build_log.txt`, certificaten
  opruimen (11I).
- §2.28 — export/import tussen toestellen.
- §2.14 — Rapportage: scope "filters" in de Rapportage-GUI.

Opgelost in 11H.1: §4.4 (deel: styles.py).
Opgelost in 11H.2: §4.4 (deel: Settings).
Opgelost in 11H.3: §4.4 (deel: ToolHubWindow + live wissel +
performance).
Opgelost in 11H.4: §4.4 (deel: chart-kleuren in AnalysisScreen).
Opgelost in 11H.5: §4.4 (deel: detail-HTML en release-notes per
thema). **§4.4 is nu volledig opgelost.**

---

## 7. TESTSTATUS — BASELINE EN TESTSTRUCTUUR

**Datum:** 2026-10-21
**Baseline:** 1546 passed
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

**Voor fase 11I (Build en cosmetica):**

De exacte bestanden hangen af van de sub-fase-indeling van 11I. Vraag
die eerst na. Waarschijnlijk betrokken:

- `build_and_publish.ps1`, `build_installer.bat`, `publish.ps1` —
  build-orchestratie
- `ESR_Tester.spec` — PyInstaller-specificatie
- `requirements.txt` — pandas/numpy pins
- `docs/packaging.md` — build-documentatie
- `app/helpers/icon_paths.py` — relatief `icon_path`
- `docs/openvragen.md` §2.16, §2.20 — de concrete punten

**Voor fase 12 (AI-extractie) — nog niet nu:**

- `app/documentation/docx_extract.py`, `pdf_extract.py`,
  `xlsx_extract.py`, `url_fetch.py`
- `app/documentation/import_service.py`

De exacte bestanden hangen af van de sub-fase-indeling. Vraag die
eerst na.

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