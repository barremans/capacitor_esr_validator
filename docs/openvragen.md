# Openvragen en observaties — Electronics Diagnostic Tool Hub / ESR Tester

**Versie:** 3.18.1
**Datum:** 2026-10-27
**Auteur:** Bart Bossuyt
**Doel:** expliciet bijhouden wat nog onduidelijk, open of te verifiëren is. Geen bugs, geen beloftes — alleen vragen en observaties.

Wijzigingen:
  v1.0.0 t/m v3.17.0  zie eerdere versies (in v3.17.0 integraal bewaard).
  v3.18.0 (2026-10-27)  Chat 7 "C1 (historiek-import CSV/Excel)"
                        afgerond. Nieuwe subsectie 4.54. §2.36
                        toegevoegd. Baseline 1795 → 1817 (na
                        correctie in v3.18.1).
  v3.18.1 (2026-10-27)  Correctie na volledige suite: 13 + 4 + 5 = 22
                        nieuwe tests, niet 23. Baseline 1795 → 1817,
                        niet 1811. Bovendien bleek
                        tests/test_main_window_update_menuV1.py nog
                        actief in de suite (10 tests) en crashte de
                        suite met een Windows fatal exception
                        (threading/SSL in een achtergrondthread).
                        Dat bestand is nu hernoemd naar
                        archived_main_window_update_menuV1.py. Niets
                        verwijderd; v3.18.0 blijft integraal behouden.

---

## 1. Uit Fase 4I — Zoektaal-observaties

Onveranderd t.o.v. v3.17.0.

---

## 2. Uit Fase 5, 6, 7, 8, 9, 10, 11 en later

### 2.1 t/m 2.35 — beantwoord of afgerond

Zie eerdere versies (t/m v3.17.0).

### 2.36 Historiek-import C1 (toegevoegd 2026-10-27)

- **Status:** **opgelost in chat 7 (2026-10-27).**
- **Symptoom:** de historiek had alleen export (overzicht/detail/beide); import van een bestaand CSV/Excel-bestand ontbrak.
- **Oorzaak:** de feature bestond niet. `HistoryScreen` had geen import-knop, geen `getOpenFileName`, en `MeasurementHistoryService`/`StorageService` hadden geen import-API.
- **Fix:**
  - `app/helpers/history_import.py` v1.1.0 — pure parser + validator + natural key + CSV/XLSX-adapters (`openpyxl` read-only).
  - `app/services/history_import_service.py` v1.0.0 — dedup op natural key, optioneel aanvullen, per-keten foutisolatie.
  - `app/gui/history_screen.py` v1.20.1 — `import_btn`, `_choose_import_file`, `_run_import`, `_show_import_result`, `_import_from_file`, optionele `import_service`-parameter. v1.20.1 fixt dat `refresh()` de import-samenvatting niet meer overschrijft.
  - i18n: 14 nieuwe keys onder `historiek.import.*` in NL + EN.
- **Bewijs:** 13 tests in `test_history_import.py`, 4 in `test_history_import_service.py`, 5 in `test_history_screen_import.py` (samen 22).
- **Baseline:** 1795 → **1817 passed** (+22).
- **Zie ook:** §4.54 voor de observaties.

---

## 3. Uit vroegere contextdocumenten (nog steeds relevant)

Onveranderd t.o.v. v3.17.0.

---

## 4. Uit eigen observaties tijdens recente fases

Ongewijzigd t.o.v. v3.17.0, plus:

### 4.37 t/m 4.53

Onveranderd t.o.v. v3.17.0.

### 4.54 Opgeloste en openstaande punten na chat 7 — C1 (2026-10-27)

**Opgelost in C1:**

- **Historiek-import CSV/Excel.**
  - **Status:** **opgelost** in C1 (2026-10-27).
  - **Zie §2.36 voor het volledige verslag.**

**Bestaande afwijking, blootgelegd tijdens C1 (niet C1):**

- **`tests/test_main_window_update_menuV1.py` nog actief in de suite.**
  - **Status:** **opgelost** op 2026-10-27.
  - **Symptoom:** de volledige suite crashte met een Windows fatal exception (0xc0000374) in `test_handmatige_check_met_fout_toont_warning`. Stack: een echte netwerk-call (`requests.get` → SSL) in een achtergrondthread, terwijl de hoofdthread Qt-objecten opruimt.
  - **Oorzaak:** het bestand was in chat 6 bedoeld als archief, maar omdat de naam met `test_` begint, pikte pytest het nog op. `--collect-only` telde 10 tests voor dit bestand.
  - **Fix:** hernoemd naar `archived_main_window_update_menuV1.py` (geen `test_`-prefix). Daarmee verdwijnen 10 tests uit de suite: 1827 → 1817.
  - **Les:** archiveren betekent hernoemen zonder `test_`-prefix. Een `V1`-suffix is niet genoeg.

**Observaties na C1:**

- **De natural key moet exact dezelfde normalisatie gebruiken in parser en DB-detail-conversie.** Elke afwijking (enum-waarde vs. enum-object, `None` vs. lege string) geeft een andere sleutel en dus onterechte duplicates of onterechte nieuwe rijen.
- **De overzichts-CSV is niet importeerbaar.** Vertaalde koppen, geen tool-specifieke velden, geen `measurement_id`. Het importschema is `DETAIL_EXPORT_HEADERS`.
- **Een rij met fouten mag het hele bestand niet blokkeren.** De parser verzamelt fouten per rij en gaat door.
- **`openpyxl` read-only is voldoende.** Excel-import voegt geen dependency toe.
- **`source_machine_id`/`source_measurement_id` blijven NULL bij C1-import.** Consistent met §2.28.
- **`refresh()` na een import mag de import-samenvatting niet overschrijven.** In v1.20.1 bewaart `_run_import` de samenvatting en zet die terug na `refresh()`.

**Openstaand na C1:**

- **C1-bis: `.xls` (oud Excel-formaat).** `openpyxl` ondersteunt dat niet; het zou `xlrd` vereisen. Niet gedaan, geen concrete vraag.
- **C1-ter: import van andere tool_keys dan `ESR_CAPACITOR`.** De parser staat het niet toe, omdat er nog geen detail-renderer voor andere tools is. Zodra een tweede tool een detail-renderer krijgt, kan `TOEGESTANE_TOOL_KEYS` worden uitgebreid.
- **OV-C5-2 / OV-C5-7 — Log-schaal voor ESR/capaciteit (5A-bis / 5B-bis).** Open.
- **Nieuwe i18n-test die controleert dat elke gebruikte key in beide module-versies staat.** Aanbevolen, niet urgent.

---

## 5. Status van dit document

- Dit document is **levend**. Bij elke fase mogen nieuwe vragen worden toegevoegd en opgeloste vragen worden gemarkeerd.
- Opgeloste vragen blijven staan voor historische context.
- Sinds v3.9.0 worden nieuwe open punten uit een debug-chat toegevoegd als nieuwe subsectie onder §4, niet als vervanging van bestaande secties.
- Sinds v3.10.0 geldt dat ook voor opgeloste punten uit een debug-chat: nieuwe subsectie, geen vervanging.