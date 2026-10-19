# Openvragen en observaties — Electronics Diagnostic Tool Hub / ESR Tester

**Versie:** 3.0.0
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
  v2.7.0 (2026-10-16)  §2.26 gemarkeerd als opgelost in 11B.
                       Subsectie 4.18 toegevoegd.
  v2.8.0 (2026-10-16)  §2.27 gemarkeerd als opgelost in 11C.
                       Subsectie 4.20 en 4.21 toegevoegd.
  v2.9.0 (2026-10-16)  §2.21 (i18n-menging) gemarkeerd als opgelost in
                       11D. Subsectie 4.22 en 4.23 toegevoegd.
  v3.0.0 (2026-10-16)  §2.6 (async URL-fetch) en §2.24 (async
                       release-notes, drie-knoppenmelding forceren)
                       gemarkeerd als opgelost in 11E. Nieuwe subsectie
                       4.24 met de opgeloste punten in 11E en 4.25 met
                       een nieuwe observatie: de async-eigenaarsconventie
                       is nu expliciet en moet in toekomstige async-modules
                       worden gerespecteerd.

---

## 1. Uit Fase 4I — Zoektaal-observaties

Onveranderd t.o.v. v2.9.0.

---

## 2. Uit Fase 5, 6, 7, 8, 9, 10, 11 en later

### 2.1 t/m 2.5 — beantwoord

Zie eerdere versies.

### 2.6 Nieuwe openstaande punten (na 5D'.2e)

- **Async URL-fetch.** **Opgelost in 11E.2.** `fetch_url_metadata_async()`
  en `fetch_url_content_async()` zijn beschikbaar; de import-wizard
  gebruikt ze. De synchrone API's blijven ongewijzigd.
- De overige punten uit §2.6 blijven open; zie eerdere versies.

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
- **i18n-menging in Diagnose/Result en Resultaatdetails.** **Opgelost
  in 11D.**

### 2.22 t/m 2.23 — beantwoord

Zie eerdere versies.

### 2.24 Update-melding cosmetica (na 9H)

- **Async `fetch_release_notes()`.** **Opgelost in 11E.1.** Nieuwe
  `fetch_release_notes_async()`; `main_window.py` gebruikt die.
- **Drie-knoppenmelding forceren voor QA.** **Opgelost in 11E.3.**
  Via `algemeen.qa_modus` en een verborgen Help-menu-item.
- De overige punten uit §2.24 blijven open; zie eerdere versies.

### 2.25 Export respecteert de selectie niet (toegevoegd 2026-10-15)

- **Status:** **opgelost in 11A.1.**

### 2.26 Betrouwbaarheidsregel verbergt goede resultaten (toegevoegd 2026-10-15)

- **Status:** **opgelost in 11B.**

### 2.27 Alle vensters een gepast icoon (toegevoegd 2026-10-15)

- **Status:** **opgelost in 11C.**

### 2.28 Metingen exporteren/importeren voor samenvoegen tussen toestellen (toegevoegd 2026-10-15)

- **Status:** open; uitgesteld naar een latere sub-fase (niet 11E).

### 2.29 Mapvoorkeuren respecteren (toegevoegd 2026-10-15)

- **Status:** **opgelost in 11A.3** via
  `app/helpers/dialog_start_directory.py`.

---

## 3. Uit vroegere contextdocumenten (nog steeds relevant)

Onveranderd t.o.v. v2.9.0.

---

## 4. Uit eigen observaties tijdens recente fases

Onveranderd t.o.v. v2.7.0, plus:

### 4.16 Nieuwe openvragen na 11A

Zie v2.6.0.

### 4.17 Opgeloste punten in 11A

Zie v2.6.0.

### 4.18 Opgeloste punten in 11B (2026-10-16)

Zie v2.7.0.

### 4.19 Nieuwe openvragen na 11B

Zie v2.7.0.

### 4.20 Opgeloste punten in 11C (2026-10-16)

Zie v2.8.0.

### 4.21 Kleine inconsistentie: `test_icon_paths.py` gebruikt een
lokale `_app`-fixture

- **Status:** open; lage prioriteit. Zie v2.8.0.

### 4.22 Opgeloste punten in 11D (2026-10-16)

Zie v2.9.0.

### 4.23 Cosmetische inconsistentie: `_fake_translate` in
`test_gui_language_switch.py` plakt kwargs achter de sleutel

- **Status:** open; lage prioriteit. Zie v2.9.0.

### 4.24 Opgeloste punten in 11E (2026-10-16)

- **§2.6 — async URL-fetch.** `fetch_url_metadata_async()` en
  `fetch_url_content_async()` in `url_fetch.py` (v1.2.0). De wizard
  (v2.0.0) gebruikt ze; knoppen worden disabled, "Bezig…"-tekst
  verschijnt in de samenvatting.
- **§2.24 — async `fetch_release_notes()`.** Nieuwe
  `fetch_release_notes_async()` in `updater.py` (v1.2.0).
  `main_window.py` (v2.18.0) gebruikt die.
- **§2.24 — drie-knoppenmelding forceren voor QA.** Nieuwe instelling
  `algemeen.qa_modus` (default `False`). Bij `True` verschijnt een
  verborgen QA-menu-item in het Help-menu.
- **Nieuwe module `async_worker.py` (v2.0.0).** Generieke
  `AsyncWorker(QRunnable)` + `run_async()`. Geen netwerklogica.
- **Bugfix "Signal source has been deleted".** Opgelost door
  `WorkerSignals` als sterk Python-attribuut op de `AsyncWorker` te
  houden, `setAutoDelete(False)`, en **de aanroeper eigenaar te maken**
  van de worker. De GUI bewaart de worker in
  `self._update_check_worker`, `self._release_notes_worker`,
  `self._url_fetch_worker` en `self._import_worker`. Tests bewaren de
  worker in `_bewaarde_workers`.
- **Baseline:** 1366 → **1395 passed** (+29 tests).

### 4.25 Nieuwe observatie: async-eigenaarsconventie is nu expliciet

- **Status:** open; lage prioriteit. Geen actie nodig voor 11E.
- **Wat:** sinds 11E.1 v2.0.0 is de eigenaarsconventie van
  `AsyncWorker` expliciet: **de aanroeper is eigenaar** en moet de
  return-waarde van `run_async()` bewaren zolang de worker bezig is.
  Dit is de standaard Qt-conventie voor `QRunnable` met
  `setAutoDelete(False)`.
- **Waarom belangrijk:** als een toekomstige async-module de worker
  lokaal vasthoudt en daarna laat vallen, kan de `WorkerSignals`
  worden opgeruimd vóór de emit klaar is. Dat geeft
  `RuntimeError: Signal source has been deleted`.
- **Conventie voor volgende async-modules:**
  - Bewaar de return-waarde in een sterk attribuut op de aanroeper
    (`self._xxx_worker = run_async(...)`).
  - In tests: bewaar de worker in een module-level lijst
    `_bewaarde_workers` tot het einde van de sessie.
  - Nooit de worker in een lokale variabele laten vallen zonder
    referentie.
- **Wanneer opruimen:** geen actie nodig; dit is een
  documentatie-afspraak, geen bug.

---

## 5. Status van dit document

- Dit document is **levend**. Bij elke fase mogen nieuwe vragen worden
  toegevoegd en opgeloste vragen worden gemarkeerd.
- Opgeloste vragen blijven staan voor historische context.