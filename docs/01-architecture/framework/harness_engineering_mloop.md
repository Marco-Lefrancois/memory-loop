Ce document théorise le **Harness Engineering (L'Ingénierie de Harnais)** et cartographie son implémentation physique dans l'écosystème **mLoop (Memory Loop Autonomous Engine v2.0.0)**.

---

### 1. Analyse Structurelle : Le Triptyque du Harnais

1. **Partie 1 (Stratégique & Économique)** : Le levier de performance passe du *Model Scaling* au *System Scaling*. Le ROI de l'IA ne réside pas dans le prompt engineering éphémère mais dans la gouvernance et le contrôle déterministe.
2. **Partie 2 (Pédagogique)** : Analogie Moteur/Harnais (Moteur = LLM, Harnais = Véhicule, Outils, Freins et Contrôles).
3. **Partie 3 (Architecturale)** : Séparation stricte entre l'exécution cognitive (Système 2 - IDE Agentique) et la gouvernance déterministe (Système 1 - Kernel `swarm.py`).

---

### 2. Les Pathologies de l'IA Agentique & Traitements mLoop

1. **La pourriture du contexte (Context Rot)** :
   * *Solution mLoop* : Compactage sémantique, requêtes RAG chirurgicales via `mcp_loop_mem.py` (`graphify query`) et fin de session propre avec le skill `handoff`.
2. **La mémoire obsolète (Stale but Confident)** :
   * *Solution mLoop* : **Ground Truth Verification** forcée via `python src/swarm.py sync` (mise à jour AST et du graphe sémantique) et Séquence d'Amorçage obligatoire.
3. **La dérive d'objectif (Goal Drift & Scope Creep)** :
   * *Solution mLoop* : **Verrou d'attention** via `python src/swarm.py focus` et **Story Guard actif (`story_guard.py`)** qui bloque physiquement toute modification de fichier hors-périmètre du SCC.

---

### 3. Matrice de Résonance : Théorie du Harnais vs Pratique mLoop v2.0.0

| Concept Théorique du Harnais | Implémentation Physique dans mLoop v2.0.0 |
| :--- | :--- |
| **Harness Engineering** (Découplage Cerveau / Moteur) | Architecture à deux couches : L'IDE (Système 2) comme Cerveau d'Analyse, et `src/swarm.py` (Système 1) comme Moteur de Validation déterministe. |
| **Vérification de la Vérité Terrain** (Ground Truth) | Séquence d'Amorçage Obligatoire (5 étapes CLI au 1er tour de parole) et auto-synchronisation (`python src/swarm.py sync`). |
| **Lutte contre la Mémoire Obsolète** | Indexation AST + Graphe de Connaissances L3 In-Memory et requêtes sémantiques 1-hop via `mcp_loop_mem.py`. |
| **Garde-Fou d'Écriture Physique (Story Guard)** | Script `story_guard.py` branché sur les contrats SCC (Story Constraint Contracts) bloquant toute écriture hors-périmètre. |
| **Génération de Preuves (Evidence Enforcement)** | Engine `EvidencePackEngine` générant les artefacts JSON `memory/evidence/<STORY_ID>_evidence.json` avec traçabilité et alerte (`[!NOTE]`, `[!WARNING]`). |
| **Topologie DAG & Stress-Test (Pattern Diamant)** | Topologie DAG Multi-Agents (`python src/swarm.py graph-run`) avec Scoper, Reducer Node (Pure Python) et Risk Router (Fast Track / Deep Review). |
| **Auto-Étalonnage & RHO** | Commandes `python src/swarm.py optimize` (RHO rules YAML) et `python src/swarm.py calibrate` (Auto-Repair 8/8 PASS). |
| **Portabilité Multi-Clients (AP 1.0)** | Empaquetage standard **Agent Plugins 1.0** (ADR-0309: `.agents/plugin.json`, `.agents/mcp.json`, 21+ skills) avec `plugin-export`. |

---

### 4. Bilan d'Audit & Conformité du Harnais mLoop

L'architecture mLoop a franchi tous les niveaux d'exigence d'un harnais industriel :
- **Séparation Exécution / Gouvernance** : Totalement scellée (System 1 Kernel vs System 2 IDE Agentic Swarm).
- **Garde-Fous Actifs** : `story_guard.py` protège le périmètre applicatif client contre les écritures non planifiées.
- **Auto-Réparation & Audit** : Le duo `wikifix` + `calibrate` garantit un score d'intégrité 100% et un auto-étalonnage sans régression.
- **Portabilité Multi-IDE** : Conforme AP 1.0 pour déploiement multi-environnements.
