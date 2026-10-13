@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

rem ================================================
rem build_installer.bat - PyInstaller build voor ESR Tester
rem File:    build_installer.bat
rem Role:    Bouwt de PyInstaller-EXE via ESR_Tester.spec. Kopieert
rem          settings.json en schrijft version.txt. Optioneel: signing
rem          (voorbereid voor fase 9D). De Inno Setup-stap volgt in 9C.
rem
rem          Niet-interactief: alle keuzes via omgevingsvariabelen.
rem            AS_BUMP_PART       = patch|minor|major (leeg = geen bump)
rem            AS_MAKE_INSTALLER  = J|N (default: J, in 9C effectief)
rem            AS_DO_SIGN         = J|N (default: N, in 9D effectief)
rem Version: 1.0.1
rem Author:  Bart Bossuyt
rem Changes: 1.0.1 (2026-10-13) - Fase 9B.2 fix: interactief set /p-blok
rem                               verwijderd. De batch werkt nu uitsluitend
rem                               via omgevingsvariabelen, wat ook beter
rem                               aansluit op build_and_publish.ps1 in 9E.
rem                               De fout ": was unexpected at this time"
rem                               trad op wanneer de batch vanuit PowerShell
rem                               werd aangeroepen en geen stdin beschikbaar
rem                               was voor set /p.
rem Changes: 1.0.0 (2026-10-13) - Fase 9B.2. Eerste versie, afgeleid van
rem                               ArticleSearch build_installer15.bat,
rem                               maar zonder Inno Setup-stap (die komt in
rem                               9C als vast .iss-bestand), zonder
rem                               signing-logica (9D), met app/version.py
rem                               als bron, en zonder icon= in de spec.
rem ================================================

rem Altijd uitvoeren vanuit de map waar dit .bat-bestand staat
cd /d "%~dp0"

rem ---- Basisconfig ----
set "PROJECT_NAME=ESR_Tester"
set "SPEC_FILE=ESR_Tester.spec"
set "DST_FOLDER=dist"
set "LOGFILE=build_log.txt"

rem ---- Python uit .venv prefereren ----
set "PYEXE="
if exist ".venv\Scripts\python.exe" set "PYEXE=.venv\Scripts\python.exe"
if not defined PYEXE if exist "Scripts\python.exe" set "PYEXE=Scripts\python.exe"
if not defined PYEXE set "PYEXE=python"

for %%I in ("%PYEXE%") do (
  if exist "%%~fI" set "PYEXE=%%~fI"
)

echo [info] Python: %PYEXE%
"%PYEXE%" -V >nul 2>&1 || (echo [FOUT] Geen werkende Python gevonden.& pause & exit /b 1)

rem ---- Optionele versie-bump (alleen via AS_BUMP_PART) ----
if defined AS_BUMP_PART (
  echo [0] Versie-bump via parameter: %AS_BUMP_PART%
  "%PYEXE%" bump_version.py %AS_BUMP_PART% || (echo [FOUT] Versieverhoging mislukt.& pause & exit /b 1)
) else (
  echo [0] Geen versie-bump.
)

rem ---- Versie robuust uitlezen uit app/version.py ----
set "PY_READV=%TEMP%\__read_version_tmp.py"
set "VER_TXT=%TEMP%\__version_out.txt"
del /q "%PY_READV%" "%VER_TXT%" >nul 2>&1
> "%PY_READV%" echo import importlib.util, io, os, re
>>"%PY_READV%" echo p=os.path.abspath(os.path.join('app','version.py')); v="0.0.0"
>>"%PY_READV%" echo try:
>>"%PY_READV%" echo ^    spec=importlib.util.spec_from_file_location("ver",p)
>>"%PY_READV%" echo ^    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
>>"%PY_READV%" echo ^    v=str(getattr(m,"__version__","0.0.0"))
>>"%PY_READV%" echo except Exception:
>>"%PY_READV%" echo ^    t=io.open(p,'r',encoding='utf-8').read()
>>"%PY_READV%" echo ^    m=re.search(r"__version__\s*=\s*['\^\"\s]*([0-9]+(?:\.[0-9]+){1,2})",t)
>>"%PY_READV%" echo ^    v=m.group(1) if m else "0.0.0"
>>"%PY_READV%" echo io.open(r'%VER_TXT%','w',encoding='utf-8').write(v.strip())
"%PYEXE%" "%PY_READV%" || (echo [FOUT] Versie uitlezen faalde.& del /q "%PY_READV%" >nul & pause & exit /b 1)
del /q "%PY_READV%" >nul 2>&1
set "NEW_VERSION=" & set /p NEW_VERSION=<"%VER_TXT%"
del /q "%VER_TXT%" >nul 2>&1
if not defined NEW_VERSION (echo [FOUT] Kon versie niet lezen.& pause & exit /b 1)
echo [1] Versie: %NEW_VERSION%

rem ---- Afgeleide paden ----
set "BUILD_FOLDER=%PROJECT_NAME%_%NEW_VERSION%"
set "INITIAL_EXE=%DST_FOLDER%\%PROJECT_NAME%\%PROJECT_NAME%.exe"

rem ---- Opschonen ----
echo [2] Opruimen...
rmdir /s /q build 2>nul
rmdir /s /q "%DST_FOLDER%" 2>nul
del /q "%LOGFILE%" 2>nul

rem ---- Vereisten ----
echo [3] Pip en vereisten...
"%PYEXE%" -m pip install --upgrade pip >nul
if exist requirements.txt "%PYEXE%" -m pip install -r requirements.txt || (echo [FOUT] pip install -r faalde.& pause & exit /b 1)

rem ---- PyInstaller aanwezig? ----
"%PYEXE%" -c "import PyInstaller" >nul 2>&1 || (
  echo [3b] PyInstaller installeren...
  "%PYEXE%" -m pip install "pyinstaller==6.11.1" "pyinstaller-hooks-contrib==2025.0" || (echo [FOUT] Installatie PyInstaller faalde.& pause & exit /b 1)
)

echo --- Build gestart op %DATE% %TIME% --- >> "%LOGFILE%"

rem ---- PyInstaller-build ----
echo [4] PyInstaller...
"%PYEXE%" -m PyInstaller --clean --noconfirm "%SPEC_FILE%" || (echo [FOUT] PyInstaller build faalde.& pause & exit /b 1)
if not exist "%INITIAL_EXE%" (echo [FOUT] EXE niet gevonden op "%INITIAL_EXE%".& pause & exit /b 1)

rem ---- Hernoemen naar map met versie ----
if exist "%DST_FOLDER%\%BUILD_FOLDER%" rmdir /S /Q "%DST_FOLDER%\%BUILD_FOLDER%"
rename "%DST_FOLDER%\%PROJECT_NAME%" "%BUILD_FOLDER%" >nul 2>&1
if errorlevel 1 (
  echo [rename] Fallback via robocopy...
  robocopy "%DST_FOLDER%\%PROJECT_NAME%" "%DST_FOLDER%\%BUILD_FOLDER%" /E /MOVE >nul
  if errorlevel 8 (echo [FOUT] Fallback kopie mislukt.& pause & exit /b 1)
  if exist "%DST_FOLDER%\%PROJECT_NAME%" rmdir /S /Q "%DST_FOLDER%\%PROJECT_NAME%"
)
if not exist "%DST_FOLDER%\%BUILD_FOLDER%\%PROJECT_NAME%.exe" (
  echo [FOUT] %PROJECT_NAME%.exe ontbreekt in %DST_FOLDER%\%BUILD_FOLDER%.
  pause & exit /b 1
)

rem ---- settings.json en version.txt ----
echo [5] settings.json en version.txt...
if exist "settings.json" copy /Y "settings.json" "%DST_FOLDER%\%BUILD_FOLDER%\" >nul
> "%DST_FOLDER%\%BUILD_FOLDER%\version.txt" echo %NEW_VERSION%

rem ---- Signing (voorbereid voor 9D; in 9B.2 altijd overgeslagen) ----
if /I "%AS_DO_SIGN%"=="J" (
  echo [6] Signing is nog niet geimplementeerd in 9B.2. Overgeslagen.
) else (
  echo [6] Signing overgeslagen.
)

echo.
echo ============================================================
echo [DONE] Build afgerond.
echo ============================================================
echo Output-map: %DST_FOLDER%\%BUILD_FOLDER%
echo Testen:     "%DST_FOLDER%\%BUILD_FOLDER%\%PROJECT_NAME%.exe"
pause
endlocal
exit /b 0