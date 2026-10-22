@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

rem Altijd uitvoeren vanuit de map waar dit .bat bestand staat
cd /d "%~dp0"

rem ================================================
rem build_installer.bat - Build + Inno Setup installer generator
rem File:    build_installer.bat
rem Role:    Bouwt de PyInstaller-EXE en genereert/compileert het Inno
rem          Setup installer-script (.iss), voor zowel interactief gebruik
rem          als niet-interactieve aanroep vanuit build_and_publish.ps1
rem          (via env vars AS_BUMP_PART, AS_MAKE_INSTALLER, AS_DO_SIGN).
rem
rem          Deze versie volgt 1-op-1 de bewezen ArticleSearch-flow
rem          (build_installer15.bat v1.4.0), met de mappen en bestanden
rem          van ESR Tester.
rem
rem Version: 2.0.1
rem Author:  Bart Bossuyt
rem Changes: 2.0.1 (2026-10-13) - Fix: in blok [6] is het set /p-blok
rem                               vervangen door een simpele if defined-
rem                               check. De prompttekst bevatte vierkante
rem                               haken ([J/N]) en ronde haken
rem                               ((standaard J)) binnen een (...)-blok,
rem                               wat cmd afbrak met
rem                               ": was unexpected at this time.".
rem                               AS_MAKE_INSTALLER wordt altijd gezet door
rem                               build_and_publish.ps1, dus set /p was
rem                               overbodig.
rem Changes: 2.0.0 (2026-10-13) - Fase 9C+9D in één keer. Exacte kopie
rem                               van de ArticleSearch-flow, met ESR
rem                               Tester-namen, signing actief, icoon
rem                               actief, .iss gegenereerd in dist\.
rem ================================================

rem ---- Basisconfig ----
set "PROJECT_NAME=ESR_Tester"
set "SPEC_FILE=ESR_Tester.spec"
set "DST_FOLDER=dist"
set "LOGFILE=build_log.txt"
set "TIMESTAMP_URL=http://timestamp.sectigo.com"
set "SIGN_SUBJECT="
set "SIGN_THUMBPRINT=%AS_SIGN_THUMBPRINT%"

rem Vaste AppId (zonder de Inno-escape "{{"). Wordt zowel in [Setup] als
rem in [Code] gebruikt. Nooit meer wijzigen na eerste uitrol.
set "APPGUID={B7E4F2A1-9C3D-4E5F-8A6B-1D2E3F4A5B6C}"

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

rem ================================================
rem [S0] Signing - default J voor ESR Tester
rem ================================================
set "DO_SIGN=J"
if defined AS_DO_SIGN set "DO_SIGN=%AS_DO_SIGN%"
if defined AS_DO_SIGN echo [sign] Modus via parameter: %AS_DO_SIGN%

set "SIGNTOOL_EXE="
if /I "%DO_SIGN%"=="J" call :FIND_SIGNTOOL
if /I "%DO_SIGN%"=="J" if not defined SIGNTOOL_EXE echo [WAARSCHUWING] signtool.exe niet gevonden. Signing overgeslagen.
if /I "%DO_SIGN%"=="J" if not defined SIGNTOOL_EXE set "DO_SIGN=N"
if /I "%DO_SIGN%"=="J" if defined SIGNTOOL_EXE echo [sign] signtool: %SIGNTOOL_EXE%

rem ---- Versie verhogen ----
if defined AS_BUMP_PART (
  set "PART_TO_BUMP=%AS_BUMP_PART%"
  echo [0] Versie-bump via parameter: %AS_BUMP_PART%
) else (
  set "PART_TO_BUMP=patch"
)
echo [0] Versie verhogen via bump_version.py (%PART_TO_BUMP%)...
"%PYEXE%" bump_version.py %PART_TO_BUMP% || (echo [FOUT] Versieverhoging mislukt.& pause & exit /b 1)

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
set "ABS_BUILD_FOLDER=%CD%\%DST_FOLDER%\%BUILD_FOLDER%"
set "INITIAL_EXE=%DST_FOLDER%\%PROJECT_NAME%\%PROJECT_NAME%.exe"
set "ISS_FILE=%DST_FOLDER%\installer.iss"

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

rem ---- Assets en losse bestanden kopieren ----
echo [5] Assets kopieren...
for %%D in (assets docs) do (
  if exist "%%D" xcopy /E /I /Y "%%D" "%DST_FOLDER%\%BUILD_FOLDER%\%%D" >nul
)
for %%F in (requirements.txt settings.json) do (
  if exist "%%F" copy /Y "%%F" "%DST_FOLDER%\%BUILD_FOLDER%\" >nul
)
> "%DST_FOLDER%\%BUILD_FOLDER%\version.txt" echo %NEW_VERSION%

rem ---- [5b] App-EXE signen (indien DO_SIGN=J) ----
if /I "%DO_SIGN%"=="J" (
  echo [5b] Signen van %DST_FOLDER%\%BUILD_FOLDER%\%PROJECT_NAME%.exe ...
  call :SIGN_FILE "%DST_FOLDER%\%BUILD_FOLDER%\%PROJECT_NAME%.exe"
  if errorlevel 1 (
    echo [FOUT] Signen/verifieren van app-EXE faalde. Build wordt gestopt.
    exit /b 1
  )
) else (
  echo [INFO] Signing overgeslagen ^(DO_SIGN=%DO_SIGN%^).
)

rem ---- Inno Setup installer ----
rem AS_MAKE_INSTALLER wordt altijd gezet door build_and_publish.ps1.
rem Geen set /p meer (dat brak de cmd-parser met haakjes in de prompt).
if defined AS_MAKE_INSTALLER (
  set "MAKE_INSTALLER=%AS_MAKE_INSTALLER%"
  echo [6] Installer via parameter: %AS_MAKE_INSTALLER%
) else (
  set "MAKE_INSTALLER=J"
  echo [6] Installer: default J
)
set "DO_ISCC=1"
if /I "%MAKE_INSTALLER%"=="N" set "DO_ISCC=0"
if "%DO_ISCC%"=="0" goto SHOW_OUTPUT

rem ---- .iss genereren ----
if not exist "%DST_FOLDER%" mkdir "%DST_FOLDER%" >nul 2>&1
del /q "%ISS_FILE%" >nul 2>&1
echo [6b] Installer-script genereren...

>>"%ISS_FILE%" echo ; --- Inno Setup script, automatisch gegenereerd ---
>>"%ISS_FILE%" echo [Setup]
>>"%ISS_FILE%" echo AppId=%APPGUID:~0,1%{%APPGUID:~1%
>>"%ISS_FILE%" echo AppName=%PROJECT_NAME%
>>"%ISS_FILE%" echo AppVersion=%NEW_VERSION%
>>"%ISS_FILE%" echo AppVerName=%PROJECT_NAME% %NEW_VERSION%
>>"%ISS_FILE%" echo AppPublisher=Electronics Diagnostic Tool Hub
>>"%ISS_FILE%" echo DefaultDirName={autopf}\Electronics Diagnostic Tool Hub\%PROJECT_NAME%
>>"%ISS_FILE%" echo DisableDirPage=no
>>"%ISS_FILE%" echo UsePreviousAppDir=no
>>"%ISS_FILE%" echo DefaultGroupName=%PROJECT_NAME%
>>"%ISS_FILE%" echo DisableProgramGroupPage=yes
>>"%ISS_FILE%" echo OutputDir=.
>>"%ISS_FILE%" echo OutputBaseFilename=%PROJECT_NAME%Setup_%NEW_VERSION%
>>"%ISS_FILE%" echo Compression=lzma
>>"%ISS_FILE%" echo SolidCompression=yes
>>"%ISS_FILE%" echo Uninstallable=yes
>>"%ISS_FILE%" echo CreateAppDir=yes
>>"%ISS_FILE%" echo PrivilegesRequired=admin
>>"%ISS_FILE%" echo ArchitecturesInstallIn64BitMode=x64
>>"%ISS_FILE%" echo DirExistsWarning=no
>>"%ISS_FILE%" echo WizardStyle=modern
>>"%ISS_FILE%" echo SetupIconFile="%ABS_BUILD_FOLDER%\assets\icons\logo.ico"
>>"%ISS_FILE%" echo CloseApplicationsFilter=%PROJECT_NAME%.exe
>>"%ISS_FILE%" echo CloseApplications=force
>>"%ISS_FILE%" echo RestartApplications=no
>>"%ISS_FILE%" echo.
>>"%ISS_FILE%" echo [InstallDelete]
>>"%ISS_FILE%" echo Type: filesandordirs; Name: "{app}\_internal"
>>"%ISS_FILE%" echo Type: filesandordirs; Name: "{app}\__pycache__"
>>"%ISS_FILE%" echo.
>>"%ISS_FILE%" echo [Files]
>>"%ISS_FILE%" echo Source: "%ABS_BUILD_FOLDER%\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
>>"%ISS_FILE%" echo.
>>"%ISS_FILE%" echo [Icons]
>>"%ISS_FILE%" echo Name: "{group}\%PROJECT_NAME%"; Filename: "{app}\%PROJECT_NAME%.exe"; WorkingDir: "{app}"; IconFilename: "{app}\assets\icons\logo.ico"
>>"%ISS_FILE%" echo Name: "{commondesktop}\%PROJECT_NAME%"; Filename: "{app}\%PROJECT_NAME%.exe"; WorkingDir: "{app}"; IconFilename: "{app}\assets\icons\logo.ico"; Tasks: desktopicon
>>"%ISS_FILE%" echo.
>>"%ISS_FILE%" echo [Tasks]
>>"%ISS_FILE%" echo Name: "desktopicon"; Description: "Maak een snelkoppeling op het bureaublad"; GroupDescription: "Extra opties:"
>>"%ISS_FILE%" echo.
>>"%ISS_FILE%" echo [Run]
>>"%ISS_FILE%" echo Filename: "{app}\%PROJECT_NAME%.exe"; WorkingDir: "{app}"; Description: "Start %PROJECT_NAME%"; Flags: nowait postinstall skipifsilent runascurrentuser
>>"%ISS_FILE%" echo.
>>"%ISS_FILE%" echo [Code]
>>"%ISS_FILE%" echo function IsUpgrade: Boolean;
>>"%ISS_FILE%" echo var sPrevPath: String;
>>"%ISS_FILE%" echo begin
>>"%ISS_FILE%" echo Result := RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\%APPGUID%_is1', 'InstallLocation', sPrevPath);
>>"%ISS_FILE%" echo end;
>>"%ISS_FILE%" echo.
>>"%ISS_FILE%" echo procedure InitializeWizard();
>>"%ISS_FILE%" echo begin
>>"%ISS_FILE%" echo if IsUpgrade then WizardForm.WelcomeLabel2.Caption := 'Dit zal %PROJECT_NAME% bijwerken naar versie %NEW_VERSION%.' + #13#10#13#10 + 'Klik op Volgende om verder te gaan.';
>>"%ISS_FILE%" echo end;

rem ---- Inno Setup compileren ----
echo [7] Inno Setup compileren...
set "ISCC_EXE="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC_EXE=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC_EXE=C:\Program Files\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE (
  echo [FOUT] ISCC.exe niet gevonden. Installeer Inno Setup 6.
  exit /b 1
)
echo [7] ISCC: %ISCC_EXE%
"%ISCC_EXE%" "%ISS_FILE%"
if errorlevel 1 (
  echo [FOUT] Inno Setup compile mislukt. Bekijk "%ISS_FILE%".
  exit /b 1
)
echo Installer aangemaakt: %DST_FOLDER%\%PROJECT_NAME%Setup_%NEW_VERSION%.exe

rem ---- [7b] Installer signen ----
if /I "%DO_SIGN%"=="J" (
  if exist "%DST_FOLDER%\%PROJECT_NAME%Setup_%NEW_VERSION%.exe" (
    echo [7b] Signen van installer: %DST_FOLDER%\%PROJECT_NAME%Setup_%NEW_VERSION%.exe ...
    call :SIGN_FILE "%DST_FOLDER%\%PROJECT_NAME%Setup_%NEW_VERSION%.exe"
    if errorlevel 1 (
      echo [FOUT] Signen/verifieren van installer faalde. Build wordt gestopt.
      exit /b 1
    )
  )
) else (
  echo [INFO] Installer-signing overgeslagen ^(DO_SIGN=%DO_SIGN%^).
)

:SHOW_OUTPUT
echo.
echo Output-map: %DST_FOLDER%\%BUILD_FOLDER%
echo Testen: "%DST_FOLDER%\%BUILD_FOLDER%\%PROJECT_NAME%.exe"
echo Installer (indien gebouwd): %DST_FOLDER%\%PROJECT_NAME%Setup_%NEW_VERSION%.exe
echo Signing: %DO_SIGN%
if not defined AS_BUMP_PART pause
endlocal
exit /b 0

rem ================================================
:FIND_SIGNTOOL
set "SIGNTOOL_EXE="
if exist "C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe" (
  set "SIGNTOOL_EXE=C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe"
  goto :eof
)
if exist "C:\Program Files (x86)\Windows Kits\10\App Certification Kit\signtool.exe" (
  set "SIGNTOOL_EXE=C:\Program Files (x86)\Windows Kits\10\App Certification Kit\signtool.exe"
  goto :eof
)
if exist "C:\Program Files\Windows Kits\10\bin\x64\signtool.exe" (
  set "SIGNTOOL_EXE=C:\Program Files\Windows Kits\10\bin\x64\signtool.exe"
  goto :eof
)
for /f "delims=" %%S in ('where signtool.exe 2^>nul') do (
  set "SIGNTOOL_EXE=%%S"
  goto :eof
)
goto :eof

rem ================================================
:SIGN_FILE
if not exist "%~1" echo [FOUT] Bestand niet gevonden: %~1
if not exist "%~1" exit /b 1
if not defined SIGNTOOL_EXE (
  echo [FOUT] signtool niet geconfigureerd.
  exit /b 1
)
echo [sign] Bestand: %~1
if defined SIGN_THUMBPRINT (
  echo [sign] Certificaat-thumbprint: %SIGN_THUMBPRINT%
  "%SIGNTOOL_EXE%" sign /fd SHA256 /td SHA256 /tr "%TIMESTAMP_URL%" /sha1 "%SIGN_THUMBPRINT%" "%~1"
) else if defined SIGN_SUBJECT (
  "%SIGNTOOL_EXE%" sign /fd SHA256 /td SHA256 /tr "%TIMESTAMP_URL%" /n "%SIGN_SUBJECT%" "%~1"
) else (
  "%SIGNTOOL_EXE%" sign /fd SHA256 /td SHA256 /tr "%TIMESTAMP_URL%" /a "%~1"
)
if errorlevel 1 (
  echo [FOUT] signtool mislukt voor: %~1
  exit /b 1
)

echo [verify] Authenticode-handtekening controleren...
"%SIGNTOOL_EXE%" verify /pa /v "%~1"
if errorlevel 1 (
  echo [FOUT] Handtekening kon niet geldig geverifieerd worden: %~1
  exit /b 1
)

echo [OK] Gesigned en geverifieerd: %~1
exit /b 0