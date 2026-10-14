# Openvragen en observaties — Electronics Diagnostic Tool Hub / ESR Tester

**Versie:** 2.2.0
**Datum:** 2026-10-14
**Auteur:** Bart Bossuyt
**Doel:** expliciet bijhouden wat nog onduidelijk, open of te verifiëren
is. Geen bugs, geen beloftes — alleen vragen en observaties.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie.
  v1.1.0 (2026-10-07)  §2 bijgewerkt na fase 5.
  v1.2.0 (2026-10-08)  §2.4 en §2.5 bijgewerkt na 5D'.2e.
  v1.3.0 (2026-10-09)  §2.7 toegevoegd: metadata van imports
                       doorzoekbaar maken (5D'.1b).
  v1.4.0 (2026-10-09)  §2.8 toegevoegd: Word- en Excel-import (fase 6).
  v1.5.0 (2026-10-09)  §2.10 toegevoegd: Grafieken en trends (fase 7).
  v1.6.0 (2026-10-12)  §2.12 en §2.13 toegevoegd: meetrapporten (8) en
                       settings-uitbreiding (8D).
  v1.7.0 (2026-10-13)  §2.15 toegevoegd: eerste Windows-build (9A/9B).
  v1.8.0 (2026-10-13)  §2.17 toegevoegd: Inno Setup installer en
                       signing (9C + 9D) — beantwoord.
  v1.9.0 (2026-10-13)  §2.18 bijgewerkt: publicatie naar GitHub is
                       uitgevoerd (9E, v1.0.3).
  v2.0.0 (2026-10-13)  §2.19 bijgewerkt: WDAC/AppLocker-vraag is
                       beantwoord (niet actief). §2.20 toegevoegd:
                       fase 9F afgerond.
  v2.1.0 (2026-10-14)  §2.21 toegevoegd: drie nieuwe punten uit de
                       9F-sessie (visuele selectie in Analyse,
                       checkbox-zichtbaarheid donker thema, i18n-menging
                       in Diagnose/Result). §2.22 toegevoegd: fase 9G
                       (GitHub-feedback) en 9H (update-check) aangekondigd.
  v2.2.0 (2026-10-14)  §2.22 bijgewerkt: 9G is afgerond. §2.23 toegevoegd:
                       9H (update-check) aangekondigd. §4.12 toegevoegd:
                       eerste geslaagde bug-/feature-melding via GitHub.

---

## 1. Uit Fase 4I — Zoektaal-observaties

### 1.1 `!` is substring-uitsluiting
- **Status:** verduidelijkt in 4I.1.a.
- **Restvraag:** blijft dit de gewenste semantiek?

### 1.2 `-%term` heeft geen eenduidige betekenis
- **Status:** opgelost in 4I.1.b.

### 1.3 Geen haakjes, geen veldnamen, geen datums
- **Status:** bewust gedocumenteerd in `docs/search_syntax.md` §8.1.
- **Restvraag:** wordt dit een probleem zodra de catalogus groeit?

---

## 2. Uit Fase 5, 6, 7, 8, 9 en later

### 2.1 t/m 2.5 — beantwoord

Zie de eerdere versies van dit document voor de volledige status van
scope, provenance, metadata, statusbeheer en assessment-koppeling.

### 2.6 Nieuwe openstaande punten (na 5D'.2e)

- Reden opgeven bij archiveren. **Open; klein.**
- Filter voor alleen gearchiveerde documenten. **Open; klein.**
- Statustransitie-beleid. **Bewust beperkt.**
- Catalogusmigratie bij statuswijzigingen. **Nog niet nodig.**
- OCR voor gescande PDF's. **Uitgesteld.**
- Async URL-fetch. **Open; overwegen in fase 11.**
- Datum-parsing bij bewerken. **Bewust geaccepteerd; verfijnen in 11.**
- Bulk-edit van meerdere imports. **Open.**
- Bulk-statuswijziging van meerdere imports. **Open.**

### 2.7 Metadata van imports doorzoekbaar — beantwoord (5D'.1b)

Zie v1.3.0.

### 2.8 Word- en Excel-import — beantwoord (fase 6)

Zie v1.4.0.

### 2.9 Nieuwe openstaande punten (na fase 6)

- AI-tekstextractie uit docx/xlsx. **Voorbereiding voor fase 12.**
- Cosmetische scrollbar in Word-samenvatting. **Open; klein.**

### 2.10 Grafieken en trends — beantwoord (fase 7)

Zie v1.5.0.

### 2.11 Nieuwe openstaande punten (na fase 7)

- Splitsen van `refresh()` in data-herberekening en label-update.
  **Open; klein.**
- Automatische as-schaling voor capaciteit. **Open; cosmetisch.**
- `QDateTimeAxis` tick-formaat. **Open; cosmetisch.**
- Scatterkleur bij onbekende `final_status`. **Bewust grijs.**
- Geen zoom/pan. **Open.**
- Geen PNG/PDF-export van grafieken. **Bewust buiten fase 7.**
- **Visuele selectie van bewaarde testen.** De huidige filterbalk
  dekt niet alle wensen van de eindgebruiker. De gebruiker wil ook
  visueel (in de grafiek of in een lijst) bepaalde bewaarde metingen
  kunnen selecteren om alleen die te tonen of te analyseren.
  **Open; toegevoegd 2026-10-14; fase 11.**

### 2.12 Meetrapporten — beantwoord (fase 8)

Zie v1.6.0.

### 2.13 Settings-uitbreiding — beantwoord (fase 8D)

Zie v1.6.0.

### 2.14 Nieuwe openstaande punten (na fase 8D)

- GUI voor scope "selectie" en "filters". **Open; uitgesteld.**
- Menu-item "Rapport maken…" disabled maken zonder selectie. **Open; cosmetisch.**
- PDF-fonts op Windows. **Opgelost in 9A.**
- Cosmetische opruiming i18n-keys. **Open; cosmetisch.**

### 2.15 Eerste Windows-build — beantwoord (fase 9A en 9B)

Zie v1.7.0.

### 2.16 Nieuwe openstaande punten (na fase 9B)

- Pandas-pin `<3`. **Open; bewust conservatief.**
- Numpy als directe dependency. **Bewust expliciet.**
- Cosmetische `[rename] Fallback via robocopy...`-melding. **Open; cosmetisch.**
- `build_log.txt` blijft leeg. **Open; cosmetisch.**
- Relatief `icon_path` in `main_window.py`. **Open; fase 11.**

### 2.17 Inno Setup installer en signing — beantwoord (fase 9C + 9D)

Zie v1.8.0.

### 2.18 Publiceren naar GitHub — beantwoord (fase 9E)

Zie v1.9.0.

### 2.19 Defender/Intune/WDAC — beantwoord (fase 9F)

Zie v2.0.0.

### 2.20 Nieuwe openstaande punten (na fase 9F)

- **LF/CRLF-waarschuwing** bij `git add releases/latest/version.txt`.
  - **Opgelost in 9F** via `.gitattributes`.
  - **Status:** opgelost.
- **`ESR_Tester.spec` in `.gitignore`.**
  - **Opgelost in 9F** via `!ESR_Tester.spec`.
  - **Status:** opgelost.
- **`Architecture identifier "x64" is deprecated`** tijdens ISCC.
  - **Status:** open; cosmetisch (fase 11).
- **`[rename] Fallback via robocopy...`-melding.**
  - **Status:** open; cosmetisch (fase 11).
- **`build_log.txt` blijft leeg.**
  - **Status:** open; cosmetisch (fase 11).
- **Relatief `icon_path` in `main_window.py`.**
  - **Status:** open; fase 11.
- **Twee verlopen certificaten in `CurrentUser\My`.**
  - **Status:** open; cosmetisch.
- **Publiek vertrouwd (EV-)certificaat.**
  - **Status:** open; lange termijn.
- **Fallback timestamp-server.**
  - **Status:** open; cosmetisch.
- **Testmatrix op andere Windows-versies** (Win10 vs Win11).
  - **Status:** open; cosmetisch.

### 2.21 Drie visuele punten uit de 9F-sessie (2026-10-14)

- **Visuele selectie in Analyse — grafieken en trends.**
  - **Wat:** de huidige filterbalk dekt niet alle wensen. De gebruiker
    wil ook visueel (in de grafiek of een lijst ernaast) bepaalde
    bewaarde testen kunnen selecteren — bijvoorbeeld door op een
    datapunt te klikken of een selectievakje per meting aan te vinken.
  - **Impact:** GUI-wijziging in `app/gui/analysis_screen.py`,
    mogelijk uitbreiding van `analysis_service.py` met een
    selectie-parameter.
  - **Status:** open; fase 11.

- **Checkbox-zichtbaarheid in donker thema.**
  - **Wat:** de filter-checkbox op zowel de Analyse-pagina als de
    History-pagina is onvoldoende zichtbaar op het donkere thema. De
    checkboxen moeten visueel duidelijk zijn.
  - **Impact:** `app/gui/styles.py` — expliciete
    `QCheckBox::indicator`-regels voor het donkere thema.
  - **Status:** open; fase 11.

- **i18n-menging in Diagnose/Result en Resultaatdetails.**
  - **Wat:** het Result-venster op de Diagnose-pagina en het
    Resultaatdetails-venster mengen Engels en Nederlands.
  - **Impact:** `app/services/assessment_service.py` (de teksten
    worden daar opgebouwd), `app/gui/esr_test_screen.py` (weergave
    van het Result-blok), en de i18n-bestanden `esr.json` in beide
    locales. De teksten moeten via i18n lopen, niet hardcoded in de
    service staan.
  - **Aandachtspunt:** dit raakt de **beoordelingslogica** niet —
    alleen de weergave. De service mag interne codes teruggeven; de
    GUI vertaalt ze. Dat is consistent met de `_status_code_label`-
    aanpak in `report_render.py`.
  - **Status:** open; fase 11.

### 2.22 Bug/feature-rapportage naar GitHub — beantwoord (fase 9G)

- **Vraag:** kunnen gebruikers vanuit de applicatie een bug of feature
  melden, zonder dat er een token in de repo belandt?
- **Antwoord:** ja. Het uniforme feedbackpakket uit ArticleSearch is
  uitgerold:
  - Vijf identieke bestanden in de projectroot: `github_feedback.py`,
    `bug_report_dialog.py`, `github_cases.py`, `check_github_secret.py`,
    `github_secret_local.example.py`.
  - Eén app-specifieke `github_feedback_config.py` met `APP_NAME`,
    `GITHUB_OWNER`, `GITHUB_REPO`, `get_reporter_name()` (via
    `getpass`, geen Azure AD in deze app) en `get_app_version()` (via
    `app.version`).
  - Het token staat in `github_secret_local.py`, dat in `.gitignore`
    staat (`*_secret_local.py`) en nooit naar GitHub gaat. PyInstaller
    bundelt het wel mee in de exe.
  - Nieuw menu "Rapporteren" tussen Diagnose en Instellingen in
    `main_window.py` v2.12.0. Twee acties: bug/feature melden, en open
    cases tonen.
  - Nieuwe i18n-keys: `menu.rapporteren`, `menu.bug_melden`,
    `menu.open_cases` (NL + EN).
  - `ESR_Tester.spec` v2.1.0 roept vóór elke build
    `check_github_secret.py` aan. Zonder geldig token stopt de build.
  - **Bewezen op 2026-10-14:** een testbug en een testfeature zijn
    succesvol aangemaakt als GitHub Issues en worden correct getoond
    in het "Open cases"-scherm.
- **Status:** afgerond voor 9G.

### 2.23 Fase 9H aangekondigd — update-check (2026-10-14)

- **Wat:** de "latest"-pointer op
  `releases/latest/version.txt` uitlezen en vergelijken met
  `app/version.py`. Bij een nieuwere versie een melding tonen, met
  een knop naar de download-URL. Zowel bij opstarten (eenmalig,
  niet-blokkerend) als via een menu-item in Help.
- **Voorbeeld:** ArticleSearch heeft al een `updater.py` (v1.3.0).
- **Status:** na 9G.

---

## 3. Uit vroegere contextdocumenten (nog steeds relevant)

### 3.1 V-Loss
- **Status:** V-Loss blijft optioneel en ongedefinieerd.

### 3.2 TEKCOPLUS-display en exportstructuur
- **Status:** handmatige invoer blijft de standaard.

### 3.3 Praktijkvalidatie
- **Status:** Fase 10 — Praktische ESR-validatie.

### 3.4 Referentiedata
- **Status:** open; relevant voor Fase 6 en later.

### 3.5 Rapportage
- **Status:** deels beantwoord in fase 8.

### 3.6 Override van automatische beoordeling
- **Status:** open; relevant voor Fase 11.

### 3.7 Praktische meetgegevens
- **Status:** Fase 10 — Praktische ESR-validatie.

---

## 4. Uit eigen observaties tijdens recente fases

### 4.1 Help per taal — nog niet alle talen gedekt
- Momenteel: `nl_NL.md` en `en_US.md`.

### 4.2 Testdekking van i18n-keys
- **Status:** bewust nog niet toegevoegd.

### 4.3 Projectstructuur-document
- **Vraag:** welk script genereert `PROJECT_STRUCTURE.md`?

### 4.4 Thema-uitbreiding — light theme
- **Status:** uitgesteld.

### 4.5 Checkbox- en radio-indicator in donker thema
- **Status:** opgelost in 5D'.2f voor de documentatie-viewer. **Nieuw
  in 2.21:** de filter-checkbox op Analyse en History is nog niet
  goed zichtbaar.

### 4.6 Aandachtspunt: `QT_QPA_FONTDIR` op Windows
- **Status:** opgelost in 9A.

### 4.7 Build-omgeving en ABI-conflicten
- **Status:** opgelost met pins; zie §2.16.

### 4.8 ArticleSearch-flow versus eigen variant
- **Status:** afgerond in 9C+9D; publicatie in 9E.

### 4.9 Eerste echte publicatie
- **Status:** afgerond in 9E.

### 4.10 Eerste Intune-installatie
- **Status:** afgerond in 9F.

### 4.11 Visuele punten uit de 9F-sessie
- **Status:** opgenomen in §2.21; fase 11.

### 4.12 Eerste geslaagde bug-/feature-melding via GitHub (9G)
- **Observatie:** op 2026-10-14 is de eerste bug ("eerste test") en de
  eerste feature-aanvraag ("eerste feature aanvraag") succesvol
  aangemaakt als GitHub Issue, met de juiste labels (`bug` en
  `enhancement`). Het "Open cases"-scherm toont ze correct.
- **Bewijs:** de GUI-screenshot in de 9G-sessie toont beide items
  onder de juiste rubriek.
- **Status:** afgerond in 9G.

---

## 5. Status van dit document

- Dit document is **levend**. Bij elke fase mogen nieuwe vragen worden
  toegevoegd en opgeloste vragen worden gemarkeerd.
- Opgeloste vragen blijven staan voor historische context.