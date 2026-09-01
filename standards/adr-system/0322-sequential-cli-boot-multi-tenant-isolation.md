# ADR-0322 : Boot Séquentiel CLI & Isolation Multi-Tenant

**Statut** : Accepté  
**Date** : 17 août 2026  
**Auteurs** : Équipe mLoop & Co-Architecte  
**Domaine** : Architecture Système, Anti-Amnésie & Gouvernance Multi-Agents  

---

## 1. Contexte et Problématique

Lors de sessions d'ingénierie assistées par agents d'IA (notamment sous OpenCode avec des modèles rapides comme `gemini-3.1-flash-lite`), deux incidents critiques de désorientation ont été observés :

1. **Confusion Syntactique CLI vs MCP (Shell Chain Failure)** :  
   Dans les directives initiales, la Boot Sequence énumérait des commandes CLI (`python src/swarm.py resume`) aux côtés d'outils MCP (`loop_mem_search`, `graphify query`). L'agent a tenté de chaîner ces instructions en une ligne unique de commande terminal (`&& loop_mem_search`). Comme les outils MCP ne sont pas des exécutables PowerShell/Bash, le shell a planté immédiatement avec l'erreur `The term 'loop_mem_search' is not recognized`, interrompant la séquence avant les étapes de validation (`vibe-check`) et de focalisation (`focus`).

2. **Pollution Croisée et Désorientation Racine (Cross-Project Drift)** :  
   Suite à cet échec, l'agent a tenté un repli par recherche filesystem non-guidée (`Glob "*food*"` ou lecture de `backlog/sprint_backlog.md` à la racine de l'espace de travail `C:\Memory Loop\`). Il y a trouvé un vieux fichier `sprint_backlog.md` orphelin (vestige d'une démo contenant `REC-013-FE`), ce qui l'a conduit à faussement affirmer à l'utilisateur que le récit demandé (`US-16-FOOD`) n'existait pas dans le projet `Metro_OneTrust`.

3. **Le Dilemme d'Accès à la Racine (Cerveau Global vs Silos Projets)** :  
   Une interdiction brutale de tout accès à la racine empêcherait les agents de consulter le Gold Standard (`standards/blueprints/story_template.md`), les compétences portables (`.agents/skills/`) ou la mémoire d'état transversale (`memory/SESSION_MEMORY_HEALTH.md`). Il était donc impératif de formaliser la frontière exacte entre le **Cerveau Système (Racine)** et les **Espaces Clients (Multi-Tenant)**.

---

## 2. Décisions Architecturales

Nous actons les principes fondamentaux suivants pour garantir la robustesse absolue du framework mLoop :

### A. Séquence d'Amorçage CLI Pure (Boot Sequence Séquentielle)
La séquence obligatoire au tout premier tour de parole est strictement composée de **3 commandes CLI Python séquentielles**, à exécuter individuellement :
1. `python src/swarm.py resume --project <nom_projet>` (Anti-amnésie, restauration de contexte et diagnostic de santé).
2. `python src/swarm.py vibe-check --project <nom_projet>` (Guardrail d'intégrité pré-vol).
3. `python src/swarm.py focus --project <nom_projet> --story <ID_OU_CHEMIN>` (Localisation automatique et verrouillage du récit).

*(Les outils d'analyse sémantique MCP comme `loop_mem_search`, `graphify query` ou `codegraph_explore` sont mobilisés lors des phases d'analyse subséquentes via les ponts MCP natifs et ne doivent JAMAIS être invoqués dans un shell terminal).*

### B. Isolation Hermétique des Données Métier Client (Multi-Tenant Lock)
* **Confinement Projet** : Tout artefact propre à un projet client (User Stories, sprint backlog, matière première `reference/`, revues Sentinel, ADRs projet) réside **exclusivement sous `Projects/<nom_projet>/`**.
* **Interdiction de Backlog Racine** : Aucun répertoire `backlog/` de travail ne doit subsister à la racine `C:\Memory Loop\`.
* **Résolution Automatique via `swarm.py focus`** : Les agents ont l'interdiction d'exécuter des recherches de fichiers manuelles (`Glob`, `find`) pour repérer un récit : la commande `python src/swarm.py focus --project <nom_projet> --story <ID>` constitue le point d'entrée unique et déterministe de chargement.

### C. Préservation et Sanctuaire du Cerveau Système Racine
L'accès aux répertoires système globaux de la racine est formellement maintenu et protégé pour tous les agents :
- 📂 **`standards/`** : Source Unique de Vérité Normative (`story_template.md`, gabarits Gherkin, protocoles INVEST).
- 📂 **`.agents/skills/`** : Réservoir des 22+ compétences portables (Standard Agent Plugins 1.0).
- 📂 **`memory/`** : Mémoire vive globale, graphe sémantique transversal et anti-amnésie inter-projets.
- 📂 **`src/`** : Moteur d'orchestration CLI pour l'auto-évolution guidée par les tests (TDD).

---

## 3. Conséquences

### Positives
* **Zéro Risque de Crash Shell** : La Boot Sequence est 100 % exécutable sans ambiguïté par tous les modèles LLM (Claude 3.7, Gemini 2.5/3.1, GPT-4o, Codex).
* **Élimination Totale des Hallucinations Inter-Projets** : La suppression du backlog racine et le verrouillage multi-tenant empêchent toute confusion entre projets distincts.
* **Intégrité Normative Préservée** : Les agents ont toujours un accès direct aux gabarits maîtres `standards/` et aux compétences globales.
* **Auto-Résolution Robuste** : La CLI `focus` résout indifféremment par clé Jira (`MMA-4659`), par identifiant logique (`US-06-FOOD`) ou par chemin physique.

### Négatives / Mitigations
* **Discipline de nommage de projet** : La commande `resume` requiert le nom du projet, mitigée par le moteur de résolution tolérante aux fautes (*fuzzy matching*, ex: `"One Trust Metro"` ➔ `Metro_OneTrust`).

---

## 4. Références & Directives Liées

* [`AGENTS.md`](file:///c:/Memory%20Loop/AGENTS.md) : Section 1 (*Commands You Can Use*) et Section 4 (*Boundaries & Multi-Tenant Lock*).
* [`ADR-0309-agent-plugins-adoption.md`](file:///c:/Memory%20Loop/docs/01-architecture/ADR-0309-agent-plugins-adoption.md) : Standardisation des compétences et manifestes MCP.
* [`0204-dual-engine-graph-architecture-graphify-codegraph.md`](file:///c:/Memory%20Loop/docs/01-architecture/0204-dual-engine-graph-architecture-graphify-codegraph.md) : Moteur à double graphe sémantique et AST.
* [`standards/blueprints/story_template.md`](file:///c:/Memory%20Loop/standards/blueprints/story_template.md) : Gabarit Gold Standard partagé.
