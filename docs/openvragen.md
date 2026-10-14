# Openvragen en observaties — Electronics Diagnostic Tool Hub / ESR Tester

**Versie:** 2.0.0
**Datum:** 2026-10-13
**Auteur:** Bart Bossuyt
**Doel:** expliciet bijhouden wat nog onduidelijk, open of te verifiëren
is. Geen bugs, geen beloftes — alleen vragen en observaties.

Wijzigingen:
  v1.0.0 (2026-10-06)  Eerste versie.
  v1.1.0 (2026-10-07)  §2 bijgewerkt na fase 5.
  v1.2.0 (2026-10-08)  §2.4 en §2.5 bijgewerkt na 5D'.2e.
  v1.3.0 (2026-10-09)  §2.7 toegevoegd: metadata van imports
                       doorzoekbaar maken (5D'.1b).
  v1.4.0 (2026-10-09)  §2.8 toegevoegd: Word- en Excel-import (fase 6).
  v1.5.0 (2026-10-09)  §2.10 toegevoegd: Grafieken en trends (fase 7).
  v1.6.0 (2026-10-12)  §2.12 en §2.13 toegevoegd: meetrapporten (8) en
                       settings-uitbreiding (8D).
  v1.7.0 (2026-10-13)  §2.15 toegevoegd: eerste Windows-build (9A/9B).
  v1.8.0 (2026-10-13)  §2.17 toegevoegd: Inno Setup installer en
                       signing (9C + 9D) — beantwoord. Nieuwe
                       openstaande punten: x64-deprecation, publish naar
                       GitHub, build_log.txt, verlopen certificaten,
                       Defender/Intune-testmatrix, WDAC/AppLocker-vraag.
  v1.9.0 (2026-10-13)  §2.18 bijgewerkt: publicatie naar GitHub is
                       uitgevoerd (9E, v1.0.3). Nieuwe openstaande
                       punten: LF/CRLF-waarschuwing,
                       `ESR_Tester.spec` in `.gitignore`.
  v2.0.0 (2026-10-13)  §2.19 bijgewerkt: WDAC/AppLocker-vraag is
                       beantwoord (niet actief). §2.20 toegevoegd:
                       fase 9F afgerond — testmatrix en packaging.md
                       bestaan. Nieuwe status van openstaande punten.

---

## 1. Uit Fase 4I — Zoektaal-observaties

### 1.1 `!` is substring-uitsluiting
- **Status:** verduidelijkt in 4I.1.a.
- **Restvraag:** blijft dit de gewenste semantiek?

### 1.2 `-%term` heeft geen eenduidige betekenis
- **Status:** opgelost in 4I.1.b.

### 1.3 Geen haakjes, geen veldnamen, geen datums
- **Status:** bewust gedocumenteerd in `docs/search_syntax.md` §8.1.
- **Restvraag:** wordt dit een probleem zodra de catalogus groeit?

---

## 2. Uit Fase 5, 6, 7, 8 en 9

### 2.1 t/m 2.5 — beantwoord

Zie de eerdere versies van dit document voor de volledige status van
scope, provenance, metadata, statusbeheer en assessment-koppeling.

### 2.6 Nieuwe openstaande punten (na 5D'.2e)

- Reden opgeven bij archiveren. **Open; klein.**
- Filter voor alleen gearchiveerde documenten. **Open; klein.**
- Statustransitie-beleid. **Bewust beperkt.**
- Catalogusmigratie bij statuswijzigingen. **Nog niet nodig.**
- OCR voor gescande PDF's. **Uitgesteld.**
- Async URL-fetch. **Open; overwegen in fase 11.**
- Datum-parsing bij bewerken. **Bewust geaccepteerd; verfijnen in 11.**
- Bulk-edit van meerdere imports. **Open.**
- Bulk-statuswijziging van meerdere imports. **Open.**

### 2.7 Metadata van imports doorzoekbaar — beantwoord (5D'.1b)

Zie v1.3.0.

### 2.8 Word- en Excel-import — beantwoord (fase 6)

Zie v1.4.0.

### 2.9 Nieuwe openstaande punten (na fase 6)

- AI-tekstextractie uit docx/xlsx. **Voorbereiding voor fase 12.**
- Cosmetische scrollbar in Word-samenvatting. **Open; klein.**

### 2.10 Grafieken en trends — beantwoord (fase 7)

Zie v1.5.0.

### 2.11 Nieuwe openstaande punten (na fase 7)

- Splitsen van `refresh()` in data-herberekening en label-update.
  **Open; klein.**
- Automatische as-schaling voor capaciteit. **Open; cosmetisch.**
- `QDateTimeAxis` tick-formaat. **Open; cosmetisch.**
- Scatterkleur bij onbekende `final_status`. **Bewust grijs.**
- Geen zoom/pan. **Open.**
- Geen PNG/PDF-export van grafieken. **Bewust buiten fase 7.**

### 2.12 Meetrapporten — beantwoord (fase 8)

Zie v1.6.0.

### 2.13 Settings-uitbreiding — beantwoord (fase 8D)

Zie v1.6.0.

### 2.14 Nieuwe openstaande punten (na fase 8D)

- GUI voor scope "selectie" en "filters". **Open; uitgesteld.**
- Menu-item "Rapport maken…" disabled maken zonder selectie. **Open; cosmetisch.**
- PDF-fonts op Windows. **Opgelost in 9A.**
- Cosmetische opruiming i18n-keys. **Open; cosmetisch.**

### 2.15 Eerste Windows-build — beantwoord (fase 9A en 9B)

Zie v1.7.0.

### 2.16 Nieuwe openstaande punten (na fase 9B)

- Pandas-pin `<3`. **Open; bewust conservatief.**
- Numpy als directe dependency. **Bewust expliciet.**
- Cosmetische `[rename] Fallback via robocopy...`-melding. **Open; cosmetisch.**
- `build_log.txt` blijft leeg. **Open; cosmetisch.**
- Relatief `icon_path` in `main_window.py`. **Open; wacht op 9F.**

### 2.17 Inno Setup installer en signing — beantwoord (fase 9C + 9D)

- **Vraag:** kunnen we de applicatie als installer bouwen, met
  code-signing, volgens de bewezen ArticleSearch-flow?
- **Antwoord:** ja. Sinds 9C+9D bestaat er een volledige buildstraat:
  - `build_installer.bat` (v2.0.1) genereert `dist\installer.iss` in
    de batch, compileert met `ISCC.exe`, en signeert zowel de app-EXE
    als de installer.
  - `bump_version.py` (v2.0.0) leest `app/version.py`.
  - `ESR_Tester.spec` (v2.0.0) heeft `icon=` actief.
  - `build_and_publish.ps1` (v1.0.0) orkestreert de hele keten met
    signing-preflight.
  - `publish.ps1` (v1.0.0) doet de GitHub-release met release-gate.
- **Certificaat:** subject `CN=CGK Local Signing`, actief thumbprint
  `BD1DC390D56E3392836FD6E39470D5F766346509`, geldig tot 2028-09-17.
- **Bewezen werkend:** build `1.0.3` geproduceerd, beide bestanden
  gesigned en geverifieerd, installer getest op gewone Windows-pc.
- **Belangrijke beslissing:** de ArticleSearch-flow is de bewezen
  flow. Geen eigen variant meer.
- **Status:** afgerond voor 9C en 9D.

### 2.18 Publiceren naar GitHub — beantwoord (fase 9E)

- **Vraag:** publiceer de eerste release naar GitHub via `publish.ps1`.
  Is `$Repo = "capacitor_esr_validator"` de echte repo-naam? En is de
  eerste release `v1.0.4` of een andere versie?
- **Antwoord:**
  - Repo is bevestigd: `https://github.com/barremans/capacitor_esr_validator`.
  - De eerste release is **`v1.0.3`** (geen bump vooraf).
  - Publicatie is uitgevoerd op **2026-10-13**.
  - Release-gate werkte: `Get-AuthenticodeSignature` gaf `Valid` met
    `CN=CGK Local Signing`.
  - Asset `ESR_TesterSetup_1.0.3.exe` (≈63 MB) is geüpload.
  - `releases/latest/version.txt` is aangemaakt en gepusht
    (2 regels: versie + URL).
  - `app/version.py` + `version.txt` zijn gecommit en gepusht
    (commit `1614c9e`).
  - De raw "latest"-pointer
    `https://raw.githubusercontent.com/barremans/capacitor_esr_validator/main/releases/latest/version.txt`
    geeft correct `1.0.3` + de download-URL.
- **Status:** afgerond voor 9E.

### 2.19 Defender/Intune/WDAC — beantwoord (fase 9F)

- **Vraag:** is WDAC of AppLocker actief op de doel-pc's? Als dat zo
  is, is de Defender-indicator niet voldoende; dan is uitrol van het
  certificaat naar `Trusted Publishers` of een publiek vertrouwd
  certificaat nodig.
- **Antwoord:** **WDAC en AppLocker zijn niet actief** in de
  doelomgeving (bevestigd 2026-10-13). De Defender-indicator volstaat.
- **Bewezen:** de installer is op een **uitgerolde Intune-beheerde
  Windows-machine** geïnstalleerd en werkt. Op een gewone Windows-pc
  werkt de SmartScreen-omzeiling ("More info → Run anyway").
- **Vervolg:** de testmatrix is vastgelegd in
  `docs/testmatrix_defender_intune.md`. De build-, signing- en
  distributieflow is vastgelegd in `docs/packaging.md`.
- **Status:** afgerond voor 9F.

### 2.20 Nieuwe openstaande punten (na fase 9F)

- **LF/CRLF-waarschuwing** bij `git add releases/latest/version.txt`.
  - **Wat:** Git meldt `LF will be replaced by CRLF the next time Git
    touches it`. Inhoudelijk geen probleem — de raw URL geeft exact de
    twee verwachte regels.
  - **Opgelost in 9F:** `.gitattributes` uitgebreid met
    `releases/latest/version.txt text eol=lf`.
  - **Status:** opgelost.
- **`Architecture identifier "x64" is deprecated`** tijdens ISCC.
  - **Restvraag:** aanpassen naar `x64compatible` in
    `build_installer.bat`?
  - **Impact:** één regel in de `.iss`-generatie.
  - **Status:** open; cosmetisch (fase 11).
- **`ESR_Tester.spec` staat in `.gitignore`** (regel `*.spec`).
  - **Wat:** de `.spec` staat in de root en wordt door PyInstaller
    gebruikt, maar werd niet meegecommit. Op een andere machine is
    de `.spec` dan niet beschikbaar na `git clone`.
  - **Opgelost in 9F:** `.gitignore` uitgebreid met `!ESR_Tester.spec`.
    De spec wordt nu meegecommit als bronbestand.
  - **Status:** opgelost.
- **`[rename] Fallback via robocopy...`-melding** in `build_installer.bat`.
  - **Restvraag:** oude `dist\<BUILD_FOLDER>` altijd eerst volledig
    verwijderen vóór de rename?
  - **Impact:** kleine wijziging in `build_installer.bat`.
  - **Status:** open; cosmetisch (fase 11).
- **`build_log.txt` blijft leeg.** Alleen starttijd, geen volledige
  PyInstaller- of Inno-output.
  - **Restvraag:** volledige output loggen (bijv. via `tee` of
    `2>&1`-redirect)?
  - **Impact:** kleine wijziging in `build_installer.bat`.
  - **Status:** open; cosmetisch (fase 11).
- **Relatief `icon_path` in `main_window.py`.** Pad
  `"assets/icons/esr.png"` werkt in de huidige build omdat de CWD de
  installatiemap is, maar breekt bij een andere CWD.
  - **Restvraag:** verfijnen via `sys._MEIPASS` of `Path(__file__).parent`?
  - **Impact:** kleine wijziging in `main_window.py`.
  - **Status:** open; fase 11.
- **Twee verlopen certificaten in `CurrentUser\My`.**
  - `4DA652BFA8FA5917A8BC76F0AA674F9FED532EF7` (verlopen 2026-09-18)
  - `13B90D29CCDE3779226958F7F4784C3FF741C70A` (verlopen 2026-09-18)
  - **Restvraag:** opruimen, of laten staan? De preflight slaat ze
    automatisch over.
  - **Impact:** geen — alleen cosmetisch.
  - **Status:** open; cosmetisch.
- **Publiek vertrouwd (EV-)certificaat.** Structurele oplossing voor
  SmartScreen zonder handmatig beheerde indicator-lijst.
  - **Restvraag:** beslissing over kosten/aanvraag.
  - **Impact:** groter traject.
  - **Status:** open; lange termijn.
- **Fallback timestamp-server.** Één server, over `http`.
  - **Restvraag:** fallback overwegen?
  - **Impact:** kleine wijziging in `build_installer.bat`.
  - **Status:** open; cosmetisch.
- **Testmatrix op andere Windows-versies** (Win10 vs Win11).
  - **Restvraag:** uitbreiden indien nodig?
  - **Impact:** geen code; alleen documentatie.
  - **Status:** open; cosmetisch.

---

## 3. Uit vroegere contextdocumenten (nog steeds relevant)

### 3.1 V-Loss
- **Status:** V-Loss blijft optioneel en ongedefinieerd.

### 3.2 TEKCOPLUS-display en exportstructuur
- **Status:** handmatige invoer blijft de standaard.

### 3.3 Praktijkvalidatie
- **Status:** Fase 10 — Praktische ESR-validatie.

### 3.4 Referentiedata
- **Status:** open; relevant voor Fase 6 en later.

### 3.5 Rapportage
- **Status:** deels beantwoord in fase 8.

### 3.6 Override van automatische beoordeling
- **Status:** open; relevant voor Fase 11.

### 3.7 Praktische meetgegevens
- **Status:** Fase 10 — Praktische ESR-validatie.

---

## 4. Uit eigen observaties tijdens recente fases

### 4.1 Help per taal — nog niet alle talen gedekt
- Momenteel: `nl_NL.md` en `en_US.md`.

### 4.2 Testdekking van i18n-keys
- **Status:** bewust nog niet toegevoegd.

### 4.3 Projectstructuur-document
- **Vraag:** welk script genereert `PROJECT_STRUCTURE.md`?

### 4.4 Thema-uitbreiding — light theme
- **Status:** uitgesteld.

### 4.5 Checkbox- en radio-indicator in donker thema
- **Status:** opgelost in 5D'.2f.

### 4.6 Aandachtspunt: `QT_QPA_FONTDIR` op Windows
- **Status:** opgelost in 9A.

### 4.7 Build-omgeving en ABI-conflicten
- **Status:** opgelost met pins; zie §2.16.

### 4.8 ArticleSearch-flow versus eigen variant
- **Observatie:** de oorspronkelijke 9C-aanpak met een vaste
  `installer.iss` in de root werkte niet betrouwbaar in deze omgeving.
  De ArticleSearch-flow (`build_installer15.bat` v1.4.0) werkt wel,
  bewezen op 2026-10-13.
- **Besluit:** geen eigen variant meer. De ArticleSearch-flow is
  bindend voor de buildstraat.
- **Status:** afgerond in 9C+9D; publicatie in 9E.

### 4.9 Eerste echte publicatie
- **Observatie:** op 2026-10-13 is de eerste GitHub-release
  gepubliceerd. De volledige keten `build_installer.bat` →
  `publish.ps1` is nu eind-to-eind bewezen, inclusief de release-gate
  op de Authenticode-handtekening.
- **Status:** afgerond in 9E.

### 4.10 Eerste Intune-installatie
- **Observatie:** op 2026-10-13 is de installer met succes
  geïnstalleerd op een uitgerolde Intune-beheerde Windows-machine,
  met de Defender-indicator actief. Geen SmartScreen-blokkade, geen
  quarantaine, app start correct.
- **Status:** afgerond in 9F.

---

## 5. Status van dit document

- Dit document is **levend**. Bij elke fase mogen nieuwe vragen worden
  toegevoegd en opgeloste vragen worden gemarkeerd.
- Opgeloste vragen blijven staan voor historische context.