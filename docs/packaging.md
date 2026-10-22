# Packaging — build, signing en distributie

**Versie:** 1.3.0
**Datum:** 2026-10-22
**Auteur:** Bart Bossuyt
**Doel:** Vastleggen hoe de Electronics Diagnostic Tool Hub / ESR Tester
gebouwd, gesigned en gedistribueerd wordt, en op welke pc-types de
installer is getest.

Dit document is de **project-eigen** samenvatting. Voor de generieke
CGK-breed build- en signing-verhaal: zie `05-signing-build-context.md` en
`signingContext.md` (extern, buiten deze repo). Voor de testmatrix:
zie `docs/testmatrix_defender_intune.md`.

**Wijzigingen:**

- v1.0.0 (2026-10-13) — Eerste versie.
- v1.1.0 (2026-10-22) — Fase 11I.1: nieuwe subsectie §2.1
  "Dependency-pins" met de motivatie voor de `numpy`/`pandas`-pins.
  Verwijst naar `requirements.txt` v1.1.0 en `docs/future_tools.md` §5.
- v1.2.0 (2026-10-22) — Fase 11I.3: `build_installer.bat` v2.0.2
  (x64compatible, robocopy-melding verduidelijkt, logging van [4] en
  [7] naar `build_log.txt`); `build_log.txt` toegevoegd aan
  `.gitignore`; §11 bijgewerkt (drie punten opgelost).
- v1.3.0 (2026-10-22) — Fase 11I.3 (herzien): `build_and_publish.ps1`
  v1.1.0 met expliciete standaardwaarde J bij de bevestigingsvraag
  "Starten?". §2-tabel bijgewerkt.

---

## 1. Overzicht van de keten

```
build_and_publish.ps1
 └─ build_installer.bat
      [0]   bump_version.py <patch|minor|major>
      [3c]  version_info.txt (Windows-metadata van de EXE)
      [4]   PyInstaller (ESR_Tester.spec)
      [5]   assets/docs/requirements/settings.json/version.txt kopiëren
      [5b]  App-EXE signen + verify
      [6b]  dist\installer.iss genereren
      [6c]  dist\innosign.bat aanmaken
      [7]   ISCC.exe /Smysigntool → setup + uninstaller gesigned
      [7b]  Installer verify
 └─ publish.ps1 (alleen bij publish=J)
      - versie lezen uit app/version.py
      - release-gate: Get-AuthenticodeSignature = Valid
      - gh release create/upload
      - releases/latest/version.txt schrijven
      - git add app/version.py releases/latest/version.txt
      - git commit + push
```

De **ArticleSearch-flow** is bindend. Geen eigen variant.

---

## 2. Bestanden en hun rol

| Bestand | Rol | Versie |
|---|---|---|
| `build_installer.bat` | Bouwt EXE + installer, signeert beide | 2.0.2 |
| `build_and_publish.ps1` | Vraagt parameters, orkestreert build + publish | 1.1.0 |
| `publish.ps1` | GitHub-release + release-gate + version.txt | 1.0.0 |
| `bump_version.py` | Verhoogt patch/minor/major in `app/version.py` | 2.0.0 |
| `ESR_Tester.spec` | PyInstaller-specificatie (icoon actief) | 2.1.0 |
| `app/version.py` | Centrale versie (één bron van waarheid) | 1.0.0 |
| `Export-SigningCertificate.ps1` | Exporteert `.cer` uit een gesigned bestand | 1.0.1 |
| `requirements.txt` | Dependency-pins met motivatie | 1.1.0 |

### 2.1 Dependency-pins

De pins staan in `requirements.txt` (v1.1.0). Ze zijn bewust:

- **`numpy>=1.26,<3` en `pandas>=2.2,<3`** hebben een bovengrens. De
  app gebruikt beide alleen voor basisfunctionaliteit (DataFrame,
  `read_excel`, eenvoudige aggregaties in `AnalysisService` en
  `documentation_screen`). Een toekomstige major-bump naar 3.x kan de
  PyInstaller-bundel breken (`collect_all("pandas")` in
  `ESR_Tester.spec` bundelt de volledige pandas-tree) of de
  pandas-API's wijzigen. De bovengrens is een **bewuste rem**, geen
  teken dat de huidige pins te oud zijn.
- **`PySide6`, `pytest`, `openpyxl`, `pypdf`, `requests`,
  `beautifulsoup4`, `python-docx`** hebben geen bovengrens. Ze hebben
  een stabiel major-beleid en worden alleen via publieke API's
  aangeroepen.
- **Geen upgrade zonder aanleiding.** De pins zijn bewezen in de
  PyInstaller-bundel. Een upgrade hoort in een aparte fase met eigen
  testronde en build.

Zie ook `docs/future_tools.md` §5 voor het dependencybeleid voor
toekomstige libraries (Schemdraw, Lcapy, PySpice, PyEIS, ...). Die
komen pas in `requirements.txt` wanneer een concrete appmodule ze echt
gebruikt.

---

## 3. Wat wordt gesigned

| # | Bestand | Wanneer | Door wie |
|---|---|---|---|
| 1 | `dist\ESR_Tester_<versie>\ESR_Tester.exe` | Stap [5b], vóór Inno | `:SIGN_FILE` → `signtool sign` |
| 2 | `dist\ESR_TesterSetup_<versie>.exe` | Tijdens ISCC-compilatie | Inno `SignTool=mysigntool` via `dist\innosign.bat` |
| 3 | `unins000.exe` (in de setup) | Idem | Idem |

**Volgorde is essentieel:** de EXE wordt gesigned *vóór* Inno de map
in de installer pakt. Anders zit er in de setup nog de ongesignede EXE.

**Niet gesigned (bewust):** DLL's/`.pyd` in de PyInstaller-map,
`version.txt`, assets.

---

## 4. Certificaat

| Wat | Waarde |
|---|---|
| Subject | `CN=CGK Local Signing` |
| Actief thumbprint | `BD1DC390D56E3392836FD6E39470D5F766346509` |
| Geldig tot | 2028-09-17 |
| Private key | `Cert:\CurrentUser\My` van `CGK-GROUP\BBossuyt` — nooit exporteren |
| Publieke kopie | `C:\PY\Tools\signing-certs\CGK_Local_Signing_BD1DC390D56E.cer` |
| Config | `%USERPROFILE%\.project_generator\signing_certificate.json` |
| Timestamp-server | `http://timestamp.sectigo.com` |

**signtool-commando (exe én installer):**

```
signtool sign /fd SHA256 /td SHA256 /tr http://timestamp.sectigo.com /sha1 <THUMBPRINT> <bestand>
signtool verify /pa /v <bestand>
```

- `/sha1 <thumbprint>`, **nooit** `/a` of `/n` — er bestaan meerdere
  certificaten met subject `CN=CGK Local Signing`.
- RFC3161-timestamp: handtekening blijft geldig ná verloop van het cert.
- `/pa` bij verify = standaard Authenticode-policy.

---

## 5. Release-gate

`publish.ps1` weigert te publiceren als de installer geen **geldige**
Authenticode-handtekening heeft:

```powershell
$sig = Get-AuthenticodeSignature -FilePath $assetPath
if ($sig.Status -ne [System.Management.Automation.SignatureStatus]::Valid) {
    throw "PUBLICATIE GEBLOKKEERD: installer heeft geen geldige Authenticode-handtekening."
}
```

Dit is de **enige** harde poort vóór upload. `build_installer.bat` stopt
zelf bij een mislukte sign/verify (exitcode 1), maar de release-gate in
`publish.ps1` is de laatste verdedigingslinie.

---

## 6. Distributie

### 6.1 GitHub-release

- Repo: `https://github.com/barremans/capacitor_esr_validator`
- Tag: `v<versie>` (bv. `v1.0.3`)
- Asset: `ESR_TesterSetup_<versie>.exe` (≈63 MB)
- Download-URL: `https://github.com/barremans/capacitor_esr_validator/releases/download/v<versie>/ESR_TesterSetup_<versie>.exe`

### 6.2 "Latest"-pointer

`releases/latest/version.txt` bevat twee regels:

```
1.0.3
https://github.com/barremans/capacitor_esr_validator/releases/download/v1.0.3/ESR_TesterSetup_1.0.3.exe
```

Raw URL:
`https://raw.githubusercontent.com/barremans/capacitor_esr_validator/main/releases/latest/version.txt`

Deze pointer is bedoeld voor de toekomstige **update-check (9H)**.

### 6.3 Bestandsencoding

`releases/latest/version.txt` wordt geschreven als **UTF-8 zonder BOM**
en moet in git als **LF** bewaard blijven. Zie §7.

---

## 7. `.gitattributes` en `.gitignore`

### 7.1 `.gitattributes`

```
# Auto detect text files and perform LF normalization
* text=auto
releases/latest/version.txt text eol=lf
```

De `eol=lf`-regel voorkomt de `LF will be replaced by CRLF`-waarschuwing
bij `git add releases/latest/version.txt`. Inhoudelijk geen probleem,
maar de pointer moet exact twee regels met LF bevatten.

### 7.2 `.gitignore`

`ESR_Tester.spec` staat **niet** meer in `.gitignore`. De spec is
nodig op een andere machine na `git clone` en is een bronbestand, geen
build-artefact. Uitzondering:

```
!ESR_Tester.spec
```

Build-artefacten (`build/`, `dist/`, `*.pyc`, `build_log.txt`) blijven
genegeerd. `build_log.txt` staat sinds 11I.3 **expliciet** in
`.gitignore` (het matcht niet op de generieke `*.log`-regel, want het
eindigt op `.txt`).

---

## 8. Testmatrix (samenvatting)

Volledige matrix: `docs/testmatrix_defender_intune.md`.

| Pc-type | Status | Actie |
|---|---|---|
| Gewone Windows-pc | ✅ Bewezen 2026-10-13 | SmartScreen "More info → Run anyway" |
| Intune-beheerde pc | ✅ Bewezen 2026-10-13 | Defender-indicator `Allow` actief |
| WDAC-pc | ❌ Niet actief in doelomgeving | Geen actie |
| AppLocker-pc | ❌ Niet actief in doelomgeving | Geen actie |

**Bij een nieuwe versie met hetzelfde certificaat:** geen nieuwe
indicator nodig. Test op beide pc-types en klaar.

**Bij een nieuw certificaat:** nieuwe `.cer` uploaden als indicator,
15–60 min wachten, testmatrix herhalen.

---

## 9. Hoe controleer je het?

1. **signtool** (meest betrouwbaar):
   ```powershell
   & "C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe" verify /pa /v "dist\ESR_TesterSetup_1.0.3.exe"
   ```
   Zoek naar *Successfully verified*, *Issued to: CGK Local Signing*,
   timestamp-regel.

2. **PowerShell**:
   ```powershell
   Get-AuthenticodeSignature "dist\ESR_TesterSetup_1.0.3.exe" | Format-List Status, SignerCertificate, TimeStamperCertificate
   ```
   Verwacht `Status: Valid` en thumbprint `BD1DC390…6509`.

3. **Na installatie:** dezelfde check op
   `C:\Program Files\Electronics Diagnostic Tool Hub\ESR_Tester\ESR_Tester.exe`
   en `unins000.exe`.

4. **Verkenner:** rechtsklik → Eigenschappen → *Digitale handtekeningen*.

---

## 10. Foutopsporing

| Symptoom | Oorzaak | Oplossing |
|---|---|---|
| `PUBLICATIE GEBLOKKEERD` in `publish.ps1` | Installer ongesigned of ongeldig | `build_installer.bat` opnieuw met `DO_SIGN=J` |
| `signtool.exe niet gevonden` | Windows SDK ontbreekt | SDK installeren |
| Timestamp-fout | Geen toegang tot `timestamp.sectigo.com` | Netwerk/proxy controleren |
| `Centrale signingconfig niet gevonden` | `signing_certificate.json` ontbreekt | Actief cert instellen in Certificate Manager |
| SmartScreen-blokkade op Intune-pc | Indicator ontbreekt of niet gesynct | Wacht 15–60 min; controleer indicator in `security.microsoft.com` |
| `Kan geen toegang krijgen tot het opgegeven apparaat…` | Geen vertrouwen (Defender/ASR) | Zie `signingContext.md` §4.2 |

---

## 11. Openstaande punten

| Punt | Status | Impact |
|---|---|---|
| `build_log.txt` blijft leeg | ✅ **Opgelost in 11I.3** — [4] en [7] loggen nu met `>> "%LOGFILE%" 2>&1` | Cosmetisch |
| `Architecture identifier "x64" is deprecated` | ✅ **Opgelost in 11I.3** — `x64compatible` in de gegenereerde `.iss` | Cosmetisch |
| `[rename] Fallback via robocopy...`-melding | ✅ **Opgelost in 11I.3** — melding verduidelijkt (reden + actie) | Cosmetisch |
| Bevestigingsvraag "Starten?" zonder standaard | ✅ **Opgelost in 11I.3** — `build_and_publish.ps1` v1.1.0 heeft expliciete standaard J | UX |
| Relatief `icon_path` in `main_window.py` | ✅ **Opgelost in 11I.2** — `sys._MEIPASS`-branch in `icon_paths.py` | Was structureel |
| Twee verlopen certificaten in `CurrentUser\My` | Open | Cosmetisch; preflight slaat ze over |
| Publiek vertrouwd (EV-)certificaat | Open | Structurele oplossing |
| Fallback timestamp-server | Open | Single point of failure |

**Toelichting bij de vier opgeloste punten (11I.2/11I.3):**

- **`build_log.txt`** — `build_installer.bat` schrijft nu de
  PyInstaller-stap [4] en de ISCC-stap [7] met `>> "%LOGFILE%" 2>&1`
  naar `build_log.txt`, plus een start- en eindmarkering. De rest
  blijft naar de console. `build_log.txt` staat expliciet in
  `.gitignore` (matcht niet op `*.log`).
- **`ArchitecturesInstallIn64BitMode`** — Inno Setup 6 beschouwt `x64`
  als deprecated; de moderne vorm is `x64compatible`. De rest van de
  gegenereerde `.iss` blijft identiek.
- **`[rename]`-fallback** — de melding zegt nu *waarom* de fallback
  draait (rename faalde, waarschijnlijk omdat een bestand in de map
  in gebruik is) en *wat* er gebeurt (robocopy `/MOVE`). De
  exitcode-check (errorlevel 8) is ongewijzigd.
- **"Starten?"-vraag** — `build_and_publish.ps1` v1.1.0 geeft Enter
  nu dezelfde standaardwaarde J als de vier vragen ervoor. Voorheen
  brak Enter af, wat verwarrend was.

**Bewust niet opgelost in 11I.3:**

- **`icon_path` in `main_window.py`** — dit is in 11I.2 opgelost op
  het niveau van `icon_paths.py`; `main_window.py` gebruikt de
  publieke API en hoefde niet gewijzigd te worden.

---

## 12. Checklist nieuwe release

1. `app/version.py` heeft de juiste versie (of `bump_version.py` draaien).
2. `%USERPROFILE%\.project_generator\signing_certificate.json` wijst naar `BD1DC390…6509`.
3. `signtool.exe` (Windows SDK) en Inno Setup 6 zijn geïnstalleerd.
4. `.\build_and_publish.ps1` draaien; kies bump, installer=J, signing=J, publish=J.
5. Controleer dat `publish.ps1` `[OK] Geldige Authenticode-handtekening` meldt.
6. Controleer de raw pointer-URL: `1.0.x` + juiste download-URL.
7. Test op een gewone Windows-pc en op een Intune-pc (zie §8).
8. Geen nieuwe Defender-indicator nodig zolang het certificaat ongewijzigd is.
9. **Controleer `build_log.txt`** na de build: bevat de PyInstaller- en
   ISCC-output. Bij een mislukking: kijk daar eerst.

---

## 13. Status van dit document

- Dit document is **levend**. Bij elke wijziging aan de buildstraat,
  het certificaat of de distributie wordt dit bijgewerkt.
- Het is de **project-eigen** tegenhanger van `05-signing-build-context.md`
  en `signingContext.md`, toegespitst op de ESR Tester.