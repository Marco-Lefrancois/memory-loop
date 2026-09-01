# ADR-0204 : Architecture à Double Moteur de Graphes (Graphify + CodeGraph)

* **Statut** : ACCEPTÉ
* **Date** : 17 août 2026
* **Décideurs** : Équipe Architecture mLoop, Agent Orchestrateur, Lead Dev & Product Owner

---

## 🚀 1. Contexte & Problématique

Dans l'ingénierie agentique moderne de **mLoop**, deux univers distincts d'informations coexistent au sein d'un projet :
1. **La Couche Conceptuelle & Métier (La Connaissance / SSOT)** : Les règles d'affaires (`RM-XXX`), les décisions d'architecture (`ADR-XXX`), la hiérarchie des User Stories (`REC-XXX`), la taxonomie et les spécifications Gherkin 4 Piliers (stockées en Markdown dans `docs/`, `backlog/`, `standards/`).
2. **La Couche Physique d'Exécution (Le Code Source)** : Les classes concrètes, méthodes, signatures d'APIs, ponts natifs (Swift ↔ ObjC, React Native TurboModules/Fabric), et structures de routage de frameworks (ASP.NET, Django, FastAPI, Express, NestJS) stockées dans les dépôts applicatifs ou le moteur mLoop lui-même (`src/`).

### Le Piège du "Grep-Glob-Read Loop"
Jusqu'alors, lorsqu'un agent architecte (Phase 2 PLAN) ou sentinelle (Phase 4 VALIDATE) devait vérifier un point d'intégration sur du code source existant, il tombait dans le travers classique des agents IA : des boucles itératives de recherche textuelle (`grep`), de listing de répertoires (`ls`), et de lectures manuelles lourdes (`view_file`/`read`). Ce processus provoquait :
- Une explosion de la consommation de jetons (**180k à 990k tokens** par question d'architecture).
- Une multiplication d'appels d'outils redondants (jusqu'à 43 tool calls).
- Un risque de dérive et d'amnésie par pollution du contexte.

---

## 💡 2. Décisions d'Architecture

### A. Adoption de la Dual-Engine Graph Architecture (Double Moteur)
mLoop consacre officiellement une **séparation stricte à deux moteurs de graphes complémentaires** :

```
                   ┌────────────────────────────────────────────────────────┐
                   │                     mLoop Core                         │
                   └───────────┬────────────────────────────────┬───────────┘
                               │                                │
                 [Graphify]    │                                │    [CodeGraph]
            Documentation / SSOT                                │ Code Physique / AST
                               ▼                                ▼
┌──────────────────────────────────────────────┐ ┌──────────────────────────────────────────────┐
│  • Règles Métier (RM-XXX)                    │ │  • Définition exacte des symboles & types    │
│  • Décisions Architecturales (ADR-XXX)       │ │  • Résolution des routes d'API/Frameworks     │
│  • Spécifications & User Stories (Gherkin)   │ │  • Ponts natifs (Swift ↔ ObjC, React Native) │
│  • Navigation holistique du domaine          │ │  • Calcul de rayon d'impact (Blast Radius)   │
└──────────────────────────────────────────────┘ └──────────────────────────────────────────────┘
```

1. **Moteur Conceptuel Documentaire (`Graphify`)** :
   - **Périmètre** : `docs/`, `backlog/`, `standards/`, `memory/`, `reference/`.
   - **Nature** : Extraction de concepts, graphe sémantique, détection de communautés (Leiden/Louvain), *God Nodes*, résumés de domaine et wiki markdown (`graphify-out/`).
   - **Interrogation** : Commandes `graphify query`, `graphify explain`, `graphify path`.

2. **Moteur Physique de Code Source (`CodeGraph`)** :
   - **Périmètre** : Fichiers source physiques du projet (`.ts`, `.py`, `.cs`, `.swift`, `.kt`, `.rs`, `.go`, etc.).
   - **Nature** : Déterministe AST compilé en Rust via grammaires *tree-sitter*, base de données SQLite locale (`.codegraph/codegraph.db`) avec recherche plein-texte **FTS5**, dispatch dynamique et liens heuristiques cross-langages.
   - **Interrogation** : Outil MCP unifié `codegraph_explore` et commandes CLI mLoop `python src/swarm.py code-explore`, `code-impact`, `code-affected`.
   - **Mise à jour** : File Watcher OS natif (FSEvents/inotify/ReadDirectoryChangesW) avec synchronisation incrémentale en arrière-plan (debounce 2s).

---

### B. Matrice d'Outillage par Phase du Cycle de Vie mLoop

| Phase Cycle | Rôle Agent | Outil Documentaire / SSOT | Outil Code Source Physique |
| :--- | :--- | :--- | :--- |
| **1: SPEC / INGEST** | `orchestrator` / `plan` | `loop_mem_search`, `markitdown_convert` | `codegraph init` (déclenchement de l'indexation physique) |
| **2: PLAN / ARCHI** | `plan` | `graphify query`, `loop_mem_search`, `grill` | `codegraph_explore` (vérification chirurgicale sans lecture brute) |
| **3: BUILD / DEV** | `build` / `orchestrator` | `loop_mem_preload_context`, `standards/` | `codegraph impact`, `codegraph_explore` (auto-dev `src/`) |
| **4: VALIDATE / QA**| `sentinel` / `validate` | `wikifix`, `rubber-duck`, `aoep` | `codegraph affected` (ciblage chirurgical des tests unitaires) |
| **5: SHIP / SYNC** | `orchestrator` | `graphify update .`, `swarm sync` | Auto-sync continu (SQLite WAL) |

---

### C. Respect Absolu de la Frontière Code vs Architecture (Directive Lead Dev)
- **Utilisation en lecture seule et à des fins d'investigation** : L'agent Plan utilise CodeGraph pour connaître les interfaces, contrats et points d'ancrage réels.
- **Zéro Snippet dans les Stories** : Les User Stories mLoop restent strictement déclaratives et agnostiques. Il est formellement interdit d'y insérer du code source ou du pseudo-code copié depuis CodeGraph.

---

## 📈 3. Conséquences & 6 Piliers d'Impact mLoop

| Pilier d'Impact | Effet & Gain Mesuré |
| :--- | :--- |
| **1. Token & API Cost** | **-62 % de jetons consommés** et **-44 % sur la facture d'API** grâce à l'élimination des boucles grep/read. |
| **2. Zéro-Lecture Brute** | **0 lecture de fichier sur disque** pendant la phase d'exploration architecturale. |
| **3. Latence & Vélocité** | Réponses d'exploration de **2.2× à 3.6× plus rapides** (un seul appel `codegraph_explore` consolidé). |
| **4. Isolation Technique** | Séparation hermétique entre la mémoire documentaire (`graphify-out/`) et l'index de code (`.codegraph/` exclu du Git). |
| **5. Cross-Language Intelligence** | Support natif des ponts React Native (JS ↔ ObjC/Java), Swift ↔ ObjC et Expo Modules dans les audits d'architecture mobile. |
| **6. CI & Test Targeting** | Capacité d'exécuter uniquement les tests impactés via `codegraph affected` dans les cycles de validation sentinelle. |
