# OVERDRACHT — Electronics Diagnostic Tool Hub / ESR Tester

**Versie overdracht:** 5.5.0
**Datum:** 2026-10-16
**Auteur:** Bart Bossuyt
**Vorige versie:** 5.4.0 (2026-10-16)
**Doel:** volledig overdrachtsdocument voor een nieuwe ChatGPT-sessie of
nieuwe ontwikkelaar. Bevat projectstaat, architectuur, regels, changelog,
teststructuur en startprompt. Alles in één bestand.

**Huidige baseline:** 1358 passed
**Laatste afgeronde fase:** 11C — iconen voor alle vensters
**Volgende fase:** 11D — i18n-menging oplossen

---

## INHOUD

1. Startprompt (lees dit eerst)
2. Context — projectstaat en architectuur
3. Kernregels — bindende afspraken
4. Stappenplan — chronologisch overzicht
5. Wat is nieuw sinds versie 5.4.0
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
- Baseline: **1358 passed**.
- Laatste afgeronde fase: **11C — iconen voor alle vensters**
  (2026-10-16).
- Volgende fase: **11D — i18n-menging oplossen**.

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
- **De ArticleSearch-flow is de bewezen build-flow.**
- **Geen aannames over de volgende fase:** vraag het na.
- **Nooit een GitHub-token in een getrackt bestand, chat of
  context-document zetten.**
- **Bij een verschil tussen de gedocumenteerde baseline en de werkelijke
  `pytest -q`-uitvoer: eerst uitzoeken, dan pas doorgaan. Nooit stil
  een nieuwe fase starten op een ongeverifieerde baseline.**

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
| Huidige baseline | **1358 passed** |
| Laatste afgeronde fase | 11C — iconen voor alle vensters |
| Volgende fase | 11D — i18n-menging oplossen |

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

Zie v5.0.0 en v5.1.0 van dit document voor de volledige
architectuurbeschrijving.

### 2.3 Belangrijke recente bugfixes

Zie v5.0.0, v5.1.0 en v5.2.0. Nieuw sinds v5.4.0: geen.

### 2.4 Openstaande werkpunten en fase 11-indeling

Volgende fase is **11D — i18n-menging oplossen**. De scope staat in
`docs/openvragen.md` §2.21.

Sub-fase-indeling fase 11 (geactualiseerd):

| Sub-fase | Onderwerp | Status |
|---|---|---|
| **11A** | Export, import en selectie: export respecteert selectie, visuele selectie in Analyse, rapport-scope "selectie", menu-item disabled zonder selectie, mapvoorkeuren respecteren | **✅ 11A.1 + 11A.2 + 11A.3 afgerond** |
| **11B** | Betrouwbaarheidsregel herzien (§2.26) — onderscheid inhoudelijk vs. administratief | **✅ afgerond** |
| **11C** | Iconen voor alle vensters (§2.27) | **✅ afgerond** |
| **11D** | i18n-menging in Diagnose/Result en Resultaatdetails oplossen (§2.21) | **Volgende** |
| 11E | Async netwerk: async URL-fetch (§2.6), async `fetch_release_notes()` (§2.24), drie-knoppenmelding forceren voor QA (§2.24) | Gepland |
| 11F | Documentatie-uitbreiding: reden bij archiveren, filter gearchiveerde, bulk-edit, bulk-statuswijziging, datum-parsing verfijnen, cosmetische opruiming i18n-keys (§2.6, §2.14) | Gepland |
| 11G | Visueel donker thema: checkbox-zichtbaarheid (§2.21), cosmetische scrollbar Word-samenvatting (§2.9), Analyse-pagina cosmetica (as-schaling, tickformaat, zoom/pan) (§2.11) | Gepland |
| 11H | Light theme (§4.4) | Gepland |
| 11I | Build en cosmetica: `Architecture identifier "x64"` (§2.20), `[rename] Fallback via robocopy` (§2.20), `build_log.txt` (§2.20), externe links changelog (§2.24), release-notes tabellen (§2.24), certificaten opruimen (§2.20), pandas/numpy pins heroverwegen (§2.16) | Gepland |

Daarna volgen fase 12 (AI-extractie), 13 (menselijke validatie),
14 (fabrikantdata koppelen) en 15 (Resistor).

### 2.5 Werkafspraken voor een nieuwe sessie

Onveranderd t.o.v. v5.4.0. Zie §9.

---

## 3. KERNREGELS — BINDENDE AFSPRAKEN

Onveranderd t.o.v. v5.4.0. Zie §3.1 t/m §3.4 van dat document.

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
| **11B** | **Betrouwbaarheidsregel herzien** | **✅ afgerond** |
| **11C** | **Iconen voor alle vensters** | **✅ afgerond** |
| **11D** | i18n-menging oplossen | **Volgende** |
| 11E | Async netwerk | Gepland |
| 11F | Documentatie-uitbreiding | Gepland |
| 11G | Visueel donker thema | Gepland |
| 11H | Light theme | Gepland |
| 11I | Build en cosmetica | Gepland |
| 12 | AI-extractie uit fabrikantdocumenten | Gepland |
| 13 | Menselijke validatie van AI-output | Gepland |
| 14 | Goedgekeurde fabrikantdata koppelen aan assessment | Gepland |
| 15 | Tweede diagnosetool — Resistor | Gepland |

---

## 5. WAT IS NIEUW SINDS VERSIE 5.4.0

### 5.1 Fase 11C — iconen voor alle vensters

**Aanleiding (§2.27 in `docs/openvragen.md`):** de applicatie had geen
icoon op de vensters. Het bestaande `logo.ico` was niet mooi en er was
geen set thematische iconen voor de hub-knoppen, diagnose-knoppen en
menu-items.

**Oplossing:** één applicatie-icoon plus twaalf thematische iconen,
alle in `assets/icons/`, met een pure helper die de paden bepaalt en
stil terugvalt op `None` als een icoon ontbreekt.

**Gewijzigde bestanden:**

| Bestand | Versie / status |
|---|---|
| `app/helpers/icon_paths.py` | **nieuw**, v1.0.0 |
| `scripts/genereer_placeholders.py` | **nieuw**, v1.0.0 |
| `main.py` | v1.4.0 → v1.5.0 |
| `app/gui/main_window.py` | v2.16.0 → v2.17.0 |
| `app/gui/esr_test_screen.py` | v1.12.0 → v1.13.0 |
| `app/gui/dialogs/report_dialog.py` | v1.4.0 → v1.5.0 |
| `app/gui/dialogs/settings_dialog.py` | v1.5.0 → v1.6.0 |
| `app/gui/dialogs/search_help_dialog.py` | v1.0.1 → v1.1.0 |
| `app/gui/dialogs/import_wizard_dialog.py` | v1.8.0 → v1.9.0 |
| `app/gui/dialogs/change_status_dialog.py` | v1.0.0 → v1.1.0 |
| `app/gui/dialogs/edit_metadata_dialog.py` | v1.0.0 → v1.1.0 |
| `app/gui/dialogs/duplicate_source_dialog.py` | v1.0.0 → v1.1.0 |
| `assets/icons/README.md` | volledig herschreven |
| `tests/test_icon_paths.py` | **nieuw**, 16 tests |
| `tests/test_main_icon.py` | **nieuw**, 1 test |
| `tests/test_main_window_help_menu.py` | v1.2.0 → v1.3.0, +1 test |
| `tests/test_main_window_report_menu.py` | v1.3.0 → v1.4.0, +1 test |
| `docs/changelog/nl_NL.md` | 11C-subsectie toegevoegd |
| `docs/changelog/en_US.md` | 11C-subsectie toegevoegd |
| `docs/help/nl_NL.md` | Ctrl+A toegevoegd onder "Globaal" |
| `docs/help/en_US.md` | Ctrl+I, Ctrl+P, Ctrl+A aangevuld |

**Nieuwe API in `icon_paths.py`:**

- `iconenmap(projectroot=None)` — pad naar `assets/icons/`.
- `icoon_pad(naam, projectroot=None, extensie="png")` — pad naar één
  icoon of `None`.
- `applicatie_icoon_pad(projectroot=None)` — fallback-keten
  `app.png` → `logo.ico` → `None`.
- `laad_icoon(naam, projectroot=None)` — `QIcon` of `None`.
- `applicatie_icoon(projectroot=None)` — `QIcon` van het
  applicatie-icoon of `None`.
- `zet_venster_icoon(widget, projectroot=None)` — zet het
  applicatie-icoon op een `QWidget`.

**Geen wijziging:** `ESR_Tester.spec` en de Inno Setup `.iss`
verwijzen nog steeds naar `assets/icons/logo.ico`. Dat bestand is
vervangen door een nieuw ICO met dezelfde naam, niet hernoemd.

**Geen nieuwe i18n-keys.** 11C voegt geen GUI-tekst toe.

### 5.2 Baselinecorrectie 11C

Tijdens 11C is de baseline gecorrigeerd van **1339** naar **1358**.
De toename is **+19 tests**: 16 in `test_icon_paths.py`, 1 in
`test_main_icon.py`, 1 in `test_main_window_help_menu.py`, 1 in
`test_main_window_report_menu.py`. In de eerste changelog-versie van
11C stond abusievelijk +18; dat is later gecorrigeerd naar +19.

### 5.3 Gewijzigde bestanden sinds 5.4.0

Zie de tabel in §5.1.

### 5.4 Teststatus

**Baseline: 1358 passed.** Was 1339 vóór 11C. De toename is +19 tests,
alle additief. Geen bestaande test is inhoudelijk gewijzigd behalve de
twee menu-bestanden, die elk één nieuwe test kregen.

### 5.5 Bekende beperkingen (bijgewerkt)

- De icoonbestanden zijn **placeholders**. Ze zijn bewust eenvoudig en
  vlak. Vervang ze door definitieve ontwerpen met dezelfde
  bestandsnamen; de code hoeft dan niet te wijzigen. Zie
  `assets/icons/README.md`.
- `test_icon_paths.py` gebruikt een **lokale `_app`-fixture** met
  `@pytest.fixture(scope="module")`. Dat is afwijkend van de
  projectafspraak (geen fixture, `QApplication` lokaal ophalen). Het
  werkt, maar is een inconsistentie om in een latere fase op te
  ruimen.

---

## 6. OPENSTAANDE VRAGEN VOOR DE NIEUWE CHAT

Zie `docs/openvragen.md` v2.8.0 voor de volledige, levende lijst.
Samenvatting van de belangrijkste punten voor fase 11D:

- §2.21 — i18n-menging in Diagnose/Result en Resultaatdetails.
- §2.20 — relatief `icon_path` verfijnen, `Architecture identifier "x64"`,
  `[rename] Fallback via robocopy`, `build_log.txt`, certificaten opruimen.
- §2.6 — diverse documentatie- en UX-punten.
- §2.9 — cosmetische scrollbar in Word-samenvatting.
- §2.11 — Analyse-pagina: as-schaling, tickformaat, zoom/pan.
- §2.14 — Rapportage: scope "filters" in de Rapportage-GUI.
- §2.16 — pandas/numpy pins heroverwegen.
- §2.24 — update-melding cosmetica.
- §2.28 — export/import tussen toestellen.
- §4.4 — light theme.

Opgelost in 11B:
- §2.26 — betrouwbaarheidsregel verbergt goede resultaten.

Opgelost in 11C:
- §2.27 — alle vensters een gepast icoon.

---

## 7. TESTSTATUS — BASELINE EN TESTSTRUCTUUR

**Datum:** 2026-10-16
**Baseline:** 1358 passed
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

**Voor fase 11D (i18n-menging oplossen):**

- `app/gui/esr_test_screen.py` — de resultaatweergave en
  `_build_result_html()`
- `app/services/assessment_service.py` — de bron van de mengeling
  (`toelichting`, `redenen`, `waarschuwingen`, `aanbevolen_vervolgstap`)
- `i18n/locales/nl_NL/esr.json`
- `i18n/locales/en_US/esr.json`
- `i18n/locales/nl_NL/app.json`
- `i18n/locales/en_US/app.json`
- `app/helpers/report_render.py` — als rapporten ook mengeling tonen
- `tests/test_esr_context_documentation.py`
- `tests/test_i18n_app_translations.py`
- `tests/test_gui_language_switch.py`

Enzovoort, afhankelijk van de gekozen sub-fase.

---

## 9. WERKAFSPRAKEN IN EEN NIEUWE SESSIE

Onveranderd t.o.v. v5.4.0. Toevoeging:

- **Bij het leveren van `.md`-bestanden: bij twijfel altijd
  viervoudige backticks.**
- **Bij een verschil tussen de gedocumenteerde baseline en de werkelijke
  `pytest -q`-uitvoer: eerst uitzoeken, dan pas doorgaan. Nooit stil
  een nieuwe fase starten op een ongeverifieerde baseline.**