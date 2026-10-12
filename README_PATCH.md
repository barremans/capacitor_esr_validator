# README_PATCH.md

Dit bestand beschrijft **kleine, tijdelijke patchinstructies** die niet in `README.md` thuishoren. Gebruik het voor eenmalige fixes, tijdelijke workarounds of release-specifieke notities.

---

## Status

**Actueel:** geen openstaande patches.

---

## Eerdere patches

### 2026-10-12 — `QT_QPA_FONTDIR` op Windows

Tijdens fase 8D+ bleek dat PDF-rapporten op Windows **zwarte blokken**
toonden in plaats van tekst. Oorzaak: Qt in een PySide6-venv kan de
systeemfonts niet vinden zonder expliciete font-directory.

**Workaround:** stel vóór het starten van de applicatie de omgevingsvariabele in:

```powershell
$env:QT_QPA_FONTDIR = "C:\Windows\Fonts"
python main.py
```

**Status:** workaround werkt. Structurele oplossing (variabele
automatisch zetten in `main.py`) staat op de roadmap voor fase 11.

**Actie voor eindgebruikers:** voer het bovenstaande commando uit bij het starten.

**Actie voor ontwikkelaars:** overweeg om in `main.py` vóór
`QApplication` de variabele te zetten als hij nog niet bestaat.

---

### 2026-10-10 — `debug_menu.py` tijdelijk toegevoegd

Tijdens fase 8C is een tijdelijk diagnoscript `debug_menu.py` in de projectroot geplaatst om een menuprobleem te onderzoeken. Dat script is **niet** bedoeld voor productie en kan veilig verwijderd worden.

**Status:** opgelost. Het script is niet meer nodig en mag verwijderd worden.

**Actie voor eindgebruikers:** niets.

**Actie voor ontwikkelaars:** verwijder `debug_menu.py` als het nog in je working tree staat.

---

## Hoe dit bestand te gebruiken

- Voeg een nieuwe sectie toe onder "Eerdere patches" voor elke patch.
- Gebruik de datum als kop.
- Beschrijf kort: wat, waarom, en welke actie nodig is.
- Sluit een patch af met **"Status: opgelost"** zodra die niet meer relevant is.

Dit bestand is **niet** de changelog. Voor gebruikersgerichte wijzigingen: zie `docs/changelog.md`.