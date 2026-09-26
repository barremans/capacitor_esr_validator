# ESR v1.2 update

Deze map bevat de bestanden voor de volgende ontwikkelfase.

## Bestanden

- `app/gui/esr_test_screen.py` — v1.2.0
- `app/services/assessment_service.py` — v1.1.0
- `app/config/settings.py` — v1.1.0
- `i18n/locales/nl_NL.json`
- `i18n/locales/en_US.json`
- `tests/test_assessment.py` — v1.1.0
- `tests/test_units.py` — ongewijzigd

## Belangrijkste wijzigingen

- primaire ESR-flow zonder `QScrollArea`;
- veiligheidsregels achter knop;
- smallere invoervelden;
- drie exclusieve meetmethoden;
- betrouwbaarheid per meetmethode;
- OL/out-of-range;
- type-mismatch van referentie verlaagt betrouwbaarheid;
- compact resultaat + aparte detaildialoog;
- Python headers met versie/datum/changelog behouden en bijgewerkt.

## Installeren

Maak eerst een backup of commit.

Kopieer daarna de bestanden over de overeenkomstige projectpaden.

Run vervolgens:

```powershell
pytest
python main.py
```

## Versiebeheerconventie

Pythonbestanden houden bovenaan het bestaande standaardheaderformaat aan:

- Module
- Project
- Versie
- Datum
- Auteur
- Doel
- Wijzigingen
- Versiebeheer

SemVer:
- MAJOR = incompatibele architectuur/API;
- MINOR = nieuwe functionaliteit;
- PATCH = bugfix/refactor.
