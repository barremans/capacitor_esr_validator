# C–ESR–D plausibiliteitscontrole

Capaciteit `C`, ESR en dissipatiefactor `D` beschrijven niet exact hetzelfde, maar kunnen samen worden gebruikt om invoer- of meetproblemen te signaleren.

Voor een passend seriesmodel:

`ESR ≈ D / (2πfC)`

waar `D = tanδ`.

## Doel van de controle

De controle is bedoeld om te vragen:

> Zijn de ingevoerde C, ESR, D en frequentie onderling plausibel?

Een sterke afwijking kan wijzen op:

- verwisseling van `mΩ` en `Ω`;
- verkeerde capaciteitseenheid;
- verkeerde meetfrequentie;
- verkeerd series/parallel model;
- afronding;
- beïnvloeding door de schakeling;
- onjuiste of instabiele meting.

## Werkwijze bij inconsistentie

1. Controleer capaciteit en eenheid.
2. Controleer ESR en eenheid.
3. Controleer de werkelijk gebruikte frequentie.
4. Controleer het LCR-model.
5. Herhaal open/short-calibratie indien van toepassing.
6. Herhaal de meting met een betrouwbaardere fysieke opstelling.

## Belangrijk

Gebruik deze relatie niet als automatische correctie van een gemeten waarde. Een inconsistentie is een signaal om de meting te controleren.



## Bronverantwoording per sectie

| Sectie | Bron-ID | Locator | Ondersteunt |
|---|---|---|---|
| Doel van de controle | `master_02` | H3.7 | C_ESR_D_consistency |
| Werkwijze bij inconsistentie | `master_02` | H3.7/H63–65 | units; frequency; model; calibration |
| Belangrijk | `master_02` | projectregel | no_auto_correction |

### Bronregister

- `master_02` — `MASTER_02_CONDENSATOR_ESR_TECHNISCHE_REFERENTIE.md`. Interne technische projectreferentie; de locator hierboven geeft het relevante hoofdstuk of de projectregel aan.
