# Documentatie-import — ontwikkelaarsreferentie

**Versie:** 1.0.0
**Datum:** 2026-10-07
**Auteur:** Bart Bossuyt
**Doel:** technische referentie voor de documentatie-import-laag.
Bevat architectuur, datamodel, opslaglocaties, foutafhandeling en
uitbreidingspunten. Geen gebruikersdocumentatie — zie `docs/changelog.md`
voor de eindgebruikersversie.

**Status:** stabiel voor schema_version 1. Geldt voor fase 5 (PDF/URL-import).

---

## 1. Positie in de architectuur

De import-laag staat **los** van de documentatie-viewer en van het
assessment. De drie verantwoordelijkheden blijven gescheiden:

| Laag | Verantwoordelijkheid | Mag schrijven? |
|---|---|---|
| `documentation_service` | Read-only zoeken, lezen en openen van documenten | Nee |
| `import_*` (deze referentie) | Registreren en bewaren van externe bronnen | Ja, in eigen catalogus |
| `assessment_service` | Beoordelingslogica | Nee (raakt import niet) |

De import-laag raakt **nooit** de ingebouwde `catalog.json`. Alles wat
geïmporteerd wordt, leeft in een **tweede cataloguslaag** onder
`%LOCALAPPDATA%`.

---

## 2. Bestandsstructuur

| Bestand | Verantwoordelijkheid | Netwerk? | Qt? |
|---|---|---|---|
| `app/documentation/import_models.py` | Immutable modellen, enums, statusmachine | Nee | Nee |
| `app/documentation/import_service.py` | Registratie, statusovergangen, JSON-persistentie | Nee | Nee |
| `app/documentation/pdf_extract.py` | PDF-metadata, tekstextractie, SHA-256, kopiëren | Nee | Nee |
| `app/documentation/pdf_import.py` | Orkestratie: hash → metadata → registratie → kopie | Nee | Nee |
| `app/documentation/url_fetch.py` | URL-metadata, HTML-fetch, snapshot opslaan | **Ja** | Nee |
| `app/documentation/url_import.py` | Orkestratie: metadata → content → registratie → snapshot | **Ja** | Nee |
| `app/gui/dialogs/import_wizard_dialog.py` | Wizard-UI | Nee (roept services aan) | Ja |

**Enige module met netwerktoegang:** `url_fetch.py`. Alle andere modules
zijn puur lokaal.

---

## 3. Datamodel — `ImportSource`

```python
@dataclass(frozen=True, slots=True)
class ImportSource:
    source_id: str                    # UUID4, verplicht, niet leeg
    source_type: ImportSourceType     # PDF of URL
    title: str                        # verplicht, niet leeg
    imported_at: int                  # Unix ms, positief
    imported_by: str                  # vrije tekst, bv. Windows-gebruikersnaam
    status: ImportStatus              # CONCEPT / ACTIEF / GEARCHIVEERD
    original_filename: Optional[str]  # alleen PDF
    source_url: Optional[str]         # alleen URL
    file_hash: Optional[str]          # alleen PDF, SHA-256 hex
    notes: Optional[str]              # optioneel, vrije tekst

## Metadata bij importeren

Sinds fase 5D'.2b bevat de import-wizard een metadata-sectie.

### Velden

| Veld | Verplicht | Opmerking |
|---|---|---|
| Categorie | Ja | Default `DATASHEET`. Dropdown met de 7 `DocumentCategory`-waarden. |
| Fabrikant | Nee | Wordt automatisch in uppercase gezet bij typen. |
| Serie | Nee | Idem. |
| Partnummer | Nee | Idem. |
| Documentversie | Nee | Idem. |
| Documentdatum | Nee | Kalenderveld, ISO-formaat `YYYY-MM-DD`. Checkbox "Datum onbekend" voor `None`. Ctrl+D = vandaag. |
| Notities | Nee | Vrije tekst, geen uppercase. |

### Opslag

Metadata wordt opgeslagen in `imported_catalog.json` onder elke
`ImportSource`:

```json
{
  "source_id": "…",
  "source_type": "pdf",
  "title": "CHONGCD11XSERIES",
  "imported_at": 1791438042560,
  "imported_by": "BBossuyt",
  "status": "concept",
  "original_filename": "CHONGCD11XSERIES.pdf",
  "source_url": null,
  "file_hash": "57a3da2a…",
  "notes": null,
  "category": "DATASHEET",
  "manufacturer": "CHONG",
  "series": "CDX",
  "part_number": null,
  "document_version": "V1.1",
  "document_date": "2026-10-08"
}