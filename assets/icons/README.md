# Iconen

Deze map bevat de visuele identiteit van de applicatie.

## Bestanden

- **`logo.ico`** — het enige icoonbestand van de applicatie. Wordt gebruikt door:
  - PyInstaller (`EXE(icon=r"assets\icons\logo.ico")`) voor het EXE-icoon;
  - Inno Setup (`SetupIconFile=...\assets\icons\logo.ico`) voor het installer-icoon;
  - Qt (`QIcon("assets/icons/logo.ico")`) voor de venster- en taakbalk.
  - Moet de resoluties 16, 32, 48 en 256 bevatten.

- **`ESR.png`** — afbeelding voor de ESR-testknop in de Diagnose-pagina
  (`app/gui/main_window.py`, `_build_diagnose_page`). Wordt op dit moment
  gebruikt; verdere venster-iconen volgen in een latere fase.

## Afspraken

- Het ICO-bestand is de bron van waarheid voor alle builds. Wijzig het niet
  handmatig; vervang het in één keer door een nieuw ICO met dezelfde naam.
- De bestandsnaam `logo.ico` ligt vast. De `.spec` en `.iss` verwijzen er
  rechtstreeks naar.