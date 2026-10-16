# Openvragen en observaties — Electronics Diagnostic Tool Hub / ESR Tester

**Versie:** 2.7.0
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

---

## 1. Uit Fase 4I — Zoektaal-observaties

Onveranderd t.o.v. v2.6.0.

---

## 2. Uit Fase 5, 6, 7, 8, 9, 10, 11 en later

### 2.1 t/m 2.5 — beantwoord

Zie eerdere versies.

### 2.6 Nieuwe openstaande punten (na 5D'.2e)

Onveranderd t.o.v. v2.6.0.

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
- **i18n-menging in Diagnose/Result en Resultaatdetails.** Open; fase 11D.

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

- **Status:** open; **fase 11C** (volgende).

### 2.28 Metingen exporteren/importeren voor samenvoegen tussen toestellen (toegevoegd 2026-10-15)

- **Status:** open; **fase 11A** (uitgesteld naar latere sub-fase).

### 2.29 Mapvoorkeuren respecteren (toegevoegd 2026-10-15)

- **Status:** **opgelost in 11A.3** via `app/helpers/dialog_start_directory.py`.

---

## 3. Uit vroegere contextdocumenten (nog steeds relevant)

Onveranderd t.o.v. v2.6.0.

---

## 4. Uit eigen observaties tijdens recente fases

Onveranderd t.o.v. v2.6.0, plus:

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

---

## 5. Status van dit document

- Dit document is **levend**. Bij elke fase mogen nieuwe vragen worden
  toegevoegd en opgeloste vragen worden gemarkeerd.
- Opgeloste vragen blijven staan voor historische context.