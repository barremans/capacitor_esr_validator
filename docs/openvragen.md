# Openvragen en observaties — Electronics Diagnostic Tool Hub / ESR Tester

**Versie:** 3.5.0
**Datum:** 2026-10-21
**Auteur:** Bart Bossuyt
**Doel:** expliciet bijhouden wat nog onduidelijk, open of te verifiëren
is. Geen bugs, geen beloftes — alleen vragen en observaties.

Wijzigingen:
  v1.0.0 t/m v3.4.0  zie eerdere versies.
  v3.5.0 (2026-10-21)  §4.4 (light theme) volledig opgelost in
                       11H.1 t/m 11H.5. Nieuwe subsectie 4.38
                       (opgeloste punten in 11H).

---

## 1. Uit Fase 4I — Zoektaal-observaties

Onveranderd t.o.v. v3.4.0.

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

- **GUI voor scope "selectie" en "filters".** Deels opgelost: 11A.2
  levert scope "selectie" via `ReportDialog.for_measurements`. Scope
  "filters" in de Rapportage-GUI blijft open.
- **Menu-item "Rapport maken…" disabled maken zonder selectie.**
  **Opgelost in 11A.1.**
- **PDF-fonts op Windows.** Opgelost in 9A.
- **Cosmetische opruiming i18n-keys.** **Opgelost in 11F.4.**
- **Statusfilter in de documentatiebibliotheek.** **Opgelost in 11F.2.**

### 2.15 t/m 2.20 — beantwoord

Zie eerdere versies.

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

- **Status:** open; uitgesteld naar een latere sub-fase (niet 11E).

### 2.29 Mapvoorkeuren respecteren (toegevoegd 2026-10-15)

- **Status:** **opgelost in 11A.3** via
  `app/helpers/dialog_start_directory.py`.

### 2.30 Filter-checkbox zichtbaarheid (toegevoegd 2026-10-20)

- **Status:** **opgelost in 11G.7.** `styles.py` v1.6.0 geeft
  `QGroupBox::indicator` een lichtere achtergrond (`#3C3C3C`) en een
  dikkere rand (2px `#B0B0B0`) in unchecked-state. Checked-state is
  blauw (`#0078D7`) met 2px rand (`#4AA3FF`). De checkbox links van
  "Filters" valt niet meer weg tegen de groupbox-rand.

---

## 3. Uit vroegere contextdocumenten (nog steeds relevant)

Onveranderd t.o.v. v3.4.0.

---

## 4. Uit eigen observaties tijdens recente fases

Onveranderd t.o.v. v3.4.0, plus:

### 4.37 Opgeloste punten in 11G.7 (2026-10-20)

- **§2.30 — filter-checkbox zichtbaarheid.** `styles.py` v1.6.0 geeft
  `QGroupBox::indicator` een lichtere achtergrond (`#3C3C3C`) en een
  dikkere rand (2px `#B0B0B0`) in unchecked-state. Checked-state is
  blauw (`#0078D7`) met 2px rand (`#4AA3FF`). Hover en disabled zijn
  consistent. Geen wijziging aan de GUI-bestanden.
- **Nieuwe tests:** `tests/test_styles.py` v1.2.0 (+3).
- **Baseline:** 1491 → **1494 passed** (+3 tests).

### 4.38 Opgeloste punten in 11H (2026-10-21)

- **§4.4 — light theme.** Volledig opgelost in 11H.1 t/m 11H.5:
  - 11H.1: `styles.py` v1.7.0 met `LIGHT_THEME_STYLESHEET`,
    `THEME_STYLESHEETS` en `apply_theme(app, thema)`.
  - 11H.2: `settings.py` v1.8.0 met `normaliseer_thema()`;
    `SettingsDialog` v1.7.0 met actieve `thema_combo`.
  - 11H.3: `ToolHubWindow` met `theme`-parameter (wint van
    `settings.json`), live wissel, en `self.setStyleSheet()` in
    plaats van `QApplication.setStyleSheet()`. Nieuwe `conftest.py`
    met autouse-opruimfixture. Performance: suite van 53 min naar
    ~3 min.
  - 11H.4: `AnalysisScreen` v1.7.0 met `theme`-parameter,
    `CHART_COLORS` en `apply_theme()`.
  - 11H.5: `HistoryScreen` v1.18.0 met `theme`-parameter,
    `DETAIL_HTML_COLORS` en `apply_theme()`;
    `main_window._toon_release_notes_dialoog` thema-afhankelijk.
- **Nieuwe tests:** `test_theme_switch.py` (10),
  `test_analysis_screen_theme.py` (11),
  `test_history_screen_theme.py` (11); uitbreiding
  `test_styles.py` (+8), `test_settings.py` (+6),
  `test_settings_dialog.py` (+6).
- **Baseline:** 1494 → **1546 passed** (+52 tests).
- **Observatie:** de performance-fix in 11H.3 (v2.22.0) was
  noodzakelijk: de globale `QApplication.setStyleSheet` in elke
  `ToolHubWindow`-constructie liep in de testsuite op tot 50–170
  seconden per test. Het venster beheert nu zijn eigen stylesheet.

---

## 5. Status van dit document

- Dit document is **levend**. Bij elke fase mogen nieuwe vragen worden
  toegevoegd en opgeloste vragen worden gemarkeerd.
- Opgeloste vragen blijven staan voor historische context.