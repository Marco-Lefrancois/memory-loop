# Mapping Architecturel des 5 Piliers mLoop (v2.0.0)

Ce document référence l'implémentation physique (Outils / Fichiers) et théorique (Concepts / Méthodes) qui correspond à chacun des 5 piliers fondateurs du framework **Memory Loop (mLoop v2.0.0)**.

---

## 1. 🧠 Memory (Mémoire et Contexte)
**Objectif :** Vaincre l'amnésie des agents et assurer la continuité architecturale du projet à long terme.

* **Outils / Fichiers physiques :** 
  * `Projects/<nom_projet>/memory/knowledge_graph.json` et `graphify-out/graph.json` : Le graphe sémantique persistant servant de SSOT.
  * Moteur RAG *L3 In-Memory* et parser AST (`graphify update .`).
  * Pont MCP `mcp_loop_mem.py` et commandes `graphify query`, `graphify explain`, `graphify path`.
* **Concepts / Méthodes :** 
  * **Search-First Protocol** : Règle absolue interdisant à l'agent de proposer du code sans avoir interrogé le graphe d'abord.
  * **RAM Cache Engram Preloading** : Chargement 1-hop en mémoire vive pour des réponses à latence quasi-nulle.

---

## 2. 🛠️ Skills (Compétences Portables & AP 1.0)
**Objectif :** Fournir des capacités d'action physiques au modèle sans surcharger son contexte global.

* **Outils / Fichiers physiques :** 
  * Le sous-système `.agents/skills/` (21+ compétences documentées avec `SKILL.md`).
  * Fichiers de manifeste **Agent Plugins 1.0** : `.agents/plugin.json` et `.agents/mcp.json`.
  * Commandes `python src/swarm.py plugin-validate` et `plugin-export`.
* **Concepts / Méthodes :** 
  * **Divulgation Progressive (Progressive Disclosure)** : Chargement de `SKILL.md` à la demande via `view_file`.
  * **Multi-IDE Portability (ADR-0309)** : Distribution autonome vers Cursor, VS Code, Copilot, Codex, Kiro, Antigravity.
  * **Moteur Calibrate Engine** : Auto-étalonnage continu (`python src/swarm.py calibrate`).

---

## 3. 👻 Soul (Identité et Garde-fous)
**Objectif :** Aligner le comportement cognitif de l'agent sur la culture d'ingénierie et prévenir les dérives (Scope Creep).

* **Outils / Fichiers physiques :** 
  * `.agents/soul.json` : Personnalité Senior Tech Lead, style Zero-Fluff.
  * Directives `tech.md`, `business.md` et `AGENTS.md`.
* **Concepts / Méthodes :** 
  * **Directives-Driven Framework** : Alignement strict sur les lois du projet.
  * **Negative Prompting / Exclusions** : Liste explicite des fonctionnalités interdites pour bloquer l'hallucination.
  * **Zero-Fluff Standard** : Haute densité informationnelle sans fioritures.

---

## 4. 🔄 Session Recall (Reprise, Checkpointing & Temporalité)
**Objectif :** Permettre le travail asynchrone sur le temps long et gérer les interruptions de session (Human-In-The-Loop).

* **Outils / Fichiers physiques :** 
  * Nœud d'état global `ML_ACTIVE_STATE` et checkpoints `.mloop_tmp/checkpoints/`.
  * `backlog/sprint_backlog.md` et `backlog/stories/`.
* **Concepts / Méthodes :** 
  * **Focus Lock** : Verrouillage d'attention via `python src/swarm.py focus --project <p> --story <s>`.
  * **Stop & Ask (HITL Strict)** : En cas d'ambiguïté fonctionnelle majeure, l'agent consigne une Question Ouverte (`Q-`) et s'arrête.
  * **Idempotent Resume** : Reprise exacte de l'exécution au nœud interrompu via `graph-run --resume`.

---

## 5. 🛡️ Validation (Audit EvidencePack & Conformité QA)
**Objectif :** Validation déterministe s'assurant que l'analyse et les livrables respectent le contrat (SCC) et la qualité.

* **Outils / Fichiers physiques :** 
  * `Wikifix` (`python src/swarm.py wikifix`) : Linter sémantique actif et mécanique.
  * `EvidencePackEngine` : Génération synchrone des artefacts JSON d'audit sous `memory/evidence/<STORY_ID>_evidence.json`.
  * Suite `aoep` (Always-On Evaluation Protocol) et l'audit des **4 Piliers Gherkin**.
* **Concepts / Méthodes :** 
  * **Zero-Ask Evidence Enforcement** : Génération synchrone obligatoire de l'EvidencePack sans demander confirmation.
  * **Gouvernance Jira (Story-Only)** : Synchronisation exclusive en tickets de type Story (`jira_sync`).
  * **INVEST Score** : Validation formelle du score INVEST avant bascule du statut de la story.
