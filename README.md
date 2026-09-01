# ðŸŒ€ Memory Loop - Cognitive Pure State-Graph Multi-Agent Engine (mLoop)

Bienvenue dans l'espace de travail de **Memory Loop (mLoop)**. Cet écosystème implémente une architecture **Kernel-Pipeline** modulaire, orchestrée par un swarm d'agents cognitifs Système 2 et Système 1.


Les outils et scripts utilitaires transverses mis à disposition des humains et des agents IA sont centralisés et indexés sous :

*   ðŸ§° **[Catalogue de la Boîte à Outils (tools/README.md)](tools/README.md)** : Index central de nos utilitaires d'ingénierie.
    *   ðŸ’³ **[Suivi du Budget IA LiteLLM (tools/budget/README.md)](tools/budget/README.md)** : Diagnostic et solde en temps réel de votre clé de calcul Nmédia Cloud.

---

## ðŸ—‚ï¸ Index des Projets Actifs

L'ensemble des projets industriels pilotés par le moteur réside sous le répertoire `/Projects` :

*   ðŸª **[commerce-react](Projects/commerce-react/README.md)** : Migration de l'application mobile Metro (Jean Coutu & Brunet) de .NET MAUI vers React Native (Expo).
*   â˜ï¸ **ReviewSenseCloud** : Solution d'extraction et de monitoring automatique d'avis clients sur les stores.

Chaque projet possède sa propre structure standardisée (ADR-0015) comprenant ses `directives/`, son `journal/` d'architecture, son `backlog/` et ses spécifications `openspec/`.

---

## 🚀 Démarrer le Moteur `src/swarm.py`

Le moteur `src/swarm.py` pilote le cycle mLoop via des pipelines modulaires. Les anciennes commandes `loop.py` ont été dépréciées et retirées.

```bash
# 1. Ingestion & construction initiale du graphe (System 1 Graphify)
python src/swarm.py ingest --project <nom-du-projet>

# 2. Entrevue interactive Drill Me (Alignement fonctionnel / DDD)
python src/swarm.py drill --project <nom-du-projet>

# 3. Synchronisation globale (WikiFix sémantique + mise à jour du graphe Graphify)
python src/swarm.py sync --project <nom-du-projet>

# 4. Exécuter un audit sémantique WikiFix indépendant
python src/swarm.py wikifix --project <nom-du-projet>

# 5. Synchroniser le backlog de stories vers Jira Cloud
python src/swarm.py jira_sync --project <nom-du-projet>

# 6. Optimisation Rétrospective du Harnais (Génération de règles RHO)
python src/swarm.py optimize --project <nom-du-projet> --keyword "mot-cle" --msg "explication" --scope <project|global>
```



