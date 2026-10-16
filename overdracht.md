# OVERDRACHT — Electronics Diagnostic Tool Hub / ESR Tester

**Versie overdracht:** 5.6.0
**Datum:** 2026-10-16
**Auteur:** Bart Bossuyt
**Vorige versie:** 5.5.0 (2026-10-16)
**Doel:** volledig overdrachtsdocument voor een nieuwe ChatGPT-sessie of
nieuwe ontwikkelaar. Bevat projectstaat, architectuur, regels, changelog,
teststructuur en startprompt. Alles in één bestand.

**Huidige baseline:** 1366 passed
**Laatste afgeronde fase:** 11D — i18n-menging oplossen
**Volgende fase:** 11E — async netwerk

---

## INHOUD

1. Startprompt (lees dit eerst)
2. Context — projectstaat en architectuur
3. Kernregels — bindende afspraken
4. Stappenplan — chronologisch overzicht
5. Wat is nieuw sinds versie 5.5.0
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
- Baseline: **1366 passed**.
- Laatste afgeronde fase: **11D — i18n-menging oplossen**
  (2026-10-16).
- Volgende fase: **11E — async netwerk**.

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
| Huidige baseline | **1366 passed** |
| Laatste afgeronde fase | 11D — i18n-menging oplossen |
| Volgende fase | 11E — async netwerk |

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
  krijgt het veld `taal`, gevuld door `beoordeel_meting`. Maakt het voor
  de GUI mogelijk te detecteren dat een resultaat in een andere taal is
  opgesteld dan de huidige GUI-taal.
- `app/gui/esr_test_screen.py` (v1.13.0 → v1.14.0) — `_show_result` en
  `_build_result_html` gebruiken `resultaat.taal` voor alle
  resultaat-specifieke labels. Nieuwe banner `result_language_banner`
  voor de taal-mismatch. Bugfix in `apply_language`:
  `result_group.isVisible()` vervangen door `_laatste_resultaat is not
  None`, omdat `isVisible()` False is in offscreen/headless situaties
  en ook in productie niet de juiste check was.

Zie v5.0.0 en v5.1.0 van dit document voor de volledige
architectuurbeschrijving.

### 2.3 Belangrijke recente bugfixes

Zie v5.0.0, v5.1.0 en v5.2.0. Nieuw sinds v5.5.0: geen.

### 2.4 Openstaande werkpunten en fase 11-indeling

Volgende fase is **11E — async netwerk**. De scope staat in
`docs/openvragen.md` §2.6, §2.24 en de fase-11-tabel.

Sub-fase-indeling fase 11 (geactualiseerd):

| Sub-fase | Onderwerp | Status |
|---|---|---|
| **11A** | Export, import en selectie: export respecteert selectie, visuele selectie in Analyse, rapport-scope "selectie", menu-item disabled zonder selectie, mapvoorkeuren respecteren | **✅ 11A.1 + 11A.2 + 11A.3 afgerond** |
| **11B** | Betrouwbaarheidsregel herzien (§2.26) — onderscheid inhoudelijk vs. administratief | **✅ afgerond** |
| **11C** | Iconen voor alle vensters (§2.27) | **✅ afgerond** |
| **11D** | i18n-menging in Diagnose/Result en Resultaatdetails oplossen (§2.21) | **✅ afgerond** |
| **11E** | Async netwerk: async URL-fetch (§2.6), async `fetch_release_notes()` (§2.24), drie-knoppenmelding forceren voor QA (§2.24) | **Volgende** |
| 11F | Documentatie-uitbreiding: reden bij archiveren, filter gearchiveerde, bulk-edit, bulk-statuswijziging, datum-parsing verfijnen, cosmetische opruiming i18n-keys (§2.6, §2.14) | Gepland |
| 11G | Visueel donker thema: checkbox-zichtbaarheid (§2.21), cosmetische scrollbar Word-samenvatting (§2.9), Analyse-pagina cosmetica (as-schaling, tickformaat, zoom/pan) (§2.11) | Gepland |
| 11H | Light theme (§4.4) | Gepland |
| 11I | Build en cosmetica: `Architecture identifier "x64"` (§2.20), `[rename] Fallback via robocopy` (§2.20), `build_log.txt` (§2.20), externe links changelog (§2.24), release-notes tabellen (§2.24), certificaten opruimen (§2.20), pandas/numpy pins heroverwegen (§2.16) | Gepland |

Daarna volgen fase 12 (AI-extractie), 13 (menselijke validatie),
14 (fabrikantdata koppelen) en 15 (Resistor).

### 2.5 Werkafspraken voor een nieuwe sessie

Onveranderd t.o.v. v5.5.0. Zie §9.

---

## 3. KERNREGELS — BINDENDE AFSPRAKEN

Onveranderd t.o.v. v5.5.0. Zie §3.1 t/m §3.4 van dat document.

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
| **11D** | **i18n-menging oplossen** | **✅ afgerond** |
| **11E** | **Async netwerk** | **Volgende** |
| 11F | Documentatie-uitbreiding | Gepland |
| 11G | Visueel donker thema | Gepland |
| 11H | Light theme | Gepland |
| 11I | Build en cosmetica | Gepland |
| 12 | AI-extractie uit fabrikantdocumenten | Gepland |
| 13 | Menselijke validatie van AI-output | Gepland |
| 14 | Goedgekeurde fabrikantdata koppelen aan assessment | Gepland |
| 15 | Tweede diagnosetool — Resistor | Gepland |

---

## 5. WAT IS NIEUW SINDS VERSIE 5.5.0

### 5.1 Fase 11D — i18n-menging oplossen

**Aanleiding (§2.21 in `docs/openvragen.md`):** na een live taalwissel
toonde het ESR-scherm een mengeling van talen. De GUI-chrome schakelde
netjes om, maar de reeds vertaalde strings uit het `Beoordeling`-object
(`toelichting`, `redenen`, `waarschuwingen`, `aanbevolen_vervolgstap`)
bleven in de oude taal staan. Daarnaast was de `*`-toelichting bij een
frequentieverschil hardcoded in de GUI in plaats van via i18n.

**Oplossing:**

- `Beoordeling` krijgt een `taal`-veld dat wordt gevuld door
  `beoordeel_meting`. De GUI kan daarmee detecteren dat een resultaat
  in een andere taal is opgesteld dan de huidige GUI-taal.
- Na een live taalwissel toont het ESR-scherm een nette banner in de
  GUI-taal. De reeds vertaalde resultaatstrings blijven in hun eigen
  taal; er is geen stille mengeling meer.
- `_show_result` en `_build_result_html` vertalen alle
  resultaat-specifieke labels in `resultaat.taal` in plaats van
  `self.taal`. De GUI-chrome blijft via `self.taal` lopen.
- De losse `*`-toelichting bij een frequentieverschil loopt nu via
  twee nieuwe i18n-keys in NL én EN.
- Bugfix in `apply_language`: de conditie `result_group.isVisible()`
  is vervangen door `_laatste_resultaat is not None`. In
  offscreen/headless situaties is `isVisible()` False en werd de
  banner nooit getoond.

**Gewijzigde bestanden:**

| Bestand | Versie / status |
|---|---|
| `app/services/assessment_service.py` | v1.5.0 → v1.6.0 |
| `app/gui/esr_test_screen.py` | v1.13.0 → v1.14.0 |
| `i18n/locales/nl_NL/esr.json` | 3 nieuwe keys onder `resultaat` |
| `i18n/locales/en_US/esr.json` | 3 nieuwe keys onder `resultaat` |
| `tests/test_assessment.py` | v1.5.0 → v1.5.1, +5 tests |
| `tests/test_gui_language_switch.py` | v1.1.1 → v1.2.0, +3 tests |
| `docs/changelog/nl_NL.md` | 11D-sectie toegevoegd |
| `docs/changelog/en_US.md` | 11D-sectie toegevoegd |
| `docs/openvragen.md` | v2.8.0 → v2.9.0 |

**Nieuwe API / velden:**

- `Beoordeling.taal: str = STANDAARD_TAAL` — de taal waarin alle
  reeds vertaalde strings zijn opgesteld.
- `EsrTestScreen._t_voor(taal, sleutel, **kwargs)` — vertaalt in een
  expliciete taal; gebruikt voor resultaatstrings.
- `EsrTestScreen.result_language_banner: QLabel` — de taal-mismatch-
  banner.

**Nieuwe i18n-keys onder `resultaat`:**

- `taal_mismatch_banner` — "Dit resultaat is opgesteld in het
  {oude_taal}. Beoordeel opnieuw om het in het {nieuwe_taal} weer te
  geven." (EN: "This result was produced in {oude_taal}. Re-assess to
  display it in {nieuwe_taal}.")
- `esr_factor_frequentie_indicatief` — "Indicatieve
  ESR-vergelijking: meet- en referentiefrequentie verschillen."
- `esr_factor_frequentie_indicatief_kort` — "* indicatief:
  frequentieverschil"

### 5.2 Baselinecorrectie 11D

Baseline vóór 11D: **1358**. Baseline ná 11D: **1366**. Toename:
**+8 tests** — 5 in `tests/test_assessment.py` (nieuwe klasse
`TestBeoordelingTaal`), 3 in `tests/test_gui_language_switch.py`
(taal-mismatch-banner).

### 5.3 Gewijzigde bestanden sinds 5.5.0

Zie de tabel in §5.1.

### 5.4 Teststatus

**Baseline: 1366 passed.** Was 1358 vóór 11D. De toename is +8 tests,
alle additief.

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
- `_fake_translate` in `tests/test_gui_language_switch.py` plakt
  kwargs achter de sleutel als `[k=v,...]` in plaats van de echte
  format-vervanging te doen. Cosmetisch, geen functionele impact. Te
  verfijnen in een latere cosmetische fase (11F of 11I).

---

## 6. OPENSTAANDE VRAGEN VOOR DE NIEUWE CHAT

Zie `docs/openvragen.md` v2.9.0 voor de volledige, levende lijst.
Samenvatting van de belangrijkste punten voor fase 11E:

- §2.6 — diverse documentatie- en UX-punten, waaronder async URL-fetch.
- §2.24 — update-melding cosmetica: async `fetch_release_notes()`,
  drie-knoppenmelding forceren voor QA.
- §2.20 — relatief `icon_path` verfijnen, `Architecture identifier "x64"`,
  `[rename] Fallback via robocopy`, `build_log.txt`, certificaten opruimen.
- §2.9 — cosmetische scrollbar in Word-samenvatting.
- §2.11 — Analyse-pagina: as-schaling, tickformaat, zoom/pan.
- §2.14 — Rapportage: scope "filters" in de Rapportage-GUI.
- §2.16 — pandas/numpy pins heroverwegen.
- §2.28 — export/import tussen toestellen.
- §4.4 — light theme.

Opgelost in 11B:
- §2.26 — betrouwbaarheidsregel verbergt goede resultaten.

Opgelost in 11C:
- §2.27 — alle vensters een gepast icoon.

Opgelost in 11D:
- §2.21 — i18n-menging in Diagnose/Result en Resultaatdetails.

---

## 7. TESTSTATUS — BASELINE EN TESTSTRUCTUUR

**Datum:** 2026-10-16
**Baseline:** 1366 passed
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

**Voor fase 11E (async netwerk):**

- `app/helpers/updater.py` — bevat `check_for_update()` en
  `fetch_release_notes()`
- `app/gui/main_window.py` — waar de update-melding wordt getoond
- `app/documentation/url_fetch.py` — URL-fetch voor de import-wizard
- `app/documentation/url_import.py` — orkestratielaag
- `app/gui/dialogs/import_wizard_dialog.py` — GUI voor de URL-import
- `i18n/locales/nl_NL/app.json`
- `i18n/locales/en_US/app.json`
- `i18n/locales/nl_NL/documentation.json`
- `i18n/locales/en_US/documentation.json`
- `tests/test_updater.py`
- `tests/test_startup_update_check.py`
- `tests/test_documentation_url_fetch.py`
- `tests/test_main_window_update_menu.py`
- `tests/test_import_wizard_dialog.py`

Enzovoort, afhankelijk van de gekozen sub-fase.

---

## 9. WERKAFSPRAKEN IN EEN NIEUWE SESSIE

Onveranderd t.o.v. v5.5.0. Toevoeging:

- **Offscreen GUI-tests en `isVisible()`:** in een test waarin het
  scherm nooit `show()` krijgt, is `isVisible()` altijd `False`, ook
  als `setVisible(True)` op een kind is aangeroepen. Gebruik
  `isHidden()` voor "is dit kind zichtbaar binnen zijn ouder?".
- **Gebruik in productie nooit `isVisible()` als conditie voor "is er
  ooit iets gebeurd?".** Gebruik daarvoor een expliciet statusveld.
  `isVisible()` is alleen betrouwbaar als het hele venster zichtbaar
  is, wat in offscreen tests en in niet-actieve `QStackedWidget`-pagina's
  niet zo is.