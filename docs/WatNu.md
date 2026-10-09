
---

## Wat nu?

**Samenvatting van deze levering:**

1. **`docs/changelog.md`** — versie 1.6 toegevoegd.
2. **`docs/documentation_import.md`** — v1.3.0 met Word/Excel-sectie.
3. **`docs/openvragen.md`** — v1.4.0 met §2.8 (Word/Excel beantwoord) en §2.9 (nieuwe openstaande punten).
4. **`overdracht.md`** — v3.5.0, klaar voor een nieuwe chat met fase 7 als volgende.

**Verificatie:**
- Geen codewijziging, dus geen nieuwe tests nodig.
- De 999 passed blijft de baseline.

**Je kunt nu een nieuwe chat starten.** In die chat:

1. Plak de startprompt uit **sectie 1** van `overdracht.md` v3.5.0.
2. De nieuwe chat vraagt om de bestanden uit **sectie 8**.
3. De nieuwe chat stelt de vragen uit **sectie 6.2** (grafiekbibliotheek, locatie, types, etc.).
4. Na jouw antwoorden begint fase 7.

**Belangrijke opmerking voor de nieuwe chat:** de eerste beslissing is de **grafiekbibliotheek**. `matplotlib` is zwaar, `pyqtgraph` is Qt-native en licht, `QtCharts` is Qt-native maar vereist de PySide6-Charts module (die standaard bij PySide6 zit). Mijn voorkeur zou **QtCharts** zijn, tenzij je interactieve zoom/pan echt nodig hebt — dan is **pyqtgraph** beter.

Succes met fase 7.

9. WERKAFSPRAKEN IN EEN NIEUWE SESSIE
Vraag altijd om de huidige bestandsinhoud voordat je een bestaand
bestand vervangt.

Uitzondering: als je het bestand in deze sessie al hebt geleverd
of gezien en er is geen tegenspraak, mag je het direct hergebruiken.

Lever altijd volledige bestanden, nooit secties met
# ... ongewijzigd ....

Lever volledige JSON-bestanden, nooit fragmenten.

Draai eerst gerichte tests, dan volledige pytest -q.

Meld nieuwe i18n-keys expliciet, met de waarde voor NL én EN.

Python-headers zijn cumulatief. Nieuwe versies krijgen een nieuwe
regel bovenaan de Wijzigingen:-lijst; oudere regels blijven staan.

Geen aannames over de eerstvolgende fase — vraag het na.

9.1 Specifieke afspraken voor fase 7
Read-only. De analyse-laag leest, schrijft nooit.

Historische data niet herberekenen. Gebruik de assessment-
snapshot, niet de huidige regels.

Grafiekbibliotheek eerst afstemmen. Niet stil een dependency
toevoegen.

Kleine stappen. Eerst een simpele lijngrafiek met één filter,
dan uitbreiden.

Testbaar zonder GUI. De aggregaties horen in een GUI-onafhankelijke
module, niet in de GUI-code.