# Openvragen en observaties — Electronics Diagnostic Tool Hub / ESR Tester

**Versie:** 2.1.0
**Datum:** 2026-10-14
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
                       signing (9C + 9D) — beantwoord.
  v1.9.0 (2026-10-13)  §2.18 bijgewerkt: publicatie naar GitHub is
                       uitgevoerd (9E, v1.0.3).
  v2.0.0 (2026-10-13)  §2.19 bijgewerkt: WDAC/AppLocker-vraag is
                       beantwoord (niet actief). §2.20 toegevoegd:
                       fase 9F afgerond.
  v2.1.0 (2026-10-14)  §2.21 toegevoegd: drie nieuwe punten uit de
                       9F-sessie (visuele selectie in Analyse,
                       checkbox-zichtbaarheid donker thema, i18n-menging
                       in Diagnose/Result). §2.22 toegevoegd: fase 9G
                       (GitHub-feedback) en 9H (update-check) aangekondigd.

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

## 2. Uit Fase 5, 6, 7, 8, 9 en later

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
- **Visuele selectie van bewaarde testen.** De huidige filterbalk
  dekt niet alle wensen van de eindgebruiker. De gebruiker wil ook
  visueel (in de grafiek of in een lijst) bepaalde bewaarde metingen
  kunnen selecteren om alleen die te tonen of te analyseren.
  **Open; toegevoegd 2026-10-14; fase 11.**

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
- Relatief `icon_path` in `main_window.py`. **Open; fase 11.**

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
- **Antwoord:**
  - Repo: `https://github.com/barremans/capacitor_esr_validator`.
  - Eerste release: **`v1.0.3`** (geen bump vooraf).
  - Publicatie: **2026-10-13**.
  - Release-gate werkte: `Get-AuthenticodeSignature` gaf `Valid`.
  - Asset `ESR_TesterSetup_1.0.3.exe` (≈63 MB) geüpload.
  - `releases/latest/version.txt` aangemaakt en gepusht
    (2 regels: versie + URL).
  - `app/version.py` + `version.txt` gecommit en gepusht
    (commit `1614c9e`).
- **Status:** afgerond voor 9E.

### 2.19 Defender/Intune/WDAC — beantwoord (fase 9F)

- **Vraag:** is WDAC of AppLocker actief op de doel-pc's?
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
  - **Opgelost in 9F:** `.gitattributes` uitgebreid met
    `releases/latest/version.txt text eol=lf`.
  - **Status:** opgelost.
- **`ESR_Tester.spec` staat in `.gitignore`** (regel `*.spec`).
  - **Opgelost in 9F:** `.gitignore` uitgebreid met `!ESR_Tester.spec`.
  - **Status:** opgelost.
- **`Architecture identifier "x64" is deprecated`** tijdens ISCC.
  - **Restvraag:** aanpassen naar `x64compatible`?
  - **Status:** open; cosmetisch (fase 11).
- **`[rename] Fallback via robocopy...`-melding** in `build_installer.bat`.
  - **Status:** open; cosmetisch (fase 11).
- **`build_log.txt` blijft leeg.**
  - **Status:** open; cosmetisch (fase 11).
- **Relatief `icon_path` in `main_window.py`.**
  - **Status:** open; fase 11.
- **Twee verlopen certificaten in `CurrentUser\My`.**
  - **Status:** open; cosmetisch.
- **Publiek vertrouwd (EV-)certificaat.**
  - **Status:** open; lange termijn.
- **Fallback timestamp-server.**
  - **Status:** open; cosmetisch.
- **Testmatrix op andere Windows-versies** (Win10 vs Win11).
  - **Status:** open; cosmetisch.

### 2.21 Nieuwe openstaande punten (uit de 9F-sessie, 2026-10-14)

De gebruiker bracht tijdens de 9F-sessie drie punten aan voor een
latere opruimfase (fase 11).

- **Visuele selectie in Analyse — grafieken en trends.**
  - **Wat:** de huidige filterbalk laat toe om op fabrikant, serie,
    datum, meetmethode, instrumentcode en frequentie te filteren.
    Dat dekt niet alle wensen van de eindgebruiker. De gebruiker wil
    ook **visueel** (in de grafiek zelf of in een lijst ernaast)
    bepaalde bewaarde testen kunnen selecteren — bijvoorbeeld door op
    een datapunt te klikken of door een selectievakje per meting aan
    te vinken.
  - **Impact:** GUI-wijziging in `app/gui/analysis_screen.py`,
    mogelijk uitbreiding van `analysis_service.py` met een
    selectie-parameter.
  - **Status:** open; toegevoegd 2026-10-14; fase 11.

- **Checkbox-zichtbaarheid in donker thema.**
  - **Wat:** de filter-checkbox op zowel de Analyse-pagina als de
    History-pagina is onvoldoende zichtbaar op het donkere thema. De
    checkboxen moeten visueel duidelijk zijn.
  - **Impact:** `app/gui/styles.py` — expliciete
    `QCheckBox::indicator`-regels voor het donkere thema. Mogelijk
    ook de `QGroupBox::indicator` als de filtercheckbox daarbinnen
    valt.
  - **Status:** open; toegevoegd 2026-10-14; fase 11.

- **i18n-menging in Diagnose/Result en Resultaatdetails.**
  - **Wat:** het Result-venster op de Diagnose-pagina en het
    Resultaatdetails-venster mengen Engels en Nederlands. Voorbeelden:
    "Reliability: low", "Compare with an identical new unit or
    disconnect one terminal for a more accurate measurement.",
    "No D value entered; consistency check not performed.", en de
    waarschuwing "Reference frequency differs from the measurement
    frequency — no automatic conversion performed." staan in het
    Engels terwijl de rest van de GUI Nederlands is.
  - **Impact:** `app/services/assessment_service.py` (de teksten
    worden daar opgebouwd), `app/gui/esr_test_screen.py` (weergave
    van het Result-blok), en de i18n-bestanden `esr.json` in beide
    locales. De teksten moeten via i18n lopen, niet hardcoded in de
    service staan.
  - **Aandachtspunt:** dit raakt de **beoordelingslogica** niet —
    alleen de weergave. De service mag interne codes teruggeven; de
    GUI vertaalt ze. Dat is consistent met de `_status_code_label`-
    aanpak in `report_render.py`.
  - **Status:** open; toegevoegd 2026-10-14; fase 11.

### 2.22 Nieuwe fases aangekondigd (2026-10-14)

- **9G — Bug/feature-rapportage naar GitHub.**
  - **Wat:** het pakket uit `GITHUB_FEEDBACK_UITROL.md` uitrollen in
    deze app: vijf identieke pakketbestanden, een app-specifieke
    `github_feedback_config.py`, een niet-getrackte
    `github_secret_local.py`, een menu "Rapporteren" in het
    hoofdvenster, het controleblok in `ESR_Tester.spec`, en `requests`
    in `requirements.txt`.
  - **Token:** de gebruiker maakt een fine-grained token aan volgens
    stap 10 van het pakket. Het token komt nooit in een getrackt
    bestand, chat of context-document.
  - **Status:** volgende fase.

- **9H — Update-check bij opstarten + via Help.**
  - **Wat:** de "latest"-pointer op
    `releases/latest/version.txt` uitlezen en vergelijken met
    `app/version.py`. Bij een nieuwere versie een melding tonen, met
    een knop naar de download-URL. Zowel bij opstarten (eenmalig,
    niet-blokkerend) als via een menu-item in Help.
  - **Voorbeeld:** ArticleSearch heeft al een `updater.py` (v1.3.0).
  - **Status:** na 9G.

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
- **Status:** opgelost in 5D'.2f voor de documentatie-viewer. **Nieuw
  in 2.21:** de filter-checkbox op Analyse en History is nog niet
  goed zichtbaar.

### 4.6 Aandachtspunt: `QT_QPA_FONTDIR` op Windows
- **Status:** opgelost in 9A.

### 4.7 Build-omgeving en ABI-conflicten
- **Status:** opgelost met pins; zie §2.16.

### 4.8 ArticleSearch-flow versus eigen variant
- **Observatie:** de oorspronkelijke 9C-aanpak met een vaste
  `installer.iss` in de root werkte niet betrouwbaar in deze omgeving.
  De ArticleSearch-flow werkt wel, bewezen op 2026-10-13.
- **Besluit:** geen eigen variant meer. De ArticleSearch-flow is
  bindend voor de buildstraat.
- **Status:** afgerond in 9C+9D; publicatie in 9E.

### 4.9 Eerste echte publicatie
- **Observatie:** op 2026-10-13 is de eerste GitHub-release
  gepubliceerd. De volledige keten `build_installer.bat` →
  `publish.ps1` is nu eind-to-eind bewezen.
- **Status:** afgerond in 9E.

### 4.10 Eerste Intune-installatie
- **Observatie:** op 2026-10-13 is de installer met succes
  geïnstalleerd op een uitgerolde Intune-beheerde Windows-machine,
  met de Defender-indicator actief.
- **Status:** afgerond in 9F.

### 4.11 Visuele punten uit de 9F-sessie
- **Observatie:** tijdens de 9F-sessie zijn drie visuele punten
  vastgesteld: visuele selectie in Analyse, checkbox-zichtbaarheid in
  donker thema, en i18n-menging in Diagnose/Result.
- **Status:** opgenomen in §2.21; fase 11.

---

## 5. Status van dit document

- Dit document is **levend**. Bij elke fase mogen nieuwe vragen worden
  toegevoegd en opgeloste vragen worden gemarkeerd.
- Opgeloste vragen blijven staan voor historische context.