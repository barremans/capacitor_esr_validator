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
  final releases. Those entries remain as functional milestones;
  they cannot be mapped 1-to-1 to a specific `app/version.py` value.
- For the current version: see `app/version.py` or Help → About.
-->

### Phase 11E — Async network (16 October 2026)

**Motivation**

The update check, the release-notes fetch and the URL import in the
import wizard performed their network traffic **synchronously on the
GUI thread**. On a slow or unreachable server the GUI froze briefly.
That was not functionally wrong, but it does not feel like a
diagnostic instrument.

**Solution: three sub-phases**

- **11E.1 — Async update check.** New module
  `app/helpers/async_worker.py` (v2.0.0) with a generic
  `AsyncWorker(QRunnable)` and `run_async()` helper, based on
  `QThreadPool`. `app/helpers/updater.py` (v1.2.0) gains
  `check_for_update_async()` and `fetch_release_notes_async()`.
  `app/gui/main_window.py` (v2.18.0) uses those async variants for
  the startup check and the manual check. The existing synchronous
  APIs remain unchanged for tests and non-GUI use.
- **11E.2 — Async URL fetch in the import wizard.**
  `app/documentation/url_fetch.py` (v1.2.0) gains
  `fetch_url_metadata_async()` and `fetch_url_content_async()`.
  `app/gui/dialogs/import_wizard_dialog.py` (v2.0.0) uses those
  async variants; while waiting, the buttons are disabled and the
  summary shows a "Busy…" text. New i18n keys:
  `documentatie.import.bezig_metadata` and
  `documentatie.import.bezig_import` (NL + EN).
- **11E.3 — Force three-button message for QA.**
  `app/config/settings.py` (v1.7.0) gains `algemeen.qa_modus`
  (default `False`). `app/gui/main_window.py` (v2.19.0) shows a
  hidden QA menu item in the Help menu when `qa_modus` is True.
  That item calls `_toon_update_melding_voor_qa()`, which passes a
  synthetic `UpdateInfo` (version 99.99.99) to the existing
  three-button message (Download / What's new? / Later). New i18n
  key: `menu.qa_toon_update_melding` (NL + EN).

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
`settings.json` without an `algemeen` namespace does not cause an
`AttributeError`.

**For developers**

- **New:** `app/helpers/async_worker.py` (v2.0.0) — generic
  `AsyncWorker` + `run_async()`. No network logic.
- **Changed:** `app/helpers/updater.py` (v1.2.0) — async variants
  added; synchronous APIs unchanged.
- **Changed:** `app/documentation/url_fetch.py` (v1.2.0) — async
  variants added; synchronous APIs unchanged.
- **Changed:** `app/gui/main_window.py` (v2.19.1) — async update
  check, QA mode, double `getattr` fix.
- **Changed:** `app/gui/dialogs/import_wizard_dialog.py` (v2.0.0)
  — async URL fetch and async URL import; PDF/Word/Excel remain
  synchronous.
- **Changed:** `app/config/settings.py` (v1.7.0) — `qa_modus`.
- **New tests:** `tests/test_async_worker.py` (9 tests), extension
  of `tests/test_updater.py` (+4 async tests),
  `tests/test_startup_update_check.py` (rewritten for async),
  `tests/test_main_window_update_menu.py` (v1.3.0, +3 QA tests),
  `tests/test_documentation_url_fetch.py` (v1.1.0, +6 async tests),
  `tests/test_import_wizard_dialog.py` (v1.8.0, +3 async tests).
- **New i18n keys:** `documentatie.import.bezig_metadata`,
  `documentatie.import.bezig_import`, `menu.qa_toon_update_melding`
  (NL + EN).
- **Baseline:** 1366 → **1395 passed** (+29 tests).

### Phase 11D — Resolving i18n mixing (16 October 2026)

**Motivation**

After a live language switch, the ESR screen showed a mixture of
languages: the GUI chrome (group titles, buttons) switched correctly,
but the already-translated strings from the `Beoordeling` object
(`toelichting`, `redenen`, `waarschuwingen`, `aanbevolen_vervolgstap`)
remained in the old language. In addition, the `*` annotation for a
frequency difference was hardcoded in the GUI instead of going through
i18n.

**Solution**

- `Beoordeling` gains a `taal` field populated by `beoordeel_meting`.
  The GUI can use it to detect that a result was produced in a
  different language than the current GUI language.
- After a live language switch, the ESR screen shows a clear banner in
  the GUI language ("This result was produced in {oude_taal}.
  Re-assess to display it in {nieuwe_taal}."). The already-translated
  result strings remain in their own language; no silent mixing.
- `_show_result` and `_build_result_html` translate all
  result-specific labels in `resultaat.taal` instead of `self.taal`.
  The GUI chrome continues to use `self.taal`.
- The `*` annotation for a frequency difference now goes through two
  new i18n keys (`resultaat.esr_factor_frequentie_indicatief` and
  `resultaat.esr_factor_frequentie_indicatief_kort`) in NL and EN.
- Bugfix in `apply_language`: the condition `result_group.isVisible()`
  is replaced by `_laatste_resultaat is not None`. In
  offscreen/headless situations (tests, pages not yet active in the
  `QStackedWidget`), `isVisible()` is False and the banner was never
  shown. `isVisible()` was also not the right check in production.

**For developers**

- `app/services/assessment_service.py` (v1.6.0) — `Beoordeling` has
  the extra field `taal: str = STANDAARD_TAAL`. `beoordeel_meting`
  populates it with the `taal` parameter.
- `app/gui/esr_test_screen.py` (v1.14.0) — `_show_result` detects a
  language mismatch and shows `result_language_banner`. New helper
  `_t_voor(taal, sleutel, **kwargs)` for translations in the language
  of the result. `_build_result_html` uses `resultaat.taal` for all
  result-specific labels. `apply_language` uses
  `_laatste_resultaat is not None` instead of
  `result_group.isVisible()`.
- New i18n keys under `resultaat`:
  - `taal_mismatch_banner` — "Dit resultaat is opgesteld in het
    {oude_taal}. Beoordeel opnieuw om het in het {nieuwe_taal} weer te
    geven." (EN: "This result was produced in {oude_taal}. Re-assess
    to display it in {nieuwe_taal}.")
  - `esr_factor_frequentie_indicatief` — "Indicatieve
    ESR-vergelijking: meet- en referentiefrequentie verschillen."
  - `esr_factor_frequentie_indicatief_kort` — "* indicatief:
    frequentieverschil"
- `tests/test_assessment.py` (v1.5.1) — 5 new tests in
  `TestBeoordelingTaal` proving that `Beoordeling.taal` is populated
  correctly and that the translated strings are in the specified
  language.
- `tests/test_gui_language_switch.py` (v1.2.0) — 3 new tests covering
  the language-mismatch banner. The `_fake_translate` stub now passes
  kwargs through to the output; `_fake_esr_settings` also provides a
  `beoordeling` namespace.
- **Baseline:** 1358 → **1366 passed** (+8 tests).

## Version 1.2.0 — Frequency-specific references and threshold validation (15 October 2026)

**ESR references per measurement frequency**

The ESR reference is now **frequency-specific**. Instead of one
official ESR70 table at 100 kHz used for all measurements, the
application now picks the reference profile closest to the actual
measurement frequency.

- **Official ESR70 table** — 100 kHz. Remains the primary source for
  100 kHz measurements (the LCR-ST1 cannot do this itself, but other
  instruments can).
- **Estimated profiles** — 100 Hz, 1 kHz and 10 kHz. These are
  derived from the official ESR70 table via the Nichicon frequency
  coefficients:
  - 100 Hz — × 2.00
  - 1 kHz — × 1.50
  - 10 kHz — × 1.15
- The estimated profiles are explicitly marked as an **estimate**
  (`is_schatting: true`) and carry a lower reliability level.
  They are not a datasheet value.

**Why this change**

The LCR-ST1 measures at 1 kHz and 10 kHz. The official ESR70 table
applies to 100 kHz. Because ESR falls with frequency, the comparison
was structurally too strict: good capacitors got factors that were
too low. With the new profiles, the comparison is correct again.

**Validated against 72 field measurements**

The new references were validated against 72 field measurements from
the history. For good capacitors, the factors dropped to
**0.09–0.41** — a healthy distribution.

**Thresholds remain unchanged**

The thresholds `≤1.0 / ≤2.0 / ≤3.0` remain as they are. With the new
references, they mean what they should: a healthy capacitor sits well
below 1.0, with room for degradation before "point of attention" is
reached.

**Visible in the result**

The result now explicitly shows the **reference frequency** used for
the comparison. That way you see immediately whether the measurement
and the reference are on the same frequency.

**For developers**

- `app/data/references/esr_references.json` — new profiles
  `algemeen_100hz_geschat`, `algemeen_1khz_geschat` and
  `algemeen_10khz_geschat`, each with the full ESR70 table scaled.
- `app/data/references/__init__.py` — `zoek_referentie()` accepts
  `meetfrequentie_hz` and picks the closest profile with rules.
- `app/services/assessment_service.py` — `Beoordeling` has the field
  `referentiefrequentie_hz`.
- `app/gui/esr_test_screen.py` — passes `meetfrequentie_hz` to
  `zoek_referentie` and displays the actual reference frequency.
- New i18n key: `resultaat.referentiefrequentie` (NL + EN).
- New analysis script: `scripts/herbereken_steekproef.py`.

### UX polish (phase 11A, 16 October 2026)

**Export now respects the selection**

In **History** and **Analysis** you can use a scope dropdown to choose
what to export: **current filters** or **selection**. If you check one
or more measurements in the table, the app exports only those. Without
a selection, the app exports the full filter result.

**Selection and report in the Analysis page**

The **Analysis** page has a compact selection list below the chart.
If you check one or more measurements there, you can:

- **Export…** — as overview CSV, detail CSV, or both.
- **Create report…** — a report for exactly that selection.

**Report with scope "selection"**

The measurement report now supports a report over **multiple
measurements**. The report header shows the scope ("Single measurement"
or "Selection"). The chart section is only available for a single
measurement.

**Menu "Create report…" is disabled without a selection**

In the **File** menu, the item **Create report…** is now disabled
while no measurement is selected. A tooltip explains why. On the
**Analysis** page, the item becomes active as soon as you have a
checkbox selection.

**Folder preferences are respected everywhere**

A new pure helper (`app/helpers/dialog_start_directory.py`) determines
the best start folder for every `QFileDialog`:

- **Export** — `laatste_exportmap` → `standaard_exportmap`.
- **Import** — `laatste_importmap` → `standaard_importmap`.
- **Report** — `laatste_rapportmap` → `standaard_exportmap`.

After a successful export/import/report, the folder used is
automatically remembered for next time.

**For developers**

- `app/gui/analysis_screen.py` — compact selection list below the
  chart via `QSplitter`, checkbox column, scope dropdown, type
  dropdown, export button and `report_btn`. New signals
  `selection_changed` and `back_requested`.
- `app/gui/history_screen.py` — new `selection_changed` signal with
  snapshot deduplication. `report_btn` respects the checkbox
  selection.
- `app/gui/main_window.py` — `_open_report_dialog()` chooses the scope
  based on the active page and selection.
- `app/gui/dialogs/report_dialog.py` — new classmethod
  `for_measurements(measurement_ids, ...)`.
- **New:** `app/helpers/dialog_start_directory.py` (v1.0.0).
- New i18n keys: 24 under `analyse.selectie.*`, `analyse.export.*`,
  `analyse.rapport.*` and `menu.rapport_tooltip` (NL + EN).
- Baseline: **1339 passed** (was 1329 before 11A).

### Reliability rule revised (phase 11B, 16 October 2026)

**Why this change**

The rule in `bepaal_eindstatus` used
`betrouwbaarheid.niveau == LAAG` as the trigger for at least
`AANDACHTSPUNT`. As a result, a good capacitor without a known
manufacturer/series never got `WAARSCHIJNLIJK_GOED`, even when C and
ESR were well within tolerance.

**Solution: substantive vs. administrative**

There is now a distinction between **substantive** and
**administrative** reliability reducers.

- **Substantive** (affects the measurement context itself):
  frequency difference, unknown or non-electrolytic capacitor type,
  type mismatch of the reference, C-ESR-D inconsistency, ONE_LEG or
  IN_CIRCUIT measurement method. These raise the minimum of the final
  status.
- **Administrative** (affects only the documentation/environment):
  unknown ambient temperature, typical reference value, unknown
  manufacturer/series. These lower the reliability, but do **not**
  raise the minimum of the final status.

**Concretely**

"Probably good, low reliability due to administrative factors" is now
possible, with an explicit reason in
`eindstatus_reden.betrouwbaarheid_laag_administratief`.

**For developers**

- `app/services/assessment_service.py` (v1.5.0) —
  `BetrouwbaarheidsResultaat` has an extra field
  `inhoudelijke_verlagers: tuple[str, ...] = ()`.
  `bepaal_eindstatus` uses
  `betrouwbaarheid.inhoudelijke_verlagers` instead of
  `betrouwbaarheid.niveau == Betrouwbaarheid.LAAG` as the trigger for
  at least `AANDACHTSPUNT`. In the `WAARSCHIJNLIJK_GOED` block, an
  extra branch was added: if the reliability is LAAG due to
  administrative reducers only, the status becomes
  `WAARSCHIJNLIJK_GOED` with an explicit reason.
- New i18n keys:
  - `betrouwbaarheid_factor.categorie_inhoudelijk` — "content-related
    reducer".
  - `betrouwbaarheid_factor.categorie_administratief` —
    "administrative reducer".
  - `eindstatus_reden.betrouwbaarheid_laag_administratief`.
  - `resultaat.inhoudelijke_verlagers` and
    `resultaat.administratieve_verlagers`.
- `tests/test_assessment.py` (v1.5.0) — 10 new tests. Two existing
  tests adjusted:
  - `test_meerdere_verlagende_factoren` — now expects 4 substantive
    reducers (frequency, type, inconsistency, in-circuit).
  - `test_gebruiksscenario_1_goed` — uses `D=None`, so the
    consistency check does not interfere.
- **Unchanged:** all thresholds in `settings.py`, the ESR
  classification, the consistency logic, the GUI (the GUI reads
  `verlagende_factoren`, which stays populated), and
  `report_render.py`.
- **Baseline:** 1329 → **1339 passed** (+10 tests, all in
  `test_assessment.py`). The previously documented baseline of 1347
  in `overdracht.md` v5.3.0 was incorrect and has been corrected in
  v5.4.0.

### Icons for all windows (phase 11C, 16 October 2026)

**One application icon, twelve thematic icons**

The application now has a complete icon set:

- **One application icon** — `assets/icons/app.png` (256×256,
  transparent) and `assets/icons/logo.ico` (resolutions 16, 32, 48,
  64, 128 and 256). The application icon appears in the window title
  bar, in the taskbar, on the EXE and in the installer.
- **Twelve thematic icons** — for Diagnostics, ESR, History,
  Documentation, Analysis, Report, Settings, Help, Bug/feature report,
  Update and Exit. Each icon is 64×64 and transparent.

**Where you see them**

- The **hub buttons** (Diagnostics, History, Documentation, Analysis)
  each have their own icon.
- The **ESR test button** on the Diagnostics page uses `esr.png`.
- The **menu items** in File, Diagnostics, Report, Settings and Help
  have an icon where meaningful.
- **Every dialog** automatically gets the application icon, even if
  it is ever used separately from the main window.

**Placeholders, to be replaced later**

The current icons are **placeholders** generated by a script
(`scripts/genereer_placeholders.py`). They are deliberately simple and
flat: dark blue (`#1F4E79`) as the primary colour, cyan (`#4AA3FF`) as
the accent. You can replace them at any time with final designs. The
file names are fixed; the code then does not need to change.

**No icon is not an error**

`app/helpers/icon_paths.py` returns `None` if an icon does not exist.
The GUI then simply omits the icon and keeps working. A build never
breaks because of a missing file.

**For developers**

- **New:** `app/helpers/icon_paths.py` (v1.0.0) — pure path resolution
  plus thin Qt wrappers. No hard Qt import at module level.
- **New:** `scripts/genereer_placeholders.py` (v1.0.0) — generates all
  PNGs and `logo.ico` with `QPainter`.
- **Changed:** `main.py` (v1.5.0) — sets the application icon via
  `QApplication.setWindowIcon()`.
- **Changed:** `app/gui/main_window.py` (v2.17.0) — icons on hub
  buttons, diagnostics buttons and menu items; dialogs get an icon
  via `_zet_dialoog_icoon()`.
- **Changed:** all dialogs in `app/gui/dialogs/` — own
  `_zet_eigen_icoon()` in `__init__`.
- **Changed:** `app/gui/esr_test_screen.py` (v1.13.0) — explicit
  window icon, so the screen also shows the right icon when used
  separately from the main window.
- **New:** `tests/test_icon_paths.py` — 16 tests for the helper.
- **New:** `tests/test_main_icon.py` — 1 test for the application
  icon.
- **Extended:** `tests/test_main_window_help_menu.py` and
  `tests/test_main_window_report_menu.py` — 1 test each for the icon
  on the corresponding menu item.
- **Unchanged:** `ESR_Tester.spec` and the Inno Setup `.iss` still
  point to `assets/icons/logo.ico`; that file was replaced, not
  renamed.
- **Baseline:** 1339 → **1358 passed** (+19 tests).

## Version 1.1.1 — Update check at startup and via Help (15 October 2026)

**Automatic check for a newer version**

At startup, the application checks once, without blocking, whether a
newer version is available on GitHub. That check reads the "latest"
pointer in `releases/latest/version.txt` and compares it with the
version in `app/version.py`. You will not notice the check as long as
there is no newer version.

**Manual check via Help**

You can also run the check manually via
**Help → Check for updates…**. You will always get a message: either
"You are using the latest version", or a newer version with the
**Download** button.

**What's new?**

If a newer version is available, the message also shows a
**What's new?** button. That fetches the release notes that the
developer entered on the GitHub release, and displays them in a
readable window. From there you can open the release page on GitHub.

**Setting: check for updates at startup**

In **Settings → General** there is a new checkbox
**Check for updates at startup**. It is on by default. The manual check
via Help always remains available, even if you turn off the automatic
check.

**Multilingual changelog**

The changelog is now available per language: `docs/changelog/nl_NL.md`
and `docs/changelog/en_US.md`. The Help menu automatically shows the
version that matches the selected language, with the same fallback
chain as the Help (language → Dutch → general).

**For developers**

- New module `app/helpers/updater.py` — pure update check logic, no Qt,
  no token. Contains `check_for_update()` and `fetch_release_notes()`.
- New resolver `changelog_pad_voor_taal()` in
  `app/helpers/help_paths.py`, with the same fallback chain as Help.
- New i18n keys under `update.*` and
  `settings.algemeen.controleer_updates` (NL + EN).
- New setting `algemeen.controleer_updates_bij_opstarten` (default
  `True`), backward-compatible with existing `settings.json`.

## Version 1.0.3 — Publication, test matrix and bug/feature reports (14 October 2026)

**The application is now publicly available on GitHub**

On 13 October 2026 the first public release **v1.0.3** appeared in the
repo `barremans/capacitor_esr_validator`. The installer
(`ESR_TesterSetup_1.0.3.exe`, about 63 MB) is signed and published,
together with a **stable "latest" pointer** in
`releases/latest/version.txt`. That pointer is the basis for the
update check.

**Build pipeline extended with `publish.ps1` and `build_and_publish.ps1`**

- **`publish.ps1`** — publishes the installer to GitHub, with a
  **release gate** on the Authenticode signature. An unsigned
  installer is never published.
- **`build_and_publish.ps1`** — orchestrator that runs the whole chain:
  bump version, build, sign, publish. It asks for the parameters
  upfront.

**Intune/Defender test matrix**

The installer has been proven on two types of Windows PCs:

- **Regular Windows PC** — SmartScreen shows a warning, but
  "More info → Run anyway" works.
- **Intune-managed PC** — the installer starts without a block, thanks
  to a **Defender Certificate Indicator** (`Allow`) for the CGK
  certificate. The app installs and works.

WDAC and AppLocker are **not active** in the target environment; the
Defender indicator is sufficient.

**Bug and feature reports from the application**

The main menu now has a **Report** menu with two options:

- **🐞 Report a bug or feature…** — opens a report screen where you
  describe a bug or feature request. The report is automatically
  created as a **GitHub Issue** (label `bug` or `enhancement`). Your
  name is pre-filled with your Windows username.
- **Show open cases** — shows the open bug reports and feature
  requests from the repo.

Reports go directly to the GitHub repo. No email traffic or external
service is needed: the application reads and writes via the GitHub
REST API.

**For developers**

- The feedback package (`github_feedback.py`, `bug_report_dialog.py`,
  `github_cases.py`, `check_github_secret.py`) is identical in the
  project root, with an app-specific `github_feedback_config.py`.
- The GitHub token lives in `github_secret_local.py`, which is in
  `.gitignore` (`*_secret_local.py`) and never goes to GitHub.
  PyInstaller does bundle it into the exe.
- `ESR_Tester.spec` calls `check_github_secret.py` before every build.
  A build without a valid token stops with a clear message, so that an
  installer never appears in which "Report a bug or feature" does not
  work.
- New i18n keys: `menu.rapporteren`, `menu.bug_melden`,
  `menu.open_cases` (NL + EN).

**Fixed**

- The `LF/CRLF` warning on `git add releases/latest/version.txt` is
  fixed via a `.gitattributes` rule
  (`releases/latest/version.txt text eol=lf`).
- `ESR_Tester.spec` is no longer in `.gitignore`. The spec is now
  committed, so a fresh clone on another machine can build
  immediately (`!ESR_Tester.spec`).

**Documentation**

- `docs/packaging.md` — build flow, signing, distribution, checklist.
- `docs/testmatrix_defender_intune.md` — the full test matrix with
  proven status per PC type.

## Version 1.0.2 — First Windows build, installer and signing (13 October 2026)

**The application now has a real version**

The application now has one central version, in one place:
`app/version.py`. The version is shown in the **About** dialog
(Help → About) and is the basis for the build pipeline and the later
update check.

**Full Windows build pipeline**

You can now build the application as a standalone Windows application
with installer. The flow follows the proven ArticleSearch flow 1-to-1:

- **`ESR_Tester.spec`** — PyInstaller spec, with icon active.
- **`build_installer.bat`** — builds the EXE, generates
  `dist\installer.iss`, compiles with Inno Setup 6, and signs both the
  EXE and the installer.
- **`bump_version.py`** — bumps patch, minor or major in
  `app/version.py`. Called by the build pipeline, can also be run
  manually: `python bump_version.py patch`.
- **`build_and_publish.ps1`** — orchestrator with signing preflight.
  Asks for the parameters, chooses the right certificate
  automatically, and calls the batch.
- **`publish.ps1`** — publishes the installer to GitHub, with a
  release gate on the Authenticode signature.

**Code signing**

The EXE and the installer are signed with the CGK certificate
(`CN=CGK Local Signing`, valid until 2028-09-17). After signing, the
signature is automatically verified with `signtool verify`.

**Installer with icon**

The installer now has the ESR Tester icon in the wizard and in the
shortcuts (Start menu and optionally desktop). After installation, the
app starts with user rights (`runascurrentuser`), not as administrator.

**Installation**

Default install folder: `C:\Program Files\Electronics Diagnostic
Tool Hub\ESR Tester`. The user can choose the folder during
installation.

**Fixed**

- The **window titles of the Help window and the Changelog window**
  showed the untranslated keys `dialog.help_titel` and
  `dialog.changelog_titel`. That is now fixed.
- The **ESR test button** in the Diagnostics page showed the
  untranslated key `tool.esr`. That is now fixed.
- The **build pipeline** previously aborted with
  `: was unexpected at this time.` due to a `set /p` prompt with
  parentheses. That is fixed by replacing the prompt with an
  `if defined` check.

**PDFs with readable text, without a manual step**

Qt could not find the Windows system fonts in a PySide6 environment,
so PDF reports showed black blocks instead of text. The application
now **automatically** sets the environment variable
`QT_QPA_FONTDIR=C:\Windows\Fonts` when you start on Windows and the
variable is not already set.

**For developers**

- `numpy` was added to `requirements.txt` as a direct dependency, with
  a pin `>=1.26,<3`. `pandas` got a pin `>=2.2,<3`.
  Reason: pandas 3.x gave an ABI conflict with numpy 2.x in the build.
- `QT_QPA_FONTDIR` is now set in `main.py` before `QApplication` is
  created.
- `app/version.py` is the central version source.

## Version 1.0.1 — Measurement reports and extended settings (12 October 2026)

**Creating measurement reports**

You can now create a **measurement report** from any stored
measurement. Open a measurement in the history, click **Report** (or
use **Ctrl+P** in the File menu), and you get a clear preview. You can
save the report as **HTML** or **PDF**.

The report contains:

- **Component identification** — manufacturer, series, part number,
  technology, nominal capacitance, nominal voltage, tolerance.
- **Measurement context** — measurement method, instrument, frequency,
  test voltage, temperature, safety confirmations.
- **Raw measurement values** — capacitance, ESR, D, out-of-range
  flags.
- **Assessment snapshots** — the stored assessments with reasons,
  warnings and advice.
- **Reference snapshots** — the references used per assessment.
- **Optional chart** — a chart section with ESR trend (only for
  ESR_CAPACITOR).

**New in the Reporting settings**

The Settings dialog now has a more extensive **Reporting tab**:

- **Author** — optional free field shown in the report header.
- **Default report folder** — the folder where the save dialog starts
  by default. Automatically updated after each successful save.

The **chart checkbox** in the report dialog now starts with the value
of **Include graph by default** from the settings.

**Automatically open the folder**

If **Open export folder after successful export** is on, the folder is
automatically opened after saving a report — just like with the CSV
export of the history.

**Read-only**

The report is built from the **stored snapshots**. Historical
measurements and assessments are never recalculated or changed. The
report is purely a view.

**Fixed**

- In the report HTML and PDF, the untranslated keys `algemeen.ja` and
  `algemeen.nee` appeared instead of "Yes"/"No". That is now fixed by
  using `app.ja` and `app.nee`.
- The **status labels** in the report (`Capacitance status`,
  `ESR status`, `Consistency status`) were shown as raw codes
  (`binnen_tolerantie`, `niet_beoordeeld`). They are now translated,
  just like in the GUI.

## Version 1.0.0 — Charts and trends (9 October 2026)

**New "Analysis" page**

The main menu now has a fourth button **Analysis**, next to
Diagnostics, History and Documentation. The page shows charts and
trends based on your stored measurements. You open the page via the
hub button, via the Diagnostics menu ("Open analysis"), or with the
shortcut **Ctrl+A**.

**Four chart types**

With a dropdown you choose which chart type you want to see:

- **ESR over time** — the ESR trend of your measurements, old to new.
- **Capacitance over time** — the capacitance trend.
- **D over time** — the trend of the dissipation factor.
- **ESR vs. capacitance** — a scatter plot in which each measurement
  is a point. The color shows the final status.

**Filter on exactly the same fields as the history**

The filter bar uses the same fields as the history page: manufacturer,
series, measurement method, instrument, frequency and a period
(from/to date). With **Ctrl+F** you open the filter panel.

**Aggregation per day, week or month**

By default, each chart shows all raw measurement values. With a second
dropdown you choose **average per day**, **per week** or **per
month**.

**Read-only**

The Analysis page reads your stored measurements and writes nothing
back.

**Keyboard shortcuts**

- **Ctrl+A** on the Main menu opens the Analysis page.
- **Ctrl+R** on the Analysis page refreshes the data.
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
wizard has four choices:

- **PDF file**
- **Word document**
- **Excel workbook**
- **From URL**

**Old formats are rejected**

The old `.doc` format (Word 97-2003) and `.xls` format (Excel 97-2003)
are not supported.

**Improved: opening Word and Excel files**

Imported Word and Excel files are opened in the default Word or Excel
application.

## Version 0.8 — Managing the status of your own imports (8 October 2026)

**Changing the status of an import**

In the documentation library there is now a **Change status…** button
for your own imports. You can adjust the lifecycle of an import:

- **Draft** — just imported, not yet confirmed as usable.
- **Active** — explicitly confirmed by you as usable.
- **Archived** — no longer in the default list, but still stored.

**New Status column**

The documentation table now has an extra **Status** column.

**Improved: checkboxes and radio buttons in the dark theme**

The checkboxes and radio buttons throughout the application are now
clearly visible in the dark theme.

## Version 0.7 — Metadata on import and editing in the viewer (7 October 2026)

**Metadata when importing a PDF or URL**

When importing a document you can now immediately fill in metadata:
category, manufacturer, series, part number, document version,
document date and notes.

**Editing metadata in the documentation library**

In the documentation library there is now an **Edit…** button for your
own imports.

**Improved search**

The search field in the documentation library now also searches the
metadata of imported documents.

## Version 0.6 — Per-language Help and clearer search explanation (6 October 2026)

**New**
- **Per-language Help.** The general help is now shown per language.
- **Clearer explanation about exclusion in the search help.**

**Improved**
- **Search term with minus and percent sign ignored.**

**For developers**
- New reference `docs/search_syntax.md`.

## Version 0.5 — Keyboard shortcuts and safer exit (5 October 2026)

**New**
- You can now work with the keyboard throughout the application.

**Improved**
- Esc on the Main menu now asks for confirmation.

## Version 0.4 — Smarter searching and help in the documentation (5 October 2026)

**New**
- **Search language for documentation.**
- **Help with searching.**

**Improved**
- The search help window is now also reachable via the Help menu.

## Version 0.3 — Multiple diagnostic tools in one hub (3 October 2026)

**New**
- Documents can now be linked to multiple diagnostic tools.

**Improved**
- Internal structure ready for future diagnostic tools.

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
  - **11A** — Export, import and selection: export respects
    selection, visual selection in Analysis, report scope "selection",
    menu item disabled without selection, folder preferences
    respected. **Completed on 16 October 2026.** The remaining points
    from §11A (import of measurements from another device) stay open.
  - **11B** — Reliability rule revised: distinction between
    substantive and administrative reliability reducers.
    **Completed on 16 October 2026.** Baseline 1329 → **1339 passed**.
  - **11C** — Icons for all windows.
    **Completed on 16 October 2026.** Baseline 1339 → **1358 passed**.
  - **11D** — i18n mixing in Diagnostics/Result resolved.
    **Completed on 16 October 2026.** Baseline 1358 → **1366 passed**.
  - **11E** — Async network (URL fetch, release notes).
    **Completed on 16 October 2026.** Baseline 1366 → **1395 passed**.
  - **11F** — Documentation extension (reasons, filters, bulk edit).
  - **11G** — Dark theme visuals (checkboxes, scrollbar).
  - **11H** — Light theme.
  - **11I** — Build and cosmetics (deprecations, log files,
    certificates).
- **Version 1.3.0 — AI extraction from manufacturer documents.**
  Automatic text extraction from docx/xlsx as preparation for human
  validation.
- **Version 1.4.0 — Human validation of AI output.**
  Approval flow for AI-extracted data.
- **Version 1.5.0 — Linking approved manufacturer data to
  assessment.** The assessment then uses validated manufacturer data.
- **Version 1.6.0 — Second diagnostic tool: Resistor.**
  Resistance measurements in the same Tool Hub.

---

_Historical numbering: the entries 0.1 through 0.9 describe the early
development period. The numbering is functional, not 1-to-1 linked to
`app/version.py`. From v1.1.1 onwards, the version numbers match the
actual releases._