# Testmatrix — Defender / Intune / SmartScreen

**Versie:** 1.0.0
**Datum:** 2026-10-13
**Auteur:** Bart Bossuyt
**Doel:** Vastleggen op welke pc-types de ESR Tester-installer is getest,
wat het resultaat was, en welke actie nodig is bij een nieuwe versie of
een nieuw certificaat.

---

## 1. Scope

Deze matrix dekt **twee** pc-types:

| Type | Omschrijving | Beleid |
|---|---|---|
| **Gewone Windows-pc** | Niet-beheerde pc, standaard Defender | SmartScreen actief, "More info → Run anyway" beschikbaar |
| **Intune-beheerde pc** | Beheerde pc, Defender for Endpoint, strenger ASR/SmartScreen-beleid | SmartScreen blokkeert zonder omzeiling; Defender-indicator nodig |

**Niet in scope (bewust):**
- WDAC-pc's — op 2026-10-13 bevestigd **niet actief** in de doelomgeving.
- AppLocker-pc's — idem.
- Servers, VM's zonder Defender, andere platformen.

Als WDAC of AppLocker later wél actief blijkt, is de Defender-indicator
**niet voldoende**; dan is uitrol van het certificaat naar `Trusted
Publishers` (Intune/GPO) of een publiek vertrouwd certificaat nodig. Zie
`docs/openvragen.md` §2.19.

---

## 2. Bewezen status (2026-10-13)

Getest met **`ESR_TesterSetup_1.0.3.exe`**, gesigned met
`CN=CGK Local Signing`, thumbprint `BD1DC390D56E3392836FD6E39470D5F766346509`,
geldig tot 2028-09-17.

| # | Test | Pc-type | Resultaat | Bewijs |
|---|---|---|---|---|
| 1 | Installer start, SmartScreen-waarschuwing | Gewone Windows-pc | ✅ Bewezen | "More info → Run anyway" werkt |
| 2 | Installatie voltooit | Gewone Windows-pc | ✅ Bewezen | App gestart vanuit `C:\Program Files\Electronics Diagnostic Tool Hub\ESR_Tester\` |
| 3 | Uninstaller gesigned | Gewone Windows-pc | ✅ Bewezen | `Get-AuthenticodeSignature` op `unins000.exe` = `Valid` |
| 4 | Installer start, geen blokkade | Intune-beheerde pc | ✅ Bewezen | Defender-indicator `Allow` actief; geen SmartScreen-blokkade |
| 5 | Installatie voltooit | Intune-beheerde pc | ✅ Bewezen | App gestart vanuit installatiemap |
| 6 | Herstart na installatie | Intune-beheerde pc | ✅ Bewezen | App blijft werken, geen Defender-quarantaine |
| 7 | `signtool verify /pa /v` op installer | Buildmachine | ✅ Bewezen | `Successfully verified`, timestamp aanwezig |
| 8 | `Get-AuthenticodeSignature` op installer | Buildmachine | ✅ Bewezen | `Status: Valid`, thumbprint `BD1DC390…6509` |

**Conclusie:** de volledige keten werkt op beide pc-types. De
Defender-indicator is voldoende voor de huidige doelomgeving.

---

## 3. Wat te doen bij een nieuwe versie

Voor **elke** nieuwe release (patch, minor, major):

1. **Build + publish** via `build_and_publish.ps1` (of `build_installer.bat` + `publish.ps1`).
2. **Controleer** dat de release-gate in `publish.ps1` `Valid` teruggaf (gebeurt automatisch; bij twijfel `Get-AuthenticodeSignature` handmatig).
3. **Test op een gewone Windows-pc:** installer start, installatie voltooit, app start.
4. **Test op een Intune-pc:** installer start zonder blokkade, installatie voltooit, app start.
5. **Geen nieuwe Defender-indicator nodig** zolang hetzelfde certificaat (`CN=CGK Local Signing`, thumbprint `BD1DC390…6509`) gebruikt wordt.

Een nieuwe versie met hetzelfde certificaat valt automatisch onder de
bestaande indicator — geen IT-ticket nodig.

---

## 4. Wat te doen bij een nieuw certificaat

Als het certificaat verandert (verloop 2028-09-17, nieuwe buildmachine,
nieuwe developer, overstap naar publiek vertrouwde CA):

1. **Exporteer** het nieuwe certificaat:
   ```powershell
   .\Export-SigningCertificate.ps1 -Path "C:\PY\capacitor_esr_validator\dist\"
   ```
2. **Vergelijk** het thumbprint met `BD1DC390…6509`.
3. **Ander thumbprint?** Voeg het nieuwe `.cer`-bestand toe als indicator:
   - `security.microsoft.com` → Settings → Endpoints → Indicators → Certificates → Add item
   - Response action: **Allow**
   - Scope: **All devices in my organization**
   - Zie `signingContext.md` §4.2 voor de volledige stappen.
4. **Wacht 15–60 minuten** op sync.
5. **Herhaal** de testmatrix uit §2 op een Intune-pc.

De oude indicator kan blijven staan (onschadelijk) of verwijderd worden
zodra geen enkele actieve installatie het oude certificaat meer gebruikt.

---

## 5. Wat te doen bij een nieuwe app

Voor een gloednieuwe CGK-app die hetzelfde certificaat gebruikt:

- **Geen nieuwe indicator nodig** — de bestaande `Allow`-regel dekt elk
  bestand dat met `CN=CGK Local Signing` gesigned is.
- **Wel controleren** na de eerste build:
  ```powershell
  .\Export-SigningCertificate.ps1 -Path "C:\PY\<NieuweApp>\dist\"
  ```
  Zelfde thumbprint? Dan is de nieuwe app al gedekt.

---

## 6. Openstaande punten

| Punt | Status | Impact |
|---|---|---|
| WDAC/AppLocker actief? | **Beantwoord 2026-10-13: nee** | Geen extra actie nodig |
| Windows-trust op andere endpoints (root/publisher via Intune/GPO) | Open | Niet nodig zolang Defender-indicator werkt |
| Vervanging bij verloop cert (2028-09-17) | Open | Nieuwe indicator nodig (zie §4) |
| Publiek vertrouwd (EV-)certificaat | Open | Structurele oplossing; zie `04-…md` §8 |
| Testmatrix op andere Windows-versies (Win10 vs Win11) | Open | Uitbreiden indien nodig |

---

## 7. Status van dit document

- Dit document is **levend**. Bij elke nieuwe versie of certificaatwijziging
  wordt §2 bijgewerkt met de nieuwe testresultaten.
- Opgeloste punten blijven staan voor historische context.