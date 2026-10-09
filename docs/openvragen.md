
---

## Bestand 3: `docs/openvragen.md`

**Versie:** 1.2.0 → 1.3.0
**Wijziging:** §2.6 bijgewerkt — "Metadata van imports doorzoekbaar maken" is nu beantwoord.

```markdown
# Openvragen en observaties — Electronics Diagnostic Tool Hub / ESR Tester

**Versie:** 1.3.0
**Datum:** 2026-10-09
**Auteur:** Bart Bossuyt
**Doel:** expliciet bijhouden wat nog onduidelijk, open of te verifiëren
is. Geen bugs, geen beloftes — alleen vragen en observaties.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie.
  v1.1.0 (2026-10-07)  §2 bijgewerkt na fase 5. Beantwoorde vragen
                       gemarkeerd. Nieuwe openstaande punten: Word-import,
                       OCR voor gescande PDF's, async URL-fetch,
                       catalogusmigratie bij meerdere versies.
  v1.2.0 (2026-10-08)  §2.4 en §2.5 bijgewerkt na 5D'.2e (status
                       wijzigen in viewer). Nieuwe openstaande punten:
                       status-reden bij archiveren, filter voor
                       gearchiveerd, statustransitie-beleid,
                       catalogusmigratie bij statuswijzigingen.
  v1.3.0 (2026-10-09)  §2.7 toegevoegd: metadata van imports
                       doorzoekbaar maken (5D'.1b) — beantwoord met
                       formele regressietests. Geen codewijziging.

---

## 1. Uit Fase 4I — Zoektaal-observaties

Deze zijn in 4I.1 afgewerkt, maar blijven relevant voor latere fases
(vooral Fase 11 — Laatste UX/documentatie-afwerking).

### 1.1 `!` is substring-uitsluiting

- **Status:** verduidelijkt in 4I.1.a (eindgebruikershelp).
- **Restvraag:** blijft dit de gewenste semantiek, of moet er ooit een
  exact-woord uitsluiting komen?
- **Impact:** nieuwe operator of nieuwe prefix zou parser + AST + tests
  raken.

### 1.2 `-%term` heeft geen eenduidige betekenis

- **Status:** opgelost in 4I.1.b (stil genegeerd, optie A1).
- **Restvraag:** moet er ooit een correcte interpretatie komen
  (bv. exact-woord met wildcard)?
- **Impact:** zou een nieuwe tak in `_term_matches` vragen.

### 1.3 Geen haakjes, geen veldnamen, geen datums

- **Status:** bewust gedocumenteerd in `docs/search_syntax.md` §8.1.
- **Restvraag:** wordt dit een probleem zodra de catalogus groeit (50+
  documenten, meerdere beheerders)?
- **Impact:** zou een echte tokenizer en geneste AST vragen.

---

## 2. Uit Fase 5 — Import-wizard, metadata en statusbeheer

### 2.1 Scope — beantwoord

- **PDF-import:** lokaal bestand op schijf, gekopieerd naar
  `%LOCALAPPDATA%\ElectronicsDiagnosticToolHub\documentation\sources\`.
- **URL-import:** ruwe HTML-snapshot, lokaal bewaard in
  `...\documentation\snapshots\`. De URL blijft als metadata bewaard.
- **Geen scraping, geen JavaScript-uitvoering, geen OCR.**

### 2.2 Provenance — beantwoord

- Verplichte velden: `source_id`, `source_type`, `title`, `imported_at`,
  `imported_by`, `status`.
- Type-specifiek verplicht: `original_filename` (PDF) of `source_url` (URL).
- Optioneel: `file_hash` (PDF), `notes`.
- Eén `ImportSource` = één document.

### 2.3 Metadata — beantwoord (5D'.2b en 5D'.2d)

- **Velden in de wizard:** categorie (verplicht, default DATASHEET),
  fabrikant, serie, partnummer, documentversie, documentdatum, notities
  (alle optioneel).
- **Identificatievelden in uppercase:** fabrikant, serie, partnummer,
  documentversie. Titel en notities blijven gemengd; documentdatum is
  een kalenderveld.
- **Documentdatum:** ISO-formaat `YYYY-MM-DD`, met "Datum onbekend"-
  checkbox. Ctrl+D zet op vandaag.
- **Bewerken in de viewer:** ja, sinds 5D'.2c. Alleen voor eigen imports
  (`is_user_import=True`). Bronbestand, status en importdatum blijven
  ongewijzigd.
- **Ingebouwde catalogus:** blijft read-only, voor altijd.

### 2.4 Statusbeheer — beantwoord (5D'.2e)

- **Statusmachine:** `CONCEPT → ACTIEF → GEARCHIVEERD`, met `revoke`
  terug naar `CONCEPT`.
- **Wijzigen in de viewer:** ja, sinds 5D'.2e. Alleen voor eigen imports
  (`is_user_import=True`). De dialoog toont alleen de toegelaten
  overgangen (afgeleid van `_ALLOWED_TRANSITIONS` in `import_models`).
- **Bevestigingsvraag:** bij archiveren en bij terug naar Concept.
  Niet bij Concept → Actief.
- **Filter:** checkbox "Toon gearchiveerde" naast de tool-dropdown.
  Standaard uit.
- **Status-kolom:** ja, sinds 5D'.2e. Tussen Categorie en Fabrikant.
  Leeg voor ingebouwde documenten.
- **Nieuwe import start altijd als `CONCEPT`.**
- **Een bron verwijderen is niet mogelijk;** wel archiveren en
  terugtrekken.

### 2.5 Assessment-koppeling — beantwoord

- De scheiding blijft gehandhaafd: `documentation_service` is read-only
  en raakt `assessment_service` niet aan.
- Een geïmporteerde bron wordt pas bruikbaar voor assessment nadat de
  gebruiker die expliciet `ACTIEF` maakt, en nadat een latere fase (12–14)
  de brug slaat.

### 2.6 Nieuwe openstaande punten (na 5D'.2e)

- **Reden opgeven bij archiveren.** In 5D'.2e is bewust gekozen voor
  géén verplichte reden, om een nieuw modelveld + catalogusmigratie te
  vermijden. De gebruiker kan een reden kwijt in de notities.
  - **Restvraag:** willen we in een latere fase (6 of 11) een optioneel
    `archive_reason`-veld toevoegen?
  - **Impact:** nieuw veld in `ImportSource`, extra rij in de dialoog,
    i18n-keys.
  - **Status:** open; geen concrete vraag.
- **Filter voor gearchiveerde documenten.** Sinds 5D'.2e is er een
  checkbox "Toon gearchiveerde". Er is nog geen filter om **alleen**
  gearchiveerde documenten te tonen (inverse filter).
  - **Restvraag:** is dat nuttig, of volstaat de huidige aanpak?
  - **Status:** open; klein.
- **Statustransitie-beleid.** De toegelaten overgangen staan nu hard
  gecodeerd in `_ALLOWED_TRANSITIONS`. Wat als een gebruiker ooit
  `GEARCHIVEERD → ACTIEF` wil, of `CONCEPT → CONCEPT` (no-op)?
  - **Restvraag:** blijft de huidige set definitief, of wordt dit
    configureerbaar?
  - **Status:** bewust beperkt gehouden; geen concrete vraag.
- **Catalogusmigratie bij statuswijzigingen.** `imported_catalog.json`
  heeft `schema_version=1`. Statuswijzigingen wijzigen alleen het
  `status`-veld; ze vragen geen schemawijziging.
  - **Restvraag:** wat als we ooit velden toevoegen (bv.
    `archive_reason`)? Migratie-mechanisme ontbreekt nog.
  - **Status:** nog niet nodig.
- **Word-import (`.docx` / `.doc`).** Moet later worden toegevoegd.
  - `.docx` kan via `python-docx` (pure Python, MIT).
  - `.doc` (oud) vereist `pywin32` + Word-installatie; waarschijnlijk
    weigeren met een duidelijke melding.
  - **Status:** voorbereiding voor fase 6 (Fabrikantdocument-import).
- **Excel-import (`.xlsx`).** `openpyxl` staat al in `requirements.txt`.
  Zelfde deelfase als Word?
- **OCR voor gescande PDF's.** `pypdf` kan geen tekst uit
  afbeeldings-PDF's halen. Willen we ooit OCR?
  - **Impact:** zware dependency, breekt "licht en lokaal".
  - **Status:** uitstellen tot er concrete noodzaak is.
- **Async URL-fetch.** De huidige fetch is synchroon en blokkeert de GUI
  tot 10 seconden.
  - **Status:** open; overwegen in fase 11.
- **Datum-parsing bij bewerken.** De editor accepteert alleen ISO-datums
  (`YYYY-MM-DD`). Een oudere vrije-tekstwaarde (bijv. `"2024-01"`) valt
  terug op "Datum onbekend" bij openen, wat bij opslaan `document_date`
  op `null` zet.
  - **Impact:** gegevenswijziging zonder expliciete waarschuwing.
  - **Status:** bewust geaccepteerd in 5D'.2c; mogelijk verfijnen in
    fase 11.
- **Bulk-edit van meerdere imports.** Nog niet ondersteund.
  - **Status:** open; geen concrete vraag.
- **Bulk-statuswijziging van meerdere imports.** Nog niet ondersteund.
  - **Status:** open; geen concrete vraag.

### 2.7 Metadata van imports doorzoekbaar — beantwoord (5D'.1b)

- **Vraag:** is het vrije zoekveld in de documentatiebibliotheek van
  toepassing op de metadata van imports?
- **Antwoord:** ja. Sinds v1.7.0 van `service.py` neemt `_search_blob`
  de menselijke metadata op: titel, categorie, fabrikant, serie,
  partnummer, documentversie, documentdatum, notities en bron-URL.
- **Formele regressietests:** toegevoegd in 5D'.1b aan
  `tests/test_documentation_service_user_catalog.py`. Per veld één test,
  plus negatieve tests voor `document_id` en `source_path`, plus
  combinatietests met `include_archived`.
- **Documentatie:** sectie 4 in `docs/documentation_import.md`.
- **Geen codewijziging nodig.** `_search_blob` was al correct.
- **Status:** afgerond.

---

## 3. Uit vroegere contextdocumenten (nog steeds relevant)

### 3.1 V-Loss

- **Bron:** `Context_ESR.md` §6.
- **Vraag:** wat toont het TEKCOPLUS-display exact bij een
  condensatormeting?
- **Vraag:** komt V-Loss van dit toestel of van een ander toestel?
- **Vraag:** is een foto van het display beschikbaar?
- **Status:** V-Loss blijft optioneel en ongedefinieerd; geen
  automatische goed/afkeur op basis van V-Loss.

### 3.2 TEKCOPLUS-display en exportstructuur

- **Vraag:** wat toont het display exact bij een condensatormeting?
- **Vraag:** is er een officiële handleiding beschikbaar?
- **Vraag:** is een voorbeeld van de Excel-export beschikbaar?
- **Status:** handmatige invoer blijft de standaard.

### 3.3 Praktijkvalidatie

- **Vraag:** hoe sterk verandert ESR tussen 100 Hz, 1 kHz en 10 kHz?
- **Vraag:** hoe sterk verandert capaciteit?
- **Vraag:** heeft 0,3 vs 0,6 Vrms praktische betekenis?
- **Vraag:** hoe reproduceerbaar is de LCR-ST1?
- **Vraag:** hoe groot is het verschil tussen EX_SITU, ONE_LEG en
  IN_CIRCUIT?
- **Vraag:** zijn de huidige app-drempels praktisch bruikbaar?
- **Status:** Fase 10 — Praktische ESR-validatie.

### 3.4 Referentiedata

- **Vraag:** welke condensatortypes komen in de praktijk het meest voor?
- **Vraag:** is de eerste scope uitsluitend aluminium elektrolytisch?
- **Vraag:** welke datasheetmerken en series worden vaak gebruikt?
- **Vraag:** moet de gebruiker zelf referentietabellen kunnen toevoegen?
- **Status:** open; relevant voor Fase 6 en later.

### 3.5 Rapportage

- **Vraag:** moeten resultaten als meetrapport kunnen worden
  afgedrukt?
- **Vraag:** moeten Frans en Engels later worden ondersteund?
- **Vraag:** is een tweede LCR-meter beschikbaar voor vergelijking?
- **Vraag:** welke foutmarge is aanvaardbaar voor de interne
  consistentiecontrole?
- **Status:** Fase 8 — Rapportage.

### 3.6 Override van automatische beoordeling

- **Vraag:** moet een gebruiker een automatische beoordeling manueel
  kunnen overrulen?
- **Vraag:** moet die override met reden worden gelogd?
- **Status:** open; relevant voor Fase 11 — Laatste UX.

### 3.7 Praktische meetgegevens

- **Vraag:** hoe lang na ontlading kunnen grote elektrolyten spanning
  opbouwen?
- **Vraag:** is er een praktisch verschil gemeten tussen "één been los"
  en "volledig uitgebouwd"?
- **Vraag:** welke ontlademethode wordt gebruikt (weerstand, lamp,
  kortsluiting)?
- **Vraag:** wordt er een multimeter gebruikt voor restspanningscontrole
  vóór LCR-meting?
- **Vraag:** hoe vaak komt in-circuit meten voor in de praktijk vs
  uitbouw?
- **Status:** Fase 10 — Praktische ESR-validatie.

---

## 4. Uit eigen observaties tijdens recente fases

### 4.1 Help per taal — nog niet alle talen gedekt

- Momenteel: `nl_NL.md` en `en_US.md`.
- Toekomstige talen: bestand `docs/help/<taal>.md` plaatsen,
  geen codewijziging.
- **Vraag:** willen we een Nederlandstalige fallback voor alle talen,
  of moet er ooit een Engelse fallback komen voor niet-EU-talentoekomst?

### 4.2 Testdekking van i18n-keys

- Nieuwe keys moeten expliciet gemeld worden in de chat.
- **Vraag:** willen we een geautomatiseerde check dat alle keys in
  beide locales aanwezig zijn?
- **Impact:** zou een nieuwe test in `tests/test_i18n_*` vragen.
- **Status:** bewust nog niet toegevoegd; de huidige tests dekken de
  meest gebruikte keys.

### 4.3 Projectstructuur-document

- `docs/PROJECT_STRUCTURE.md` wordt "automatisch gegenereerd" volgens
  de header.
- **Vraag:** welk script genereert dit? Moet dat meegecommit worden?
- **Impact:** klein, maar relevant voor nieuwe ontwikkelaars.

### 4.4 Thema-uitbreiding — light theme

- Momenteel is alleen `apply_dark_theme()` aanwezig in
  `app/gui/styles.py`.
- **Vraag:** willen we een licht thema als alternatief?
- **Impact:** zou een refactor van `styles.py` vragen naar
  kleurconstanten (`PALET_DARK` / `PALET_LIGHT`) en een
  `apply_theme(app, palet)`.
- **Status:** uitgesteld; bewust nog niet gedaan in 5E om de
  kleine-stappen-regel te respecteren.

### 4.5 Checkbox- en radio-indicator in donker thema

- **Status:** opgelost in 5D'.2f. De `QCheckBox::indicator` en
  `QRadioButton::indicator` hebben nu expliciete styling.
- **Restvraag:** willen we in een latere fase ook de **tri-state**
  checkbox (partially checked) stylen? Niet nodig vandaag.
- **Impact:** klein.

---

## 5. Status van dit document

- Dit document is **levend**. Bij elke fase mogen nieuwe vragen worden
  toegevoegd en opgeloste vragen worden gemarkeerd.
- Opgeloste vragen blijven staan voor historische context.