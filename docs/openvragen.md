# Openvragen en observaties — Electronics Diagnostic Tool Hub / ESR Tester

**Versie:** 1.1.0
**Datum:** 2026-10-07
**Auteur:** Bart Bossuyt
**Doel:** expliciet bijhouden wat nog onduidelijk, open of te verifiëren
is. Geen bugs, geen beloftes — alleen vragen en observaties.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie.
  v1.1.0 (2026-10-07)  §2 bijgewerkt na fase 5. Beantwoorde vragen
                       gemarkeerd. Nieuwe openstaande punten: Word-import,
                       OCR voor gescande PDF's, async URL-fetch,
                       catalogusmigratie bij meerdere versies.

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

## 2. Uit Fase 5 — Import-wizard en metadata

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

### 2.4 Menselijke goedkeuring — beantwoord

- Statusmachine: `CONCEPT → ACTIEF → GEARCHIVEERD` met terugkeer naar
  `CONCEPT` via `revoke`.
- Nieuwe import start altijd als `CONCEPT`.
- Een bron verwijderen is niet mogelijk; wel `archiveren` en
  `terugtrekken`.
- De editor in de viewer wijzigt geen status.

### 2.5 Assessment-koppeling — beantwoord

- De scheiding blijft gehandhaafd: `documentation_service` is read-only
  en raakt `assessment_service` niet aan.
- Een geïmporteerde bron wordt pas bruikbaar voor assessment nadat de
  gebruiker die expliciet `ACTIEF` maakt, en nadat een latere fase (12–14)
  de brug slaat.

### 2.6 Nieuwe openstaande punten (na 5D'.2c)

- **Status wijzigen vanuit de viewer.** Een gebruiker kan nu metadata
  bewerken, maar nog niet de status (concept → actief → gearchiveerd)
  aanpassen vanuit de documentatiebibliotheek. Dat is een logische
  volgende deelfase (5D'.2e of 5D'.3).
  - **Impact:** nieuwe knop(en) in de viewer, nieuwe service-aanroep
    (`set_status` bestaat al), i18n-keys, tests.
  - **Status:** open; voorstel voor 5D'.2e.
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
- **Catalogusmigratie bij meerdere versies.** `imported_catalog.json` heeft
  `schema_version=1`. Wat als we ooit velden toevoegen of wijzigen?
  - **Status:** nog niet nodig; migratie-mechanisme ontbreekt.
- **Datum-parsing bij bewerken.** De editor accepteert alleen ISO-datums
  (`YYYY-MM-DD`). Een oudere vrije-tekstwaarde (bijv. `"2024-01"`) valt
  terug op "Datum onbekend" bij openen, wat bij opslaan `document_date`
  op `null` zet.
  - **Impact:** gegevenswijziging zonder expliciete waarschuwing.
  - **Status:** bewust geaccepteerd in 5D'.2c; mogelijk verfijnen in
    fase 11.
- **Bulk-edit van meerdere imports.** Nog niet ondersteund.
  - **Status:** open; geen concrete vraag.

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

---

## 5. Status van dit document

- Dit document is **levend**. Bij elke fase mogen nieuwe vragen worden
  toegevoegd en opgeloste vragen worden gemarkeerd.
- Opgeloste vragen blijven staan voor historische context.