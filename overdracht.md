# OVERDRACHT — Electronics Diagnostic Tool Hub / ESR Tester

**Versie overdracht:** 5.4.0
**Datum:** 2026-10-16
**Auteur:** Bart Bossuyt
**Vorige versie:** 5.3.0 (2026-10-16)
**Doel:** volledig overdrachtsdocument voor een nieuwe ChatGPT-sessie of
nieuwe ontwikkelaar. Bevat projectstaat, architectuur, regels, changelog,
teststructuur en startprompt. Alles in één bestand.

**Huidige baseline:** 1339 passed
**Laatste afgeronde fase:** 11B — betrouwbaarheidsregel herzien
**Volgende fase:** 11C — iconen voor alle vensters

---

## INHOUD

1. Startprompt (lees dit eerst)
2. Context — projectstaat en architectuur
3. Kernregels — bindende afspraken
4. Stappenplan — chronologisch overzicht
5. Wat is nieuw sinds versie 5.3.0
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
- Baseline: **1339 passed**.
- Laatste afgeronde fase: **11B — betrouwbaarheidsregel herzien**
  (2026-10-16).
- Volgende fase: **11C — iconen voor alle vensters**.

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
| Huidige versie | `1.1.2` |
| Huidige baseline | **1339 passed** |
| Laatste afgeronde fase | 11B — betrouwbaarheidsregel herzien |
| Volgende fase | 11C — iconen voor alle vensters |

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

Zie v5.0.0 en v5.1.0 van dit document voor de volledige
architectuurbeschrijving.

### 2.3 Belangrijke recente bugfixes

Zie v5.0.0, v5.1.0 en v5.2.0. Nieuw sinds v5.3.0: geen.

### 2.4 Openstaande werkpunten en fase 11-indeling

Volgende fase is **11C — iconen voor alle vensters**. De scope staat in
`docs/openvragen.md` §2.27.

Sub-fase-indeling fase 11 (geactualiseerd):

| Sub-fase | Onderwerp | Status |
|---|---|---|
| **11A** | Export, import en selectie: export respecteert selectie, visuele selectie in Analyse, rapport-scope "selectie", menu-item disabled zonder selectie, mapvoorkeuren respecteren | **✅ 11A.1 + 11A.2 + 11A.3 afgerond** |
| **11B** | Betrouwbaarheidsregel herzien (§2.26) — onderscheid inhoudelijk vs. administratief | **✅ afgerond** |
| **11C** | Iconen voor alle vensters (§2.27), relatief `icon_path` verfijnen (§2.20) | **Volgende** |
| 11D | i18n-menging in Diagnose/Result en Resultaatdetails oplossen (§2.21) | Gepland |
| 11E | Async netwerk: async URL-fetch (§2.6), async `fetch_release_notes()` (§2.24), drie-knoppenmelding forceren voor QA (§2.24) | Gepland |
| 11F | Documentatie-uitbreiding: reden bij archiveren, filter gearchiveerde, bulk-edit, bulk-statuswijziging, datum-parsing verfijnen, cosmetische opruiming i18n-keys (§2.6, §2.14) | Gepland |
| 11G | Visueel donker thema: checkbox-zichtbaarheid (§2.21), cosmetische scrollbar Word-samenvatting (§2.9), Analyse-pagina cosmetica (as-schaling, tickformaat, zoom/pan) (§2.11) | Gepland |
| 11H | Light theme (§4.4) | Gepland |
| 11I | Build en cosmetica: `Architecture identifier "x64"` (§2.20), `[rename] Fallback via robocopy` (§2.20), `build_log.txt` (§2.20), externe links changelog (§2.24), release-notes tabellen (§2.24), certificaten opruimen (§2.20), pandas/numpy pins heroverwegen (§2.16) | Gepland |

Daarna volgen fase 12 (AI-extractie), 13 (menselijke validatie),
14 (fabrikantdata koppelen) en 15 (Resistor).

### 2.5 Werkafspraken voor een nieuwe sessie

Onveranderd t.o.v. v5.3.0. Zie §9.

---

## 3. KERNREGELS — BINDENDE AFSPRAKEN

Onveranderd t.o.v. v5.3.0. Zie §3.1 t/m §3.4 van dat document.

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
| **11C** | Iconen voor alle vensters | **Volgende** |
| 11D | i18n-menging oplossen | Gepland |
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

## 5. WAT IS NIEUW SINDS VERSIE 5.3.0

### 5.1 Fase 11B — betrouwbaarheidsregel herzien

**Aanleiding (§2.26 in `docs/openvragen.md`):** de regel in
`bepaal_eindstatus` gebruikte `betrouwbaarheid.niveau == LAAG` als
trigger voor minimaal `AANDACHTSPUNT`. Daardoor kreeg een goede
condensator zonder bekende fabrikant/serie nooit `WAARSCHIJNLIJK_GOED`,
ook al waren C en ESR ruim binnen tolerantie.

**Oplossing:** onderscheid tussen **inhoudelijke** en **administratieve**
betrouwbaarheidsverlagers.

- Inhoudelijk (raakt de meetcontext zelf): frequentieverschil,
  condensatortype onbekend of niet-elektrolytisch, type-mismatch van de
  referentie, C-ESR-D-inconsistentie, meetmethode ONE_LEG of IN_CIRCUIT.
  Deze verhogen het minimum van de eindstatus.
- Administratief (raakt enkel de documentatie/omgeving):
  omgevingstemperatuur onbekend, typische referentiewaarde,
  fabrikant/serie onbekend. Deze verlagen de betrouwbaarheid wel, maar
  verhogen het minimum van de eindstatus **niet**.

**Gewijzigde bestanden:**

| Bestand | Versie / status |
|---|---|
| `app/services/assessment_service.py` | v1.5.0 |
| `i18n/locales/nl_NL/esr.json` | 5 nieuwe keys |
| `i18n/locales/en_US/esr.json` | 5 nieuwe keys |
| `tests/test_assessment.py` | v1.5.0, 10 nieuwe tests |

**Nieuwe i18n-keys:**

- `betrouwbaarheid_factor.categorie_inhoudelijk` —
  "inhoudelijke verlager" / "content-related reducer".
- `betrouwbaarheid_factor.categorie_administratief` —
  "administratieve verlager" / "administrative reducer".
- `eindstatus_reden.betrouwbaarheid_laag_administratief` — nieuwe reden
  voor "waarschijnlijk goed, betrouwbaarheid laag door administratieve
  factoren".
- `resultaat.inhoudelijke_verlagers` en
  `resultaat.administratieve_verlagers` — labels voor de detailweergave.

**Nieuwe API in `assessment_service.py`:**

- `BetrouwbaarheidsResultaat` heeft een extra veld
  `inhoudelijke_verlagers: tuple[str, ...] = ()`.
- `bepaal_eindstatus` gebruikt `betrouwbaarheid.inhoudelijke_verlagers`
  in plaats van `betrouwbaarheid.niveau == Betrouwbaarheid.LAAG` als
  trigger voor minimaal `AANDACHTSPUNT`.
- In het `WAARSCHIJNLIJK_GOED`-blok is een extra tak toegevoegd: als de
  betrouwbaarheid LAAG is door uitsluitend administratieve verlagers,
  wordt de status alsnog `WAARSCHIJNLIJK_GOED` met een expliciete reden.

**Twee bestaande tests aangepast:**

- `test_meerdere_verlagende_factoren` — verwacht nu 4 inhoudelijke
  verlagers (frequentie, type, inconsistentie, in-circuit).
- `test_gebruiksscenario_1_goed` — gebruikt `D=None`, zodat de
  consistentiecontrole niet tussenbeide komt. De test toont zo dat het
  frequentieverschil de enige inhoudelijke verlager is.

**Niet gewijzigd:** alle drempels in `settings.py`, de
ESR-classificatie, de consistentie-logica, de GUI (de GUI leest
`verlagende_factoren`, dat blijft gevuld), en `report_render.py`.

### 5.2 Baselinecorrectie

De baseline van **1347** in v5.3.0 kwam **niet overeen** met de
werkelijke teststand op de machine. De werkelijke stand was:

- vóór 11B: **1329 passed**.
- ná 11B: **1339 passed** (10 nieuwe tests in `test_assessment.py`).

Het verschil (18 tests) is niet toe te schrijven aan 11B. De
gedocumenteerde baseline in eerdere overdrachten was te hoog. Vanaf
v5.4.0 wordt de werkelijke baseline gevolgd: **1339 passed**.

### 5.3 Gewijzigde bestanden sinds 5.3.0

| Bestand | Versie / status |
|---|---|
| `app/services/assessment_service.py` | v1.5.0 (was v1.4.0) |
| `i18n/locales/nl_NL/esr.json` | uitgebreid met 5 keys |
| `i18n/locales/en_US/esr.json` | uitgebreid met 5 keys |
| `tests/test_assessment.py` | v1.5.0 (was v1.4.0) |
| `docs/openvragen.md` | v2.7.0 |
| `overdracht.md` | v5.4.0 (dit bestand) |

### 5.4 Teststatus

**Baseline: 1339 passed.** Was 1329 vóór 11B. De toename is +10 tests,
alle in `test_assessment.py`.

### 5.5 Bekende beperkingen (bijgewerkt)

Onveranderd t.o.v. v5.3.0.

---

## 6. OPENSTAANDE VRAGEN VOOR DE NIEUWE CHAT

Zie `docs/openvragen.md` v2.7.0 voor de volledige, levende lijst.
Samenvatting van de belangrijkste punten voor fase 11C:

- §2.27 — iconen voor alle vensters.
- §2.20 — relatief `icon_path` verfijnen, `Architecture identifier "x64"`,
  `[rename] Fallback via robocopy`, `build_log.txt`, certificaten opruimen.
- §2.6 — diverse documentatie- en UX-punten.
- §2.9 — cosmetische scrollbar in Word-samenvatting.
- §2.11 — Analyse-pagina: as-schaling, tickformaat, zoom/pan.
- §2.14 — Rapportage: scope "filters" in de Rapportage-GUI.
- §2.16 — pandas/numpy pins heroverwegen.
- §2.21 — checkbox-zichtbaarheid donker thema, i18n-menging.
- §2.24 — update-melding cosmetica.
- §2.28 — export/import tussen toestellen.
- §4.4 — light theme.

Opgelost in 11B:
- §2.26 — betrouwbaarheidsregel verbergt goede resultaten.

---

## 7. TESTSTATUS — BASELINE EN TESTSTRUCTUUR

**Datum:** 2026-10-16
**Baseline:** 1339 passed
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

**Voor fase 11C (Iconen voor alle vensters):**

- `main.py`
- `app/gui/main_window.py`
- `app/gui/dialogs/*.py` (minstens `report_dialog.py`,
  `settings_dialog.py`, `import_wizard_dialog.py`,
  `search_help_dialog.py`, `change_status_dialog.py`,
  `edit_metadata_dialog.py`, `duplicate_source_dialog.py`)
- `assets/icons/` (huidige inhoud, minstens `README.md` en de
  bestaande `ESR.png` / `logo.ico`)
- `ESR_Tester.spec`
- `docs/python_header_standard.md`
- `docs/markdown_levering.md`

Enzovoort, afhankelijk van de gekozen sub-fase.

---

## 9. WERKAFSPRAKEN IN EEN NIEUWE SESSIE

Onveranderd t.o.v. v5.3.0. Toevoeging:

- **Bij het leveren van `.md`-bestanden: bij twijfel altijd
  viervoudige backticks.**
- **Bij een verschil tussen de gedocumenteerde baseline en de werkelijke
  `pytest -q`-uitvoer: eerst uitzoeken, dan pas doorgaan. Nooit stil
  een nieuwe fase starten op een ongeverifieerde baseline.**