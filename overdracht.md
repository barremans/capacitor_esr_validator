# Overdracht — Electronics Diagnostic Tool Hub / ESR Tester

**Versie:** 6.15.1
**Datum:** 2026-10-27
**Auteur:** Bart Bossuyt

Wijzigingen:
  v6.9.0 t/m v6.14.0  zie eerdere versies (in v6.14.0 integraal bewaard).
  v6.15.0 (2026-10-27) Chat 7 "C1 (historiek-import CSV/Excel)"
                        afgerond. Nieuwe pure parser/validator
                        app/helpers/history_import.py v1.1.0 (CSV +
                        XLSX via openpyxl), nieuwe service
                        app/services/history_import_service.py v1.0.0
                        (dedup op natural key, optioneel aanvullen),
                        import-knop in HistoryScreen v1.20.1.
                        Nieuwe i18n-keys in beide history.json-
                        modules.
  v6.15.1 (2026-10-27) Correctie na volledige suite: de nieuwe tests
                        zijn 13 + 4 + 5 = 22, niet 14 + 4 + 5 = 23.
                        Baseline wordt 1795 → 1817 (niet 1811).
                        Bovendien bleek tests/test_main_window_update_
                        menuV1.py nog steeds actief in de suite (10
                        tests); dat bestand crasht de volledige suite
                        met een Windows fatal exception (threading/SSL
                        in een achtergrondthread). Dat is een bestaande
                        afwijking, geen C1-regressie. Actie: bestand
                        hernoemen naar archived_main_window_update_
                        menuV1.py (geen test_-prefix) zodat pytest het
                        niet meer oppikt. Baseline na die ingreep:
                        1817 passed.

---

## 1. Werkafspraken

Ongewijzigd t.o.v. v6.14.0. De belangrijkste punten:

- **Volledige bestanden leveren, nooit fragmenten.** Als je een bestand aanpast, lever je het in zijn geheel opnieuw, ook als er maar één regel verandert. Géén secties met "… ongewijzigd …" of losse stukjes code in de lopende tekst.
- JSON altijd volledig, nooit fragmenten.
- `.md` in viervoudige backticks zodra het bestand zelf codeblokken bevat (`docs/markdown_levering.md`).
- Geen `qtbot`, geen `pytest-qt`.
- Eerst gerichte tests, dan volledige `pytest -q`.
- Testtelling verifiëren met `pytest --collect-only -q`, niet schatten.
- Bij elke nieuwe sub-fase: `Compare-Object` tegen de vorige versie om te controleren dat er geen tests verdwijnen.
- **Les uit C1 (1):** Een natural key over de canonieke keten is alleen bruikbaar als de parser en de DB-detail-conversie exact dezelfde velden en dezelfde normalisatie gebruiken. Elke afwijking (bv. enum-waarde vs. enum-object) geeft een andere sleutel en dus onterechte duplicates of onterechte nieuwe rijen.
- **Les uit C1 (2):** De overzichts-CSV is niet importeerbaar (vertaalde koppen). Het importschema is `DETAIL_EXPORT_HEADERS`, het enige stabiele machineleesbare schema.
- **Les uit C1 (3):** Excel-import via `openpyxl` read-only; geen nieuwe dependency (stond al in `requirements.txt`).
- **Les uit C1 (4):** Een archiefbestand met `test_`-prefix wordt door pytest nog steeds opgepikt. Archiveren betekent hernoemen naar een naam zonder `test_`-prefix, niet alleen een versie-suffix toevoegen.
- **Les uit C1 (5):** Een test die een echte netwerk-call doet in een achtergrondthread (zoals `test_main_window_update_menuV1.py`) kan de hele suite laten crashen met een Windows heap-corruptie. Dat is geen assertie-fout en geen C1-regressie; het is een bestaande afwijking die de suite blokkeert.

---

## 2. Projectstaat na chat 7

### 2.1 Baseline

**1817 passed, 14 subtests passed** (`pytest -q`, 2026-10-27, na chat 7 en na het archiveren van `test_main_window_update_menuV1.py`).
(1795 → 1817 = +22: 13 in `test_history_import.py`, 4 in `test_history_import_service.py`, 5 in `test_history_screen_import.py`.)

**Tussentijdse stand vóór het archiveren:** 1827 collected, 1 crash in `test_main_window_update_menuV1.py`. Dat bestand is een archiefstuk dat per ongeluk nog actief was; zie §5.13 "Bestaande afwijking".

### 2.2 Nieuwe en gewijzigde bestanden in chat 7

| Bestand | Was | Nu |
|---|---|---|
| `app/helpers/history_import.py` | — | **v1.1.0** (nieuw) |
| `app/services/history_import_service.py` | — | **v1.0.0** (nieuw) |
| `app/gui/history_screen.py` | v1.19.0 | **v1.20.1** |
| `i18n/locales/nl_NL/history.json` | — | **new keys** |
| `i18n/locales/en_US/history.json` | — | **new keys** |
| `tests/test_history_import.py` | — | **v1.0.0** (13 tests) |
| `tests/test_history_import_service.py` | — | **v1.0.0** (4 tests) |
| `tests/test_history_screen_import.py` | — | **v1.0.0** (5 tests) |
| `tests/test_main_window_update_menuV1.py` | aanwezig | **verwijderd** (hernoemd naar `archived_main_window_update_menuV1.py`) |
| `overdracht.md` | v6.14.0 | **v6.15.1** |
| `docs/openvragen.md` | v3.17.0 | **v3.18.1** |

### 2.3 Openstaand na 7

- **5A-bis / 5B-bis** — Log-schaal voor ESR/capaciteit.
- **Nieuwe i18n-test die controleert dat elke gebruikte key in beide module-versies staat.**
- **C1-bis (optioneel):** import van `.xls` (oud formaat) — alleen als de gebruiker dat expliciet vraagt. Nu niet gedaan.
- **Cosmetische header-fix in `test_main_window_update_menuV1.py`** is vervallen: het bestand is nu gearchiveerd als `archived_main_window_update_menuV1.py` en doet niet meer mee in de suite.

---

## 3. Werkafspraken — herinnering

Ongewijzigd. Zie §1.

---

## 4. Planning

| Sub-fase | Status | Baseline |
|---|---|---|
| 5A — Y-as en outliers | afgerond | 1766 → 1779 |
| 5B — Categorische X-as | afgerond | 1779 → 1787 |
| 5C — Selectie → grafiek | afgerond | 1787 → 1793 |
| 5D — Vergelijkingsmodus | afgerond | 1793 → 1795 |
| 5A-bis / 5B-bis — Log-schaal | open | ? → ? |
| Chat 6 — Masterplan debugging review | afgerond | 1795 → 1795 |
| **Chat 7 — C1 (historiek-import CSV/Excel)** | **afgerond** | **1795 → 1817** |

---

## 5. Eerdere chats

Volledige inhoud van §5.1 t/m §5.7 staat in v6.9.0. §5.8 in v6.10.0, §5.9 in v6.11.0, §5.10 in v6.12.0/v6.12.1, §5.11 in v6.13.0, §5.12 in v6.14.0.

### 5.1 t/m 5.12 — zie eerdere versies

### 5.13 Chat 7 — C1 (historiek-import CSV/Excel) (2026-10-27)

**Aanleiding:** masterplan C1. De GUI had alleen export (overzicht/detail/beide); import van een bestaand CSV/Excel-bestand ontbrak.

**Ontwerpkeuzes:**
1. **Importschema = `DETAIL_EXPORT_HEADERS`**, het enige stabiele machineleesbare schema. De overzichts-CSV is niet importeerbaar (vertaalde koppen).
2. **Dedup op natural key** (SHA-256 over de canonieke keten, regels van `docs/export_import_format.md` §6). Standaard overslaan; optioneel "aanvullen" voegt een nieuwe meting toe (nooit een update).
3. **`source_machine_id`/`source_measurement_id` blijven NULL.** C1 is een ruwe-data-import, geen exchange-import (§2.28).
4. **Import-knop in `HistoryScreen`** (naast export). Geen nieuwe menu-items in `main_window.py`.
5. **CSV + XLSX** via `openpyxl` read-only. Geen nieuwe dependency.
6. **Validatie vóór schrijven**, met duidelijke foutmeldingen per rij. Een rij met fouten blokkeert de andere rijen niet.
7. **tool_key moet `ESR_CAPACITOR` zijn.** Andere tools worden overgeslagen met een melding; dat is bewust, omdat er nog geen detail-renderer voor andere tools is.

**Nieuwe bestanden:**
- `app/helpers/history_import.py` v1.1.0 — pure parser, validator, natural key, CSV- en XLSX-adapters.
- `app/services/history_import_service.py` v1.0.0 — dedup + `save_new_measurement_chain`.
- `tests/test_history_import.py` v1.0.0 — 13 tests.
- `tests/test_history_import_service.py` v1.0.0 — 4 tests.
- `tests/test_history_screen_import.py` v1.0.0 — 5 tests.

**Gewijzigd:**
- `app/gui/history_screen.py` v1.20.1 — `import_btn`, `_choose_import_file`, `_run_import`, `_show_import_result`, `_format_import_fout`, `_import_from_file`, extra constructor-parameter `import_service`, nieuwe i18n-keys. v1.20.1 fixt dat `refresh()` de import-samenvatting niet meer overschrijft.
- `i18n/locales/nl_NL/history.json` — `historiek.import.*` (14 keys).
- `i18n/locales/en_US/history.json` — idem.

**Bewust niet in C1:**
- **Import van `.xls` (oud Excel-formaat).** `openpyxl` ondersteunt dat niet; het zou `xlrd` vereisen. Niet gedaan.
- **Import van de overzichts-CSV.** Vertaalde koppen, geen tool-specifieke velden.
- **Automatische herberekening van assessment of referentie.**
- **Samenvoegen van assessments.**
- **`source_*` vullen bij C1-import.**

**Bestaande afwijking (niet C1):** tijdens de volledige suite crashte `tests/test_main_window_update_menuV1.py` met een Windows fatal exception (0xc0000374). Oorzaak: dat bestand start een echte netwerk-call in een achtergrondthread, en de hoofdthread ruimt Qt-objecten op terwijl de thread nog bezig is. Dat bestand was in chat 6 bedoeld als archief, maar omdat de naam met `test_` begint, pikte pytest het nog op. **Fix:** hernoemd naar `archived_main_window_update_menuV1.py`. Daarmee verdwijnen 10 tests uit de suite: 1827 → 1817.

**Lessen uit C1:**
1. **De natural key moet exact dezelfde normalisatie gebruiken in parser en DB-detail-conversie.** Elke afwijking (enum-waarde vs. enum-object, `None` vs. lege string) geeft een andere sleutel.
2. **De overzichts-CSV is niet importeerbaar.** Het importschema is `DETAIL_EXPORT_HEADERS`.
3. **`openpyxl` read-only is voldoende.** Geen nieuwe dependency.
4. **Een rij met fouten mag het hele bestand niet blokkeren.** Valideer per rij, rapporteer per rij.
5. **Archiveren betekent hernoemen zonder `test_`-prefix.** Een `V1`-suffix is niet genoeg; pytest pikt het bestand anders nog op.
6. **Een test met een echte netwerk-call in een achtergrondthread kan de hele suite laten crashen.** Dat is geen assertie-fout en geen feature-regressie, maar het blokkeert de suite wel.

**Baseline:** 1795 → **1817 passed** (+22).

---

## 6. Einde van het document