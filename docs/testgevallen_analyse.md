<!--
Modulepad: capacitor_esr_validator/docs/testgevallen_analyse.md
Doel: De 20 testgevallen uit PROJECT_CONTEXT_capacitor_ESR_validator.md
      §22 doorrekenen tegen data_model.md en validation_rules.md, om
      hiaten te vinden vóór er databaseschema of code wordt geschreven.
Referentie: PROJECT_CONTEXT_capacitor_ESR_validator.md §22.
Status: analysedocument, GEEN applicatiecode. Basis voor bijsturing van
        data_model.md / validation_rules.md indien nodig.
-->

# Testgevallen-analyse (§22 context) t.o.v. het huidige ontwerp

Legende: ✅ gedekt door huidig model/regels — ⚠️ gedekt maar met een
kanttekening — ❌ hiaat, moet aangepast worden.

---

**1. 470 µF ingevoerd als 0,47 mF.**
✅ `eenheid_capaciteit` is een keuzelijst (pF/nF/µF/mF), geen vrije
tekst. Capaciteitsvalidatie (validation_rules §3) rekent expliciet om
naar één eenheid vóór vergelijking. Consistentiecontrole (§5) zou dit
bovendien signaleren als factor ~1000 tussen verwachte en gemeten ESR
optreedt bij een gekoppelde eenhedenfout.

**2. ESR ingevoerd in mΩ en Ω.**
✅ `eenheid_gemeten_ESR` is verplichte keuzelijst (mΩ/Ω). ESR-vergelijking
(§4) rekent expliciet om naar dezelfde eenheid als de referentie.

**3. Komma en punt als decimaalteken.**
✅ Alle `getal`-velden in data_model.md vermelden expliciet "komma of
punt toegelaten als invoer, intern omgezet naar float".

**4. Capaciteit exact op tolerantielimiet.**
⚠️ Gedekt door validation_rules §3, maar de grens tussen "op grens" en
"buiten tolerantie" ligt nu bij precies `tolerantie_percent` (100%).
Bij exact op de limiet valt dit in "op grens" (want `≤ tolerantie_percent`
grenst niet naar buiten tolerantie totdat je hem overschrijdt) —
correct, maar dit randgeval (`==`) moet als expliciete unittest worden
opgenomen zodra we bij `tests/` zijn, om afrondingsfouten met floats
te vangen.

**5. Capaciteit buiten tolerantie.**
✅ Gedekt, §3.

**6. Datasheetwaarde met gelijke frequentie.**
✅ Referentiehiërarchie niveau 1 (§2), betrouwbaarheid `hoog`, geen
frequentiewaarschuwing nodig.

**7. Datasheetwaarde met andere frequentie.**
✅ Gedekt: §4 verplicht een waarschuwing en §6 verlaagt betrouwbaarheid
bij `referentiefrequentie ≠ meetfrequentie`, ongeacht referentieniveau.

**8. Algemene ESR-cheatsheet gebruikt.**
✅ Referentieniveau 5/6 (§2), betrouwbaarheid start al op `middel`/`laag`.

**9. In-circuit meting.**
✅ `in_circuit` boolean in meetcontext; §6 verlaagt betrouwbaarheid
altijd bij in-circuit, ongeacht andere factoren.

**10. Meting met één aansluiting los.**
⚠️ `een_aansluiting_los` is aanwezig in data_model.md, maar
validation_rules.md §6 verlaagt betrouwbaarheid nu alleen expliciet
bij `in_circuit`. Er is **geen aparte regel** die "één aansluiting los"
als hogere betrouwbaarheid dan volledig in-circuit behandelt, terwijl
§13 context dit wél als tussenstap in de relatieve-validatiehiërarchie
ziet. **Hiaat** → toe te voegen aan validation_rules.md: `een_aansluiting_los`
telt niet mee als extra verlaging (het is al beter dan zuiver in-circuit),
maar `volledig_uitgebouwd` zonder `een_aansluiting_los` of `in_circuit`
is het meest betrouwbare geval. Voorstel: expliciete opsomming van de
drie meetopstellingen met elk hun eigen effect, i.p.v. enkel een
in-circuit-vlag.

**11. Verschillende resultaten op 100 Hz, 1 kHz en 10 kHz.**
✅ Elke frequentie = apart Meting-record (data_model §6), dus geen
overschrijven. ⚠️ Er is nog **geen regel** die meerdere metingen van
hetzelfde component op verschillende frequenties onderling vergelijkt
of samenvat (bv. trend/consistentie tussen frequenties). Dat staat wel
in functional_design §4 punt 5 ("Componentgeschiedenis... per
frequentie, met trend") maar niet in validation_rules.md. **Hiaat**,
maar mag voor v1 beperkt blijven tot weergave (geschiedenisscherm),
niet per se extra beoordelingslogica — te bevestigen.

**12. C, ESR en D die onderling ongeveer kloppen.**
✅ Consistentiecontrole §5, factor binnen marge → "consistent, geen
signaal".

**13. C, ESR en D met een factor-1000-eenhedenfout.**
✅ §5 dekt dit expliciet met de `consistentie_eenhedenfout_drempel`
(default 100) als aparte, sterkere waarschuwingsklasse.

**14. Geen V-Loss ingevoerd.**
✅ V-Loss optioneel, geen enkele regel vereist het (§6.1 data_model, §8
validation_rules).

**15. V-Loss met onbekende betekenis.**
✅ `V_Loss_eenheid` kent expliciet de waarde "onbekend"; blijft
ongebruikt in beoordeling.

**16. Polymercondensator waarvoor een elektrolytische tabel wordt gekozen.**
⚠️ `condensatortype` = "Anders" toont een waarschuwing (data_model §4),
maar validation_rules.md verbiedt nergens **expliciet** dat een
elektrolytische referentieregel toch gekozen wordt voor een
"Anders"-type. **Hiaat** → toe te voegen aan §2 (referentiehiërarchie):
als `condensatortype` van de Referentieregel niet overeenkomt met dat
van het Component, mag deze referentie niet automatisch voorgesteld
worden; enkel manueel te kiezen, met een verplichte extra waarschuwing
en betrouwbaarheid nooit hoger dan `laag`.

**17. Waarde buiten meetbereik.**
❌ **Hiaat**: geen enkel veld of regel behandelt momenteel "waarde
buiten toestelbereik" (het TEKCOPLUS-bereik is nog niet vastgelegd,
open vraag 1 context). §17 context noemt dit expliciet als reden voor
"niet te beoordelen". Voorstel: een optioneel veld
`meetwaarde_buiten_bereik` (boolean, door gebruiker aan te vinken bij
overflow/onderloop-indicatie op het toestel), dat automatisch tot
eindstatus "niet te beoordelen" leidt. Toe te voegen aan data_model.md
§6 en validation_rules.md §7.

**18. Ontbrekende referentiefrequentie.**
✅ data_model.md maakt `datasheet_referentiefrequentie` verplicht zodra
`datasheet_esr_of_impedantie` is ingevuld; voor externe referentieregels
is `frequentie` sowieso verplicht (§7 data_model). Zonder frequentie
kan de referentie dus niet bruikbaar zijn → valt terug op volgend
hiërarchieniveau of "niet te beoordelen".

**19. Referentiecomponent met bekende serieweerstand.**
⚠️ Dit betreft de functionele toestelcontrole uit §14 context (precisie-
weerstand in serie plaatsen om de ESR-meting zelf te verifiëren), niet
de beoordeling van een gebruikerscomponent. Dit zit **niet** in het
huidige gegevensmodel — het is een apart concept ("toestelverificatie"),
geen Component/Meting in de normale zin. **Hiaat, bewust uitgesteld**:
dit is functioneel nuttig maar niet strikt nodig voor v1-kernscope
(§21 context noemt het niet expliciet in de v1-lijst). Voorstel: niet
in v1-datamodel opnemen, wel vermelden als toekomstige uitbreiding.

**20. Export en herimport zonder gegevensverlies.**
⚠️ Geen specifiek hiaat in het gegevensmodel zelf (alle velden zijn
expliciet getypeerd), maar er is nog **geen vastgelegd exportformaat**
(kolomvolgorde, welke velden wel/niet in CSV/Excel, hoe de
referentie-snapshot uit §8 data_model wordt meegenomen). Dat hoort
thuis in een apart, later te schrijven `docs/export_format.md`, niet
in dit document — voorlopig genoteerd als openstaand.

---

## Samenvatting hiaten om op te lossen vóór databaseschema

| # | Hiaat | Actie |
|---|---|---|
| 10 | Geen aparte betrouwbaarheidsregel voor "één aansluiting los" t.o.v. in-circuit/uitgebouwd | validation_rules.md §6 uitbreiden met drie niveaus i.p.v. één in-circuit-vlag |
| 11 | Geen regel voor vergelijking/trend tussen frequenties van hetzelfde component | Beperken tot weergave in v1 (geschiedenisscherm), geen extra beoordelingslogica — te bevestigen |
| 16 | Geen verbod op automatisch kiezen van een referentie met ander condensatortype | validation_rules.md §2 uitbreiden met een expliciete type-matchregel |
| 17 | Geen veld/regel voor "waarde buiten meetbereik" | data_model.md §6 + validation_rules.md §7 uitbreiden |
| 19 | Toestelverificatie met bekende serieweerstand niet in datamodel | Bewust uitstellen naar latere versie, expliciet vermelden in "niet in scope" |
| 20 | Exportformaat nog niet vastgelegd | Apart document `docs/export_format.md`, later, niet blokkerend voor databaseschema |

Geen van deze hiaten is blokkerend voor het opstellen van een eerste
databaseschema — punten 10, 16 en 17 zijn wel klein genoeg om **vóór**
het schema te verwerken in de twee bestaande documenten, zodat het
schema er meteen rekening mee houdt. Punten 11, 19 en 20 kunnen later.

---

## Voorgestelde volgende stap

1. `data_model.md` en `validation_rules.md` bijwerken met de oplossingen
   voor hiaten 10, 16 en 17 hierboven (kleine aanvullingen, geen
   herontwerp).
2. Pas daarna: databaseschema (tabellen, kolommen, sleutels) opstellen
   als volgende apart document, vóór er `app/services/storage_service.py`
   of ander code wordt geschreven.
