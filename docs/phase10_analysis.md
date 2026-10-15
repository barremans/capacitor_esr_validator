<!--
Modulepad: capacitor_esr_validator/docs/phase10_analysis.md
Doel: Vastleggen wat de 72 LCR-ST1-metingen leren over de
      referentiedrempels, welk besluit is genomen voor 10B, en wat de
      resultaten van de implementatie zijn.
Status: analysedocument, geen code.
-->

# Fase 10B — Analyse van de 72 praktijkmetingen

**Versie:** 1.1.0
**Datum:** 2026-10-15
**Auteur:** Bart Bossuyt
**Doel:** Vastleggen wat de 72 LCR-ST1-metingen leren over de
referentiedrempels, welk besluit is genomen voor 10B, en wat de
resultaten van de implementatie zijn.

**Status:** analysedocument, 10B is afgerond.

---

## 1. Samenvatting

De 72 metingen zijn op **1 kHz** en **10 kHz** gedaan met de LCR-ST1.
De nieuwe referentie uit stap 10A is de **officiële ESR70-tabel op
100 kHz**. Dat is een structurele mismatch: ESR daalt met frequentie,
dus de factor `gemeten / referentie` wordt systematisch te laag.

Met de nieuwe referentie zakken vrijwel alle factoren voor goede
condensatoren naar **≤ 0,5**. Dat betekent dat de bestaande drempels
`≤1,0 / ≤2,0 / ≤3,0` niet meer passen: alles valt in "waarschijnlijk
normaal", ook exemplaren die er in de praktijk verdacht uitzien.

Er is gekozen voor **Optie B**: frequentie-specifieke referenties op
basis van Nichicon-frequentiecoëfficiënten, met een duidelijke
markering als schatting.

**Resultaat na 10B:** de nieuwe referenties werken; de drempels blijven
ongewijzigd; de steekproef bevestigt dat goede condensatoren nu
factoren 0,09–0,41 hebben.

---

## 2. De oorspronkelijke factoren (100 kHz-referentie)

Voor de waarden waar meerdere exemplaren van zijn gemeten, met de
oude 100 kHz-referentie.

### 220 µF / 25 V — referentie = 840 mΩ @ 100 kHz

| Meting | Freq | Gemeten ESR | Oude factor |
|---|---|---|---|
| id 30 | 1 kHz | 193 mΩ | 1,07 |
| id 34 | 1 kHz | 190 mΩ | 1,06 |
| id 32 | 1 kHz | 190 mΩ | 1,05 |
| id 33 | 10 kHz | 151 mΩ | 0,84 |
| id 35 | 10 kHz | 151 mΩ | 0,84 |
| id 31 | 10 kHz | 152 mΩ | 0,85 |

### 470 µF / 25 V — referentie = 400 mΩ @ 100 kHz

| Meting | Freq | Gemeten ESR | Oude factor |
|---|---|---|---|
| id 15 | 1 kHz | 183 mΩ | 1,52 |
| id 10 | 1 kHz | 177 mΩ | 1,47 |
| id 12 | 1 kHz | 180 mΩ | 1,50 |
| id 11 | 10 kHz | 148 mΩ | 1,23 |
| id 13 | 10 kHz | 152 mΩ | 1,27 |
| id 16 | 10 kHz | 153 mΩ | 1,28 |

### 1000 µF / 16 V — referentie = 210 mΩ @ 100 kHz

| Meting | Freq | Gemeten ESR | Oude factor |
|---|---|---|---|
| id 21 | 1 kHz | 114 mΩ | 1,42 |
| id 19 | 1 kHz | 114 mΩ | 1,43 |
| id 17 | 1 kHz | 115 mΩ | 1,44 |
| id 22 | 10 kHz | 96 mΩ | 1,21 |
| id 20 | 10 kHz | 99 mΩ | 1,23 |
| id 18 | 10 kHz | 92 mΩ | 1,15 |

### 330 µF / 35 V — referentie = 340 mΩ @ 100 kHz

| Meting | Freq | Gemeten ESR | Oude factor |
|---|---|---|---|
| id 50 | 10 kHz | 78 mΩ | 0,43 |
| id 55 | 10 kHz | 76 mΩ | 0,42 |
| id 52 | 10 kHz | 82 mΩ | 0,45 |
| id 49 | 1 kHz | 99 mΩ | 0,55 |
| id 51 | 1 kHz | 99 mΩ | 0,55 |
| id 53 | 1 kHz | 100 mΩ | 0,55 |
| id 56 | 1 kHz | 128 mΩ | 0,71 |

---

## 3. De kernconclusie (vóór 10B)

Met de nieuwe officiële ESR70-referentie (100 kHz) zakken alle
factoren voor goede condensatoren naar **≤ 0,55** in deze steekproef.
Dat had drie gevolgen:

1. De drempels `≤1,0 / ≤2,0 / ≤3,0` zijn te ruim. Goede condensatoren
   komen nooit meer in "aandachtspunt" of "verdacht".
2. De mismatch tussen meetfrequentie (1 kHz / 10 kHz) en
   referentiefrequentie (100 kHz) is een structureel probleem.
3. De oude "waarschijnlijk defect"-meldingen kwamen vooral van de
   oude te strenge referentie, niet van echte defecten.

---

## 4. Drie strategieën

### Optie A — Nieuwe drempels voor de nieuwe referentie

De drempels worden verlaagd om de lagere factoren op te vangen,
bijvoorbeeld:

| Factor | Status |
|---|---|
| ≤ 0,5 | waarschijnlijk normaal |
| 0,5 – 1,0 | aandachtspunt |
| 1,0 – 2,0 | verdacht |
| > 2,0 | waarschijnlijk defect |

**Nadeel:** de drempels compenseren voor de frequentie-mismatch,
maar de mismatch blijft in de code zitten. De app blijft dan vergelijken
wat niet vergelijkbaar is.

### Optie B — 100 kHz-referentie vervangen door frequentie-specifieke referenties

De 1 kHz- en 10 kHz-profielen worden gevuld met schattingen op basis
van de Nichicon-frequentiecoëfficiënten. Dan is de referentie op
dezelfde frequentie als de meting, en blijven de drempels
`≤1,0 / ≤2,0 / ≤3,0` zinvol.

**Nadeel:** de 1 kHz- en 10 kHz-schattingen zijn niet officieel.

### Optie C — Hybride

100 kHz blijft primair. Voor 1 kHz en 10 kHz wordt een expliciete
frequentie-correctiefactor toegepast op de factor.

**Nadeel:** complex om uit te leggen, en de app moet twee soorten
factoren onderscheiden (ruw en gecorrigeerd).

---

## 5. Gekozen aanpak — Optie B

**Optie B, met een duidelijk gemarkeerde schatting.**

Waarom:

- De LCR-ST1 meet op 1 kHz en 10 kHz. De referentie hoort op dezelfde
  frequentie te staan.
- De Nichicon-frequentiecoëfficiënten geven een redelijke eerste
  schatting.
- De gebruiker ziet in de app dat het om een schatting gaat, niet om
  een datasheet-waarde.
- De drempels `≤1,0 / ≤2,0 / ≤3,0` blijven werken zoals bedoeld.

### Schattingsfactoren

De officiële ESR70-referentie is 100 kHz. Om van daar naar 1 kHz en
10 kHz te gaan, gebruiken we de Nichicon-frequentiecoëfficiënten:

| Frequentie | Correctiefactor t.o.v. 100 kHz |
|---|---|
| 100 kHz | 1,00 |
| 10 kHz | 1,15 |
| 1 kHz | 1,50 |
| 100 Hz | 2,00 |

---

## 6. Resultaten na 10B — herberekening van de 72 metingen

Na de implementatie van 10B zijn de 72 metingen opnieuw doorgerekend
met het script `scripts/herbereken_steekproef.py`.

### 6.1 Nieuwe referentiewaarden

| Frequentie | Oude referentie (100 kHz) | Nieuwe referentie |
|---|---|---|
| 1 kHz (470 µF / 25 V) | 400 mΩ | **600 mΩ** (× 1,50) |
| 10 kHz (470 µF / 25 V) | 400 mΩ | **460 mΩ** (× 1,15) |
| 100 Hz (470 µF / 25 V) | 400 mΩ | **800 mΩ** (× 2,00) |

### 6.2 Nieuwe factoren voor goede condensatoren

| Situatie | Oud (100 kHz) | Nieuw (1/10 kHz) |
|---|---|---|
| 220 µF / 25 V, 1 kHz | 1,05–1,07 | **0,15–0,20** |
| 220 µF / 25 V, 10 kHz | 0,84–0,85 | **0,15–0,16** |
| 470 µF / 25 V, 1 kHz | 1,47–1,52 | **0,25–0,31** |
| 470 µF / 25 V, 10 kHz | 1,23–1,28 | **0,32–0,33** |
| 1000 µF / 16 V, 1 kHz | 1,42–1,44 | **0,36–0,37** |
| 1000 µF / 16 V, 10 kHz | 1,15–1,23 | **0,38–0,41** |
| 330 µF / 35 V, 1 kHz | 0,55–0,71 | **0,09–0,12** |
| 330 µF / 35 V, 10 kHz | 0,42–0,45 | **0,09–0,10** |

Alle goede exemplaren zitten nu **ruim onder 1,0**.

### 6.3 Verdeling van de nieuwe statussen

| Status | Aantal |
|---|---|
| aandachtspunt | 50 |
| twijfelachtig | 9 |
| waarschijnlijk_defect | 17 |

**Opvallend:** de statussen zijn nauwelijks veranderd t.o.v. de oude
situatie. Dat komt omdat de status nu vooral door de
**betrouwbaarheid** en de **capaciteitsafwijking** wordt bepaald, niet
meer door de ESR-factor.

---

## 7. Conclusies

1. **De nieuwe referenties werken.** Goede condensatoren hebben nu
   factoren 0,09–0,41. Dat is een gezonde verdeling.
2. **De drempels `≤1,0 / ≤2,0 / ≤3,0` blijven ongewijzigd.** De
   structuur is nu goed; het fijnstellen kan later met een grotere
   dataset.
3. **Echte defecten blijven zichtbaar.** Metingen met een
   eenhedenfout of een werkelijk defecte condensator vallen ook met
   de nieuwe referenties ruim buiten elke drempel.
4. **Open UX-punt:** de regel "betrouwbaarheid laag → minstens
   aandachtspunt" verbergt goede resultaten wanneer alleen
   administratieve gegevens ontbreken (fabrikant/serie onbekend).
   Zie `docs/openvragen.md` §2.26.

---

## 8. Implementatie-overzicht

**Gewijzigde bestanden:**

- `app/data/references/esr_references.json` — profielen 100 Hz, 1 kHz
  en 10 kHz gevuld met de volledige ESR70-tabel, geschaald met
  1,50 / 1,15 / 2,00.
- `app/services/assessment_service.py` v1.4.0 — `Beoordeling` heeft
  het veld `referentiefrequentie_hz`.
- `app/gui/esr_test_screen.py` v1.12.0 — toont werkelijke
  referentiefrequentie; geeft `meetfrequentie_hz` door aan
  `zoek_referentie`.
- `i18n/locales/nl_NL/esr.json` en `i18n/locales/en_US/esr.json` —
  nieuwe key `resultaat.referentiefrequentie`.

**Nieuwe bestanden:**

- `scripts/herbereken_steekproef.py` v1.1.0 — eenmalig analyse-
  draaiboek.

**Tests:**

- `tests/test_references.py` v1.1.0 — tests voor profielselectie en
  schalingsfactoren.
- `tests/test_assessment.py` v1.4.0 — tests voor
  `referentiefrequentie_hz`.

**Baseline:** 1297 passed.

---

## 9. Databestand

De 72 metingen staan in:
- `historiek_overzicht_2026-10-15_15-51-41.csv` (mensleesbaar)
- `historiek_detail_2026-10-15_15-51-41.csv` (machineleesbaar)

De factoren in die CSV's zijn berekend met de **oude** referentie.
Met de nieuwe referentie zijn de factoren herberekend met
`scripts/herbereken_steekproef.py`.

---

## 10. Versie

Document: Fase 10B — Analyse van de 72 praktijkmetingen
Versie: 1.1.0
Datum: 2026-10-15
Status: 10B is afgerond.