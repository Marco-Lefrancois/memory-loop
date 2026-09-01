#!/usr/bin/env bash
# ==============================================================================
# mLoop x Herdr - Boot Script Full Autonomous Agent (Unattended Mode)
# ==============================================================================

set -e

echo "=== mLoop x Herdr Daemon Initializer ==="

# 1. Assurer que le daemon Herdr est démarré
echo "[1/4] Vérification du daemon Herdr..."
herdr daemon start 2>/dev/null || true

# 2. Créer l'espace de travail d'orchestration maître
echo "[2/4] Création du workspace master-orchestration..."
WORKSPACE_JSON=$(herdr workspace create --cwd "$(pwd)" --label "master-orchestration" --no-focus)
ROOT_PANE_ID=$(echo "$WORKSPACE_JSON" | jq -r '.result.root_pane.pane_id')

if [ -z "$ROOT_PANE_ID" ] || [ "$ROOT_PANE_ID" == "null" ]; then
    echo "ERROR: Impossible de récupérer le PANE_ID racine."
    exit 1
fi

echo "-> Workspace créé avec le volet racine : $ROOT_PANE_ID"

# 3. Lancer l'agent maître en mode auto-approbation avec le protocole mLoop
echo "[3/4] Démarrage de l'agent orchestrateur maître (claude --dangerously-skip-permissions)..."
herdr agent start master_orchestrator --kind claude --pane "$ROOT_PANE_ID" -- --dangerously-skip-permissions

echo "[4/4] Attachement à la session d'orchestration Herdr..."
herdr session attach -s master-orchestration
