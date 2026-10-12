# Electronics Diagnostic Tool Hub / ESR Tester

Een lokale Windows-applicatie voor het diagnosticeren van elektronische componenten. De primaire tool is een **ESR- en condensator-validator**. De applicatie is opgezet als een **Tool Hub** waar in latere fases ook andere diagnosetools (zoals een weerstandstester) kunnen worden toegevoegd.

**Versie:** zie `app/version.py`  
**Baseline tests:** zie `overdracht.md`

---

## Wat doet de applicatie?

- **ESR- en condensator-diagnose** — voer een meting in, krijg een onderbouwd oordeel met bron, betrouwbaarheid en vervolgstap.
- **Historiek** — sla metingen lokaal op en bekijk ze later terug.
- **Documentatie** — een meertalige technische bibliotheek met onder meer veilig ontladen, meetmethoden, LCR-meter, dissipatiefactor en C-ESR-D-plausibiliteit.
- **Analyse** — grafieken en trends van je opgeslagen metingen.
- **Rapportage** — één meting omzetten in een leesbaar HTML- of PDF-rapport.

Alles werkt **lokaal en offline**.

---

## Installatie

### Voor eindgebruikers

Een installer voor Windows is **nog niet beschikbaar**; die staat gepland voor een latere fase.

### Voor ontwikkelaars

Vereist: **Python 3.12** op Windows 10 of 11.

```powershell
# Kloon of pak het project uit.
cd capacitor_esr_validator

# Maak een virtuele omgeving en activeer die.
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Installeer de dependencies.
pip install -r requirements.txt

# Start de applicatie.
python main.py
```

De applicatie gebruikt een lokale SQLite-database op `%LOCALAPPDATA%\ElectronicsDiagnosticToolHub\measurements.sqlite3`. Bij het eerste gebruik wordt die automatisch aangemaakt.

## Tests draaien

```powershell
# Eerst gerichte tests van een fase:
pytest tests/test_<fase>.py -q

# Daarna de volledige suite:
pytest -q
```

GUI-tests draaien met `QT_QPA_PLATFORM=offscreen`. Er is geen `pytest-qt`-dependency; tests gebruiken `QApplication.instance()` of `QApplication([])`.

## Projectstructuur

Zie `PROJECT_STRUCTURE.md` voor een automatisch gegenereerde mappenstructuur. Kort:

```text
app/
├── config/         — instellingen en instrumentprofielen
├── data/           — ingebouwde referenties en documentatie
├── documentation/  — documentatie-import (PDF, Word, Excel, URL)
├── gui/            — hoofdvenster, schermen en dialogen
├── helpers/        — pure helpers (units, i18n, formatting, enz.)
├── services/       — assessment, persistence, history, analysis,
│                     report
└── storage/        — SQLite, migraties, modellen
docs/               — ontwikkelaarsdocumentatie
i18n/locales/       — vertaalbestanden (NL/EN)
tests/              — pytest-suite
```

## Documentatie voor ontwikkelaars

| Bestand | Doel |
|---|---|
| `overdracht.md` | Primaire bron voor een nieuwe sessie |
| `docs/context.md` | Architectuur en ontwerpprincipes |
| `docs/changelog.md` | Versiegeschiedenis voor de gebruiker |
| `docs/openvragen.md` | Levende lijst van open vragen |
| `docs/search_syntax.md` | Zoektaal van de documentatiebibliotheek |
| `docs/python_header_standard.md` | Header-standaard |
| `docs/documentation_import.md` | Import-laag (technisch) |
| `docs/future_tools.md` | Roadmap en dependencybeleid |
| `docs/help/nl_NL.md`, `docs/help/en_US.md` | Eindgebruikershelp |

## Bijdragen

Dit is een persoonlijk project. Als je een bijdrage wilt leveren:

1. Lees `overdracht.md` en `docs/context.md`.
2. Respecteer de kernregels in `overdracht.md` §3.
3. Voeg tests toe voor elke wijziging.
4. Draai de volledige suite vóór je commit.

## Licentie

Zie `LICENSE`.
