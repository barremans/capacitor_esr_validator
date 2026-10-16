# Changelog

Overzicht van wat er nieuw of verbeterd is in de Electronics Diagnostic
Tool Hub. Voor technische details en architectuurkeuzes verwijzen we naar
`docs/context.md`.

<!--
Opmerking over de versienummering:
- Vanaf v1.1.1 komen de versienummers 1-op-1 overeen met
  `app/version.py`, met de GitHub-releases en met
  `releases/latest/version.txt`.
- Vóór v1.1.1 is de nummering historisch: de vroege ontwikkelfases
  gebruikten een eigen 1.x-teller die niet altijd samenviel met de
  uiteindelijke releases. Die entries blijven staan als functionele
  mijlpalen; ze zijn niet 1-op-1 te mappen op een specifieke
  `app/version.py`-waarde.
- Voor de actuele versie: zie `app/version.py` of Help → Over.
-->

## Versie 1.2.0 — Frequentie-specifieke referenties en drempelvalidatie (15 oktober 2026)

**ESR-referenties per meetfrequentie**

De ESR-referentie is nu **frequentie-specifiek**. In plaats van één
officiële ESR70-tabel op 100 kHz te gebruiken voor alle metingen, kiest
de applicatie voortaan het referentieprofiel dat het dichtst bij de
werkelijke meetfrequentie ligt.

- **Officiële ESR70-tabel** — 100 kHz. Blijft de primaire bron voor
  metingen op 100 kHz (de LCR-ST1 kan dit zelf niet, maar andere
  toestellen wel).
- **Geschatte profielen** — 100 Hz, 1 kHz en 10 kHz. Deze zijn
  afgeleid van de officiële ESR70-tabel via de Nichicon-
  frequentiecoëfficiënten:
  - 100 Hz — × 2,00
  - 1 kHz — × 1,50
  - 10 kHz — × 1,15
- De geschatte profielen zijn expliciet gemarkeerd als **schatting**
  (`is_schatting: true`) en dragen een lager betrouwbaarheidsniveau.
  Ze zijn géén datasheet-waarde.

**Waarom deze wijziging**

De LCR-ST1 meet op 1 kHz en 10 kHz. De officiële ESR70-tabel geldt voor
100 kHz. Omdat ESR daalt met frequentie, was de vergelijking
structureel te streng: goede condensatoren kregen factoren die te laag
uitvielen. Met de nieuwe profielen klopt de vergelijking weer.

**Validatie met 72 praktijkmetingen**

De nieuwe referenties zijn gevalideerd tegen 72 praktijkmetingen uit de
historiek. Voor goede condensatoren zakten de factoren naar
**0,09–0,41** — een gezonde verdeling.

**Drempels blijven ongewijzigd**

De drempels `≤1,0 / ≤2,0 / ≤3,0` blijven zoals ze zijn. Met de nieuwe
referenties betekenen ze weer wat ze moeten betekenen: een gezonde
condensator zit ruim onder 1,0, en er is marge voor verslechtering
voordat "aandachtspunt" wordt bereikt.

**Zichtbaar in het resultaat**

Het resultaat toont nu expliciet de **referentiefrequentie** die voor
de vergelijking gebruikt is. Zo zie je meteen of de meting en de
referentie op dezelfde frequentie staan.

**Voor ontwikkelaars**

- `app/data/references/esr_references.json` — nieuwe profielen
  `algemeen_100hz_geschat`, `algemeen_1khz_geschat` en
  `algemeen_10khz_geschat`, elk met de volledige ESR70-tabel geschaald.
- `app/data/references/__init__.py` — `zoek_referentie()` accepteert
  `meetfrequentie_hz` en kiest het dichtstbijzijnde profiel met regels.
- `app/services/assessment_service.py` — `Beoordeling` heeft het veld
  `referentiefrequentie_hz`.
- `app/gui/esr_test_screen.py` — geeft `meetfrequentie_hz` door aan
  `zoek_referentie` en toont de werkelijke referentiefrequentie.
- Nieuwe i18n-key: `resultaat.referentiefrequentie` (NL + EN).
- Nieuw analysedraaiboek: `scripts/herbereken_steekproef.py`.

### UX-afwerking (fase 11A, 16 oktober 2026)

**Export respecteert nu de selectie**

In de **Historiek** en de **Analyse** kun je met een selectie-DDL kiezen
wat je exporteert: **huidige filters** of **selectie**. Vink je in de
tabel een of meer metingen aan, dan exporteert de app alleen die
metingen. Zonder selectie exporteert de app de volledige filter-selectie.

**Selectie en rapport in de Analyse-pagina**

De **Analyse**-pagina heeft onder de grafiek een compacte selectielijst.
Vink je daar een of meer metingen aan, dan kun je:

- **Exporteren…** — als overzicht-CSV, detail-CSV, of beide.
- **Rapport maken…** — een rapport voor precies die selectie.

**Rapport met scope "selectie"**

Het meetrapport ondersteunt nu een rapport over **meerdere metingen**.
De rapportkop toont de scope ("Eén meting" of "Selectie"). De
grafieksectie is alleen beschikbaar voor één meting.

**Menu "Rapport maken…" is disabled zonder selectie**

In het **Bestand**-menu is het item **Rapport maken…** nu disabled
zolang je geen meting geselecteerd hebt. Een tooltip legt uit waarom.
Op de **Analyse**-pagina wordt het item actief zodra je een
checkbox-selectie hebt.

**Mapvoorkeuren worden overal gerespecteerd**

Een nieuwe pure helper
(`app/helpers/dialog_start_directory.py`) bepaalt de beste startmap
voor elke `QFileDialog`:

- **Export** — `laatste_exportmap` → `standaard_exportmap`.
- **Import** — `laatste_importmap` → `standaard_importmap`.
- **Rapport** — `laatste_rapportmap` → `standaard_exportmap`.

Na een geslaagde export/import/rapport wordt de gebruikte map
automatisch onthouden voor de volgende keer.

**Voor ontwikkelaars**

- `app/gui/analysis_screen.py` — compacte selectielijst onder de
  grafiek via `QSplitter`, checkbox-kolom, scope-DDL, type-DDL,
  exportknop en `report_btn`. Nieuwe signalen `selection_changed` en
  `back_requested`.
- `app/gui/history_screen.py` — nieuw `selection_changed`-signaal met
  snapshot-dedup. `report_btn` respecteert de checkbox-selectie.
- `app/gui/main_window.py` — `_open_report_dialog()` kiest de scope op
  basis van de actieve pagina en selectie.
- `app/gui/dialogs/report_dialog.py` — nieuwe classmethod
  `for_measurements(measurement_ids, ...)`.
- **Nieuw:** `app/helpers/dialog_start_directory.py` (v1.0.0).
- Nieuwe i18n-keys: 24 onder `analyse.selectie.*`, `analyse.export.*`,
  `analyse.rapport.*` en `menu.rapport_tooltip` (NL + EN).
- Baseline: **1347 passed** (was 1297).

## Versie 1.1.1 — Update-controle bij opstarten en via Help (15 oktober 2026)

**Automatische controle op een nieuwere versie**

De applicatie controleert bij het opstarten eenmalig en niet-blokkerend
of er een nieuwere versie beschikbaar is op GitHub. Die controle leest
de "latest"-pointer in `releases/latest/version.txt` en vergelijkt die
met de versie in `app/version.py`. Je merkt niets van de controle zolang
er geen nieuwere versie is.

**Handmatige controle via Help**

Je kunt de controle ook handmatig uitvoeren via
**Help → Controleren op updates…**. Je krijgt dan altijd een melding:
ofwel "Je gebruikt de nieuwste versie", ofwel een nieuwere versie met
de knop **Downloaden**.

**Wat is er nieuw?**

Als er een nieuwere versie is, toont de melding ook een knop
**Wat is er nieuw?**. Die haalt de release notes op die de ontwikkelaar
bij de GitHub-release heeft ingevuld, en toont ze in een leesbaar
venster. Van daaruit kun je de release-pagina op GitHub openen.

**Instelling: bij opstarten controleren op updates**

In **Instellingen → Algemeen** staat een nieuwe checkbox
**Bij opstarten controleren op updates**. Standaard staat die aan. De
handmatige controle via Help blijft altijd beschikbaar, ook als je de
automatische controle uitzet.

**Meertalige changelog**

De changelog is nu beschikbaar per taal: `docs/changelog/nl_NL.md` en
`docs/changelog/en_US.md`. Het Help-menu toont automatisch de versie
die bij de gekozen taal hoort, met dezelfde fallback-keten als de Help
(taal → Nederlands → algemeen).

**Voor ontwikkelaars**

- Nieuwe module `app/helpers/updater.py` — pure update-check logica,
  geen Qt, geen token. Bevat `check_for_update()` en
  `fetch_release_notes()`.
- Nieuwe resolver `changelog_pad_voor_taal()` in
  `app/helpers/help_paths.py`, met dezelfde fallback-keten als Help.
- Nieuwe i18n-keys onder `update.*` en
  `settings.algemeen.controleer_updates` (NL + EN).
- Nieuwe instelling `algemeen.controleer_updates_bij_opstarten` (default
  `True`), backward-compatible met bestaande `settings.json`.

## Versie 1.0.3 — Publicatie, testmatrix en bug/feature-meldingen (14 oktober 2026)

**De applicatie is nu publiek beschikbaar op GitHub**

Op 13 oktober 2026 is de eerste publieke release **v1.0.3** verschenen
in de repo `barremans/capacitor_esr_validator`. De installer
(`ESR_TesterSetup_1.0.3.exe`, ongeveer 63 MB) is ondertekend en
gepubliceerd, samen met een **stabiele "latest"-pointer** in
`releases/latest/version.txt`. Die pointer is de basis voor de
update-controle.

**Buildstraat uitgebreid met `publish.ps1` en `build_and_publish.ps1`**

- **`publish.ps1`** — publiceert de installer naar GitHub, met een
  **release-gate** op de Authenticode-handtekening. Een ongesigneerde
  installer wordt nooit gepubliceerd.
- **`build_and_publish.ps1`** — orchestrator die de hele keten draait:
  versie bumpen, builden, signeren, publiceren. Vraagt de parameters
  vooraf.

**Intune/Defender-testmatrix**

De installer is bewezen op twee soorten Windows-pc's:

- **Gewone Windows-pc** — SmartScreen toont een waarschuwing, maar
  "More info → Run anyway" werkt.
- **Intune-beheerde pc** — de installer start zonder blokkade, dank zij
  een **Defender Certificate Indicator** (`Allow`) voor het
  CGK-certificaat. De app installeert en werkt.

WDAC en AppLocker zijn in de doelomgeving **niet actief**; de
Defender-indicator volstaat.

**Bug- en feature-meldingen vanuit de applicatie**

Het hoofdmenu heeft nu een **Rapporteren**-menu met twee opties:

- **🐞 Bug of feature melden…** — opent een meldscherm waarin je een
  bug of feature-aanvraag beschrijft. De melding wordt automatisch
  aangemaakt als **GitHub Issue** (label `bug` of `enhancement`). Je
  naam wordt voorgevuld met je Windows-gebruikersnaam.
- **Open cases tonen** — toont de open bugmeldingen en
  feature-aanvragen uit de repo.

De meldingen gaan rechtstreeks naar de GitHub-repo. Er is geen
e-mailverkeer of externe dienst nodig: de applicatie leest en schrijft
via de GitHub REST API.

**Voor ontwikkelaars**

- Het feedbackpakket (`github_feedback.py`, `bug_report_dialog.py`,
  `github_cases.py`, `check_github_secret.py`) staat identiek in de
  projectroot, met een app-specifieke `github_feedback_config.py`.
- Het GitHub-token staat in `github_secret_local.py`, dat in
  `.gitignore` staat (`*_secret_local.py`) en nooit naar GitHub gaat.
  PyInstaller bundelt het wel mee in de exe.
- `ESR_Tester.spec` roept vóór elke build `check_github_secret.py` aan.
  Een build zonder geldig token stopt met een duidelijke melding, zodat
  er nooit een installer verschijnt waarin "Bug of feature melden"
  niet werkt.
- Nieuwe i18n-keys: `menu.rapporteren`, `menu.bug_melden`,
  `menu.open_cases` (NL + EN).

**Opgelost**

- De `LF/CRLF`-waarschuwing bij `git add releases/latest/version.txt`
  is opgelost via een `.gitattributes`-regel
  (`releases/latest/version.txt text eol=lf`).
- `ESR_Tester.spec` staat niet langer in `.gitignore`. De spec wordt nu
  meegecommit, zodat een verse clone op een andere machine direct kan
  bouwen (`!ESR_Tester.spec`).

**Documentatie**

- `docs/packaging.md` — build-flow, signing, distributie, checklist.
- `docs/testmatrix_defender_intune.md` — de volledige testmatrix met
  bewezen status per pc-type.

## Versie 1.0.2 — Eerste Windows-build, installer en signing (13 oktober 2026)

**De applicatie heeft nu een echte versie**

De applicatie heeft nu één centrale versie, op één plek: `app/version.py`.
De versie wordt getoond in de **Over**-dialoog (Help → Over) en is de
basis voor de buildstraat en de latere update-controle.

**Volledige Windows-buildstraat**

Je kunt de applicatie nu bouwen als een zelfstandige Windows-applicatie
met installer. De flow volgt 1-op-1 de bewezen ArticleSearch-flow:

- **`ESR_Tester.spec`** — PyInstaller-specificatie, met icoon actief.
- **`build_installer.bat`** — bouwt de EXE, genereert `dist\installer.iss`,
  compileert met Inno Setup 6, en tekent zowel de EXE als de installer.
- **`bump_version.py`** — verhoogt patch, minor of major in
  `app/version.py`. Wordt aangeroepen door de buildstraat, kan ook
  handmatig: `python bump_version.py patch`.
- **`build_and_publish.ps1`** — orchestrator met signing-preflight.
  Vraagt de parameters, kiest automatisch het juiste certificaat, en
  roept de batch aan.
- **`publish.ps1`** — publiceert de installer naar GitHub, met een
  release-gate op de Authenticode-handtekening.

**Code-signing**

De EXE en de installer worden ondertekend met het CGK-certificaat
(`CN=CGK Local Signing`, geldig tot 2028-09-17). Na het ondertekenen
wordt de handtekening automatisch geverifieerd met `signtool verify`.

**Installer met icoon**

De installer heeft nu het ESR Tester-icoon in de wizard en in de
snelkoppelingen (Startmenu en optioneel bureaublad). De app start na
installatie met gebruikersrechten (`runascurrentuser`), niet als
administrator.

**Installatie**

Standaard installatiemap: `C:\Program Files\Electronics Diagnostic
Tool Hub\ESR Tester`. De gebruiker kan de map kiezen tijdens de
installatie.

**Opgelost**

- De **venstertitels van het Help-venster en het Wijzigingslog-venster**
  toonden de onvertaalde keys `dialog.help_titel` en
  `dialog.changelog_titel`. Dat is nu opgelost.
- De **ESR-testknop** in de Diagnose-pagina toonde de onvertaalde key
  `tool.esr`. Dat is nu opgelost.
- De **buildstraat** brak eerder af met
  `: was unexpected at this time.` door een `set /p`-prompt met
  haakjes. Dat is opgelost door de prompt te vervangen door een
  `if defined`-check.

**PDF's met leesbare tekst, zonder handmatige stap**

Qt kon in een PySide6-omgeving de Windows-systeemfonts niet vinden,
waardoor PDF-rapporten zwarte blokken toonden in plaats van tekst. De
applicatie stelt nu **automatisch** de omgevingsvariabele
`QT_QPA_FONTDIR=C:\Windows\Fonts` in wanneer je op Windows start en de
variabele nog niet gezet is.

**Voor ontwikkelaars**

- `numpy` is toegevoegd aan `requirements.txt` als directe dependency,
  met een pin `>=1.26,<3`. `pandas` kreeg een pin `>=2.2,<3`.
  Reden: pandas 3.x gaf een ABI-conflict met numpy 2.x in de build.
- `QT_QPA_FONTDIR` wordt nu in `main.py` gezet vóór `QApplication`
  aangemaakt wordt.
- `app/version.py` is de centrale versiebron.

## Versie 1.0.1 — Meetrapporten en uitgebreidere instellingen (12 oktober 2026)

**Meetrapporten maken**

Je kunt nu van elke opgeslagen meting een **meetrapport** maken. Open een
meting in de historiek, klik op **Rapport** (of gebruik **Ctrl+P** in het
Bestand-menu), en je krijgt een overzichtelijke preview. Je kunt het
rapport opslaan als **HTML** of als **PDF**.

Het rapport bevat:

- **Componentidentificatie** — fabrikant, serie, partnummer, technologie,
  nominale capaciteit, nominale spanning, tolerantie.
- **Meetcontext** — meetmethode, instrument, frequentie, testspanning,
  temperatuur, veiligheidsbevestigingen.
- **Ruwe meetwaarden** — capaciteit, ESR, D, out-of-range-vlaggen.
- **Assessment-snapshots** — de opgeslagen beoordelingen met redenen,
  waarschuwingen en advies.
- **Referentie-snapshots** — de gebruikte referenties per beoordeling.
- **Optionele grafiek** — een grafieksectie met ESR-verloop (alleen voor
  ESR_CAPACITOR).

**Nieuw in de Rapportage-instellingen**

De Settings-dialoog heeft nu een uitgebreidere **Rapportage-tab**:

- **Auteur** — optioneel vrij veld dat in de rapportkop wordt getoond.
- **Standaard rapportmap** — de map waarin de opslaandialoog standaard
  start. Wordt automatisch bijgewerkt na elke geslaagde opslag.

De **grafiek-checkbox** in het rapportdialoog start voortaan met de
waarde van **Grafiek standaard opnemen** uit de instellingen.

**Automatisch de map openen**

Als **Exportmap openen na succesvolle export** aan staat, wordt na het
opslaan van een rapport automatisch de map geopend — net als bij de
CSV-export van de historiek.

**Read-only**

Het rapport wordt opgebouwd uit de **opgeslagen snapshots**. Historische
metingen en beoordelingen worden nooit opnieuw berekend of gewijzigd.
Het rapport is puur een weergave.

**Opgelost**

- In de rapport-HTML en -PDF verschenen de onvertaalde keys
  `algemeen.ja` en `algemeen.nee` in plaats van "Ja"/"Nee". Dat is nu
  opgelost door `app.ja` en `app.nee` te gebruiken.
- De **statuslabels** in het rapport (`Capacitance status`,
  `ESR status`, `Consistency status`) werden als ruwe codes getoond
  (`binnen_tolerantie`, `niet_beoordeeld`). Ze worden nu vertaald,
  net als in de GUI.

## Versie 1.0.0 — Grafieken en trends (9 oktober 2026)

**Nieuwe pagina "Analyse"**

In het hoofdmenu staat nu een vierde knop **Analyse**, naast Diagnose,
Historiek en Documentatie. De pagina toont grafieken en trends op basis
van je opgeslagen metingen. Je opent de pagina via de hub-knop, via het
Diagnose-menu ("Analyse openen"), of met de sneltoets **Ctrl+A**.

**Vier grafiektypes**

Met een dropdown kies je welk type grafiek je wilt zien:

- **ESR over tijd** — het ESR-verloop van je metingen, oud naar nieuw.
- **Capaciteit over tijd** — het capaciteitsverloop.
- **D over tijd** — het verloop van de dissipatiefactor.
- **ESR vs. capaciteit** — een spreidingsdiagram waarin elke meting een
  punt is. De kleur toont de eindstatus.

**Filteren op precies dezelfde velden als de historiek**

De filterbalk gebruikt dezelfde velden als de historiekpagina:
fabrikant, serie, meetmethode, instrument, frequentie en een
periode (van/tot datum). Met **Ctrl+F** open je het filterpaneel.

**Aggregatie per dag, week of maand**

Standaard toont elke grafiek alle ruwe meetwaarden. Met een tweede
dropdown kies je **gemiddelde per dag**, **per week** of **per maand**.

**Read-only**

De Analyse-pagina leest je opgeslagen metingen en schrijft niets terug.

**Sneltoetsen**

- **Ctrl+A** op het Hoofdmenu opent de Analyse-pagina.
- **Ctrl+R** op de Analyse-pagina ververst de gegevens.
- **Ctrl+F** opent het filterpaneel.
- **Esc** gaat terug naar het Hoofdmenu.

---

<!--
Vanaf hier: vroege ontwikkelfases. De nummering is historisch en komt
niet altijd 1-op-1 overeen met `app/version.py`. Deze entries blijven
staan als functionele mijlpalen.
-->

## Versie 0.9 — Fabrikantdocumenten: Word en Excel (9 oktober 2026)

**Word- en Excel-import**

Naast PDF en URL kun je nu ook **Word-documenten (.docx)** en
**Excel-werkmappen (.xlsx)** importeren als documentatiebron. De
import-wizard heeft vier keuzes:

- **PDF-bestand**
- **Word-document**
- **Excel-werkmap**
- **Vanaf URL**

**Oude formaten worden geweigerd**

Het oude `.doc`-formaat (Word 97-2003) en `.xls`-formaat (Excel 97-2003)
worden niet ondersteund.

**Verbeterd: Word- en Excel-bestanden openen**

Geïmporteerde Word- en Excel-bestanden worden geopend in de standaard
Word- of Excel-applicatie.

## Versie 0.8 — Status van eigen imports beheren (8 oktober 2026)

**Status van een import wijzigen**

In de documentatiebibliotheek is er nu een knop **Status wijzigen…**
voor je eigen imports. Je kunt de levenscyclus van een import aanpassen:

- **Concept** — pas geïmporteerd, nog niet bevestigd als bruikbaar.
- **Actief** — expliciet door jou bevestigd als bruikbaar.
- **Gearchiveerd** — niet meer in de standaardlijst, maar blijft bewaard.

**Nieuwe Status-kolom**

De documentatietabel heeft nu een extra kolom **Status**.

**Verbeterd: checkboxen en radio buttons in het donkere thema**

De checkboxen en radio buttons in de hele applicatie zijn nu duidelijk
zichtbaar in het donkere thema.

## Versie 0.7 — Metadata bij import en bewerken in de viewer (7 oktober 2026)

**Metadata bij importeren van een PDF of URL**

Bij het importeren van een document kun je nu meteen metadata invullen:
categorie, fabrikant, serie, partnummer, documentversie, documentdatum
en notities.

**Metadata bewerken in de documentatiebibliotheek**

In de documentatiebibliotheek is er nu een knop **Bewerken…** voor je
eigen imports.

**Verbeterd zoeken**

Het zoekveld in de documentatiebibliotheek doorzoekt nu ook de metadata
van geïmporteerde documenten.

## Versie 0.6 — Help per taal en duidelijkere zoekuitleg (6 oktober 2026)

**Nieuw**
- **Help per taal.** De algemene help wordt nu per taal getoond.
- **Duidelijkere uitleg over uitsluiten in de zoekhulp.**

**Verbeterd**
- **Zoekterm met minteken én procentteken genegeerd.**

**Voor ontwikkelaars**
- Nieuwe referentie `docs/search_syntax.md`.

## Versie 0.5 — Sneltoetsen en veiliger afsluiten (5 oktober 2026)

**Nieuw**
- Je kan nu door de hele applicatie met het toetsenbord werken.

**Verbeterd**
- Esc op het Hoofdmenu vraagt nu een bevestiging.

## Versie 0.4 — Slimmer zoeken en hulp in de documentatie (5 oktober 2026)

**Nieuw**
- **Zoektaal voor documentatie.**
- **Help bij het zoeken.**

**Verbeterd**
- Het venster voor zoekhulp is nu ook bereikbaar via het Help-menu.

## Versie 0.3 — Meerdere diagnosetools in één hub (3 oktober 2026)

**Nieuw**
- Documenten kunnen nu aan meerdere diagnosetools gekoppeld worden.

**Verbeterd**
- Interne structuur klaar voor toekomstige diagnosetools.

## Versie 0.2 — Documentatiebibliotheek (3 oktober 2026)

**Nieuw**
- Een centrale, meertalige documentatiebibliotheek met 8 technische
  documenten.

## Versie 0.1 — Eerste werkende versie (11 augustus 2026)

**Nieuw**
- Eerste versie van de ESR-validator.

---

## Gepland voor volgende versies

- **Versie 1.2.0 — UX/documentatie-afwerking.** Alle kleine punten die
  in eerdere fases zijn blijven liggen:
  - **11A** — Export, import en selectie: export respecteert selectie,
    visuele selectie in Analyse, rapport-scope "selectie",
    menu-item disabled zonder selectie, mapvoorkeuren respecteren.
    **Afgerond op 16 oktober 2026.** De resterende punten uit §11A
    (import van metingen uit een ander toestel) blijven open.
  - **11B** — Betrouwbaarheidsregel herzien: onderscheid tussen
    inhoudelijke en administratieve betrouwbaarheidsverlagers.
  - **11C** — Iconen voor alle vensters.
  - **11D** — i18n-menging in Diagnose/Result oplossen.
  - **11E** — Async netwerk (URL-fetch, release notes).
  - **11F** — Documentatie-uitbreiding (redenen, filters, bulk-edit).
  - **11G** — Visueel donker thema (checkboxen, scrollbar).
  - **11H** — Light theme.
  - **11I** — Build en cosmetica (deprecations, logbestanden,
    certificaten).
- **Versie 1.3.0 — AI-extractie uit fabrikantdocumenten.**
  Automatische tekstextractie uit docx/xlsx als voorbereiding op
  menselijke validatie.
- **Versie 1.4.0 — Menselijke validatie van AI-output.**
  Goedkeuringsstroom voor AI-geëxtraheerde gegevens.
- **Versie 1.5.0 — Goedgekeurde fabrikantdata koppelen aan
  assessment.** De assessment gebruikt dan gevalideerde
  fabrikantgegevens.
- **Versie 1.6.0 — Tweede diagnosetool: Resistor.**
  Weerstandsmetingen in dezelfde Tool Hub.

---

_Historische nummering: de entries 0.1 t/m 0.9 beschrijven de vroege
ontwikkelperiode. De nummering is functioneel, niet 1-op-1 gekoppeld
aan `app/version.py`. Vanaf v1.1.1 komen de versienummers overeen met
de werkelijke releases._