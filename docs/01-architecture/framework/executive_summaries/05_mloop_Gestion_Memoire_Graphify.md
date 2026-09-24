# mLoop - 05. Gestion de la Mémoire : Graphify, RAG & Ponts MCP

Dans Memory Loop, l'état du système (`LoopState`) n'est jamais maintenu sous la forme d'un long texte collé dans un prompt d'IA, ce qui provoquerait fatalement une "pourriture du contexte".

## Le Graphe de Connaissance (Graphify & AST)
L'état complet (architecture, journal des événements, directives et dépendances AST du code) est structuré dans un graphe de connaissances stocké sous format JSON (`Projects/<nom_projet>/memory/knowledge_graph.json` pour mLoop et `graphify-out/graph.json` pour les utilitaires graphify).
C'est la Source Unique de Vérité (Ground Truth). Le moteur de recherche sémantique *L3 In-Memory* permet de réaliser des requêtes graph complexes :
* `graphify query "<question>"` : Navigation sémantique ciblée dans le sous-graphe.
* `graphify explain "<concept>"` : Explication détaillée des nœuds et relations.
* `graphify path "<A>" "<B>"` : Analyse du plus court chemin de dépendance entre deux composants.

## L'Encapsulation via les Ponts MCP (Model Context Protocol)
L'IDE Agentique interagit avec cet état et le code source via des serveurs MCP locaux :
*   `mcp_loop_mem.py` : Expose des outils clés tels que `loop_mem_search` (recherche dans les observations de session) et `loop_mem_preload_context` (chargement 1-hop en RAM Cache), permettant à l'IDE de lire l'état de session sans saturer le contexte.
*   `mcp_crawler.py` : Expose des capacités d'aspiration web via le moteur local Node.js (`mloop-crawler`).

## State Checkpointing & Restauration
Pour supporter les interruptions et la reprise d'exécution des pipelines DAG Multi-Agents, mLoop enregistre des points de contrôle sous `.mloop_tmp/checkpoints/<initiative>.json`, permettant la reprise immédiate via `python src/swarm.py graph-run --resume`.

## L'obligation d'Auto-Synchronisation
Après toute modification de fichier source ou documentaire, l'agent a l'obligation stricte de lancer `python src/swarm.py sync --project <nom_projet>` (ou `graphify update .`). Cette commande reconstruit le graphe de connaissances et met à jour l'index cache (SHA256).
