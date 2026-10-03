# Beperkingen van in-circuit condensatormetingen

In-circuit meten is snel en nuttig voor screening, maar parallelle circuitpaden kunnen C en ESR sterk beïnvloeden.

## Mogelijke parallelpaden

Onder andere:

- meerdere condensatoren parallel;
- keramische bypass-condensatoren;
- weerstanden;
- spoelen;
- transformatorwikkelingen;
- halfgeleiders;
- andere belastingen op dezelfde rail.

## ESR

### Duidelijk te hoog

Een duidelijk te hoge ESR in-circuit is verdacht. Parallelpaden maken de gemeten ESR meestal eerder lager dan hoger.

Praktische vervolgstap:

`te hoge ESR → één poot los → opnieuw meten`

### Normaal of laag

Een normale of lage ESR bewijst niet dat de individuele condensator goed is.

Mogelijke verklaringen:

- parallelle goede condensator;
- lage weerstand;
- kortgesloten component;
- andere lage impedantie op de rail.

## Capaciteit

Capaciteitsmeting in-circuit kan fout zijn door parallelle condensatoren, halfgeleiders en weerstanden. Een veel te hoge gemeten capaciteit is vaak een parallel-effect.

## Condensatorbanken

Bij parallelle banken:

- totale capaciteit is de som;
- totale ESR daalt;
- één slechte condensator kan gemaskeerd worden.

## Bevestigen

Wanneer de uitkomst belangrijk is of niet past bij het circuitgedrag, neem minstens één aansluiting los of bouw de component volledig uit en meet opnieuw onder bekende voorwaarden.



## Bronverantwoording per sectie

| Sectie | Bron-ID | Locator | Ondersteunt |
|---|---|---|---|
| Mogelijke parallelpaden | `master_02` | H6 | parallel_paths |
| ESR | `master_02` | H6 | masking; high_esr_confirmation |
| Capaciteit | `master_02` | H6 | parallel_capacitance |
| Condensatorbanken | `master_02` | H66 | capacitor_banks |
| Bevestigen | `master_02` | H6/H7 | confirm_one_leg; confirm_ex_situ |

### Bronregister

- `master_02` — `MASTER_02_CONDENSATOR_ESR_TECHNISCHE_REFERENTIE.md`. Interne technische projectreferentie; de locator hierboven geeft het relevante hoofdstuk of de projectregel aan.
