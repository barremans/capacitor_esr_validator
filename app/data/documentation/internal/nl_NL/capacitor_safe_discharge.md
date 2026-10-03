# Condensator veilig ontladen vóór meting

> Interne meetinstructie. Geen formele veiligheidsvrijgave.

Een condensator kan geladen blijven nadat een toestel is uitgeschakeld. De opgeslagen energie volgt uit:

`E = 1/2 × C × V²`

waar `E` in joule, `C` in farad en `V` in volt wordt uitgedrukt.

## Vaste volgorde vóór ESR-, LCR- of ohmmeting

1. Schakel het toestel uit.
2. Ontkoppel alle voedingen.
3. Wacht indien het toestel interne ontlaadcircuits heeft.
4. Meet de resterende spanning met een geschikt meetinstrument.
5. Ontlaad gecontroleerd via een geschikte weerstand.
6. Controleer de spanning opnieuw.
7. Start pas daarna de ESR-, LCR- of ohmmeting.

## Niet doen

- Kort een geladen elco niet rechtstreeks met gereedschap.
- Raak een onbekende hoogspanningscondensator niet aan.
- Voer geen leakage-test uit zonder stroombegrenzing.
- Keer de polariteit van gepolariseerde condensatoren niet om.
- Vervang safety-condensatoren niet door gewone condensatoren.

## Extra aandacht

Grote condensatoren kunnen na het ontladen opnieuw spanning opbouwen. Controleer daarom opnieuw vóór je de aansluitingen aanraakt of de meetopstelling wijzigt.



## Bronverantwoording per sectie

| Sectie | Bron-ID | Locator | Ondersteunt |
|---|---|---|---|
| Vaste volgorde vóór ESR-, LCR- of ohmmeting | `master_02` | H1 | power_off; discharge_resistor; recheck_voltage |
| Niet doen | `master_02` | H1 | safe_discharge; polarity; safety_capacitors |
| Extra aandacht | `master_02` | H1 | rebound_voltage |

### Bronregister

- `master_02` — `MASTER_02_CONDENSATOR_ESR_TECHNISCHE_REFERENTIE.md`. Interne technische projectreferentie; de locator hierboven geeft het relevante hoofdstuk of de projectregel aan.
