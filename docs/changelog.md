# Changelog

Overzicht van wat er nieuw of verbeterd is in de Electronics Diagnostic
Tool Hub. Voor technische details en architectuurkeuzes verwijzen we naar
`docs/context.md`.

## Versie 1.5 — Status van eigen imports beheren (8 oktober 2026)

**Status van een import wijzigen**

In de documentatiebibliotheek is er nu een knop **Status wijzigen…**
voor je eigen imports. Je kunt de levenscyclus van een import aanpassen:

- **Concept** — pas geïmporteerd, nog niet bevestigd als bruikbaar.
- **Actief** — expliciet door jou bevestigd als bruikbaar.
- **Gearchiveerd** — niet meer in de standaardlijst, maar blijft bewaard.

De toegelaten overgangen zijn:

- Concept → Actief (geen bevestiging nodig)
- Concept → Gearchiveerd (met bevestiging)
- Actief → Concept (met bevestiging)
- Actief → Gearchiveerd (met bevestiging)
- Gearchiveerd → Concept (met bevestiging)

Een bron wordt **nooit verwijderd**. Je kunt een gearchiveerde bron altijd
terugzetten naar Concept. De bron en de metadata blijven ongewijzigd bij
een statuswijziging; alleen de levenscyclus verandert.

Documenten uit de ingebouwde bibliotheek zijn en blijven read-only. De
Status wijzigen-knop is dan uitgeschakeld met een tooltip die uitlegt
waarom.

**Gearchiveerde imports zichtbaar maken**

Naast de tool-dropdown staat nu een checkbox **Toon gearchiveerde**.
Standaard staat die uit: gearchiveerde imports blijven verborgen. Vink
je hem aan, dan verschijnen ze opnieuw in de lijst, zodat je ze kunt
openen, bewerken of terugzetten naar Concept.

**Nieuwe Status-kolom**

De documentatietabel heeft nu een extra kolom **Status**, tussen
Categorie en Fabrikant. Voor ingebouwde documenten is die kolom leeg.
Voor eigen imports toont hij de huidige levenscyclusstatus (Concept,
Actief of Gearchiveerd).

**Verbeterd: checkboxen en radio buttons in het donkere thema**

De checkboxen en radio buttons in de hele applicatie zijn nu duidelijk
zichtbaar in het donkere thema. Voorheen gebruikte Qt de standaard
Fusion-stijl, waardoor de indicator (het vierkantje of rondje) bijna
onzichtbaar was op de donkere achtergrond. De nieuwe stijl geeft een
duidelijke rand, een blauwe checked-state en consistente hover- en
disabled-styling.

## Versie 1.4 — Metadata bij import en bewerken in de viewer (7 oktober 2026)

**Metadata bij importeren van een PDF of URL**

Bij het importeren van een document kun je nu meteen metadata invullen:
categorie, fabrikant, serie, partnummer, documentversie, documentdatum
en notities. De categorie is verplicht (default: fabrikantdatasheet);
de andere velden zijn optioneel. Identificatievelden (fabrikant, serie,
partnummer, documentversie) worden automatisch in hoofdletters gezet
zodat ze consistent in de bibliotheek staan.

De documentdatum is een kalenderveld met een knop "Datum onbekend" voor
documenten zonder bekende datum. Met Ctrl+D zet je de datum op vandaag.

Bestaande imports van vóór deze versie blijven geldig. Ze hebben geen
metadata; die kun je later toevoegen door de import te bewerken.

**Metadata bewerken in de documentatiebibliotheek**

In de documentatiebibliotheek is er nu een knop **Bewerken…** voor je
eigen imports. Je kunt de metadata (titel, categorie, fabrikant, serie,
partnummer, documentversie, documentdatum, notities) achteraf aanpassen
zonder het bronbestand opnieuw te importeren. Het bronbestand, de status
en de importdatum blijven ongewijzigd.

Documenten uit de ingebouwde bibliotheek (meegeleverd met de app) zijn
en blijven read-only. De Bewerken-knop is dan uitgeschakeld met een
tooltip die uitlegt waarom.

**Verbeterd zoeken**

Het zoekveld in de documentatiebibliotheek doorzoekt nu ook de metadata
van geïmporteerde documenten (categorie, fabrikant, serie, partnummer,
versie, datum, notities en bron-URL). Zoeken op fabrikant of serie werkt
daardoor nu ook voor eigen imports.


## Versie 1.3 — Help per taal en duidelijkere zoekuitleg
**Datum:** 6 oktober 2026

**Nieuw**
- **Help per taal.** De algemene help wordt nu per taal getoond. De
  applicatie kiest automatisch de juiste versie op basis van je
  taalkeuze. Ontbreekt een taalversie, dan valt de applicatie terug op
  het Nederlands.
- **Duidelijkere uitleg over uitsluiten in de zoekhulp.** In het
  Help-venster van de zoektaal staat nu een extra uitleg: het
  uitroepteken (`!`) sluit elk woord uit dat de gezochte tekst bevat,
  niet enkel het losse woord. Zo weet je meteen waarom `!esr` ook
  `mesr` uitsluit.

**Verbeterd**
- **Zoekterm met minteken én procentteken genegeerd.** Een zoekterm die
  met een minteken begint én een procentteken bevat (bv. `-%meter`)
  heeft geen eenduidige betekenis. De applicatie negeert zulke termen
  nu stil, net zoals lege termen. De rest van je zoekopdracht blijft
  gewoon werken: `esr,-%meter` gedraagt zich hetzelfde als `esr`.

**Voor ontwikkelaars**
- Nieuwe referentie `docs/search_syntax.md`: volledige beschrijving
  van de zoektaal van de documentatiebibliotheek (operatoren,
  semantiek, randgevallen, uitbreidingspunten).

## Versie 1.2 — Sneltoetsen en veiliger afsluiten
**Datum:** 5 oktober 2026

**Nieuw**
- Je kan nu door de hele applicatie met het toetsenbord werken:
  - **ESR-test:** Esc (terug), Ctrl+Enter (beoordelen),
    Ctrl+S (meting opslaan), Ctrl+W (wissen),
    Ctrl+I (meetinstructies).
  - **Historiek:** Esc (terug), Ctrl+R (verversen),
    Ctrl+F (filterpaneel openen), Ctrl+D (details),
    Ctrl+H (meting herhalen).
  - **Hoofdmenu:** Ctrl+D (Diagnose), Ctrl+H (Historiek),
    Ctrl+K (Documentatie).
  - **Diagnose-pagina:** Esc (terug naar Hoofdmenu).

**Verbeterd**
- Esc op het Hoofdmenu vraagt nu een bevestiging voordat de applicatie
  sluit. Zo sluit je de applicatie niet per ongeluk af.
- De vensterknop X blijft de applicatie direct sluiten zoals voorheen.

## Versie 1.1 — Slimmer zoeken en hulp in de documentatie
**Datum:** 5 oktober 2026

**Nieuw**
- **Zoektaal voor documentatie.** Je kan nu gericht zoeken met
  eenvoudige tekens:
  - meerdere woorden of een komma = alle woorden moeten voorkomen;
  - een verticale streep `|` = één van beide woorden;
  - een minteken `-` = exact dit woord;
  - een uitroepteken `!` = sluit dit woord uit;
  - een procentteken `%` = vul zelf aan (wildcard).
- **Help bij het zoeken.** Een vraagteken-knop naast het zoekveld en de
  toets F1 openen een hulpvenster met uitleg en voorbeelden.
- **Menu Help → Documentatie zoeken…** opent hetzelfde hulpvenster.

**Verbeterd**
- Het venster voor zoekhulp is nu ook bereikbaar via het Help-menu.
- Algemene stabiliteit van het menu bij het wisselen van taal.

## Versie 1.0 — Meerdere diagnosetools in één hub
**Datum:** 3 oktober 2026

**Nieuw**
- Documenten kunnen nu aan meerdere diagnosetools gekoppeld worden.
- Elk document heeft extra kenmerken: soort component, soort test,
  meetmethode, meetinstrument en onderwerp. Zo vind je sneller het
  juiste document.
- De productcatalogus is voorzien van deze kenmerken.

**Verbeterd**
- Interne structuur klaar voor toekomstige diagnosetools
  (zoals een weerstandstester) zonder de bestaande werking te wijzigen.

## Versie 0.9 — Documentatiebibliotheek
**Datum:** 3 oktober 2026

**Nieuw**
- Een centrale, meertalige documentatiebibliotheek met 8 technische
  documenten (veilig ontladen, meetmethoden, LCR-meter, ESR-meter,
  frequentie en testspanning, dissipatiefactor,
  C-ESR-D-plausibiliteit, beperkingen van in-circuit meten).
- Elk document heeft een vaste ID en metadata (titel, categorie,
  bron, herkomst).
- De documentatie kan doorzocht en gefilterd worden op categorie
  en tool.
- Vanuit het ESR-scherm kan je rechtstreeks de meest relevante
  meetinstructie openen.
- Vanuit het ESR-scherm geeft de knop "Meetinstructies" een
  contextuele aanbeveling op basis van meetmethode en instrument.

**Verbeterd**
- Documenten verschijnen in het Nederlands of Engels, afhankelijk
  van de gekozen taal. Ontbreekt een taal, dan valt de applicatie
  terug op het Nederlands.

## Versie 0.8 — Historiek
**Datum:** 1 oktober 2026

**Nieuw**
- Een overzichtelijke historiekpagina met alle opgeslagen metingen:
  datum en tijd, tool, component, meetmethode, instrument, meetwaarden,
  eindstatus en betrouwbaarheid.
- Filteren op tool, fabrikant, serie, meetmethode, instrument,
  frequentie, eindstatus, betrouwbaarheid en periode.
- Een detailvenster per meting met alle opgeslagen informatie.
- **Meting herhalen**: neem de component en meetcontext over als
  startpunt voor een nieuwe meting. De oude meetwaarden worden niet
  overgenomen.
- Exporteren naar CSV: overzicht of volledig detail, van de volledige
  filter of enkel de geselecteerde rijen.

## Versie 0.7 — Lokale opslag
**Datum:** 27 september 2026

**Nieuw**
- Beoordeelde metingen kunnen lokaal opgeslagen worden op de computer.
- Alle ruwe meetdata, beoordelingen en referenties worden samen
  bewaard.
- Opgeslagen metingen worden nooit automatisch opnieuw beoordeeld
  als regels later wijzigen.

## Versie 0.6 — Robuustere invoer en veiligere OL
**Datum:** 29 september 2026

**Nieuw**
- Duidelijke behandeling van "buiten bereik" (OL) en van een
  vermoedelijke open verbinding of kortsluiting.
- Bij OL mag je één of beide meetwaarden leeg laten; de applicatie
  geeft dan de status "niet te beoordelen".
- Exacte tolerantiegrenzen worden gerespecteerd: net binnen of net
  buiten.

**Verbeterd**
- Foutmeldingen bij ongeldige invoer zijn duidelijker.
- Ongeldige tekst wordt ook bij OL geweigerd, zodat geen verkeerde
  waarden worden opgeslagen.

## Versie 0.5 — Instellingen
**Datum:** 27 september 2026

**Nieuw**
- Een instellingenvenster met drie tabbladen: Algemeen,
  ESR/Condensator en Rapportage.
- Voorkeuren worden bewaard tussen sessies.
- Het ESR-scherm gebruikt jouw opgeslagen voorkeuren als startpunt.
- Je kiest zelf of "Wissen" eerst om bevestiging vraagt.

## Versie 0.4 — Compact ESR-scherm
**Datum:** 26 september 2026

**Nieuw**
- Het ESR-scherm is compacter gemaakt: drie kolommen voor
  condensator, meetopstelling en meting.
- Geen storende scrollbar meer in het hoofdscherm.
- Een aparte knop "Veiligheidsinstructies" opent meteen het juiste
  document.
- Frequenties verschijnen als 100 Hz, 1 kHz of 10 kHz.
- Het resultaat wordt samengevat; de knop "Details" toont de volledige
  uitleg met bron en grenzen.

## Versie 0.3 — Donker thema
**Datum:** 27 september 2026

**Verbeterd**
- Uniform donker thema in alle schermen en dialoogvensters.
- Betere leesbaarheid van tekst en knoppen in dialogen.

## Versie 0.2 — Eén venster met interne navigatie
**Datum:** 13 augustus 2026

**Nieuw**
- Eén hoofdvenster met interne pagina's voor Hoofdmenu, Diagnose,
  ESR-test, Historiek en Documentatie.
- De knop X gedraagt zich contextueel: binnen een tool keer je terug
  naar de vorige pagina; op het Hoofdmenu sluit je de applicatie.

## Versie 0.1 — Eerste werkende versie
**Datum:** 11 augustus 2026

**Nieuw**
- Eerste versie van de ESR-validator met basisberekeningen en
  beoordeling.
- Donker thema.
- Nederlands en Engels.
- Eerste validatieregels voor capaciteit, ESR en C-ESR-D-consistentie.

---

## Gepland voor volgende versies
- **Versie 2.0** — PDF- en URL-import van fabrikantdocumenten via
  een wizard. *(grotendeels afgerond in 1.4 en 1.5; resterende
  onderdelen — Word, Excel — volgen in fase 6.)*
- **Versie 2.1** — Automatische herkenning van fabrikantgegevens
  (met verplichte menselijke goedkeuring).
- **Versie 3.0** — Grafieken en trends over meerdere metingen.
- **Versie 3.1** — Rapportage en export van bevindingen.
- **Versie 4.0** — Installer en code-ondertekening voor eenvoudige
  installatie op Windows.
- **Versie 5.0** — Uitgebreide praktijkvalidatie van ESR-metingen.
- **Versie 6.0** — Een tweede diagnosetool: weerstandsmetingen.