# Changelog

Overview of what is new or improved in the Electronics Diagnostic Tool
Hub. For technical details and architecture decisions, see
`docs/context.md`.

## Version 1.12 — Update check at startup and via Help (15 October 2026)

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

## Version 1.10 — Publication, test matrix and bug/feature reports (14 October 2026)

**The application is now publicly available on GitHub**

On 13 October 2026 the first public release **v1.0.3** appeared in the
repo `barremans/capacitor_esr_validator`. The installer
(`ESR_TesterSetup_1.0.3.exe`, about 63 MB) is signed and published,
together with a **stable "latest" pointer** in
`releases/latest/version.txt`. That pointer is the basis for the
future update check.

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

## Version 1.9 — First Windows build, installer and signing (13 October 2026)

**The application now has a real version**

The application now has one central version, in one place:
`app/version.py`. At this release it is **1.0.3**. The version is shown
in the **About** dialog (Help → About) and is the basis for the build
pipeline and later update check.

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

## Version 1.8 — Measurement reports and extended settings (12 October 2026)

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

## Version 1.7 — Charts and trends (9 October 2026)

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

## Version 1.6 — Manufacturer documents: Word and Excel (9 October 2026)

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

## Version 1.5 — Managing the status of your own imports (8 October 2026)

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

## Version 1.4 — Metadata on import and editing in the viewer (7 October 2026)

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

## Version 1.3 — Per-language Help and clearer search explanation
**Date:** 6 October 2026

**New**
- **Per-language Help.** The general help is now shown per language.
- **Clearer explanation about exclusion in the search help.**

**Improved**
- **Search term with minus and percent sign ignored.**

**For developers**
- New reference `docs/search_syntax.md`.

## Version 1.2 — Keyboard shortcuts and safer exit
**Date:** 5 October 2026

**New**
- You can now work with the keyboard throughout the application.

**Improved**
- Esc on the Main menu now asks for confirmation.

## Version 1.1 — Smarter searching and help in the documentation
**Date:** 5 October 2026

**New**
- **Search language for documentation.**
- **Help with searching.**

**Improved**
- The search help window is now also reachable via the Help menu.

## Version 1.0 — Multiple diagnostic tools in one hub
**Date:** 3 October 2026

**New**
- Documents can now be linked to multiple diagnostic tools.

**Improved**
- Internal structure ready for future diagnostic tools.

## Version 0.9 — Documentation library
**Date:** 3 October 2026

**New**
- A central, multilingual documentation library with 8 technical
  documents.

## Version 0.8 — History
**Date:** 1 October 2026

**New**
- A clear history page with all stored measurements.

## Version 0.7 — Local storage
**Date:** 27 September 2026

**New**
- Assessed measurements can be stored locally.

## Version 0.6 — More robust input and safer OL
**Date:** 29 September 2026

**New**
- Clear handling of "out of range" (OL).

## Version 0.5 — Settings
**Date:** 27 September 2026

**New**
- A settings window with three tabs.

## Version 0.4 — Compact ESR screen
**Date:** 26 September 2026

**New**
- The ESR screen has been made more compact.

## Version 0.3 — Dark theme
**Date:** 27 September 2026

**Improved**
- Uniform dark theme.

## Version 0.2 — One window with internal navigation
**Date:** 13 August 2026

**New**
- One main window with internal pages.

## Version 0.1 — First working version
**Date:** 11 August 2026

**New**
- First version of the ESR validator.

---

## Planned for future versions
- **Version 1.12** — Practical ESR validation with real measurement
  data.
- **Version 1.13** — UX/documentation polish: visual selection in
  Analysis, checkbox visibility in the dark theme, and aligning the
  language in the Diagnostics/Result window.
- **Version 2.0** — Second diagnostic tool: resistance measurements.
- **Version 3.0** — AI extraction from manufacturer documents with
  mandatory human approval.