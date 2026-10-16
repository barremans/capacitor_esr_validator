# Iconen

Deze map bevat de visuele identiteit van de applicatie.

## Bestanden

### Applicatie-icoon

- **`app.png`** — 256×256, transparant. Bron voor Qt
  (`QApplication.setWindowIcon()` en `QWidget.setWindowIcon()`).
- **`logo.ico`** — het enige ICO-bestand van de applicatie. Wordt
  gebruikt door:
  - PyInstaller (`EXE(icon=r"assets\icons\logo.ico")`) voor het
    EXE-icoon;
  - Inno Setup (`SetupIconFile=...\assets\icons\logo.ico`) voor het
    installer-icoon.
  - Moet de resoluties 16, 32, 48, 64, 128 en 256 bevatten.

### Thematische iconen

Elk icoon is 64×64, transparant, en heeft dezelfde stijl: donkerblauw
(`#1F4E79`) als hoofdkleur, cyaan (`#4AA3FF`) als accent.

| Bestand | Gebruikt voor |
|---|---|
| `diagnose.png` | Hub-knop **Diagnose**, menu-item **Diagnose openen** |
| `esr.png` | ESR-testknop in Diagnose, hub-knop **ESR-test**, menu-item **ESR-test** |
| `history.png` | Hub-knop **Historiek**, menu-item **Historiek** (via Diagnose) |
| `documentation.png` | Hub-knop **Documentatie**, menu-item **Documentatie zoeken…** |
| `analysis.png` | Hub-knop **Analyse**, menu-item **Analyse** |
| `report.png` | Menu-item **Rapport maken…**, knoppen **Rapport** in Historiek, Analyse en ReportDialog |
| `settings.png` | Menu-item **Instellingen…** |
| `help.png` | Menu-item **Help** (F1) |
| `bug.png` | Menu-item **Bug of feature melden…** |
| `update.png` | Menu-item **Controleren op updates…** |
| `exit.png` | Menu-item **Afsluiten** |

## Placeholders

De huidige iconen zijn **placeholders** die met
`scripts/genereer_placeholders.py` zijn gegenereerd. Ze zijn bewust
eenvoudig en vlak, zodat de GUI-code volledig afgewerkt en getest kan
worden zonder te wachten op een definitief ontwerp.

Je kunt ze op elk moment vervangen door definitieve ontwerpen. De
bestandsnamen liggen vast; de code hoeft dan niet te veranderen.

Draai het script één keer vanuit de projectroot:

```powershell
python scripts\genereer_placeholders.py
```

## Afspraken

- **Bestandsnamen zijn in kleine letters**, ook op Windows. Dat is
  nodig voor clones op case-sensitive bestandssystemen (Linux, macOS,
  CI).
- **Het ICO-bestand is de bron van waarheid voor alle builds.**
  Wijzig het niet handmatig; vervang het in één keer door een nieuw
  ICO met dezelfde naam.
- **De bestandsnaam `logo.ico` ligt vast.** De `.spec` en `.iss`
  verwijzen er rechtstreeks naar.
- **Ontbrekende iconen zijn geen fout.** `app/helpers/icon_paths.py`
  geeft `None` terug als een icoon niet bestaat, en de GUI laat het
  icoon dan weg. De applicatie blijft werken.

  ## Vervangen door definitieve ontwerpen

De placeholders zijn bedoeld om vervangen te worden. Werkwijze:

1. Teken of exporteer je definitieve ontwerpen op 256×256 (PNG,
   transparant) en 64×64 (PNG, transparant) voor de thematische
   iconen.
2. Genereer een nieuw `logo.ico` met de resoluties 16, 32, 48, 64,
   128 en 256.
3. Overschrijf de bestanden in deze map met dezelfde bestandsnamen.
4. Draai de tests:

   ```powershell
   pytest tests/test_icon_paths.py -q
   pytest -q
   ```

De code hoeft niet te veranderen. De helper `icon_paths` leest de
bestanden bij het opstarten.