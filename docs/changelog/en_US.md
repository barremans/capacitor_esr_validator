# Changelog

Overview of what is new or improved in the Electronics Diagnostic Tool
Hub. For technical details and architecture decisions, see
`docs/context.md`.

<!--
Note on version numbering:
- From v1.1.1 onwards, the version numbers map 1-to-1 to
  `app/version.py`, to the GitHub releases, and to
  `releases/latest/version.txt`.
- Before v1.1.1, the numbering is historical: the early development
  phases used their own 1.x counter that did not always match the
  final releases. Those entries remain as functional milestones; they
  cannot be mapped 1-to-1 to a specific `app/version.py` value.
- For the current version: see `app/version.py` or Help → About.
-->

### Chat 3 — Import wizard and exchange selection (26 October 2026)

**Why this change**

Two previously reported points from the master plan turned out not to
work, or not to work correctly, in practice: the "Import document…"
button did not open the import wizard (A2), and the exchange dialog
exported the filters instead of the checked selection (A4). Both are
debug points, not new features.

**Solution: two sub-phases**

- **3A — Import wizard (master plan A2).** The button "File → Import
  document…" and the "Import" button on the Documentation page did
  nothing. Cause: a typo in `main_window._show_import_wizard()` —
  `self._zet_dialoog_icono(...)` instead of
  `self._zet_dialoog_icoon(...)`. The error raised an
  `AttributeError` before `dialog.exec()`. Fix: one line in
  `app/gui/main_window.py` (v2.23.0 → v2.23.1). New test:
  `tests/test_main_window_import_menu.py` (v1.0.1, 4 tests).
  Baseline 1711 → **1715**.
- **3B — Exchange selection (master plan A4).** The exchange dialog
  exported the filters instead of the selection. Cause: two
  independent `if` rules in `ExchangeDialog._build_export_tab()`
  determined the default scope; the second (on `active_filters`)
  overwrote the first (on `selected_measurement_ids`). On
  AnalysisScreen `_active_filters()` is never empty because of the
  implicit `tool_key="ESR_CAPACITOR"`, so the scope there was always
  FILTERED. Fix: new private helper `_bepaal_default_scope()` with an
  explicit priority — selection > filters > selection-as-fallback.
  `exchange_dialog.py` v1.0.1 → v1.0.2. New tests: 3 in
  `tests/test_exchange_dialog.py` (v1.0.1 → v1.0.2). Baseline
  1715 → **1718**.

**Important observation**

The typo from 3A had already been mentioned in `overdracht.md` §2.2
since §2.28 as "important bugfix in §2.28", but the code in
`main_window.py` v2.23.0 still contained it. Documentation and code
had drifted apart. Lesson: with every handover, check whether the
mentioned bugfixes are actually present in the supplied files.

**For developers**

- **Changed:** `app/gui/main_window.py` (v2.23.0 → v2.23.1) — typo
  in `_show_import_wizard()`.
- **Changed:** `app/gui/dialogs/exchange_dialog.py`
  (v1.0.1 → v1.0.2) — `_bepaal_default_scope()` with explicit
  priority.
- **New tests:** `tests/test_main_window_import_menu.py`
  (v1.0.1, 4 tests).
- **Extended:** `tests/test_exchange_dialog.py` (v1.0.1 → v1.0.2,
  11 → 14 tests).
- **Baseline:** 1711 → **1718 passed** (+7 tests across 3A and 3B).

### Phase §2.28 — Export/import between devices (23 October 2026)

**Motivation**

The app stores measurements locally on one device. Anyone who wants to
continue on a second PC had to copy the database by hand — with all the
risks that entails. §2.28 adds an explicit exchange format: a JSON
envelope of measurement chains, so you can selectively export and import
measurements on another device without overwriting the existing history.

**Solution: six sub-phases**

- **28A — Format + models.** New binding spec
  `docs/export_import_format.md` (v1.0.0). New models in
  `app/services/exchange/models.py` (v1.0.0): `ExportEnvelope`,
  `ExportedMeasurementChain`, `ImportPlan`, `ImportConflict`,
  `ImportDecision`, `ImportResult`. JSON envelope (not SQLite dump),
  UTF-8 without BOM, pretty-printed, `format_version="1.0"`. Natural
  key = SHA-256 over a canonical JSON of the chain (§6 spec). 34 tests.
- **28B — Export service.** `app/services/exchange/export_service.py`
  (v1.0.1) with `export_measurements`, `export_filters`,
  `write_envelope`, `bereken_natural_key`, `verkrijg_machine_id` and
  (since 28F) `read_envelope`. Machine ID as UUID4 in `settings.json`
  (`algemeen.machine_id`). 15 tests.
- **28C — Import planner.** `app/services/exchange/import_planner.py`
  (v1.0.0) with `ImportPlanner.plan(envelope) -> ImportPlan`. Detects
  duplicates by origin (`source_machine_id` + `source_measurement_id`)
  and by natural key. Recomputes the natural key and rejects a mismatch.
  `HerkomstRepositoryProtocol` for optional origin detection. 11 tests.
- **28E — Schema migration v2 → v3.** `app/storage/schema.py`,
  `migrations.py`, `models.py`, `service.py` (all v1.2.0). Two new
  columns on `measurements`: `source_machine_id TEXT` and
  `source_measurement_id INTEGER` (both nullable). New index
  `ix_measurements_source_identity`. Validation: "both or neither".
  Existing measurements get `NULL`. 16 tests.
- **28D — Import service.** `app/services/exchange/import_service.py`
  (v1.0.0) with `ImportService.apply_plan(plan, on_conflict="conflict_copy")`.
  Writes per chain via `StorageService.save_new_measurement_chain`,
  with a race check before each write. `on_conflict="skip"` or
  `"conflict_copy"`. Per-chain rollback: a failure in one chain does not
  block the rest. 16 tests.
- **28F — GUI integration.** New `app/gui/dialogs/exchange_dialog.py`
  (v1.0.1) with two tabs (Export / Import) and a conflict table. Two new
  menu items in `app/gui/main_window.py` (v2.23.0): "Export to device…"
  (Ctrl+Shift+E) and "Import from device…" (Ctrl+Shift+I). New
  `exchange.json` in NL and EN. New category `"exchange"` in
  `dialog_start_directory.py` (v1.0.1). New `laatste_exchangemap` in
  `settings.py` (v1.8.2). 16 tests.

**Important design decisions**

- **JSON envelope, not SQLite dump.** Human-readable, versionable,
  works across schema versions, and matches the existing `snapshot_json`
  pattern.
- **Origin tracking via schema migration v3.** Two nullable columns on
  `measurements`, filled at import, `NULL` for locally created
  measurements.
- **Natural key = content, not `source_measurement_id`.** Two chains
  with the same content produce the same key, also on different devices
  (spec §6). That makes duplicate detection content-reliable.
- **Conflict copy is the default on a conflict.** Never silently skip
  without the user seeing it; the GUI (28F) offers a per-row "as copy"
  checkbox.
- **Race check before each write.** Two simultaneous imports or an
  intervening new measurement are handled correctly.
- **Per-chain transactions.** A failure in one chain does not block the
  rest of the import; `ImportResult.errors` reports per chain.

**For developers**

- **New:** `app/services/exchange/__init__.py` (v1.0.4),
  `models.py` (v1.0.0), `export_service.py` (v1.0.1),
  `import_planner.py` (v1.0.0), `import_service.py` (v1.0.0).
- **New:** `app/gui/dialogs/exchange_dialog.py` (v1.0.1).
- **New:** `docs/export_import_format.md` (v1.0.0).
- **New:** `i18n/locales/nl_NL/exchange.json` and
  `i18n/locales/en_US/exchange.json`.
- **Changed:** `app/storage/schema.py` (v1.1.0 → v1.2.0),
  `migrations.py` (v1.1.0 → v1.2.0), `models.py` (v1.1.0 → v1.2.0),
  `service.py` (v1.1.0 → v1.2.0).
- **Changed:** `app/gui/main_window.py` (v2.22.2 → v2.23.0) — two new
  menu items + `_open_exchange_dialog`. **Bugfix:** `_show_import_wizard`
  had a typo `self._zet_dialoog_icono(...)` instead of
  `self._zet_dialoog_icoon(...)`. Latent bug that raised an
  `AttributeError` when opening the import wizard. **Note
  (2026-10-26):** that bugfix was only actually applied to the code in
  chat 3A; in v2.23.0 the typo was still present.
- **Changed:** `app/helpers/dialog_start_directory.py`
  (v1.0.0 → v1.0.1) — category `"exchange"`.
- **Changed:** `app/config/settings.py` (v1.8.1 → v1.8.2) —
  `laatste_exchangemap`.
- **Changed:** `app/version.py` (v1.1.0 → v1.2.0) — `__version__ =
  "1.3.0"`.
- **New tests:** `tests/test_exchange_models.py` (v1.0.1, 34),
  `tests/test_exchange_export_service.py` (v1.0.3, 15),
  `tests/test_exchange_import_planner.py` (v1.0.2, 11),
  `tests/test_exchange_import_service.py` (v1.0.1, 16),
  `tests/test_exchange_dialog.py` (v1.0.1, 11; later v1.0.2, 14),
  `tests/test_main_window_exchange_menu.py` (v1.0.0, 5).
- **Extended:** `tests/test_storage_schema.py` (v1.1.0 → v1.2.0),
  `tests/test_storage_migrations.py` (v1.0.0 → v1.1.0),
  `tests/test_storage_service.py` (v1.0.0 → v1.1.0),
  `tests/test_storage_multitool_v2.py` (v1.0.0 → v1.0.1).
- **New i18n keys:** the full `exchange.*` block in both languages.
- **Baseline:** 1598 → **1700 passed** (+102 tests across 28A through 28F).

### Phase 11I — Build and cosmetics (22 October 2026)

**Motivation**

Phase 11I closes the cosmetic and build-technical points left over from
11F/11G/11H: the pandas/numpy pins were undocumented, the icon path was
not robust in the PyInstaller bundle, the build orchestration had three
cosmetic points (x64 deprecation, unclear robocopy fallback, empty
`build_log.txt`), and the two expired certificates in the certificate
store were undocumented.

**Solution: five sub-phases**

- **11I.1 — Documenting the pins.** `requirements.txt` (v1.1.0) gains a
  comment explaining why `numpy` and `pandas` have an upper bound
  `<3`. `docs/packaging.md` (v1.1.0) gains a new §2.1
  "Dependency pins". `docs/future_tools.md` §5 is aligned with the
  actual pins (including `numpy`, `pypdf`, `requests`, `beautifulsoup4`,
  `python-docx`). No pin change: the current pins are proven in the
  PyInstaller bundle.
- **11I.2 — `icon_path` via `sys._MEIPASS`.** `app/helpers/icon_paths.py`
  (v1.1.0) gains an explicit `sys._MEIPASS` branch before the
  upward-search loop. In a PyInstaller bundle, `assets/` lives in
  `_internal/assets/`, and the upward-search loop could also succeed,
  but not deterministically. The explicit branch makes the resolution
  deterministic and independent of the CWD. Two new tests in
  `tests/test_icon_paths.py` (v1.2.0, +2). Baseline 1546 → **1548**.
- **11I.3 — Cleaning up the build orchestration.** Three cosmetic
  points: (a) `ArchitecturesInstallIn64BitMode=x64` → `x64compatible`
  in the generated `.iss` (Inno Setup 6 considers `x64` deprecated);
  (b) the `[rename]` fallback message in `build_installer.bat` is
  clarified (reason + action), and the multi-line echo broke the cmd
  parser — fixed in v2.0.3; (c) `build_installer.bat` now logs the
  PyInstaller step [4] and the ISCC step [7] with
  `>> "%LOGFILE%" 2>&1` to `build_log.txt`. `build_log.txt` is listed
  explicitly in `.gitignore` (does not match `*.log`). In addition:
  `build_and_publish.ps1` (v1.1.0) gives the confirmation question
  "Starten?" an explicit default J on Enter, consistent with the four
  questions before it.
- **11I.4 — Certificate store hygiene.** New §4.1 in
  `docs/packaging.md` (v1.4.0): the preflight in
  `build_and_publish.ps1` skips expired certificates; they are
  harmless; cleanup is optional and manual via Certificate Manager.
  `signing-certs/` (the default folder of
  `Export-SigningCertificate.ps1`) is listed in `.gitignore`.
- **11I.5 — Wrap-up.** Changelog, handover, WatNu and open questions
  updated.

**For developers**

- **Changed:** `requirements.txt` (v1.0.0 → v1.1.0) — comments.
- **Changed:** `app/helpers/icon_paths.py` (v1.0.0 → v1.1.0) —
  `sys._MEIPASS` branch.
- **Changed:** `build_installer.bat` (v2.0.1 → v2.0.3) —
  `x64compatible`, robocopy message clarified (single line), logging
  of [4] and [7] to `build_log.txt`.
- **Changed:** `build_and_publish.ps1` (v1.0.0 → v1.1.0) —
  default J on "Starten?".
- **Changed:** `.gitignore` — `build_log.txt` and `signing-certs/`.
- **Changed:** `docs/future_tools.md` §5 — pins aligned.
- **Changed:** `docs/packaging.md` (v1.0.0 → v1.5.0) — §2.1, §4.1,
  §11 updated.
- **New tests:** `tests/test_icon_paths.py` (v1.1.0 → v1.2.0, +2).
- **Baseline:** 1546 → **1548 passed** (+2 tests).

### Phase 11H — Light theme (21 October 2026)

**Motivation**

The dark theme was the only supported theme so far. The user wanted a
light theme option, without dark patches on a light window. The dark
chart colours, the dark detail HTML in the history detail dialog, and
the dark release-notes dialog had to become per-theme.

**Solution: five sub-phases**

- **11H.1 — Light theme in styles.py.** `styles.py` (v1.7.0) gains
  `LIGHT_THEME_STYLESHEET`, a `THEME_STYLESHEETS` dict and an
  `apply_theme(app, thema="dark")` API. `apply_dark_theme(app)` remains
  as a thin wrapper for backward compatibility. Unknown theme values
  fall back to `"dark"`. The light theme's
  `QGroupBox::indicator:unchecked` gets a white background with a 2px
  `#5A5A5A` border, consistent with the 11G.7 fix in the dark theme.
  New tests in `tests/test_styles.py` (v1.3.0, +8).
- **11H.2 — Theme choice in Settings.** `settings.py` (v1.8.0) gains
  `TOEGESTANE_THEMAS`, `STANDAARD_THEMA` and a pure
  `normaliseer_thema()`. `laad_instellingen()` normalises the loaded
  theme. `SettingsDialog` (v1.7.0) has an active `thema_combo` with
  "Donker"/"Licht" (resp. "Dark"/"Light"), and
  `_widgets_naar_instellingen` uses `normaliseer_thema()` as a safety
  net. New i18n keys `thema_licht` and updated `thema_tooltip` (NL +
  EN). `tests/test_settings.py` (v1.5.0, +6) and
  `tests/test_settings_dialog.py` (v1.4.0, +6).
- **11H.3 — Theme parameter on ToolHubWindow + live switch.**
  `ToolHubWindow` gains a `theme` parameter (wins over
  `settings.json`, analogous to language). `_apply_settings` detects a
  theme switch and applies it immediately. `main.py` (v1.6.0) reads
  `algemeen.thema` and calls `apply_theme(app, thema)`. Since v2.22.0
  the window manages its own stylesheet (`self.setStyleSheet(...)`)
  instead of the `QApplication`: that fixes a structural performance
  problem. New `conftest.py` (v1.1.0) with autouse cleanup fixture.
  `tests/test_theme_switch.py` (new, 10 tests).
  **Performance fix in v2.22.0:** the unconditional
  `QApplication.setStyleSheet` in `ToolHubWindow` cost 50–170 seconds
  per test in the suite. `_apply_theme_if_needed()` skips the expensive
  call if the stylesheet is already correct, and the window uses
  `self.setStyleSheet()` instead of `QApplication.setStyleSheet()`.
  Together with the `conftest.py` fixture, the suite went from 53 min
  back to ~3 min.
- **11H.4 — Chart colours per theme in AnalysisScreen.**
  `analysis_screen.py` (v1.7.0) gains a keyword-only `theme` parameter
  and a module-level `CHART_COLORS` dict with all previously hardcoded
  chart colours per theme (chart background, axis labels, grid, line,
  scatter border, neutral scatter, state label). New
  `apply_theme(theme)` method applies the colours without clearing the
  series. `main_window.py` (v2.22.1) passes `theme` to
  `AnalysisScreen` and calls `apply_theme` on a theme switch.
  `tests/test_analysis_screen_theme.py` (new, 11 tests).
- **11H.5 — Detail HTML and release notes per theme.**
  `history_screen.py` (v1.18.0) gains a keyword-only `theme` parameter
  and a module-level `DETAIL_HTML_COLORS` dict with per-theme detail
  HTML colours (background, text, heading, muted, table border, state
  label). New `apply_theme(theme)` method. `_show_detail_dialog` uses
  the per-theme `QTextBrowser` stylesheet; the `state_label` colour
  follows the theme. `main_window.py` (v2.22.2) passes `theme` to
  `HistoryScreen`, calls `apply_theme` on a theme switch, and makes
  `_toon_release_notes_dialoog` theme-dependent. `_markdown_naar_html`
  gains optional `body_bg`/`body_fg` parameters (default dark,
  backward-compatible). `tests/test_history_screen_theme.py` (new, 11
  tests).

**Important observation: test count**

In 11H.1 through 11H.5 my own estimates sometimes deviated from the
actual counts. The actual counts via `pytest --collect-only -q` per
file and the full `pytest -q` were consistent. The sum of the targeted
`--collect-only` was compared with the full suite in every sub-phase.

**For developers**

- **Changed:** `app/gui/styles.py` (v1.6.0 → v1.7.0) —
  `LIGHT_THEME_STYLESHEET`, `THEME_STYLESHEETS`,
  `apply_theme(app, thema)`; `apply_dark_theme` remains as a wrapper.
- **Changed:** `app/config/settings.py` (v1.7.0 → v1.8.0) —
  `TOEGESTANE_THEMAS`, `STANDAARD_THEMA`, `normaliseer_thema()`,
  normalisation in `laad_instellingen()`.
- **Changed:** `app/gui/dialogs/settings_dialog.py` (v1.6.0 → v1.7.0)
  — active `thema_combo`, `normaliseer_thema()` as a safety net.
- **Changed:** `app/gui/main_window.py` (v2.20.0 → v2.22.2) — `theme`
  parameter, `_apply_theme_if_needed()`, `self.setStyleSheet()`
  instead of `QApplication.setStyleSheet()`, passing `theme` to
  `AnalysisScreen` and `HistoryScreen`, theme-dependent
  release-notes dialog.
- **Changed:** `main.py` (v1.5.0 → v1.6.0) — `laad_instellingen()`
  before theme application; `apply_theme(app, thema)` instead of
  `apply_dark_theme(app)`.
- **Changed:** `app/gui/analysis_screen.py` (v1.6.3 → v1.7.0) —
  `theme` parameter, `CHART_COLORS`, `apply_theme()`, all chart
  colours per theme.
- **Changed:** `app/gui/history_screen.py` (v1.17.1 → v1.18.0) —
  `theme` parameter, `DETAIL_HTML_COLORS`, `apply_theme()`, detail
  HTML per theme.
- **New:** `conftest.py` (v1.1.0) — autouse cleanup fixture.
- **New tests:** `tests/test_theme_switch.py` (10 tests),
  `tests/test_analysis_screen_theme.py` (11 tests),
  `tests/test_history_screen_theme.py` (11 tests).
- **Changed tests:** `tests/test_styles.py` (v1.2.0 → v1.3.0,
  12 → 20 tests), `tests/test_settings.py` (v1.4.0 → v1.5.0,
  17 → 23 tests), `tests/test_settings_dialog.py` (v1.3.0 → v1.4.0,
  18 → 24 tests).
- **New i18n keys:** `settings.algemeen.thema_licht`, updated
  `settings.algemeen.thema_tooltip` (NL + EN).
- **Baseline:** 1494 → **1546 passed** (+52 tests across 11H.1 to
  11H.5).

### Phase 11G — Dark theme visuals (20 October 2026)

**Motivation**

Five visual points from earlier sessions were still open: checkbox
and radio focus were invisible in the dark theme, the scrollbar in
the Word summary of the import wizard was light, the Analysis page
had no readable tick format, no zoom/pan and no clickable data
points. In addition, the menu option "Exit" on a subpage only closed
the window instead of the application.

**Solution: seven sub-phases**

- **11G.1 — Checkbox and radio visibility.** `styles.py` (v1.4.0)
  gains `QCheckBox::indicator:focus`, `QRadioButton::indicator:focus`,
  `QTableView::indicator`, `QGroupBox::indicator` and
  `QComboBox::drop-down:hover`. New pure tests in
  `tests/test_styles.py` (v1.0.0).
- **11G.2 — Dark scrollbar.** `styles.py` (v1.5.0) gains
  `QScrollBar:vertical` and `QScrollBar:horizontal` with dark track,
  grey handle, hover/pressed states, and disabled arrow buttons.
  `tests/test_styles.py` (v1.1.0) gains three scrollbar tests.
- **11G.3 — Axis scaling and tick format.** `analysis_screen.py`
  (v1.4.0) gives `QValueAxis` an explicit `labelFormat` per chart
  type and a 5% margin on the y-axis. `QDateTimeAxis` gets an
  adaptive format. `test_analysis_screen.py` (v1.4.0) gains five
  tests.
- **11G.4 — Zoom/pan.** `analysis_screen.py` (v1.5.0) sets
  `QChartView.RubberBand.RectangleRubberBand`, adds a `wheelEvent`
  override for Ctrl+wheel zoom, a `reset_zoom_btn` with Ctrl+0, and
  a `refresh()` that resets the zoom. New i18n keys
  `analyse.zoom.reset_knop` and `analyse.zoom.reset_tooltip` (NL +
  EN). `test_analysis_screen.py` (v1.5.0) gains five tests.
  **Fix in v1.5.1:** `QChartView.RubberBand.Rectangle` does not
  exist; the correct constant is `RectangleRubberBand`.
- **11G.5 — Clickable data points + selection-driven analysis.** The
  existing `export_scope_combo` now also drives the chart scope.
  Labels come from `analyse.scope.*` (NL + EN). At scope SELECTED
  with ≥1 checked measurement, the GUI passes `measurement_ids=[...]`
  to the service. `AnalysisService` (v1.1.0) gains an optional
  `measurement_ids` parameter. In `_draw_scatter` each
  `QScatterSeries` gets a `clicked` connection.
  `test_analysis_screen.py` (v1.6.0) gains six tests,
  `test_analysis_service.py` (v1.1.0) two.
  **Fix in v1.6.1–v1.6.3:** `refresh(preserve_selection=True)`
  preserves the selection at scope SELECTED; the "Selection cleared"
  message returns on a normal refresh; `_category_label` and
  `_category_color` had accidentally disappeared and are restored.
  `test_analysis_screen_nan.py` (v1.0.4) and
  `test_main_window_report_menu.py` (v1.4.1) gain the new
  `measurement_ids` parameter on their stubs.
- **11G.6 — Explicit exit closes the app.** `main_window.py`
  (v2.20.0) gains a `_force_close` flag and a `_sluit_app()` method.
  Menu "Exit" (Ctrl+Q) and the confirmation dialog on the hub use
  `_sluit_app()`. `closeEvent` accepts the event if `_force_close`
  is True; otherwise the contextual "back to hub" behaviour for the
  window-X on a subpage remains. `test_navigation_regressions.py`
  (v1.2.0) gains five tests.
- **11G.7 — Filter checkbox visibility.** `styles.py` (v1.6.0) gives
  `QGroupBox::indicator` a lighter background (`#3C3C3C`) and a
  thicker border (2px `#B0B0B0`) in unchecked state. Checked state
  is blue (`#0078D7`) with a 2px border (`#4AA3FF`).
  `tests/test_styles.py` (v1.2.0, +3).

**For developers**

- **Changed:** `app/gui/styles.py` (v1.3.0 → v1.6.0) — focus states,
  table indicator, groupbox indicator, combobox hover, dark
  scrollbar, clearer groupbox checkbox.
- **Changed:** `app/gui/analysis_screen.py` (v1.3.0 → v1.6.3) — axis
  scaling, tick format, zoom/pan, clickable scatter points,
  selection-driven scope.
- **Changed:** `app/services/analysis_service.py` (v1.0.0 → v1.1.0)
  — optional `measurement_ids` parameter.
- **Changed:** `app/gui/main_window.py` (v2.19.1 → v2.20.0) —
  `_force_close`, `_sluit_app()`, `closeEvent` update.
- **Changed:** `tests/test_styles.py` (v1.2.0, 12 tests).
- **Changed:** `tests/test_analysis_screen.py` (v1.3.1 → v1.6.2,
  30 → 46 tests), `tests/test_analysis_screen_nan.py`
  (v1.0.3 → v1.0.4, 6 tests), `tests/test_analysis_service.py`
  (v1.0.0 → v1.1.0, 7 → 9 tests),
  `tests/test_main_window_report_menu.py` (v1.4.0 → v1.4.1),
  `tests/test_navigation_regressions.py` (v1.1.0 → v1.2.0,
  5 → 10 tests).
- **New i18n keys:** `analyse.zoom.reset_knop`,
  `analyse.zoom.reset_tooltip`, `analyse.scope.selectie`,
  `analyse.scope.filters`, `analyse.scope.tooltip` (NL + EN).
- **Baseline:** 1462 → **1494 passed** (+32 tests across 11G.1 to
  11G.7).

### Phase 11F — Documentation extension (20 October 2026)

**Motivation**

The documentation library had four practical limitations: there was
no place to record why an import was archived, the "Show archived"
checkbox was an all-or-nothing switch, you could only edit or change
the status of one import at a time, and `EditMetadataDialog` accepted
only ISO dates as an existing `document_date`. In addition, two
cosmetic points (§4.21, §4.23) were still open, and there were some
unused i18n keys.

**Solution: four sub-phases**

- **11F.1 — Archive reason.** `ImportService.archive(source_id, *,
  reason=None)` in `import_service.py` (v1.5.0). `ImportSource` gains
  `archive_reason` (v1.4.0), backward-compatible. `revoke` keeps the
  reason; `replace_source` and `update_metadata` leave the field
  untouched. `ChangeStatusDialog` (v1.2.0) shows an optional reason
  field when archiving. `DocumentationScreen` (v2.4.0) shows the
  reason as a tooltip on the Status column for an archived user
  import.
- **11F.2 — Status filter.** `DocumentationScreen` (v2.5.0) replaces
  the "Show archived" checkbox with a `status_filter_combo` with four
  options (All / Draft / Active / Archived). The GUI filters on
  `import_status` after fetching from the service. New i18n keys under
  `documentatie.status_filter.*`; the old
  `documentatie.toon_gearchiveerd(_tooltip)` are removed.
- **11F.3 — Bulk edit and bulk status change.** Two new dialogs:
  `BulkEditMetadataDialog` (v1.0.0) with a checkbox per field, and
  `BulkChangeStatusDialog` (v1.0.0) with a fixed target status choice
  and an optional reason when archiving. `DocumentationScreen` (v2.6.0)
  is on `ExtendedSelection` with two new buttons "Bulk edit…" and
  "Bulk status…". New i18n keys under `documentatie.bulk_edit.*`,
  `documentatie.bulk_status.*` and `documentatie.bulk_resultaat.*`.
- **11F.4 — Date parsing + cosmetic points + i18n cleanup.**
  `EditMetadataDialog` (v1.2.0) has a new pure helper
  `_parse_datum_naar_qdate` that accepts, besides `yyyy-MM-dd`, also
  `yyyy/MM/dd`, `dd-MM-yyyy`, `yyyy-MM` (day 1) and `yyyy` (1
  January). §4.21 resolved: `test_icon_paths.py` (v1.1.0) uses the
  project-wide `_app()` helper. §4.23 resolved: `_fake_translate` in
  `test_gui_language_switch.py` (v1.3.1) does real format
  substitution where the key contains `{placeholders}`. i18n cleanup:
  unused keys `dialog.documentatie_placeholder` and
  `documentatie.info.ondersteunt` removed from NL and EN.

**For developers**

- **Changed:** `app/gui/documentation_screen.py` (v2.4.0 → v2.6.0) —
  status filter dropdown, `ExtendedSelection`, two bulk buttons.
- **Changed:** `app/gui/dialogs/edit_metadata_dialog.py`
  (v1.1.0 → v1.2.0) — `_parse_datum_naar_qdate` with fallback chain.
- **New:** `app/gui/dialogs/bulk_edit_metadata_dialog.py` (v1.0.0).
- **New:** `app/gui/dialogs/bulk_change_status_dialog.py` (v1.0.0).
- **New tests:** `tests/test_bulk_edit_metadata_dialog.py` (11 tests),
  `tests/test_bulk_change_status_dialog.py` (10 tests), extension of
  `tests/test_documentation_screen.py` (55 → 63 tests), extension of
  `tests/test_edit_metadata_dialog.py` (22 → 34 tests).
- **Changed tests:** `tests/test_icon_paths.py` (v1.0.0 → v1.1.0),
  `tests/test_gui_language_switch.py` (v1.2.0 → v1.3.1).
- **New i18n keys:** `documentatie.status_kolom.gearchiveerd_met_reden`,
  `documentatie.status_wijzigen_reden.*`,
  `documentatie.status_filter.*`, `documentatie.bulk_edit.*`,
  `documentatie.bulk_status.*`, `documentatie.bulk_resultaat.*`.
- **Removed i18n keys:** `documentatie.toon_gearchiveerd`,
  `documentatie.toon_gearchiveerd_tooltip`,
  `dialog.documentatie_placeholder`, `documentatie.info.ondersteunt`.
- **Baseline:** 1395 → **1462 passed** (+67 tests across 11F.1 to
  11F.4).

### Phase 11E — Async network (16 October 2026)

**Motivation**

The update check, the release-notes fetch and the URL import in the
import wizard performed their network traffic **synchronously on the
GUI thread**. On a slow or unreachable server the GUI froze briefly.

**Solution: three sub-phases**

- **11E.1 — Async update check.** New module
  `app/helpers/async_worker.py` (v2.0.0) with a generic
  `AsyncWorker(QRunnable)` and `run_async()` helper.
  `app/helpers/updater.py` (v1.2.0) gains
  `check_for_update_async()` and `fetch_release_notes_async()`.
  `app/gui/main_window.py` (v2.18.0) uses those async variants.
- **11E.2 — Async URL fetch in the import wizard.**
  `app/documentation/url_fetch.py` (v1.2.0) gains
  `fetch_url_metadata_async()` and `fetch_url_content_async()`.
  `app/gui/dialogs/import_wizard_dialog.py` (v2.0.0) uses those
  async variants.
- **11E.3 — Force three-button message for QA.**
  `app/config/settings.py` (v1.7.0) gains `algemeen.qa_modus`.
  `app/gui/main_window.py` (v2.19.0) shows a hidden QA menu item in
  the Help menu when `qa_modus` is True.

**Important bugfix in 11E.1**

The first versions of `async_worker.py` failed with
`RuntimeError: Signal source has been deleted`. Cause: the
`WorkerSignals` was cleaned up before the emit had finished. The
final solution (v2.0.0): `WorkerSignals` as a strong Python attribute
on the `AsyncWorker`, `setAutoDelete(False)`, no registry. **The
caller is the owner** and must keep the return value. In the GUI,
`main_window.py` does so via `self._update_check_worker` and
`self._release_notes_worker`; in the wizard via
`self._url_fetch_worker` and `self._import_worker`. In tests via
`_bewaarde_workers`.

**Small bugfix in 11E.3**

`app/gui/main_window.py` (v2.19.1) uses a double `getattr` in
`_build_menu()` and `_apply_settings()`, so that a test or an older
`settings.json` without an `algemeen` namespace does not raise an
`AttributeError`.

**For developers**

- **New:** `app/helpers/async_worker.py` (v2.0.0).
- **Changed:** `app/helpers/updater.py` (v1.2.0) — async variants.
- **Changed:** `app/documentation/url_fetch.py` (v1.2.0) — async
  variants.
- **Changed:** `app/gui/main_window.py` (v2.19.1).
- **Changed:** `app/gui/dialogs/import_wizard_dialog.py` (v2.0.0).
- **Changed:** `app/config/settings.py` (v1.7.0) — `qa_modus`.
- **New tests:** `tests/test_async_worker.py` (9 tests), extension
  of `tests/test_updater.py` (+4 async tests),
  `tests/test_startup_update_check.py` (rewritten for async),
  `tests/test_main_window_update_menu.py` (v1.3.0, +3 QA tests),
  `tests/test_documentation_url_fetch.py` (v1.1.0, +6 async tests),
  `tests/test_import_wizard_dialog.py` (v1.8.0, +3 async tests).
- **New i18n keys:** `documentatie.import.bezig_metadata`,
  `documentatie.import.bezig_import`, `menu.qa_toon_update_melding`.
- **Baseline:** 1366 → **1395 passed** (+29 tests).

### Phase 11D — Resolving i18n mixing (16 October 2026)

**Motivation**

After a live language switch, the ESR screen showed a mixture of
languages: the GUI chrome switched correctly, but the
already-translated strings from the `Beoordeling` object remained in
the old language. In addition, the `*` annotation for a frequency
difference was hardcoded in the GUI.

**Solution**

- `Beoordeling` gains a `taal` field populated by
  `beoordeel_meting`. The GUI can detect a language mismatch.
- After a live language switch, the ESR screen shows a clear banner
  in the GUI language. The already-translated result strings remain
  in their own language; no silent mixing.
- `_show_result` and `_build_result_html` translate all
  result-specific labels in `resultaat.taal`.
- The `*` annotation for a frequency difference now goes through two
  new i18n keys in NL and EN.
- Bugfix in `apply_language`: the condition `result_group.isVisible()`
  is replaced by `_laatste_resultaat is not None`.

**For developers**

- `app/services/assessment_service.py` (v1.6.0) — `Beoordeling` has
  the extra field `taal: str = STANDAARD_TAAL`.
- `app/gui/esr_test_screen.py` (v1.14.0) — `_show_result` detects a
  language mismatch and shows `result_language_banner`. New helper
  `_t_voor(taal, sleutel, **kwargs)`.
- New i18n keys under `resultaat`: `taal_mismatch_banner`,
  `esr_factor_frequentie_indicatief`,
  `esr_factor_frequentie_indicatief_kort` (NL + EN).
- `tests/test_assessment.py` (v1.5.1) — 5 new tests.
- `tests/test_gui_language_switch.py` (v1.2.0) — 3 new tests.
- **Baseline:** 1358 → **1366 passed** (+8 tests).

## Version 1.2.0 — Frequency-specific references and threshold validation (15 October 2026)

**ESR references per measurement frequency**

The ESR reference is now **frequency-specific**. Instead of one
official ESR70 table at 100 kHz used for all measurements, the
application now picks the reference profile closest to the actual
measurement frequency.

- **Official ESR70 table** — 100 kHz. Remains the primary source for
  100 kHz measurements.
- **Estimated profiles** — 100 Hz, 1 kHz and 10 kHz, derived from the
  official ESR70 table via the Nichicon frequency coefficients
  (×2.00 / ×1.50 / ×1.15). Explicitly marked as an **estimate**
  (`is_schatting: true`) with a lower reliability level.

**Why this change**

The LCR-ST1 measures at 1 kHz and 10 kHz. The official ESR70 table
applies to 100 kHz. Because ESR falls with frequency, the comparison
was structurally too strict.

**Validated against 72 field measurements**

For good capacitors, the factors dropped to **0.09–0.41** — a healthy
distribution. The thresholds `≤1.0 / ≤2.0 / ≤3.0` remain unchanged.

**Visible in the result**

The result now explicitly shows the **reference frequency** used for
the comparison.

**For developers**

- `app/data/references/esr_references.json` — new profiles
  `algemeen_100hz_geschat`, `algemeen_1khz_geschat`,
  `algemeen_10khz_geschat`.
- `app/data/references/__init__.py` — `zoek_referentie()` accepts
  `meetfrequentie_hz`.
- `app/services/assessment_service.py` — `Beoordeling` has the field
  `referentiefrequentie_hz`.
- New i18n key: `resultaat.referentiefrequentie` (NL + EN).
- New analysis script: `scripts/herbereken_steekproef.py`.

### UX polish (phase 11A, 16 October 2026)

**Export now respects the selection**

In **History** and **Analysis** you can use a scope dropdown to choose
what to export: **current filters** or **selection**.

**Selection and report in the Analysis page**

The **Analysis** page has a compact selection list below the chart
with **Export…** and **Create report…**.

**Report with scope "selection"**

The measurement report now supports a report over **multiple
measurements**.

**Menu "Create report…" is disabled without a selection**

In the **File** menu, the item **Create report…** is now disabled
while no measurement is selected.

**Folder preferences are respected everywhere**

A new pure helper (`app/helpers/dialog_start_directory.py`)
determines the best start folder for every `QFileDialog`.

**For developers**

- `app/gui/analysis_screen.py` — compact selection list, scope
  dropdown, export button and `report_btn`.
- `app/gui/history_screen.py` — `selection_changed` signal.
- `app/gui/main_window.py` — `_open_report_dialog()`.
- `app/gui/dialogs/report_dialog.py` — `for_measurements(...)`.
- **New:** `app/helpers/dialog_start_directory.py` (v1.0.0).
- New i18n keys: 24 under `analyse.selectie.*`, `analyse.export.*`,
  `analyse.rapport.*` and `menu.rapport_tooltip` (NL + EN).
- Baseline: **1339 passed** (was 1329 before 11A).

### Reliability rule revised (phase 11B, 16 October 2026)

**Solution: substantive vs. administrative**

There is now a distinction between **substantive** and
**administrative** reliability reducers. Substantive reducers raise
the minimum of the final status; administrative reducers lower the
reliability but do not raise the minimum. "Probably good, low
reliability due to administrative factors" is now possible.

**For developers**

- `app/services/assessment_service.py` (v1.5.0) —
  `BetrouwbaarheidsResultaat` has `inhoudelijke_verlagers`.
- New i18n keys: `betrouwbaarheid_factor.categorie_inhoudelijk`,
  `betrouwbaarheid_factor.categorie_administratief`,
  `eindstatus_reden.betrouwbaarheid_laag_administratief`,
  `resultaat.inhoudelijke_verlagers`,
  `resultaat.administratieve_verlagers` (NL + EN).
- `tests/test_assessment.py` (v1.5.0) — 10 new tests.
- **Baseline:** 1329 → **1339 passed** (+10 tests).

### Icons for all windows (phase 11C, 16 October 2026)

**One application icon, twelve thematic icons**

The application now has a complete icon set:
`assets/icons/app.png`, `assets/icons/logo.ico` and twelve thematic
icons. The current icons are **placeholders** generated by a script
(`scripts/genereer_placeholders.py`).

**For developers**

- **New:** `app/helpers/icon_paths.py` (v1.0.0).
- **New:** `scripts/genereer_placeholders.py` (v1.0.0).
- **Changed:** `main.py` (v1.5.0), `app/gui/main_window.py` (v2.17.0),
  all dialogs in `app/gui/dialogs/`,
  `app/gui/esr_test_screen.py` (v1.13.0).
- **New:** `tests/test_icon_paths.py` (16 tests),
  `tests/test_main_icon.py` (1 test).
- **Extended:** `tests/test_main_window_help_menu.py` and
  `tests/test_main_window_report_menu.py` (1 test each).
- **Baseline:** 1339 → **1358 passed** (+19 tests).

## Version 1.1.1 — Update check at startup and via Help (15 October 2026)

**Automatic check for a newer version**

At startup, the application checks once, without blocking, whether a
newer version is available on GitHub.

**Manual check via Help**

You can also run the check manually via
**Help → Check for updates…**.

**What's new?**

If a newer version is available, the message also shows a
**What's new?** button with the release notes from the GitHub
release.

**Setting: check for updates at startup**

In **Settings → General** there is a new checkbox
**Check for updates at startup** (on by default).

**Multilingual changelog**

The changelog is now available per language: `docs/changelog/nl_NL.md`
and `docs/changelog/en_US.md`.

**For developers**

- New module `app/helpers/updater.py`.
- New resolver `changelog_pad_voor_taal()` in
  `app/helpers/help_paths.py`.
- New i18n keys under `update.*` and
  `settings.algemeen.controleer_updates` (NL + EN).
- New setting `algemeen.controleer_updates_bij_opstarten` (default
  `True`), backward-compatible.

## Version 1.0.3 — Publication, test matrix and bug/feature reports (14 October 2026)

**The application is now publicly available on GitHub**

On 13 October 2026 the first public release **v1.0.3** appeared in the
repo `barremans/capacitor_esr_validator`.

**Build pipeline extended with `publish.ps1` and `build_and_publish.ps1`**

- **`publish.ps1`** — publishes the installer to GitHub, with a
  **release gate** on the Authenticode signature.
- **`build_and_publish.ps1`** — orchestrator that runs the whole chain.

**Intune/Defender test matrix**

The installer has been proven on two types of Windows PCs: a regular
PC (SmartScreen warning, "More info → Run anyway" works) and an
Intune-managed PC (starts without a block thanks to a Defender
Certificate Indicator for the CGK certificate).

**Bug and feature reports from the application**

The main menu now has a **Report** menu with **🐞 Report a bug or
feature…** and **Show open cases**. Reports go directly to the GitHub
repo via the REST API.

**For developers**

- The feedback package (`github_feedback.py`, `bug_report_dialog.py`,
  `github_cases.py`, `check_github_secret.py`) is identical in the
  project root.
- The GitHub token lives in `github_secret_local.py`, which is in
  `.gitignore` and never goes to GitHub.
- New i18n keys: `menu.rapporteren`, `menu.bug_melden`,
  `menu.open_cases` (NL + EN).

**Fixed**

- `LF/CRLF` warning on `releases/latest/version.txt` via
  `.gitattributes`.
- `ESR_Tester.spec` is no longer in `.gitignore`.

**Documentation**

- `docs/packaging.md` — build flow, signing, distribution, checklist.
- `docs/testmatrix_defender_intune.md` — the full test matrix.

## Version 1.0.2 — First Windows build, installer and signing (13 October 2026)

**The application now has a real version**

Central version in `app/version.py`, shown in Help → About.

**Full Windows build pipeline**

- **`ESR_Tester.spec`** — PyInstaller spec.
- **`build_installer.bat`** — builds the EXE, generates
  `dist\installer.iss`, compiles with Inno Setup 6, and signs.
- **`bump_version.py`** — bumps patch, minor or major.
- **`build_and_publish.ps1`** — orchestrator with signing preflight.
- **`publish.ps1`** — publishes to GitHub with a release gate.

**Code signing**

The EXE and the installer are signed with the CGK certificate
(`CN=CGK Local Signing`, valid until 2028-09-17).

**Installer with icon**

The installer now has the ESR Tester icon in the wizard and in the
shortcuts. After installation, the app starts with user rights.

**Fixed**

- Window titles of the Help and Changelog windows showed untranslated
  keys.
- The ESR test button in the Diagnostics page showed `tool.esr`.
- The build pipeline aborted with `: was unexpected at this time.`
  due to a `set /p` prompt with parentheses.

**PDFs with readable text, without a manual step**

The application now automatically sets
`QT_QPA_FONTDIR=C:\Windows\Fonts` on Windows.

**For developers**

- `numpy` pin `>=1.26,<3`, `pandas` pin `>=2.2,<3`.
- `QT_QPA_FONTDIR` is set in `main.py` before `QApplication`.
- `app/version.py` is the central version source.

## Version 1.0.1 — Measurement reports and extended settings (12 October 2026)

**Creating measurement reports**

From any stored measurement you can create a **measurement report**
(HTML or PDF) with component identification, measurement context, raw
measurement values, assessment snapshots, reference snapshots and an
optional chart.

**New in the Reporting settings**

- **Author** — optional free field in the report header.
- **Default report folder** — automatically updated after each save.

**Automatically open the folder**

After saving a report, the folder is automatically opened (if the
setting is on).

**Read-only**

The report is built from the stored snapshots. Historical measurements
and assessments are never recalculated.

**Fixed**

- `algemeen.ja` and `algemeen.nee` appeared as untranslated keys; now
  `app.ja` and `app.nee`.
- Status labels in the report were shown as raw codes; now translated.

## Version 1.0.0 — Charts and trends (9 October 2026)

**New "Analysis" page**

Next to Diagnostics, History and Documentation there is now a fourth
hub button **Analysis** with four chart types: ESR over time,
capacitance over time, D over time, and ESR vs. capacitance.

**Filter on exactly the same fields as the history**

The filter bar uses the same fields as the history page.

**Aggregation per day, week or month**

With a second dropdown you choose average per day, per week or per
month.

**Read-only**

The Analysis page reads your stored measurements and writes nothing
back.

**Keyboard shortcuts**

- **Ctrl+A** opens the Analysis page.
- **Ctrl+R** refreshes the data.
- **Ctrl+F** opens the filter panel.
- **Esc** returns to the Main menu.

---

<!--
From here on: early development phases. The numbering is historical and
does not always map 1-to-1 to `app/version.py`. These entries remain as
functional milestones.
-->

## Version 0.9 — Manufacturer documents: Word and Excel (9 October 2026)

**Word and Excel import**

Besides PDF and URL, you can now also import **Word documents (.docx)**
and **Excel workbooks (.xlsx)** as documentation sources. The import
wizard has four choices.

**Old formats are rejected**

The old `.doc` format (Word 97-2003) and `.xls` format (Excel 97-2003)
are not supported.

## Version 0.8 — Managing the status of your own imports (8 October 2026)

**Changing the status of an import**

In the documentation library there is now a **Change status…** button
for your own imports.

**New Status column**

The documentation table now has an extra **Status** column.

## Version 0.7 — Metadata on import and editing in the viewer (7 October 2026)

**Metadata when importing a PDF or URL**

When importing a document you can now immediately fill in metadata.

**Editing metadata in the documentation library**

In the documentation library there is now an **Edit…** button.

**Improved search**

The search field in the documentation library now also searches the
metadata of imported documents.

## Version 0.6 — Per-language Help and clearer search explanation (6 October 2026)

**New**
- **Per-language Help.**
- **Clearer explanation about exclusion in the search help.**

## Version 0.5 — Keyboard shortcuts and safer exit (5 October 2026)

**New**
- You can now work with the keyboard throughout the application.

## Version 0.4 — Smarter searching and help in the documentation (5 October 2026)

**New**
- **Search language for documentation.**
- **Help with searching.**

## Version 0.3 — Multiple diagnostic tools in one hub (3 October 2026)

**New**
- Documents can now be linked to multiple diagnostic tools.

## Version 0.2 — Documentation library (3 October 2026)

**New**
- A central, multilingual documentation library with 8 technical
  documents.

## Version 0.1 — First working version (11 August 2026)

**New**
- First version of the ESR validator.

---

## Planned for future versions

- **Version 1.2.0 — UX/documentation polish.** All small points left
  over from earlier phases:
  - **11A** — Export, import and selection. **Completed on 16 October
    2026.**
  - **11B** — Reliability rule revised. **Completed on 16 October
    2026.**
  - **11C** — Icons for all windows. **Completed on 16 October 2026.**
  - **11D** — i18n mixing in Diagnostics/Result resolved. **Completed
    on 16 October 2026.**
  - **11E** — Async network. **Completed on 16 October 2026.**
  - **11F** — Documentation extension. **Completed on 20 October
    2026.**
  - **11G** — Dark theme visuals. **Completed on 20 October 2026.**
  - **11H** — Light theme. **Completed on 21 October 2026.**
  - **11I** — Build and cosmetics. **Completed on 22 October 2026.**
- **Version 1.3.0 — AI extraction from manufacturer documents.**
- **Version 1.4.0 — Human validation of AI output.**
- **Version 1.5.0 — Linking approved manufacturer data to
  assessment.**
- **Version 1.6.0 — Second diagnostic tool: Resistor.**

---

_Historical numbering: the entries 0.1 through 0.9 describe the early
development period. The numbering is functional, not 1-to-1 linked to
`app/version.py`. From v1.1.1 onwards, the version numbers match the
actual releases._