# File:    Export-SigningCertificate.ps1
# Rol:     Exporteert het Authenticode signing-certificaat van een of
#          meerdere .exe-bestanden als .cer-bestand(en) -- klaar om te
#          uploaden in security.microsoft.com > Settings > Endpoints >
#          Indicators > Certificates > Add item (Action: Allow). Herbruikbaar
#          voor élke huidige of toekomstige CGK-applicatie (ArticleSearch,
#          Project Generator, OpenElements2Csv, ESR Tester, ...): geef één
#          of meerdere paden mee (bestand, map, of wildcard) en het script
#          vindt en exporteert automatisch elk uniek certificaat dat het
#          tegenkomt.
# Versie:  1.0.1
# Auteur:  Barremans
#
# Gebruik:
#   # Eén specifieke exe
#   .\Export-SigningCertificate.ps1 -Path "C:\PY\capacitor_esr_validator\dist\ESR_Tester_1.0.0\ESR_Tester.exe"
#
#   # Een hele map (zoekt recursief alle .exe's)
#   .\Export-SigningCertificate.ps1 -Path "C:\PY\capacitor_esr_validator\dist\"
#
#   # Meerdere apps in één keer -- dedupliceert automatisch als ze hetzelfde
#   # (interne CGK-)certificaat delen, dus je krijgt maar 1 .cer om te
#   # uploaden i.p.v. eentje per app.
#   .\Export-SigningCertificate.ps1 -Path "C:\ArticleSearch\","C:\PY\capacitor_esr_validator\dist\","C:\PY\OpenElements2Csv\"
#
#   # Wildcard
#   .\Export-SigningCertificate.ps1 -Path "C:\PY\*\dist\*.exe"
#
# Output: één .cer-bestand per uniek certificaat in .\signing-certs\
#         (of de map opgegeven via -OutputDir), plus een samenvattingstabel
#         met Subject/Issuer/Thumbprint/vervaldatum per gevonden certificaat.
#
# Changes:
#   1.0.1 (2026-10-13) - Waarschuwing toegevoegd wanneer een gevonden
#                        certificaat al VERLOPEN is (NotAfter < nu). Dat
#                        voorkomt dat een verlopen cert stil wordt
#                        geëxporteerd en later de import/indicator faalt.
#                        Verder identiek aan 1.0.0.
#   1.0.0 - Eerste versie.

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string[]]$Path,

    [string]$OutputDir = ".\signing-certs"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

# Verzamel alle .exe-bestanden uit de opgegeven paden (bestand, map, of wildcard)
$exeFiles = foreach ($p in $Path) {
    if (Test-Path $p -PathType Container) {
        Get-ChildItem -Path $p -Filter *.exe -Recurse -File -ErrorAction SilentlyContinue
    }
    else {
        Get-ChildItem -Path $p -ErrorAction SilentlyContinue
    }
}

if (-not $exeFiles) {
    Write-Warning "Geen .exe-bestanden gevonden voor: $($Path -join ', ')"
    return
}

# Per uniek certificaat (thumbprint) exporteren we maar 1x een .cer -- apps
# die hetzelfde interne CGK-certificaat delen hebben er samen maar 1 nodig
# in Defender for Endpoint.
$seen = @{}
$results = @()

foreach ($exe in $exeFiles) {
    $sig = Get-AuthenticodeSignature -FilePath $exe.FullName

    if (-not $sig.SignerCertificate) {
        Write-Warning "Geen handtekening gevonden op: $($exe.FullName) (status: $($sig.Status))"
        continue
    }

    $thumb = $sig.SignerCertificate.Thumbprint

    if ($seen.ContainsKey($thumb)) {
        Write-Host "  (zelfde certificaat als $($seen[$thumb]), overgeslagen): $($exe.Name)" -ForegroundColor DarkGray
        continue
    }
    $seen[$thumb] = $exe.Name

    # Waarschuwing bij verlopen certificaat
    if ($sig.SignerCertificate.NotAfter -lt (Get-Date)) {
        Write-Warning "Certificaat VERLOPEN op $($sig.SignerCertificate.NotAfter): $($exe.FullName)"
    }

    $outFile = Join-Path $OutputDir "$thumb.cer"
    Export-Certificate -Cert $sig.SignerCertificate -FilePath $outFile -Type CERT | Out-Null

    $results += [PSCustomObject]@{
        Bestand    = $exe.FullName
        Subject    = $sig.SignerCertificate.Subject
        Issuer     = $sig.SignerCertificate.Issuer
        Thumbprint = $thumb
        NotAfter   = $sig.SignerCertificate.NotAfter
        Status     = $sig.Status
        CerFile    = $outFile
    }

    Write-Host "[OK] $($exe.Name) -> $outFile" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================================"
Write-Host "Samenvatting -- $($results.Count) uniek(e) certifica(a)t(en) geexporteerd naar $OutputDir"
Write-Host "============================================================"
$results | Format-Table Bestand, Subject, Thumbprint, NotAfter, Status -AutoSize

Write-Host ""
Write-Host "Volgende stap per .cer-bestand:"
Write-Host "  security.microsoft.com > Settings (tandwiel) > Endpoints > Indicators"
Write-Host "  > tabblad Certificates > + Add item > upload het .cer-bestand > Action: Allow"