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

### Chat 5 — Analysis: comparison mode, Y-axis, X-axis and selection (26–27 October 2026)

**Why this change**

The Analysis page had four problems: the Y-axis was completely
stretched by a single extreme measurement (master plan C2, part 1),
the X-axis showed literally "..." on every tick for log-distributed
data (master plan C2, part 2), checking a row in the selection table
did not update the chart at scope "Selection only" (master plan C2,
part 3), and there was no comparison mode to put multiple measurements
side by side (master plan C2, part 4). All four have been fixed with
pure, testable helpers and GUI changes.

**Solution: four sub-phases**

- **5A — Smart Y-axis clamping (outliers).** The Y-axis of the time
  series and the scatter plot was set directly to min/max. One
  measurement of 109,500 mΩ stretched the axis to −5,473…114,975 mΩ.
  New pure helper `bereken_y_as_range()` in
  `app/helpers/chart_axis.py` applies the Tukey fence (1.5 × IQR) and
  returns a readable range plus the number of hidden points.
  `AnalysisScreen` v1.8.0 and `report_chart` v1.1.0 use the same
  helper. `state_label` shows the new i18n key
  `analyse.outliers_verborgen`. Baseline 1766 → **1779** (+13).
- **5B — Readable X-axis labels.** The X-axis of the scatter plot used
  a fixed `QValueAxis` with 6 ticks and `%.0f`. At a range of
  0.1–1,160 µF, Qt could not produce readable labels and showed `...`.
  New pure helper `bereken_x_as_ticks()` in the same `chart_axis.py`
  adaptively chooses the number of ticks, the label format and the
  rotation (−45° for wide ranges). `AnalysisScreen` v1.9.0 and
  `report_chart` v1.2.0 use the same helper. Baseline
  1779 → **1787** (+8).
- **5C — Selection drives the chart at scope "Selection only".**
  Checking a row in the selection table did not update the chart at
  scope `SELECTED`; the user had to press "Refresh" or switch scope
  first. `AnalysisScreen._on_selection_item_changed` now calls
  `refresh(preserve_selection=True)` when the scope is `SELECTED`. At
  scope `FILTERED` the chart deliberately stays unchanged: the filters
  determine the chart, not the table selection. The duplicate
  `selection_changed.emit()` was removed because
  `_update_selection_count()` already emits. `AnalysisScreen`
  v1.9.0 → **v1.9.1**. Baseline 1787 → **1793** (+6).
- **5D — Comparison mode.** New chart type "Compare series". New
  dataclass `VergelijkReeks` and pure function
  `build_vergelijk_reeksen()` in `analysis_series.py` v1.1.0. New
  service method `vergelijken()` in `analysis_service.py` v1.2.0.
  New `_draw_vergelijk()` in `AnalysisScreen` v1.10.2: one
  `QLineSeries` per checked measurement with a fixed colour cycle
  (blue/orange/green/red/purple), max 5 series, Y-axis with the same
  5A clamping on all series together. At scope FILTERED or without a
  selection, a message is shown. Five new i18n keys under
  `analyse.vergelijk`. Baseline 1793 → **1795** (+2 measured; the
  three analysis files gained +18 tests, the suite as a whole +2).

**Important observations**

- **5B:** a `NameError` in a test often points to a missing import in
  the test file, not to a missing function in the production code.
  Always check the imports first.
- **5C (signal flow):** a GUI change that touches a signal flow can
  expose a double emit. `_on_selection_item_changed` and
  `_update_selection_count` both emitted `selection_changed`; that was
  harmless (idempotent) but sloppy. Cleaned up.
- **5C ("does not respond" can also be "deliberately does not
  respond"):** the open point OV-C5-8 ("at scope FILTERED the chart
  does not respond to table selection") turned out to be desired
  behaviour, not a bug. The fix is therefore "respond at SELECTED,
  deliberately not at FILTERED", now documented in the code and
  captured in a test.
- **5C (existing test with unrealistic state):** the old version of
  `test_analysis_report_met_selectie_blijft_for_measurements` placed
  a row manually in the selection table that did not come from the
  service. Since 5C, `setItem` triggers a refresh, and that refresh
  discards such a row. The test has been rewritten to follow the real
  GUI flow; a new test captures the deliberate behaviour. Lesson: a
  test that simulates an unrealistic state can break as soon as the
  production code validates more — rewrite the test, not the
  production code.
- **5D (selection source):** a `_draw_*` function that needs the
  selection must use the same source as `refresh()` itself —
  `_scope_measurement_ids()`, not `_selected_measurement_ids()`.
  During a `refresh(preserve_selection=True)` the selection table is
  temporarily empty. Fixed in v1.10.1.
- **5D (QtCharts and multiple series):** QtCharts does not reliably
  respect a `setRange()` on an axis with multiple series. If one
  series contains a point outside the range, Qt expands the axis.
  Fixed in v1.10.2: filter outliers out of the QLineSeries before
  adding them.
- **5D (Tukey fence with few points):** `bereken_y_as_range()` only
  applies the Tukey fence with 4 or more points. With 1–3 points the
  helper falls back to min/max + 5% margin. A test that wants to
  verify 5A clamping must therefore have at least 4 points in the
  series. Fixed in test v1.9.2.
- **5D (checking multiple rows in a test):** in a GUI test that checks
  multiple rows at scope SELECTED, each `setCheckState` triggers a
  refresh. Work row by row, by measurement id, with
  `QApplication.processEvents()` after each change.

**For developers**

- **New:** `app/helpers/chart_axis.py` (v1.1.1) — `bereken_y_as_range`
  and `bereken_x_as_ticks`.
- **New:** `app/helpers/analysis_series.py` v1.1.0 — `VergelijkReeks`
  and `build_vergelijk_reeksen`.
- **Changed:** `app/gui/analysis_screen.py` (v1.7.2 → **v1.10.2**) —
  Y-axis clamping, X-axis ticks, `state_label` indicator,
  selection-driven refresh at scope SELECTED, comparison mode.
- **Changed:** `app/services/analysis_service.py` (v1.1.0 → **v1.2.0**)
  — `vergelijken()`.
- **Changed:** `app/helpers/report_chart.py` (v1.0.3 → **v1.2.0**) —
  the same helpers in both render functions.
- **New i18n keys:** `analyse.outliers_verborgen`,
  `analyse.grafiektype.vergelijk`, `analyse.vergelijk.geen_selectie`,
  `analyse.vergelijk.te_veel_reeksen`,
  `analyse.vergelijk.alleen_bij_selectie`,
  `analyse.vergelijk.aantal_reeksen` (NL + EN).
- **New tests:** `tests/test_chart_axis.py` (v1.1.0, 12 tests),
  `tests/test_analysis_series.py` (v1.1.0, 4 tests).
- **Extended:** `tests/test_analysis_screen.py` (v1.6.2 → v1.9.2,
  +18 tests across 5A/5B/5C/5D), `tests/test_report_chart.py`
  (v1.0.0 → v1.2.0, +3 tests),
  `tests/test_analysis_service.py` (v1.1.0 → v1.2.0, +4 tests),
  `tests/test_main_window_report_menu.py` (v1.4.1 → v1.4.2, +1 test),
  `tests/test_report_dialog_scope_filters.py` (v1.0.1 → v1.0.2,
  1 test rewritten, +1 test).
- **Baseline:** 1766 → **1795 passed** (+29 tests across 5A, 5B, 5C
  and 5D; the suite as a whole 1795).

### Chat 4 — Assessment, schema v4 and type matching (26 October 2026)

See earlier version for the full text. Summary: assessment sanity
checks (B1/B2), OL status and schema v4 (B3), type matching §14 (B4).
+48 tests. Baseline **1718 → 1766 passed**.

### Chat 3 — Import wizard and exchange selection (26 October 2026)

See earlier version for the full text. Summary: typo in
`main_window._show_import_wizard()` fixed (A2), exchange selection
gets explicit priority (A4). Baseline 1711 → **1718**.

### Phase §2.28 — Export/import between devices (23 October 2026)

See earlier version for the full text. Summary: JSON envelope of
measurement chains, natural key on content, origin columns in schema
v3, import planner, import service, export service, and GUI
integration. +102 tests.

### Phase 11I — Build and cosmetics (22 October 2026)

See earlier version for the full text. Summary: pins documented,
`icon_path` via `sys._MEIPASS`, build orchestration cleaned up,
certificate store hygiene. Baseline 1546 → **1548**.

### Phase 11H — Light theme (21 October 2026)

See earlier version for the full text. Summary:
`LIGHT_THEME_STYLESHEET`, `apply_theme(app, thema)`, live theme switch,
chart colours per theme in `AnalysisScreen`, detail HTML per theme in
`HistoryScreen`. Baseline 1494 → **1546**.

### Phase 11G — Dark theme visuals (20 October 2026)

See earlier version for the full text. Summary: focus states, dark
scrollbar, axis scaling, zoom/pan, clickable data points,
selection-driven analysis, explicit exit, filter checkbox visibility.
Baseline 1462 → **1494**.

### Phase 11F — Documentation extension (20 October 2026)

See earlier version for the full text. Summary: archive reason, status
filter, bulk edit, date parsing, i18n cleanup. Baseline 1395 → **1462**.

### Phase 11E — Async network (16 October 2026)

See earlier version for the full text. Summary: `async_worker.py`,
async update check, async URL fetch, QA mode. Baseline 1366 → **1395**.

### Phase 11D — Resolving i18n mixing (16 October 2026)

See earlier version for the full text. Summary: `Beoordeling` gains a
`taal` field, banner on language mismatch, no silent mixing. Baseline
1358 → **1366**.

## Version 1.2.0 — Frequency-specific references and threshold validation (15 October 2026)

See earlier version for the full text. Summary: ESR reference is
frequency-specific, estimated profiles for 100 Hz/1 kHz/10 kHz,
validated against 72 field measurements.

### UX polish (phase 11A, 16 October 2026)

See earlier version for the full text. Summary: export respects the
selection, selection and report in the Analysis page, menu item
disabled without selection, folder preferences.

### Reliability rule revised (phase 11B, 16 October 2026)

See earlier version for the full text. Summary: distinction between
substantive and administrative reliability reducers.

### Icons for all windows (phase 11C, 16 October 2026)

See earlier version for the full text. Summary: one application icon,
twelve thematic icons.

## Version 1.1.1 — Update check at startup and via Help (15 October 2026)

See earlier version for the full text. Summary: automatic update check
at startup, manual check via Help, release notes in the message.

## Version 1.0.3 — Publication, test matrix and bug/feature reports (14 October 2026)

See earlier version for the full text. Summary: public release,
`publish.ps1`, Intune/Defender test matrix, Report menu.

## Version 1.0.2 — First Windows build, installer and signing (13 October 2026)

See earlier version for the full text. Summary: central version,
PyInstaller spec, installer, code signing, PDF fonts.

## Version 1.0.1 — Measurement reports and extended settings (12 October 2026)

See earlier version for the full text. Summary: measurement reports
(HTML/PDF), author, default report folder, automatically open folder.

## Version 1.0.0 — Charts and trends (9 October 2026)

See earlier version for the full text. Summary: new Analysis page with
four chart types, filter on the same fields as the history, aggregation
per day/week/month.

---

<!--
From here on: early development phases. The numbering is historical and
does not always map 1-to-1 to `app/version.py`. These entries remain as
functional milestones.
-->

## Version 0.9 — Manufacturer documents: Word and Excel (9 October 2026)

Word and Excel import added.

## Version 0.8 — Managing the status of your own imports (8 October 2026)

Change status for your own imports.

## Version 0.7 — Metadata on import and editing in the viewer (7 October 2026)

Metadata on import and editing in the viewer.

## Version 0.6 — Per-language Help and clearer search explanation (6 October 2026)

Per-language Help, clearer search explanation.

## Version 0.5 — Keyboard shortcuts and safer exit (5 October 2026)

Keyboard shortcuts throughout the application.

## Version 0.4 — Smarter searching and help in the documentation (5 October 2026)

Search language for documentation, help with searching.

## Version 0.3 — Multiple diagnostic tools in one hub (3 October 2026)

Documents can be linked to multiple tools.

## Version 0.2 — Documentation library (3 October 2026)

Central, multilingual documentation library.

## Version 0.1 — First working version (11 August 2026)

First version of the ESR validator.

---

## Planned for future versions

- **Version 1.2.0 — UX/documentation polish.** All small points left
  over from earlier phases. **Completed on 22 October 2026.**
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