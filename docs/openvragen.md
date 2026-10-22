# Openvragen en observaties — Electronics Diagnostic Tool Hub / ESR Tester

**Versie:** 3.7.0
**Datum:** 2026-10-22
**Auteur:** Bart Bossuyt
**Doel:** expliciet bijhouden wat nog onduidelijk, open of te verifiëren
is. Geen bugs, geen beloftes — alleen vragen en observaties.

Wijzigingen:
  v1.0.0 t/m v3.5.0  zie eerdere versies.
  v3.6.0 (2026-10-22)  §2.16 en §2.20 gemarkeerd als opgelost in
                       11I.1 t/m 11I.4. Nieuwe subsectie 4.39
                       (opgeloste punten in 11I).
  v3.7.0 (2026-10-22)  §2.14 volledig gemarkeerd als opgelost in 12E
                       (scope "filters"). Nieuwe subsectie 4.40
                       (opgeloste punten in 12A) en 4.41 (opgeloste
                       punten in 12E). §2.28 staat nu als "volgende
                       opdracht".

---

## 1. Uit Fase 4I — Zoektaal-observaties

Onveranderd t.o.v. v3.6.0.

---

## 2. Uit Fase 5, 6, 7, 8, 9, 10, 11 en later

### 2.1 t/m 2.5 — beantwoord

Zie eerdere versies.

### 2.6 Nieuwe openstaande punten (na 5D'.2e)

- **Async URL-fetch.** **Opgelost in 11E.2.**
- **Archiefreden.** **Opgelost in 11F.1.**
- De overige punten uit §2.6 blijven open; zie eerdere versies.

### 2.7 t/m 2.8 — beantwoord

Zie eerdere versies.

### 2.9 Cosmetische scrollbar in Word-samenvatting

- **Status:** **opgelost in 11G.2.**

### 2.10 t/m 2.13 — beantwoord

Zie eerdere versies.

### 2.11 Analyse-pagina: as-schaling, tickformaat, zoom/pan

- **Status:** **opgelost in 11G.3 en 11G.4.**

### 2.12 t/m 2.13 — beantwoord

Zie eerdere versies.

### 2.14 Nieuwe openstaande punten (na fase 8D)

- **GUI voor scope "selectie" en "filters".** **Volledig opgelost in
  11A.2 (selectie) en 12E (filters).** `ReportDialog` heeft nu drie
  ingangen: `ReportDialog(id, ...)` (enkelvoudig),
  `ReportDialog.for_measurements(ids, ...)` (selectie) en
  `ReportDialog.for_filters(filters, ...)` (huidige filters). Zowel
  `HistoryScreen._show_report_for_selected` als
  `AnalysisScreen._open_report_for_selection` kiezen de juiste
  ingang automatisch.
- **Menu-item "Rapport maken…" disabled maken zonder selectie.**
  **Opgelost in 11A.1.**
- **PDF-fonts op Windows.** Opgelost in 9A.
- **Cosmetische opruiming i18n-keys.** **Opgelost in 11F.4.**
- **Statusfilter in de documentatiebibliotheek.** **Opgelost in 11F.2.**

### 2.15 t/m 2.20 — beantwoord

Zie eerdere versies.

### 2.16 pandas/numpy pins heroverwegen (toegevoegd 2026-10-13)

- **Status:** **opgelost in 11I.1.** De pins zijn bewust:
  `numpy>=1.26,<3` en `pandas>=2.2,<3`. De bovengrens beschermt
  tegen een major-bump die de PyInstaller-bundel of de pandas-API's
  kan breken. Motivatie staat in `requirements.txt` v1.1.0 en in
  `docs/packaging.md` §2.1.

### 2.17 t/m 2.19 — beantwoord

Zie eerdere versies.

### 2.20 Cosmetische en build-technische punten (toegevoegd 2026-10-13)

- **Relatief `icon_path`.** **Opgelost in 11I.2.**
- **`Architecture identifier "x64" is deprecated`.** **Opgelost in
  11I.3.**
- **`[rename] Fallback via robocopy`-melding.** **Opgelost in 11I.3.**
- **`build_log.txt` blijft leeg.** **Opgelost in 11I.3.**
- **Certificaten opruimen.** **Opgelost in 11I.4.**

### 2.21 Drie visuele punten uit de 9F-sessie (2026-10-14)

- **Visuele selectie in Analyse.** **Opgelost in 11A.1** (compacte
  selectielijst) **en 11G.5** (klikbare datapunten, selectie-gedreven
  scope).
- **Checkbox-zichtbaarheid in donker thema.** **Deels opgelost in
  11G.1** (focus-states, tabel-indicator, groupbox-indicator). De
  filter-checkbox is verder opgelost in 11G.7.
- **i18n-menging in Diagnose/Result en Resultaatdetails.** **Opgelost
  in 11D.**

### 2.22 t/m 2.23 — beantwoord

Zie eerdere versies.

### 2.24 Update-melding cosmetica (na 9H)

- **Async `fetch_release_notes()`.** **Opgelost in 11E.1.**
- **Drie-knoppenmelding forceren voor QA.** **Opgelost in 11E.3.**
- De overige punten uit §2.24 blijven open; zie eerdere versies.

### 2.25 Export respecteert de selectie niet (toegevoegd 2026-10-15)

- **Status:** **opgelost in 11A.1.**

### 2.26 Betrouwbaarheidsregel verbergt goede resultaten (toegevoegd 2026-10-15)

- **Status:** **opgelost in 11B.**

### 2.27 Alle vensters een gepast icoon (toegevoegd 2026-10-15)

- **Status:** **opgelost in 11C.**

### 2.28 Metingen exporteren/importeren voor samenvoegen tussen toestellen (toegevoegd 2026-10-15)

- **Status:** **open; volgende opdracht.** Dit is een aparte fase,
  geen restpost van 12. De exacte sub-fase-indeling wordt bij de
  start bepaald. Vereist doordachte keuzes over het exportformaat
  (JSON-envelope vs. SQLite-dump), de duplicate-/conflictregels en
  de herkomst-tracking. Raakt `storage/schema.py`,
  `storage/service.py`, `storage/models.py`, `history_service.py`,
  de GUI en mogelijk een nieuw exportformaat.

### 2.29 Mapvoorkeuren respecteren (toegevoegd 2026-10-15)

- **Status:** **opgelost in 11A.3** via
  `app/helpers/dialog_start_directory.py`.

### 2.30 Filter-checkbox zichtbaarheid (toegevoegd 2026-10-20)

- **Status:** **opgelost in 11G.7.**

---

## 3. Uit vroegere contextdocumenten (nog steeds relevant)

Onveranderd t.o.v. v3.6.0.

---

## 4. Uit eigen observaties tijdens recente fases

Onveranderd t.o.v. v3.6.0, plus:

### 4.37 Opgeloste punten in 11G.7 (2026-10-20)

Onveranderd t.o.v. v3.6.0.

### 4.38 Opgeloste punten in 11H (2026-10-21)

Onveranderd t.o.v. v3.6.0.

### 4.39 Opgeloste punten in 11I (2026-10-22)

Onveranderd t.o.v. v3.6.0.

### 4.40 Opgeloste punten in 12A (2026-10-22)

- **Uniform extractiemodel.** `app/documentation/extraction_models.py`
  v1.0.0 met `ExtractionResult`, `ExtractionError` en
  `ExtractionSourceKind` (PDF/DOCX/XLSX/URL). Frozen, slots,
  validatie in `__post_init__`.
- **Uniforme extractie-dispatcher.**
  `app/documentation/extraction_service.py` v1.0.0 met
  `extract_for_source`, `extract_for_path` en `extract_for_url`.
  Roept de bestaande extractors aan en vertaalt hun resultaat naar
  het uniforme model. Lokale URL-teksthepler via BeautifulSoup,
  zodat `url_fetch.py` niet gewijzigd hoefde te worden.
- **Bestaande modules ongewijzigd:** `pdf_extract.py`,
  `docx_extract.py`, `xlsx_extract.py`, `url_fetch.py`,
  `import_service.py`, `import_models.py` en de vier `*_import.py`
  zijn onaangeroerd.
- **Nieuwe tests:** `tests/test_documentation_extraction_models.py`
  v1.0.0 (15 tests) en
  `tests/test_documentation_extraction_service.py` v1.0.0
  (22 tests).
- **Baseline:** 1548 → **1585 passed** (+37 tests).

### 4.41 Opgeloste punten in 12E (2026-10-22)

- **§2.14 — scope "filters" in de Rapportage-GUI.** Volledig
  opgelost:
  - `app/gui/dialogs/report_dialog.py` v1.6.1 met classmethod
    `for_filters`, `_kop_tekst`-helper en kop-update in
    `_laad_bundle`.
  - `app/gui/history_screen.py` v1.19.0 met drie modi in
    `_show_report_for_selected` en een `_heeft_actieve_filters`-
    helper.
  - `app/gui/analysis_screen.py` v1.7.2 met drie modi in
    `_open_report_for_selection` en een `_heeft_actieve_filters`-
    helper die uitsluitend naar de GUI-velden kijkt.
- **Bugfix in `AnalysisScreen._heeft_actieve_filters()`:** de
  helper gaf altijd `True` omdat `_active_filters()` altijd
  `tool_key="ESR_CAPACITOR"` bevat. Opgelost in v1.7.2.
- **Bugfix in `ReportDialog.kop_label`:** toonde "0 metingen"
  voor de filters-modus omdat `_build_ui()` vóór `_laad_bundle()`
  loopt. Opgelost in v1.6.1.
- **Nieuwe tests:** `tests/test_report_dialog_scope_filters.py`
  v1.0.1 (13 tests).
- **Baseline:** 1585 → **1598 passed** (+13 tests).

---

## 5. Status van dit document

- Dit document is **levend**. Bij elke fase mogen nieuwe vragen worden
  toegevoegd en opgeloste vragen worden gemarkeerd.
- Opgeloste vragen blijven staan voor historische context.