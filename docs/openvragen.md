# Openvragen en observaties — Electronics Diagnostic Tool Hub / ESR Tester

**Versie:** 3.12.0
**Datum:** 2026-10-26
**Auteur:** Bart Bossuyt
**Doel:** expliciet bijhouden wat nog onduidelijk, open of te verifiëren
is. Geen bugs, geen beloftes — alleen vragen en observaties.

Wijzigingen:
  v1.0.0 t/m v3.5.0  zie eerdere versies.
  v3.6.0 (2026-10-22)  §2.16 en §2.20 gemarkeerd als opgelost in
                       11I.1 t/m 11I.4.
  v3.7.0 (2026-10-22)  §2.14 volledig gemarkeerd als opgelost in 12E.
                       Nieuwe subsectie 4.40 (12A) en 4.41 (12E).
                       §2.28 staat nu als "volgende opdracht".
  v3.8.0 (2026-10-23)  §2.28 volledig gemarkeerd als opgelost in
                       §2.28 (zes sub-fases). Nieuwe subsectie 4.42
                       (opgeloste punten in §2.28). De volgende
                       opdracht is nu 12B (op hold).
  v3.9.0 (2026-10-26)  Nieuwe subsectie 4.44 (open punten na chat 2,
                       settings & persistentie). Niets verwijderd;
                       v3.8.0 blijft integraal behouden.
  v3.10.0 (2026-10-26) Nieuwe subsectie 4.45 (opgeloste punten in
                       chat 3A en 3B: masterplan A2 en A4). Nieuwe
                       subsectie 4.46 (open punt 3C:
                       documentatie-import-regressies, alleen op
                       verzoek). Niets verwijderd; v3.9.0 blijft
                       integraal behouden.
  v3.11.0 (2026-10-26) §4.44 (open punten chat 2) definitief
                       geformuleerd na afronding van chat 2. OV-S2
                       aangevuld met noot over bestaande minimale
                       conftest.py. Baseline in §4.45 gecorrigeerd
                       naar 1711 → 1718 (wiskundig sluitend met
                       de nieuwe settings-baseline van 1711).
  v3.12.0 (2026-10-26) Chat 4 / 4A afgerond. §4.44 OV-S4 gemarkeerd
                       als opgelost (type- en keuzelijst-validatie
                       via valideer_en_normaliseer). Nieuwe subsectie
                       4.47: opgeloste punten in chat 4 / 4A (B1, B2,
                       OV-S4). Nieuwe subsectie 4.48: openstaand na
                       4A (B1-b ontwerpvraag, B3/OL-status voor 4B,
                       B4/type-match voor 4C). Niets verwijderd;
                       v3.11.0 blijft integraal behouden.

---

## 1. Uit Fase 4I — Zoektaal-observaties

Onveranderd t.o.v. v3.7.0.

---

## 2. Uit Fase 5, 6, 7, 8, 9, 10, 11 en later

### 2.1 t/m 2.5 — beantwoord

Zie eerdere versies.

### 2.6 Nieuwe openstaande punten (na 5D'.2e)

- **Async URL-fetch.** **Opgelost in 11E.2.**
- **Archiefreden.** **Opgelost in 11F.1.**
- De overige punten uit §2.6 blijven open; zie eerdere versies.

### 2.7 t/m 2.8 — beantwoord

Zie eerdere versies.

### 2.9 Cosmetische scrollbar in Word-samenvatting

- **Status:** **opgelost in 11G.2.**

### 2.10 t/m 2.13 — beantwoord

Zie eerdere versies.

### 2.11 Analyse-pagina: as-schaling, tickformaat, zoom/pan

- **Status:** **opgelost in 11G.3 en 11G.4.**

### 2.12 t/m 2.13 — beantwoord

Zie eerdere versies.

### 2.14 Nieuwe openstaande punten (na fase 8D)

- **GUI voor scope "selectie" en "filters".** **Volledig opgelost in
  11A.2 (selectie) en 12E (filters).**
- **Menu-item "Rapport maken…" disabled maken zonder selectie.**
  **Opgelost in 11A.1.**
- **PDF-fonts op Windows.** Opgelost in 9A.
- **Cosmetische opruiming i18n-keys.** **Opgelost in 11F.4.**
- **Statusfilter in de documentatiebibliotheek.** **Opgelost in 11F.2.**

### 2.15 t/m 2.20 — beantwoord

Zie eerdere versies.

### 2.16 pandas/numpy pins heroverwegen (toegevoegd 2026-10-13)

- **Status:** **opgelost in 11I.1.**

### 2.17 t/m 2.19 — beantwoord

Zie eerdere versies.

### 2.20 Cosmetische en build-technische punten (toegevoegd 2026-10-13)

- **Relatief `icon_path`.** **Opgelost in 11I.2.**
- **`Architecture identifier "x64" is deprecated`.** **Opgelost in
  11I.3.**
- **`[rename] Fallback via robocopy`-melding.** **Opgelost in 11I.3.**
- **`build_log.txt` blijft leeg.** **Opgelost in 11I.3.**
- **Certificaten opruimen.** **Opgelost in 11I.4.**

### 2.21 Drie visuele punten uit de 9F-sessie (2026-10-14)

- **Visuele selectie in Analyse.** **Opgelost in 11A.1 en 11G.5.**
- **Checkbox-zichtbaarheid in donker thema.** **Opgelost in 11G.1
  en 11G.7.**
- **i18n-menging in Diagnose/Result en Resultaatdetails.** **Opgelost
  in 11D.**

### 2.22 t/m 2.23 — beantwoord

Zie eerdere versies.

### 2.24 Update-melding cosmetica (na 9H)

- **Async `fetch_release_notes()`.** **Opgelost in 11E.1.**
- **Drie-knoppenmelding forceren voor QA.** **Opgelost in 11E.3.**
- De overige punten uit §2.24 blijven open; zie eerdere versies.

### 2.25 Export respecteert de selectie niet (toegevoegd 2026-10-15)

- **Status:** **opgelost in 11A.1.**

### 2.26 Betrouwbaarheidsregel verbergt goede resultaten (toegevoegd 2026-10-15)

- **Status:** **opgelost in 11B.**

### 2.27 Alle vensters een gepast icoon (toegevoegd 2026-10-15)

- **Status:** **opgelost in 11C.**

### 2.28 Metingen exporteren/importeren voor samenvoegen tussen toestellen (toegevoegd 2026-10-15)

- **Status:** **volledig opgelost in §2.28 (2026-10-23).**
  Zes sub-fases (28A, 28B, 28C, 28E, 28D, 28F), +102 tests. JSON-
  envelope met meetketens, natuurlijke sleutel op inhoud, herkomst-
  kolommen in schema v3, import-planner, import-service,
  export-service, en GUI-koppeling. Twee nieuwe Bestand-menu-items.

### 2.29 Mapvoorkeuren respecteren (toegevoegd 2026-10-15)

- **Status:** **opgelost in 11A.3.**

### 2.30 Filter-checkbox zichtbaarheid (toegevoegd 2026-10-20)

- **Status:** **opgelost in 11G.7.**

---

## 3. Uit vroegere contextdocumenten (nog steeds relevant)

Onveranderd t.o.v. v3.7.0.

---

## 4. Uit eigen observaties tijdens recente fases

Onveranderd t.o.v. v3.7.0, plus:

### 4.37 t/m 4.39

Onveranderd t.o.v. v3.7.0.

### 4.40 Opgeloste punten in 12A (2026-10-22)

Onveranderd t.o.v. v3.7.0.

### 4.41 Opgeloste punten in 12E (2026-10-22)

Onveranderd t.o.v. v3.7.0.

### 4.42 Opgeloste punten in §2.28 (2026-10-23)

- **§2.28 — export/import tussen toestellen.** Volledig opgelost in
  zes sub-fases:
  - **28A** — `docs/export_import_format.md` v1.0.0;
    `app/services/exchange/models.py` v1.0.0. 34 tests.
  - **28B** — `app/services/exchange/export_service.py` v1.0.1.
    15 tests.
  - **28C** — `app/services/exchange/import_planner.py` v1.0.0.
    11 tests.
  - **28E** — `app/storage/schema.py` v1.2.0,
    `migrations.py` v1.2.0, `models.py` v1.2.0, `service.py`
    v1.2.0. Schema-migratie v2 → v3. 16 tests.
  - **28D** — `app/services/exchange/import_service.py` v1.0.0.
    16 tests.
  - **28F** — `app/gui/dialogs/exchange_dialog.py` v1.0.1,
    `app/gui/main_window.py` v2.23.0, nieuwe
    `exchange.json` in NL en EN. 16 tests.
- **Belangrijke bugfix in 28F:** `_show_import_wizard` in
  `main_window.py` had een typfout `self._zet_dialoog_icono(...)`
  in plaats van `self._zet_dialoog_icoon(...)`. Latente bug die
  bij het openen van de import-wizard een `AttributeError` gaf.
  **Noot (2026-10-26):** deze bugfix stond hier als "opgelost",
  maar de code in `main_window.py` v2.23.0 bevatte de typfout nog.
  Zie 4.45 — pas in chat 3A daadwerkelijk gefixt.
- **Nieuwe i18n-keys:** het volledige `exchange.*`-blok in beide
  talen.
- **Baseline:** 1598 → **1700 passed** (+102 tests).

### 4.43 Openstaande punten na §2.28 (2026-10-23)

- **12B — AI-model-keuze en API-koppeling.** Op hold. Wacht op een
  ontwerpbeslissing: welke provider, welk model, offline-first of
  cloud-API, en waar de API-key leeft.
- **Publiek vertrouwd (EV-)certificaat.** Structurele oplossing.
- **Fallback timestamp-server.** Single point of failure.

### 4.44 Openstaande punten na chat 2 — settings & persistentie (2026-10-26)

Deze punten zijn tijdens chat 2 (settings & persistentie) gevonden
en **bewust niet** in chat 2 gefixt. Ze zijn doorgeschoven naar een
latere chat. De merge-logica zelf is ongewijzigd gebleven; chat 2
heeft alleen tests toegevoegd in `tests/test_settings_robustness.py`.

- **OV-S1 — `language: null` geeft `taal=None` door.**
  - **Status:** open, bewust niet gefixt in chat 2.
  - **Effect:** `AppInstellingen.taal = None`. `i18n.vertaal` valt
    stil terug op de sleutel. `SettingsDialog._select` toont combo
    op index 0. GUI self-healt bij Toepassen (schrijft `"nl_NL"`).
  - **Routering:** chat 8 (i18n).
  - **Mogelijke fix:** `normaliseer_taal()` analoog aan
    `normaliseer_thema()`.

- **OV-S2 — geen `conftest.py` in de repo-root (voor settings).**
  - **Status:** open, bewust niet gefixt in chat 2.
  - **Effect:** `tests/test_settings_main_window.py` leest de echte
    repo-`settings.json`. Verborgen afhankelijkheid.
  - **Routering:** chat 7 (release / testinfrastructuur).
  - **Mogelijke fix:** autouse-fixture in `tests/conftest.py`.
  - **Noot:** er is wél een minimale `conftest.py` in de root sinds
    11H.3 (Qt-opruiming). Die dekt dit punt niet; het gaat om een
    settings-specifieke fixture.

- **OV-S4 — scalaire velden niet type-gevalideerd.**
  - **Status:** **opgelost in chat 4 / 4A (2026-10-26).**
  - **Effect (voor fix):** `meetfrequentie_hz="hoog"` werd opgeslagen
    als string. Downstream kon dit crashen (`"hoog" + 1` →
    TypeError). De GUI negeerde het stil (`_select` → index 0) en
    self-healde bij Toepassen.
  - **Fix:** nieuwe pure helper `valideer_en_normaliseer()` in
    `app/config/settings.py` v1.9.0. Per veld type- en
    keuzelijst-validatie, zelfherstellend naar de dataclass-default.
    Aanroep vanuit `laad_instellingen()` ná het samenstellen van
    `AppInstellingen`. `taal` wordt bewust NIET genormaliseerd (dat
    is OV-S1, gerouteerd naar chat 8).
  - **Bewijs:** 7 nieuwe tests in
    `tests/test_settings_robustness.py` v1.1.0: string voor
    int-veld, int buiten keuzelijst, bool voor int-veld,
    condensatortype buiten keuzelijst, meetmethode buiten
    keuzelijst, andere velden in dezelfde groep blijven behouden,
    en de nieuwe sanity-drempel volgt dezelfde validatie.
  - **Routering:** was chat 4 (schema v4), nu afgerond in 4A.

- **OV-S3 (ingetrokken) — dubbele `settings.json` in i18n-map.**
  - **Status:** geen issue. Vertaalbestanden, geen app-settings.
  - **Reden intrekking:** de `settings.json` in de i18n-map is een
    vertaalbestand, geen app-configuratie. Geen actie nodig.

### 4.45 Opgeloste punten in chat 3A en 3B (2026-10-26)

Chat 3 had als opdracht masterplan **A2** (dode import-knop) en
**A4** (exchange negeert selectie) te debuggen, plus
documentatie-import-regressies. 3A en 3B zijn afgerond; 3C is
alleen op verzoek.

- **OV-C3-1 — Import-wizard opende niet (masterplan A2).**
  - **Status:** **opgelost** in chat 3A (2026-10-26).
  - **Oorzaak:** typfout `self._zet_dialoog_icono(dialog)` in
    `main_window._show_import_wizard()`. De methode heet
    `_zet_dialoog_icoon`. De typfout gaf een `AttributeError` vóór
    `dialog.exec()`, waardoor de wizard nooit opende (dode knop).
  - **Fix:** `app/gui/main_window.py` v2.23.0 → **v2.23.1**,
    één regel.
  - **Bewijs:** `tests/test_main_window_import_menu.py`
    **nieuw** (v1.0.1, 4 tests): menu-item bestaat, heeft Ctrl+I,
    `_show_import_wizard()` opent de dialoog (fix-bewijs), en
    `documentation_page.import_requested` is gekoppeld aan
    `_show_import_wizard`.
  - **Baseline:** 1711 → **1715** (+4).
  - **Les:** de fout stond al in 4.42 als "belangrijke bugfix in
    §2.28", maar de code in `main_window.py` v2.23.0 bevatte hem
    nog. Documentatie en code liepen uit elkaar. Bij elke
    overdracht controleren of genoemde bugfixes daadwerkelijk in
    de geleverde bestanden zitten.

- **OV-C3-2 — Exchange-dialoog negeert selectie (masterplan A4).**
  - **Status:** **opgelost** in chat 3B (2026-10-26).
  - **Oorzaak:** `ExchangeDialog._build_export_tab()` gebruikte
    twee onafhankelijke `if`-regels om de standaard-scope te
    bepalen. De tweede (op `active_filters`) overschreef de
    eerste (op `selected_measurement_ids`). Op HistoryScreen met
    selectie én filters bleef de scope op FILTERED staan; op
    AnalysisScreen (waar `_active_filters()` nooit leeg is vanwege
    de impliciete `tool_key="ESR_CAPACITOR"`) stond de scope altijd
    op FILTERED. De selectie werd daardoor genegeerd.
  - **Fix:** `app/gui/dialogs/exchange_dialog.py`
    v1.0.1 → **v1.0.2**. Nieuwe private helper
    `_bepaal_default_scope()` met expliciete prioriteit:
    selectie > filters > selectie-als-fallback. Geen wijziging aan
    de service-laag; `export_measurements` en `export_filters`
    waren al correct.
  - **Bewijs:** 3 nieuwe tests in `tests/test_exchange_dialog.py`
    (v1.0.1 → v1.0.2):
    `test_scope_default_is_selectie_bij_selectie_en_filters`,
    `test_scope_default_is_filters_zonder_selectie`,
    `test_analysis_screen_achtige_filters_overstemmen_selectie_niet`.
  - **Baseline:** 1715 → **1718** (+3).
  - **Les:** twee opeenvolgende `if`-regels die dezelfde state
    zetten zijn een prioriteitsval. Gebruik `if/elif/else` of een
    expliciete helper met een gedocumenteerde volgorde.

- **Totaal chat 3A + 3B:** +7 tests. Baseline **1711 → 1718**.

### 4.46 Openstaand na chat 3 — documentatie-import-regressies (3C)

- **OV-C3-3 — Documentatie-import-regressies.**
  - **Status:** open. Niet behandeld in 3A/3B.
  - **Scope:** de DuplicateSourceDialog-flow,
    `documentation_screen.import_btn` en de duplicate-popup zijn
    in 3A alleen indirect gedekt (via de signaal-koppelingstest).
    Als de gebruiker specifieke regressies wil onderzoeken, is dat
    een aparte sub-fase (3C).
  - **Routering:** chat 3C — alleen op verzoek van de gebruiker.
  - **Noot:** de bestaande tests
    (`tests/test_import_wizard_dialog.py`,
    `tests/test_documentation_screen.py`,
    `tests/test_duplicate_source_dialog.py`) dekken de functionele
    werking al. 3C zou alleen aanvullend zijn als er een concreet
    symptoom is.

### 4.47 Opgeloste punten in chat 4 / 4A (2026-10-26)

Chat 4 / 4A had als opdracht masterplan **B1** (EX_SITU-
betrouwbaarheid), **B2** (fysiek onmogelijke waarden) en **OV-S4**
(scalaire velden niet type-gevalideerd) te debuggen.

- **OV-C4-1 — B1: EX_SITU-meting kreeg onterecht "laag".**
  - **Status:** **opgelost** in chat 4 / 4A (2026-10-26).
  - **Oorzaak:** twee onafhankelijke sub-oorzaken.
    (1) `bepaal_betrouwbaarheid` gebruikte een exacte string-match
    `condensatortype != "Aluminium elektrolytisch"`. De geldige
    varianten "Aluminium elektrolytisch — Low ESR" en
    "Aluminium elektrolytisch — Bipolair/NP" uit
    `CONDENSATORTYPES` vielen daardoor in de "type onbekend"-branch
    en leverden een onterechte inhoudelijke verlager op. Een
    EX_SITU-meting op een Low ESR-condensator zakte daardoor
    onterecht in betrouwbaarheid en eindstatus.
    (2) Dezelfde exacte match werd gebruikt voor de type-mismatch-
    check tussen referentie en meting, met een onterechte
    waarschuwing en een onterechte degradatie naar LAAG tot gevolg.
  - **Fix:** `app/services/assessment_service.py` v1.6.0 → **v1.7.0**.
    Nieuwe pure helper `is_elektrolytisch_type(condensatortype)`
    erkent alle varianten die met de prefix
    `"Aluminium elektrolytisch"` beginnen. Nieuwe private helper
    `_zelfde_technologie_familie(a, b)` gebruikt dezelfde
    familie-logica voor de type-mismatch. Beide plekken in
    `bepaal_betrouwbaarheid` en `beoordeel_meting` gebruiken nu
    deze helpers.
  - **Bewijs:** 5 nieuwe tests in `tests/test_assessment.py`
    v1.6.0 (sectie `TestTypeFamilie`): alle elektrolytische
    varianten zijn familie, alle niet-elektrolytische types zijn
    geen familie, Low ESR krijgt geen type-verlager, Low ESR met
    standaard-referentie is geen mismatch, en Tantaal met
    elektrolytische referentie is wél een mismatch.
  - **B1-b (ontwerpvraag, buiten scope 4A):** of EX_SITU met
    alleen administratieve verlagers onder MIDDEL mag zakken, is
    een **domeinvraag**, geen bugfix. Zie 4.48 OV-C4-3.

- **OV-C4-2 — B2: fysiek onmogelijke waarden werden geaccepteerd.**
  - **Status:** **opgelost** in chat 4 / 4A (2026-10-26).
  - **Oorzaak:** `beoordeel_esr` en `beoordeel_capaciteit` hadden
    geen plausibiliteitscheck. Een ESR van 0,0999 mΩ werd
    geconverteerd naar 9,99e-5 Ω, gedeeld door de referentie, en
    als "waarschijnlijk normaal" beoordeeld.
  - **Fix:** `assessment_service.py` v1.7.0 voegt twee
    configureerbare sanity-drempels toe in
    `BeoordelingsInstellingen` (`esr_min_realistisch_ohm` = 1 µΩ,
    `capaciteit_min_realistisch_f` = 1 pF). Een waarde eronder
    levert `NIET_TE_BEOORDELEN` respectievelijk
    `NIET_BEOORDEELBAAR`, met een aparte toelichting en een
    waarschuwing in de `Beoordeling`. Dit is een **sanity-check**,
    geen beoordelingsdrempel.
  - **Bewijs:** 7 nieuwe tests in `tests/test_assessment.py`
    v1.6.0 (sectie `TestFysiekePlausibiliteit`): ESR onder 1 µΩ,
    ESR op de drempel, capaciteit onder 1 pF, capaciteit op de
    drempel, waarschuwing bij onrealistische ESR, waarschuwing bij
    onrealistische capaciteit, en configureerbaarheid van de
    drempels.
  - **Nieuwe i18n-keys:** `toelichting.esr.fysiek_onrealistisch`,
    `toelichting.capaciteit.fysiek_onrealistisch`,
    `veiligheid.esr_onrealistisch`,
    `veiligheid.capaciteit_onrealistisch` (NL + EN).

- **OV-S4 — scalaire velden niet type-gevalideerd.**
  - **Status:** **opgelost** in chat 4 / 4A (2026-10-26).
  - **Zie 4.44 voor de oorspronkelijke formulering.**
  - **Fix:** `app/config/settings.py` v1.8.2 → **v1.9.0**.
    Nieuwe pure helper `valideer_en_normaliseer()` past per veld
    type- en keuzelijst-validatie toe, zelfherstellend naar de
    dataclass-default. Aanroep vanuit `laad_instellingen()` ná het
    samenstellen van `AppInstellingen`. `taal` wordt bewust NIET
    genormaliseerd (dat is OV-S1, gerouteerd naar chat 8).
  - **Bewijs:** 7 nieuwe tests in
    `tests/test_settings_robustness.py` v1.1.0 (zie 4.44 voor de
    lijst).

- **Totaal chat 4 / 4A:** +19 tests (5 B1 + 7 B2 + 7 OV-S4).
  Baseline **1718 → 1737**.

### 4.48 Openstaand na chat 4 / 4A (2026-10-26)

- **OV-C4-3 — EX_SITU met alleen administratieve verlagers: mag dat
  onder MIDDEL zakken?**
  - **Status:** open, bewust niet in 4A beslist.
  - **Aanleiding:** tijdens het debuggen van B1 bleek dat
    `bepaal_betrouwbaarheid` de aftrek van verlagende factoren
    toepast vóór de methode-clamp. Voor EX_SITU is er geen clamp,
    dus drie administratieve verlagers (temperatuur onbekend,
    fabrikant onbekend, serie onbekend) brengen een start-MIDDEL
    EX_SITU-meting naar LAAG. Dat is consistent met fase 11B
    (`bepaal_eindstatus` kijkt naar inhoudelijke verlagers voor
    AANDACHTSPUNT), maar niet met de bredere filosofie dat
    administratieve factoren geen inhoudelijk oordeel mogen
    veroorzaken.
  - **Wat is de domeinvraag?** Is een EX_SITU-meting met onbekende
    temperatuur en onbekende fabrikant/serie een "middel"-
    betrouwbare meting (fysieke meting is goed, alleen documentatie
    ontbreekt) of een "laag"-betrouwbare meting (de meetcontext is
    niet volledig gedocumenteerd)?
  - **Routering:** latere chat (na 4B en 4C). Geen impact op 4A.
  - **Mogelijke fix (ter overweging):** in
    `bepaal_betrouwbaarheid`, als alle verlagers administratief
    zijn en de methode EX_SITU is, de ordinaal clampen op MIDDEL.
    Dat brengt de bestaande test
    `test_alleen_administratieve_verlagers_meerdere_geven_waarschijnlijk_goed`
    aan het wankelen (verwacht nu LAAG, zou MIDDEL worden); daarom
    een aparte ontwerpbeslissing, niet een 4A-fix.

- **OV-C4-4 — B3: OL-status / schema v4.**
  - **Status:** open. Scope van **4B**.
  - **Samenvatting:** de OL-knoppen in `esr_test_screen.py` zijn
    visueel aanwezig maar missen de onderliggende database- en
    service-koppeling. Schema v3 → v4 met `meetstatus` op
    `measurements` (NORMAL, OL, UNDER_RANGE, OVER_RANGE, UNKNOWN).
  - **Migratie-tests verplicht.**
  - **Routering:** chat 4 / 4B.

- **OV-C4-5 — B4: type-match §14.**
  - **Status:** open. Scope van **4C**.
  - **Samenvatting:** er is geen harde blokkade die voorkomt dat
    een tantaal/polymer condensator per ongeluk met de
    elektrolytische ESR-tabel wordt vergeleken. De huidige
    `zoek_referentie` filtert alleen op `condensatortype=`, maar
    een aanroeper die de parameter weglaat krijgt het eerste
    profiel met regels (ESR70 100 kHz, elektrolytisch). 4A heeft
    de familie-logica al in de assessment-service geconsolideerd;
    4C moet de blokkade in `zoek_referentie` zelf of in de GUI
    afdwingen.
  - **Routering:** chat 4 / 4C.

---

## 5. Status van dit document

- Dit document is **levend**. Bij elke fase mogen nieuwe vragen worden
  toegevoegd en opgeloste vragen worden gemarkeerd.
- Opgeloste vragen blijven staan voor historische context.
- Sinds v3.9.0 worden nieuwe open punten uit een debug-chat
  toegevoegd als nieuwe subsectie onder §4, niet als vervanging van
  bestaande secties.
- Sinds v3.10.0 geldt dat ook voor opgeloste punten uit een
  debug-chat: nieuwe subsectie, geen vervanging.