# Help

Welkom bij de Help van de Electronics Diagnostic Tool Hub.

Deze help wordt per taal aangeboden. De applicatie toont automatisch
de versie die hoort bij de gekozen taal. Ontbreekt een taalversie, dan
valt de applicatie terug op het Nederlands en daarna op de algemene
help.

## ESR / Condensator tester

De ESR / Condensator tester ondersteunt het invoeren en beoordelen van
condensator- en ESR-metingen.

Uitgebreide uitleg over:

- het gebruik van de ESR-tool;
- meetmethodes;
- meetinstrumenten;
- veiligheidsinstructies;
- interpretatie van resultaten;

wordt in een latere ontwikkelfase toegevoegd.

## Historiek

De **Historiek** toont de opgeslagen metingen uit de lokale database.
Je kunt filteren op fabrikant, serie, meetmethode, instrument,
frequentie, datum en status. Elke meting heeft een detailweergave met
de volledige opgeslagen meetketen en beoordeling.

Selecteer een rij om de knoppen **Rapport**, **Meting herhalen** en
**Details** te activeren. Je kunt ook een of meer metingen aanvinken
via de checkboxkolom om een selectie te maken voor export of rapport.

## Analyse

De **Analyse**-pagina toont grafieken en trends van je opgeslagen
metingen. Er zijn vier grafiektypes:

- ESR over tijd;
- capaciteit over tijd;
- D over tijd;
- ESR vs. capaciteit (spreidingsdiagram, gekleurd per eindstatus).

Met de aggregatie-dropdown kies je **ruwe metingen**, **gemiddelde
per dag**, **per week** of **per maand**. De filterbalk gebruikt
dezelfde velden als de Historiek. De pagina is volledig read-only.

Onder de grafiek staat een compacte **selectielijst** met dezelfde
metingen. Vink een of meer metingen aan om ze te exporteren of er een
rapport van te maken.

## Rapporten maken

Vanuit de **Historiek** kun je voor één meting een meetrapport maken
via de knop **Rapport** of via **Ctrl+P** in het Bestand-menu. Vanuit
de **Analyse** kun je een rapport maken voor je volledige
checkbox-selectie.

Het rapport bevat componentidentificatie, meetcontext, ruwe
meetwaarden, assessment-snapshots, referentie-snapshots en optioneel
een grafiek (alleen bij één meting). Je kunt het opslaan als **HTML**
of als **PDF**. Het rapport is read-only: er worden geen historische
metingen of beoordelingen opnieuw berekend.

## Exporteren en selectie

In de **Historiek** en in de **Analyse** kun je met een selectie-DDL
kiezen wat je exporteert:

- **Huidige filters** — alle metingen die aan de actieve filters
  voldoen.
- **Selectie** — alleen de metingen die je hebt aangevinkt in de
  checkboxkolom.

Zonder selectie exporteert de app de volledige filter-selectie. Je kunt
kiezen tussen een **overzicht-CSV**, een **detail-CSV** of **beide**.

## Documentatiebibliotheek

Naast deze algemene help bevat de applicatie een meertalige
documentatiebibliotheek met technische documenten over veilig ontladen,
meetmethoden, LCR-meter, ESR-meter, frequentie en testspanning,
dissipatiefactor, C-ESR-D-plausibiliteit en de beperkingen van
in-circuit meten.

Je opent de bibliotheek via het Hoofdmenu of via het menu
**Help → Documentatie zoeken…**.

## Zoeken in de documentatie

De zoektaal ondersteunt eenvoudige tekens:

- meerdere woorden of een komma = alle woorden moeten voorkomen;
- een verticale streep `|` = één van beide woorden;
- een minteken `-` = exact dit woord;
- een uitroepteken `!` = sluit dit woord uit;
- een procentteken `%` = vul zelf aan (wildcard).

Druk op **F1** of gebruik de knop met het vraagteken naast het zoekveld
voor een uitgebreide uitleg met voorbeelden.

## Updates

De applicatie controleert bij het opstarten eenmalig en niet-blokkerend
of er een nieuwere versie beschikbaar is. Je kunt die controle ook
handmatig uitvoeren via **Help → Controleren op updates…**.

Als er een nieuwere versie is, verschijnt een melding met de knop
**Downloaden**. Die opent de downloadpagina in je browser. Via
**Instellingen → Algemeen** kun je de automatische controle bij het
opstarten uitschakelen; de handmatige controle blijft altijd
beschikbaar.

## Sneltoetsen

- **Globaal:** Ctrl+Q (afsluiten), Ctrl+E (ESR-test),
  Ctrl+I (Document importeren), Ctrl+P (Rapport maken),
  Ctrl+A (Analyse), F1 (help).
- **ESR-scherm:** Esc (terug), Ctrl+Enter (beoordelen), Ctrl+S (opslaan),
  Ctrl+W (wissen), Ctrl+I (meetinstructies).
- **Historiek:** Esc (terug), Ctrl+R (verversen), Ctrl+F (filters),
  Ctrl+D (details), Ctrl+H (herhaal meting).
- **Analyse:** Esc (terug), Ctrl+R (verversen), Ctrl+F (filters).
- **Hoofdmenu:** Ctrl+D (Diagnose), Ctrl+H (Historiek),
  Ctrl+K (Documentatie), Ctrl+A (Analyse), Esc (afsluiten met
  bevestiging).

## Talen

De applicatie ondersteunt meerdere talen. Je wisselt van taal via
**Instellingen → Talen**. Alle schermen, help-bestanden en
documenten volgen de gekozen taal. Ontbreekt een vertaling, dan valt
de applicatie terug op het Nederlands.