# Documentation Catalog Architecture

**Doel:** Vastleggen van de architectuur en het toekomstige splitsingspad van
de centrale documentatiecatalogus (`app/data/documentation/catalog.json`).

**Status:** architectuurnotitie — geen implementatie, geen code, geen service-wijziging.

**Datum:** 2026-10-04
**Auteur:** Bart Bossuyt
**Gerelateerd:** `app/documentation/service.py`, `app/documentation/models.py`,
`app/data/documentation/catalog.json`

---

## 1. Huidige situatie

De centrale documentatiebibliotheek gebruikt op dit moment **één enkel
JSON-bestand**:

```text
app/data/documentation/
├── catalog.json
└── internal/
    ├── nl_NL/
    └── en_US/