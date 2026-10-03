# Meetfrequentie en testniveau kiezen

ESR, impedantie en sommige capaciteitsmetingen zijn afhankelijk van de meetvoorwaarden.

## Meetfrequentie

Noteer altijd de frequentie.

Een ESR-waarde mag niet zonder onderbouwde frequentiekarakteristiek rechtstreeks met een limiet op een andere frequentie worden vergeleken.

Voorbeeld:

`ESR @ 1 kHz` is niet automatisch vergelijkbaar met `ESR max @ 100 kHz`.

Gebruik bij voorkeur dezelfde frequentie als de datasheet of de referentiebron.

## AC-testniveau / testspanning

Volg voor karakterisering de testvoorwaarden uit de datasheet en de mogelijkheden van het instrument.

Voor bepaalde condensatortechnologieën kan de gemeten capaciteit afhankelijk zijn van het AC-testniveau. Een meetresultaat zonder passende testconditie hoeft daarom niet representatief te zijn voor de datasheetwaarde.

## Geen verborgen correcties

Wanneer meet- en referentiefrequentie verschillen:

- noteer het verschil;
- voer geen automatische omrekening uit zonder gevalideerd model of fabrikantcurve;
- behandel de vergelijking als contextafhankelijk.

## Praktische registratie

Noteer minstens:

- instrument;
- meetfrequentie;
- testniveau/testspanning;
- meetmethode;
- temperatuur wanneer relevant.



## Bronverantwoording per sectie

| Sectie | Bron-ID | Locator | Ondersteunt |
|---|---|---|---|
| Meetfrequentie | `master_02` | H9/H61 | frequency_context; no_hidden_conversion |
| AC-testniveau / testspanning | `master_02` | H58/H63 | test_level; datasheet_conditions |
| Geen verborgen correcties | `master_02` | H9 | no_hidden_conversion |
| Praktische registratie | `master_02` | H58/H63 | traceable_conditions |

### Bronregister

- `master_02` — `MASTER_02_CONDENSATOR_ESR_TECHNISCHE_REFERENTIE.md`. Interne technische projectreferentie; de locator hierboven geeft het relevante hoofdstuk of de projectregel aan.
