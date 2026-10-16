# Openvragen en observaties — Electronics Diagnostic Tool Hub / ESR Tester

**Versie:** 2.8.0
**Datum:** 2026-10-16
**Auteur:** Bart Bossuyt
**Doel:** expliciet bijhouden wat nog onduidelijk, open of te verifiëren
is. Geen bugs, geen beloftes — alleen vragen en observaties.

Wijzigingen:
  v1.0.0 t/m v2.4.0  zie eerdere versies.
  v2.5.0 (2026-10-15)  §2.27 t/m §2.29 toegevoegd.
  v2.6.0 (2026-10-16)  §2.25 gemarkeerd als opgelost in 11A.1. §2.29
                       gemarkeerd als opgelost in 11A.3. §2.14 bijgewerkt:
                       menu-item disabled zonder selectie is opgelost in
                       11A.1; rapport-scope "selectie" is opgelost in
                       11A.2. §2.28 blijft open (export/import tussen
                       toestellen).
  v2.7.0 (2026-10-16)  §2.26 gemarkeerd als opgelost in 11B
                       (onderscheid inhoudelijke vs. administratieve
                       betrouwbaarheidsverlagers). Nieuwe subsectie 4.18
                       toegevoegd met de opgeloste punten in 11B.
  v2.8.0 (2026-10-16)  §2.27 gemarkeerd als opgelost in 11C (iconen voor
                       alle vensters). Nieuwe subsectie 4.20 toegevoegd
                       met de opgeloste punten in 11C. Nieuwe subsectie
                       4.21 met een kleine inconsistentie in
                       test_icon_paths.py (lokale _app-fixture).

---

## 1. Uit Fase 4I — Zoektaal-observaties

Onveranderd t.o.v. v2.7.0.

---

## 2. Uit Fase 5, 6, 7, 8, 9, 10, 11 en later

### 2.1 t/m 2.5 — beantwoord

Zie eerdere versies.

### 2.6 Nieuwe openstaande punten (na 5D'.2e)

Onveranderd t.o.v. v2.7.0.

### 2.7 t/m 2.13 — beantwoord

Zie eerdere versies.

### 2.14 Nieuwe openstaande punten (na fase 8D)

- **GUI voor scope "selectie" en "filters".** Deels opgelost: 11A.2
  levert scope "selectie" via `ReportDialog.for_measurements`. Scope
  "filters" in de Rapportage-GUI blijft open.
- **Menu-item "Rapport maken…" disabled maken zonder selectie.**
  **Opgelost in 11A.1.**
- **PDF-fonts op Windows.** Opgelost in 9A.
- **Cosmetische opruiming i18n-keys.** Open; fase 11F.

### 2.15 t/m 2.20 — beantwoord

Zie eerdere versies.

### 2.21 Drie visuele punten uit de 9F-sessie (2026-10-14)

- **Visuele selectie in Analyse.** **Deels opgelost in 11A.1** via de
  compacte selectielijst onder de grafiek. Klikbare datapunten blijven
  open voor fase 11G.
- **Checkbox-zichtbaarheid in donker thema.** Open; fase 11G.
- **i18n-menging in Diagnose/Result en Resultaatdetails.** Open;
  **fase 11D (volgende).**

### 2.22 t/m 2.24 — beantwoord

Zie eerdere versies.

### 2.25 Export respecteert de selectie niet (toegevoegd 2026-10-15)

- **Status:** **opgelost in 11A.1.** De Historiek en de Analyse
  bieden nu een scope-DDL met `FILTERED` en `SELECTED`. De export
  respecteert de checkbox-selectie.

### 2.26 Betrouwbaarheidsregel verbergt goede resultaten (toegevoegd 2026-10-15)

- **Status:** **opgelost in 11B.**
- **Wat was:** in `assessment_service.bepaal_eindstatus` stond de regel
  dat `betrouwbaarheid.niveau == LAAG` de eindstatus altijd minstens
  naar `AANDACHTSPUNT` duwde — ook als C binnen tolerantie was en ESR
  waarschijnlijk normaal. Een goede condensator zonder fabrikant/serie
  kreeg dus nooit "waarschijnlijk goed".
- **Oplossing:** onderscheid tussen **inhoudelijke** en
  **administratieve** betrouwbaarheidsverlagers.
  - Inhoudelijk (frequentieverschil, type onbekend/niet-elektrolytisch,
    type-mismatch, inconsistentie, ONE_LEG/IN_CIRCUIT) → verlaagt
    betrouwbaarheid én verhoogt minimum-eindstatus.
  - Administratief (temperatuur onbekend, typische referentiewaarde,
    fabrikant/serie onbekend) → verlaagt betrouwbaarheid, maar verhoogt
    het minimum van de eindstatus niet.
- **Concreet:** "waarschijnlijk goed, betrouwbaarheid laag door
  administratieve factoren" is nu mogelijk, met een expliciete reden in
  `eindstatus_reden.betrouwbaarheid_laag_administratief`.
- **Gewijzigd:** `app/services/assessment_service.py` (v1.5.0),
  `i18n/locales/nl_NL/esr.json`, `i18n/locales/en_US/esr.json`,
  `tests/test_assessment.py` (v1.5.0, 10 nieuwe tests).
- **Baseline:** 1329 → 1339 passed.

### 2.27 Alle vensters een gepast icoon (toegevoegd 2026-10-15)

- **Status:** **opgelost in 11C.**
- **Wat was:** de applicatie had geen icoon op de vensters en geen
  thematische iconen voor de hub-knoppen, diagnose-knoppen en
  menu-items.
- **Oplossing:** één applicatie-icoon (`app.png`, `logo.ico`) plus
  twaalf thematische iconen, alle in `assets/icons/`, met een pure
  helper (`app/helpers/icon_paths.py`) die de paden bepaalt en stil
  terugvalt op `None` als een icoon ontbreekt. De GUI laat het icoon
  dan weg.
- **Gewijzigd:** `main.py` (v1.5.0), `app/gui/main_window.py`
  (v2.17.0), `app/gui/esr_test_screen.py` (v1.13.0), alle dialogen in
  `app/gui/dialogs/`, `assets/icons/README.md`. Nieuw:
  `app/helpers/icon_paths.py` (v1.0.0),
  `scripts/genereer_placeholders.py` (v1.0.0),
  `tests/test_icon_paths.py` (16 tests),
  `tests/test_main_icon.py` (1 test).
- **Baseline:** 1339 → 1358 passed (+19 tests).

### 2.28 Metingen exporteren/importeren voor samenvoegen tussen toestellen (toegevoegd 2026-10-15)

- **Status:** open; **fase 11A** (uitgesteld naar latere sub-fase).

### 2.29 Mapvoorkeuren respecteren (toegevoegd 2026-10-15)

- **Status:** **opgelost in 11A.3** via `app/helpers/dialog_start_directory.py`.

---

## 3. Uit vroegere contextdocumenten (nog steeds relevant)

Onveranderd t.o.v. v2.7.0.

---

## 4. Uit eigen observaties tijdens recente fases

Onveranderd t.o.v. v2.7.0, plus:

### 4.16 Nieuwe openvragen na 11A

- §2.28 — export/import tussen toestellen (uitgesteld).
- §2.26 — betrouwbaarheidsregel (opgelost in 11B).
- Overige fase 11-sub-fases.

### 4.17 Opgeloste punten in 11A

- §2.25 — export respecteert selectie.
- §2.29 — mapvoorkeuren.
- §2.14 — menu-item disabled zonder selectie.
- §2.14 — rapport-scope "selectie".
- §2.21 — visuele selectie in Analyse (deels).

### 4.18 Opgeloste punten in 11B (2026-10-16)

- **§2.26 — betrouwbaarheidsregel herzien.** Inhoudelijke verlagers
  verhogen het minimum van de eindstatus; administratieve verlagers
  verlagen de betrouwbaarheid wel, maar blokkeren "waarschijnlijk goed"
  niet meer.
- **Baselinecorrectie.** De gedocumenteerde baseline van 1347 in
  `overdracht.md` v5.3.0 kwam niet overeen met de werkelijke teststand.
  Werkelijke baseline: 1329 vóór 11B, 1339 ná 11B.

### 4.19 Nieuwe openvragen na 11B

- Geen nieuwe openvragen toegevoegd door 11B zelf.
- De GUI toont de opsplitsing inhoudelijk/administratief nog niet in de
  resultaatdetails. Dat is een mogelijke cosmetische aanvulling voor een
  latere fase (11D of 11F), geen open vraag.

### 4.20 Opgeloste punten in 11C (2026-10-16)

- **§2.27 — iconen voor alle vensters.** Eén applicatie-icoon plus
  twaalf thematische iconen. Pure helper `icon_paths` met veilige
  fallback. Baseline 1339 → 1358 passed.
- **Help-sneltoetsen gecontroleerd.** De NL Help en EN Help zijn nu
  consistent: `Ctrl+I`, `Ctrl+P` en `Ctrl+A` staan in beide onder
  "Globaal".
- **Changelogs bijgewerkt** voor 11B en 11C.

### 4.21 Kleine inconsistentie: `test_icon_paths.py` gebruikt een
lokale `_app`-fixture

- **Status:** open; lage prioriteit.
- **Wat:** `tests/test_icon_paths.py` definieert een lokale
  `_app`-fixture met `@pytest.fixture(scope="module")`. De
  projectafspraak zegt: **geen fixture, `QApplication` lokaal ophalen
  in de testfunctie**. De fixture werkt, maar wijkt af van de
  afspraak.
- **Wanneer opruimen:** een latere cosmetische fase (11F of 11I).
  Geen functionele impact.

---

## 5. Status van dit document

- Dit document is **levend**. Bij elke fase mogen nieuwe vragen worden
  toegevoegd en opgeloste vragen worden gemarkeerd.
- Opgeloste vragen blijven staan voor historische context.