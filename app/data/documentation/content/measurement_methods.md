# Meetmethoden: EX_SITU, ONE_LEG en IN_CIRCUIT

De fysieke meetopstelling bepaalt sterk hoeveel vertrouwen je aan C- en ESR-metingen kunt geven.

## EX_SITU — volledig uitgebouwd

De condensator is volledig geïsoleerd van de schakeling.

Voordelen:

- parallelpaden zijn verwijderd;
- capaciteit, ESR en D zijn beter aan één component toe te schrijven;
- dit is doorgaans de beste opstelling voor een definitieve beoordeling.

## ONE_LEG — één aansluiting los

Eén aansluiting van de condensator is losgenomen.

Dit is een goede praktische tussenstap:

- veel parallelpaden worden onderbroken;
- minder soldeerwerk dan volledig uitbouwen;
- betrouwbaarder dan volledig in-circuit;
- nog steeds contextafhankelijk.

## IN_CIRCUIT — volledig in de schakeling

Voordelen:

- snel;
- weinig soldeerwerk;
- bruikbaar als eerste screening.

Beperkingen:

- parallelle condensatoren, weerstanden, spoelen, transformatorwikkelingen en halfgeleiders kunnen de meting beïnvloeden;
- een lage ESR kan gemaskeerd worden door parallelpaden;
- een veel te hoge gemeten capaciteit kan een parallel-effect zijn.

## Praktische keuze

Gebruik in-circuit als screening wanneer dat zinvol is. Is ESR duidelijk te hoog of is de meting twijfelachtig, neem dan minstens één aansluiting los en meet opnieuw. Gebruik voor een definitieve beoordeling bij voorkeur een geïsoleerde component.



## Bronverantwoording per sectie

| Sectie | Bron-ID | Locator | Ondersteunt |
|---|---|---|---|
| EX_SITU | `master_02` | H6/H7 | isolated_component; reliability |
| ONE_LEG | `master_02` | H6/H7 | parallel_paths_reduced |
| IN_CIRCUIT | `master_02` | H6 | screening; parallel_paths |
| Praktische keuze | `master_02` | H6/H7 | confirm_one_leg; confirm_ex_situ |

### Bronregister

- `master_02` — `MASTER_02_CONDENSATOR_ESR_TECHNISCHE_REFERENTIE.md`. Interne technische projectreferentie; de locator hierboven geeft het relevante hoofdstuk of de projectregel aan.
