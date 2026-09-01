# Documentation de Graphify

**Graphify** est le moteur d'ingestion sémantique et de création de la "Mémoire" (pilier *Memory*) pour l'écosystème Memory Loop (mLoop). Son rôle est d'analyser physiquement la base de code et de générer le **Graphe Cognitif Vivant** exploitable par les agents.

---

## 1. Fonctionnalités Principales

### A. Indexation et Graphe Sémantique
Graphify scanne l'arbre du projet (fichiers, dossiers) et génère deux artefacts cruciaux :
* `knowledge_graph.json` : Le graphe réseau (nœuds et liens) de toute l'architecture.
* `graph_index.db` : Un index de recherche rapide (FTS5 SQLite) utilisé par le protocole *Search-First*.

### B. Traçabilité des Récits (Story Tracking)
Graphify lie directement les récits d'affaires (Stories) aux fichiers de code physiques.
* **Fonctionnement** : Il scanne le code source à la recherche de tags de traçabilité (regex `\[(US-\d+|[A-Z0-9]+-\d+)\]`).
* **Usage** : Un développeur ou l'agent `build` peut insérer un commentaire comme `// [US-001]` dans un fichier.
* **Résultat** : Graphify créera automatiquement une relation sémantique (flèche `"implements"`) entre le nœud de la Story `US-001` et le nœud du fichier physique.

### C. Support C# (.NET) via Parsing Lexical
Pour les projets hérités ou de référence (ex: `reference/ReviewSense-main/`), Graphify inclut un parser lexical hybride léger basé sur des regex robustes, évitant l'instabilité des lourdes dépendances AST natives.
* **Extraction** : Détecte les `namespace`, `class`, `interface`, et `method`.
* **Relations** : Analyse les imports `using` pour tisser des liens avec le lexique technologique.

### D. Normalisation Lexicale et Déduplication
Pour éviter un graphe pollué par des doublons technologiques, Graphify intègre une table de synonymes.
* **Exemple** : `postgres`, `postgresql`, `PostgreSQL` seront fusionnés dans un seul et même nœud unique `PostgreSQL`.

---

## 2. Commandes et Utilisation

Les opérations de Graphify sont désormais appelées via la CLI locale (sans surcharger le Kernel).

**Mettre à jour / Ingérer le graphe manuellement :**
*(À exécuter après toute modification physique importante du code)*
```powershell
graphify update .
```

**Forcer une ré-ingestion complète (sans cache) :**
```powershell
graphify update . --force
```

---

## 3. Architecture Interne
Graphify fonctionne via des analyseurs AST et lexicaux statiques, garantissant des performances d'ingestion élevées même sur d'imposantes bases de code, grâce au maintien d'un cache incrémental SHA-256 (`ingest_cache.json`). Il n'est plus considéré comme un agent indépendant (v1.0.0) mais comme un outil métier autonome invoqué soit par l'humain, soit par l'Event Bus (v1.1.0).
