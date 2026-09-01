---
name: calibrate
description: "Calibrate: Auto-étalonnage continu de l'écosystème mLoop (CLI, opencode.json, skills, MCP, AGENTS.md, guardrails)."
disable-model-invocation: false
---

# 📐 Skill Calibrate (Auto-Étalonnage Écosystème mLoop)

> **Status:** Active | **Standard:** mLoop Core

## 🎯 Purpose
Ce skill permet de vérifier et réaligner instantanément l'ensemble de l'écosystème mLoop. À utiliser à la demande de l'utilisateur ("recalibre mloop", "vérifie les outils") ou après l'ajout d'une nouvelle fonctionnalité/commande dans `src/`.

## 🗺️ Les 8 Contrôles Automatisés du Calibrage

1. **CLI ➔ OpenCode Shortcuts** : Aligne les commandes `swarm.py` avec `opencode.json`.
2. **MCP Bridges** : Vérifie la déclaration des ponts Python `src/bridges/mcp_*.py` sous `opencode.json["mcp"]`.
3. **Skills ➔ Router Index** : Enregistre tout dossier de compétence `.agents/skills/` dans [.agents/skills/router/SKILL.md](file:///c:/Memory%20Loop/.agents/skills/router/SKILL.md).
4. **Directives Système** : S'assure que `AGENTS.md` et `GEMINI.md` listent l'outillage complet.
5. **Gabarits Officiels** : Contrôle la conformité des blueprints sous `standards/blueprints/`.
6. **Synchronisation Sémantique** : Met à jour la base SQLite FTS5 et le graphe Graphify.
7. **Registre Ingestion SHA256** : Vérifie l'intégrité anti-doublon d'ingestion.
8. **Validation Guardrails (audit-loop)** : Certifie l'état `status: PASS` (Exit 0).

## 🚀 Commande d'Exécution

```powershell
# Exécution CLI déterministe en mode Auto-Repair
python src/swarm.py calibrate --project <nom_projet>

# Raccourci OpenCode
/loop-calibrate <nom_projet>
```
