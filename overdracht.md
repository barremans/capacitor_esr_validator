# OVERDRACHT — Electronics Diagnostic Tool Hub / ESR Tester

**Versie overdracht:** 6.7.0
**Datum:** 2026-10-23
**Auteur:** Bart Bossuyt
**Vorige versie:** 6.6.0 (2026-10-22)
**Doel:** volledig overdrachtsdocument voor een nieuwe ChatGPT-sessie of
nieuwe ontwikkelaar. Bevat projectstaat, architectuur, regels, changelog,
teststructuur en startprompt. Alles in één bestand.

**Huidige baseline:** 1700 passed
**Huidige app-versie:** 1.3.0
**Laatste afgeronde fase:** §2.28 — Export/import tussen toestellen
**Volgende fase:** 12B — AI-model-keuze en API-koppeling (op hold)
**Op hold:** 12B — wacht op provider/model-keuze

---

## INHOUD

1. Startprompt (lees dit eerst)
2. Context — projectstaat en architectuur
3. Kernregels — bindende afspraken
4. Stappenplan — chronologisch overzicht
5. Wat is nieuw sinds versie 6.6.0
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
- Baseline: **1700 passed**.
- Huidige versie: `1.3.0`.
- Laatste afgeronde fase: **§2.28 — Export/import tussen toestellen**
  (2026-10-23). Zes sub-fases (28A, 28B, 28C, 28E, 28D, 28F), +102 tests.
- Daarvoor afgerond: **12A** (2026-10-22, extractiemodel + dispatcher,
  +37 tests) en **12E** (2026-10-22, scope "filters" in de
  Rapportage-GUI, +13 tests).
- Op hold: **12B — AI-model-keuze en API-koppeling** (wacht op
  provider/model-keuze en offline-first-vs-cloud-beslissing).
- Volgende opdracht: **12B** — pas nadat de AI-keuze is genomen.

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
  in GUI-tests.
- **Verwerk `deleteLater()` in GUI-tests** met
  `QApplication.processEvents()` vóór je de menubar of andere
  QObject-hiërarchieën inspecteert.
- **De taalparameter van `ToolHubWindow` heeft voorrang op
  `settings.json`. Hetzelfde geldt sinds 11H.3 voor de
  `theme`-parameter.**
- **`setStyleSheet` op een venster, niet op de `QApplication`.**
- **Thema doorgeven aan schermen** met een keyword-only
  `theme`-parameter en een `apply_theme(theme)`-methode.
- **Voor leesbare PDF-rapporten:** sinds fase 9A zet `main.py`
  automatisch `QT_QPA_FONTDIR=C:\Windows\Fonts` op Windows.
- **Bij het leveren van `.md`-bestanden die zelf codeblokken bevatten:**
  gebruik **viervoudige backticks**. Bij twijfel: altijd viervoudig.
- **De ArticleSearch-flow is de bewezen build-flow.**
- **Geen aannames over de volgende fase:** vraag het na.
- **Nooit een GitHub-token in een getrackt bestand, chat of
  context-document zetten.**
- **Bij een verschil tussen de gedocumenteerde baseline en de werkelijke
  `pytest -q`-uitvoer: eerst uitzoeken, dan pas doorgaan.**
- **Testtelling bijhouden per fase:** tel nieuwe tests per bestand
  (gerichte `pytest --collect-only -q`), niet op basis van een schatting.
- **Bij het herschrijven van een test-sectie: `Compare-Object` tegen
  de vorige versie.**
- **Versie bumpen: de buildstraat (`build_and_publish.ps1` +
  `bump_version.py`) doet dit bij de build. Bij de afronding van een
  fase mag de versie in `app/version.py` mee omhoog; bij elke
  sub-fase niet.**

**Wat ik nu van je vraag:**

1. Bevestig dat je de context hebt gelezen en dat je de baseline en
   de volgende fase correct begrijpt.
2. Geef een korte samenvatting (max 10 regels) van de huidige
   projectstaat en de eerstvolgende fase.
3. Wacht op mijn instructie "start 12B" of een andere opdracht.

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
| Database-schema | **v3** (herkomst-kolommen sinds §2.28) |
| GitHub-repo | `https://github.com/barremans/capacitor_esr_validator` |
| Huidige versie | `1.3.0` |
| Huidige baseline | **1700 passed** |
| Laatste afgeronde fase | §2.28 — Export/import tussen toestellen |
| Op hold | 12B — AI-model-keuze en API-koppeling |
| Volgende opdracht | 12B — pas na AI-keuze |

### 2.2 Huidige applicatiearchitectuur

Zie v6.0.0 §2.2 voor de volledige architectuurbeschrijving. Nieuw
sinds v6.6.0:

**Nieuw in §2.28 (allemaal afgerond):**

| Onderdeel | Bestand | Versie |
|---|---|---|
| Exchange-modellen | `app/services/exchange/models.py` | v1.0.0 |
| Exchange-package-init | `app/services/exchange/__init__.py` | v1.0.4 |
| Export-service | `app/services/exchange/export_service.py` | v1.0.1 |
| Import-planner | `app/services/exchange/import_planner.py` | v1.0.0 |
| Import-service | `app/services/exchange/import_service.py` | v1.0.0 |
| Exchange-dialoog | `app/gui/dialogs/exchange_dialog.py` | v1.0.1 |
| Bindende spec | `docs/export_import_format.md` | v1.0.0 |
| i18n NL | `i18n/locales/nl_NL/exchange.json` | — |
| i18n EN | `i18n/locales/en_US/exchange.json` | — |
| Schema (v3) | `app/storage/schema.py` | v1.2.0 |
| Migraties (v2→v3) | `app/storage/migrations.py` | v1.2.0 |
| Storage-modellen | `app/storage/models.py` | v1.2.0 |
| Storage-service | `app/storage/service.py` | v1.2.0 |
| Hoofdvenster | `app/gui/main_window.py` | v2.23.0 |
| Startmaphelper | `app/helpers/dialog_start_directory.py` | v1.0.1 |
| Instellingen | `app/config/settings.py` | v1.8.2 |

**Samenvatting van §2.28:**

Export/import tussen toestellen. JSON-envelope met meetketens, zes
sub-fases: formaat (28A), export (28B), import-planner (28C),
schema-migratie v2→v3 (28E), import-service (28D), GUI (28F). Twee
nieuwe Bestand-menu-items: "Exporteren naar toestel…" (Ctrl+Shift+E)
en "Importeren van toestel…" (Ctrl+Shift+I). Natuurlijke sleutel =
SHA-256 over de canonieke keten (spec §6); duplicate-detectie
inhoudelijk. Conflict-copy is de standaard. Race-check vóór elke
write. Per-keten transacties.

**Belangrijke bugfix in §2.28:** `_show_import_wizard` in
`main_window.py` had een typfout `self._zet_dialoog_icono(...)` in
plaats van `self._zet_dialoog_icoon(...)`. Latente bug die bij het
openen van de import-wizard een `AttributeError` gaf.

### 2.3 Belangrijke recente bugfixes

Zie v6.0.0 §2.3 en v6.5.0 §2.3. Nieuw sinds v6.6.0:

- **§2.28:** `_show_import_wizard` typfout `icono` → `icoon`. Latente
  bug die pas bij het openen van de import-wizard optrad.

### 2.4 Openstaande werkpunten en fase-indeling

**Op hold:** 12B — AI-model-keuze en API-koppeling. Wacht op een
ontwerpbeslissing: welke provider, welk model, offline-first of
cloud-API, en waar de API-key leeft.

**Volgende opdracht:** **12B — AI-model-keuze en API-koppeling** —
pas nadat de AI-keuze is genomen.

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

Onveranderd t.o.v. v6.6.0, behalve:

- **`app/services/exchange/` is de uniforme ingang voor export/import
  tussen toestellen sinds §2.28.** Nieuwe code die metingen wil
  uitwisselen gebruikt `ExportService`, `ImportPlanner`,
  `ImportService` en `read_envelope`, niet de onderliggende
  storage-modules rechtstreeks.
- **`docs/export_import_format.md` is bindend voor alle code in
  `app/services/exchange/`.** Wijzigingen aan het formaat vereisen een
  nieuwe `format_version` en een aparte sub-fase.
- **Versie-bump: bij de build (via `build_and_publish.ps1`), niet per
  sub-fase.** Bij de afronding van een fase mag de versie in
  `app/version.py` mee omhoog. Bij elke sub-fase niet.

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
| **§2.28** | **Export/import tussen toestellen** | ✅ (28A, 28B, 28C, 28E, 28D, 28F) |
| 13 | Menselijke validatie van AI-output | Gepland |
| 14 | Goedgekeurde fabrikantdata koppelen aan assessment | Gepland |
| 15 | Tweede diagnosetool — Resistor | Gepland |

---

## 5. WAT IS NIEUW SINDS VERSIE 6.6.0

### 5.1 §2.28 — Export/import tussen toestellen

**Aanleiding:** de app bewaart metingen lokaal op één toestel. Wie op
een tweede pc verder wil werken, moest de database handmatig kopiëren.
§2.28 voegt een expliciet uitwisselformaat toe: een JSON-envelope met
meetketens, waarmee je metingen selectief kunt exporteren en op een
ander toestel importeren.

**Oplossing: zes sub-fases**

| Sub-fase | Wat | Tests |
|---|---|---|
| 28A | Formaat + modellen | 34 |
| 28B | Export-service | 15 |
| 28C | Import-planner | 11 |
| 28E | Schema-migratie v2 → v3 | 16 |
| 28D | Import-service | 16 |
| 28F | GUI-koppeling | 16 |

**Totaal:** +102 tests. Baseline 1598 → **1700 passed**.

**Belangrijke ontwerpbeslissingen:**

- JSON-envelope (geen SQLite-dump), UTF-8 zonder BOM, pretty-printed,
  `format_version="1.0"`.
- Natuurlijke sleutel = SHA-256 over de canonieke keten (§6 spec).
- Duplicate-detectie op herkomst (`source_machine_id` +
  `source_measurement_id`) én op natural_key.
- Conflict-copy is de standaard bij een conflict; nooit stil
  overslaan.
- Race-check vóór elke write.
- Per-keten transacties; een fout in één keten blokkeert de rest
  niet.
- Machine-ID als UUID4 in `settings.json` (`algemeen.machine_id`).

**Nieuwe gebruikersfuncties:**

- Bestand → "Exporteren naar toestel…" (Ctrl+Shift+E)
- Bestand → "Importeren van toestel…" (Ctrl+Shift+I)

### 5.2 Baseline

| Sub-fase | Baseline vóór | Baseline ná | Nieuw |
|---|---|---|---|
| 11I.5 | 1548 | 1548 | 0 |
| 12A | 1548 | 1585 | +37 |
| 12E | 1585 | 1598 | +13 |
| 28A | 1598 | 1632 | +34 |
| 28B | 1632 | 1647 | +15 |
| 28C | 1647 | 1658 | +11 |
| 28E | 1658 | 1668 | +16 |
| 28D | 1668 | 1684 | +16 |
| 28F | 1684 | **1700** | +16 |

**Totaal sinds 11I.5:** 1548 → 1700 (+152 tests).

### 5.3 Gewijzigde bestanden sinds 6.6.0

| Bestand | Versie / status |
|---|---|
| `app/services/exchange/__init__.py` | **nieuw** v1.0.4 |
| `app/services/exchange/models.py` | **nieuw** v1.0.0 |
| `app/services/exchange/export_service.py` | **nieuw** v1.0.1 |
| `app/services/exchange/import_planner.py` | **nieuw** v1.0.0 |
| `app/services/exchange/import_service.py` | **nieuw** v1.0.0 |
| `app/gui/dialogs/exchange_dialog.py` | **nieuw** v1.0.1 |
| `docs/export_import_format.md` | **nieuw** v1.0.0 |
| `i18n/locales/nl_NL/exchange.json` | **nieuw** |
| `i18n/locales/en_US/exchange.json` | **nieuw** |
| `app/storage/schema.py` | v1.1.0 → **v1.2.0** |
| `app/storage/migrations.py` | v1.1.0 → **v1.2.0** |
| `app/storage/models.py` | v1.1.0 → **v1.2.0** |
| `app/storage/service.py` | v1.1.0 → **v1.2.0** |
| `app/gui/main_window.py` | v2.22.2 → **v2.23.0** |
| `app/helpers/dialog_start_directory.py` | v1.0.0 → **v1.0.1** |
| `app/config/settings.py` | v1.8.1 → **v1.8.2** |
| `app/version.py` | v1.1.0 → **v1.2.0** (`__version__ = "1.3.0"`) |
| `tests/test_exchange_models.py` | **nieuw** v1.0.1 (34 tests) |
| `tests/test_exchange_export_service.py` | **nieuw** v1.0.3 (15 tests) |
| `tests/test_exchange_import_planner.py` | **nieuw** v1.0.2 (11 tests) |
| `tests/test_exchange_import_service.py` | **nieuw** v1.0.1 (16 tests) |
| `tests/test_exchange_dialog.py` | **nieuw** v1.0.1 (11 tests) |
| `tests/test_main_window_exchange_menu.py` | **nieuw** v1.0.0 (5 tests) |
| `tests/test_storage_schema.py` | v1.1.0 → **v1.2.0** |
| `tests/test_storage_migrations.py` | v1.0.0 → **v1.1.0** |
| `tests/test_storage_service.py` | v1.0.0 → **v1.1.0** |
| `tests/test_storage_multitool_v2.py` | v1.0.0 → **v1.0.1** |
| `overdracht.md` | → **v6.7.0** |
| `docs/openvragen.md` | → **v3.8.0** |
| `docs/changelog/nl_NL.md` | nieuwe §2.28-sectie |
| `docs/changelog/en_US.md` | nieuwe §2.28-sectie |
| `WatNu.md` | → **v2.4.0** |

### 5.4 Teststatus

**Baseline: 1700 passed.** Was 1598 vóór §2.28. De suite draait in
~227 s.

### 5.5 Bekende beperkingen (bijgewerkt)

Onveranderd t.o.v. v6.5.0. Wat nog rest:

- **`QApplication.setStyleSheet` is verboden** behalve in `main.py`
  bij opstart.
- **`esr_test_screen.py` en `documentation_screen.py`** bevatten nog
  geen thema-afhankelijke kleuren.
- **Publiek vertrouwd (EV-)certificaat** — structurele oplossing.
- **Fallback timestamp-server** — single point of failure.
- **12B op hold** — wacht op provider/model-keuze.

---

## 6. OPENSTAANDE VRAGEN VOOR DE NIEUWE CHAT

Zie `docs/openvragen.md` v3.8.0 voor de volledige, levende lijst.
Samenvatting van de belangrijkste punten:

- **12B op hold** — provider/model-keuze ontbreekt.
- §11 packaging — publiek vertrouwd (EV-)certificaat;
  fallback timestamp-server.

Opgelost in 12A: de extractie-orkestratie.
Opgelost in 12E: §2.14 (scope "filters" in de Rapportage-GUI).
Opgelost in §2.28: §2.28 (export/import tussen toestellen).

**§2.14 en §2.28 zijn nu volledig opgelost.**

---

## 7. TESTSTATUS — BASELINE EN TESTSTRUCTUUR

**Datum:** 2026-10-23
**Baseline:** 1700 passed
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

**Voor 12B (AI-model-keuze en API-koppeling):**

- `docs/export_import_format.md` (v1.0.0) — sinds §2.28 de bindende
  spec voor uitwisseling
- `app/services/exchange/__init__.py` (v1.0.4)
- `app/services/exchange/models.py` (v1.0.0)
- `app/services/exchange/export_service.py` (v1.0.1)
- `app/services/exchange/import_planner.py` (v1.0.0)
- `app/services/exchange/import_service.py` (v1.0.0)
- `app/documentation/extraction_models.py` (v1.0.0)
- `app/documentation/extraction_service.py` (v1.0.0)
- `docs/context.md`

**Sterk aanbevolen:**

- `app/gui/main_window.py` (v2.23.0)
- `app/gui/dialogs/exchange_dialog.py` (v1.0.1)
- `app/config/settings.py` (v1.8.2)
- `tests/test_exchange_import_planner.py` (v1.0.2)
- `tests/test_exchange_import_service.py` (v1.0.1)
- `app/version.py` (v1.2.0)

---

## 9. WERKAFSPRAKEN IN EEN NIEUWE SESSIE

Onveranderd t.o.v. v6.0.0 §9, aangevuld met:

- **`conftest.py` is een geaccepteerd onderdeel van de suite** sinds
  11H.3.
- **`setStyleSheet` nooit onvoorwaardelijk op de `QApplication`**
  aanroepen.
- **Thema doorgeven aan schermen** met een keyword-only
  `theme`-parameter en een `apply_theme(theme)`-methode.
- **`icon_paths.py` gebruikt sinds 11I.2 een expliciete
  `sys._MEIPASS`-branch** vóór de omhoog-zoeklus.
- **`build_installer.bat` logt sinds 11I.3 de PyInstaller-stap [4] en
  de ISCC-stap [7]** naar `build_log.txt`.
- **`build_and_publish.ps1` geeft sinds 11I.3 de bevestigingsvraag
  "Starten?" een expliciete standaardwaarde J.**
- **`signing-certs/` staat sinds 11I.4 in `.gitignore`.**
- **`ReportDialog.for_filters` bestaat sinds 12E.**
- **`extraction_service.py` is sinds 12A de uniforme extractie-ingang.**
- **`app/services/exchange/` is sinds §2.28 de uniforme
  export/import-ingang.**
- **Versie-bump bij de build, niet per sub-fase.**