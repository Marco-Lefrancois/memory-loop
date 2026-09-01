# ADR-0324 : Auto-Eval Harvesting, Context Guard & Supersession

**Statut** : Accepté  
**Date** : 18 août 2026  
**Auteurs** : Équipe mLoop & Co-Architecte Agentique  
**Domaine** : Évaluation Continue, Gestion de Contexte (Dumb Zone), Observabilité, Cycle de Vie Mémoriel (Statewave / SAGE)  

---

## 1. Contexte et Problématique

À la suite du benchmark de référence **Awesome Agents (Août 2026)**, trois vulnérabilités systémiques des architectures d'agents autonomes ont été identifiées :

1. **La Non-Régression Invisible (*Missing Failure-Driven Evals*)** :
   Les rejets contradictoires de l'agent Sentinel/Rubber Duck et les écarts INVEST/WikiFix sont généralement traités de manière éphémère sans être convertis en tests de régression pérennes.
2. **Le Décrochage Cognitif par Saturation de Contexte (*Dumb-Zone Amnesia*)** :
   Au-delà de 60 % de remplissage de la fenêtre de contexte maximale, les LLMs perdent leur capacité d'attention fine et inventent des règles inexistantes (*Compounding Errors*).
3. **L'Accumulation de Règles Obsolètes (*Stale Memory Pollution*)** :
   Au fur et à mesure que les décisions d'architecture (ADRs) évoluent, les anciennes règles contradictoires polluent la base de connaissances et les recherches sémantiques.

---

## 2. Décisions Architecturales

Nous actons l'intégration de trois moteurs complémentaires au cœur de **mLoop** :

### A. Moteur de Moisson Automatique d'Evals (`src/pipelines/eval_harvester.py`)
* **Conversion Déterministe des Rejets** : Toute anomalie bloquante (`[REJET]`, `[GUARDRAIL TECH]`) consignée dans les rapports d'audit Sentinel/WikiFix est automatiquement transformée en cas de test d'évaluation structuré (`EvalTestCase`).
* **Registre Permanent** : Sauvegarde synchrone sous `memory/evals/harvested_evals.json`.
* **Commande CLI** : `python src/swarm.py eval-harvest --project <nom>`.

### B. Moniteur de Contexte & Dumb-Zone Watcher (`src/utils/context_monitor.py`)
* **Segmentation en 3 Zones Cognitives** :
  - 🟢 **Smart Zone (0% - 40%)** : Raisonnement optimal et adhésion stricte aux règles.
  - 🟡 **Caution Zone (40% - 60%)** : Alerte de compactage recommandée.
  - 🔴 **Dumb Zone (> 60%)** : Alerte critique de saturation. L'orchestrateur doit obligatoirement scinder le travail vers un worker Herdr clean-slate ou effacer le contexte résiduel.
* **Jauge Visuelle CLI** : `python src/swarm.py context-watch --project <nom>`.

### C. Moteur de Supersession de Connaissances (`src/loop_mem/supersession.py`)
* **Détection des Clauses de Remplacement** : Analyse automatique des mentions `Remplace : ADR-XXXX` dans les documents d'architecture.
* **Registre de Supersession** : Maintien du fichier de traçabilité `memory/supersession_ledger.json`. Les connaissances obsolètes sont formellement isolées et exclues des prompts actifs.
* **Commande CLI** : `python src/swarm.py supersession-sync --project <nom>`.

---

## 3. Conséquences

### Positives
* **Immunité Évolutive** : Chaque bug ou anomalie intercepté renforce le filet de sécurité du framework sans effort manuel.
* **Prévention Active des Hallucinations** : Le seuil de 60 % protège l'agent contre l'effet d'amnésie et de saturation contextuelle.
* **Hygiène SSOT Parfaite** : Les règles caduques sont formellement repérées et ne rentrent plus en conflit avec les nouvelles décisions.

---

## 4. Références & Alignement

* **Benchmark de Référence** : `https://github.com/kyrolabs/awesome-agents` (Projets *Latitude*, *ctop*, *ClawMetry*, *Statewave*, *SAGE*)
* **ADR Associés** :
  - `ADR-0324` : Isolation Contextuelle Clean-Slate et Herdr Subagents
  - `ADR-0325` : Semantic Chunking et Extraction Documentaire Agentique
