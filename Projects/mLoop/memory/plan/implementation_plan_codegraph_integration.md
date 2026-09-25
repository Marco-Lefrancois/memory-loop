# 📐 Plan d'Implémentation : Intégration de la Dual-Engine Graph Architecture (Graphify + CodeGraph) dans mLoop

Ce plan détaille la mise en œuvre de l'architecture à **Double Moteur de Graphes (Dual-Engine Graph Architecture)** pour mLoop :
- **Graphify** : Moteur de graphe sémantique pour la documentation, l'architecture SSOT, les règles d'affaires (`RM-XXX`) et les User Stories.
- **CodeGraph** : Moteur AST déterministe (Rust + SQLite FTS5) pour l'indexation chirurgicale du code source physique, la résolution des routes de frameworks, les ponts cross-langages (React Native, Swift/ObjC) et le calcul du rayon d'impact (*blast radius*).

---

## User Review Required

> [!IMPORTANT]
> **Étanchéité Code vs Architecture (Directive Lead Dev Renaud)** :
> L'utilisation de CodeGraph par l'agent Plan (Phase 2) est strictement dédiée à l'investigation et à la découverte chirurgicale des points d'intégration réels. Les User Stories produites doivent rester purement déclaratives (**zéro snippet de code physique**, **zéro pseudo-code**).

> [!TIP]
> **Disponibilité MCP & CLI** :
> CodeGraph sera configuré comme serveur MCP local (`codegraph serve --mcp`) dans `.agents/mcp.json` et `opencode.json`, tout en exposant des commandes dédiées via la CLI Swarm (`python src/swarm.py code-explore`, `code-impact`, `code-affected`).

---

## Open Questions

> [!NOTE]
> 1. **Auto-démarrage du File Watcher** : Souhaitez-vous que l'indexation `.codegraph/` soit déclenchée automatiquement lors de `python src/swarm.py init` sur un projet contenant du code source ? *(Recommandé : Oui)*
> 2. **Exclusion Git** : Confirmez-vous que le répertoire `.codegraph/` doit être ajouté systématiquement au `.gitignore` racine de mLoop et des sous-projets ? *(Recommandé : Oui)*

---

## Proposed Changes

### 1. Architecture SSOT & Décision d'Architecture (ADR)

#### [NEW] [0204-dual-engine-graph-architecture-graphify-codegraph.md](file:///c:/Memory%20Loop/docs/01-architecture/0204-dual-engine-graph-architecture-graphify-codegraph.md)
- Formalisation de la décision d'architecture : séparation nette entre le graphe documentaire conceptuel (`graphify-out/`) et le graphe AST physique (`.codegraph/`).
- Définition des règles d'arbitrage par phase du cycle de vie mLoop (Phases 1 à 5).

---

### 2. Configuration MCP & Plugins Multi-Agents

#### [MODIFY] [.agents/mcp.json](file:///c:/Memory%20Loop/.agents/mcp.json)
- Ajout du serveur MCP `codegraph` :
  ```json
  "codegraph": {
    "type": "stdio",
    "command": "codegraph",
    "args": ["serve", "--mcp"]
  }
  ```

#### [MODIFY] [opencode.json](file:///c:/Memory%20Loop/opencode.json)
- Enregistrement du serveur MCP `codegraph` sous la clé `"mcp"`.
- Ajout des commandes rapides mLoop (`loop-code-explore`, `loop-code-impact`, `loop-code-affected`) dans la section `"command"`.
- Ajout de `.codegraph/**` dans les règles du watcher (`watcher.ignore`).

---

### 3. Backbone CLI mLoop (`src/`)

#### [NEW] [code_intelligence.py](file:///c:/Memory%20Loop/src/commands/handlers/code_intelligence.py)
- Handlers CLI dédiés :
  - `handle_code_explore(args, state, project_path)` : Interface vers `codegraph explore`.
  - `handle_code_impact(args, state, project_path)` : Interface vers `codegraph impact`.
  - `handle_code_affected(args, state, project_path)` : Interface vers `codegraph affected` (pipeline CI / tests).
  - `handle_code_init(args, state, project_path)` : Initialisation de l'index local `.codegraph/`.

#### [MODIFY] [_registry.py](file:///c:/Memory%20Loop/src/commands/_registry.py)
- Déclaration des nouvelles commandes CLI dans le registre canonique mLoop :
  - `code-explore`
  - `code-impact`
  - `code-affected`
  - `code-init`

---

### 4. Directives Système & Compétences Agentiques (Skills)

#### [MODIFY] [AGENTS.md](file:///c:/Memory%20Loop/AGENTS.md)
- Mise à jour de la **Matrice d'Outillage par Phase** :
  - Phase 2 (PLAN / ARCHI) : Ajout de `codegraph_explore` pour la découverte chirurgicale sans lecture brute de fichiers.
  - Phase 3 (BUILD / DEV) : Ajout de `codegraph impact` pour l'auto-développement mLoop (`src/`).
  - Phase 4 (VALIDATE / QA) : Ajout de `codegraph affected` pour la sélection des tests ciblés.

#### [MODIFY] [.agents/skills/plan/SKILL.md](file:///c:/Memory%20Loop/.agents/skills/plan/SKILL.md)
- Intégration de la consigne d'utilisation de `codegraph_explore` lors de l'investigation des points d'intégration pour éliminer la lecture manuelle de fichiers sources.

#### [MODIFY] [.agents/skills/blindspot-scan/SKILL.md](file:///c:/Memory%20Loop/.agents/skills/blindspot-scan/SKILL.md)
- Intégration de `codegraph impact` pour l'audit automatique des dépendances diamant, des points de rupture cross-langages (React Native / iOS) et du blast radius.

---

### 5. Documentation & Archivage Mémoire (ADR-0307)

#### [NEW] [implementation_plan_codegraph_integration.md](file:///c:/Memory%20Loop/Projects/mLoop/memory/plan/implementation_plan_codegraph_integration.md)
- Sauvegarde persistante du plan d'implémentation sous le répertoire projet mLoop.

---

## Verification Plan

### Automated Tests
- **Test unitaire du handler CLI CodeGraph** :
  ```powershell
  pytest tests/test_code_intelligence.py -v
  ```
- **Validation de la conformité Agent Plugins 1.0** :
  ```powershell
  python src/swarm.py plugin-validate --project mLoop
  ```
- **Auto-étalonnage du système** :
  ```powershell
  python src/swarm.py calibrate --project mLoop
  ```

### Manual Verification
- Exécution de `codegraph status` et vérification de la création de `.codegraph/` lors de `python src/swarm.py code-init --project mLoop`.
- Test d'interrogation chirurgicale : `python src/swarm.py code-explore --project mLoop --query "LoopState"` et validation de la réponse verbatim sans lecture de fichier brut.
