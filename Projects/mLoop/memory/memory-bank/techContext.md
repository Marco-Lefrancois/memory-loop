# Tech Context — mLoop

## 1. Stack Technique
- Langage : Python 3.11+ (Typage strict, dataclasses, Protocol).
- Orchestration PTY : Herdr (v0.8.0+).
- Runtimes Workers : OpenCode (v1.18.x), Cline (v3.0.x).
- Tests & Qualité : pytest, pytest-asyncio, Vibe-Check (23 contrôles déterministes).
- Stockage & Indexation : SQLite FTS5, Hypergraphe sémantique JSON.

## 2. Commandes CLI Souveraines mLoop
```powershell
python src/swarm.py doctor --agents
python src/swarm.py sync --project mLoop
python src/swarm.py vibe-check --project mLoop
python src/swarm.py worker-spawn --kind cline --story <ID> --project mLoop
python src/swarm.py worker-spawn --kind opencode --story <ID> --project mLoop
```
