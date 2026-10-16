# PROJECT CONTEXT — Electronics Diagnostic Tool Hub

**Huidige kernmodule:** Condensator- en ESR-validator  
**Platform:** Windows 10 / 11  
**Taal v1:** Nederlands, met Engelse vertaalstructuur aanwezig  
**Technologie:** Python + PySide6  
**Status:** Werkend prototype; kernlogica en GUI bestaan, maar ESR v1 moet nog functioneel en ergonomisch afgewerkt worden.

---

## 1. Hoofddoel

Het project moet uitgroeien tot een praktische **diagnose- en kennisbanktool voor elektronica**.

De gebruiker moet niet alleen een getal kunnen berekenen, maar:
- een component of schakeling kunnen identificeren;
- meetcontext kunnen vastleggen;
- meetwaarden invoeren;
- meetwaarden tegen betrouwbare referenties vergelijken;
- onzekerheden en beperkingen zien;
- een onderbouwde diagnose krijgen;
- weten welke vervolgstap logisch is;
- eerdere metingen kunnen bewaren en vergelijken;
- later aanvullende elektronica-tools vanuit één Tool Hub kunnen gebruiken.

De eerste concrete en prioritaire module is de **ESR- en condensatortester**.

---

## 2. Scope ESR v1

Versie 1 richt zich in eerste instantie op:
- aluminium elektrolytische condensatoren;
- handmatige meetinvoer;
- capaciteit;
- ESR;
- optioneel D, Q, Z en X;
- meting in-circuit;
- meting met één aansluiting los;
- volledig uitgebouwde meting;
- vergelijking met datasheet, referentiemeting en algemene ESR-tabellen;
- transparante beoordeling;
- lokale opslag in een latere stap;
- CSV/Excel-export in een latere stap.

Andere condensatortypes mogen geregistreerd worden, maar mogen niet automatisch met elektrolytische ESR-tabellen beoordeeld worden.

---

## 3. Doelplatform

- Windows 10 en Windows 11
- Python
- PySide6
- later als zelfstandige `.exe` of installer
- lokaal gebruik
- geen verplichte cloud
- geschikt voor gebruikers zonder Python-kennis

Projectvenv:
```text
.venv/
```

VS Code moet de `.venv` automatisch selecteren en activeren via:
```text
.vscode/settings.json
```

---

## 4. Huidige projectstructuur

Belangrijkste onderdelen:

```text
capacitor_esr_validator/
├─ app/
│  ├─ config/
│  │  └─ settings.py
│  ├─ data/
│  │  └─ references/
│  │     └─ esr_references.json
│  ├─ gui/
│  │  ├─ esr_test_screen.py
│  │  ├─ main_window.py
│  │  └─ styles.py
│  ├─ helpers/
│  │  ├─ i18n.py
│  │  └─ units.py
│  └─ services/
│     └─ assessment_service.py
├─ assets/
│  └─ icons/
├─ docs/
│  ├─ data_model.md
│  ├─ validation_rules.md
│  ├─ testgevallen_analyse.md
│  └─ future_tools.md
├─ i18n/
│  └─ locales/
│     ├─ nl_NL.json
│     └─ en_US.json
├─ tests/
│  ├─ test_assessment.py
│  └─ test_units.py
├─ .vscode/
│  └─ settings.json
├─ main.py
├─ pyproject.toml
├─ requirements.txt
└─ README.md
```

---

## 5. Huidige status van de software

Aanwezig:
- werkende Tool Hub;
- ESR-tool opent als apart venster;
- PySide6 GUI;
- donker thema;
- i18n-laag;
- Nederlandse en Engelse vertalingen;
- configureerbare drempels;
- eenheidsconversie;
- ESR-referentie-JSON;
- assessment-service;
- capaciteitsoordeel;
- ESR-oordeel;
- C-ESR-D-consistentiecheck;
- betrouwbaarheid;
- eindstatus;
- tests voor kernlogica.

Nog niet voldoende:
- meetmethode is in de daadwerkelijke code nog te simplistisch;
- GUI gebruikt nog scroll;
- veiligheidsinformatie neemt te veel schermruimte in;
- invoervelden zijn te breed;
- resultaatweergave is te lang en formulierachtig;
- type-match van referenties moet explicieter;
- out-of-range/OL moet nog ondersteund worden;
- referentiedata moet verder gevalideerd worden;
- database en historiek zijn nog niet geïmplementeerd.

---

## 6. UX-richting

De ESR-tool moet aanvoelen als een **diagnose-instrument**, niet als een lang administratief formulier.

### 6.1 Geen scroll in de primaire meetflow

Bij normale desktopresolutie moet het volledige primaire ESR-invoerscherm zichtbaar zijn zonder verticale scrollbar.

Details mogen in:
- popup;
- dialoog;
- apart detailvenster;
- uitklapbare sectie.

### 6.2 Veiligheidsinformatie

Niet negen regels permanent in beeld.

Hoofdscherm:
```text
☐ Schakeling spanningsloos en condensator veilig ontladen
[Veiligheidsinstructies]
```

De knop toont de volledige waarschuwingstekst.

De bevestiging blijft verplicht vóór beoordeling.

### 6.3 Compacte velden

Numerieke velden moeten compact zijn:
- capaciteit;
- tolerantie;
- werkspanning;
- temperatuur;
- ESR;
- D.

Eenheden moeten direct naast de waarde staan.

Fabrikant/serie mogen iets breder zijn, maar niet vensterbreed.

### 6.4 Voorgestelde lay-out

Drie logische kolommen:

```text
CONDENSATOR        MEETOPSTELLING       METING
------------------------------------------------
Capaciteit         Meetmethode           Gemeten C
Tolerantie         Frequentie            ESR
Werkspanning       Testspanning          D
Type               Temperatuur           Out of range / OL
Fabrikant
Serie
```

Onder:
```text
[Beoordeel] [Wissen]
```

Daaronder compact resultaat:
```text
STATUS | BETROUWBAARHEID | ESR-FACTOR | C-AFWIJKING | ADVIES
```

Knop:
```text
[Details]
```

---

## 7. Meetmethoden

Er moeten drie expliciete en exclusieve meetmethoden zijn.

### EX_SITU
Volledig uitgebouwd.

Betrouwbaarheid meetopstelling:
- hoogste.

Eigenschappen:
- geen parallelle circuitpaden;
- geschikt voor volwaardige componentbeoordeling;
- voorkeur bij twijfel.

### ONE_LEG
Één aansluiting los.

Betrouwbaarheid:
- middel.

Eigenschappen:
- parallelle paden grotendeels onderbroken;
- praktischer dan volledig uitbouwen;
- betere diagnose dan volledig in-circuit.

### IN_CIRCUIT
Volledig in-circuit.

Betrouwbaarheid:
- laag.

Mogelijke beïnvloeding:
- parallelle weerstand;
- parallelle condensator;
- diodepaden;
- voedingrails;
- andere halfgeleiders.

App moet resultaat expliciet als indicatie behandelen.

### Implementatiebesluit

In applicatiecode bij voorkeur één veld:
```python
meetmethode = "EX_SITU" | "ONE_LEG" | "IN_CIRCUIT"
```

Niet drie onafhankelijke booleans die tegelijk waar kunnen zijn.

---

## 8. Veiligheidsprincipes

Altijd gelden:
- nooit meten aan een schakeling onder spanning;
- afwezigheid van spanning controleren met geschikt meetinstrument;
- condensator gecontroleerd ontladen;
- grote condensatoren kunnen opnieuw spanning opbouwen;
- in-circuit meting kan foutief zijn;
- bij twijfel één aansluiting losnemen;
- LCR-meting test geen volledige isolatie of doorslag;
- goede ESR betekent niet automatisch veilig op nominale spanning;
- app is geen formele veiligheidsvrijgave.

De tool geeft diagnosehulp, geen veiligheidsattest.

---

## 9. Meettoestel en frequenties

Uitgangspunt:
- TEKCOPLUS draagbare LCR-meetpincet of vergelijkbaar toestel.

Bekende meetfrequenties:
- 100 Hz
- 1 kHz
- 10 kHz

Bekende testspanningen:
- 0,3 Vrms
- 0,6 Vrms

Belangrijk:
- exacte displayvelden en toestelprotocol zijn nog niet volledig bevestigd;
- geen USB/seriële automatisering in ESR v1;
- handmatige invoer blijft de standaard.

---

## 10. Kerngegevens

### Component
- gebruiker
- klant
- project
- installatie/machine
- printplaat/module
- componentreferentie
- fabrikant
- serie
- onderdeelnummer
- opmerkingen

### Nominaal
- capaciteit
- eenheid
- tolerantie
- werkspanning
- AC/DC
- condensatortype
- polariteit
- datasheet
- datasheet ESR/impedantie
- referentiefrequentie
- referentietemperatuur

### Meetcontext
- meetmethode
- spanningsloos bevestigd
- ontladen bevestigd
- restspanning
- frequentie
- testspanning
- omgevingstemperatuur
- toestel
- parallelle componenten
- mechanische toestand

### Meetwaarden
- capaciteit
- ESR
- D
- Q
- Z
- X
- V-Loss als ruwe waarde
- stabiliteit
- datum/tijd
- out-of-range/OL-status

---

## 11. Eenheden

Capaciteit:
- pF
- nF
- µF
- mF

ESR:
- mΩ
- Ω

Komma en punt moeten beide als decimaalteken worden aanvaard.

Interne berekeningen gebruiken consistente basiseenheden.

---

## 12. V-Loss

V-Loss is nog niet voldoende gedefinieerd.

Regels:
- optioneel;
- altijd als ruwe waarde opslaan;
- eenheid opslaan;
- nooit automatisch gelijkstellen aan ESR;
- nooit automatisch gelijkstellen aan D;
- nooit gebruiken in eindbeoordeling zolang betekenis niet bevestigd is.

---

## 13. Referentiehiërarchie

Van sterkste naar zwakste bron:

1. exacte fabrikantdatasheet voor exact onderdeel;
2. referentiemeting van nieuw identiek exemplaar;
3. fabrikantgegevens van dezelfde serie;
4. interne bedrijfstabel met gedocumenteerde bron;
5. Peak Atlas ESR70;
6. andere algemene ESR-tabellen;
7. relatieve vergelijking.

Elke beoordeling toont:
- bron;
- referentieniveau;
- referentiefrequentie;
- meetfrequentie;
- temperatuur indien bekend;
- typisch of maximum;
- betrouwbaarheidsniveau.

---

## 14. Type-match van referentie

Elektrolytische referentietabellen mogen niet automatisch toegepast worden op:
- polymer;
- tantaal;
- film;
- keramiek;
- supercap;
- onbekende technologie.

Bij mismatch:
- niet automatisch selecteren;
- manueel gebruik alleen met duidelijke waarschuwing;
- betrouwbaarheid nooit hoger dan laag.

---

## 15. Frequentiebeleid

ESR is frequentieafhankelijk.

Nooit automatisch omrekenen tussen bijvoorbeeld:
- 100 Hz;
- 1 kHz;
- 10 kHz;
- 100 kHz.

Als referentie- en meetfrequentie verschillen:
- beide tonen;
- waarschuwing tonen;
- betrouwbaarheid verlagen;
- geen verborgen correctie uitvoeren.

---

## 16. Capaciteitsbeoordeling

Formule:
```text
afwijking_percent =
((gemeten - nominaal) / nominaal) × 100
```

Status:
- binnen tolerantie;
- op grens;
- buiten tolerantie;
- niet beoordeelbaar bij ontbrekende tolerantie.

Default:
```text
capaciteit_marge_binnen = 0,9
```

Hierdoor wordt de zone tussen 90% en 100% van de tolerantie als "op grens" weergegeven.

---

## 17. ESR-beoordeling

Wanneer een bruikbare referentie beschikbaar is:

```text
factor = gemeten_ESR / referentie_ESR
```

Configureerbare defaults:
```text
factor <= 1,0        waarschijnlijk normaal
1,0 < factor <= 2,0 aandachtspunt
2,0 < factor <= 3,0 verdacht
factor > 3,0        waarschijnlijk defect
```

Dit zijn geen universele normen.

De bron en frequentie moeten altijd zichtbaar blijven.

---

## 18. C-ESR-D-consistentie

Alleen indien C, ESR en D voor dezelfde frequentie aanwezig zijn:

```text
D ≈ 2 × π × f × C × ESR
```

of:
```text
ESR ≈ D / (2 × π × f × C)
```

Gebruik:
- eenhedenfouten detecteren;
- mΩ/Ω-verwisseling detecteren;
- foutieve frequentie vermoeden;
- verkeerd overgenomen displaywaarde signaleren.

Niet gebruiken als zelfstandige goed/afkeurregel.

Configureerbare defaults:
```text
consistentie_marge = 2,0
consistentie_eenhedenfout_drempel = 100
```

---

## 19. Betrouwbaarheid

Betrouwbaarheid is apart van de status.

Bronbasis:
- niveau 1-3: hoog;
- niveau 4-5: middel;
- niveau 6-7: laag.

Verlagende factoren:
- frequentieverschil;
- temperatuur onbekend;
- verkeerd/onbekend condensatortype;
- in-circuit;
- typische waarde in plaats van maximum;
- fabrikant/serie onbekend;
- C-ESR-D-inconsistentie.

Meetmethode moet daarnaast expliciet meewegen:
- EX_SITU: geen verlaging puur door meetopstelling;
- ONE_LEG: middelmatige meetcontext;
- IN_CIRCUIT: duidelijke verlaging en waarschuwing.

---

## 20. Eindstatus

Mogelijke statussen:
- niet beoordeeld;
- waarschijnlijk goed;
- aandachtspunt;
- twijfelachtig;
- waarschijnlijk defect;
- niet te beoordelen.

Nooit enkel een label.

Altijd tonen:
- gemeten waarden;
- nominale waarden;
- gebruikte referentie;
- berekende afwijking;
- ESR-factor;
- frequenties;
- waarschuwingen;
- betrouwbaarheid;
- redenen;
- aanbevolen vervolgstap.

---

## 21. Out-of-range / OL

Nog toe te voegen.

Veld:
```text
meetwaarde_buiten_bereik: boolean
```

of meer specifiek:
```text
meetstatus = NORMAL | OL | UNDER_RANGE | OVER_RANGE | UNKNOWN
```

Bij out-of-range:
- numerieke waarde niet als betrouwbare meting interpreteren;
- eindstatus doorgaans "niet te beoordelen";
- melding tonen dat bereik/toestelinstelling gecontroleerd moet worden.

---

## 22. Referentiedata

Huidige ingebouwde algemene tabel:
- Peak Atlas ESR70-achtig JSON-bestand.

Belangrijk:
- referentiedata systematisch verifiëren tegen originele bron;
- algemene tabellen zijn indicatief;
- specifieke datasheet blijft voorkeur;
- versie/snapshot van gebruikte referentie later bewaren in database.

---

## 23. Huidige assessment-architectuur

De `assessment_service` is GUI-onafhankelijk.

Logische keten:
```text
capaciteit
    ↓
ESR
    ↓
C-ESR-D consistentie
    ↓
betrouwbaarheid
    ↓
eindstatus
```

Dit is een goed ontwerpprincipe en moet behouden blijven.

GUI:
- verzamelt invoer;
- zoekt referentie;
- roept service aan;
- toont resultaat.

Service:
- bevat beoordelingslogica;
- geen GUI-code;
- geen databasecode.

---

## 24. Tests

Bestaande tests behandelen:
- µF/mF-conversie;
- mΩ/Ω-conversie;
- komma/punt;
- capaciteit;
- ESR-factor;
- frequentieverschil;
- C-ESR-D;
- betrouwbaarheid;
- eindstatus;
- volledige meetvoorbeelden.

Nieuwe tests nodig voor:
- exact op tolerantielimiet;
- EX_SITU;
- ONE_LEG;
- IN_CIRCUIT;
- exclusieve meetmethode;
- type mismatch;
- out-of-range/OL;
- referentie zonder frequentie;
- verkeerde condensatortechnologie;
- compact resultaatscenario;
- regressietests voor referentietabel.

---

## 25. Database — latere stap

Na ESR v1-logica en meetmethodecorrectie volgt SQLite.

Voorziene entiteiten:
- component;
- meting;
- referentieregel;
- meting-referentie-koppeling;
- eventueel assessment snapshot.

Belangrijk:
- oude beoordeling mag niet veranderen omdat referentietabel later wijzigt;
- gebruikte referentie dus als snapshot bewaren.

---

## 26. Export — latere stap

V1-doel:
- CSV;
- Excel.

Later:
- afdrukbaar meetrapport;
- eventueel PDF.

Export moet bevatten:
- ruwe waarden;
- eenheden;
- meetcontext;
- status;
- betrouwbaarheid;
- referentie;
- frequentie;
- redenen;
- waarschuwingen;
- referentiesnapshot.

---

## 27. Requirements

Huidige basis:
```text
PySide6>=6.7
pytest>=8.0
pandas>=2.2
openpyxl>=3.1
```

Nog niet toevoegen totdat nodig:
- numpy;
- scipy;
- Lcapy;
- Schemdraw;
- SKiDL;
- PySpice;
- PyEIS;
- overige experimentele tools.

---

## 28. Tool Hub — toekomst

De ESR-tool is module 1.

Later mogelijke modules:
- weerstand/kleurcode;
- spanning/stroom/vermogen;
- spanningsdelers;
- RC/RL/RLC;
- filters;
- diode/Zener/LED;
- transistor/MOSFET;
- opamps;
- circuit solver;
- schemaweergave;
- netlistanalyse;
- SPICE;
- kennisbank;
- componenthistoriek;
- diagnosewizard.

Zie:
```text
docs/future_tools.md
```

---

## 29. Belangrijkste externe libraries voor later

Hoogste interesse:
- Schemdraw;
- Lcapy;
- CircuitCalculator;
- SKiDL;
- PySpice.

Voor gespecialiseerde latere functies:
- PyEIS;
- C_ESR_METER als referentieproject;
- circuit-solver;
- pyams-lib.

Niet automatisch dependencies maken.

---

## 30. Ontwerpprincipes

- veiligheid vóór snelheid;
- datasheet vóór cheatsheet;
- exacte frequentie vóór grove vergelijking;
- ruwe meetgegevens altijd bewaren;
- geen verborgen correcties;
- beoordeling altijd uitleggen;
- meetcontext beïnvloedt betrouwbaarheid;
- verschillende condensatortypes krijgen aparte regels;
- geen verzonnen toestelprotocol;
- geen automatische frequentieomrekening zonder gevalideerd model;
- referentieversies bewaren;
- GUI compact en taakgericht;
- primaire workflow zonder scroll;
- details achter knoppen/dialogen;
- logica scheiden van GUI en opslag;
- externe libraries pas toevoegen wanneer werkelijk nodig;
- eerst ESR v1 goed maken, daarna verbreden.

---

## 31. Concrete eerstvolgende ontwikkelstap

### Fase A — ESR UI v1.2
1. `QScrollArea` uit primaire ESR-flow verwijderen.
2. veiligheidsregels uit hoofdscherm verwijderen.
3. knop `Veiligheidsinstructies` behouden.
4. invoervelden smaller maken.
5. scherm in compacte kolommen herindelen.
6. resultaat compact maken met detailknop.

### Fase B — meetmethode
1. `in_circuit: bool` vervangen door expliciete meetmethode.
2. keuzes:
   - EX_SITU
   - ONE_LEG
   - IN_CIRCUIT
3. reliability service aanpassen.
4. waarschuwingen aanpassen.
5. tests toevoegen.

### Fase C — ontbrekende validatie
1. type-match referentie.
2. out-of-range/OL.
3. referentiedata controleren.
4. regressietests.

### Fase D — opslag
1. databaseschema.
2. SQLite storage service.
3. component- en meetgeschiedenis.
4. referentiesnapshot.

### Fase E — kennisbank/uitbreiding
Pas wanneer ESR-flow stabiel is.

---

## 32. Definitie van “ESR v1 klaar”

ESR v1 is klaar wanneer:

- de gebruiker zonder scroll een meting kan invoeren;
- veiligheid bevestigd kan worden zonder grote tekstblokken;
- de drie meetmethoden correct bestaan;
- C, ESR en optioneel D ingevoerd kunnen worden;
- out-of-range geregistreerd kan worden;
- juiste referentie gekozen wordt;
- verkeerde condensatortypes niet automatisch fout beoordeeld worden;
- frequentieverschil zichtbaar is;
- betrouwbaarheid logisch bepaald wordt;
- resultaat compact én uitlegbaar is;
- alle relevante tests slagen;
- referentiedata gecontroleerd is;
- de app niet doet alsof een indicatieve tabel een fabrikantdatasheet is.

---

## 33. Richting op lange termijn

Het product moet uiteindelijk niet alleen antwoorden:

> “Is deze condensator goed?”

maar eerder:

> “Wat heb je gemeten, hoe betrouwbaar is die meting, hoe verhoudt die zich tot bekende gegevens, welke onzekerheden zijn er, en wat is de verstandigste volgende diagnosestap?”

Dat is het centrale concept voor alle toekomstige tools in deze applicatie.

## Update 2026-09-26 — ESR GUI v1.4

Uitgevoerd:
- invoervelden/comboboxen/tekstdialogen krijgen expliciet donker thema met hoog contrast;
- veiligheidsbevestiging is een echte checkbox, neutraal vóór bevestiging en groen na bevestiging;
- aluminium elektrolytisch krijgt in de GUI een wijzigbaar standaardvoorstel van ±20%;
- de tolerantie staat als echte veldwaarde in `QLineEdit`, zodat de assessment-service ze ontvangt;
- regressietest toegevoegd voor de praktijkmeting 330 µF / 35 V: 286,2 µF, 62,3 mΩ, D=1,1207 bij 10 kHz / 0,3 Vrms;
- venster-X blijft contextueel via `main_window.py`: op ESR-pagina terug naar Tool Hub, op Tool Hub applicatie afsluiten.

Belangrijk:
- ±20% is een GUI-voorstel voor aluminium elektrolytisch, geen universele fabrikantgarantie.
- Exacte datasheetwaarde blijft leidend.
- Geen automatische ESR-frequentieconversie.

## Update 2026-09-26 — ESR GUI v1.5

- Frequentiekeuze wordt getoond als `100 Hz`, `1 kHz`, `10 kHz`; intern blijven de waarden Hz.
- Compact resultaat toont nu capaciteitstolerantiegrenzen en gebruikte ESR-referentie.
- Details toont afgeleide ESR-zones op basis van de huidige configureerbare factoren.
- ESR-zones worden expliciet als indicatief aangeduid; ze zijn geen universele afkeurgrenzen.
- De ESR-data en bronselectie zijn in v1.5 bewust niet gewijzigd. Dat volgt in de aparte data-audit.
- Toekomstige data-architectuur: JSON per condensatortechnologie/type; nog niet implementeren vóór de bron-audit.

## Update 2026-09-26 — ESR GUI v1.5.1

- Bugfix: `\n` wordt niet meer letterlijk in de resultaatbalk weergegeven.
- Compact resultaat gebruikt drie regels: capaciteit, ESR en advies.
- Gemeten capaciteit en gemeten ESR worden rechtstreeks in de samenvatting getoond.
- Geen wijziging aan assessment-logica of ESR-referentiedata.
- Na visuele bevestiging is de GUI-fase afgesloten; volgende fase is data/logica-audit.

## 10. Qt-specifieke eigenaardigheden

- **`QApplication.setStyle("Fusion")`** moet voor
  `apply_dark_theme(app)` — anders negeert Qt CSS op
  `QRadioButton::indicator` en `QCheckBox::indicator`.
- **`QValueAxis.applyNiceNumbers()`** op een nog niet geattache
  reeks geeft `[nan - nan]`. Vermijd deze aanroep.
- **`QDateTime.fromMSecsSinceEpoch()`** accepteert een `qint64`.
  Klem absurde waarden op een veilig bereik.
- **`deleteLater()`** wordt niet verwerkt in tests zonder event loop.
  Gebruik `QApplication.processEvents()` in GUI-testfixtures.
- **QAction-parent:** een QAction hoort het menu als parent te hebben,
  niet het venster. Dan ruimt `deleteLater()` op het menu automatisch
  de acties op.
- **`QT_QPA_FONTDIR` op Windows:** Qt in een PySide6-venv kan de
  systeemfonts niet vinden zonder `QT_QPA_FONTDIR=C:\Windows\Fonts`.
  Zonder deze variabele rendert `QPrinter` PDF-rapporten met zwarte
  blokken in plaats van tekst. De HTML-viewer gebruikt de OS-fontstack
  en heeft dit probleem niet.
- **`QPrinter` en `QTextDocument`** zitten standaard bij PySide6; het
  zijn **geen** aparte dependencies. Idem voor `PySide6.QtCharts`.
- **`QChartView.grab()`** is de juiste manier om een grafiek als
  afbeelding te exporteren (voor het rapport). Werkt zonder extra
  dependency.

## Update 2026-10-16 — stand na fase 11C

Sinds de vorige update-blokken is het project doorgegroeid tot en met
fase 11C. De oorspronkelijke tekst in dit document blijft gelden als
**ontwerpprincipe en richting**, maar de operationele stand is nu:

**Versie:** `1.2.0`. **Baseline:** 1358 passed.

**Afgeronde fases sinds de vorige update:**
- 9A t/m 9H — build, GitHub-feedback, update-check.
- 10A — referentie-architectuur met frequentieprofielen.
- 10B — drempelvalidatie.
- 11A — export/import/selectie en mapvoorkeuren.
- 11B — betrouwbaarheidsregel herzien (inhoudelijk vs. administratief).
- 11C — iconen voor alle vensters.

**Nieuwe architectuuronderdelen:**
- `app/helpers/dialog_start_directory.py` (11A.3) — centrale
  startmaphelper voor `QFileDialog`.
- `app/helpers/icon_paths.py` (11C) — centrale icoonpadhelper met
  veilige fallback.
- `scripts/genereer_placeholders.py` (11C) — genereert de
  placeholder-iconen.
- `assets/icons/` — één applicatie-icoon plus twaalf thematische
  iconen.

**Belangrijke ontwerpbeslissingen sinds de vorige update:**
- De beoordelingslogica onderscheidt sinds 11B **inhoudelijke** en
  **administratieve** betrouwbaarheidsverlagers. Alleen inhoudelijke
  verlagers verhogen het minimum van de eindstatus.
- De ESR-referentie is sinds 10B **frequentie-specifiek**. De officiële
  ESR70-tabel op 100 kHz blijft de primaire bron voor 100 kHz; voor
  100 Hz, 1 kHz en 10 kHz bestaan geschatte profielen.
- Sinds 11A respecteert de export de selectie en worden
  mapvoorkeuren overal gerespecteerd.
- Sinds 11C heeft elk venster een icoon; ontbrekende iconen zijn geen
  fout en laten de GUI gewoon zonder icoon verder werken.

**Volgende fase:** 11D — i18n-menging in Diagnose/Result en
Resultaatdetails oplossen.

De tekst in §31 ("Concrete eerstvolgende ontwikkelstap") is historisch
en niet meer actueel. De actuele planning staat in `overdracht.md` §4
en §2.4.