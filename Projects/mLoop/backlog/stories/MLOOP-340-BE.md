---
id: MLOOP-340-BE
jira_key: ''
epic_key: EPIC-34-WFM-COGNITIVE-WIKI-GRAPH
type: Enabler
title: Schéma Relationnel & Persistance SQLite du Wiki Graph Dual-Layer (Entities, Passages & Hyper-Edges)
tags:
- core
- memory
- wiki
- graph
- sqlite
- backend
status: READY_FOR_DEV
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by: []
created_at: '2026-09-25'
validated_by: Marco
validated_at: '2026-09-25T14:12:15Z'
dossier_ref: memory/evidence/MLOOP-340-BE_fact_dossier.md
ttl_cycles: 3
---

# Schéma Relationnel & Persistance SQLite du Wiki Graph Dual-Layer (Entities, Passages & Hyper-Edges)

---

## Description
**En tant qu'** Moteur Cognitif mLoop responsable de la mémoire long-terme et de l'intégrité contextuelle,  
**je veux** disposer d'un schéma relationnel SQLite formel unifiant les entités conceptuelles discrètes ($\mathcal{E}_w$), les relations d'architecture ($\mathcal{R}_w$) et les passages textuels continus ($\mathcal{D}$) au sein de la base `memory/loop_mem.db`, couplé à une table virtuelle FTS5 `wiki_passages_fts` et à une politique de remplacement en cascade par document,  
**afin de** fournir une structure de données hybride native éliminant la fracture entre les index lexicaux plats et les graphes de code épars, conformément au standard WFM (*arXiv:2609.18182*).

---

## Contexte & Périmètre

### Contexte Métier
Dans l'architecture de mémoire de mLoop, les connaissances du projet (décisions d'architecture, règles métier, scénarios Gherkin, symboles de code AST et documents bruts ingérés) sont actuellement dispersées entre l'index lexical FTS5, des graphes de code isolés et des fichiers Markdown sans pont formel. L'étude WFM démontre que séparer les triplets relationnels des passages textuels denses dégrade le rappel de mémoire de plus de 7 points. Ce récit pose les fondations relationnelles persistantes de la mémoire unifiée de mLoop, intégrant une table FTS5 synchrone pour la recherche plein texte instantanée et une purge atomique en cascade par document lors des ré-ingestions.

### In-Scope
- Création et migration idempotente des tables SQLite dans `memory/loop_mem.db` :
  - `wiki_entities` : identifiant canonique (`entity_id`), type (`ADR`, `RULE`, `STORY`, `AST_SYMBOL`, `CONCEPT`), nom, métadonnées JSON, empreinte SHA-256.
  - `wiki_relations` : `source_entity_id`, `target_entity_id`, `relation_type` (`implements`, `verifies`, `governs`, `depends_on`, `calls`), poids, métadonnées JSON.
  - `wiki_passages` : `passage_id`, document source (`doc_path`), numéro de section, titre, contenu textuel brut, hash SHA-256, date d'ingestion.
  - `wiki_cross_links` : table de pont liant `entity_id` $\leftrightarrow$ `passage_id`, avec type d'hyper-arête (`defines`, `mentions`, `justifies`), position/offset, et force de liaison (`ON DELETE CASCADE`).
  - `wiki_passages_fts` : table virtuelle FTS5 couplée et synchronisée via triggers SQLite automatiques (`AFTER INSERT`, `AFTER UPDATE`, `AFTER DELETE`).
- Fonction de purge atomique en cascade `purge_document_passages(doc_path: str)` garantissant un remplacement propre sans résidus orphelins lors de la ré-ingestion d'un document Markdown.
- Vues d'interrogation et index optimisés pour la traversée multi-hop.
- Module d'accès de données `src/state/wiki_graph_db.py` (strictement $\le 300$L, `RULE-AST-01`).

### Out-of-Scope
- Découpage automatique des textes Markdown en sections (couvert par MLOOP-341-BE).
- Algorithmes de recherche réflexive et d'attention (couverts par MLOOP-342-BE et MLOOP-343-BE).
- Moteurs de stockage NoSQL ou graphes orientés objet externes (Neo4j, etc.).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*
#### 1. Initialisation & Migration du Schéma Wiki Graph (`initialize_wiki_graph_schema`)
* **Entrée Métier** : Connexion active SQLite vers `memory/loop_mem.db`.
* **Règles d'admissibilité & Validation** : La base de données doit être accessible en lecture/écriture avec support FTS5 et clés étrangères activées (`PRAGMA foreign_keys = ON`).
* **Traitement & Algorithme Métier** :
  1. Exécution transactionnelle `CREATE TABLE IF NOT EXISTS` pour les 4 tables relationnelles avec contraintes d'unicité et clés primaires strictes.
  2. Création de la table virtuelle FTS5 `wiki_passages_fts` et de ses 3 triggers synchrones (`AFTER INSERT`, `AFTER UPDATE`, `AFTER DELETE`).
  3. Création d'index couvrants sur `(source_entity_id, relation_type)`, `(entity_id, passage_id)` et `doc_path`.
  4. Migration descendante non destructive si d'anciennes versions de tables existent.
* **Résultat Métier & Mutations** : Schéma garanti conforme sans altérer les données FTS5 existantes.
* **Cas de Rejet Métier** : Échec transactionnel si corruption de fichier SQLite ou verrouillage concurrent non résolu.

#### 2. Enregistrement d'Entités et d'Hyper-Arêtes (`upsert_wiki_entity_link`)
* **Entrée Métier** : Dictionnaire d'entité, passage associé et type d'hyper-arête (`defines`, `mentions`, `justifies`).
* **Règles d'admissibilité & Validation** : L'identifiant d'entité ne doit pas être vide ; le passage doit exister ou être fourni dans la transaction.
* **Traitement & Algorithme Métier** :
  1. Insertion ou mise à jour atomique (`INSERT ... ON CONFLICT DO UPDATE`).
  2. Mise à jour de l'empreinte SHA-256 pour traçabilité radicale.
* **Résultat Métier & Mutations** : Tuple persisté et horodaté.
* **Cas de Rejet Métier** : Rejet si type d'entité ou d'hyper-arête non reconnu dans le vocabulaire contrôlé.

#### 3. Purge Atomique par Document Source (`purge_document_passages`)
* **Entrée Métier** : Chemin relatif normalisé du document (`doc_path: str`).
* **Règles d'admissibilité & Validation** : Le chemin doit être non vide et normalisé avec des slashs conventionnels (`docs/...`).
* **Traitement & Algorithme Métier** :
  1. Transaction atomique : `DELETE FROM wiki_passages WHERE doc_path = ?`.
  2. Déclenchement automatique de la suppression en cascade dans `wiki_cross_links` via contrainte de clé étrangère.
  3. Déclenchement du trigger FTS5 supprimant les entrées correspondantes dans `wiki_passages_fts`.
* **Résultat Métier & Mutations** : Suppression tout-ou-rien confirmée avec compte d'enregistrements purgés.
* **Cas de Rejet Métier** : Annulation complète (ROLLBACK) si une sous-opération échoue.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
- `src.state.wiki_graph_db:initialize_wiki_graph_schema(db_path: Path) -> bool`
- `src.state.wiki_graph_db:upsert_wiki_entity(entity: dict) -> str`
- `src.state.wiki_graph_db:link_entity_to_passage(entity_id: str, passage_id: str, link_type: str) -> bool`
- `src.state.wiki_graph_db:purge_document_passages(doc_path: str) -> int`

#### Matrice des Contrats API
| Méthode | Route / Point d'Entrée | Finalité | Contrat |
| :--- | :--- | :--- | :--- |
| `initialize_wiki_graph_schema` | `src.state.wiki_graph_db:initialize_wiki_graph_schema` | Initialisation des tables SQLite du Wiki Graph | `(db_path: Path) -> bool` |
| `upsert_wiki_entity` | `src.state.wiki_graph_db:upsert_wiki_entity` | Enregistrement idempotent d'une entité | `(entity: dict) -> str` |
| `link_entity_to_passage` | `src.state.wiki_graph_db:link_entity_to_passage` | Liaison transversale entité-passage | `(entity_id: str, passage_id: str, link_type: str) -> bool` |

- **Admission of Limits & Résilience Système** :
  - **Absence de réseau / Timeout** : 100% local SQLite in-process, zéro latence réseau.
  - **Concurrence & Anti-Rebond** : Utilisation du mode SQLite WAL (`PRAGMA journal_mode = WAL`) et d'un timeout de busy handler de 5000 ms pour gérer les accès concurrents.
  - **Entrées Extrêmes** : Tout identifiant contenant des injections SQL ou caractères invalides est paramétré via requêtes préparées strictes (`?`).

---

## Règles d'affaires

- **Intégrité Référentielle Stricte** : Aucune hyper-arête ne peut pointer vers une entité inexistante ; les contraintes de clés étrangères sont obligatoirement appliquées.
- **Idempotence Absolue de Migration** : Le schéma peut être initialisé $N$ fois de suite sans duplication ni écrasement destructif des données historiques.
- **Vocabulaire Contrôlé des Entités** : Seuls les types `ADR`, `RULE`, `STORY`, `AST_SYMBOL`, `CONCEPT` sont admis comme entités de premier ordre.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves** : [`memory/evidence/EPIC-34_wfm_fact_dossier.md`](../../memory/evidence/EPIC-34_wfm_fact_dossier.md)
- 📄 **Publication de Référence** : WFM (*arXiv:2609.18182*, Définition 2, Équations 1-2).

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Norme SQLite mLoop** : [`docs/01-architecture/SCHEMAS_BD_ET_GRAPHES.md`](../../docs/01-architecture/SCHEMAS_BD_ET_GRAPHES.md)
- 📜 **ADR Associé** : [ADR-0395](../../standards/adr-system/0395-wiki-graph-dual-layer-et-fact-search-reflexif-wfm.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Schéma Relationnel & Persistance SQLite du Wiki Graph Dual-Layer

  # CHEMIN NOMINAL (Happy Path & Persistance)
  Scénario: Initialisation nominale du schéma et liaison entité-passage
    Étant donné un chemin de base de données "memory/loop_mem.db" accessible
    Quand le module initialise le schéma du Wiki Graph
    Alors les tables "wiki_entities", "wiki_relations", "wiki_passages" et "wiki_cross_links" sont créées
    Et l'enregistrement d'une entité "ADR-0392" avec son passage lié persiste avec succès
    Et une requête jointe retourne immédiatement la relation transversale

  # EXCEPTIONS & REJETS MÉTIER (Règles d'affaires)
  Scénario: Rejet lors de l'enregistrement d'une entité avec un type inconnu
    Étant donné une tentative d'insertion d'une entité ayant pour type "TYPE_INVENTE"
    Quand la validation des règles de typage est exécutée
    Alors l'opération est refusée avec une exception de vocabulaire contrôlé
    Et aucune ligne n'est insérée dans la table "wiki_entities"

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Timeouts, Idempotence, Concurrence)
  Scénario: Idempotence lors d'exécutions multiples successives de la migration
    Étant donné une base contenant déjà des entités et des liens existants
    Quand la fonction d'initialisation de schéma est déclenchée 3 fois consécutives
    Alors aucune exception n'est levée
    Et l'ensemble des données préexistantes est strictement préservé

  # UX, OBSERVABILITÉ & EMPTY STATE (Spinners, Retours Écran, Logs)
  Scénario: Journalisation structurée de la migration et de la latence
    Étant donné l'initialisation réussie des tables du graphe
    Quand le traitement s'achève
    Alors un journal structuré consigne le nombre de tables créées et le temps d'exécution
    Et aucune alerte de performance n'est émise
```
