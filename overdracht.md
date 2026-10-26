# Overdracht — Electronics Diagnostic Tool Hub / ESR Tester

**Versie:** 6.11.0
**Datum:** 2026-10-26
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

---

## 1. Werkafspraken

Ongewijzigd t.o.v. v6.10.0. De belangrijkste punten:

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

---

## 2. Projectstaat na chat 5B

### 2.1 Baseline

**1787 passed, 14 subtests passed** (`pytest -q`, 2026-10-26).

### 2.2 Wat er sinds chat 4 is veranderd

Sub-fasen **5A** en **5B** zijn afgerond. 5C en 5D staan nog open (zie §4).

### 2.3 Nieuwe en gewijzigde bestanden

| Bestand | Was | Nu |
|---|---|---|
| `app/helpers/chart_axis.py` | — | **v1.1.1** (nieuw; was v1.0.0 → v1.1.0 → v1.1.1) |
| `app/gui/analysis_screen.py` | v1.7.2 | **v1.9.0** |
| `app/helpers/report_chart.py` | v1.0.3 | **v1.2.0** |
| `i18n/locales/nl_NL/analysis.json` | — | +1 key (`analyse.outliers_verborgen`) |
| `i18n/locales/en_US/analysis.json` | — | +1 key (`analyse.outliers_verborgen`) |
| `tests/test_chart_axis.py` | — | **v1.1.0** (nieuw, 12 tests) |
| `tests/test_analysis_screen.py` | v1.6.2 | **v1.8.0** (+6 tests) |
| `tests/test_report_chart.py` | v1.0.0 | **v1.2.0** (+3 tests) |

### 2.4 Openstaand na 5B

- **5C** — Selectie → grafiek. 11G.5 heeft de GUI-flow al geïmplementeerd; verificatie nodig wat nog open is. Bij scope FILTERED reageert de grafiek niet op tabelselectie; is dat het openstaande punt?
- **5D** — Vergelijkingsmodus. Feature, geen bugfix. Voorstel: aparte chat.
- **5A-bis / 5B-bis** — Log-schaal voor ESR/capaciteit. Zie `docs/openvragen.md` §4.49 en §4.50.

---

## 3. Werkafspraken — herinnering

Ongewijzigd. Zie §1.

---

## 4. Planning

| Sub-fase | Status | Baseline |
|---|---|---|
| 5A — Y-as en outliers | **afgerond** | 1766 → 1779 |
| 5B — Categorische X-as | **afgerond** | 1779 → 1787 |
| 5C — Selectie → grafiek | open | 1787 → ? |
| 5D — Vergelijkingsmodus | open (aparte chat?) | ? → ? |
| 5A-bis / 5B-bis — Log-schaal | nieuw, open | ? → ? |

---

## 5. Eerdere chats

Volledige inhoud van §5.1 t/m §5.7 staat in v6.9.0. §5.8 staat in v6.10.0 en §5.9 in v6.11.0.

### 5.1 t/m 5.7 — zie v6.9.0

### 5.8 Chat 5A — Y-as en outlier-detectie (2026-10-26)

Zie v6.10.0 voor het volledige verslag.

**Samenvatting:** nieuwe pure helper `bereken_y_as_range()` met Tukey-fence. `AnalysisScreen` en `report_chart` gebruiken dezelfde helper. `state_label` toont `analyse.outliers_verborgen`. Baseline 1766 → 1779 (+13).

### 5.9 Chat 5B — Leesbare X-as-labels (2026-10-26)

**Aanleiding:** masterplan C2, deel 2. De X-as van de scatter "ESR vs. capaciteit" toonde op de ticks letterlijk "..." in plaats van getallen. De data (0,1 µF tot 1.160 µF) is log-verdeeld, en Qt's standaard lineaire `QValueAxis` kon bij 6 ticks op dat bereik geen leesbare labels produceren.

**Reproductie:** de screenshots van de scatter-grafiek tonen op elke tick-positie `...`. De Y-as toonde in dezelfde screenshots nog het oude 5A-symptoom (−5.473 tot 114.975), wat bevestigt dat de screenshots van vóór de 5A-fix zijn.

**Oorzaak:** `AnalysisScreen._draw_scatter` (v1.8.0, regel ~1010) zette de X-as op `QValueAxis` met vast `setTickCount(6)` en `setLabelFormat("%.0f")`. Bij een log-verdeeld bereik kiest Qt tick-posities die te dicht bij elkaar liggen om leesbaar te zijn, en toont dan `...` in plaats van het getal.

**Fix:** nieuwe pure helper `bereken_x_as_ticks(x_min, x_max)` in `app/helpers/chart_axis.py` (v1.1.0, daarna v1.1.1 voor de drempel-correctie). De helper kiest op basis van de breedte van het bereik:

- `< 1`: 4 ticks, `%.2f`, rotatie 0
- `< 10`: 5 ticks, `%.1f`, rotatie 0
- `< 100`: 5 ticks, `%.0f`, rotatie 0
- `< 1500`: 5 ticks, `%.0f`, rotatie -45
- `< 10000`: 4 ticks, `%.0f`, rotatie -45
- `>= 10000`: 3 ticks, `%.3g`, rotatie -45

`AnalysisScreen` v1.9.0 en `report_chart` v1.2.0 gebruiken dezelfde helper.

**Bewijs:**
- `tests/test_chart_axis.py` v1.1.0 (12 tests, waarvan 5 nieuw voor 5B): de helper geeft de juiste waarden voor kleine, middelgrote en grote bereiken, en een veilige fallback bij ongeldige grenzen.
- `tests/test_analysis_screen.py` v1.8.0 (+2 tests): de GUI past de helper toe op de X-as; het labelFormat, tickCount en de labelsAngle kloppen voor het echte CSV-bereik en voor een klein bereik.
- `tests/test_report_chart.py` v1.2.0 (+1 test): de rapportgrafiek gebruikt dezelfde helper.

**Bewust niet in 5B:**
- **Log-schaal** voor de X-as. Dat is dezelfde discussie als 5A-bis en staat genoteerd als **5B-bis** in `docs/openvragen.md` §4.50.

**Baseline:** 1779 → **1787 passed** (+8: 5 + 2 + 1).

**Lessen uit 5B:**
1. **Een `NameError` in een test wijst vaak op een ontbrekende import in het testbestand, niet op een ontbrekende functie in de productiecode.** De `bereken_x_as_ticks`-functie stond wel in `chart_axis.py`, maar de import ontbrak in `test_chart_axis.py`. Daardoor bleef de fout terugkomen, ook nadat de productiecode correct was. Altijd eerst controleren: staat de import erin?
2. **Een drempel in een helper moet je aan beide kanten testen.** De drempel `breedte < 1000` gaf 4 ticks voor het CSV-bereik, terwijl de GUI-test 5 verwachtte. Pas na het verschuiven naar `< 1500` klopte het. Dit is dezelfde les als chat 4 (sanity-drempels aan beide kanten testen).
3. **Volledige bestanden leveren is niet genoeg; de levering moet ook compleet zijn.** Ik heb de `import`-regel in een eerdere stap als losse instructie gegeven in plaats van in het volledige bestand. Daardoor is de import nooit in het bestand terechtgekomen.

---

## 6. Einde van het document