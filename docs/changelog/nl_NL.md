# Changelog

Overzicht van wat er nieuw of verbeterd is in de Electronics Diagnostic
Tool Hub. Voor technische details en architectuurkeuzes verwijzen we naar
`docs/context.md`.

<!--
Opmerking over de versienummering:
- Vanaf v1.1.1 komen de versienummers 1-op-1 overeen met
  `app/version.py`, met de GitHub-releases en met
  `releases/latest/version.txt`.
- Vóór v1.1.1 is de nummering historisch: de vroege ontwikkelfases
  gebruikten een eigen 1.x-teller die niet altijd samenviel met de
  uiteindelijke releases. Die entries blijven staan als functionele
  mijlpalen; ze zijn niet 1-op-1 te mappen op een specifieke
  `app/version.py`-waarde.
- Voor de actuele versie: zie `app/version.py` of Help → Over.
-->

### Chat 5 — Analyse: vergelijkingsmodus, Y-as, X-as en selectie (26–27 oktober 2026)

**Waarom deze wijziging**

De Analyse-pagina had vier problemen: de Y-as werd volledig uitgerekt
door één extreme meting (masterplan C2, deel 1), de X-as toonde op elke
tick letterlijk "..." bij log-verdeelde data (masterplan C2, deel 2),
het aanvinken van een rij in de selectietabel werkte de grafiek niet bij
bij scope "Alleen selectie" (masterplan C2, deel 3), en er was geen
vergelijkingsmodus om meerdere metingen naast elkaar te leggen
(masterplan C2, deel 4). Alle vier zijn opgelost met pure, testbare
helpers en GUI-aanpassingen.

**Oplossing: vier sub-fases**

- **5A — Slimme Y-as-clamping (outliers).** De Y-as van de tijdreeksen
  en de scatter werd rechtstreeks op min/max gezet. Eén meting van
  109.500 mΩ rekte de as op tot −5.473…114.975 mΩ. Nieuwe pure helper
  `bereken_y_as_range()` in `app/helpers/chart_axis.py` past de
  Tukey-fence toe (1.5 × IQR) en geeft een leesbaar bereik terug plus
  het aantal verborgen punten. `AnalysisScreen` v1.8.0 en
  `report_chart` v1.1.0 gebruiken dezelfde helper. `state_label` toont
  de nieuwe i18n-key `analyse.outliers_verborgen`. Baseline
  1766 → **1779** (+13).
- **5B — Leesbare X-as-labels.** De X-as van de scatter gebruikte een
  vaste `QValueAxis` met 6 ticks en `%.0f`. Bij een bereik van
  0,1–1.160 µF kon Qt geen leesbare labels produceren en toonde `...`.
  Nieuwe pure helper `bereken_x_as_ticks()` in dezelfde
  `chart_axis.py` kiest adaptief het aantal ticks, het labelformaat en
  de rotatie (−45° voor brede bereiken). `AnalysisScreen` v1.9.0 en
  `report_chart` v1.2.0 gebruiken dezelfde helper. Baseline
  1779 → **1787** (+8).
- **5C — Selectie stuurt de grafiek bij scope "Alleen selectie".**
  Het aanvinken van een rij in de selectietabel werkte de grafiek niet
  bij bij scope `SELECTED`; de gebruiker moest eerst op "Verversen"
  of een scope-wissel drukken. `AnalysisScreen._on_selection_item_changed`
  roept nu `refresh(preserve_selection=True)` aan als de scope
  `SELECTED` is. Bij scope `FILTERED` blijft de grafiek bewust
  ongewijzigd: de filters bepalen de grafiek, niet de tabelselectie.
  De dubbele `selection_changed.emit()` is verwijderd omdat
  `_update_selection_count()` al emit. `AnalysisScreen`
  v1.9.0 → **v1.9.1**. Baseline 1787 → **1793** (+6).
- **5D — Vergelijkingsmodus.** Nieuwe grafiekoptie "Vergelijk reeksen".
  Nieuwe dataclass `VergelijkReeks` en pure functie
  `build_vergelijk_reeksen()` in `analysis_series.py` v1.1.0. Nieuwe
  service-methode `vergelijken()` in `analysis_service.py` v1.2.0.
  Nieuwe `_draw_vergelijk()` in `AnalysisScreen` v1.10.2: per
  aangevinkte meting een `QLineSeries` met een vaste kleur-cyclus
  (blauw/oranje/groen/rood/paars), max 5 reeksen, Y-as met dezelfde
  5A-clamping op alle reeksen samen. Bij scope FILTERED of zonder
  selectie een melding. Vijf nieuwe i18n-keys onder `analyse.vergelijk`.
  Baseline 1793 → **1795** (+2 gemeten; de drie analysis-bestanden
  kregen +18 tests, de suite als geheel +2).

**Belangrijke observaties**

- **5B:** een `NameError` in een test wijst vaak op een ontbrekende
  import in het testbestand, niet op een ontbrekende functie in de
  productiecode. Controleer altijd eerst de imports.
- **5C (signaal-flow):** een GUI-wijziging die een signaal-flow raakt,
  kan een dubbele emit blootleggen. `_on_selection_item_changed` én
  `_update_selection_count` emitterden allebei `selection_changed`;
  dat was onschadelijk (idempotent) maar slordig. Opgeruimd.
- **5C ("reageert niet" kan ook "reageert bewust niet" zijn):** het
  openstaande punt OV-C5-8 ("bij scope FILTERED reageert de grafiek
  niet op tabelselectie") bleek geen bug maar gewenst gedrag. De fix
  is daarom "reageren bij SELECTED, bewust niet bij FILTERED", nu
  gedocumenteerd in de code en vastgelegd in een test.
- **5C (bestaande test met onrealistische staat):** de oude versie van
  `test_analysis_report_met_selectie_blijft_for_measurements` zette
  handmatig een rij in de selectietabel die niet uit de service kwam.
  Sinds 5C triggert `setItem` een refresh, en die gooit zo'n rij weg.
  De test is herschreven volgens de echte GUI-flow; een nieuwe test
  legt het bewuste gedrag vast. Les: een test die een onrealistische
  staat simuleert, kan breken zodra de productiecode meer valideert —
  herschrijf de test, niet de productiecode.
- **5D (selectiebron):** een `_draw_*`-functie die de selectie nodig
  heeft, moet dezelfde bron gebruiken als `refresh()` zelf —
  `_scope_measurement_ids()`, niet `_selected_measurement_ids()`.
  Tijdens een `refresh(preserve_selection=True)` is de selectietabel
  tijdelijk leeg. Fix in v1.10.1.
- **5D (QtCharts en meerdere reeksen):** QtCharts respecteert een
  `setRange()` op een as met meerdere reeksen niet betrouwbaar. Als
  één reeks een punt buiten de range bevat, rekt Qt de as op. Fix in
  v1.10.2: filter outliers uit de QLineSeries voordat je ze toevoegt.
- **5D (Tukey-fence bij weinig punten):** `bereken_y_as_range()` past
  de Tukey-fence alleen toe bij 4+ punten. Bij 1–3 punten valt de
  helper terug op min/max + 5% marge. Een test die 5A-clamping wil
  testen, moet dus minstens 4 punten in de reeks hebben. Fix in test
  v1.9.2.
- **5D (meerdere rijen aanvinken in een test):** in een GUI-test die
  meerdere rijen aanvinkt bij scope SELECTED, triggert elke
  `setCheckState` een refresh. Werk rij voor rij, op basis van
  meet-id, met `QApplication.processEvents()` na elke wissel.

**Voor ontwikkelaars**

- **Nieuw:** `app/helpers/chart_axis.py` (v1.1.1) — `bereken_y_as_range`
  en `bereken_x_as_ticks`.
- **Nieuw:** `app/helpers/analysis_series.py` v1.1.0 — `VergelijkReeks`
  en `build_vergelijk_reeksen`.
- **Gewijzigd:** `app/gui/analysis_screen.py` (v1.7.2 → **v1.10.2**) —
  Y-as-clamping, X-as-ticks, `state_label`-indicator,
  selectie-gedreven refresh bij scope SELECTED, vergelijkingsmodus.
- **Gewijzigd:** `app/services/analysis_service.py` (v1.1.0 → **v1.2.0**)
  — `vergelijken()`.
- **Gewijzigd:** `app/helpers/report_chart.py` (v1.0.3 → **v1.2.0**) —
  dezelfde helpers in beide render-functies.
- **Nieuwe i18n-keys:** `analyse.outliers_verborgen`,
  `analyse.grafiektype.vergelijk`, `analyse.vergelijk.geen_selectie`,
  `analyse.vergelijk.te_veel_reeksen`,
  `analyse.vergelijk.alleen_bij_selectie`,
  `analyse.vergelijk.aantal_reeksen` (NL + EN).
- **Nieuwe tests:** `tests/test_chart_axis.py` (v1.1.0, 12 tests),
  `tests/test_analysis_series.py` (v1.1.0, 4 tests).
- **Uitgebreid:** `tests/test_analysis_screen.py` (v1.6.2 → v1.9.2,
  +18 tests over 5A/5B/5C/5D), `tests/test_report_chart.py`
  (v1.0.0 → v1.2.0, +3 tests),
  `tests/test_analysis_service.py` (v1.1.0 → v1.2.0, +4 tests),
  `tests/test_main_window_report_menu.py` (v1.4.1 → v1.4.2, +1 test),
  `tests/test_report_dialog_scope_filters.py` (v1.0.1 → v1.0.2,
  1 test herschreven, +1 test).
- **Baseline:** 1766 → **1795 passed** (+29 tests over 5A, 5B, 5C en
  5D; de suite als geheel 1795).

### Chat 4 — Assessment, schema v4 en type-match (26 oktober 2026)

Zie eerdere versie voor de volledige tekst. Samenvatting: assessment
sanity checks (B1/B2), OL-status en schema v4 (B3), type-match §14
(B4). +48 tests. Baseline **1718 → 1766 passed**.

### Chat 3 — Import-wizard en exchange-selectie (26 oktober 2026)

Zie eerdere versie voor de volledige tekst. Samenvatting: typfout in
`main_window._show_import_wizard()` hersteld (A2), exchange-selectie
krijgt expliciete prioriteit (A4). Baseline 1711 → **1718**.

### Fase §2.28 — Export/import tussen toestellen (23 oktober 2026)

Zie eerdere versie voor de volledige tekst. Samenvatting: JSON-envelope
met meetketens, natuurlijke sleutel op inhoud, herkomst-kolommen in
schema v3, import-planner, import-service, export-service, en
GUI-koppeling. +102 tests.

### Fase 11I — Build en cosmetica (22 oktober 2026)

Zie eerdere versie voor de volledige tekst. Samenvatting: pins
gedocumenteerd, `icon_path` via `sys._MEIPASS`, build-orchestratie
opgeschoond, certificaatstore-hygiëne. Baseline 1546 → **1548**.

### Fase 11H — Licht thema (21 oktober 2026)

Zie eerdere versie voor de volledige tekst. Samenvatting:
`LIGHT_THEME_STYLESHEET`, `apply_theme(app, thema)`, live themawissel,
chart-kleuren per thema in `AnalysisScreen`, detail-HTML per thema in
`HistoryScreen`. Baseline 1494 → **1546**.

### Fase 11G — Visueel donker thema (20 oktober 2026)

Zie eerdere versie voor de volledige tekst. Samenvatting: focus-states,
donkere scrollbar, as-schaling, zoom/pan, klikbare datapunten,
selectie-gedreven analyse, expliciet afsluiten, filter-checkbox
zichtbaarheid. Baseline 1462 → **1494**.

### Fase 11F — Documentatie-uitbreiding (20 oktober 2026)

Zie eerdere versie voor de volledige tekst. Samenvatting: archiefreden,
statusfilter, bulk-edit, datum-parsing, i18n-opruiming. Baseline
1395 → **1462**.

### Fase 11E — Async netwerk (16 oktober 2026)

Zie eerdere versie voor de volledige tekst. Samenvatting:
`async_worker.py`, async update-check, async URL-fetch, QA-modus.
Baseline 1366 → **1395**.

### Fase 11D — i18n-menging oplossen (16 oktober 2026)

Zie eerdere versie voor de volledige tekst. Samenvatting: `Beoordeling`
krijgt een `taal`-veld, banner bij taal-mismatch, geen stille
mengeling meer. Baseline 1358 → **1366**.

## Versie 1.2.0 — Frequentie-specifieke referenties en drempelvalidatie (15 oktober 2026)

Zie eerdere versie voor de volledige tekst. Samenvatting:
ESR-referentie is frequentie-specifiek, geschatte profielen voor
100 Hz/1 kHz/10 kHz, gevalideerd met 72 praktijkmetingen.

### UX-afwerking (fase 11A, 16 oktober 2026)

Zie eerdere versie voor de volledige tekst. Samenvatting: export
respecteert de selectie, selectie en rapport in de Analyse-pagina,
menu-item disabled zonder selectie, mapvoorkeuren.

### Betrouwbaarheidsregel herzien (fase 11B, 16 oktober 2026)

Zie eerdere versie voor de volledige tekst. Samenvatting: onderscheid
tussen inhoudelijke en administratieve betrouwbaarheidsverlagers.

### Iconen voor alle vensters (fase 11C, 16 oktober 2026)

Zie eerdere versie voor de volledige tekst. Samenvatting: één
applicatie-icoon, twaalf thematische iconen.

## Versie 1.1.1 — Update-controle bij opstarten en via Help (15 oktober 2026)

Zie eerdere versie voor de volledige tekst. Samenvatting: automatische
update-check bij opstarten, handmatige check via Help, release notes
in de melding.

## Versie 1.0.3 — Publicatie, testmatrix en bug/feature-meldingen (14 oktober 2026)

Zie eerdere versie voor de volledige tekst. Samenvatting: publieke
release, `publish.ps1`, Intune/Defender-testmatrix, Rapporteren-menu.

## Versie 1.0.2 — Eerste Windows-build, installer en signing (13 oktober 2026)

Zie eerdere versie voor de volledige tekst. Samenvatting: centrale
versie, PyInstaller-spec, installer, code-signing, PDF-fonts.

## Versie 1.0.1 — Meetrapporten en uitgebreidere instellingen (12 oktober 2026)

Zie eerdere versie voor de volledige tekst. Samenvatting: meetrapporten
(HTML/PDF), auteur, standaard rapportmap, automatisch map openen.

## Versie 1.0.0 — Grafieken en trends (9 oktober 2026)

Zie eerdere versie voor de volledige tekst. Samenvatting: nieuwe
Analyse-pagina met vier grafiektypes, filteren op dezelfde velden als
de historiek, aggregatie per dag/week/maand.

---

<!--
Vanaf hier: vroege ontwikkelfases. De nummering is historisch en komt
niet altijd 1-op-1 overeen met `app/version.py`. Deze entries blijven
staan als functionele mijlpalen.
-->

## Versie 0.9 — Fabrikantdocumenten: Word en Excel (9 oktober 2026)

Word- en Excel-import toegevoegd.

## Versie 0.8 — Status van eigen imports beheren (8 oktober 2026)

Status wijzigen voor eigen imports.

## Versie 0.7 — Metadata bij import en bewerken in de viewer (7 oktober 2026)

Metadata bij import en bewerken in de viewer.

## Versie 0.6 — Help per taal en duidelijkere zoekuitleg (6 oktober 2026)

Help per taal, duidelijkere zoekuitleg.

## Versie 0.5 — Sneltoetsen en veiliger afsluiten (5 oktober 2026)

Sneltoetsen door de hele applicatie.

## Versie 0.4 — Slimmer zoeken en hulp in de documentatie (5 oktober 2026)

Zoektaal voor documentatie, help bij zoeken.

## Versie 0.3 — Meerdere diagnosetools in één hub (3 oktober 2026)

Documenten kunnen aan meerdere tools gekoppeld worden.

## Versie 0.2 — Documentatiebibliotheek (3 oktober 2026)

Centrale, meertalige documentatiebibliotheek.

## Versie 0.1 — Eerste werkende versie (11 augustus 2026)

Eerste versie van de ESR-validator.

---

## Gepland voor volgende versies

- **Versie 1.2.0 — UX/documentatie-afwerking.** Alle kleine punten die
  in eerdere fases zijn blijven liggen. **Afgerond op 22 oktober 2026.**
- **Versie 1.3.0 — AI-extractie uit fabrikantdocumenten.**
- **Versie 1.4.0 — Menselijke validatie van AI-output.**
- **Versie 1.5.0 — Goedgekeurde fabrikantdata koppelen aan
  assessment.**
- **Versie 1.6.0 — Tweede diagnosetool: Resistor.**

---

_Historische nummering: de entries 0.1 t/m 0.9 beschrijven de vroege
ontwikkelperiode. De nummering is functioneel, niet 1-op-1 gekoppeld
aan `app/version.py`. Vanaf v1.1.1 komen de versienummers overeen met
de werkelijke releases._