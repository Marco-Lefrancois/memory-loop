# Tech Context — Memory Loop (mLoop)

## 1. Stack Technique
- Langage : Python 3.11+ (Typage strict, dataclasses, Protocol).
- Orchestration PTY : Herdr (v0.8.0+).
- Runtimes Workers : OpenCode (v1.18.x), Cline (v3.0.x).
- Tests & Qualité : pytest, pytest-asyncio, Vibe-Check (23 contrôles déterministes).
- Stockage & Indexation : SQLite FTS5, Hypergraphe sémantique JSON.

## 2. Commandes CLI Souveraines mLoop
```powershell
# Diagnostic de santé des agents
python src/swarm.py doctor --agents

# Synchronisation et mise à jour de la mémoire
python src/swarm.py sync --project mLoop

# Contrôle de vol pré-vol (Guardrails)
python src/swarm.py vibe-check --project mLoop

# Lancement d'un worker délégué via Herdr
python src/swarm.py worker-spawn --kind cline --story <ID> --project mLoop
python src/swarm.py worker-spawn --kind opencode --story <ID> --project mLoop
```
