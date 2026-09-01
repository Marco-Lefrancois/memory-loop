---
name: analyze
description: Ingestion documentaire et modélisation du graphe de connaissances (Graphify). Utiliser pour amorcer un projet, analyser des sources de référence ou reconstruire le graphe sémantique d'un domaine.
---

# 📥 analyze (Phase A)

> **Status:** Active | **Standard:** mLoop Core

## 🎯 Purpose
Cette compétence assure l'ingestion et l'indexation de toutes les sources brutes (directives, références, code) pour alimenter le Graphe de Connaissances (SSOT). Elle est le préalable obligatoire à toute prise de décision.

## 🧱 Core Principles
1. **Lexical Strictness (Zero-Drift)** : Lors de l'extraction documentaire et de la génération du Graphe, ne JAMAIS paraphraser les concepts d'affaires. Utiliser les entités exactes des directives.
2. **Self-Improving Queries** : Lorsqu'une requête utilisateur nécessite d'analyser et de croiser plusieurs sources pour produire une synthèse inédite, proposer à l'utilisateur : *"Souhaitez-vous que je pérennise cette analyse dans le wiki ?"*. Si validé, générer un fichier Markdown de synthèse (ex: `docs/wiki/synthese_concept.md`), y inclure les références appropriées, puis exécuter `python src/swarm.py sync`.

## 🛠️ Workflow
1. **Source Sync & Ingestion MarkItDown**: Exécuter `python src/swarm.py ingest --project <nom_projet>` pour convertir les fichiers de `reference/` (PDF, Word, Excel, PowerPoint, images) en Markdown autonome sous `docs/00-ingested/` et extraire/placer les actifs visuels et maquettes vectorielles sous `docs/05-assets/maquettes/` (ADR-0332).
2. **Consultation Documentaire via MarkItDown**: Les agents ont l'interdiction de deviner ou de lire à l'aveugle les fichiers binaires bruts sous `reference/`. L'agent DOIT lire les fichiers Markdown normalisés générés sous `docs/00-ingested/` et référencer les actifs visuels sous `docs/05-assets/`.
3. **Docs Structuration (SSOT)**: Vérifier l'existence du dossier `docs/` et s'assurer qu'il respecte l'arborescence SSOT (`00-ingested/`, `01-architecture/`, `02-business-rules/`, `03-models/`, `04-transverse/`, `05-assets/`, `index.md`).
4. **Knowledge Extraction & Scraping**:
   - **Graphify**: Construction du graphe sémantique (respectant strictement le Lexical Strictness).
   - **God Nodes Extraction**: AVANT toute interaction avec l'humain, vous devez extraire les "God Nodes" (les concepts centraux ultra-connectés) et les communautés sémantiques identifiées par Graphify. Présentez cette "carte mentale" à l'humain pour pré-valider votre compréhension globale.
   - **MCP Crawler**: Moissonnage de la documentation technique externe. L'agent **DOIT** utiliser le serveur MCP local `src/bridges/mcp_crawler.py` (qui délègue au moteur Node.js `mloop-crawler`) pour lire, extraire et indexer les pages ou documentations en ligne.
   - **Multi-Agent Debate (Résolution de Conflits de Sources)**: Lors de l'ingestion, si deux documents de référence se contredisent factuellement, l'agent **DOIT** exécuter `python src/bridges/agentic_debate.py --project <nom_projet> --query "<contexte du conflit>" --context-file <chemin>`. L'Orchestrateur lit le `debate_transcript.md` et tranche sur la version à retenir pour le graphe de connaissances. L'utilisation du débat est interdite en phase d'analyse en dehors de ce cas strict.
5. **Audit (WikiFix)**: Identification et rapport des inconsistances dans la base de connaissances.
6. **Contract Gen**: Génération initiale des types TypeScript à partir des schémas API analysés.

## 📊 Output
- `graphify-out/` : Graphe et rapports FTS5.
- `memory/wikifix_report.md` : Audit de cohérence.
- `memory/debate_transcript.md` : Log des débats en cas de conflit de sources.
- `src/models.ts` : Typages de contrats.

