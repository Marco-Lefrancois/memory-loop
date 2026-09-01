# 📋 Blueprint : Project AGENTS.md, opencode.json & .gitignore Template

Ce gabarit officiel définit la structure standard d'un projet mLoop autonome, comportant un unique `README.md` racine, un `AGENTS.md` dédié, un `opencode.json` contextuel et un `.gitignore` protégeant le dépôt des matières premières lourdes.

---

## 1. Structure Racine Obligatoire d'un Projet mLoop (Dépôt Git)

```
Projects/<ProjectName>/
├── 📄 README.md                # SSOT Humain : Présentation générale, contexte, équipe, livrables
├── 📄 AGENTS.md                # SSOT IA : Boot sequence, règles métier, guardrails et séparation des 3 piliers
├── 📄 opencode.json            # Configuration IDE OpenCode : MCP servers, watcher ignores, CLI shortcuts
├── 📄 .gitignore               # Protection Git : Exclusion de reference/, .codegraph/, caches
├── 📂 backlog/                 # Stories au gabarit story_template.md + sprint_backlog.md
├── 📂 docs/                    # Architecture SSOT, ADRs, règles métier, assets graphiques versionnés (docs/05-assets/)
└── 📂 memory/                  # EvidencePacks JSON, bilans de santé de session
```

> [!IMPORTANT]
> **Règle Git & SSOT pour `reference/` vs `docs/05-assets/` (ADR-0332)** :
> Le dossier `reference/` est un **espace de staging local réservé à la machine de l'architecte** (matière première, documentations et scans bruts). Il est **strictement ignoré par Git** afin de prévenir l'alourdissement du dépôt (*Repo Bloat*) et les fuites de données brutes. Seuls les documents normalisés en Markdown dans `docs/00-ingested/` et les actifs visuels optimisés (maquettes SVG, diagrammes) sous `docs/05-assets/` sont versionnés dans le dépôt distant.

> [!NOTE]
> Aucun sous-répertoire (`backlog/`, `docs/`, `memory/`, `reference/`) ne doit contenir de fichier `README.md` intermédiaire.

---

## 2. Modèle de Fichier `.gitignore` par Projet

```gitignore
# Python Bytecode & Cache
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/

# Graphify & CodeGraph Local AST Caches
graphify-out/
.codegraph/
**/.codegraph/

# Memory Machine Caches & Traces (Recalculable localement)
memory/cache/
memory/tmp/
memory/execution_traces.json
memory/ingest_cache.json

# Matière Première Brute & Espace Local (Non synchronisé dans le dépôt)
reference/

# OS Metadata
.DS_Store
Thumbs.db
desktop.ini

# Temporary Office Lock files
~$*.xlsx
*.tmp
```

---

## 3. Modèle de Fichier `AGENTS.md` par Projet

```markdown
# 🛡️ Guide Agentique Spécifique — {{PROJECT_NAME}} (mLoop Project Engine)

Ce document constitue la **Source de Vérité Agentique (AGENTS.md)** pour le projet **{{PROJECT_NAME}}**. Tout agent IA (Cursor, Antigravity, OpenCode, Codex, Copilot, Kiro) opérant dans ce projet doit appliquer scrupuleusement ces directives.

---

## 1. Séquence d'Amorçage & Outils CLI

**Boot Sequence Obligatoire au Premier Tour** :
1. `python src/swarm.py resume --project {{PROJECT_NAME}}` (Anti-amnésie & historique de session)
2. `loop_mem_search` (Fact-Search documentaire)
3. `graphify query` (Navigation dans le graphe sémantique)
4. `python src/swarm.py vibe-check --project {{PROJECT_NAME}}` (Guardrails pré-vol)
5. `python src/swarm.py focus --project {{PROJECT_NAME}} --story <chemin>` (Verrouillage de contexte)

---

## 2. Règles Métier Spécifiques du Projet

{{PROJECT_BUSINESS_RULES}}

---

## 3. Séparation Stricte des 3 Piliers (Architecture mLoop)

- 📂 **`reference/` (Matière Première & Staging Local)** : Documents clients, scans, code source de référence. **Espace local ignoré par Git**. Interdiction de modification directe.
- 📂 **`docs/` (SSOT Architecturale & Métier)** : Règles métier, décisions d'architecture (`01-architecture/`), documents ingérés (`00-ingested/`) et actifs visuels versionnés (`docs/05-assets/maquettes/`, `docs/05-assets/diagrams/` - ADR-0332).
- 📂 **`backlog/` (Terrain d'Exécution)** : User Stories sous `backlog/stories/` au gabarit Gold Standard (`story_template.md`).
- 📂 **`memory/` (Traçabilité & Audit)** : EvidencePacks obligatoires sous `memory/evidence/<STORY_ID>_evidence.json`.

---

## 4. Limites Comportementales & Handoff Développeur

- ✅ **Toujours Faire** :
  - Respecter scrupuleusement le gabarit unique `standards/blueprints/story_template.md` avec les **4 Piliers Gherkin**.
  - Générer systématiquement l'EvidencePack JSON synchronisé pour chaque récit.
  - Valider chaque récit avec `python src/swarm.py rubber-duck --project {{PROJECT_NAME}} --file <story_path>` et `python src/swarm.py wikifix`.
- 🚫 **Ne Jamais Faire (Pureté Fonctionnelle & Zéro Code Physique)** :
  - **Zéro Snippet ni Noms de Code Physique dans les Récits** : Ne jamais insérer de code source, de pseudo-code syntaxique ou de noms de classes/méthodes physiques internes dans le corps des récits. Décrire les parcours, interfaces et règles exclusivement en français fonctionnel clair afin que les spécifications soient immédiatement exploitables par l'équipe de développement et ses agents d'implémentation.
  - **Doc-First Obligatoire** : Pointer vers la documentation officielle ingérée (`docs/00-ingested/...`) plutôt que de suggérer du code d'intégration.
  - **Zéro Auto-Approbation sans Grilling** : Toujours mener l'interview 1 question par tour avec le PO.
```

---

## 4. Modèle de Fichier `opencode.json` par Projet

```json
{
  "$schema": "https://opencode.ai/schema.json",
  "project": "{{PROJECT_NAME}}",
  "version": "1.0.0",
  "instructions": [
    "AGENTS.md"
  ],
  "mcp": {
    "loop_mem": {
      "type": "local",
      "command": [
        "python",
        "-m",
        "src.mcp_server"
      ]
    },
    "graphify": {
      "type": "local",
      "command": [
        "python",
        "-m",
        "graphify.server"
      ]
    },
    "codegraph": {
      "type": "local",
      "command": [
        "codegraph",
        "serve",
        "--mcp"
      ]
    }
  },
  "watcher": {
    "ignore": [
      ".codegraph/**",
      "memory/cache/**",
      "memory/events.jsonl"
    ]
  },
  "commands": {
    "loop-explore": {
      "command": "python src/swarm.py code-explore --project {{PROJECT_NAME}} --query \"$QUERY\"",
      "description": "Explorer le graphe AST physique de code (CodeGraph)"
    },
    "loop-impact": {
      "command": "python src/swarm.py code-impact --project {{PROJECT_NAME}} --symbol \"$SYMBOL\"",
      "description": "Calculer le rayon d'impact d'un symbole"
    },
    "loop-grill": {
      "command": "python src/swarm.py grill --project {{PROJECT_NAME}} --story \"$STORY\"",
      "description": "Lancer une session d'arbitrage interactif Grill-with-Docs"
    },
    "loop-rubber-duck": {
      "command": "python src/swarm.py rubber-duck --project {{PROJECT_NAME}} --file \"$FILE\"",
      "description": "Exécuter l'audit contradictoire Sentinel (Rubber Duck)"
    },
    "loop-sync": {
      "command": "python src/swarm.py sync --project {{PROJECT_NAME}}",
      "description": "Synchroniser la mémoire et le graphe de connaissances"
    }
  }
}
```
