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

### Fase §2.28 — Export/import tussen toestellen (23 oktober 2026)

**Waarom deze wijziging**

De app bewaart metingen lokaal op één toestel. Wie op een tweede pc
verder wil werken, moest de database handmatig kopiëren — met alle
risico's van dien. §2.28 voegt een expliciet uitwisselformaat toe:
een JSON-envelope met meetketens, waarmee je metingen selectief kunt
exporteren en op een ander toestel importeren, zonder de bestaande
historiek te overschrijven.

**Oplossing: zes sub-fases**

- **28A — Formaat + modellen.** Nieuwe bindende spec
  `docs/export_import_format.md` (v1.0.0). Nieuwe modellen in
  `app/services/exchange/models.py` (v1.0.0): `ExportEnvelope`,
  `ExportedMeasurementChain`, `ImportPlan`, `ImportConflict`,
  `ImportDecision`, `ImportResult`. JSON-envelope (geen SQLite-dump),
  UTF-8 zonder BOM, pretty-printed, `format_version="1.0"`. Natuurlijke
  sleutel = SHA-256 over een canonieke JSON van de keten (§6 spec).
  34 tests.
- **28B — Export-service.** `app/services/exchange/export_service.py`
  (v1.0.1) met `export_measurements`, `export_filters`, `write_envelope`,
  `bereken_natural_key`, `verkrijg_machine_id` en (sinds 28F)
  `read_envelope`. Machine-ID als UUID4 in `settings.json`
  (`algemeen.machine_id`). 15 tests.
- **28C — Import-planner.** `app/services/exchange/import_planner.py`
  (v1.0.0) met `ImportPlanner.plan(envelope) -> ImportPlan`. Detecteert
  duplicates op herkomst (`source_machine_id` + `source_measurement_id`)
  en op natural_key. Herberekent de natural_key en weigert een
  mismatch. `HerkomstRepositoryProtocol` voor de optionele
  herkomst-detectie. 11 tests.
- **28E — Schema-migratie v2 → v3.** `app/storage/schema.py`,
  `migrations.py`, `models.py`, `service.py` (alle v1.2.0). Twee nieuwe
  kolommen op `measurements`: `source_machine_id TEXT` en
  `source_measurement_id INTEGER` (beide nullable). Nieuwe index
  `ix_measurements_source_identity`. Validatie: "beide of geen van
  beide". Bestaande metingen krijgen `NULL`. 16 tests.
- **28D — Import-service.** `app/services/exchange/import_service.py`
  (v1.0.0) met `ImportService.apply_plan(plan, on_conflict="conflict_copy")`.
  Schrijft per keten via `StorageService.save_new_measurement_chain`,
  met race-check vóór elke write. `on_conflict="skip"` of
  `"conflict_copy"`. Per-keten rollback: een fout in één keten
  blokkeert de rest niet. 16 tests.
- **28F — GUI-koppeling.** Nieuwe `app/gui/dialogs/exchange_dialog.py`
  (v1.0.1) met twee tabbladen (Exporteren / Importeren) en een
  conflict-tabel. Twee nieuwe menu-items in `app/gui/main_window.py`
  (v2.23.0): "Exporteren naar toestel…" (Ctrl+Shift+E) en "Importeren
  van toestel…" (Ctrl+Shift+I). Nieuwe `exchange.json` in NL en EN.
  Nieuwe categorie `"exchange"` in `dialog_start_directory.py`
  (v1.0.1). Nieuwe `laatste_exchangemap` in `settings.py` (v1.8.2).
  16 tests.

**Belangrijke ontwerpbeslissingen**

- **JSON-envelope, geen SQLite-dump.** Mensleesbaar, versieerbaar, werkt
  over schemaversies heen, en sluit aan bij het bestaande patroon van
  `snapshot_json`.
- **Herkomst-tracking via schema-migratie v3.** Twee nullable kolommen
  op `measurements`, gevuld bij import, `NULL` voor lokaal aangemaakte
  metingen.
- **Natural key = inhoud, niet `source_measurement_id`.** Twee ketens
  met dezelfde inhoud geven dezelfde sleutel, ook op verschillende
  toestellen (spec §6). Daardoor is een duplicate-detectie inhoudelijk
  betrouwbaar.
- **Conflict-copy als standaard bij een conflict.** Nooit stil
  overslaan zonder dat de gebruiker het ziet; de GUI (28F) biedt per
  rij een checkbox "als kopie" aan.
- **Race-check vóór elke write.** Twee imports tegelijk of een
  tussentijdse nieuwe meting worden correct afgehandeld.
- **Per-keten transacties.** Een fout in één keten blokkeert de rest
  van de import niet; `ImportResult.errors` rapporteert per keten.

**Voor ontwikkelaars**

- **Nieuw:** `app/services/exchange/__init__.py` (v1.0.4),
  `models.py` (v1.0.0), `export_service.py` (v1.0.1),
  `import_planner.py` (v1.0.0), `import_service.py` (v1.0.0).
- **Nieuw:** `app/gui/dialogs/exchange_dialog.py` (v1.0.1).
- **Nieuw:** `docs/export_import_format.md` (v1.0.0).
- **Nieuw:** `i18n/locales/nl_NL/exchange.json` en
  `i18n/locales/en_US/exchange.json`.
- **Gewijzigd:** `app/storage/schema.py` (v1.1.0 → v1.2.0),
  `migrations.py` (v1.1.0 → v1.2.0), `models.py` (v1.1.0 → v1.2.0),
  `service.py` (v1.1.0 → v1.2.0).
- **Gewijzigd:** `app/gui/main_window.py` (v2.22.2 → v2.23.0) — twee
  menu-items + `_open_exchange_dialog`. **Bugfix:** `_show_import_wizard`
  had een typfout `self._zet_dialoog_icono(...)` in plaats van
  `self._zet_dialoog_icoon(...)`. Latente bug die bij het openen van de
  import-wizard een `AttributeError` gaf.
- **Gewijzigd:** `app/helpers/dialog_start_directory.py`
  (v1.0.0 → v1.0.1) — categorie `"exchange"`.
- **Gewijzigd:** `app/config/settings.py` (v1.8.1 → v1.8.2) —
  `laatste_exchangemap`.
- **Gewijzigd:** `app/version.py` (v1.1.0 → v1.2.0) — `__version__ =
  "1.3.0"`.
- **Nieuwe tests:** `tests/test_exchange_models.py` (v1.0.1, 34),
  `tests/test_exchange_export_service.py` (v1.0.3, 15),
  `tests/test_exchange_import_planner.py` (v1.0.2, 11),
  `tests/test_exchange_import_service.py` (v1.0.1, 16),
  `tests/test_exchange_dialog.py` (v1.0.1, 11),
  `tests/test_main_window_exchange_menu.py` (v1.0.0, 5).
- **Uitgebreid:** `tests/test_storage_schema.py` (v1.1.0 → v1.2.0),
  `tests/test_storage_migrations.py` (v1.0.0 → v1.1.0),
  `tests/test_storage_service.py` (v1.0.0 → v1.1.0),
  `tests/test_storage_multitool_v2.py` (v1.0.0 → v1.0.1).
- **Nieuwe i18n-keys:** het volledige `exchange.*`-blok in beide talen.
- **Baseline:** 1598 → **1700 passed** (+102 tests over 28A t/m 28F).

### Fase 11I — Build en cosmetica (22 oktober 2026)

**Waarom deze wijziging**

Fase 11I rondt de cosmetische en build-technische punten af die sinds
11F/11G/11H openstonden: de pandas/numpy-pins waren niet gedocumenteerd,
het icoonpad was niet bestand tegen de PyInstaller-bundel, de
build-orchestratie had drie cosmetische punten (x64-deprecation,
onduidelijke robocopy-fallback, leeg `build_log.txt`), en de twee
verlopen certificaten in de certificaatstore waren niet gedocumenteerd.

**Oplossing: vijf sub-fases**

- **11I.1 — Pins documenteren.** `requirements.txt` (v1.1.0) krijgt
  commentaar dat uitlegt waarom `numpy` en `pandas` een bovengrens
  `<3` hebben. `docs/packaging.md` (v1.1.0) krijgt een nieuwe subsectie
  §2.1 "Dependency-pins". `docs/future_tools.md` §5 wordt gelijkgetrokken
  met de werkelijke pins (inclusief `numpy`, `pypdf`, `requests`,
  `beautifulsoup4`, `python-docx`). Geen pin-wijziging: de huidige pins
  zijn bewezen in de PyInstaller-bundel.
- **11I.2 — `icon_path` via `sys._MEIPASS`.** `app/helpers/icon_paths.py`
  (v1.1.0) krijgt een expliciete `sys._MEIPASS`-branch vóór de
  omhoog-zoeklus. In een PyInstaller-bundel staat `assets/` in
  `_internal/assets/`, en de omhoog-zoeklus zou ook kunnen slagen, maar
  niet deterministisch. De expliciete branch maakt de resolutie
  deterministisch en onafhankelijk van de CWD. Twee nieuwe tests in
  `tests/test_icon_paths.py` (v1.2.0, +2). Baseline 1546 → **1548**.
- **11I.3 — Build-orchestratie opschonen.** Drie cosmetische punten:
  (a) `ArchitecturesInstallIn64BitMode=x64` → `x64compatible` in de
  gegenereerde `.iss` (Inno Setup 6 beschouwt `x64` als deprecated);
  (b) de `[rename]`-fallbackmelding in `build_installer.bat` is
  verduidelijkt (reden + actie), en de meerregelige echo brak de
  cmd-parser — opgelost in v2.0.3; (c) `build_installer.bat` logt nu
  de PyInstaller-stap [4] en de ISCC-stap [7] met
  `>> "%LOGFILE%" 2>&1` naar `build_log.txt`. `build_log.txt` staat
  expliciet in `.gitignore` (matcht niet op `*.log`). Daarnaast:
  `build_and_publish.ps1` (v1.1.0) geeft de bevestigingsvraag
  "Starten?" nu een expliciete standaardwaarde J bij Enter, consistent
  met de vier vragen ervoor.
- **11I.4 — Certificaatstore-hygiëne.** Nieuwe subsectie §4.1 in
  `docs/packaging.md` (v1.4.0): de preflight in
  `build_and_publish.ps1` slaat verlopen certificaten over; ze zijn
  onschadelijk; opruimen is optioneel en handmatig via Certificate
  Manager. `signing-certs/` (de standaardmap van
  `Export-SigningCertificate.ps1`) staat in `.gitignore`.
- **11I.5 — Afronding.** Changelog, overdracht, WatNu en openvragen
  bijgewerkt.

**Voor ontwikkelaars**

- **Gewijzigd:** `requirements.txt` (v1.0.0 → v1.1.0) — commentaar.
- **Gewijzigd:** `app/helpers/icon_paths.py` (v1.0.0 → v1.1.0) —
  `sys._MEIPASS`-branch.
- **Gewijzigd:** `build_installer.bat` (v2.0.1 → v2.0.3) —
  `x64compatible`, robocopy-melding verduidelijkt (één regel),
  logging van [4] en [7] naar `build_log.txt`.
- **Gewijzigd:** `build_and_publish.ps1` (v1.0.0 → v1.1.0) —
  standaard J bij "Starten?".
- **Gewijzigd:** `.gitignore` — `build_log.txt` en `signing-certs/`.
- **Gewijzigd:** `docs/future_tools.md` §5 — pins gelijkgetrokken.
- **Gewijzigd:** `docs/packaging.md` (v1.0.0 → v1.5.0) — §2.1, §4.1,
  §11 bijgewerkt.
- **Nieuwe tests:** `tests/test_icon_paths.py` (v1.1.0 → v1.2.0, +2).
- **Baseline:** 1546 → **1548 passed** (+2 tests).

### Fase 11H — Licht thema (21 oktober 2026)

**Waarom deze wijziging**

Het donkere thema was tot nu het enige ondersteunde thema. De
gebruiker wilde een licht thema kunnen kiezen, zonder dat de app
donkere lappen op een licht venster toont. De donkere chart-kleuren,
de donkere detail-HTML in de historiek-detaildialoog en de donkere
release-notes-dialoog moesten daarvoor per thema variabel worden.

**Oplossing: vijf sub-fases**

- **11H.1 — Light theme in styles.py.** `styles.py` (v1.7.0) krijgt
  `LIGHT_THEME_STYLESHEET`, een `THEME_STYLESHEETS`-dict en een
  `apply_theme(app, thema="dark")`-API. `apply_dark_theme(app)` blijft
  als dunne wrapper voor backward-compat. Onbekende thema-waarden
  vallen terug op `"dark"`. De `QGroupBox::indicator:unchecked` in
  licht thema krijgt een witte achtergrond met 2px `#5A5A5A`-rand,
  consistent met de 11G.7-fix in donker thema. Nieuwe tests in
  `tests/test_styles.py` (v1.3.0, +8).
- **11H.2 — Thema-keuze in Settings.** `settings.py` (v1.8.0) krijgt
  `TOEGESTANE_THEMAS`, `STANDAARD_THEMA` en een pure
  `normaliseer_thema()`. `laad_instellingen()` normaliseert het
  geladen thema. `SettingsDialog` (v1.7.0) heeft een actieve
  `thema_combo` met "Donker"/"Licht" (resp. "Dark"/"Light"), en
  `_widgets_naar_instellingen` gebruikt `normaliseer_thema()` als
  vangnet. Nieuwe i18n-keys `thema_licht` en bijgewerkte
  `thema_tooltip` (NL + EN). `tests/test_settings.py` (v1.5.0, +6)
  en `tests/test_settings_dialog.py` (v1.4.0, +6).
- **11H.3 — Thema-parameter op ToolHubWindow + live wissel.**
  `ToolHubWindow` krijgt een `theme`-parameter (wint van
  `settings.json`, analoog aan taal). `_apply_settings` detecteert
  een themawissel en past het nieuwe thema direct toe. `main.py`
  (v1.6.0) leest `algemeen.thema` en roept `apply_theme(app, thema)`
  aan. Sinds v2.22.0 beheert het venster zijn eigen stylesheet
  (`self.setStyleSheet(...)`) in plaats van de `QApplication`: dat
  lost een structureel performance-probleem op. Nieuwe
  `conftest.py` (v1.1.0) met autouse-opruimfixture.
  `tests/test_theme_switch.py` (nieuw, 10 tests).
  **Performance-fix in v2.22.0:** de onvoorwaardelijke
  `QApplication.setStyleSheet` in `ToolHubWindow` werd in de
  testsuite 50–170 seconden per test. `_apply_theme_if_needed()`
  slaat de dure aanroep over als de stylesheet al klopt, en het
  venster gebruikt `self.setStyleSheet()` in plaats van
  `QApplication.setStyleSheet()`. Samen met de `conftest.py`-fixture
  zakte de suite van 53 min naar ~3 min.
- **11H.4 — Chart-kleuren per thema in AnalysisScreen.**
  `analysis_screen.py` (v1.7.0) krijgt een keyword-only
  `theme`-parameter en een module-level `CHART_COLORS`-dict met per
  thema alle voorheen hardcoded chart-kleuren (chart-achtergrond,
  as-labels, grid, lijn, scatter-rand, neutrale scatter,
  state-label). Nieuwe `apply_theme(theme)`-methode past de kleuren
  toe zonder de reeksen te wissen. `main_window.py` (v2.22.1) geeft
  `theme` mee aan `AnalysisScreen` en roept `apply_theme` aan bij een
  themawissel. `tests/test_analysis_screen_theme.py` (nieuw, 11
  tests).
- **11H.5 — Detail-HTML en release-notes per thema.**
  `history_screen.py` (v1.18.0) krijgt een keyword-only
  `theme`-parameter en een module-level `DETAIL_HTML_COLORS`-dict met
  per thema de detail-HTML-kleuren (achtergrond, tekst, heading,
  muted, tabel-rand, state-label). Nieuwe `apply_theme(theme)`-
  methode. `_show_detail_dialog` gebruikt de per-thema
  `QTextBrowser`-stylesheet; `state_label`-kleur volgt het thema.
  `main_window.py` (v2.22.2) geeft `theme` mee aan `HistoryScreen`,
  roept `apply_theme` aan bij een themawissel, en maakt
  `_toon_release_notes_dialoog` thema-afhankelijk.
  `_markdown_naar_html` krijgt optionele `body_bg`/`body_fg` (default
  donker, backward-compat). `tests/test_history_screen_theme.py`
  (nieuw, 11 tests).

**Belangrijke observatie: testtelling**

In 11H.1 t/m 11H.5 weken mijn eigen schattingen soms af van de
werkelijke tellingen. De werkelijke tellingen via
`pytest --collect-only -q` per bestand en de volledige `pytest -q`
waren consistent. De som van de gerichte `--collect-only` is bij elke
sub-fase vergeleken met de volledige suite.

**Voor ontwikkelaars**

- **Gewijzigd:** `app/gui/styles.py` (v1.6.0 → v1.7.0) —
  `LIGHT_THEME_STYLESHEET`, `THEME_STYLESHEETS`,
  `apply_theme(app, thema)`; `apply_dark_theme` blijft als wrapper.
- **Gewijzigd:** `app/config/settings.py` (v1.7.0 → v1.8.0) —
  `TOEGESTANE_THEMAS`, `STANDAARD_THEMA`, `normaliseer_thema()`,
  normalisatie in `laad_instellingen()`.
- **Gewijzigd:** `app/gui/dialogs/settings_dialog.py` (v1.6.0 →
  v1.7.0) — actieve `thema_combo`, `normaliseer_thema()` als vangnet.
- **Gewijzigd:** `app/gui/main_window.py` (v2.20.0 → v2.22.2) —
  `theme`-parameter, `_apply_theme_if_needed()`,
  `self.setStyleSheet()` in plaats van `QApplication.setStyleSheet()`,
  `theme` doorgeven aan `AnalysisScreen` en `HistoryScreen`,
  thema-afhankelijke release-notes-dialoog.
- **Gewijzigd:** `main.py` (v1.5.0 → v1.6.0) — `laad_instellingen()`
  vóór de thematoepassing; `apply_theme(app, thema)` in plaats van
  `apply_dark_theme(app)`.
- **Gewijzigd:** `app/gui/analysis_screen.py` (v1.6.3 → v1.7.0) —
  `theme`-parameter, `CHART_COLORS`, `apply_theme()`, alle
  chart-kleuren per thema.
- **Gewijzigd:** `app/gui/history_screen.py` (v1.17.1 → v1.18.0) —
  `theme`-parameter, `DETAIL_HTML_COLORS`, `apply_theme()`,
  detail-HTML per thema.
- **Nieuw:** `conftest.py` (v1.1.0) — autouse-opruimfixture.
- **Nieuwe tests:** `tests/test_theme_switch.py` (10 tests),
  `tests/test_analysis_screen_theme.py` (11 tests),
  `tests/test_history_screen_theme.py` (11 tests).
- **Gewijzigde tests:** `tests/test_styles.py` (v1.2.0 → v1.3.0,
  12 → 20 tests), `tests/test_settings.py` (v1.4.0 → v1.5.0,
  17 → 23 tests), `tests/test_settings_dialog.py` (v1.3.0 → v1.4.0,
  18 → 24 tests).
- **Nieuwe i18n-keys:** `settings.algemeen.thema_licht`,
  bijgewerkte `settings.algemeen.thema_tooltip` (NL + EN).
- **Baseline:** 1494 → **1546 passed** (+52 tests over 11H.1 t/m
  11H.5).

### Fase 11G — Visueel donker thema (20 oktober 2026)

**Waarom deze wijziging**

Vijf visuele punten uit eerdere sessies stonden nog open: checkbox- en
radiobutton-focus was onzichtbaar in het donkere thema, de scrollbar in
de Word-samenvatting van de import-wizard was licht, de Analyse-pagina
had geen leesbaar tickformaat, geen zoom/pan en geen klikbare
datapunten. Daarnaast sloot de menu-optie "Afsluiten" op een subpagina
alleen het venster in plaats van de applicatie.

**Oplossing: zeven sub-fases**

- **11G.1 — Checkbox- en radio-zichtbaarheid.** `styles.py` (v1.4.0)
  krijgt `QCheckBox::indicator:focus`, `QRadioButton::indicator:focus`,
  `QTableView::indicator`, `QGroupBox::indicator` en
  `QComboBox::drop-down:hover`. Nieuwe pure tests in
  `tests/test_styles.py` (v1.0.0).
- **11G.2 — Donkere scrollbar.** `styles.py` (v1.5.0) krijgt
  `QScrollBar:vertical` en `QScrollBar:horizontal` met donkere track,
  grijze handle, hover/pressed-states, en uitgeschakelde pijl-knoppen
  (`add-line`/`sub-line` op `height: 0` / `width: 0`).
  `tests/test_styles.py` (v1.1.0) krijgt drie scrollbar-tests.
- **11G.3 — As-schaling en tickformaat.** `analysis_screen.py`
  (v1.4.0) geeft `QValueAxis` een expliciet `labelFormat` per
  grafiektype en een 5%-marge op de y-as. `QDateTimeAxis` krijgt een
  adaptief formaat. `test_analysis_screen.py` (v1.4.0) krijgt vijf
  tests.
- **11G.4 — Zoom/pan.** `analysis_screen.py` (v1.5.0) zet
  `QChartView.RubberBand.RectangleRubberBand`, voegt een
  `wheelEvent`-override toe voor Ctrl+wheel-zoom, een
  `reset_zoom_btn` met Ctrl+0, en een `refresh()` die de zoom
  automatisch reset. Nieuwe i18n-keys `analyse.zoom.reset_knop` en
  `analyse.zoom.reset_tooltip` (NL + EN).
  `test_analysis_screen.py` (v1.5.0) krijgt vijf tests.
  **Fix in v1.5.1:** `QChartView.RubberBand.Rectangle` bestaat niet;
  de juiste constante is `RectangleRubberBand`.
- **11G.5 — Klikbare datapunten + selectie-gedreven analyse.** De
  bestaande `export_scope_combo` stuurt nu ook de grafiek-scope aan.
  Labels komen uit `analyse.scope.*` (NL + EN). Bij scope SELECTED en
  ≥1 aangevinkte meting geeft de GUI `measurement_ids=[...]` mee aan
  de service. `AnalysisService` (v1.1.0) krijgt een optionele
  `measurement_ids`-parameter. In `_draw_scatter` krijgt elke
  `QScatterSeries` een `clicked`-connectie.
  `test_analysis_screen.py` (v1.6.0) krijgt zes tests,
  `test_analysis_service.py` (v1.1.0) twee.
  **Fix in v1.6.1–v1.6.3:** `refresh(preserve_selection=True)` bewaart
  de selectie bij scope SELECTED; de "Selectie gewist"-melding
  verschijnt weer bij een gewone refresh; `_category_label` en
  `_category_color` waren per ongeluk verdwenen en zijn teruggezet.
  `test_analysis_screen_nan.py` (v1.0.4) en
  `test_main_window_report_menu.py` (v1.4.1) krijgen de nieuwe
  `measurement_ids`-parameter op hun stubs.
- **11G.6 — Expliciet afsluiten sluit de app.** `main_window.py`
  (v2.20.0) krijgt een `_force_close`-vlag en een `_sluit_app()`-
  methode. Menu "Afsluiten" (Ctrl+Q) en de bevestigingsdialoog op de
  hub gebruiken `_sluit_app()`. `closeEvent` accepteert het event
  als `_force_close` True is; anders blijft het contextuele "terug
  naar hub"-gedrag voor de venster-X op een subpagina.
  `test_navigation_regressions.py` (v1.2.0) krijgt vijf tests.
- **11G.7 — Filter-checkbox zichtbaarheid.** `styles.py` (v1.6.0)
  geeft `QGroupBox::indicator` een lichtere achtergrond (`#3C3C3C`)
  en een dikkere rand (2px `#B0B0B0`) in unchecked-state.
  Checked-state is blauw (`#0078D7`) met 2px rand (`#4AA3FF`).
  `tests/test_styles.py` (v1.2.0, +3).

**Voor ontwikkelaars**

- **Gewijzigd:** `app/gui/styles.py` (v1.3.0 → v1.6.0) — focus-states,
  tabel-indicator, groupbox-indicator, combobox-hover, donkere
  scrollbar, duidelijker groupbox-checkbox.
- **Gewijzigd:** `app/gui/analysis_screen.py` (v1.3.0 → v1.6.3) —
  as-schaling, tickformaat, zoom/pan, klikbare scatter-punten,
  selectie-gedreven scope.
- **Gewijzigd:** `app/services/analysis_service.py` (v1.0.0 → v1.1.0)
  — optionele `measurement_ids`-parameter.
- **Gewijzigd:** `app/gui/main_window.py` (v2.19.1 → v2.20.0) —
  `_force_close`, `_sluit_app()`, `closeEvent`-update.
- **Gewijzigd:** `tests/test_styles.py` (v1.2.0, 12 tests).
- **Gewijzigd:** `tests/test_analysis_screen.py` (v1.3.1 → v1.6.2,
  30 → 46 tests), `tests/test_analysis_screen_nan.py`
  (v1.0.3 → v1.0.4, 6 tests), `tests/test_analysis_service.py`
  (v1.0.0 → v1.1.0, 7 → 9 tests),
  `tests/test_main_window_report_menu.py` (v1.4.0 → v1.4.1),
  `tests/test_navigation_regressions.py` (v1.1.0 → v1.2.0,
  5 → 10 tests).
- **Nieuwe i18n-keys:** `analyse.zoom.reset_knop`,
  `analyse.zoom.reset_tooltip`, `analyse.scope.selectie`,
  `analyse.scope.filters`, `analyse.scope.tooltip` (NL + EN).
- **Baseline:** 1462 → **1494 passed** (+32 tests over 11G.1 t/m
  11G.7).

### Fase 11F — Documentatie-uitbreiding (20 oktober 2026)

**Waarom deze wijziging**

De documentatiebibliotheek had vier praktische beperkingen: er was geen
plek om vast te leggen waarom een import gearchiveerd werd, de
"Toon gearchiveerde"-checkbox was een alles-of-niets-schakelaar, je kon
maar één import per keer bewerken of van status laten veranderen, en
`EditMetadataDialog` accepteerde alleen ISO-datums als bestaande
`document_date`. Daarnaast stonden er twee cosmetische punten open
(§4.21, §4.23) en was er een aantal ongebruikte i18n-keys.

**Oplossing: vier sub-fases**

- **11F.1 — Archiefreden.** `ImportService.archive(source_id, *,
  reason=None)` in `import_service.py` (v1.5.0). `ImportSource` krijgt
  `archive_reason` (v1.4.0), backward-compatible. `revoke` behoudt de
  reden; `replace_source` en `update_metadata` laten het veld
  ongemoeid. `ChangeStatusDialog` (v1.2.0) toont een optioneel
  redenveld bij archiveren. `DocumentationScreen` (v2.4.0) toont de
  reden als tooltip op de Status-kolom bij een gearchiveerde
  gebruikersimport.
- **11F.2 — Statusfilter.** `DocumentationScreen` (v2.5.0) vervangt de
  checkbox "Toon gearchiveerde" door een `status_filter_combo` met
  vier opties (Alle / Concept / Actief / Gearchiveerd). De GUI filtert
  op `import_status` na het ophalen uit de service. Nieuwe i18n-keys
  onder `documentatie.status_filter.*`; de oude
  `documentatie.toon_gearchiveerd(_tooltip)` zijn verwijderd.
- **11F.3 — Bulk-edit en bulk-statuswijziging.** Twee nieuwe dialogen:
  `BulkEditMetadataDialog` (v1.0.0) met een checkbox per veld, en
  `BulkChangeStatusDialog` (v1.0.0) met een vaste doelstatuskeuze en
  optionele reden bij archiveren. `DocumentationScreen` (v2.6.0) staat
  op `ExtendedSelection` met twee nieuwe knoppen "Bulk bewerken…" en
  "Bulk status…". Nieuwe i18n-keys onder `documentatie.bulk_edit.*`,
  `documentatie.bulk_status.*` en `documentatie.bulk_resultaat.*`.
- **11F.4 — Datum-parsing + cosmetische punten + i18n-opruiming.**
  `EditMetadataDialog` (v1.2.0) heeft een nieuwe pure helper
  `_parse_datum_naar_qdate` die naast `yyyy-MM-dd` ook `yyyy/MM/dd`,
  `dd-MM-yyyy`, `yyyy-MM` (dag 1) en `yyyy` (1 januari) accepteert.
  §4.21 opgelost: `test_icon_paths.py` (v1.1.0) gebruikt de
  projectafspraak `_app()`-helper. §4.23 opgelost: `_fake_translate`
  in `test_gui_language_switch.py` (v1.3.1) doet echte
  format-vervanging waar de sleutel `{placeholders}` bevat. i18n-
  opruiming: ongebruikte keys `dialog.documentatie_placeholder` en
  `documentatie.info.ondersteunt` verwijderd uit NL en EN.

**Voor ontwikkelaars**

- **Gewijzigd:** `app/gui/documentation_screen.py` (v2.4.0 → v2.6.0) —
  statusfilter-dropdown, `ExtendedSelection`, twee bulk-knoppen.
- **Gewijzigd:** `app/gui/dialogs/edit_metadata_dialog.py`
  (v1.1.0 → v1.2.0) — `_parse_datum_naar_qdate` met fallback-keten.
- **Nieuw:** `app/gui/dialogs/bulk_edit_metadata_dialog.py` (v1.0.0).
- **Nieuw:** `app/gui/dialogs/bulk_change_status_dialog.py` (v1.0.0).
- **Nieuwe tests:** `tests/test_bulk_edit_metadata_dialog.py` (11
  tests), `tests/test_bulk_change_status_dialog.py` (10 tests),
  uitbreiding `tests/test_documentation_screen.py` (55 → 63 tests),
  uitbreiding `tests/test_edit_metadata_dialog.py` (22 → 34 tests).
- **Gewijzigde tests:** `tests/test_icon_paths.py` (v1.0.0 → v1.1.0),
  `tests/test_gui_language_switch.py` (v1.2.0 → v1.3.1).
- **Nieuwe i18n-keys:** `documentatie.status_kolom.gearchiveerd_met_reden`,
  `documentatie.status_wijzigen_reden.*`,
  `documentatie.status_filter.*`, `documentatie.bulk_edit.*`,
  `documentatie.bulk_status.*`, `documentatie.bulk_resultaat.*`.
- **Verwijderde i18n-keys:** `documentatie.toon_gearchiveerd`,
  `documentatie.toon_gearchiveerd_tooltip`,
  `dialog.documentatie_placeholder`, `documentatie.info.ondersteunt`.
- **Baseline:** 1395 → **1462 passed** (+67 tests over 11F.1 t/m
  11F.4).

### Fase 11E — Async netwerk (16 oktober 2026)

**Waarom deze wijziging**

De update-check, de release-notes-fetch en de URL-import in de
import-wizard deden hun netwerkverkeer **synchroon in de GUI-thread**.
Bij een trage of onbereikbare server bevroor de GUI heel even.

**Oplossing: drie sub-fases**

- **11E.1 — Async update-check.** Nieuwe module
  `app/helpers/async_worker.py` (v2.0.0) met een generieke
  `AsyncWorker(QRunnable)` en `run_async()`-helper.
  `app/helpers/updater.py` (v1.2.0) krijgt
  `check_for_update_async()` en `fetch_release_notes_async()`.
  `app/gui/main_window.py` (v2.18.0) gebruikt die async-varianten.
- **11E.2 — Async URL-fetch in de import-wizard.**
  `app/documentation/url_fetch.py` (v1.2.0) krijgt
  `fetch_url_metadata_async()` en `fetch_url_content_async()`.
  `app/gui/dialogs/import_wizard_dialog.py` (v2.0.0) gebruikt die
  async-varianten.
- **11E.3 — Drie-knoppenmelding forceren voor QA.**
  `app/config/settings.py` (v1.7.0) krijgt `algemeen.qa_modus`.
  `app/gui/main_window.py` (v2.19.0) toont een verborgen QA-menu-item
  in het Help-menu als `qa_modus` True is.

**Belangrijke bugfix in 11E.1**

De eerste versies van `async_worker.py` faalden met
`RuntimeError: Signal source has been deleted`. Oorzaak: de
`WorkerSignals` werd opgeruimd voordat de emit klaar was. De
definitieve oplossing (v2.0.0): `WorkerSignals` als sterk
Python-attribuut op de `AsyncWorker`, `setAutoDelete(False)`, geen
registry. **De aanroeper is eigenaar** en moet de return-waarde
bewaren. In de GUI doet `main_window.py` dat via
`self._update_check_worker` en `self._release_notes_worker`; in de
wizard via `self._url_fetch_worker` en `self._import_worker`. In
tests via `_bewaarde_workers`.

**Kleine bugfix in 11E.3**

`app/gui/main_window.py` (v2.19.1) gebruikt dubbele `getattr` in
`_build_menu()` en `_apply_settings()`, zodat een test of een oudere
`settings.json` zonder `algemeen`-namespace geen `AttributeError`
veroorzaakt.

**Voor ontwikkelaars**

- **Nieuw:** `app/helpers/async_worker.py` (v2.0.0).
- **Gewijzigd:** `app/helpers/updater.py` (v1.2.0) — async-varianten.
- **Gewijzigd:** `app/documentation/url_fetch.py` (v1.2.0) —
  async-varianten.
- **Gewijzigd:** `app/gui/main_window.py` (v2.19.1).
- **Gewijzigd:** `app/gui/dialogs/import_wizard_dialog.py` (v2.0.0).
- **Gewijzigd:** `app/config/settings.py` (v1.7.0) — `qa_modus`.
- **Nieuwe tests:** `tests/test_async_worker.py` (9 tests),
  uitbreiding `tests/test_updater.py` (+4 async-tests),
  `tests/test_startup_update_check.py` (herschreven voor async),
  `tests/test_main_window_update_menu.py` (v1.3.0, +3 QA-tests),
  `tests/test_documentation_url_fetch.py` (v1.1.0, +6 async-tests),
  `tests/test_import_wizard_dialog.py` (v1.8.0, +3 async-tests).
- **Nieuwe i18n-keys:** `documentatie.import.bezig_metadata`,
  `documentatie.import.bezig_import`, `menu.qa_toon_update_melding`.
- **Baseline:** 1366 → **1395 passed** (+29 tests).

### Fase 11D — i18n-menging oplossen (16 oktober 2026)

**Waarom deze wijziging**

Na een live taalwissel toonde het ESR-scherm een mengeling van talen:
de GUI-chrome schakelde netjes om, maar de reeds vertaalde strings uit
het `Beoordeling`-object bleven in de oude taal staan. Daarnaast was de
`*`-toelichting bij een frequentieverschil hardcoded in de GUI.

**Oplossing**

- `Beoordeling` krijgt een `taal`-veld dat wordt gevuld door
  `beoordeel_meting`. De GUI kan daarmee detecteren dat een resultaat
  in een andere taal is opgesteld.
- Na een live taalwissel toont het ESR-scherm een nette banner in de
  GUI-taal. De reeds vertaalde resultaatstrings blijven in hun eigen
  taal; er is geen stille mengeling meer.
- `_show_result` en `_build_result_html` vertalen alle
  resultaat-specifieke labels in `resultaat.taal`.
- De losse `*`-toelichting loopt nu via twee nieuwe i18n-keys in NL
  én EN.
- Bugfix in `apply_language`: de conditie `result_group.isVisible()`
  is vervangen door `_laatste_resultaat is not None`.

**Voor ontwikkelaars**

- `app/services/assessment_service.py` (v1.6.0) — `Beoordeling` heeft
  het extra veld `taal: str = STANDAARD_TAAL`.
- `app/gui/esr_test_screen.py` (v1.14.0) — `_show_result` detecteert
  taal-mismatch en toont `result_language_banner`. Nieuwe helper
  `_t_voor(taal, sleutel, **kwargs)`.
- Nieuwe i18n-keys onder `resultaat`: `taal_mismatch_banner`,
  `esr_factor_frequentie_indicatief`,
  `esr_factor_frequentie_indicatief_kort` (NL + EN).
- `tests/test_assessment.py` (v1.5.1) — 5 nieuwe tests.
- `tests/test_gui_language_switch.py` (v1.2.0) — 3 nieuwe tests.
- **Baseline:** 1358 → **1366 passed** (+8 tests).

## Versie 1.2.0 — Frequentie-specifieke referenties en drempelvalidatie (15 oktober 2026)

**ESR-referenties per meetfrequentie**

De ESR-referentie is nu **frequentie-specifiek**. In plaats van één
officiële ESR70-tabel op 100 kHz te gebruiken voor alle metingen, kiest
de applicatie voortaan het referentieprofiel dat het dichtst bij de
werkelijke meetfrequentie ligt.

- **Officiële ESR70-tabel** — 100 kHz. Blijft de primaire bron voor
  metingen op 100 kHz.
- **Geschatte profielen** — 100 Hz, 1 kHz en 10 kHz, afgeleid van de
  officiële ESR70-tabel via de Nichicon-frequentiecoëfficiënten
  (×2,00 / ×1,50 / ×1,15). Expliciet gemarkeerd als schatting
  (`is_schatting: true`) met lager betrouwbaarheidsniveau.

**Waarom deze wijziging**

De LCR-ST1 meet op 1 kHz en 10 kHz. De officiële ESR70-tabel geldt voor
100 kHz. Omdat ESR daalt met frequentie, was de vergelijking
structureel te streng.

**Validatie met 72 praktijkmetingen**

Voor goede condensatoren zakten de factoren naar **0,09–0,41** — een
gezonde verdeling. De drempels `≤1,0 / ≤2,0 / ≤3,0` blijven ongewijzigd.

**Zichtbaar in het resultaat**

Het resultaat toont nu expliciet de **referentiefrequentie** die voor
de vergelijking gebruikt is.

**Voor ontwikkelaars**

- `app/data/references/esr_references.json` — nieuwe profielen
  `algemeen_100hz_geschat`, `algemeen_1khz_geschat`,
  `algemeen_10khz_geschat`.
- `app/data/references/__init__.py` — `zoek_referentie()` accepteert
  `meetfrequentie_hz`.
- `app/services/assessment_service.py` — `Beoordeling` heeft het veld
  `referentiefrequentie_hz`.
- Nieuwe i18n-key: `resultaat.referentiefrequentie` (NL + EN).
- Nieuw analysedraaiboek: `scripts/herbereken_steekproef.py`.

### UX-afwerking (fase 11A, 16 oktober 2026)

**Export respecteert nu de selectie**

In de **Historiek** en de **Analyse** kun je met een selectie-DDL kiezen
wat je exporteert: **huidige filters** of **selectie**.

**Selectie en rapport in de Analyse-pagina**

De **Analyse**-pagina heeft onder de grafiek een compacte selectielijst
met **Exporteren…** en **Rapport maken…**.

**Rapport met scope "selectie"**

Het meetrapport ondersteunt nu een rapport over **meerdere metingen**.

**Menu "Rapport maken…" is disabled zonder selectie**

In het **Bestand**-menu is het item **Rapport maken…** nu disabled
zolang je geen meting geselecteerd hebt.

**Mapvoorkeuren worden overal gerespecteerd**

Een nieuwe pure helper (`app/helpers/dialog_start_directory.py`)
bepaalt de beste startmap voor elke `QFileDialog`.

**Voor ontwikkelaars**

- `app/gui/analysis_screen.py` — compacte selectielijst, scope-DDL,
  exportknop en `report_btn`.
- `app/gui/history_screen.py` — `selection_changed`-signaal.
- `app/gui/main_window.py` — `_open_report_dialog()`.
- `app/gui/dialogs/report_dialog.py` — `for_measurements(...)`.
- **Nieuw:** `app/helpers/dialog_start_directory.py` (v1.0.0).
- Nieuwe i18n-keys: 24 onder `analyse.selectie.*`, `analyse.export.*`,
  `analyse.rapport.*` en `menu.rapport_tooltip` (NL + EN).
- Baseline: **1339 passed** (was 1329 vóór 11A).

### Betrouwbaarheidsregel herzien (fase 11B, 16 oktober 2026)

**Oplossing: inhoudelijk vs. administratief**

Er is nu een onderscheid tussen **inhoudelijke** en **administratieve**
betrouwbaarheidsverlagers. Inhoudelijke verlagers verhogen het minimum
van de eindstatus; administratieve verlagen de betrouwbaarheid wel,
maar verhogen het minimum niet. "Waarschijnlijk goed, betrouwbaarheid
laag door administratieve factoren" is nu mogelijk.

**Voor ontwikkelaars**

- `app/services/assessment_service.py` (v1.5.0) —
  `BetrouwbaarheidsResultaat` heeft `inhoudelijke_verlagers`.
- Nieuwe i18n-keys: `betrouwbaarheid_factor.categorie_inhoudelijk`,
  `betrouwbaarheid_factor.categorie_administratief`,
  `eindstatus_reden.betrouwbaarheid_laag_administratief`,
  `resultaat.inhoudelijke_verlagers`,
  `resultaat.administratieve_verlagers` (NL + EN).
- `tests/test_assessment.py` (v1.5.0) — 10 nieuwe tests.
- **Baseline:** 1329 → **1339 passed** (+10 tests).

### Iconen voor alle vensters (fase 11C, 16 oktober 2026)

**Eén applicatie-icoon, twaalf thematische iconen**

De applicatie heeft nu een volledige iconenset: `assets/icons/app.png`,
`assets/icons/logo.ico` en twaalf thematische iconen. De huidige iconen
zijn **placeholders** die met een script zijn gegenereerd
(`scripts/genereer_placeholders.py`).

**Voor ontwikkelaars**

- **Nieuw:** `app/helpers/icon_paths.py` (v1.0.0).
- **Nieuw:** `scripts/genereer_placeholders.py` (v1.0.0).
- **Gewijzigd:** `main.py` (v1.5.0), `app/gui/main_window.py` (v2.17.0),
  alle dialogen in `app/gui/dialogs/`,
  `app/gui/esr_test_screen.py` (v1.13.0).
- **Nieuw:** `tests/test_icon_paths.py` (16 tests),
  `tests/test_main_icon.py` (1 test).
- **Uitgebreid:** `tests/test_main_window_help_menu.py` en
  `tests/test_main_window_report_menu.py` (1 test elk).
- **Baseline:** 1339 → **1358 passed** (+19 tests).

## Versie 1.1.1 — Update-controle bij opstarten en via Help (15 oktober 2026)

**Automatische controle op een nieuwere versie**

De applicatie controleert bij het opstarten eenmalig en niet-blokkerend
of er een nieuwere versie beschikbaar is op GitHub.

**Handmatige controle via Help**

Je kunt de controle ook handmatig uitvoeren via
**Help → Controleren op updates…**.

**Wat is er nieuw?**

Als er een nieuwere versie is, toont de melding ook een knop
**Wat is er nieuw?** met de release notes van de GitHub-release.

**Instelling: bij opstarten controleren op updates**

In **Instellingen → Algemeen** staat een nieuwe checkbox
**Bij opstarten controleren op updates** (standaard aan).

**Meertalige changelog**

De changelog is nu beschikbaar per taal: `docs/changelog/nl_NL.md` en
`docs/changelog/en_US.md`.

**Voor ontwikkelaars**

- Nieuwe module `app/helpers/updater.py`.
- Nieuwe resolver `changelog_pad_voor_taal()` in
  `app/helpers/help_paths.py`.
- Nieuwe i18n-keys onder `update.*` en
  `settings.algemeen.controleer_updates` (NL + EN).
- Nieuwe instelling `algemeen.controleer_updates_bij_opstarten` (default
  `True`), backward-compatible.

## Versie 1.0.3 — Publicatie, testmatrix en bug/feature-meldingen (14 oktober 2026)

**De applicatie is nu publiek beschikbaar op GitHub**

Op 13 oktober 2026 is de eerste publieke release **v1.0.3** verschenen
in de repo `barremans/capacitor_esr_validator`.

**Buildstraat uitgebreid met `publish.ps1` en `build_and_publish.ps1`**

- **`publish.ps1`** — publiceert de installer naar GitHub, met een
  **release-gate** op de Authenticode-handtekening.
- **`build_and_publish.ps1`** — orchestrator die de hele keten draait.

**Intune/Defender-testmatrix**

De installer is bewezen op twee soorten Windows-pc's: gewone pc
(SmartScreen-waarschuwing, "More info → Run anyway" werkt) en
Intune-beheerde pc (start zonder blokkade dank zij een Defender
Certificate Indicator voor het CGK-certificaat).

**Bug- en feature-meldingen vanuit de applicatie**

Het hoofdmenu heeft nu een **Rapporteren**-menu met **🐞 Bug of feature
melden…** en **Open cases tonen**. De meldingen gaan rechtstreeks naar
de GitHub-repo via de REST API.

**Voor ontwikkelaars**

- Het feedbackpakket (`github_feedback.py`, `bug_report_dialog.py`,
  `github_cases.py`, `check_github_secret.py`) staat identiek in de
  projectroot.
- Het GitHub-token staat in `github_secret_local.py`, dat in
  `.gitignore` staat en nooit naar GitHub gaat.
- Nieuwe i18n-keys: `menu.rapporteren`, `menu.bug_melden`,
  `menu.open_cases` (NL + EN).

**Opgelost**

- `LF/CRLF`-waarschuwing op `releases/latest/version.txt` via
  `.gitattributes`.
- `ESR_Tester.spec` staat niet langer in `.gitignore`.

**Documentatie**

- `docs/packaging.md` — build-flow, signing, distributie, checklist.
- `docs/testmatrix_defender_intune.md` — de volledige testmatrix.

## Versie 1.0.2 — Eerste Windows-build, installer en signing (13 oktober 2026)

**De applicatie heeft nu een echte versie**

Centrale versie in `app/version.py`, getoond in Help → Over.

**Volledige Windows-buildstraat**

- **`ESR_Tester.spec`** — PyInstaller-specificatie.
- **`build_installer.bat`** — bouwt de EXE, genereert
  `dist\installer.iss`, compileert met Inno Setup 6, en tekent.
- **`bump_version.py`** — verhoogt patch, minor of major.
- **`build_and_publish.ps1`** — orchestrator met signing-preflight.
- **`publish.ps1`** — publiceert naar GitHub met release-gate.

**Code-signing**

De EXE en de installer worden ondertekend met het CGK-certificaat
(`CN=CGK Local Signing`, geldig tot 2028-09-17).

**Installer met icoon**

De installer heeft nu het ESR Tester-icoon in de wizard en in de
snelkoppelingen. De app start na installatie met gebruikersrechten.

**Opgelost**

- Venstertitels van Help en Wijzigingslog toonden onvertaalde keys.
- De ESR-testknop in de Diagnose-pagina toonde `tool.esr`.
- De buildstraat brak af met `: was unexpected at this time.` door een
  `set /p`-prompt met haakjes.

**PDF's met leesbare tekst, zonder handmatige stap**

De applicatie stelt nu automatisch `QT_QPA_FONTDIR=C:\Windows\Fonts` in
op Windows.

**Voor ontwikkelaars**

- `numpy` pin `>=1.26,<3`, `pandas` pin `>=2.2,<3`.
- `QT_QPA_FONTDIR` wordt in `main.py` gezet vóór `QApplication`.
- `app/version.py` is de centrale versiebron.

## Versie 1.0.1 — Meetrapporten en uitgebreidere instellingen (12 oktober 2026)

**Meetrapporten maken**

Van elke opgeslagen meting kun je een **meetrapport** maken (HTML of
PDF) met componentidentificatie, meetcontext, ruwe meetwaarden,
assessment-snapshots, referentie-snapshots en een optionele grafiek.

**Nieuw in de Rapportage-instellingen**

- **Auteur** — optioneel vrij veld in de rapportkop.
- **Standaard rapportmap** — automatisch bijgewerkt na elke opslag.

**Automatisch de map openen**

Na het opslaan van een rapport wordt automatisch de map geopend (als de
instelling aan staat).

**Read-only**

Het rapport wordt opgebouwd uit de opgeslagen snapshots. Historische
metingen en beoordelingen worden nooit opnieuw berekend.

**Opgelost**

- `algemeen.ja` en `algemeen.nee` verschenen als onvertaalde keys;
  nu `app.ja` en `app.nee`.
- Statuslabels in het rapport werden als ruwe codes getoond; nu
  vertaald.

## Versie 1.0.0 — Grafieken en trends (9 oktober 2026)

**Nieuwe pagina "Analyse"**

Naast Diagnose, Historiek en Documentatie staat nu een vierde hub-knop
**Analyse** met vier grafiektypes: ESR over tijd, capaciteit over tijd,
D over tijd, en ESR vs. capaciteit.

**Filteren op precies dezelfde velden als de historiek**

De filterbalk gebruikt dezelfde velden als de historiekpagina.

**Aggregatie per dag, week of maand**

Met een tweede dropdown kies je gemiddelde per dag, per week of per
maand.

**Read-only**

De Analyse-pagina leest je opgeslagen metingen en schrijft niets terug.

**Sneltoetsen**

- **Ctrl+A** opent de Analyse-pagina.
- **Ctrl+R** ververst de gegevens.
- **Ctrl+F** opent het filterpaneel.
- **Esc** gaat terug naar het Hoofdmenu.

---

<!--
Vanaf hier: vroege ontwikkelfases. De nummering is historisch en komt
niet altijd 1-op-1 overeen met `app/version.py`. Deze entries blijven
staan als functionele mijlpalen.
-->

## Versie 0.9 — Fabrikantdocumenten: Word en Excel (9 oktober 2026)

**Word- en Excel-import**

Naast PDF en URL kun je nu ook **Word-documenten (.docx)** en
**Excel-werkmappen (.xlsx)** importeren als documentatiebron. De
import-wizard heeft vier keuzes.

**Oude formaten worden geweigerd**

Het oude `.doc`- en `.xls`-formaat worden niet ondersteund.

## Versie 0.8 — Status van eigen imports beheren (8 oktober 2026)

**Status van een import wijzigen**

In de documentatiebibliotheek is er nu een knop **Status wijzigen…**
voor je eigen imports.

**Nieuwe Status-kolom**

De documentatietabel heeft nu een extra kolom **Status**.

## Versie 0.7 — Metadata bij import en bewerken in de viewer (7 oktober 2026)

**Metadata bij importeren van een PDF of URL**

Bij het importeren kun je meteen metadata invullen.

**Metadata bewerken in de documentatiebibliotheek**

In de documentatiebibliotheek is er nu een knop **Bewerken…**.

**Verbeterd zoeken**

Het zoekveld doorzoekt nu ook de metadata van geïmporteerde documenten.

## Versie 0.6 — Help per taal en duidelijkere zoekuitleg (6 oktober 2026)

**Nieuw**
- **Help per taal.**
- **Duidelijkere uitleg over uitsluiten in de zoekhulp.**

## Versie 0.5 — Sneltoetsen en veiliger afsluiten (5 oktober 2026)

**Nieuw**
- Werken met het toetsenbord door de hele applicatie.

## Versie 0.4 — Slimmer zoeken en hulp in de documentatie (5 oktober 2026)

**Nieuw**
- **Zoektaal voor documentatie.**
- **Help bij het zoeken.**

## Versie 0.3 — Meerdere diagnosetools in één hub (3 oktober 2026)

**Nieuw**
- Documenten kunnen nu aan meerdere diagnosetools gekoppeld worden.

## Versie 0.2 — Documentatiebibliotheek (3 oktober 2026)

**Nieuw**
- Een centrale, meertalige documentatiebibliotheek met 8 technische
  documenten.

## Versie 0.1 — Eerste werkende versie (11 augustus 2026)

**Nieuw**
- Eerste versie van de ESR-validator.

---

## Gepland voor volgende versies

- **Versie 1.2.0 — UX/documentatie-afwerking.** Alle kleine punten die
  in eerdere fases zijn blijven liggen:
  - **11A** — Export, import en selectie. **Afgerond op 16 oktober 2026.**
  - **11B** — Betrouwbaarheidsregel herzien. **Afgerond op 16 oktober
    2026.**
  - **11C** — Iconen voor alle vensters. **Afgerond op 16 oktober 2026.**
  - **11D** — i18n-menging in Diagnose/Result oplossen. **Afgerond op
    16 oktober 2026.**
  - **11E** — Async netwerk. **Afgerond op 16 oktober 2026.**
  - **11F** — Documentatie-uitbreiding. **Afgerond op 20 oktober 2026.**
  - **11G** — Visueel donker thema. **Afgerond op 20 oktober 2026.**
  - **11H** — Licht thema. **Afgerond op 21 oktober 2026.**
  - **11I** — Build en cosmetica. **Afgerond op 22 oktober 2026.**
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