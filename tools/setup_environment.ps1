# mLoop Framework Environment Setup & Tuning Script (Windows PowerShell)
# Configure les variables d'environnement utilisateur pour 8 Go de RAM Sidecar Node.js et UTF-8 natif.

Write-Host "=== CONFIGURATION DE L'ENVIRONNEMENT MLOOP & OPENCODE ===" -ForegroundColor Cyan

# 1. Allocation Mémoire 8 GB (8192 MB) pour Node.js / OpenCode Sidecar (Anti-OOM)
[Environment]::SetEnvironmentVariable("NODE_OPTIONS", "--max-old-space-size=8192", "User")
$env:NODE_OPTIONS = "--max-old-space-size=8192"
Write-Host "  [OK] NODE_OPTIONS configuré à --max-old-space-size=8192 (8 Go RAM)" -ForegroundColor Green

# 2. Forçage Encodage UTF-8 sous Windows PowerShell / Python
[Environment]::SetEnvironmentVariable("PYTHONUTF8", "1", "User")
[Environment]::SetEnvironmentVariable("PYTHONIOENCODING", "utf-8", "User")
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
Write-Host "  [OK] PYTHONUTF8 et PYTHONIOENCODING configurés à UTF-8" -ForegroundColor Green

Write-Host "`nConfiguration de l'environnement terminée avec succès !" -ForegroundColor Cyan
