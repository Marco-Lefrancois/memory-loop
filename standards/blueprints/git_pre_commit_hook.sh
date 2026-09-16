#!/bin/sh
# mLoop Git Pre-Commit Hook (Auto-protection anti-amnésie & hygiène de projet)
echo "🛡️ [mLoop Pre-Commit] Exécution du Guardrail Vibe-Check..."
cd "{{ROOT_DIR}}"
python "{{SWARM_PY}}" vibe-check --project {{PROJECT_NAME}}
if [ $? -ne 0 ]; then
    echo "❌ [mLoop Pre-Commit] Commit bloqué : Échec du Guardrail Vibe-Check."
    exit 1
fi
exit 0
