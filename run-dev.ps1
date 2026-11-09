<#
    Indes Portal — local development server.

    Activates the local virtualenv and starts Django's development server on
    port 9000 using the SQLite dev settings module.

    Usage (from the repository root):
        .\run-dev.ps1
        .\run-dev.ps1 -Port 9100
        .\run-dev.ps1 -NoReload
#>
param(
    [int]$Port = 9000,
    [switch]$NoReload
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $repoRoot

$venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $venvPython)) {
    Write-Host 'Virtualenv not found. Creating .venv and installing requirements...' -ForegroundColor Yellow
    python -m venv .venv
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r requirements.txt
}

if (-not (Test-Path (Join-Path $repoRoot '.env'))) {
    Write-Host '.env not found — copy .env.example and fill in local dev values.' -ForegroundColor Yellow
}

if (-not (Test-Path (Join-Path $repoRoot 'db.sqlite3'))) {
    Write-Host 'No db.sqlite3 yet. Run the migrations first:' -ForegroundColor Yellow
    Write-Host '    .venv\Scripts\python manage.py migrate --settings=ong_platform.settings_dev'
}

$args = @(
    'manage.py', 'runserver', "0.0.0.0:$Port",
    '--settings=ong_platform.settings_dev'
)

if ($NoReload) { $args += '--noreload' }

Write-Host "Starting Indes Portal on http://localhost:$Port/ (settings_dev, SQLite)" -ForegroundColor Green
& $venvPython @args