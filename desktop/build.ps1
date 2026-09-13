# ============================================================================
# StudySync — build do executável desktop (Windows)
#
# Pré-requisitos: backend\venv criado com backend\requirements.txt, e as
# dependências de build instaladas nele:
#   backend\venv\Scripts\python.exe -m pip install -r desktop\requirements.txt
#
# Uso (na raiz do repositório):
#   pwsh desktop\build.ps1
#
# Saída: desktop\dist\StudySync\StudySync.exe (a pasta inteira é o app).
# ============================================================================
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root 'backend\venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw "venv do backend não encontrado em $python" }

Write-Host '==> Build do frontend' -ForegroundColor Cyan
Push-Location (Join-Path $root 'frontend')
try {
    npm run build
    if ($LASTEXITCODE -ne 0) { throw 'npm run build falhou' }
} finally { Pop-Location }

Write-Host '==> Empacotamento com PyInstaller' -ForegroundColor Cyan
& $python -m PyInstaller (Join-Path $PSScriptRoot 'StudySync.spec') `
    --noconfirm --clean `
    --distpath (Join-Path $PSScriptRoot 'dist') `
    --workpath (Join-Path $PSScriptRoot 'build')
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller falhou' }

Write-Host "==> Pronto: $(Join-Path $PSScriptRoot 'dist\StudySync\StudySync.exe')" -ForegroundColor Green
