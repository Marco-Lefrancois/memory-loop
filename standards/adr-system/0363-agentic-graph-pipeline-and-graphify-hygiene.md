# ADR-0363 : Protocole Agentic Subgraph Retrieval, Hygiène Graphify, Cache Mémoire et Cloisonnement CodeGraph

- **Statut** : Approuvé (Constitutionnel)
- **Date** : 2026-09-10
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Périmètre** : Framework Swarm (`src/bridges/mcp_graphify.py`, `src/commands/handlers/graph_intelligence.py`, `src/commands/_registry.py`), Filtrage Racine (`.graphifyignore`), Standards mLoop (`ADR-0204`, `CLAUDE.md`, `AGENTS.md`)

---

## 1. Contexte & Problématique

L'expérience d'exploitation du double moteur de graphes (CodeGraph et Graphify, formalisé par l'**ADR-0204**) a mis en lumière trois pathologies critiques au sein de l'espace de travail mLoop :

1. **La dérive volumétrique et la récursion d'indexation (198 Mo de JSON)** :
   En l'absence de fichier `.graphifyignore`, l'indexation globale Graphify a avalé récursivement 14 693 fichiers, dont 6 972 fichiers C# clients sous `Projects/*/reference/codebase/`, 2 274 maquettes vectorielles SVG et 708 fichiers JSON (dont des caches et des `knowledge_graph.json` préexistants, provoquant une boucle d'auto-indexation de graphes).
2. **La violation de frontière constitutionnelle (ADR-0204)** :
   L'ADR-0204 prescrit formellement que **CodeGraph** est l'unique détenteur de l'analyse AST du code physique applicatif volumineux (stocké en base SQLite WAL 928 Mo). L'ingestion par Graphify de 7 000 fichiers C# constituait un dédoublement stérile et pénalisant.
3. **Le goulot d'étranglement CPU/RAM et l'absence de cache** :
   Dans [`src/bridges/mcp_graphify.py`](file:///C:/Memory%20Loop/src/bridges/mcp_graphify.py), chaque requête d'outil MCP (`graph_query`, `graph_explain`) relisait le disque et réexécutait `json.loads()` sur 198 Mo (3-5 secondes de blocage CPU, 1.5 Go de RAM). De plus, l'ordre de chargement priorisait la racine sur les projets actifs (ex: `Metro_FOOD` dont le graphe ne pèse que 17 Ko).
4. **L'illusion de la lecture brute de graphe par l'agent LLM (Context Poisoning)** :
   Un agent injectant un fichier `.json` de graphe directement dans sa fenêtre de contexte (via `view_file`) s'expose à une saturation immédiate de tokens, un bruit syntaxique destructeur et du *Context Rot*.

---

## 2. Décisions d'Architecture

```
                                  ┌────────────────────────────────────────────────────────┐
                                  │          AGENTIC SUBGRAPH RETRIEVAL & HYGIÈNE          │
                                  └───────────────────────────┬────────────────────────────┘
                                                              │
                        ┌─────────────────────────────────────┼─────────────────────────────────────┐
                        │                                     │                                     │
                        ▼                                     ▼                                     ▼
        ┌───────────────────────────────┐     ┌───────────────────────────────┐     ┌───────────────────────────────┐
        │  1. CLOISONNEMENT & IGNORE    │     │  2. CACHE & PRIORITÉ PROJET   │     │  3. AGENTIC RETRIEVAL PIPELINE│
        │ • .graphifyignore souverain   │     │ • Cache Singleton en mémoire  │     │ • swarm.py graph-query/explain│
        │ • Exclusion C# (CodeGraph)    │     │ • Priorité : Projet Actif     │     │ • Réponse Markdown 200-400 tok│
        │ • Exclusion SVGs, Caches      │     │ • Invalidation sur mtime disk │     │ • Interdiction JSON brut      │
        │ • Racine : 198 Mo -> 4.6 Mo   │     │ • Latence : 3500ms -> 0.00ms  │     │ • Token Budget Guardrail      │
        └───────────────────────────────┘     └───────────────────────────────┘     └───────────────────────────────┘
```

### 2.1 Protocole "Agentic Subgraph Retrieval" (Zéro JSON Brut en Inférence)

- **Interdiction Formelle** : Les agents d'orchestration ou de spécialisation mLoop ne doivent **JAMAIS** charger un fichier `graph.json` ou `knowledge_graph.json` brut dans leur fenêtre d'attention.
- **Canal Exclusif par Pipeline** : La consultation du graphe s'effectue exclusivement par :
  1. Le bridge MCP officiel (`graph_query`, `graph_explain`, `graph_impact`, `graph_status`).
  2. Les commandes CLI du pipeline : `python src/swarm.py graph-query --query "..."`, `python src/swarm.py graph-explain --concept "..."`.
- **Token Budget Guardrail** : Les commandes de consultation condensent le résultat en une fiche Markdown ultra-compacte de **200 à 400 tokens** (nœud, description, voisins entrants/sortants 1-hop).

### 2.2 Cloisonnement Strict ADR-0204 et Fichier `.graphifyignore`

- Un fichier [`.graphifyignore`](file:///C:/Memory%20Loop/.graphifyignore) racine est déployé et gouverne toute exécution de `graphify`.
- Il exclut obligatoirement :
  - Le code physique AST réservé à CodeGraph : `**/reference/codebase/**`, `**/*.cs`, `**/*.vb`.
  - Les assets graphiques et binaires : `**/*.svg`, `**/*.png`, `**/*.jpg`, `**/*.pdf`.
  - Les caches internes et fichiers récursifs : `**/knowledge_graph.json`, `**/ingest_cache.json`, `**/test_cache/**`.
  - Les dossiers de compilation et IDE : `**/bin/**`, `**/obj/**`, `**/dist/**`, `**/.obsidian/**`, `**/.codegraph/**`.
- **Résultat Métrique** : Le volume du graphe racine `graphify-out/graph.json` est ramené de **188.85 Mo à 4.62 Mo** (réduction de **97.6 %**).

### 2.3 Cache Singleton en Mémoire et Routage Projet Prioritaire

Dans [`src/bridges/mcp_graphify.py`](file:///C:/Memory%20Loop/src/bridges/mcp_graphify.py) :
- **Routage de Projet** : Lorsqu'une requête cible un projet (ou le projet actif), le résolveur charge :
  1. `Projects/<project>/memory/knowledge_graph.json`
  2. `Projects/<project>/graphify-out/graph.json`
  Le fichier racine global `graphify-out/graph.json` n'est interrogé qu'en dernier ressort ou si `--global` est explicitement déclaré.
- **Cache Mémoire Singleton** : Un dictionnaire `_GRAPH_CACHE` associe à chaque chemin canonique son horodatage de modification (`st_mtime`) et les données parsées. Tant que le fichier n'est pas modifié sur le disque, l'accès mémoire est immédiat (**0.00 ms**).

### 2.4 Commandes Déclaratives du Pipeline CLI (`src/swarm.py`)

Quatre commandes souveraines sont enregistrées dans [`src/commands/_registry.py`](file:///C:/Memory%20Loop/src/commands/_registry.py) et implémentées dans [`src/commands/handlers/graph_intelligence.py`](file:///C:/Memory%20Loop/src/commands/handlers/graph_intelligence.py) :
- `graph-status` : Affiche la santé, la taille, le nombre de nœuds et d'arêtes du graphe actif.
- `graph-query` : Recherche plein texte ciblée sur les identifiants, labels et descriptions de concepts.
- `graph-explain` : Restitution de la fiche conceptuelle et des dépendances 1-hop amont/aval.
- `graph-impact` : Calcul déterministe du rayon d'impact (Blast Radius) via le moteur souverain mLoop.

---

## 3. Conséquences & Bénéfices

| Dimension | Avant ADR-0363 | Après ADR-0363 |
| :--- | :--- | :--- |
| **Poids Graphe Racine** | 188.85 Mo (177k nœuds) | **4.62 Mo** (4.2k nœuds) (-97.6%) |
| **Fichiers Scannés Racine** | 14 693 fichiers | **362 fichiers** (-97.5%) |
| **Latence Requête Projet** | ~3 500 ms (blocage CPU 198 Mo) | **< 1 ms** (chargement 17 Ko / cache mémoire) |
| **Consommation RAM MCP** | ~1.5 Go de dicts volumineux | **< 15 Mo** pour le projet actif |
| **Pollution Contexte Agent** | Risque critique de dumping JSON brut | **200-400 tokens Markdown synthétiques** |
| **Interface Agent/CLI** | Zéro commande directe dans `swarm.py` | 4 commandes CLI intégrées + MCP bridge |