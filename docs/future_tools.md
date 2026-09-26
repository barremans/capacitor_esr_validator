# Future tools & libraries

**Project:** Condensator- en ESR-validator / Electronics Diagnostic Tool Hub  
**Status:** Roadmapdocument — geen van onderstaande libraries is momenteel verplicht voor de ESR-tool.  
**Doel:** Interessante externe libraries en projecten bijhouden voor latere uitbreiding van de applicatie naar een bredere diagnose- en kennisbanktool voor elektronica.

---

## 1. Uitgangspunt

De huidige ontwikkelfocus blijft:

1. ESR- en condensatordiagnose afwerken.
2. In-circuit, één aansluiting los en volledig uitgebouwd correct ondersteunen.
3. Betrouwbare beoordeling op basis van capaciteit, ESR, D, referentiebron en meetcontext.
4. Compacte, praktische GUI zonder onnodige complexiteit.
5. Pas daarna uitbreiden met bijkomende elektronische diagnose- en rekentools.

Deze roadmap voorkomt dat interessante externe libraries verloren gaan, zonder ze nu al als dependency in `requirements.txt` op te nemen.

---

## 2. Kandidaten voor latere integratie

### 2.1 C_ESR_METER
**URL:** https://github.com/latchdevel/C_ESR_METER

**Mogelijke toepassing**
- Referentie voor praktische ESR-meetprincipes.
- Vergelijken van meetmethodes en berekeningen.
- Inspiratie voor condensator- en ESR-diagnostiek.
- Mogelijke ideeën voor kalibratie of meetvalidatie.

**Relevantie:** Hoog voor de huidige ESR-tool.  
**Status:** Onderzoeken, niet rechtstreeks integreren vóór architectuur, algoritmes, meetfrequentie, kalibratie en licentie beoordeeld zijn.

### 2.2 PyEIS
**URL:** https://github.com/kbknudsen/PyEIS

**Mogelijke toepassing**
- Electrochemical Impedance Spectroscopy.
- Bode- en Nyquist-analyse.
- Equivalent-circuit fitting.
- Analyse van frequentiesweeps.
- Latere geavanceerde impedantieanalyse.

**Relevantie huidige ESR-tool:** Laag.  
**Relevantie advanced diagnostics:** Hoog.  
**Status:** Bewaren voor latere uitbreiding.

### 2.3 CircuitCalculator
**URL:** https://pypi.org/project/CircuitCalculator/

**Mogelijke toepassing**
- DC- en AC-circuitberekeningen.
- Nodale analyse.
- Mogelijke rekenengine voor een ingebouwde circuit solver.

**Relevantie:** Hoog.  
**Status:** Later evalueren.

### 2.4 circuit-solver
**URL:** https://github.com/daniyalmaroufi/circuit-solver

**Mogelijke toepassing**
- Referentie voor circuitoplossing.
- Inspiratie voor interactieve circuitanalyse.

**Relevantie:** Middel.  
**Status:** Architectuur, API, onderhoudsstatus en licentie beoordelen.

### 2.5 manim-circuit
**URL:** https://pypi.org/project/manim-circuit/

**Mogelijke toepassing**
- Geanimeerde schakelingen.
- Educatieve uitleg en trainingsmodus.

**Relevantie:** Laag.  
**Status:** Geen prioriteit.

### 2.6 pyams-lib
**URL:** https://pypi.org/project/pyams-lib/

**Mogelijke toepassing**
- Analoge modellering.
- Mixed-signal simulatie.
- Eigen componentmodellen.

**Relevantie:** Middel.  
**Status:** Later onderzoeken; licentie en afhankelijkheden eerst controleren.

### 2.7 SKiDL
**URL:** https://pypi.org/project/skidl/

**Mogelijke toepassing**
- Schakelingen beschrijven in Python.
- Netlists genereren.
- Koppeling met EDA/PCB-workflows.
- Latere schema- of netlistgestuurde diagnose.

**Relevantie:** Middel tot hoog.  
**Status:** Interessant voor latere circuit/netlist-module.

### 2.8 Schemdraw
**URL:** https://pypi.org/project/schemdraw/

**Mogelijke toepassing**
- Automatisch tekenen van schema's.
- Visuele uitleg bij diagnoses.
- Meetopstellingen tonen.
- Kennisbankdiagrammen.

**Relevantie:** Hoog.  
**Status:** Sterke kandidaat zodra de ESR-tool stabiel is.

### 2.9 Lcapy
**URL:** https://pypi.org/project/lcapy/

**Mogelijke toepassing**
- Symbolische lineaire circuitanalyse.
- RLC-analyse.
- Transferfuncties.
- Impedantie- en frequentieanalyse.
- SPICE-achtige netlists.

**Relevantie:** Hoog.  
**Status:** Sterke kandidaat voor analyse- en kennisbankfunctionaliteit.

### 2.10 PySpice
**URL:** https://pyspice.fabrice-salvaire.fr/releases/v1.4/

**Mogelijke toepassing**
- SPICE-simulatie vanuit Python.
- DC, AC sweep, transient en noise.
- Meting versus simulatie vergelijken.

**Relevantie:** Hoog voor latere geavanceerde uitbreiding.  
**Status:** Niet opnemen in v1.  
**Aandachtspunt:** Extra installatiecomplexiteit door externe SPICE-engine.

### 2.11 circuit
**URL:** https://pypi.org/project/circuit/

**Mogelijke toepassing:** Nog te onderzoeken.  
**Relevantie:** Onbekend / laag.  
**Status:** Eerst overlap met Lcapy, CircuitCalculator en PySpice evalueren.

### 2.12 pyelectronics
**URL:** https://pypi.org/project/pyelectronics/

**Mogelijke toepassing**
- Mogelijke communicatie met fysieke elektronica of randapparatuur.

**Relevantie:** Laag voor de huidige desktopdiagnosetool.  
**Status:** Alleen opnieuw bekijken wanneer directe hardwarecommunicatie nodig wordt.

---

## 3. Mogelijke uitbreidingsrichting

De applicatie kan evolueren van een ESR-validator naar een bredere **Electronics Diagnostic Tool Hub** met onder meer:

- ESR / condensatordiagnose
- capaciteit en tolerantie
- lekstroomregistratie
- weerstandscalculator en kleurcode
- vermogen en spanningsdeler
- RC/RL/RLC-calculators
- filterberekening
- diode/Zener/LED-diagnose
- BJT- en MOSFET-hulpmiddelen
- opamp-tools
- circuit solver
- schemaweergave
- netlistanalyse
- SPICE-simulatie
- Bode/Nyquist
- componentvergelijking
- componenthistoriek
- elektronica-kennisbank
- diagnosewizard op basis van symptomen en metingen

---

## 4. Voorgestelde technische lagen

### GUI
- Huidig: PySide6
- Later: Schemdraw voor schema's en meetdiagrammen

### Rekenen / symbolische analyse
- CircuitCalculator
- Lcapy
- eventueel SymPy rechtstreeks

### Netlists / circuitbeschrijving
- SKiDL
- Lcapy

### Simulatie
- PySpice
- eventueel pyams-lib voor specifieke use-cases

### Advanced impedance
- PyEIS
- eventueel eigen frequentiesweep-module

---

## 5. Dependencybeleid

Niet alle mogelijke libraries in `requirements.txt` opnemen.

Regel:
- alleen dependency toevoegen wanneer een concrete appmodule die echt gebruikt;
- zware of optionele dependencies later bij voorkeur als optionele extra's behandelen;
- ESR v1 blijft licht en lokaal.

Huidige kernrequirements:
```text
PySide6>=6.7
pytest>=8.0
pandas>=2.2
openpyxl>=3.1
```

---

## 6. Evaluatiecriteria vóór integratie

Voor elke externe library eerst controleren:

1. actief onderhoud;
2. Python-versiecompatibiliteit;
3. Windows-compatibiliteit;
4. licentie;
5. installatiecomplexiteit;
6. documentatie;
7. testdekking;
8. overlap met bestaande functionaliteit;
9. nut voor de gebruiker;
10. mogelijkheid om functionaliteit optioneel te houden.

---

## 7. Prioriteit

**Na ESR v1**
1. Schemdraw
2. Lcapy
3. CircuitCalculator

**Daarna**
4. SKiDL
5. PySpice
6. PyEIS

**Alleen indien nodig**
7. circuit-solver
8. pyams-lib
9. manim-circuit
10. circuit
11. pyelectronics

---

## 8. Belangrijk ontwerpprincipe

De applicatie moet geen verzameling losse calculators worden.

Elke nieuwe tool moet bijdragen aan één centraal doel:

> een praktische diagnose- en kennisbanktool voor elektronica waarmee een gebruiker meetwaarden kan invoeren, resultaten kan begrijpen, met betrouwbare referenties kan vergelijken en een onderbouwde volgende diagnosestap krijgt.
