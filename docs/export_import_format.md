# Export/import-formaat tussen toestellen — bindende spec

**Versie:** 1.0.0  
**Datum:** 2026-10-22  
**Auteur:** Bart Bossuyt  
**Fase:** §2.28A  
**Status:** bindend voor alle export- en importcode in §2.28

---

## 1. Doel

Dit document legt het formaat vast waarin de Electronics Diagnostic Tool Hub
meetketens exporteert naar en importeert uit een ander toestel. Het formaat is
ontworpen voor:

- **round-trip:** exporteren en op een ander toestel importeren levert
  dezelfde meetketens op, zonder verlies van ruwe waarden of snapshots;
- **samenvoegen:** meerdere exports kunnen na elkaar geïmporteerd worden,
  zonder dat dezelfde keten twee keer in de database belandt;
- **herkomst:** elke geïmporteerde keten blijft herkenbaar als afkomstig
  van een specifiek toestel en een specifieke meting;
- **versiebeheer:** het formaat heeft een eigen versie, los van de
  app-versie en de databaseschemaversie.

Het formaat is **geen** vervanging van de bestaande CSV-exports
(`history_csv_export`, `history_detail_export`) of van de rapportage. Die
blijven ongewijzigd. Dit formaat is uitsluitend bedoeld voor uitwisseling
tussen toestellen.

---

## 2. Bestandsnaam en encoding

- **Extensie:** `.esrexchange.json`
- **Encoding:** UTF-8, **zonder BOM**
- **Regeleinden:** LF (`\n`)
- **Pretty-printed:** 2 spaties inspringing, `sort_keys=True` voor
  determinisme
- **Geen** gecomprimeerde vorm, **geen** base64, **geen** binaire bijlagen

De bestandsnaam wordt door de GUI bepaald (28F) en bevat doorgaans een
timestamp, bv. `export_2026-10-22_14-30-00.esrexchange.json`.

---

## 3. Envelope-structuur

Een exportbestand is één JSON-object met de volgende velden:

```json
{
  "format_version": "1.0",
  "app_version": "1.3.0",
  "schema_version": 2,
  "exported_at_ms": 1792651200000,
  "source_machine_id": "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
  "chains": []
}
```

| Veld | Type | Verplicht | Betekenis |
|---|---|---|---|
| `format_version` | string | ja | `"1.0"`. Toekomstige versies `"1.1"`, `"2.0"`. |
| `app_version` | string | ja | De `__version__` van de exporterende app. Alleen informatief. |
| `schema_version` | int | ja | `CURRENT_SCHEMA_VERSION` van de bron-database op exportmoment. |
| `exported_at_ms` | int | ja | Unix epoch-ms van het exportmoment. |
| `source_machine_id` | string (UUID4) | ja | Eenmalig per machine gegenereerd, opgeslagen in `settings.json`. |
| `chains` | array | ja | Lijst van meetketens. Mag leeg zijn (lege export is geldig). |

**Extra velden** die een toekomstige versie toevoegt, worden bij import
van een oudere app **genegeerd**, niet als fout behandeld. Omgekeerd
weigert een oudere app een envelope met een `format_version` die zij niet
kent (zie §9).

---

## 4. Keten-structuur

Elke entry in `chains` is één volledige meetketen: dezelfde zeven
entiteiten die `StorageService.get_measurement_detail()` teruggeeft,
in dezelfde vorm, maar **zonder database-`id`'s** en **zonder
`created_at_ms`** (die zijn toestel-specifiek en zinloos op een ander
toestel).

```json
{
  "source_measurement_id": 42,
  "source_machine_id": "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
  "natural_key": "9f2c…",
  "component_model": { },
  "component_sample": { },
  "measurement_session": { },
  "measurement": { },
  "assessment_snapshots": [ ],
  "reference_snapshots_by_assessment_index": [ ]
}
```

| Veld | Type | Verplicht | Betekenis |
|---|---|---|---|
| `source_measurement_id` | int | ja | De `measurement.id` op het brontoestel. |
| `source_machine_id` | string (UUID4) | ja | Machine-ID van het brontoestel. |
| `natural_key` | string (hex) | ja | SHA-256 van de canonieke keten (zie §6). |
| `component_model` | object | ja | Velden zonder `id` en `created_at_ms`. |
| `component_sample` | object | ja | Velden zonder `id`, `component_model_id`, `created_at_ms`. |
| `measurement_session` | object | ja | Velden zonder `id`, `component_sample_id`, `created_at_ms`. |
| `measurement` | object | ja | Velden zonder `id`, `measurement_session_id`, `created_at_ms`. |
| `assessment_snapshots` | array | ja | Lijst van assessment-snapshots, elk zonder `id`, `measurement_id`, `created_at_ms`. |
| `reference_snapshots_by_assessment_index` | array | ja | Lijst van lijsten; `[i]` hoort bij `assessment_snapshots[i]`. Elk item zonder `id`, `assessment_snapshot_id`, `created_at_ms`. |

**Waarom `_by_assessment_index` en niet `_by_id`?** Omdat de assessment-`id`'s
op het doelmachine anders zijn. De index in de array is de enige stabiele
verwijzing binnen één keten.

**Waarom `natural_key` in de keten én niet alleen berekend bij import?**
Omdat de import-planner (28C) de sleutel moet kunnen vergelijken zonder
de canonieke berekening opnieuw te doen voor elke bestaande rij in de
database. De sleutel wordt bij export berekend en meegeschreven; bij
import **herberekent** de planner hem uit de velden en vergelijkt met de
meegeschreven waarde. Bij afwijking weigert de planner de keten.

---

## 5. Dataclass-velden (canoniek)

Voor elke entiteit worden alleen de volgende velden opgenomen. Velden die
`None` zijn, worden **weggelaten** (niet als `null` geschreven). Dat houdt
de bestanden compact en maakt de canonieke vorm eenduidig.

### 5.1 `component_model`

```
manufacturer, series, part_number, technology,
nominal_capacitance_f, nominal_capacitance_value, nominal_capacitance_unit,
rated_voltage_v, voltage_type,
tolerance_lower_pct, tolerance_upper_pct,
temperature_min_c, temperature_max_c,
case_size, notes
```

### 5.2 `component_sample`

```
sample_code, sample_state, source, batch_lot_code, date_code,
visual_condition, notes
```

### 5.3 `measurement_session`

```
started_at_ms, ended_at_ms, operator_name, customer, project, installation,
module_board, component_reference, notes
```

### 5.4 `measurement`

```
measured_at_ms, measurement_method, tool_key,
instrument_key, instrument_name, instrument_profile_version,
frequency_hz, test_voltage_vrms, temperature_c,
power_off_confirmed, discharged_confirmed,
residual_voltage_before_v, residual_voltage_after_v,
capacitance_f, esr_ohm, dissipation_factor_d, quality_factor_q,
impedance_z_ohm, reactance_x_ohm,
out_of_range, open_suspected, short_suspected, unstable_reading,
parallel_components_notes, mechanical_condition_notes, notes,
record_status, invalid_reason
```

**Let op:** `supersedes_measurement_id` wordt **niet** opgenomen. Een
keten is een zelfstandige eenheid; de "vervangt"-relatie tussen metingen
is toestel-specifiek en wordt bij import niet gereconstrueerd.

### 5.5 `assessment_snapshots`

```
assessed_at_ms, engine_version,
capacitance_status, capacitance_deviation_pct,
esr_status, esr_factor, consistency_status, derived_esr_from_d_ohm,
reliability_level, final_status,
reasons_json, warnings_json, advice_json
```

### 5.6 `reference_snapshots`

```
reference_role, reference_level, reference_type,
manufacturer, series, part_number,
reference_value, reference_unit,
frequency_hz, temperature_c, test_voltage_vrms, dc_bias_v,
value_kind,
source_name, source_document, source_version, source_data_version,
source_entry_id, source_hash, snapshot_json
```

---

## 6. Natuurlijke sleutel

De natuurlijke sleutel is een SHA-256 hex-string over een canonieke
JSON-weergave van de keten **zonder** de velden die toestel-specifiek
zijn. Concreet:

1. Bouw een dict met exact de velden uit §5, in de volgorde van §5.
2. Laat `None`-velden weg.
3. Converteer naar JSON met `sort_keys=True`, `separators=(",", ":")`,
   `ensure_ascii=False`.
4. Encodeer als UTF-8.
5. `hashlib.sha256(...).hexdigest()`.

De canonieke dict bevat **geen** `source_measurement_id`,
`source_machine_id`, `natural_key` en **geen** `created_at_ms`/`id`-velden.
Twee ketens met dezelfde inhoud (zelfde component, zelfde meting, zelfde
snapshots) geven dus dezelfde sleutel, ook op verschillende toestellen.

**Waarom SHA-256 en niet iets korter?** Omdat de sleutel ook als
duplicate-detectie dient bij grote historieken (duizenden ketens). Een
botsing is dan catastrofaal; SHA-256 is de goedkoopste veilige keuze.

---

## 7. Conflictregels

Bij import vergelijkt de planner (28C) elke keten met de bestaande
database op twee niveaus:

1. **Expliciete duplicate:** bestaat er al een keten met dezelfde
   `(source_machine_id, source_measurement_id)`? Dat kan alleen als
   de herkomst-kolommen (28E) gevuld zijn. Zo ja → `SKIP_DUPLICATE`.
2. **Inhoudelijke duplicate:** bestaat er al een keten met dezelfde
   `natural_key`? Zo ja → `SKIP_DUPLICATE`.
3. **Anders:** `IMPORT_NEW`.

De planner kent `NEEDS_USER_CHOICE` alleen toe als de gebruiker in de
GUI expliciet om een keuze is gevraagd (28F). De **standaard** bij een
`NEEDS_USER_CHOICE` is `IMPORT_AS_CONFLICT_COPY`: de keten wordt als
nieuwe keten opgeslagen, met de herkomst-kolommen gevuld. Zo gaat er
nooit stil een meting verloren.

---

## 8. Herkomst-kolommen (schema v3, fase 28E)

De import-service (28D) vult bij elke geïmporteerde keten twee kolommen
in de `measurements`-tabel:

- `source_machine_id TEXT` — de UUID4 van het brontoestel
- `source_measurement_id INTEGER` — de `measurement.id` op het brontoestel

Beide zijn `NULL` voor metingen die op dit toestel zelf zijn aangemaakt.
Een index `ix_measurements_source_identity` op
`(source_machine_id, source_measurement_id)` versnelt de
duplicate-detectie.

---

## 9. Versiebeleid

| Situatie | Gedrag |
|---|---|
| `format_version` exact `"1.0"` | Verwerken. |
| `format_version` nieuwer (`"1.1"`, `"2.0"`, …) | Weigeren met duidelijke melding. |
| `format_version` onbekend/leeg/geen string | Weigeren. |
| `format_version` ouder (bestaat niet in 1.0) | N.v.t. |
| Extra onbekende velden in envelope of keten | Negeren. |
| Ontbrekend verplicht veld | Weigeren. |
| `schema_version` nieuwer dan `CURRENT_SCHEMA_VERSION` | Weigeren. |
| `schema_version` ouder | Toestaan; de import-service vult ontbrekende velden met `None`. |

Een geweigerde envelope wordt nooit gedeeltelijk geïmporteerd: de
planner (28C) weigert vóór er iets naar de database gaat.

---

## 10. Wat dit formaat **niet** doet

- Geen compressie, geen encryptie, geen signing.
- Geen overdracht van de documentatiebibliotheek, referentietabellen of
  instellingen.
- Geen overdracht van `supersedes_measurement_id`.
- Geen merge van assessments: een assessment-snapshot is een
  onveranderlijk historisch feit en wordt als nieuwe snapshot
  geïmporteerd, nooit samengevoegd.
- Geen automatische herberekening van assessment of referentie.

---

## 11. Status van dit document

- Dit document is **bindend** voor alle code in `app/services/exchange/`.
- Wijzigingen aan het formaat vereisen een nieuwe `format_version` en
  een aparte sub-fase.
- Nieuwe inzichten komen als nieuwe sectie erbij, niet als vervanging
  van bestaande secties.