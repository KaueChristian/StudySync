# ============================================================================
# StudySync — arquivos de release (Windows)
#
# Gera em desktop\release\:
#   StudySync-Setup-<versão>.exe      instalador (Inno Setup)
#   StudySync-<versão>-win64.zip      versão portátil (a pasta inteira do app)
#   SHA256SUMS.txt                    checksums dos dois
#
# É o mesmo script que o GitHub Actions roda ao receber uma tag v* — rodar
# localmente reproduz a CI.
#
# Uso (na raiz do repositório):
#   pwsh desktop\release.ps1                 # versão lida do código
#   pwsh desktop\release.ps1 -Version 1.0.0  # exige que o código declare 1.0.0
# ============================================================================
param(
    [string]$Version = ''
)
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot

# --- Versão: uma só em todo lugar -------------------------------------------
$configMatch = Select-String -Path (Join-Path $root 'backend\app\core\config.py') -Pattern 'VERSION: str = "([^"]+)"'
if (-not $configMatch) { throw 'VERSION não encontrada em backend\app\core\config.py' }
$backendVersion = $configMatch.Matches[0].Groups[1].Value
$frontendVersion = (Get-Content (Join-Path $root 'frontend\package.json') -Raw | ConvertFrom-Json).version

if ($backendVersion -ne $frontendVersion) {
    throw "Versões divergentes: config.py=$backendVersion, package.json=$frontendVersion"
}
if ($Version -and $Version -ne $backendVersion) {
    throw "A tag pede a versão $Version, mas o código declara $backendVersion. Atualize config.py e package.json."
}
$Version = $backendVersion
Write-Host "==> Versão $Version" -ForegroundColor Cyan

# --- Build do app -------------------------------------------------------------
& (Join-Path $PSScriptRoot 'build.ps1')

$releaseDir = Join-Path $PSScriptRoot 'release'
if (Test-Path $releaseDir) { Get-ChildItem $releaseDir | Remove-Item -Recurse -Force }
New-Item -ItemType Directory -Force $releaseDir | Out-Null

# --- Instalador ---------------------------------------------------------------
$iscc = (Get-Command iscc.exe -ErrorAction SilentlyContinue).Source
if (-not $iscc) {
    $iscc = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1
}
if (-not $iscc) { throw 'Inno Setup 6 (ISCC.exe) não encontrado. Instale com: winget install JRSoftware.InnoSetup' }

Write-Host '==> Instalador (Inno Setup)' -ForegroundColor Cyan
& $iscc /Q "/DAppVersion=$Version" (Join-Path $PSScriptRoot 'installer.iss')
if ($LASTEXITCODE -ne 0) { throw 'Inno Setup falhou' }

# --- Zip portátil -------------------------------------------------------------
Write-Host '==> Zip portátil' -ForegroundColor Cyan
$zip = Join-Path $releaseDir "StudySync-$Version-win64.zip"
# Com a pasta StudySync\ na raiz do zip: extrair entrega o app inteiro junto.
Compress-Archive -Path (Join-Path $PSScriptRoot 'dist\StudySync') -DestinationPath $zip

# --- Checksums ----------------------------------------------------------------
$sums = Get-ChildItem $releaseDir -File | Where-Object Extension -in '.exe', '.zip' | ForEach-Object {
    "{0}  {1}" -f (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower(), $_.Name
}
# Sem BOM e com LF: formato que o `sha256sum -c` aceita.
[IO.File]::WriteAllText((Join-Path $releaseDir 'SHA256SUMS.txt'), (($sums -join "`n") + "`n"))

Write-Host "==> Pronto em $releaseDir" -ForegroundColor Green
Get-ChildItem $releaseDir | Format-Table Name, @{ n = 'MB'; e = { '{0:N1}' -f ($_.Length / 1MB) } } -AutoSize
