# ==============================================================================
# mLoop x Herdr - Windows PowerShell Boot Script (Full Autonomous Mode)
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=== mLoop x Herdr Daemon Initializer (Windows) ===" -ForegroundColor Cyan

# 1. Démarrer / Vérifier le daemon Herdr
Write-Host "[1/4] Démarrage / Vérification du daemon Herdr..." -ForegroundColor Yellow
try {
    herdr daemon start 2>$null
} catch {
    # Daemon déjà actif
}

# 2. Créer l'espace de travail d'orchestration
Write-Host "[2/4] Création du workspace master-orchestration..." -ForegroundColor Yellow
$currentDir = Get-Location
$jsonOutput = herdr workspace create --cwd "$currentDir" --label "master-orchestration"

try {
    $parsed = $jsonOutput | ConvertFrom-Json
    $rootPaneId = $parsed.result.root_pane.pane_id
    $workspaceId = $parsed.result.workspace.workspace_id
} catch {
    Write-Host "ERROR: Échec du parsing du JSON Herdr." -ForegroundColor Red
    exit 1
}

Write-Host "-> Workspace créé ($workspaceId) avec le volet racine : $rootPaneId" -ForegroundColor Green

# 3. Lancer l'agent maître dans le volet via pane run (détection auto par Herdr)
Write-Host "[3/4] Démarrage de l'agent maître (opencode --yolo)..." -ForegroundColor Yellow
herdr pane run "$rootPaneId" "opencode --yolo"

# Focus sur le nouveau workspace pour afficher OpenCode immédiatement à l'écran
try {
    herdr workspace focus "$workspaceId" 2>$null
} catch {
    # Ignorer si déjà au premier plan
}

# 4. Attacher la session
Write-Host "[4/4] Attachement à la session Herdr..." -ForegroundColor Cyan
herdr session attach master-orchestration
