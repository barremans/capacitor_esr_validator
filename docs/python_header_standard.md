# Python file header & versiebeheer — projectstandaard

Gebruik dit formaat bovenaan elk Pythonbestand in dit en toekomstige projecten.

```python
"""
================================================================================
Module:     pad/naar/module.py
Project:    Projectnaam
Versie:     1.0.0
Datum:      YYYY-MM-DD
Auteur:     <auteur>

Doel:       Korte omschrijving van de verantwoordelijkheid van deze module.

Wijzigingen:
  v1.0.0 (YYYY-MM-DD)  Initiële versie.

Versiebeheer:
  - MAJOR: incompatibele architectuur- of API-wijziging.
  - MINOR: nieuwe functionaliteit die compatibel blijft met het projectdoel.
  - PATCH: bugfix, kleine optimalisatie of interne refactor.
  - Bij elke wijziging: Versie, Datum en Wijzigingen hierboven bijwerken.
================================================================================
"""
```

## Regels

- Bestandsversie hoort bij het bestand, niet automatisch bij de applicatieversie.
- Nieuwe functionaliteit: MINOR verhogen.
- Alleen bugfix/refactor: PATCH verhogen.
- Breaking API/architectuur: MAJOR verhogen.
- Nooit een bestaande changelogregel overschrijven; nieuwe regel toevoegen.
- Datum is de datum waarop de betreffende bestandsversie wordt gemaakt.
- Functie- en klassedocstrings blijven daarnaast verplicht waar ze de bedoeling verduidelijken.
