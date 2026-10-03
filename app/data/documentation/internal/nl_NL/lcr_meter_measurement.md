# ESR en capaciteit meten met een LCR-meter

Een LCR-meter kan onder meer `C`, `ESR`, `D`, `Q`, `tanδ` en impedantie meten. Het resultaat is alleen bruikbaar wanneer meetmodel en meetvoorwaarden passen bij de component en de referentie.

## Voorbereiding

1. Maak de schakeling spanningsloos en ontlaad de condensator.
2. Kies de fysieke meetmethode: bij voorkeur uit circuit voor een definitieve beoordeling.
3. Voer open/short-calibratie uit volgens het instrument.
4. Houd meetsnoeren kort; gebruik Kelvin/4-wire waar lage ESR dit vereist.
5. Noteer temperatuur en meetfrequentie.

## Instellingen

Controleer:

- de juiste meetfrequentie;
- het AC-testniveau/testspanning;
- series- of parallelmodel (`Cs/Rs` of `Cp/Rp`);
- dezelfde meetvoorwaarden als de datasheet wanneer je met een fabrikantlimiet vergelijkt.

## Interpretatie

Een LCR-meting test niet automatisch:

- leakage current;
- isolatieweerstand;
- doorslagspanning;
- gedrag onder nominale DC-spanning.

Een goede ESR- of capaciteitswaarde alleen bewijst dus niet dat de condensator in alle opzichten goed of veilig is.

## Bij afwijkingen

Wanneer C, ESR en D onderling niet plausibel zijn:

- controleer eenheden;
- controleer frequentie;
- controleer series/parallel model;
- herhaal de kalibratie;
- meet indien mogelijk uit circuit.



## Bronverantwoording per sectie

| Sectie | Bron-ID | Locator | Ondersteunt |
|---|---|---|---|
| Voorbereiding | `master_02` | H58/H63–65 | open_short_calibration; probes |
| Instellingen | `master_02` | H36/H63 | series_parallel_model; frequency; test_level |
| Interpretatie | `master_02` | H5/H36 | measurement_scope; limitations |
| Bij afwijkingen | `master_02` | H3.7/H63–65 | C_ESR_D_consistency; calibration |

### Bronregister

- `master_02` — `MASTER_02_CONDENSATOR_ESR_TECHNISCHE_REFERENTIE.md`. Interne technische projectreferentie; de locator hierboven geeft het relevante hoofdstuk of de projectregel aan.
