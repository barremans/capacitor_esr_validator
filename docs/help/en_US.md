# Help

Welcome to the Help for the Electronics Diagnostic Tool Hub.

This help is offered per language. The application automatically shows
the version that matches the selected language. If a language version
is missing, the application falls back to Dutch and then to the
general help.

## ESR / Capacitor tester

The ESR / Capacitor tester supports entering and assessing capacitor
and ESR measurements.

Detailed explanations about:

- using the ESR tool;
- measurement methods;
- measurement instruments;
- safety instructions;
- interpreting results;

will be added in a later development phase.

## History

The **History** page shows the stored measurements from the local
database. You can filter on manufacturer, series, measurement method,
instrument, frequency, date and status. Each measurement has a detail
view with the full stored measurement chain and assessment.

Select a row to activate the **Report**, **Repeat measurement** and
**Details** buttons. You can also check one or more measurements via
the checkbox column to make a selection for export or report.

## Analysis

The **Analysis** page shows charts and trends of your stored
measurements. There are four chart types:

- ESR over time;
- capacitance over time;
- D over time;
- ESR vs. capacitance (scatter plot, coloured per final status).

With the aggregation dropdown you choose **raw measurements**,
**average per day**, **per week** or **per month**. The filter bar uses
the same fields as the History. The page is fully read-only.

Below the chart there is a compact **selection list** with the same
measurements. Check one or more measurements to export them or create
a report from them.

## Creating reports

From the **History** you can create a measurement report for a single
measurement via the **Report** button or via **Ctrl+P** in the File
menu. From the **Analysis** you can create a report for your full
checkbox selection.

The report contains component identification, measurement context,
raw measurement values, assessment snapshots, reference snapshots and
optionally a chart (only for a single measurement). You can save it as
**HTML** or **PDF**. The report is read-only: no historical
measurements or assessments are recalculated.

## Exporting and selection

In the **History** and in the **Analysis** you can use a scope
dropdown to choose what you export:

- **Current filters** — all measurements that match the active
  filters.
- **Selection** — only the measurements you checked in the checkbox
  column.

Without a selection, the app exports the full filter result. You can
choose between an **overview CSV**, a **detail CSV** or **both**.

## Documentation library

Besides this general help, the application contains a multilingual
documentation library with technical documents about safe discharge,
measurement methods, LCR meter, ESR meter, frequency and test voltage,
dissipation factor, C-ESR-D plausibility, and the limitations of
in-circuit measurement.

You open the library from the Main menu or via the menu
**Help → Search documentation…**.

## Searching the documentation

The search language supports simple characters:

- multiple words or a comma = all words must be present;
- a vertical bar `|` = either word;
- a minus sign `-` = this exact word;
- an exclamation mark `!` = exclude this word;
- a percent sign `%` = fill in yourself (wildcard).

Press **F1** or use the question-mark button next to the search field
for detailed instructions with examples.

## Updates

The application checks once at startup, without blocking, whether a
newer version is available. You can also run that check manually via
**Help → Check for updates…**.

If a newer version is available, a message appears with the
**Download** button. That opens the download page in your browser.
Via **Settings → General** you can disable the automatic check at
startup; the manual check always remains available.

## Keyboard shortcuts

- **Global:** Ctrl+Q (quit), Ctrl+E (ESR test),
  Ctrl+I (Import document), Ctrl+P (Create report), F1 (help).
- **ESR screen:** Esc (back), Ctrl+Enter (assess), Ctrl+S (save),
  Ctrl+W (clear), Ctrl+I (measurement instructions).
- **History:** Esc (back), Ctrl+R (refresh), Ctrl+F (filters),
  Ctrl+D (details), Ctrl+H (repeat measurement).
- **Analysis:** Esc (back), Ctrl+R (refresh), Ctrl+F (filters).
- **Main menu:** Ctrl+D (Diagnose), Ctrl+H (History),
  Ctrl+K (Documentation), Ctrl+A (Analysis), Esc (quit with
  confirmation).

## Languages

The application supports multiple languages. You switch language via
**Settings → Languages**. All screens, help files and documents follow
the selected language. If a translation is missing, the application
falls back to Dutch.