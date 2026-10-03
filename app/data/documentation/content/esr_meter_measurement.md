# ESR meten met een ESR-meter

Een ESR-meter is vooral bruikbaar voor aluminium elektrolytische condensatoren, low-ESR-types en een eerste in-circuit screening.

## Voor je meet

- Maak de schakeling spanningsloos.
- Ontlaad de condensator gecontroleerd en verifieer opnieuw de spanning.
- Noteer de meetmethode: `EX_SITU`, `ONE_LEG` of `IN_CIRCUIT`.
- Controleer de testfrequentie van het instrument.
- Controleer de testspanning of het testsignaal van het instrument.
- Gebruik bij zeer lage ESR geschikte probes; kabel- en contactweerstand kunnen de meting domineren.

## Tijdens de meting

Let op:

- meetfrequentie;
- testspanning;
- instrumentresolutie;
- contactweerstand;
- parallelpaden in de schakeling.

Een instrumentresolutie van `0,01 Ω` kan bijvoorbeeld waarden van enkele milliohm niet betrouwbaar van elkaar onderscheiden.

## In-circuit interpretatie

Een duidelijk te hoge ESR in-circuit is betekenisvol en moet worden bevestigd door minstens één aansluiting los te nemen.

Een lage ESR is **niet automatisch bewijs dat de condensator goed is**. Een parallelle goede condensator, lage weerstand, kortsluiting of andere railimpedantie kan de gemeten ESR verlagen.

## Vergelijken met een referentie

Vergelijk de meetwaarde alleen met een passende referentie. Vergelijk bijvoorbeeld niet rechtstreeks `ESR @ 1 kHz` met `ESR max @ 100 kHz` zonder geldige frequentiekarakteristiek.



## Bronverantwoording per sectie

| Sectie | Bron-ID | Locator | Ondersteunt |
|---|---|---|---|
| Voor je meet | `master_02` | H5/H58 | frequency; test_signal; probes |
| Tijdens de meting | `master_02` | H58–61 | resolution; contact_resistance |
| In-circuit interpretatie | `master_02` | H6 | parallel_paths; masking |
| Vergelijken met een referentie | `master_02` | H9/H61 | frequency_context; no_hidden_conversion |

### Bronregister

- `master_02` — `MASTER_02_CONDENSATOR_ESR_TECHNISCHE_REFERENTIE.md`. Interne technische projectreferentie; de locator hierboven geeft het relevante hoofdstuk of de projectregel aan.
