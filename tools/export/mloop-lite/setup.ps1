# Script d'installation PowerShell mLoop Lite
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "🚀 Installation & Initialisation de l'Environnement mLoop Lite" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

try {
    $pyVer = python --version
    Write-Host "Python detecte : $pyVer" -ForegroundColor Green
} catch {
    Write-Host "❌ Python n'est pas detecte. Installez-le via : winget install Python.Python.3.11" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path ".venv")) {
    Write-Host "[1/4] Creation de l'environnement virtuel (.venv)..." -ForegroundColor Yellow
    python -m venv .venv
}

Write-Host "[2/4] Installation des dependances..." -ForegroundColor Yellow
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\pip.exe install -r requirements.txt

Write-Host "[3/4] Creation et verification des repertoires piliers..." -ForegroundColor Yellow
$dirs = @("projects", "reference", "docs", "docs/adr", "deliverables", "deliverables/templates", "memory", "memory/evidence")
foreach ($d in $dirs) {
    if (-not (Test-Path $d)) {
        New-Item -ItemType Directory -Path $d -Force | Out-Null
    }
}

Write-Host "`n✅ Installation et arborescence pretes avec succes !" -ForegroundColor Green
Write-Host "Pour demarrer : mloop resume ou mloop init --role ba --project NomClient" -ForegroundColor Cyan
