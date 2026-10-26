### 5.7 Chat 4 — Assessment, schema v4 en type-match (2026-10-26)

**Aanleiding:** de starttekst van Chat 4 noemde vier werkpunten:
B1 (EX_SITU-betrouwbaarheid), B2 (fysiek onmogelijke waarden),
OV-S4 (scalaire velden niet type-gevalideerd) en B3 (OL-status /
schema v4), plus B4 (type-match §14). De chat is opgesplitst in
drie sub-fases: 4A (assessment sanity checks), 4B (OL-status en
schema v4) en 4C (type-match §14).

**Totaal:** +48 tests. Baseline **1718 → 1766 passed**.

#### 4A — Assessment sanity checks (2026-10-26, +21 tests)

- **B1-a:** `assessment_service.bepaal_betrouwbaarheid` gebruikte
  een exacte string-match `condensatortype != "Aluminium elektrolytisch"`.
  Geldige varianten uit `CONDENSATORTYPES` ("Low ESR",
  "Bipolair/NP") werden daardoor als "type onbekend" geboekt, met
  een onterechte daling van betrouwbaarheid en eindstatus tot gevolg.
  Fix: nieuwe pure helper `is_elektrolytisch_type` (later verplaatst
  naar `app/helpers/technology.py` in 4C). `assessment_service.py`
  v1.6.0 → **v1.7.0**.
- **B2:** `beoordeel_esr` en `beoordeel_capaciteit` hadden geen
  fysieke plausibiliteitscheck. Een ESR van 0,0999 mΩ werd als
  "waarschijnlijk normaal" beoordeeld. Fix: twee nieuwe
  configureerbare sanity-drempels in `BeoordelingsInstellingen`
  (`esr_min_realistisch_ohm` = 1 µΩ, `capaciteit_min_realistisch_f`
  = 1 pF). Een waarde eronder levert `NIET_TE_BEOORDELEN`
  respectievelijk `NIET_BEOORDEELBAAR`, met aparte toelichting en
  waarschuwing. `settings.py` v1.8.2 → **v1.9.0**.
- **OV-S4:** `meetfrequentie_hz="hoog"` werd als string opgeslagen,
  omdat dataclasses geen type-checking doen. Fix: nieuwe pure helper
  `valideer_en_normaliseer` in `settings.py`, per veld
  zelfherstellend, met type- én keuzelijst-validatie. `taal` wordt
  bewust NIET genormaliseerd (OV-S1, gerouteerd naar chat 8).
- **Bugfix in `_normaliseer_veld` (v1.9.1):** de str-branch negeerde
  de `allowed`-parameter. `condensatortype="xyz"` en
  `meetmethode="HALF_IN_CIRCUIT"` werden niet naar de default
  teruggezet. Twee settings-tests legden dit bloot.
- **Nieuwe i18n-keys:** `toelichting.esr.fysiek_onrealistisch`,
  `toelichting.capaciteit.fysiek_onrealistisch`,
  `veiligheid.esr_onrealistisch`,
  `veiligheid.capaciteit_onrealistisch`.

#### 4B — OL-status en schema v4 (2026-10-26, +17 tests)

- **B3:** schema v3 → v4. Nieuwe kolom `meetstatus` op
  `measurements` (TEXT NOT NULL DEFAULT 'NORMAL', CHECK op
  NORMAL/OL/UNDER_RANGE/OVER_RANGE/UNKNOWN), plus index
  `ix_measurements_meetstatus`. Bestaande metingen krijgen NORMAL.
  `out_of_range` blijft bestaan als assessment-flag; `meetstatus`
  is het nieuwe opslagcontract.
- **Migratie v3 → v4:** `_migrate_v3_to_v4` in `migrations.py`,
  `MIGRATIONS = {2: ..., 3: ..., 4: ...}`. Verplichte
  migratie-tests: data-behoud, idempotentie, v2 → v4 in één call.
- **Model:** nieuwe enum `Meetstatus`, veld op `Measurement`
  (default `Meetstatus.NORMAL`, aan het einde van de dataclass
  zodat bestaande constructors blijven werken).
- **Service:** `create_measurement(meetstatus=...)`,
  validatie via `_meetstatus()` en `_meetstatus_from_storage()`.
- **GUI:** bestaande checkboxes blijven, met een nieuwe private
  helper `_meetstatus_voor_opslag()` die `out_of_range_check` →
  `OL`, `open_connection_check` → `UNKNOWN` en geen van beide →
  `NORMAL` mapt.
- **Persistence:** `save_esr_measurement(payload, meetstatus=...)`
  geeft de status door aan `save_new_measurement_chain`.
- **Niet in scope:** het exchange-formaat (`docs/export_import_format.md`
  blijft v1.0.0). `meetstatus` in de envelope vereist een latere
  `format_version 1.1` plus import-mapping.

#### 4C — Type-match §14 (2026-10-26, +10 tests)

- **B4:** `zoek_referentie` gebruikte een default
  `condensatortype="Aluminium elektrolytisch"` en filterde op
  exacte string-gelijkheid. Een tantaal/polymer condensator die
  per ongeluk zonder `condensatortype=` werd doorgegeven, kreeg
  stilzwijgend een elektrolytisch profiel. Omgekeerd werd
  "Low ESR" via de GUI geblokkeerd (regressie van 4A).
- **Fix:** nieuwe gedeelde helper-module `app/helpers/technology.py`
  met `is_elektrolytisch_type`, `technologie_familie` en
  `zelfde_technologie_familie`. `zoek_referentie` blokkeert
  niet-elektrolytische types expliciet (levert `None`), gebruikt
  familie-match voor profielselectie, en heeft een escape-hatch
  `condensatortype=None` voor geavanceerd gebruik.
- **Assessment:** `beoordeel_meting` voegt bij een
  niet-elektrolytisch type de waarschuwing
  `veiligheid.geen_elektrolytische_referentie` toe.
- **GUI:** `_on_assess` gebruikt `is_elektrolytisch_type(cond_type)`
  i.p.v. `cond_type == "Aluminium elektrolytisch"`. Low ESR en
  Bipolair/NP krijgen weer een elektrolytische referentie;
  tantaal/polymer krijgen geen referentie plus de waarschuwing.
- **Nieuwe i18n-key:** `veiligheid.geen_elektrolytische_referentie`.

#### Gewijzigde bestanden in Chat 4

| Bestand | Was | Nu |
|---|---|---|
| `app/services/assessment_service.py` | v1.6.0 | **v1.7.1** |
| `app/config/settings.py` | v1.8.2 | **v1.9.1** |
| `app/data/references/__init__.py` | v2.0.0 | **v2.1.0** |
| `app/helpers/technology.py` | — | **v1.0.0** (nieuw) |
| `app/storage/schema.py` | v1.2.0 | **v1.3.0** |
| `app/storage/migrations.py` | v1.2.0 | **v1.3.0** |
| `app/storage/models.py` | v1.2.0 | **v1.3.0** |
| `app/storage/service.py` | v1.2.0 | **v1.3.0** |
| `app/services/measurement_persistence_service.py` | v1.1.0 | **v1.2.0** |
| `app/gui/esr_test_screen.py` | v1.14.0 | **v1.15.1** |
| `i18n/locales/nl_NL/esr.json` | — | +5 keys |
| `i18n/locales/en_US/esr.json` | — | +5 keys |
| `tests/test_assessment.py` | v1.5.1 | **v1.6.2** |
| `tests/test_settings_robustness.py` | v1.0.1 | **v1.1.0** |
| `tests/test_references.py` | v1.1.0 | **v1.2.0** |
| `tests/test_storage_schema.py` | v1.2.0 | **v1.3.0** |
| `tests/test_storage_migrations.py` | v1.1.0 | **v1.2.0** |
| `tests/test_storage_service.py` | v1.1.0 | **v1.2.0** |
| `tests/test_storage_multitool_v2.py` | v1.0.1 | **v1.0.2** |
| `tests/test_esr_screen_settings_regressions.py` | v1.4.0 | **v1.5.1** |
| `tests/test_measurement_persistence_service.py` | v1.0.0 | **v1.1.0** |
| `docs/openvragen.md` | v3.11.0 | **v3.12.0** |
| `overdracht.md` | v6.8.0 | **v6.9.0** |

#### Openstaand na Chat 4

- **OV-C4-3** (`openvragen.md` §4.48): mag EX_SITU met alleen
  administratieve verlagers onder MIDDEL zakken? Domeinvraag.
- **Exchange v1.1:** `meetstatus` moet bij een latere
  `format_version 1.1` worden toegevoegd aan
  `docs/export_import_format.md`, `export_service.py` en
  `import_service.py`.
- **OV-S1, OV-S2, 3C:** ongewijzigd open.

#### Lessen uit Chat 4

1. Test-tellingen zijn een schatting, geen garantie. `--collect-only`
   per bestand is de enige betrouwbare verificatie.
2. Sanity-drempels moet je aan beide kanten testen: een waarde
   *net onder* én *net boven* de drempel.
3. Documentatie en code kunnen uit elkaar lopen, ook binnen één
   chat. De tests zijn de enige bron van waarheid.
4. Gedeelde helpers (`app/helpers/technology.py`) voorkomen drift
   tussen modules.
5. Exchange-formaat is een aparte laag: database-schema en
   envelope-specificatie zijn onafhankelijk.