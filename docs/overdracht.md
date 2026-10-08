# OVERDRACHT — Electronics Diagnostic Tool Hub / ESR Tester

**Versie overdracht:** 3.3.0
**Datum:** 2026-10-08
**Auteur:** Bart Bossuyt
**Vorige versie:** 3.2.0 (2026-10-08)
**Doel:** volledig overdrachtsdocument voor een nieuwe ChatGPT-sessie of
nieuwe ontwikkelaar. Bevat projectstaat, architectuur, regels, changelog,
teststructuur en startprompt. Alles in één bestand.

**Huidige baseline:** 885 passed
**Laatste afgeronde fase:** 5D'.2f — Checkbox-indicator in donker thema
**Volgende fase:** Nog te bepalen —
   - 5D'.1b — Metadata van imports doorzoekbaar maken (formaliseren; geen codewijziging)
   - 6 — Fabrikantdocument-import (Word, Excel)
   - 5F-formalisering — Documentatie definitief afronden (deels gedaan)

---

## INHOUD

1. Startprompt (lees dit eerst)
2. Context — projectstaat en architectuur
3. Kernregels — bindende afspraken
4. Stappenplan — chronologisch overzicht
5. Wat is nieuw sinds versie 3.2.0
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
- Baseline: **885 passed**.
- Laatste afgeronde fase: **5D'.2f — Checkbox-indicator in donker thema**.
- Volgende fase: **nog te bepalen** — zie sectie 6.

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
- Leg elke stap eerst kort uit, dan implementeren.
- Draai altijd eerst **gerichte tests**, dan **volledige `pytest -q`**.
- Een fase is pas afgerond wanneer **beide groen** zijn.
- Nieuwe GUI-tekst en tooltips lopen via **NL/EN i18n**; meld nieuwe
  keys expliciet met beide waarden.
- Python-bestanden krijgen een **header** met bestandsnaam, project,
  versie, datum, auteur, doel en **cumulatieve wijzigingshistoriek**.
  Zie `docs/python_header_standard.md`.
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
| Huidige baseline | **885 passed** |
| Laatste afgeronde fase | 5D'.2f — Checkbox-indicator in donker thema |
| Volgende fase | Nog te bepalen |

### 2.2 Huidige applicatiearchitectuur

**Eén-venster-navigatie (ToolHubWindow):**

- `QStackedWidget` met pagina's: hub, diagnose, ESR, historiek, documentatie.
- Contextueel X-gedrag: binnen een pagina terug naar de bovenliggende pagina;
  op de hub sluit de applicatie.
- Menu: Bestand, Diagnose, Instellingen (incl. Talen), Help.

**Sneltoetsen:**

- **Globaal:** `Ctrl+Q`, `Ctrl+E`, `Ctrl+I`, `F1`.
- **ESR-scherm:** `Esc`, `Ctrl+Return`, `Ctrl+S`, `Ctrl+W`, `Ctrl+I`.
- **Historiek:** `Esc`, `Ctrl+R`, `Ctrl+F`, `Ctrl+D`, `Ctrl+H`.
- **Hoofdmenu:** `Ctrl+D`, `Ctrl+H`, `Ctrl+K`, `Esc`.
- **Diagnose:** `Esc`.
- **Documentatie:** `Esc`, `Return`, `Ctrl+F`, `Ctrl+L`, `Ctrl+O`, `F1`.
- **Import-wizard:** `Ctrl+D` (datum op vandaag).
- **Metadata-editor:** `Ctrl+D` (datum op vandaag).

Alle lokale sneltoetsen gebruiken `WidgetWithChildrenShortcut`.

**Storage:**

- SQLite op `%LOCALAPPDATA%\ElectronicsDiagnosticToolHub\measurements.sqlite3`.
- Schema v1: 7 tabellen. Schema v2: `measurements.tool_key`.
- Migratieframework transactioneel en sequentieel.
- Ruwe meetdata append-mostly; assessment en reference als snapshots.

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
- **Sinds 5D'.2c:** Bewerken-knop voor eigen imports. Ingebouwde
  documenten blijven read-only.
- **Sinds 5D'.2e:** Status wijzigen-knop voor eigen imports, Toon
  gearchiveerde-checkbox, Status-kolom.
- **Sinds 5D'.2f:** checkboxen en radio buttons duidelijk zichtbaar in
  donker thema.

**Documentatie-import (fase 5 + 5D'.2b/d + 5D'.2e):**

- Wizard voor PDF- en URL-import via `Bestand → Document importeren…`
  (`Ctrl+I`) en via knop "Importeren" op het Documentatie-scherm.
- Twee cataloguslagen: ingebouwde `app/data/documentation/catalog.json`
  en gebruikerscatalogus `%LOCALAPPDATA%\ElectronicsDiagnosticToolHub\documentation\imported_catalog.json`.
- Geïmporteerde PDF's in `...\documentation\sources\<source_id>.pdf`.
- HTML-snapshots van URL-imports in `...\documentation\snapshots\<source_id>.html`.
- Statusmachine: `CONCEPT → ACTIEF → GEARCHIVEERD`, met `revoke` terug
  naar `CONCEPT`.
- **Metadata in de wizard:** categorie (verplicht, default DATASHEET),
  fabrikant, serie, partnummer, documentversie (uppercase),
  documentdatum (`QDateEdit` + "Datum onbekend"-checkbox + `Ctrl+D`),
  notities.
- **Import is gescheiden van viewer en van assessment.**

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

**Toon gearchiveerde (fase 5D'.2e):**

- Checkbox naast de tool-dropdown in `documentation_screen.py`.
- Standaard uit. Aan = ook gearchiveerde imports zichtbaar.
- Roept `DocumentationService.list_documents(include_archived=True)` aan.
- `DocumentationService.get_document` zoekt altijd in beide
  cataloguslagen, inclusief gearchiveerd.

**Status-kolom (fase 5D'.2e):**

- Extra kolom in de documentatietabel, tussen Categorie en Fabrikant.
- Leeg voor ingebouwde documenten.
- `ImportStatus`-waarde voor eigen imports.

**Help per taal:**

- `docs/help/<taal>.md` (bv. `nl_NL.md`, `en_US.md`).
- Fallback-keten: `<taal>.md` → `nl_NL.md` → `help.md` →
  `FileNotFoundError`.
- Resolutie in `app/helpers/help_paths.py`.

**i18n:**

- Alle GUI-teksten via `app/helpers/i18n.py` en JSON-bestanden onder
  `i18n/locales/<taal>/`.
- Modules: `app.json`, `esr.json`, `history.json`, `documentation.json`,
  `settings.json`, `language.json`.
- Ontbrekende EN-key valt terug op NL.
- Live taalwissel behoudt state.

**Qt-stijl:**

- `main.py` zet `app.setStyle("Fusion")` vóór `apply_dark_theme(app)`.
- Zonder Fusion negeert Qt op Windows 10/11 CSS op
  `QRadioButton::indicator` en `QCheckBox::indicator`.
- Sinds 5D'.2f heeft `styles.py` expliciete `QCheckBox::indicator` en
  `QRadioButton::indicator`-regels.

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

### 2.4 Openstaande werkpunten

Volgens het stappenplan:

- **5D'.1b** — Metadata van imports doorzoekbaar maken (deels al
  gedaan via `_search_blob`, te formaliseren).
- **5F** — Changelog + documentatie. **Deels gedaan in deze sessie.**
- **6** — Fabrikantdocument-import (incl. Word `.docx` en Excel
  `.xlsx`).
- **7** — Grafieken & trends.
- **8** — Rapportage.
- **9** — Packaging / installer / signing.
- **10** — Praktische ESR-validatie.
- **11** — Laatste UX/documentatie-afwerking (incl. light theme).
- **12** — AI-extractie uit fabrikantdocumenten.
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
| 5D'.1b | Metadata van imports doorzoekbaar maken | Deels gedaan |
| 5F | Changelog + documentatie | Deels gedaan |
| 6 | Fabrikantdocument-import (Word, Excel) | Gepland |
| 7 | Grafieken & trends | Gepland |
| 8 | Rapportage | Gepland |
| 9 | Packaging / installer / signing | Gepland |
| 10 | Praktische ESR-validatie | Gepland |
| 11 | Laatste UX/documentatie-afwerking | Gepland |
| 12 | AI-extractie uit fabrikantdocumenten | Gepland |
| 13 | Menselijke validatie van AI-output | Gepland |
| 14 | Goedgekeurde fabrikantdata koppelen aan assessment | Gepland |
| 15 | Tweede diagnosetool — Resistor | Gepland |

---

## 5. WAT IS NIEUW SINDS VERSIE 3.2.0

### 5.1 5D'.2e — Status wijzigen in de viewer

**Doel:** de gebruiker kan de levenscyclus van een eigen import aanpassen
vanuit de documentatiebibliotheek.

**Nieuwe bestanden:**

| Bestand | Versie | Verantwoordelijkheid |
|---|---|---|
| `app/gui/dialogs/change_status_dialog.py` | 1.0.0 | Status-editor |
| `tests/test_change_status_dialog.py` | 1.0.0 | GUI-tests |

**Gewijzigde bestanden:**

| Bestand | Versie | Wijziging |
|---|---|---|
| `app/gui/documentation_screen.py` | 2.2.0 → 2.3.0 | Status wijzigen-knop, Toon gearchiveerde-checkbox, Status-kolom |
| `app/documentation/service.py` | 1.8.2 → 1.9.1 | `include_archived`-parameter, `get_document` zoekt ook gearchiveerd |
| `app/documentation/models.py` | 1.5.0 → 1.6.0 | `import_status`-veld |
| `app/documentation/import_service.py` | 1.3.0 → 1.3.1 | `_atomic_replace` voor Windows-robuustheid |
| `i18n/locales/nl_NL/documentation.json` | 1.3.0 → 1.4.0 | 19 nieuwe keys |
| `i18n/locales/en_US/documentation.json` | 1.3.0 → 1.4.0 | 19 nieuwe keys |
| `tests/test_documentation_screen.py` | 1.10.1 → 1.11.0 | 12 nieuwe tests |
| `tests/test_documentation_service_user_catalog.py` | 1.0.1 → 1.1.0 | 6 nieuwe tests |

### 5.2 5D'.2f — Checkbox-indicator in donker thema

**Doel:** checkboxen en radio buttons duidelijk zichtbaar in het donkere
thema.

**Gewijzigde bestanden:**

| Bestand | Versie | Wijziging |
|---|---|---|
| `app/gui/styles.py` | 1.2.0 → 1.3.0 | `QCheckBox::indicator`- en `QRadioButton::indicator`-styling |

**Geen nieuwe tests, geen functionele impact.**

### 5.3 Nieuwe i18n-keys (sinds 3.2.0)

In `i18n/locales/<taal>/documentation.json`:

| Key | NL | EN |
|---|---|---|
| `status_wijzigen` | Status wijzigen… | Change status… |
| `status_wijzigen_tooltip` | Wijzig de status van deze import | Change the status of this import |
| `status_wijzigen_alleen_eigen` | Alleen eigen imports kunnen van status veranderen. Ingebouwde documenten zijn read-only. | Only your own imports can change status. Built-in documents are read-only. |
| `status_wijzigen_titel` | Status wijzigen | Change status |
| `status_wijzigen_subtitel` | Kies de nieuwe status voor deze import. De bron en de metadata blijven ongewijzigd. | Choose the new status for this import. The source and metadata remain unchanged. |
| `status_wijzigen_huidige` | Huidige status | Current status |
| `status_wijzigen_nieuwe` | Nieuwe status | New status |
| `status_wijzigen_opslaan` | Opslaan | Save |
| `status_wijzigen_annuleren` | Annuleren | Cancel |
| `status_wijzigen_fout_titel` | Fout bij wijzigen | Error changing status |
| `status_wijzigen_fout_bericht` | Status kon niet worden gewijzigd: {bericht} | Status could not be changed: {bericht} |
| `status_wijzigen_bevestiging_archiveren` | Weet je zeker dat je deze bron wilt archiveren? De bron verdwijnt uit de standaardlijst maar blijft bewaard. | Are you sure you want to archive this source? The source disappears from the default list but is kept. |
| `status_wijzigen_bevestiging_terug` | Weet je zeker dat je deze bron terug wilt zetten naar Concept? De bron verschijnt opnieuw in de standaardlijst. | Are you sure you want to set this source back to Concept? The source reappears in the default list. |
| `toon_gearchiveerd` | Toon gearchiveerde | Show archived |
| `toon_gearchiveerd_tooltip` | Toon ook gearchiveerde imports in de lijst. | Also show archived imports in the list. |
| `status_kolom.concept` | Concept | Concept |
| `status_kolom.actief` | Actief | Active |
| `status_kolom.gearchiveerd` | Gearchiveerd | Archived |
| `kolom.status` | Status | Status |

### 5.4 Nieuwe dependencies

Geen nieuwe dependencies in 5D'.2e/f. De bestaande set blijft:
- `pypdf>=5.0`
- `requests>=2.31`
- `beautifulsoup4>=4.12`

### 5.5 Belangrijke ontwerpkeuzes (sinds 3.2.0)

- **Status wijzigen alleen voor eigen imports.** Ingebouwde documenten
  blijven read-only, ook in de status-editor.
- **Bevestigingsvraag bij ingrijpende overgangen.** Archiveren en terug
  naar Concept vragen bevestiging; activeren niet.
- **Toon gearchiveerde is een filter, geen opslagwijziging.** De
  checkbox beïnvloedt alleen de weergave.
- **`get_document` zoekt altijd beide cataloguslagen, inclusief
  gearchiveerd.** Reden: de Bewerken- en Status-knoppen moeten ook
  werken voor een gearchiveerd document dat zichtbaar is via de
  checkbox.
- **`include_archived` is een filter voor `list_documents`, niet voor
  `get_document`.**
- **Status-kolom is leeg voor ingebouwde documenten.** Ze hebben geen
  status.
- **Checkbox- en radio-indicator expliciet gestyled.** Fusion respecteert
  CSS, maar de default-indicator had te weinig contrast.

### 5.6 Bekende beperkingen

- **Geen OCR** voor gescande PDF's.
- **Geen Word/Excel-import** in fase 5. Voorbereiding voor fase 6.
- **Geen async URL-fetch.** Blokkeert de GUI tot 10s.
- **Datum-parsing bij bewerken** accepteert alleen ISO-formaat. Een
  oudere vrije-tekstwaarde valt terug op "Datum onbekend".
- **Geen bulk-edit** van meerdere imports.
- **Geen bulk-statuswijziging** van meerdere imports.
- **Geen reden bij archiveren.** Bewust geaccepteerd in 5D'.2e.

---

## 6. OPENSTAANDE VRAGEN VOOR DE NIEUWE CHAT

### 6.1 Welke fase starten?

De laatst afgeronde fase is **5D'.2f** (checkbox-indicator). Er zijn
drie logische volgende stappen:

**A. 5D'.1b — Metadata van imports doorzoekbaar maken (formaliseren)**

Het vrije zoekveld doorzoekt nu al de metadata van imports (omdat
`_search_blob` de velden meeneemt en `service.py` ze vult). Maar er is
nog geen formele test of documentatie voor dit gedrag.

- Tests toevoegen aan `test_documentation_service_user_catalog.py`.
- Documentatie bijwerken.
- **Geen codewijziging nodig.**

**B. 6 — Fabrikantdocument-import (Word, Excel)**

- `.docx` via `python-docx`.
- `.doc` weigeren met duidelijke melding.
- `.xlsx` via `openpyxl` (staat al in `requirements.txt`).
- Uitbreiding van de wizard met nieuwe bron-types.
- Nieuwe `ImportSourceType`-waarden of een aparte service.

**C. 5F-formalisering — Documentatie definitief afronden**

- Changelog, openvragen en overdracht zijn in deze sessie bijgewerkt.
- `docs/PROJECT_STRUCTURE.md` is deels bijgewerkt; formele generator
  ontbreekt nog.
- Geen functionele wijziging.

### 6.2 Open vragen per optie

**Voor 5D'.1b:**

1. Moet het zoeken op metadata ook formeel gedocumenteerd worden in
   `docs/documentation_import.md`?
2. Willen we een test die bevestigt dat **specifiek** op metadata wordt
   gezocht (bijv. op document_date of part_number)?

**Voor 6:**

1. Moet de wizard één type-keuze krijgen met vier opties (PDF / URL /
   Word / Excel), of aparte menu-items?
2. Moet Word/Excel ook een kopie naar `sources/` krijgen?
3. Hoe omgaan met `.doc` (oud Word-formaat)?
4. Moet Excel-extractie de cellen als tekst in de catalogus opslaan, of
   alleen het bestand kopiëren?
5. Nieuwe dependency `python-docx` toevoegen aan `requirements.txt`?

**Voor 5F-formalisering:**

1. Willen we een script om `PROJECT_STRUCTURE.md` te genereren?
2. Waar hoort dat script? (`tools/generate_project_structure.py`?)

### 6.3 Overige openstaande punten

- **Reden opgeven bij archiveren.** Bewust niet gedaan in 5D'.2e.
- **Filter voor alleen gearchiveerde documenten.** Nog niet aanwezig.
- **Bulk-edit en bulk-statuswijziging.** Nog niet ondersteund.
- **Word-import (`.docx` / `.doc`).** Fase 6.
- **Excel-import (`.xlsx`).** Fase 6.
- **OCR voor gescande PDF's.** Uitgesteld.
- **Async URL-fetch.** Fase 11.
- **Catalogusmigratie bij meerdere versies.** Nog niet nodig.
- **Light theme.** Uitgesteld naar fase 11.

---

## 7. TESTSTATUS — BASELINE EN TESTSTRUCTUUR

**Datum:** 2026-10-08
**Baseline:** 885 passed
**Werkwijze:** eerst gerichte tests, dan volledige `pytest -q`.

### 7.1 Commando's

```powershell
# Eerst gerichte tests van de fase
pytest tests/test_<fase>.py -q

# Daarna volledige suite
pytest -q