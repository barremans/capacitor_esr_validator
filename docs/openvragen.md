# Openvragen en observaties — Electronics Diagnostic Tool Hub / ESR Tester

**Versie:** 2.4.0
**Datum:** 2026-10-15
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
  v2.3.0 (2026-10-15)  §2.23 bijgewerkt: 9H is afgerond en gepubliceerd
                       als v1.1.1. Nieuwe openstaande punten: meertalige
                       changelog (opgelost in 9H) en een drietal
                       cosmetische/UX-punten rond de update-melding.
                       §4.13 toegevoegd: eerste publicatie met
                       update-check. §4.14 toegevoegd: changelog-resolver
                       gedeeld met Help.
  v2.4.0 (2026-10-15)  §2.24 bijgewerkt: fase 10A/10B afgerond.
                       §2.25 toegevoegd: export respecteert selectie niet.
                       §2.26 toegevoegd: betrouwbaarheidsregel verbergt
                       goede resultaten bij ontbrekende administratieve
                       gegevens.

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

## 2. Uit Fase 5, 6, 7, 8, 9, 10 en later

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

### 2.23 Update-check bij opstarten en via Help — beantwoord (fase 9H)

- **Vraag:** kan de applicatie bij het opstarten en via het Help-menu
  controleren of er een nieuwere versie beschikbaar is, zonder dat er
  een token in de repo belandt?
- **Antwoord:** ja. De oplossing leunt op dezelfde bewezen aanpak als
  de ArticleSearch-flow:
  - `app/helpers/updater.py` (v1.1.0) — pure, GUI-onafhankelijke
    update-check. Leest `releases/latest/version.txt` via de raw-URL,
    met de Contents API als fallback, en vergelijkt die met
    `app/version.__version__` via `packaging.version.parse`.
  - `fetch_release_notes()` haalt de release notes (body) van de
    laatste gepubliceerde GitHub Release op via de Releases API. Geen
    token; de repo is publiek.
  - `ToolHubWindow.__init__(check_on_startup=True)` plant een
    eenmalige, niet-blokkerende check via `QTimer.singleShot(0, …)`.
    De check vangt alle fouten af en toont alleen bij een nieuwere
    versie een melding.
  - Nieuw Help-menu-item **"Controleren op updates…"** dat
    `_check_for_updates_manually()` aanroept. Toont altijd een
    melding: nieuwere versie, "je gebruikt de nieuwste versie", of
    een foutmelding.
  - De melding bij een nieuwere versie heeft drie knoppen:
    **Downloaden**, **Wat is er nieuw?**, **Later**. De "Wat is er
    nieuw?"-knop opent een `QTextBrowser`-dialoog met de release
    notes van GitHub, plus een knop **Open op GitHub**.
  - Nieuwe Settings-checkbox **"Bij opstarten controleren op
    updates"** onder **Instellingen → Algemeen**, gekoppeld aan
    `algemeen.controleer_updates_bij_opstarten` (default `True`).
    Backward-compatible met bestaande `settings.json`.
  - Nieuwe i18n-keys: `menu.controleren_op_updates`, `update.*`,
    `dialog.sluiten`, `settings.algemeen.controleer_updates` en
    `settings.algemeen.controleer_updates_tooltip` (NL + EN).
  - **Meertalige changelog:** `changelog_pad_voor_taal()` in
    `app/helpers/help_paths.py` gebruikt dezelfde fallback-keten als
    `help_pad_voor_taal()` (taal → nl_NL → legacy). De changelog
    staat nu onder `docs/changelog/nl_NL.md` en
    `docs/changelog/en_US.md`.
  - **Gepubliceerd als v1.1.1 op 2026-10-15**, met succesvolle
    handtekening en release-gate.
- **Status:** afgerond voor 9H.

### 2.24 Nieuwe openstaande punten (na fase 9H)

- **Drie-knoppenmelding is niet testbaar zonder nieuwe versie.**
  - **Wat:** de knoppen **Downloaden** en **Wat is er nieuw?**
    verschijnen alleen wanneer `is_newer` True is. In een normale
    ontwikkelomgeving (waar lokaal == remote) is dat nooit het geval,
    dus manuele visuele QA is niet mogelijk zonder een echte release.
  - **Opties:** (a) een verborgen `--force-update-check` flag in
    `main.py`; (b) een verborgen menu-item dat de melding forceert;
    (c) niets doen, vertrouwen op de pytest-dekking.
  - **Status:** open; cosmetisch; fase 11.
- **`fetch_release_notes()` blokkeert kort bij netwerk-timeout.**
  - **Wat:** `requests.get(..., timeout=5)` blokkeert de GUI tot 5
    seconden wanneer de netwerkverbinding traag of afwezig is. Dat is
    alleen merkbaar wanneer de gebruiker op **Wat is er nieuw?**
    klikt; bij het opstarten is de check via `QTimer.singleShot`
    gepland, maar de timeout blijft.
  - **Opties:** (a) async fetch via `QThread`; (b) kortere timeout;
    (c) accepteren zoals het is.
  - **Status:** open; cosmetisch; fase 11.
- **De release notes-dialoog ondersteunt geen tabellen.**
  - **Wat:** `_markdown_naar_html()` ondersteunt koppen, vet,
    cursief, code en eenvoudige lijsten, maar geen tabellen. Als de
    gebruiker tabellen in de release notes zet, worden die niet
    weergegeven.
  - **Status:** bewust beperkt; fase 11 (of nooit, als de
    release-notes-conventie het niet nodig maakt).
- **`docs/changelog.md` bestaat niet meer.**
  - **Wat:** de changelog staat nu onder `docs/changelog/` per taal.
  - **Impact:** eventuele externe links of scripts die naar
    `docs/changelog.md` verwijzen, moeten naar
    `docs/changelog/nl_NL.md` of `docs/changelog/en_US.md` wijzen.
  - **Status:** opgelost (in 9H); controle van externe verwijzingen
    open; fase 11.

### 2.25 Export respecteert de selectie niet (toegevoegd 2026-10-15)

- **Wat:** als de gebruiker in de Historiek (of Analyse) een selectie
  maakt — bijvoorbeeld 4 metingen aanvinkt — dan exporteert de app nog
  steeds **alles**, niet alleen de selectie. Dat is niet wat de
  gebruiker verwacht.
- **Impact:** `app/gui/history_screen.py` (selectie-detectie),
  `app/services/history_service.py` (export-scope),
  `app/helpers/history_csv_export.py` en
  `app/helpers/history_detail_export.py` (filterparameter), mogelijk
  `app/gui/analysis_screen.py` (rapport/export vanuit Analyse).
- **Gewenst gedrag:** als er een selectie actief is, exporteert de app
  **alleen de geselecteerde metingen**. Als er geen selectie is,
  exporteert de app alles (huidig gedrag). De gebruiker moet in de
  GUI expliciet kunnen kiezen tussen "alles" en "selectie".
- **Aandachtspunt:** dit raakt ook de Rapportage-laag (fase 8): het
  `ReportDialog` heeft nu een scope-parameter die "één meting" of
  "alles" ondersteunt. De uitbreiding naar "selectie" moet consistent
  doorwerken in rapport én CSV/Excel-export.
- **Status:** open; toegevoegd 2026-10-15; fase 11.

### 2.26 Betrouwbaarheidsregel verbergt goede resultaten (toegevoegd 2026-10-15)

- **Wat:** in `assessment_service.bepaal_eindstatus` staat de regel:

  ```
  if (capaciteit.status == OP_GRENS
      or esr.status == AANDACHTSPUNT
      or betrouwbaarheid.niveau == LAAG):
      return Eindstatus.AANDACHTSPUNT
  ```

  Met andere woorden: als de betrouwbaarheid laag is, wordt de
  eindstatus **altijd** minstens "aandachtspunt" — ook als C binnen
  tolerantie is en ESR waarschijnlijk normaal.

  In de praktijk betekent dat: een goede condensator waarvan de
  gebruiker geen fabrikant of serie heeft ingevuld, krijgt nooit
  "waarschijnlijk goed". Dat is verwarrend, want de meting zelf is
  goed; alleen de **administratieve** context ontbreekt.
- **Impact:** `app/services/assessment_service.py` (`bepaal_eindstatus`
  en `bepaal_betrouwbaarheid`), en de redenenteksten in `esr.json`.
- **Voorstel:** onderscheid maken tussen **inhoudelijke** en
  **administratieve** betrouwbaarheidsverlagers:
  - Inhoudelijk (frequentieverschil, in-circuit, type-mismatch,
    inconsistentie) → verlaagt betrouwbaarheid én verhoogt
    minimum-eindstatus.
  - Administratief (fabrikant/serie onbekend) → verlaagt
    betrouwbaarheid, maar verhoogt **niet** het minimum van de
    eindstatus. De gebruiker ziet dan "waarschijnlijk goed,
    betrouwbaarheid laag" i.p.v. "aandachtspunt".
- **Open vraag:** is dit de juiste richting, of blijft de
  conservatieve regel bewust gehandhaafd?
- **Status:** open; toegevoegd 2026-10-15; fase 11.

---

## 3. Uit vroegere contextdocumenten (nog steeds relevant)

### 3.1 V-Loss
- **Status:** V-Loss blijft optioneel en ongedefinieerd.

### 3.2 TEKCOPLUS-display en exportstructuur
- **Status:** handmatige invoer blijft de standaard.

### 3.3 Praktijkvalidatie
- **Status:** Fase 10 — afgerond in 10A/10B.

### 3.4 Referentiedata
- **Status:** opgelost in 10A/10B (frequentie-specifieke profielen).

### 3.5 Rapportage
- **Status:** deels beantwoord in fase 8. Scope "selectie" blijft open
  (zie §2.25).

### 3.6 Override van automatische beoordeling
- **Status:** open; relevant voor Fase 11.

### 3.7 Praktische meetgegevens
- **Status:** Fase 10 — afgerond.

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
- **Status:** afgerond in 9G.

### 4.13 Eerste publicatie met update-check (9H)
- **Observatie:** op 2026-10-15 is v1.1.1 gepubliceerd via
  `publish.ps1`, met succesvolle release-gate op de
  Authenticode-handtekening. `releases/latest/version.txt` staat op
  GitHub en bevat `1.1.1` + de download-URL.
- **Status:** afgerond in 9H.

### 4.14 Changelog-resolver gedeeld met Help (9H)
- **Observatie:** `changelog_pad_voor_taal()` in
  `app/helpers/help_paths.py` gebruikt dezelfde fallback-keten als
  `help_pad_voor_taal()` (taal → nl_NL → legacy). Dat betekent dat
  het toevoegen van een nieuwe taal aan de changelog géén codewijziging
  vraagt — alleen een nieuw bestand onder `docs/changelog/`.
- **Status:** afgerond in 9H.

### 4.15 Nieuwe referentie-architectuur en drempelvalidatie (10A/10B)
- **Observatie:** fase 10A introduceerde frequentie-specifieke
  referentieprofielen. Fase 10B vulde de geschatte profielen op
  100 Hz, 1 kHz en 10 kHz met de volledige ESR70-tabel, geschaald
  met 2,00 / 1,50 / 1,15.
- **Bewijs:** herberekening van de 72 praktijkmetingen via
  `scripts/herbereken_steekproef.py` toont factoren 0,09–0,41 voor
  goede condensatoren. De drempels `≤1,0 / ≤2,0 / ≤3,0` blijven
  ongewijzigd.
- **Belangrijkste observatie:** de statussen in de steekproef
  veranderen weinig, omdat de betrouwbaarheid en de
  capaciteitsafwijking nu de bepalende factoren zijn. Dit leidt tot
  §2.26.
- **Status:** afgerond in 10A/10B.

---

## 5. Status van dit document

- Dit document is **levend**. Bij elke fase mogen nieuwe vragen worden
  toegevoegd en opgeloste vragen worden gemarkeerd.
- Opgeloste vragen blijven staan voor historische context.