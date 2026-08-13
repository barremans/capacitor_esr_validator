<!--
Modulepad: capacitor_esr_validator/docs/validation_rules.md
Doel: Exacte formules, drempels en bewoording van waarschuwingen voor
      de beoordelingslogica (GOOD/MID/BAD-achtige eindstatus), vóór er
      code voor app/services/assessment_service.py wordt geschreven.
Referentie: PROJECT_CONTEXT_capacitor_ESR_validator.md §7-§19,
            functional_design_v1.md §6 (punten 3-8) en §8.
Status: ontwerpdocument, GEEN applicatiecode. Nog niet goedgekeurd.
        Onderdelen gemarkeerd [AANNAME] zijn voorstellen ter bevestiging,
        géén vaststaand ontwerp.
-->

# Validatieregels — Condensator- en ESR-validator (v1)

Alle grenswaarden in dit document zijn **configureerbaar** en worden
uit `app/config/settings.py` gelezen, nooit hardcoded in de
beoordelingslogica (§16 context, §21 context: "configureerbare
grensfactoren"). De hier vermelde getallen zijn de **defaults**.

---

## 1. Volgorde van beoordeling

Voor één meting gebeurt de beoordeling in deze vaste volgorde:

1. Referentiehiërarchie doorlopen → beste beschikbare referentiebron bepalen (§2)
2. Capaciteitsvalidatie (§3)
3. ESR-beoordeling t.o.v. de gekozen referentie (§4)
4. Interne C–ESR–D-consistentiecontrole als signaal (§5)
5. Betrouwbaarheid bepalen op basis van alle contextfactoren (§6)
6. Eindstatus samenstellen uit bovenstaande, met verplichte toelichting (§7)

Elke stap wordt vastgelegd (welke bron, welke formule, welk resultaat)
zodat het eindresultaat volledig transparant is (§18 context).

---

## 2. Referentiehiërarchie

Vaste volgorde, hoogste eerst (§7 context). De assessment-service
doorloopt deze lijst en gebruikt de **eerste** bron waarvoor geldige
data beschikbaar is voor het condensatortype/capaciteit/spanningsklasse:

1. Exacte fabrikantdatasheet van het juiste onderdeel → betrouwbaarheid `hoog`
2. Referentiemeting van een nieuw identiek exemplaar → `hoog`
3. Fabrikantgegevens voor dezelfde serie → `hoog`
4. Interne bedrijfstabel met gedocumenteerde bron → `middel`
5. Peak Atlas ESR70-look-uptabel → `middel`
6. Andere algemene ESR-cheatsheets (bv. Specap) → `laag`
7. Alleen relatieve vergelijking (§13 context) → `laag`, en de
   eindstatus kan dan nooit "waarschijnlijk goed" of "waarschijnlijk
   defect" zijn, hoogstens "aandachtspunt" of "niet te beoordelen"

Als geen enkel niveau bruikbare data oplevert: ESR-deelresultaat =
**niet te beoordelen**, met reden "geen geschikte referentie".

---

## 3. Capaciteitsvalidatie

Formule:

```
afwijking_percent = ((gemeten_capaciteit - nominale_capaciteit) / nominale_capaciteit) × 100
```

> Vóór deze berekening worden beide waarden omgezet naar dezelfde
> eenheid (bv. alles naar µF). Dit is **eenheidsconversie** (pF↔nF↔µF↔mF),
> geen frequentieconversie, en dus wél toegelaten — in tegenstelling
> tot ESR-frequentieconversie (§9 context), die nooit automatisch gebeurt.

Classificatie, met `tolerantie_percent` uit het component:

| Voorwaarde | Status |
|---|---|
| `tolerantie_percent` ontbreekt | **niet beoordeelbaar** |
| \|afwijking_percent\| ≤ tolerantie_percent × marge_binnen [AANNAME: marge_binnen = 0,9] | **binnen tolerantie** |
| tolerantie_percent × marge_binnen < \|afwijking_percent\| ≤ tolerantie_percent | **op grens** |
| \|afwijking_percent\| > tolerantie_percent | **buiten tolerantie** |

`marge_binnen` (default 0,9 = 90 % van de tolerantiegrens) is een
[AANNAME] om een "op grens"-zone te creëren vlak tegen de harde
tolerantiegrens aan; te bevestigen of aan te passen.

Elk resultaat toont: nominale waarde, gemeten waarde, absolute
afwijking, procentuele afwijking, gebruikte tolerantie — nooit enkel
het label (§11 context).

---

## 4. Indicatieve ESR-beoordeling

**Alleen** wanneer geen exacte datasheetwaarde met gelijke frequentie
beschikbaar is (referentieniveau 1), wordt een algemene referentie
gebruikt (§12 context).

Verhouding:

```
factor = gemeten_ESR / referentie_ESR
```

> Beide waarden moeten in dezelfde eenheid staan (mΩ of Ω) — expliciete
> eenheidsconversie is toegelaten, dit is geen frequentieconversie.

Classificatie (defaults uit `settings.py`, exact zoals §12 context):

| Verhouding | Status |
|---|---|
| factor ≤ 1,0 | waarschijnlijk normaal |
| 1,0 < factor ≤ 2,0 | aandachtspunt |
| 2,0 < factor ≤ 3,0 | verdacht |
| factor > 3,0 | waarschijnlijk defect |

Deze vier drempels (1,0 / 2,0 / 3,0) zijn configureerbaar en worden
**nooit** als universele norm gepresenteerd — de UI en export tonen
altijd erbij welke referentiebron en -frequentie gebruikt zijn.

Als `meetfrequentie` (meetcontext) ≠ `frequentie` van de gebruikte
referentieregel: verplichte waarschuwing tonen (§9 context) en
betrouwbaarheid verlagen (zie §6). **Geen automatische omrekening.**

---

## 5. Interne C–ESR–D-consistentiecontrole (signaal, geen afkeurregel)

Enkel wanneer C, ESR én D voor dezelfde meting/frequentie beschikbaar zijn:

```
D_verwacht ≈ 2 × π × f × C × ESR_gemeten
```

of, omgekeerd, als plausibiliteitscheck op ESR:

```
ESR_verwacht ≈ D_gemeten / (2 × π × f × C)
```

Vergelijk `ESR_verwacht` met `ESR_gemeten`:

```
consistentie_factor = ESR_gemeten / ESR_verwacht   (of omgekeerd, grootste/kleinste)
```

| Voorwaarde | Signaal |
|---|---|
| 1/consistentie_marge ≤ consistentie_factor ≤ consistentie_marge [AANNAME: consistentie_marge = 2,0] | consistent — geen signaal |
| consistentie_factor buiten die marge, maar < 100 | **mogelijke inconsistentie** — waarschuwing, reden vermelden (bv. "mogelijke mΩ/Ω-verwisseling of foutieve frequentie") |
| consistentie_factor ≥ ~100 (grootteorde 1000 mogelijk) | **sterke aanwijzing voor eenhedenfout** (bv. mF i.p.v. µF, testgeval 13) — expliciete waarschuwing, geen automatische correctie |

`consistentie_marge` (default 2,0) is **[AANNAME]** — dit is open
vraag 13 uit de context/functional design ("welke foutmarge is
aanvaardbaar"), nog niet beantwoord. Voorlopig conservatief ingesteld
en configureerbaar.

Dit signaal beïnvloedt **nooit** rechtstreeks de eindstatus als
"defect" — het verlaagt hoogstens de betrouwbaarheid en wordt getoond
als aandachtspunt (§10 context: "geen universele goed/afkeurregel").

---

## 6. Betrouwbaarheid bepalen

Start op `hoog` (bepaald door het referentieniveau, §2). Verlaag met
één niveau (hoog→middel, middel→laag) voor **elke** van deze
voorwaarden die van toepassing is (§12 context, cumulatief tot
minimum `laag`):

- referentiefrequentie ≠ meetfrequentie;
- omgevingstemperatuur onbekend;
- condensatortype onbekend of "Anders";
- meting is in-circuit;
- gebruikte referentieregel is `typisch` (geen maximumwaarde);
- fabrikant en/of serie onbekend (bij component én bij referentieregel);
- mogelijke inconsistentie gesignaleerd (§5).

In-circuit metingen krijgen dus per definitie een lagere betrouwbaarheid
dan uitgebouwde metingen of metingen met één losgenomen aansluiting
(§4 en §26 context).

---

## 7. Eindstatus (§17 context)

De eindstatus wordt samengesteld uit capaciteitsstatus (§3),
ESR-status (§4), consistentiesignaal (§5) en betrouwbaarheid (§6).
Onderstaande matrix is een **[AANNAME]**-voorstel — combinatielogica
stond nog niet expliciet in de context en moet bevestigd worden vóór
implementatie:

| Voorwaarde | Eindstatus |
|---|---|
| invoer onvolledig / geen meting gestart | **niet beoordeeld** |
| capaciteit "niet beoordeelbaar" OF ESR "niet te beoordelen" OF condensatortype onbekend OF veiligheidsbevestiging ontbreekt zonder reden | **niet te beoordelen** |
| capaciteit "binnen tolerantie" EN ESR "waarschijnlijk normaal" EN geen sterke inconsistentie EN betrouwbaarheid ≥ middel | **waarschijnlijk goed** |
| capaciteit "op grens" OF ESR "aandachtspunt" OF betrouwbaarheid "laag" (zonder verdere alarmsignalen) | **aandachtspunt** |
| capaciteit "buiten tolerantie" OF ESR "verdacht" OF mogelijke inconsistentie (§5) OF sterke in-circuit-twijfel | **twijfelachtig** |
| ESR "waarschijnlijk defect" tegenover betrouwbaarheid ≥ middel, OF capaciteit sterk buiten tolerantie mét bevestigde open verbinding/kortsluiting, OF ≥2 onafhankelijke criteria wijzen op defect | **waarschijnlijk defect** |

Bij twijfel tussen twee niveaus kiest de logica altijd het
**voorzichtigste** (lagere) niveau — nooit optimistisch afronden.

Elk eindresultaat toont verplicht (§18 context, letterlijk over te
nemen als velden in het resultaatscherm/export):

- gemeten waarden (ruw, zoals ingevoerd);
- nominale waarden;
- gebruikte bron (referentieniveau + naam);
- gebruikte grenswaarde(n);
- meetfrequentie;
- referentiefrequentie;
- berekende afwijkingen (capaciteit % en ESR-factor);
- waarschuwingen (frequentieverschil, in-circuit, onbekend type, ...);
- betrouwbaarheid (hoog/middel/laag) + welke factoren die verlaagd hebben;
- reden(en) voor de status (verwijzing naar welke regel(s) hierboven getriggerd zijn);
- aanbevolen vervolgstap (tekst, bv. "vergelijk met identiek nieuw exemplaar" of "raadpleeg datasheet").

**Nooit** een "goed" of "slecht" label zonder deze onderbouwing.

---

## 8. V-Loss

V-Loss heeft **geen enkele rol** in bovenstaande regels. Het wordt
opgeslagen (zie `data_model.md` §6.1) en getoond, maar nooit gebruikt
in een berekening, drempel of statusbepaling, zolang de betekenis niet
bevestigd is (§6 context).

---

## 9. Manuele override [OPEN — §9 vraag 14-15 fd, nog te bevestigen]

Voorstel, nog niet definitief: een gebruiker kan de automatische
eindstatus overrulen, maar enkel met een verplicht ingevuld
reden-/commentaarveld, en de override wordt apart gelogd (wie, wanneer,
van welke status naar welke status, waarom) zonder de automatische
beoordeling te overschrijven — beide blijven zichtbaar. Dit wordt pas
in het gegevensmodel/databaseschema verwerkt na bevestiging.

---

## 10. Vaste veiligheidswaarschuwingen (§19 context, letterlijk te tonen)

Op elk scherm met meetinvoer of -resultaat, minstens:

- meet nooit aan een onder spanning staande schakeling;
- controleer afwezigheid van spanning met een geschikt meetinstrument;
- ontlaad de condensator gecontroleerd;
- grote condensatoren kunnen opnieuw spanning opbouwen;
- in-circuit metingen kunnen foutief zijn;
- neem bij twijfel één aansluiting los;
- een LCR-meting test niet automatisch lekstroom, isolatie of doorslagspanning;
- een goede ESR-waarde bewijst niet dat de condensator veilig is op nominale spanning;
- de app is geen formele veiligheidsvrijgave.

---

## 11. Samenvatting configureerbare parameters (→ `app/config/settings.py`)

| Parameter | Default | Bron |
|---|---|---|
| `esr_factor_normaal` | 1,0 | §12 context |
| `esr_factor_aandachtspunt` | 2,0 | §12 context |
| `esr_factor_verdacht` | 3,0 | §12 context |
| `capaciteit_marge_binnen` | 0,9 | [AANNAME] |
| `consistentie_marge` | 2,0 | [AANNAME], open vraag 13 |
| `consistentie_eenhedenfout_drempel` | 100 | [AANNAME] |

---

## 12. Volgende stap

Ná bevestiging van dit document en `data_model.md`: de testgevallen
uit §22 van de context (20 gevallen) stuk voor stuk doorrekenen tegen
deze regels om hiaten te vinden, vóór er databaseschema of
`assessment_service.py`-code wordt geschreven.
