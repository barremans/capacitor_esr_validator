# Markdown-levering — projectstandaard

**Versie:** 1.0.0  
**Datum:** 2026-10-13  
**Auteur:** Bart Bossuyt  
**Doel:** Vastleggen hoe `.md`-bestanden geleverd worden in een chat, zodat de Markdown-opmaak nooit halverwege omschakelt naar gewone tekst.

---

## 1. Waarom deze afspraak

Wanneer een `.md`-bestand in een chat geleverd wordt, wordt het vaak in een omhullend codeblok geplaatst zodat de lezer het als één blok kan kopiëren. Dat omhullende codeblok gebruikt zelf backticks.

Als het bestand **zelf ook codeblokken bevat** (bijvoorbeeld ` ```powershell ` of ` ```python `, zonder de spaties), dan kan een interne codeblokafsluiting het omhullende blok voortijdig beëindigen wanneer de afbakening onvoldoende lang is.

Het gevolg: de rest van het bestand wordt niet langer als één samenhangend codeblok weergegeven. Later kan de weergave opnieuw naar een codeblok omschakelen. Dat geeft een ongewenste mengeling van opgemaakte Markdown en gewone tekst.

Deze afspraak voorkomt dat.

---

## 2. De regel in één zin

> **Bevat een `.md`-bestand zelf codeblokken met driedubbele backticks, lever het dan in viervoudige backticks. Anders mogen driedubbele backticks.**

---

## 3. Wanneer geldt de regel

De regel geldt bij **elk `.md`-bestand dat in een chat geleverd wordt**, ongeacht of het een nieuw bestand is of een bijgewerkte versie.

De regel geldt **niet** voor Python-bestanden, JSON-bestanden of andere bestanden zonder Markdown-opmaak. Daarvoor blijven de gewone regels van kracht (volledige bestanden, geen secties met `# ... ongewijzigd ...`).

---

## 4. Hoe je het toepast

**Stap 1 — Kijk of het `.md`-bestand zelf driedubbele backticks bevat.**

Zoek in de inhoud naar regels die met drie backticks beginnen. Dat zijn doorgaans de grenzen van codeblokken.

**Stap 2 — Kies het juiste omhullende blok.**

| Situatie | Omhullend blok |
|---|---|
| Het bestand bevat **geen** driedubbele backticks | Driedubbele backticks: een opening met `markdown` als taal en een afsluiting met drie backticks |
| Het bestand bevat **wel** driedubbele backticks | Viervoudige backticks: een opening met `markdown` als taal en een afsluiting met vier backticks |

**Stap 3 — Controleer vóór het verzenden.**

Lees de eerste en de laatste regel van je levering. Ze moeten hetzelfde aantal backticks hebben als het gekozen omhullende blok. Bij viervoudig: vier aan het begin, vier aan het einde, en de taal (`markdown`) direct na de opening.

---

## 5. Voorbeeld — goed

Het bestand bevat een codeblok. Daarom wordt het in **viervoudige** backticks geleverd.

````markdown
# Titel van het bestand

Hier wat uitleg.

```powershell
pytest -q
```

Nog wat uitleg.
````

In de chat ziet de lezer dit als één samenhangend codeblok. De driedubbele backticks binnenin blijven intact.

---

## 6. Voorbeeld — fout

Hetzelfde bestand, maar geleverd in **driedubbele** backticks. Het volgende voorbeeld staat ter illustratie in een langer omhullend blok zodat de fout zichtbaar blijft zonder dit document zelf te beschadigen:

````text
```markdown
# Titel van het bestand

Hier wat uitleg.

```powershell
pytest -q
```

Nog wat uitleg.
```
````

Wat er gebeurt bij zo'n onjuiste levering:

- De eerste drie backticks openen het omhullende blok.
- De drie backticks vóór `powershell` sluiten dat omhullende blok voortijdig.
- Vanaf dat punt wordt de rest buiten het bedoelde omhullende blok weergegeven.
- Volgende backtickregels kunnen de weergave opnieuw doen omschakelen.

Het resultaat is de mengeling van Markdown en gewone tekst die deze afspraak wil voorkomen.

---

## 7. Controlelijst vóór het leveren

Loop deze vier punten na voordat je een `.md`-bestand in de chat zet:

1. **Bevat het bestand driedubbele backticks?** Ja → ga door naar punt 2. Nee → gebruik driedubbele backticks en stop.
2. **Gebruik viervoudige backticks** als omhullend blok.
3. **Controleer het eerste en laatste backtick-blok** van je levering: ze moeten beide vier backticks hebben.
4. **Controleer dat er niets tussen het omhullende blok en het bestand staat** — geen commentaar, geen uitleg, geen extra sectie. Het omhullende blok bevat precies de inhoud van het bestand.

---

## 8. Wat te doen bij twijfel

**Gebruik altijd viervoudige backticks.** Het werkt ook wanneer het bestand geen codeblokken bevat. Het is alleen iets meer typwerk.

De omgekeerde fout (driedubbele backticks gebruiken terwijl het bestand zelf codeblokken heeft) is de fout die deze afspraak wil voorkomen. Bij twijfel is viervoudig dus altijd de veilige keuze.

---

## 9. Meerdere `.md`-bestanden in één levering

Wanneer je meerdere `.md`-bestanden in één bericht levert, krijgt elk bestand zijn **eigen** omhullend blok. Bijvoorbeeld:

````markdown
# Bestand 1

Inhoud van bestand 1.
````

````markdown
# Bestand 2

Inhoud van bestand 2.
````

Niet twee bestanden in één omhullend blok. Elk bestand apart, zodat de lezer elk blok afzonderlijk kan kopiëren.

---

## 10. Verwante afspraken

- **Volledige bestanden leveren, nooit secties met `# ... ongewijzigd ...`** staat in `overdracht.md`, secties 3.1 en 9.
- **JSON altijd volledig leveren, nooit fragmenten** staat in `overdracht.md`, secties 3.1 en 9.
- **Python-headers zijn cumulatief** staat in `docs/python_header_standard.md`.

Deze afspraak vult die regels aan: het gaat niet over *wat* je levert, maar over *hoe* je het levert zodat de opmaak niet stukgaat.

---

## 11. Status van dit document

- Dit document is **bindend** voor elke chat die `.md`-bestanden levert binnen dit project.
- Het verandert niet per fase. Nieuwe inzichten komen als nieuwe sectie erbij, niet als vervanging van bestaande secties.
