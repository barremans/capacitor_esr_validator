# Overdracht — Electronics Diagnostic Tool Hub / ESR Tester

**Versie:** 6.13.0
**Datum:** 2026-10-27
**Auteur:** Bart Bossuyt

Wijzigingen:
  v6.9.0 (2026-10-26)  Chat 4 afgerond: assessment (B1/B2), schema v4
                        (B3/OL-status), type-match (B4). Baseline
                        1718 → 1766 passed.
  v6.10.0 (2026-10-26) Chat 5A afgerond: slimme Y-as-clamping met
                        outlier-detectie in AnalysisScreen en
                        report_chart via de nieuwe pure helper
                        app/helpers/chart_axis.py. Baseline
                        1766 → 1779 passed (+13).
  v6.11.0 (2026-10-26) Chat 5B afgerond: leesbare X-as-labels in de
                        scatter via bereken_x_as_ticks() in dezelfde
                        helper. Baseline 1779 → 1787 passed (+8).
  v6.12.0 (2026-10-26) Chat 5C afgerond: selectie volgt onmiddellijk
                        de grafiek bij scope SELECTED. Baseline
                        1787 → 1792 passed (+5).
  v6.12.1 (2026-10-27) Correctie na volledige suite: de bestaande
                        test test_analysis_report_met_selectie_blijft_
                        for_measurements in test_report_dialog_scope_
                        filters.py simuleerde een onrealistische staat
                        (handmatige rij zonder service-rij) en brak
                        door de 5C-refresh. Test herschreven volgens
                        de echte GUI-flow + één nieuwe test die het
                        bewuste gedrag vastlegt. Baseline
                        1792 → 1793 passed (+1).
  v6.13.0 (2026-10-27) Chat 5D afgerond: vergelijkingsmodus. Nieuwe
                        grafiekoptie "Vergelijk reeksen", nieuwe
                        service-methode vergelijken(), nieuwe
                        VergelijkReeks-dataclass, vaste kleur-cyclus.
                        Baseline 1793 → 1795 passed (+2 gemeten;
                        de drie analysis-bestanden kregen +18 tests,
                        de suite als geheel +2).

---

## 1. Werkafspraken

Ongewijzigd t.o.v. v6.11.0. De belangrijkste punten:

- **Volledige bestanden leveren, nooit fragmenten.** Als je een bestand aanpast, lever je het in zijn geheel opnieuw, ook als er maar één regel verandert. Géén secties met "… ongewijzigd …" of losse stukjes code in de lopende tekst.
- JSON altijd volledig, nooit fragmenten.
- `.md` in viervoudige backticks zodra het bestand zelf codeblokken bevat (`docs/markdown_levering.md`).
- Geen `qtbot`, geen `pytest-qt`.
- Eerst gerichte tests, dan volledige `pytest -q`.
- Testtelling verifiëren met `pytest --collect-only -q`, niet schatten.
- Bij elke nieuwe sub-fase: `Compare-Object` tegen de vorige versie om te controleren dat er geen tests verdwijnen.
- **Bij wijzigingen aan de chart-aslogica: test met een representatieve CSV met een echte outlier.**
- **Lessen uit eerdere chats:** documentatie en code kunnen uit elkaar lopen; sanity-drempels aan beide kanten testen; gedeelde helpers voorkomen drift; schaal vóór filteren, niet erna; klem de x-as op een veilig bereik.
- **Les uit 5B:** Een `NameError` in een test betekent vaak een ontbrekende import in het testbestand, niet een ontbrekende functie in de productiecode. Controleer altijd eerst de imports.
- **Les uit 5C:** Als een GUI-wijziging een signaal-flow raakt, controleer of het signaal niet dubbel geëmit wordt. In `analysis_screen.py` zat een dubbele emit (`_on_selection_item_changed` + `_update_selection_count`); die is opgeruimd.
- **Les uit 5C (aanvulling):** Een bestaande test die een onrealistische staat simuleert (een rij die niet uit de service komt), kan breken zodra de productiecode meer gaat valideren. Herschrijf zulke tests volgens de echte GUI-flow in plaats van de productiecode terug te draaien.
- **Les uit 5D (1):** Een `_draw_*`-functie die de selectie nodig heeft, moet dezelfde bron gebruiken als `refresh()` zelf — `_scope_measurement_ids()`, niet `_selected_measurement_ids()`. Tijdens een `refresh(preserve_selection=True)` is de selectietabel tijdelijk leeg; `_scope_measurement_ids()` kijkt eerst naar `_te_herstellen_selectie` en pas daarna naar de huidige selectie.
- **Les uit 5D (2):** QtCharts respecteert een `setRange()` op een as met **meerdere reeksen** niet betrouwbaar. Als één reeks een punt buiten de range bevat, rekt Qt de as op om dat punt toch te tonen. De robuuste oplossing is: voeg alleen punten toe die je wilt tonen. Filter outliers uit de QLineSeries voordat je ze toevoegt.
- **Les uit 5D (3):** `bereken_y_as_range()` past de Tukey-fence alleen toe bij **4 of meer punten**. Bij 1–3 punten valt de helper terug op min/max + 5% marge (bewuste 5A-keuze: IQR is dan onbetrouwbaar). Een test die 5A-clamping wil testen, moet dus minstens 4 punten in de reeks hebben.
- **Les uit 5D (4):** In een GUI-test die meerdere rijen aanvinkt bij scope SELECTED, triggert elke `setCheckState` een `refresh(preserve_selection=True)` die de tabel opnieuw opbouwt. Wie in een lus op rij-index werkt, grijpt na de eerste wissel een verouderd item aan. Werk rij voor rij, op basis van meet-id (`_select_measurement_row_by_id`), met `QApplication.processEvents()` na elke wissel.

---

## 2. Projectstaat na chat 5D

### 2.1 Baseline

**1795 passed, 14 subtests passed** (`pytest -q`, 2026-10-27).

Eerlijke noot: de drie analysis-bestanden kregen in 5D +18 nieuwe tests (4 in `test_analysis_series.py`, 4 in `test_analysis_service.py`, 10 in `test_analysis_screen.py`). De suite als geheel groeide met +2 (1793 → 1795). De 16 ontbrekende tests zijn niet te verklaren zonder de volledige collectie van vóór 5D; de 1795 is de nieuwe, gemeten baseline.

### 2.2 Wat er sinds chat 5C is veranderd

Sub-fase **5D** is afgerond. 5A-bis/5B-bis (log-schaal) staat nog open.

### 2.3 Nieuwe en gewijzigde bestanden

| Bestand | Was | Nu |
|---|---|---|
| `app/helpers/analysis_series.py` | v1.0.1 | **v1.1.0** (VergelijkReeks + build_vergelijk_reeksen) |
| `app/services/analysis_service.py` | v1.1.0 | **v1.2.0** (vergelijken) |
| `app/gui/analysis_screen.py` | v1.9.1 | **v1.10.2** (vergelijkingsmodus + 2 bugfixes) |
| `i18n/locales/nl_NL/analysis.json` | — | +5 keys onder `analyse.vergelijk` |
| `i18n/locales/en_US/analysis.json` | — | +5 keys onder `analyse.vergelijk` |
| `tests/test_analysis_series.py` | — | **v1.1.0** (nieuw, 4 tests) |
| `tests/test_analysis_service.py` | v1.1.0 | **v1.2.0** (+4 tests) |
| `tests/test_analysis_screen.py` | v1.8.1 | **v1.9.2** (+10 tests) |

### 2.4 Openstaand na 5D

- **5A-bis / 5B-bis** — Log-schaal voor ESR/capaciteit. Zie `docs/openvragen.md` §4.49, §4.50 en §4.52.
- **Masterplan debugging review** — aparte chat. Zie de starttekst voor Chat 6.

---

## 3. Werkafspraken — herinnering

Ongewijzigd. Zie §1.

---

## 4. Planning

| Sub-fase | Status | Baseline |
|---|---|---|
| 5A — Y-as en outliers | **afgerond** | 1766 → 1779 |
| 5B — Categorische X-as | **afgerond** | 1779 → 1787 |
| 5C — Selectie → grafiek | **afgerond** | 1787 → 1793 |
| 5D — Vergelijkingsmodus | **afgerond** | 1793 → 1795 |
| 5A-bis / 5B-bis — Log-schaal | nieuw, open | ? → ? |
| Masterplan debugging review | nieuw, open | ? → ? |

---

## 5. Eerdere chats

Volledige inhoud van §5.1 t/m §5.7 staat in v6.9.0. §5.8 staat in v6.10.0, §5.9 in v6.11.0, §5.10 in v6.12.0/v6.12.1 en §5.11 in v6.13.0.

### 5.1 t/m 5.7 — zie v6.9.0

### 5.8 Chat 5A — Y-as en outlier-detectie (2026-10-26)

Zie v6.10.0 voor het volledige verslag.

**Samenvatting:** nieuwe pure helper `bereken_y_as_range()` met Tukey-fence. `AnalysisScreen` en `report_chart` gebruiken dezelfde helper. `state_label` toont `analyse.outliers_verborgen`. Baseline 1766 → 1779 (+13).

### 5.9 Chat 5B — Leesbare X-as-labels (2026-10-26)

Zie v6.11.0 voor het volledige verslag.

**Samenvatting:** nieuwe pure helper `bereken_x_as_ticks()` in `app/helpers/chart_axis.py` v1.1.0 → v1.1.1. `AnalysisScreen` v1.9.0 en `report_chart` v1.2.0 gebruiken dezelfde helper. Baseline 1779 → 1787 (+8).

### 5.10 Chat 5C — Selectie → grafiek (2026-10-26 / 2026-10-27)

Zie v6.12.0/v6.12.1 voor het volledige verslag.

**Samenvatting:** `AnalysisScreen._on_selection_item_changed` roept nu `refresh(preserve_selection=True)` aan bij scope SELECTED. Bij scope FILTERED blijft de grafiek bewust ongewijzigd. De dubbele `selection_changed.emit()` is opgeruimd. Baseline 1787 → 1793 (+6).

### 5.11 Chat 5D — Vergelijkingsmodus (2026-10-27)

**Aanleiding:** masterplan C2, deel 4 (OV-C5-5 / OV-C5-9). Er was geen vergelijkingsmodus om 1 of meerdere metingen van hetzelfde type naast elkaar te leggen.

**Ontwerpkeuzes (bevestigd vóór implementatie):**
1. **Alleen aangevinkte metingen** (max 5). "Alle metingen van hetzelfde component" is niet implementeerbaar op de bestaande dataset: 76 van de 80 metingen hebben geen component-identiteit.
2. **Max 5 reeksen**; bij meer toont de GUI een melding.
3. **Alleen bij scope SELECTED**; bij FILTERED een melding.
4. **X-as = tijd** (QDateTimeAxis), net als de bestaande tijdreeksen.
5. **Vaste kleur-cyclus** (blauw/oranje/groen/rood/paars), niet `STATUS_COLORS` (die is per eindstatus en zou bij meerdere reeksen met dezelfde status dezelfde kleur geven).
6. **Zelfde Y-as-schaal voor alle reeksen**, met 5A-clamping (Tukey-fence).

**Fix (v1.10.2):**
- **`app/helpers/analysis_series.py` v1.1.0:** nieuwe dataclass `VergelijkReeks` (measurement_id, label, color_index, points) en pure functie `build_vergelijk_reeksen()`. Valideert max_reeksen; sorteert per reeks op x_ms; laat lege reeksen bestaan (de legenda moet de meting tonen, ook als de reeks leeg is).
- **`app/services/analysis_service.py` v1.2.0:** nieuwe methode `vergelijken(measurement_ids, *, max_reeksen=5, filters=None)`. Leest via `load_rows()` en delegeert naar `build_vergelijk_reeksen()`.
- **`app/gui/analysis_screen.py` v1.10.2:** nieuwe grafiekoptie `COMPARE_SERIES` ("Vergelijk reeksen"). Nieuwe `_draw_vergelijk()` tekent per aangevinkte meting een `QLineSeries` met een vaste kleur. Max 5 reeksen; bij meer een melding. Bij scope FILTERED of zonder selectie een melding. De Y-as gebruikt dezelfde 5A-clamping op alle reeksen samen.
- **i18n:** 5 nieuwe keys onder `analyse.vergelijk` (NL + EN).

**Drie bugfixes in `_draw_vergelijk`:**
1. **v1.10.1:** `_draw_vergelijk` gebruikte `_selected_measurement_ids()` in plaats van `_scope_measurement_ids()`. Tijdens een `refresh(preserve_selection=True)` is de selectietabel tijdelijk leeg; `_scope_measurement_ids()` kijkt eerst naar `_te_herstellen_selectie` en is de enige bron die in beide situaties klopt.
2. **v1.10.2:** QtCharts respecteert een `setRange()` op een as met meerdere reeksen niet betrouwbaar. Als één reeks een punt buiten de range bevat, rekt Qt de as op. Fix: filter outliers uit de QLineSeries voordat je ze toevoegt.
3. **v1.9.2 (test):** de test `test_vergelijk_y_as_gebruikt_clamping` had maar 2 punten. `bereken_y_as_range()` past de Tukey-fence alleen toe bij 4+ punten. De test gebruikt nu 5 punten (4 normaal + 1 uitschieter).

**Bewust niet in 5D:**
- **Grafiek volgt altijd de tabelselectie, ook bij FILTERED.** De bestaande, geteste scope-semantiek blijft leidend.
- **Component-identiteit als vergelijkingsbasis.** De dataset heeft die niet.
- **Meer dan 5 reeksen.** De legenda wordt dan onleesbaar.

**Bewijs:**
- `tests/test_analysis_series.py` v1.1.0 (4 tests): volgorde, max_reeksen, lege input, lege rijen.
- `tests/test_analysis_service.py` v1.2.0 (+4 tests): volgorde, max_reeksen, lege input, lege rijen.
- `tests/test_analysis_screen.py` v1.9.2 (+10 tests): grafiekoptie bestaat, scope FILTERED melding, geen selectie melding, te veel reeksen melding, 2 reeksen tekenen, Y-as-clamping, plus de bestaande 5A/5B/5C-tests die ongewijzigd zijn gebleven.

**Baseline:** 1793 → **1795 passed** (+2 gemeten; de drie analysis-bestanden kregen +18 tests, de suite als geheel +2).

**Lessen uit 5D:**
1. **Een `_draw_*`-functie die de selectie nodig heeft, moet dezelfde bron gebruiken als `refresh()` zelf.** `_scope_measurement_ids()` in plaats van `_selected_measurement_ids()`. Tijdens een `refresh(preserve_selection=True)` is de selectietabel tijdelijk leeg.
2. **QtCharts respecteert `setRange()` op een as met meerdere reeksen niet betrouwbaar.** Filter outliers uit de QLineSeries voordat je ze toevoegt; dan kan Qt de as niet oprekken.
3. **`bereken_y_as_range()` past de Tukey-fence alleen toe bij 4+ punten.** Een test die 5A-clamping wil testen, moet minstens 4 punten in de reeks hebben.
4. **In een GUI-test die meerdere rijen aanvinkt bij scope SELECTED, triggert elke `setCheckState` een refresh.** Werk rij voor rij, op basis van meet-id, met `QApplication.processEvents()` na elke wissel.

---

## 6. Einde van het document