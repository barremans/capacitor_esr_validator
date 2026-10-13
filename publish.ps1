# publish.ps1 - Electronics Diagnostic Tool Hub / ESR Tester
# =============================================================================
# Release + asset + version.txt naar GitHub.
# Run vanuit de repo root (C:\PY\capacitor_esr_validator):  .\publish.ps1
# Vereist: gh (ingelogd) + git
#
# Leest de versie uit app/version.py, controleert de Authenticode-handtekening
# van de installer (release-gate), maakt de GitHub-release aan, uploadt de
# installer, schrijft releases/latest/version.txt en pusht version.py +
# version.txt naar GitHub.
#
# Version: 1.0.0
# Author:  Bart Bossuyt
# Changes: 1.0.0 (2026-10-13) - Fase 9C+9D. Eerste versie, 1-op-1 afgeleid
#                               van ArticleSearch publish.ps1 v1.1. Enige
#                               verschillen:
#                                 - versionPy = app\version.py
#                                 - Repo-default = capacitor_esr_validator
#                                   (pas aan naar je echte GitHub-repo-naam)
#                                 - Asset-naam = ESR_TesterSetup_<versie>.exe
#                               De release-gate (geldige Authenticode-
#                               handtekening verplicht) is behouden.
# =============================================================================

param(
    [string]$Owner = "barremans",
    [string]$Repo  = "capacitor_esr_validator"
)

$ErrorActionPreference = "Stop"

# Repo root = map waar dit script staat
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

# 1) Versie lezen uit app/version.py
$versionPy = Join-Path $Root "app\version.py"
if (-not (Test-Path $versionPy)) { throw "Niet gevonden: $versionPy" }

$txt = Get-Content $versionPy -Raw
$m = [regex]::Match($txt, '__version__\s*=\s*["''](?<v>\d+\.\d+\.\d+)["'']')
if (-not $m.Success) { throw "Kon __version__ niet vinden in app/version.py" }
$version = $m.Groups["v"].Value

$tag = "v$version"
$assetName = "ESR_TesterSetup_$version.exe"
$assetPath = Join-Path $Root ("dist\" + $assetName)

Write-Host "[INFO] Repo: $Owner/$Repo"
Write-Host "[INFO] Versie: $version"
Write-Host "[INFO] Tag: $tag"
Write-Host "[INFO] Asset: $assetPath"

# 2) Installer bestaat?
if (-not (Test-Path $assetPath)) {
    throw "Installer niet gevonden: $assetPath`nRun eerst build_installer.bat en maak de installer."
}

# 2b) RELEASE-GATE: publiceer nooit een ongesigneerde/ongeldige installer.
Write-Host "[CHECK] Authenticode-handtekening van installer controleren..."
$sig = Get-AuthenticodeSignature -FilePath $assetPath

if ($sig.Status -ne [System.Management.Automation.SignatureStatus]::Valid) {
    throw "PUBLICATIE GEBLOKKEERD: installer heeft geen geldige Authenticode-handtekening. Status: $($sig.Status). Bestand: $assetPath"
}
if (-not $sig.SignerCertificate) {
    throw "PUBLICATIE GEBLOKKEERD: geen SignerCertificate gevonden op installer: $assetPath"
}

Write-Host "[OK] Geldige Authenticode-handtekening:"
Write-Host "  Subject    : $($sig.SignerCertificate.Subject)"
Write-Host "  Thumbprint : $($sig.SignerCertificate.Thumbprint)"
Write-Host "  Geldig tot : $($sig.SignerCertificate.NotAfter)"

# 3) Release bestaat? Anders maken.
$releaseExists = $false
try {
    & gh release view $tag --repo "$Owner/$Repo" *> $null
    if ($LASTEXITCODE -eq 0) { $releaseExists = $true }
}
catch {
    $releaseExists = $false
}

if (-not $releaseExists) {
    Write-Host "[INFO] Release $tag bestaat nog niet. Maken..."
    & gh release create $tag --repo "$Owner/$Repo" --title "$tag" --notes "Release $tag"
    if ($LASTEXITCODE -ne 0) { throw "Aanmaken release $tag mislukt." }
}
else {
    Write-Host "[INFO] Release $tag bestaat al."
}

# 4) Upload asset (clobber = overschrijven indien al aanwezig)
Write-Host "[INFO] Uploaden asset..."
& gh release upload $tag "$assetPath" --repo "$Owner/$Repo" --clobber
if ($LASTEXITCODE -ne 0) { throw "Upload asset mislukt." }

# 5) Download-URL opbouwen
$downloadUrl = "https://github.com/$Owner/$Repo/releases/download/$tag/$assetName"
Write-Host "[OK] Download URL: $downloadUrl"

# 6) version.txt (2 regels) schrijven
$versionTxt = Join-Path $Root "releases\latest\version.txt"
$versionDir = Split-Path -Parent $versionTxt
if (-not (Test-Path $versionDir)) { New-Item -ItemType Directory -Path $versionDir -Force | Out-Null }

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($versionTxt, "$version`n$downloadUrl", $utf8NoBom)

# 7) Commit + push version.py EN version.txt
& git add "app/version.py" "releases/latest/version.txt"
& git commit -m "Release $version - sync app/version.py and version.txt" *> $null
& git push
if ($LASTEXITCODE -ne 0) {
    throw "git push MISLUKT (exitcode $LASTEXITCODE). De GitHub Release en de installer-asset staan wel al online (die gaan via 'gh', los van git push), maar app/version.py en releases/latest/version.txt zijn enkel LOKAAL gecommit en NIET naar GitHub gepusht - de app detecteert de nieuwe versie hierdoor niet. Los het pushprobleem op (bv. eerst 'git pull --rebase origin main') en run dan handmatig: git push"
}
Write-Host "[OK] app/version.py + version.txt succesvol gepusht naar $Owner/$Repo."

Write-Host ""
Write-Host "============================================================"
Write-Host "[DONE] Published $tag"
Write-Host "Release: https://github.com/$Owner/$Repo/releases/tag/$tag"
Write-Host "Version file: https://raw.githubusercontent.com/$Owner/$Repo/main/releases/latest/version.txt"
Write-Host "============================================================"