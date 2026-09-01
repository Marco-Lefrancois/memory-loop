---
name: validate
description: Audit QA, vérification de l'isolation technique (WikiFix) et calcul du score INVEST. Utiliser après la rédaction de User Stories pour valider leur qualité avant la clôture de la session (Definition of Ready).
---

# 🛡️ validate (Phase QA)

> **Status:** Active | **Standard:** mLoop Core

## 🎯 Purpose
Vérifier que le Backlog généré (User Stories) est de très haute qualité et respecte la méthodologie INVEST avant la clôture de la session. C'est l'ultime barrière d'analyse métier (Definition of Ready).

## 🛠️ Workflow
1. **Semantic Linting (Dream Sequence)**: Lorsqu'invoqué pour un audit sémantique profond (ex: "Lance la Dream Sequence"), l'agent interroge le graphe pour détecter les **contradictions logiques** (ex: conflit entre deux ADRs), les **User Stories orphelines** (sans Epic) et les **lacunes métiers**. Un rapport d'anomalies est généré.
2. **Compliance & Technical Leakage (WikiFix)**: L'agent **DOIT déléguer l'audit** au Moteur. Invoquez `python src/swarm.py wikifix --project <nom_du_projet>`. Ce pipeline vérifie que le backlog est pur et qu'il n'y a aucune fuite technique (Zéro Mention de Librairie).
3. **INVEST Score Calculation**: Valider chaque nouvelle Story selon la grille INVEST.
4. **Revue Contradictoire Sentinel (Avocat du Diable)** : Exécuter `python src/swarm.py rubber-duck --project <nom_projet> --file <story_file>` pour déclencher l'orchestration DAG du débat contradictoire Red Team (Sentinel) vs Blue Team (Plan). L'agent Sentinel compare le récit à la galerie des `standards/gold_standards/` et challenge les cas aux limites.

5. **Self-Validation (RHO)**: S'il manque chroniquement l'un de ces critères ou face à des anomalies sémantiques récurrentes, ajoutez une règle d'optimisation via `python src/swarm.py optimize --project <nom_du_projet> --keyword "<erreur/motif>" --msg "<directive>" --scope <project|global>`.

## 📊 Output
- `memory/wikifix_report.md` : Rapport d'audit de conformité.
- **INVEST-Score** : Score numérique final (ex: 6/6) injecté dans l'en-tête de la Story. Si le score est faible, la Story doit être retravaillée.
