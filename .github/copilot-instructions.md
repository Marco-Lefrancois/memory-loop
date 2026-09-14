# 🌀 Instructions Copilot Dépôt — Memory Loop (mLoop)

Bienvenue dans le dépôt **Memory Loop (mLoop)** (`https://github.com/Marco-Lefrancois/memory-loop.git`).
Ce document fournit le contexte souverain, les conventions d'architecture et les règles de validation requises pour tout agent GitHub Copilot (Cloud Agent, Copilot CLI, VS Code Agent Mode).

---

## 🧭 1. Vue d'Ensemble & Architecture

mLoop est un moteur multi-agents cognitif pur basé sur un **State-Graph** et une architecture **Kernel-Pipeline**. Il structure le développement logiciel piloté par les spécifications à travers 6 phases souveraines :

1. **Phase 0 — Inception & SOW** : T-Shirt sizing, cadrage et estimation d'effort.
2. **Phase 1 — Spec & Ingestion** : Ingestion documentaire MarkItDown, indexation vectorielle/FTS5 (`.fact_search_index.db`) et graphe sémantique Graphify.
3. **Phase 2 — Plan & Architecture** : Découpage vertical de récits (INVEST), arbitrage contradictoire *Grill* et formalisation d'ADRs (`standards/adr-system/`).
4. **Phase 3 — Build & Stories** : Rédaction des récits verticaux selon le Gold Standard (Gherkin 4 Piliers, profilage d'API, contrats d'EvidencePacks).
5. **Phase 4 — Validate & QA** : Contrôles pré-vol déterministes **Vibe-Check** (9 contrôles déterministes), audit sémantique WikiFix et critique Sentinel.
6. **Phase 5 — Ship & Sync** : Synchronisation tripartite (Dépôt Git, Jira Cloud / Azure DevOps Boards, Index Graphify).

---

## 🚀 2. Commandes de Pilotage du Swarm (`src/swarm.py`)

Tout agent travaillant sur le dépôt ou sur un projet orchestré doit utiliser les commandes suivantes :

```bash
# 1. Boot Sequence Obligatoire (Anti-amnésie, Vibe-Check, Focus)
python src/swarm.py resume --project <nom-du-projet>
python src/swarm.py vibe-check --project <nom-du-projet>
python src/swarm.py focus --project <nom-du-projet> --story <chemin_ou_id>

# 2. Ingestion & construction du graphe
python src/swarm.py ingest --project <nom-du-projet>

# 3. Entrevue interactive de cadrage fonctionnel (Grill)
python src/swarm.py drill --project <nom-du-projet>

# 4. Synchronisation & Audit qualité
python src/swarm.py sync --project <nom-du-projet>
python src/swarm.py wikifix --project <nom-du-projet>

# 5. Synchronisation de backlog
python src/swarm.py jira_sync --project <nom-du-projet>
```

---

## 🏛️ 3. Standards d'Architecture Inviolables

### Gouvernance des Liens Wiki Azure DevOps (ADR-0327)
Dans toute User Story (`backlog/stories/`), la section `## Références` contient des liens vers la documentation externe hébergée sur Azure DevOps Wiki :
- **Priorité 1 — Le Permalink officiel avec `pageId`** :
  `https://dev.azure.com/{org}/{projet}/_wiki/wikis/{wikiName}/{pageId}/{slug}`
- **Priorité 2 — Le `pagePath` déterministe RFC 3986** :
  `https://dev.azure.com/{org}/{projet}/_wiki/wikis/{wikiName}?pagePath={chemin}`
  - **Interdiction formelle** d'utiliser `friendlyName=` conjointement avec `pagePath=`.
  - **Interdiction formelle** de coder des triples tirets `---` (utiliser `%20-%20`).
  - L'extension `.md` doit être omise du `pagePath`.
  - Toujours vérifier l'existence physique du fichier dans le staging local `reference/<nom_wiki>.wiki/`.
  - Outil de validation : `python .agents/skills/azure-devops-lifecycle/scripts/resolve_wiki_url.py`

### Règle du Double Lien (Dual-Link Pattern)
Toujours fournir conjointement :
1. Le lien Web distant HTTPS (Azure DevOps ou GitHub).
2. Le chemin physique relatif dans le dépôt ou dans `reference/` (jamais de chemins absolus Windows `file:///C:/...` non portables dans les livrables partagés).

---

## 🧪 4. Environnement Technique & Tests

* **Langage & Gestionnaire** : Python 3.11+, géré avec `uv` (`pyproject.toml`, `uv.lock`).
* **Validation & Tests** :
  ```bash
  pytest tests/           # Suite de tests unitaires
  ruff check .            # Linting et conformité du code
  python src/swarm.py vibe-check # Validation d'intégrité globale
  ```
* **Bases de Données & Mémoire** :
  * SQLite avec extension FTS5 pour le lexique et la recherche de faits.
  * Graphify / Codegraph pour le graphe de dépendances de code.
* **Intégrations Externes (.agents/mcp.json)** :
  * GitHub : `@modelcontextprotocol/server-github`
  * Azure DevOps : `@azure-devops/mcp`
  * Documentation contextuelle : Context7

---

## 🛡️ 5. Lignes Directrices pour les Agents Copilot

* **Search-Before-Ask** : Vérifier systématiquement dans le graphe ou dans la documentation `reference/` avant de formuler une question ou de supposer un schéma d'API.
* **Intégrité Lexicale** : Ne jamais altérer les termes métier normalisés définis dans le dictionnaire de lexique mLoop (`src/utils/lexicon_resolver.py`).
* **Non-Régression** : Toute modification apportée aux pipelines de `src/` doit s'accompagner d'un test unitaire dans `tests/` et d'une validation verte de `pytest`.
