---
name: wait-what
description: Pause de sécurité et d'auto-audit contradicteur en cas d'incohérence majeure ou de risque d'hallucination. Use when encountering an obvious contradiction, suspecting hallucinated requirements, or performing a Stop & Ask pause.
---

# 🛑 Skill `/wait-what` (Sanity Check & Pause Anti-Hallucination)

> **Standard :** mLoop Safety Interceptor Protocol  

## 🧠 Description
Le skill `/wait-what` est un réflexe de sécurité agentique. Lorsqu'un agent mLoop rencontre une contradiction entre la demande de l'utilisateur, la base de connaissances (`docs/`) et le code physique (`src/`), ou s'il s'apprête à effectuer une action potentiellement destructive, il déclenche ce skill pour s'arrêter et questionner explicitement l'utilisateur (*Stop & Ask*).

## ⚡ Directives d'Interception
1. **Fact-Check Obligatoire** : Relancer la recherche de faits via `loop_mem_search` ou `graphify query`.
2. **Recherche de Contradiction** : Vérifier si la demande enfreint un ADR existant sous `docs/01-architecture/`.
3. **Formulation de l'Alerte** : 
   - Exposer clairement l'incohérence détectée.
   - Proposer les 2 ou 3 options d'arbitrage possibles.
   - Bloquer toute modification de code tant que l'utilisateur n'a pas tranché.
