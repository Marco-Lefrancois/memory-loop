# Moteur d'Auto-Calibrage Natif `mLoop Calibrate Engine`

Ce document constitue la référence d'architecture du système d'auto-étalonnage continu de mLoop.

---

## 🏛️ Vue d'Ensemble

Le moteur `Calibrate Engine` garantit un alignement déterministe entre le code Python, les configurations IDE, les compétences des agents et les mémoires sémantiques.

```
[1/8] CLI -> OpenCode Shortcuts .......... [PASS / REPAIRED]
[2/8] MCP Bridges -> opencode.json ........ [PASS / REPAIRED]
[3/8] Skills -> Router Index .............. [PASS / REPAIRED]
[4/8] Directives AGENTS.md / GEMINI.md .... [PASS]
[5/8] Gabarits standards/blueprints ....... [PASS]
[6/8] Synchronisation SQLite & Graphify ... [PASS]
[7/8] Registre Open Notebook SHA256 ....... [PASS]
[8/8] Validation 3 Guardrails (audit-loop)  [PASS Exit 0]
```

---

## 🛠️ Utilisation CLI & OpenCode

```powershell
# Exécution CLI en mode Auto-Repair
python src/swarm.py calibrate --project <nom_projet>

# Raccourci OpenCode
/loop-calibrate <nom_projet>
```
