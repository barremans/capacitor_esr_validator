# Documentatie-import — ontwikkelaarsreferentie

**Versie:** 1.3.0
**Datum:** 2026-10-09
**Auteur:** Bart Bossuyt
**Doel:** technische referentie voor de documentatie-import-laag.
Bevat architectuur, datamodel, opslaglocaties, foutafhandeling en
uitbreidingspunten. Geen gebruikersdocumentatie — zie `docs/changelog.md`
voor de eindgebruikersversie.

**Status:** stabiel voor schema_version 1. Geldt voor fase 5 (PDF/URL),
5D'.2e (statusbeheer), 5D'.1b (metadata doorzoekbaar) en 6 (Word/Excel).

Wijzigingen:
  v1.0.0 (2026-10-07)  Eerste versie: architectuur, datamodel,
                       opslaglocaties, metadata-uitbreiding 5D'.2b/d.
  v1.1.0 (2026-10-08)  Secties toegevoegd over statusbeheer (5D'.2e):
                       statusmachine, statuswijzigen in de viewer,
                       Toon gearchiveerde-filter en Status-kolom.
                       Robuustheid op Windows (_atomic_replace) beschreven.
  v1.2.0 (2026-10-09)  Sectie toegevoegd over doorzoekbare metadata van
                       imports (5D'.1b): welke velden in _search_blob
                       zitten, welke niet, en de formele regressietests.
  v1.3.0 (2026-10-09)  Sectie toegevoegd over Word- en Excel-import
                       (fase 6): docx_extract, xlsx_extract,
                       docx_import, xlsx_import, en de weigering van
                       .doc en .xls.

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
| `app/documentation/docx_extract.py` | Word-metadata, tekstextractie, SHA-256, kopiëren | Nee | Nee |
| `app/documentation/docx_import.py` | Orkestratie: hash → metadata → registratie → kopie | Nee | Nee |
| `app/documentation/xlsx_extract.py` | Excel-metadata, celinhoud, SHA-256, kopiëren | Nee | Nee |
| `app/documentation/xlsx_import.py` | Orkestratie: hash → metadata → registratie → kopie | Nee | Nee |
| `app/documentation/url_fetch.py` | URL-metadata, HTML-fetch, snapshot opslaan | **Ja** | Nee |
| `app/documentation/url_import.py` | Orkestratie: metadata → content → registratie → snapshot | **Ja** | Nee |
| `app/documentation/service.py` | Read-only viewer, ook voor imports (`is_user_import=True`) | Nee | Nee |
| `app/gui/dialogs/import_wizard_dialog.py` | Wizard-UI | Nee (roept services aan) | Ja |
| `app/gui/dialogs/edit_metadata_dialog.py` | Metadata-editor | Nee | Ja |
| `app/gui/dialogs/change_status_dialog.py` | Status-editor | Nee | Ja |

**Enige module met netwerktoegang:** `url_fetch.py`. Alle andere modules
zijn puur lokaal.

---

## 3. Datamodel — `ImportSource`

```python
@dataclass(frozen=True, slots=True)
class ImportSource:
    source_id: str                    # UUID4, verplicht, niet leeg
    source_type: ImportSourceType     # PDF / URL / DOCX / XLSX
    title: str                        # verplicht, niet leeg
    imported_at: int                  # Unix ms, positief
    imported_by: str                  # vrije tekst, bv. Windows-gebruikersnaam
    status: ImportStatus              # CONCEPT / ACTIEF / GEARCHIVEERD
    original_filename: Optional[str]  # alleen PDF/DOCX/XLSX
    source_url: Optional[str]         # alleen URL
    file_hash: Optional[str]          # alleen PDF/DOCX/XLSX, SHA-256 hex
    notes: Optional[str]              # optioneel, vrije tekst
    category: Optional[str]           # DocumentCategory-waarde
    manufacturer: Optional[str]       # uppercase
    series: Optional[str]             # uppercase
    part_number: Optional[str]        # uppercase
    document_version: Optional[str]   # uppercase
    document_date: Optional[str]      # ISO-datum YYYY-MM-DD