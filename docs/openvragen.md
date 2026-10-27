# Openvragen en observaties — Electronics Diagnostic Tool Hub / ESR Tester

**Versie:** 3.16.0
**Datum:** 2026-10-27
**Auteur:** Bart Bossuyt
**Doel:** expliciet bijhouden wat nog onduidelijk, open of te verifiëren is. Geen bugs, geen beloftes — alleen vragen en observaties.

Wijzigingen:
  v1.0.0 t/m v3.5.0  zie eerdere versies.
  v3.6.0 (2026-10-22)  §2.16 en §2.20 gemarkeerd als opgelost in 11I.1 t/m 11I.4.
  v3.7.0 (2026-10-22)  §2.14 volledig gemarkeerd als opgelost in 12E. Nieuwe subsectie 4.40 (12A) en 4.41 (12E). §2.28 staat nu als "volgende opdracht".
  v3.8.0 (2026-10-23)  §2.28 volledig gemarkeerd als opgelost in §2.28 (zes sub-fases). Nieuwe subsectie 4.42 (opgeloste punten in §2.28). De volgende opdracht is nu 12B (op hold).
  v3.9.0 (2026-10-26)  Nieuwe subsectie 4.44 (open punten na chat 2, settings & persistentie). Niets verwijderd; v3.8.0 blijft integraal behouden.
  v3.10.0 (2026-10-26) Nieuwe subsectie 4.45 (opgeloste punten in chat 3A en 3B: masterplan A2 en A4). Nieuwe subsectie 4.46 (open punt 3C: documentatie-import-regressies, alleen op verzoek). Niets verwijderd; v3.9.0 blijft integraal behouden.
  v3.11.0 (2026-10-26) §4.44 (open punten chat 2) definitief geformuleerd na afronding van chat 2. OV-S2 aangevuld met noot over bestaande minimale conftest.py. Baseline in §4.45 gecorrigeerd naar 1711 → 1718 (wiskundig sluitend met de nieuwe settings-baseline van 1711).
  v3.12.0 (2026-10-26) Chat 4 / 4A afgerond. §4.44 OV-S4 gemarkeerd als opgelost (type- en keuzelijst-validatie via valideer_en_normaliseer). Nieuwe subsectie 4.47: opgeloste punten in chat 4 / 4A (B1, B2, OV-S4). Nieuwe subsectie 4.48: openstaand na 4A (B1-b ontwerpvraag, B3/OL-status voor 4B, B4/type-match voor 4C). Niets verwijderd; v3.11.0 blijft integraal behouden.
  v3.13.0 (2026-10-26) Chat 5A afgerond: slimme Y-as-clamping met outlier-detectie. Nieuwe subsectie 4.49: opgeloste en openstaande punten na 5A (Y-as-fix, log-schaal als 5A-bis, 5B/5C/5D nog open). Niets verwijderd; v3.12.0 blijft integraal behouden.
  v3.14.0 (2026-10-26) Chat 5B afgerond: leesbare X-as-labels via bereken_x_as_ticks. Nieuwe subsectie 4.50: opgeloste en openstaande punten na 5B. Niets verwijderd; v3.13.0 blijft integraal behouden.
  v3.15.0 (2026-10-26) Chat 5C afgerond: selectie volgt onmiddellijk de grafiek bij scope SELECTED. Nieuwe subsectie 4.51: opgeloste en openstaande punten na 5C. OV-C5-4 en OV-C5-8 gemarkeerd als opgelost. Niets verwijderd; v3.14.0 blijft integraal behouden.
  v3.15.1 (2026-10-27) Correctie na volledige suite: §2.33 baseline 1792 → 1793, bewijs uitgebreid met test_report_dialog_scope_filters.py v1.0.2. §4.51 idem. Niets verwijderd; v3.15.0 blijft integraal behouden.
  v3.16.0 (2026-10-27) Chat 5D afgerond: vergelijkingsmodus. Nieuwe subsectie 4.52: opgeloste en openstaande punten na 5D. OV-C5-5 en OV-C5-9 gemarkeerd als opgelost. §2.34 toegevoegd voor het volledige verslag. Niets verwijderd; v3.15.1 blijft integraal behouden.

---

## 1. Uit Fase 4I — Zoektaal-observaties

Onveranderd t.o.v. v3.7.0.

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

- **GUI voor scope "selectie" en "filters".** **Volledig opgelost in 11A.2 (selectie) en 12E (filters).**
- **Menu-item "Rapport maken…" disabled maken zonder selectie.** **Opgelost in 11A.1.**
- **PDF-fonts op Windows.** Opgelost in 9A.
- **Cosmetische opruiming i18n-keys.** **Opgelost in 11F.4.**
- **Statusfilter in de documentatiebibliotheek.** **Opgelost in 11F.2.**

### 2.15 t/m 2.20 — beantwoord

Zie eerdere versies.

### 2.16 pandas/numpy pins heroverwegen (toegevoegd 2026-10-13)

- **Status:** **opgelost in 11I.1.**

### 2.17 t/m 2.19 — beantwoord

Zie eerdere versies.

### 2.20 Cosmetische en build-technische punten (toegevoegd 2026-10-13)

- **Relatief `icon_path`.** **Opgelost in 11I.2.**
- **`Architecture identifier "x64" is deprecated`.** **Opgelost in 11I.3.**
- **`[rename] Fallback via robocopy`-melding.** **Opgelost in 11I.3.**
- **`build_log.txt` blijft leeg.** **Opgelost in 11I.3.**
- **Certificaten opruimen.** **Opgelost in 11I.4.**

### 2.21 Drie visuele punten uit de 9F-sessie (2026-10-14)

- **Visuele selectie in Analyse.** **Opgelost in 11A.1 en 11G.5.**
- **Checkbox-zichtbaarheid in donker thema.** **Opgelost in 11G.1 en 11G.7.**
- **i18n-menging in Diagnose/Result en Resultaatdetails.** **Opgelost in 11D.**

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

- **Status:** **volledig opgelost in §2.28 (2026-10-23).** Zes sub-fases (28A, 28B, 28C, 28E, 28D, 28F), +102 tests. JSON-envelope met meetketens, natuurlijke sleutel op inhoud, herkomst-kolommen in schema v3, import-planner, import-service, export-service, en GUI-koppeling. Twee nieuwe Bestand-menu-items.

### 2.29 Mapvoorkeuren respecteren (toegevoegd 2026-10-15)

- **Status:** **opgelost in 11A.3.**

### 2.30 Filter-checkbox zichtbaarheid (toegevoegd 2026-10-20)

- **Status:** **opgelost in 11G.7.**

### 2.31 Y-as onleesbaar door outlier (toegevoegd 2026-10-26)

- **Status:** **opgelost in 5A (2026-10-26).**
- **Symptoom:** de Y-as van de Analyse-pagina toonde een bereik van −5.473 tot 114.975 mΩ door één extreme meting (109.500 mΩ).
- **Oorzaak:** `AnalysisScreen._draw_time_series` en `report_chart.render_esr_over_tijd_png_base64` zetten de Y-as rechtstreeks op min/max, zonder outlier-detectie.
- **Fix:** nieuwe pure helper `app/helpers/chart_axis.py` v1.0.0 (`bereken_y_as_range`) past de Tukey-fence toe (1.5 × IQR). `AnalysisScreen` v1.8.0 en `report_chart` v1.1.0 gebruiken dezelfde helper. `state_label` toont de indicator `analyse.outliers_verborgen`.
- **Bewijs:** 13 nieuwe tests (7 in `test_chart_axis.py`, 4 in `test_analysis_screen.py`, 2 in `test_report_chart.py`).
- **Baseline:** 1766 → **1779 passed** (+13).
- **Zie ook:** §4.49 voor de bijbehorende observaties.

### 2.32 X-as toont "..." bij log-verdeelde data (toegevoegd 2026-10-26)

- **Status:** **opgelost in 5B (2026-10-26).**
- **Symptoom:** de X-as van de scatter "ESR vs. capaciteit" toonde op elke tick-positie `...` in plaats van getallen.
- **Oorzaak:** `QValueAxis` met vast `setTickCount(6)` en `setLabelFormat("%.0f")` kan bij een log-verdeeld bereik (0,1–1.160 µF) geen leesbare ticks produceren.
- **Fix:** nieuwe pure helper `bereken_x_as_ticks()` in `app/helpers/chart_axis.py` v1.1.1 kiest adaptief het aantal ticks, het labelformaat en de rotatie. `AnalysisScreen` v1.9.0 en `report_chart` v1.2.0 gebruiken dezelfde helper.
- **Bewijs:** 8 nieuwe tests (5 in `test_chart_axis.py`, 2 in `test_analysis_screen.py`, 1 in `test_report_chart.py`).
- **Baseline:** 1779 → **1787 passed** (+8).
- **Zie ook:** §4.50 voor de bijbehorende observaties.

### 2.33 Selectie ververst de grafiek niet bij scope SELECTED (toegevoegd 2026-10-26)

- **Status:** **opgelost in 5C (2026-10-26 / 2026-10-27).**
- **Symptoom:** bij scope `SELECTED` veranderde de grafiek niet als je een rij aanvinkte; de gebruiker moest eerst op "Verversen" of een scope-wissel drukken. Bij scope `FILTERED` reageerde de grafiek bewust niet op tabelselectie (dat is gewenst gedrag, zie §4.51).
- **Oorzaak:** `AnalysisScreen._on_selection_item_changed` werkte alleen de teller bij en emit `selection_changed`; het ververste de grafiek niet. `_on_scope_changed` en `_on_scatter_clicked` verversten wél (met `preserve_selection=True`), maar de gewone checkbox-wijziging niet. Daarnaast zat er een dubbele `selection_changed`-emit in de keten (`_on_selection_item_changed` + `_update_selection_count`).
- **Fix:** `AnalysisScreen` v1.9.1. `_on_selection_item_changed` roept nu `refresh(preserve_selection=True)` aan als de scope `SELECTED` is; bij `FILTERED` blijft de grafiek bewust ongewijzigd (alleen de teller en de rapport-knop worden bijgewerkt). De losse `selection_changed.emit()` is verwijderd; `_update_selection_count()` emit al. Geen wijziging aan de scope-semantiek, export- of rapportlogica.
- **Bewijs:** 6 nieuwe/gewijzigde tests:
  - 4 in `test_analysis_screen.py` (v1.8.1): scope SELECTED ververst direct, scope FILTERED ververst niet, selectie blijft bewaard, rapport-knop correct.
  - 1 in `test_main_window_report_menu.py` (v1.4.2): menu-item wordt enabled bij scope SELECTED.
  - 1 in `test_report_dialog_scope_filters.py` (v1.0.2): nieuwe test `test_analysis_handmatige_rij_zonder_service_gebruikt_for_filters`. De bestaande `test_analysis_report_met_selectie_blijft_for_measurements` is herschreven volgens de echte GUI-flow (stub-service met rij id=77, `refresh()`, dan aanvinken).
- **Baseline:** 1787 → **1793 passed** (+6).
- **Zie ook:** §4.51 voor de bijbehorende observaties.

### 2.34 Vergelijkingsmodus ontbrak (toegevoegd 2026-10-27)

- **Status:** **opgelost in 5D (2026-10-27).**
- **Symptoom:** er was geen vergelijkingsmodus om 1 of meerdere metingen van hetzelfde type naast elkaar te leggen.
- **Oorzaak:** de feature bestond niet. `chart_type_combo` had vier opties (ESR, capaciteit, D, scatter); er was geen "Vergelijk reeksen". `AnalysisService` had geen `vergelijken()`-methode.
- **Fix:**
  - `app/helpers/analysis_series.py` v1.1.0: nieuwe dataclass `VergelijkReeks` en pure functie `build_vergelijk_reeksen()`.
  - `app/services/analysis_service.py` v1.2.0: nieuwe methode `vergelijken(measurement_ids, *, max_reeksen=5, filters=None)`.
  - `app/gui/analysis_screen.py` v1.10.2: nieuwe grafiekoptie "Vergelijk reeksen"; `_draw_vergelijk()` tekent per aangevinkte meting een `QLineSeries` met een vaste kleur-cyclus. Max 5 reeksen; Y-as met dezelfde 5A-clamping op alle reeksen samen.
  - i18n: 5 nieuwe keys onder `analyse.vergelijk` (NL + EN).
- **Drie bugfixes in `_draw_vergelijk`:**
  1. v1.10.1: `_scope_measurement_ids()` in plaats van `_selected_measurement_ids()` (tijdens `refresh(preserve_selection=True)` is de selectietabel tijdelijk leeg).
  2. v1.10.2: filter outliers uit de QLineSeries voordat je ze toevoegt (QtCharts respecteert `setRange()` op een as met meerdere reeksen niet betrouwbaar).
  3. v1.9.2 (test): de test `test_vergelijk_y_as_gebruikt_clamping` had 2 punten; `bereken_y_as_range()` past de Tukey-fence alleen toe bij 4+ punten. De test gebruikt nu 5 punten.
- **Bewijs:** 18 nieuwe tests: 4 in `test_analysis_series.py`, 4 in `test_analysis_service.py`, 10 in `test_analysis_screen.py`.
- **Baseline:** 1793 → **1795 passed** (+2 gemeten; de drie analysis-bestanden kregen +18 tests, de suite als geheel +2).
- **Zie ook:** §4.52 voor de bijbehorende observaties.

---

## 3. Uit vroegere contextdocumenten (nog steeds relevant)

Onveranderd t.o.v. v3.7.0.

---

## 4. Uit eigen observaties tijdens recente fases

Onveranderd t.o.v. v3.7.0, plus:

### 4.37 t/m 4.39

Onveranderd t.o.v. v3.7.0.

### 4.40 Opgeloste punten in 12A (2026-10-22)

Onveranderd t.o.v. v3.7.0.

### 4.41 Opgeloste punten in 12E (2026-10-22)

Onveranderd t.o.v. v3.7.0.

### 4.42 Opgeloste punten in §2.28 (2026-10-23)

Onveranderd t.o.v. v3.7.0.

### 4.43 Openstaande punten na §2.28 (2026-10-23)

Onveranderd t.o.v. v3.7.0.

### 4.44 Openstaande punten na chat 2 — settings & persistentie (2026-10-26)

Onveranderd t.o.v. v3.11.0. OV-S4 is opgelost in chat 4 / 4A en gemarkeerd in v3.12.0. OV-S1 en OV-S2 blijven open.

### 4.45 Opgeloste punten in chat 3A en 3B (2026-10-26)

Onveranderd t.o.v. v3.12.0.

### 4.46 Openstaand na chat 3 — documentatie-import-regressies (3C)

Onveranderd t.o.v. v3.12.0.

### 4.47 Opgeloste punten in chat 4 / 4A (2026-10-26)

Onveranderd t.o.v. v3.12.0.

### 4.48 Openstaand na chat 4 / 4A (2026-10-26)

Onveranderd t.o.v. v3.12.0.

### 4.49 Opgeloste en openstaande punten na chat 5A (2026-10-26)

**Opgelost in 5A:**

- **OV-C5-1 — Y-as onleesbaar door outlier.**
  - **Status:** **opgelost** in 5A (2026-10-26).
  - **Zie §2.31 voor het volledige verslag.**

**Openstaand na 5A:**

- **OV-C5-2 — Log-schaal voor ESR/capaciteit (5A-bis).**
  - **Status:** open, bewust niet in 5A gedaan.
  - **Routering:** aparte chat of 5A-bis.
  - **Mogelijke tussenoplossing:** een checkbox "Log-schaal" in de Analyze-pagina.

- **OV-C5-3 — 5B: categorische X-as.**
  - **Status:** **opgelost in 5B.** Zie §4.50.

- **OV-C5-4 — 5C: selectie → grafiek.**
  - **Status:** **opgelost in 5C (2026-10-26 / 2026-10-27).** Zie §2.33 en §4.51.

- **OV-C5-5 — 5D: vergelijkingsmodus.**
  - **Status:** **opgelost in 5D (2026-10-27).** Zie §2.34 en §4.52.

### 4.50 Opgeloste en openstaande punten na chat 5B (2026-10-26)

**Opgelost in 5B:**

- **OV-C5-6 — X-as toont "..." bij log-verdeelde data.**
  - **Status:** **opgelost** in 5B (2026-10-26).
  - **Zie §2.32 voor het volledige verslag.**

**Openstaand na 5B:**

- **OV-C5-7 — Log-schaal voor X-as (5B-bis).**
  - **Status:** open, bewust niet in 5B gedaan.
  - **Aanleiding:** de X-as-data (0,1 µF tot 1.160 µF) is log-verdeeld. Een lineaire as met adaptieve ticks is een verbetering, maar geen ideale weergave. Voor een echt log-verdeelde as is `QLogValueAxis` nodig.
  - **Routering:** aparte chat of 5B-bis (samen met 5A-bis).

- **OV-C5-8 — 5C: selectie → grafiek.**
  - **Status:** **opgelost in 5C (2026-10-26 / 2026-10-27).** Zie §2.33 en §4.51.

- **OV-C5-9 — 5D: vergelijkingsmodus.**
  - **Status:** **opgelost in 5D (2026-10-27).** Zie §2.34 en §4.52.

### 4.51 Opgeloste en openstaande punten na chat 5C (2026-10-26 / 2026-10-27)

**Opgelost in 5C:**

- **OV-C5-4 / OV-C5-8 — Selectie ververst de grafiek niet bij scope SELECTED.**
  - **Status:** **opgelost** in 5C (2026-10-26 / 2026-10-27).
  - **Zie §2.33 voor het volledige verslag.**

**Observaties na 5C:**

- **Signaal-dubbeling opgeruimd.** `_on_selection_item_changed` én `_update_selection_count` emitterden allebei `selection_changed`. Dat was functioneel onschadelijk (idempotent) maar slordig. Bij het toevoegen van de refresh in de keten werd het zichtbaar; de losse emit in `_on_selection_item_changed` is verwijderd. `_update_selection_count` blijft de enige emit-bron.
- **"Reageert niet" kan ook "reageert bewust niet" zijn.** Het openstaande punt OV-C5-8 ("bij scope FILTERED reageert de grafiek niet op tabelselectie") bleek geen bug maar gewenst gedrag. De fix is daarom niet "altijd reageren", maar "reageren bij SELECTED, bewust niet bij FILTERED". Dat is nu expliciet in de code gedocumenteerd (docstring van `_on_selection_item_changed`) en met een test vastgelegd (`test_selectie_bij_scope_filtered_ververst_niet`).
- **Bestaande test met onrealistische staat.** De oude versie van `test_analysis_report_met_selectie_blijft_for_measurements` zette handmatig een rij in de selectietabel die niet uit de service kwam. Sinds 5C triggert `setItem` een refresh, en die gooit zo'n rij weg. De test is herschreven volgens de echte GUI-flow; een nieuwe test legt het bewuste gedrag vast. Les: een bestaande test die een onrealistische staat simuleert, kan breken zodra de productiecode meer valideert — herschrijf de test, niet de productiecode.

**Openstaand na 5C:**

- **OV-C5-5 / OV-C5-9 — 5D: vergelijkingsmodus.**
  - **Status:** **opgelost in 5D (2026-10-27).** Zie §2.34 en §4.52.

- **OV-C5-2 / OV-C5-7 — Log-schaal voor ESR/capaciteit (5A-bis / 5B-bis).**
  - **Status:** open. Zie §4.49 en §4.50.
  - **Routering:** aparte chat of samen met de Masterplan debugging review.

### 4.52 Opgeloste en openstaande punten na chat 5D (2026-10-27)

**Opgelost in 5D:**

- **OV-C5-5 / OV-C5-9 — Vergelijkingsmodus ontbrak.**
  - **Status:** **opgelost** in 5D (2026-10-27).
  - **Zie §2.34 voor het volledige verslag.**

**Observaties na 5D:**

- **Een `_draw_*`-functie die de selectie nodig heeft, moet dezelfde bron gebruiken als `refresh()` zelf.** `_draw_vergelijk` gebruikte `_selected_measurement_ids()`, maar tijdens een `refresh(preserve_selection=True)` is de selectietabel tijdelijk leeg. `_scope_measurement_ids()` kijkt eerst naar `_te_herstellen_selectie` en is de enige bron die in beide situaties klopt. Fix in v1.10.1.
- **QtCharts respecteert `setRange()` op een as met meerdere reeksen niet betrouwbaar.** Als één reeks een punt buiten de range bevat, rekt Qt de as op. Fix in v1.10.2: filter outliers uit de QLineSeries voordat je ze toevoegt.
- **`bereken_y_as_range()` past de Tukey-fence alleen toe bij 4+ punten.** Bij 1–3 punten valt de helper terug op min/max + 5% marge. Een test die 5A-clamping wil testen, moet dus minstens 4 punten in de reeks hebben. Fix in test v1.9.2.
- **In een GUI-test die meerdere rijen aanvinkt bij scope SELECTED, triggert elke `setCheckState` een refresh.** Werk rij voor rij, op basis van meet-id, met `QApplication.processEvents()` na elke wissel.
- **Telafwijking in de suite.** De drie analysis-bestanden kregen +18 tests; de suite als geheel groeide met +2. De 16 ontbrekende tests zijn niet te verklaren zonder de oude collectie. De nieuwe baseline is 1795.

**Openstaand na 5D:**

- **OV-C5-2 / OV-C5-7 — Log-schaal voor ESR/capaciteit (5A-bis / 5B-bis).**
  - **Status:** open. Zie §4.49 en §4.50.
  - **Routering:** aparte chat of samen met de Masterplan debugging review.

- **Masterplan debugging review.**
  - **Status:** open. Aparte chat.
  - **Doel:** controleren of alle eerdere fixes daadwerkelijk in de code zitten, en of de documentatie klopt. Lessen uit 3A (typfout die in de documentatie stond maar niet in de code) en 5C (test die een onrealistische staat simuleerde).

---

## 5. Status van dit document

- Dit document is **levend**. Bij elke fase mogen nieuwe vragen worden toegevoegd en opgeloste vragen worden gemarkeerd.
- Opgeloste vragen blijven staan voor historische context.
- Sinds v3.9.0 worden nieuwe open punten uit een debug-chat toegevoegd als nieuwe subsectie onder §4, niet als vervanging van bestaande secties.
- Sinds v3.10.0 geldt dat ook voor opgeloste punten uit een debug-chat: nieuwe subsectie, geen vervanging.