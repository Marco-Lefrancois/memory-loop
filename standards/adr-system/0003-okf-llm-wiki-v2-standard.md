# ADR-0003 : Adoption de l'Open Knowledge Format (OKF v0.1) et du Paradigme LLM Wiki v2

* **Statut** : Accepté
* **Date** : 30 Juillet 2026
* **Décideurs** : Équipe Architecture mLoop & Co-Architecte IA
* **Contexte** : Framework Memory Loop (mLoop v2.2.0)

---

## 1. Contexte et Problématique

Les approches traditionnelles de génération augmentée par récupération (**RAG classique**) reposent sur un découpage linéaire ("chunking") et éphémère de la documentation. Ce modèle provoque une fragmentation sémantique, une absence de capitalisation cognitive et le phénomène de **Context Rot** sur des bases de connaissances volumineuses (> 20 pages).

Le framework mLoop repose sur le paradigme du **LLM-Wiki (Base de connaissances compilée et persistante)**. Pour pérenniser et standardiser ce modèle, mLoop doit adopter une spécification universelle d'interopérabilité et gérer dynamiquement le cycle de vie de sa mémoire.

---

## 2. Décision d'Architecture

Il est décidé d'adopter formellement l'**Open Knowledge Format (OKF v0.1)** de Google Cloud et les extensions du **LLM Wiki v2 (Andrej Karpathy + agentmemory / rohitg00)** comme standard universel de gouvernance mnémonique dans mLoop.

### A. Manifest OKF v0.1 Minimal
Tout document SSOT, règle métier (`RM-XXX`) ou récit (`ST-*.md`) dans mLoop utilise le Frontmatter YAML OKF v0.1 :
```yaml
---
type: Architecture | BusinessRule | Story | Infrastructure
title: Nom du Concept ou Récit
description: Résumé condensé à haut niveau d'abstraction
resource: file:///chemin/vers/la/source
tags: [tag1, tag2]
timestamp: 2026-07-30T00:00:00Z
---
```

### B. Cycle de Vie Mnémonique à 4 Tiers (LLM Wiki v2)
La mémoire de mLoop est structurée en 4 niveaux d'abstraction :
1. **Working Memory** : Traces d'exécution brutes (`graph_execution_log.json`).
2. **Episodic Memory** : Compte-rendus de sessions `/grill-me` et logs de handoff.
3. **Semantic Memory** : Fichiers SSOT OKF (`docs/`, `RM-XXX`, `ADR-XXX`).
4. **Procedural Memory** : Règles d'auto-immunisation (`rho_rules.yaml`) et compétences (`.agents/skills/`).

### C. Scoring de Confiance, Supersession & Rétention (Ebbinghaus Decay)
- **Score de Confiance $C \in [0, 1]$** : Chaque fait est doté d'un score basé sur le nombre de confirmations et la récence.
- **Supersession Explicite** : En cas de contradiction, l'ancienne version d'une règle est conservée avec marquage `stale` et liée à la nouvelle assertion via un `[[wikilink]]` horodaté.
- **Retention Decay** : Les observations isolées ou non renforcées voient leur priorité décroître exponentiellement selon la courbe d'Ebbinghaus.

---

## 3. Conséquences

### Positives
* **Interopérabilité Absolue** : Format Markdown/YAML agnostique consommable par n'importe quel agent (Claude Code, Gemini, Antigravity IDE).
* **Élimination du Context Rot** : Conservation de la structure globale des documents et élimination du bruit.
* **Auto-Assainissement** : Supersession explicite et rétention sélective empêchant la corruption du LLM-Wiki.

### Négatives / Risques
* Exige une discipline de rédaction YAML stricte contrôlée par le linter `swarm.py wikifix`.
