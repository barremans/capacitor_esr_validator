<!--
Modulepad: capacitor_esr_validator/docs/data_model.md
Doel: Formeel gegevensmodel (velden, types, verplicht/optioneel, validatie)
      voor de condensator- en ESR-validator, vóór er databaseschema of
      applicatiecode wordt geschreven.
Referentie: functional_design_v1.md §6 (Gegevensmodel) en
            PROJECT_CONTEXT_capacitor_ESR_validator.md §5 en §20.
Status: ontwerpdocument, GEEN applicatiecode. Nog niet goedgekeurd.
-->

# Gegevensmodel — Condensator- en ESR-validator (v1)

Dit document maakt §6 van `functional_design_v1.md` concreet: exacte
veldtypes, verplicht/optioneel, toegelaten waarden en veldvalidatie.
Er wordt hier nog géén databaseschema (tabellen, kolommen, sleutels)
vastgelegd — dat is de volgende stap, ná goedkeuring van dit document.

Legende types: `tekst`, `getal` (decimaal, komma én punt toegelaten
als invoer, intern altijd omgezet naar `float`), `geheel getal`,
`keuzelijst` (vaste opties, geen vrije tekst), `boolean`
(ja/nee-vinkje), `datum_tijd`.

---

## 1. Open vragen die dit model raken (nog onbeantwoord)

Deze open vragen uit `functional_design_v1.md` §9 zijn nog niet
beantwoord. Waar ze een veld raken, staat dat expliciet vermeld met
**[OPEN]**. Zolang ze open staan, wordt met een veilige, conservatieve
default gewerkt (bv. veld optioneel houden, geen automatische afleiding).

- Vraag 1–4: exacte TEKCOPLUS-displayvelden/-volgorde, herkomst V-Loss,
  voorbeeldexport, handleiding.
- Vraag 6: mag de gebruiker referentietabellen zelf toevoegen/bewerken?
- Vraag 10: gebruikersprofielen/rechten, of blijft "gebruiker" vrije tekst?
- Vraag 11: standaardlocatie van de SQLite-database.

---

## 2. Entiteiten — overzicht

1. **Component** — het fysieke onderdeel (identificatie + nominale gegevens)
2. **Meting** — één meetsessie op een component (meetcontext + meetwaarden)
3. **Referentieregel** — één regel uit een referentietabel/datasheet
4. **Meting–Referentie-koppeling** — welke referentie gebruikt is bij welke beoordeling, en met welke versie

Verhouding: één Component heeft nul of meer Metingen. Één Meting
verwijst naar nul of meer Referentieregels (via de koppeling), nooit
rechtstreeks — altijd traceerbaar via een aparte koppelrecord (zie §6).

---

## 3. Component — identificatie

| Veld | Type | Verplicht | Validatie / opmerking |
|---|---|---|---|
| `id` | geheel getal | systeem | intern, automatisch gegenereerd |
| `datum_aangemaakt` | datum_tijd | systeem | automatisch, niet manueel wijzigbaar |
| `gebruiker` | tekst | verplicht | vrij tekstveld (§9 vraag 10 nog open — geen login v1) |
| `klant` | tekst | optioneel | |
| `project` | tekst | optioneel | |
| `installatie_machine` | tekst | optioneel | |
| `printplaat_module` | tekst | optioneel | |
| `component_referentie` | tekst | verplicht | vrije tekst, bv. `C12`; geen opgelegd formaat |
| `fabrikant` | tekst | optioneel | leeg toegelaten — beïnvloedt betrouwbaarheid (zie validation_rules.md) |
| `serie` | tekst | optioneel | idem |
| `onderdeelnummer` | tekst | optioneel | |
| `opmerkingen` | tekst (meerdere regels) | optioneel | |

---

## 4. Component — nominale gegevens

| Veld | Type | Verplicht | Validatie / opmerking |
|---|---|---|---|
| `nominale_capaciteit` | getal | verplicht | > 0; komma of punt toegelaten als decimaalteken |
| `eenheid_capaciteit` | keuzelijst | verplicht | `pF`, `nF`, `µF`, `mF` — geen vrije tekst, voorkomt eenhedenfout (testgeval 1) |
| `tolerantie_percent` | getal | optioneel | ≥ 0; leeg = "tolerantie onbekend" → capaciteitsstatus wordt "niet beoordeelbaar" |
| `nominale_werkspanning` | getal | optioneel | > 0 indien ingevuld |
| `ac_of_dc` | keuzelijst | optioneel | `AC`, `DC`, `onbekend` |
| `condensatortype` | keuzelijst | verplicht | `Aluminium elektrolytisch`, `Anders` (vrij tekstveld erbij) — bij "Anders" toont de app een waarschuwing dat de elektrolytische ESR-tabellen niet gelden (aanname 1, fd §2) |
| `polariteit` | keuzelijst | optioneel | `gepolariseerd`, `niet-gepolariseerd`, `onbekend` |
| `datasheet_referentie` | tekst | optioneel | bv. bestandsnaam of link |
| `datasheet_esr_of_impedantie` | getal | optioneel | zie §5 voor eenheid; alleen zinvol samen met `datasheet_referentiefrequentie` |
| `datasheet_referentiefrequentie` | getal (Hz) | optioneel, **verplicht als `datasheet_esr_of_impedantie` is ingevuld** | zonder deze waarde is de datasheet-ESR niet bruikbaar (§9 context) |
| `datasheet_referentietemperatuur` | getal (°C) | optioneel | ontbreken verlaagt betrouwbaarheid (§12 context) |

---

## 5. Meting — meetcontext (verplicht vóór meetwaarden)

Ontwerpregel uit `functional_design_v1.md` §6.3: de meetwaarden-stap
wordt pas vrijgegeven nadat de veiligheidsbevestigingen zijn aangevinkt.

| Veld | Type | Verplicht | Validatie / opmerking |
|---|---|---|---|
| `in_circuit` | boolean | verplicht | |
| `een_aansluiting_los` | boolean | verplicht | |
| `volledig_uitgebouwd` | boolean | verplicht | Deze drie samen vormen de meetopstelling; app toont waarschuwing als geen enkele is aangevinkt |
| `schakeling_spanningsloos_bevestigd` | boolean | **verplicht = ja**, of expliciet "niet van toepassing" + reden | blokkeert meetwaarden-stap tot bevestigd (§6.3 fd) |
| `condensator_ontladen_bevestigd` | boolean | **verplicht = ja**, of expliciet "niet van toepassing" + reden | idem |
| `reden_niet_van_toepassing` | tekst | verplicht **indien** een van bovenstaande twee op "n.v.t." staat | voorkomt stilzwijgend overslaan van veiligheidsstap |
| `restspanning_gemeten` | getal + eenheid (V/mV) | optioneel, aanbevolen | |
| `meetfrequentie` | keuzelijst | verplicht | `100 Hz`, `1 kHz`, `10 kHz` — vaste lijst, toestel ondersteunt geen andere (§3 context) |
| `testspanning` | keuzelijst | verplicht | `0,3 Vrms`, `0,6 Vrms` |
| `omgevingstemperatuur` | getal (°C) | optioneel | ontbreken verlaagt betrouwbaarheid |
| `toestel_identificatie` | tekst | optioneel | bv. serienummer LCR-meter |
| `opmerkingen_parallelle_componenten` | tekst | optioneel | |

---

## 6. Meting — meetwaarden

| Veld | Type | Verplicht | Validatie / opmerking |
|---|---|---|---|
| `gemeten_capaciteit` | getal | verplicht | > 0 |
| `eenheid_gemeten_capaciteit` | keuzelijst | verplicht | `pF`, `nF`, `µF`, `mF` |
| `gemeten_ESR` | getal | verplicht | ≥ 0 |
| `eenheid_gemeten_ESR` | keuzelijst | verplicht | `mΩ`, `Ω` — expliciete keuze verplicht (testgeval 2) |
| `D` | getal | optioneel | dissipation factor, dimensieloos |
| `Q` | getal | optioneel | |
| `Z` | getal | optioneel | impedantie |
| `X` | getal | optioneel | reactantie |
| `V_Loss_ruwe_waarde` | getal | optioneel | zie §7 — nooit gebruikt in beoordeling |
| `V_Loss_eenheid` | keuzelijst | verplicht **indien** `V_Loss_ruwe_waarde` is ingevuld | `V`, `mV`, `%`, `dimensieloos`, `onbekend` |
| `stabiliteit_van_de_meting` | keuzelijst | optioneel | bv. `stabiel`, `schommelt licht`, `schommelt sterk`, `onbekend` |
| `datum_tijd_meting` | datum_tijd | verplicht | default = nu, wijzigbaar |

**Meerdere metingen per frequentie:** een Meting-record is altijd
gekoppeld aan één `meetfrequentie` (uit de meetcontext). Meerdere
metingen op verschillende frequenties voor hetzelfde component worden
opgeslagen als aparte Meting-records, nooit als overschreven waarden
(§9 context, §22 testgeval 11).

### 6.1 V-Loss — expliciete regel

`V-Loss` blijft ongedefinieerd totdat een handleiding, schermafbeelding
of concrete voorbeeldmeting beschikbaar is (§6 context, aanname 5 fd).
Concreet in dit model:

- het veld wordt **altijd** samen met zijn eenheid opgeslagen als ruwe waarde;
- het wordt **nooit** gelijkgesteld aan ESR of D;
- het heeft **geen** rol in de assessment-service (zie `validation_rules.md`);
- de UI toont het veld met een label "betekenis onbekend — enkel ter registratie".

---

## 7. Referentieregel (extern, §20 context)

| Veld | Type | Verplicht | Validatie / opmerking |
|---|---|---|---|
| `unieke_id` | tekst/geheel getal | systeem | |
| `bron` | tekst | verplicht | bv. "Peak Atlas ESR70", "Specap", "Datasheet Panasonic FC-serie" |
| `bron_url` | tekst | optioneel | |
| `condensatortype` | keuzelijst | verplicht | zie §4 |
| `fabrikant` | tekst | optioneel | leeg = generieke tabel (bv. Peak Atlas/Specap) |
| `serie` | tekst | optioneel | |
| `capaciteit` | getal + eenheid | verplicht | |
| `spanningsklasse` | getal | verplicht | |
| `esr_waarde` | getal | verplicht | |
| `eenheid` | keuzelijst | verplicht | `mΩ`, `Ω` |
| `typisch_of_maximaal` | keuzelijst | verplicht | `typisch`, `maximaal` — beïnvloedt betrouwbaarheid |
| `frequentie` | getal (Hz) | verplicht | |
| `temperatuur` | getal (°C) | optioneel | ontbreken verlaagt betrouwbaarheid |
| `toepassingsgebied` | tekst | optioneel | |
| `betrouwbaarheidsniveau` | keuzelijst | verplicht | `hoog`, `middel`, `laag` — volgt uit validatiehiërarchie §7 context |
| `datum_toegevoegd` | datum_tijd | systeem | |
| `opmerkingen` | tekst | optioneel | |

---

## 8. Koppeling Meting ↔ Referentie

Elke beoordeling van een meting bewaart welke referentieregel(s)
gebruikt zijn, met welke versie, zodat latere updates van referentie-
tabellen oude resultaten niet stilzwijgend wijzigen (§20 context).

| Veld | Type | Verplicht | Validatie / opmerking |
|---|---|---|---|
| `meting_id` | verwijzing | verplicht | |
| `referentieregel_id` | verwijzing | verplicht | |
| `referentie_versie_snapshot` | tekst/JSON | verplicht | kopie van de gebruikte referentiewaarden op moment van beoordeling, onafhankelijk van latere wijzigingen aan de referentietabel |
| `rol_in_hiërarchie` | keuzelijst | verplicht | volgens §7 context, niveau 1–7 (exacte datasheet t.e.m. relatieve vergelijking) |

---

## 9. Vaste keuzelijsten (samenvatting)

- `eenheid_capaciteit`: pF, nF, µF, mF
- `eenheid_ESR`: mΩ, Ω
- `meetfrequentie`: 100 Hz, 1 kHz, 10 kHz
- `testspanning`: 0,3 Vrms, 0,6 Vrms
- `condensatortype`: Aluminium elektrolytisch, Anders
- `ac_of_dc`: AC, DC, onbekend
- `polariteit`: gepolariseerd, niet-gepolariseerd, onbekend
- `typisch_of_maximaal`: typisch, maximaal
- `betrouwbaarheidsniveau`: hoog, middel, laag
- `V_Loss_eenheid`: V, mV, %, dimensieloos, onbekend
- `stabiliteit_van_de_meting`: stabiel, schommelt licht, schommelt sterk, onbekend

Al deze lijsten zijn keuzelijsten, geen vrije tekst — dit voorkomt
eenheden- en typefouten (§9 context, testgevallen 1–3).

---

## 10. Wat hier bewust NIET in zit

- geen automatische frequentieconversie of afgeleide velden op basis daarvan;
- geen automatisch ingevulde beoordeling — dat is het onderwerp van `validation_rules.md`;
- geen databaseschema (tabellen, sleutels, indexen) — volgende stap ná goedkeuring;
- geen velden voor USB-aansturing van het meettoestel (buiten scope v1).

---

## 11. Volgende stap

Ná bevestiging van dit document: `docs/validation_rules.md` uitwerken
(exacte formules, drempels, bewoording van waarschuwingen), gevolgd
door het doorlopen van de testgevallen uit §22 van de context tegen
dit model, vóór er databaseschema of code wordt geschreven.
