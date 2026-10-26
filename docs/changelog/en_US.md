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

### Chat 5 — Analysis: Y-axis, X-axis and readability (26 October 2026)

**Why this change**

The Analysis page had two persistent visual problems that made the
charts unreadable: the Y-axis was completely stretched by a single
extreme measurement (master plan C2, part 1), and the X-axis showed
literally "..." on every tick for log-distributed data (master plan
C2, part 2). Both have been fixed with pure, testable helpers.

**Solution: two sub-phases**

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

**Important observation**

During 5B it turned out that a `NameError` in a test often points to a
missing import in the test file, not to a missing function in the
production code. The helper was present in `chart_axis.py`, but the
import was missing in `test_chart_axis.py`. Lesson: on a `NameError`,
always check the imports first.

**For developers**

- **New:** `app/helpers/chart_axis.py` (v1.1.1) — `bereken_y_as_range`
  and `bereken_x_as_ticks`.
- **Changed:** `app/gui/analysis_screen.py` (v1.7.2 → **v1.9.0**) —
  Y-axis clamping, X-axis ticks, `state_label` indicator.
- **Changed:** `app/helpers/report_chart.py` (v1.0.3 → **v1.2.0**) —
  the same helpers in both render functions.
- **New i18n key:** `analyse.outliers_verborgen` (NL + EN).
- **New tests:** `tests/test_chart_axis.py` (v1.1.0, 12 tests).
- **Extended:** `tests/test_analysis_screen.py` (v1.6.2 → v1.8.0,
  +6 tests), `tests/test_report_chart.py` (v1.0.0 → v1.2.0, +3 tests).
- **Baseline:** 1766 → **1787 passed** (+21 tests across 5A and 5B).

### Chat 4 — Assessment, schema v4 and type matching (26 October 2026)

**Why this change**

Three substantive points from the master plan were still open: B1
(EX_SITU reliability), B2 (physically impossible values), OV-S4
(scalar fields not type-validated) and B3/OL status (schema v4), plus
B4 (type matching §14). The chat was split into three sub-phases:
4A (assessment sanity checks), 4B (OL status and schema v4) and 4C
(type matching §14).

**Total:** +48 tests. Baseline **1718 → 1766 passed**.

#### 4A — Assessment sanity checks (2026-10-26, +21 tests)

- **B1-a:** `assessment_service.bepaal_betrouwbaarheid` used an exact
  string match `condensatortype != "Aluminium elektrolytisch"`. Valid
  variants from `CONDENSATORTYPES` ("Low ESR", "Bipolar/NP") were
  therefore booked as "type unknown", with an unwarranted drop in
  reliability and final status. Fix: new pure helper
  `is_elektrolytisch_type` (later moved to
  `app/helpers/technology.py` in 4C).
- **B2:** `beoordeel_esr` and `beoordeel_capaciteit` had no physical
  plausibility check. Fix: two new configurable sanity thresholds in
  `BeoordelingsInstellingen`.
- **OV-S4:** `meetfrequentie_hz="hoog"` was stored as a string. Fix:
  new pure helper `valideer_en_normaliseer` in `settings.py`.

#### 4B — OL status and schema v4 (2026-10-26, +17 tests)

- **B3:** schema v3 → v4. New column `meetstatus` on `measurements`
  (TEXT NOT NULL DEFAULT 'NORMAL', CHECK on
  NORMAL/OL/UNDER_RANGE/OVER_RANGE/UNKNOWN), plus index
  `ix_measurements_meetstatus`. Existing measurements get NORMAL.
- **Migration v3 → v4:** `_migrate_v3_to_v4` in `migrations.py`.
- **Model:** new enum `Meetstatus`.
- **Service:** `create_measurement(meetstatus=...)`.
- **GUI:** new private helper `_meetstatus_voor_opslag()`.

#### 4C — Type matching §14 (2026-10-26, +10 tests)

- **B4:** `zoek_referentie` used a default
  `condensatortype="Aluminium elektrolytisch"` and filtered on exact
  string equality. Fix: new shared helper module
  `app/helpers/technology.py` with `is_elektrolytisch_type`,
  `technologie_familie` and `zelfde_technologie_familie`.
  `zoek_referentie` explicitly blocks non-electrolytic types.

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
  overwrote the first (on `selected_measurement_ids`). Fix: new
  private helper `_bepaal_default_scope()` with an explicit priority —
  selection > filters > selection-as-fallback.
  `exchange_dialog.py` v1.0.1 → v1.0.2. New tests: 3 in
  `tests/test_exchange_dialog.py` (v1.0.1 → v1.0.2). Baseline
  1715 → **1718**.

**Important observation**

The typo from 3A had already been mentioned in `overdracht.md` §2.2
since §2.28 as "important bugfix in §2.28", but the code in
`main_window.py` v2.23.0 still contained it. Documentation and code
had drifted apart. Lesson: with every handover, check whether the
mentioned bugfixes are actually present in the supplied files.

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
  `app/services/exchange/models.py` (v1.0.0).
- **28B — Export service.** `app/services/exchange/export_service.py`
  (v1.0.1).
- **28C — Import planner.** `app/services/exchange/import_planner.py`
  (v1.0.0).
- **28E — Schema migration v2 → v3.** Two new columns on
  `measurements`.
- **28D — Import service.** `app/services/exchange/import_service.py`
  (v1.0.0).
- **28F — GUI integration.** New `exchange_dialog.py` (v1.0.1),
  two new menu items.

**Important design decisions**

- **JSON envelope, not SQLite dump.**
- **Origin tracking via schema migration v3.**
- **Natural key = content.**
- **Conflict copy is the default.**
- **Race check before each write.**
- **Per-chain transactions.**

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