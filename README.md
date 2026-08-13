# Condensator- en ESR-validator

Nederlandstalige Windows-app voor het registreren en indicatief
beoordelen van condensatormetingen (aluminium elektrolytisch, v1).

Status: prototype in opbouw. Zie `docs/` voor het functioneel ontwerp,
het gegevensmodel en de validatieregels vóór er in de code gekeken
wordt — die documenten zijn de bron van waarheid voor elke beslissing.

## Structuur

Zie `PROJECT_STRUCTURE.md` in de projectkennis voor de volledige
mapindeling en naamgevingsconventies.

## Tests uitvoeren

```
pip install pytest
python -m pytest tests/ -v
```
