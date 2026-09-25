---
id: MLOOP-341-BE
jira_key: ''
epic_key: EPIC-34-WFM-COGNITIVE-WIKI-GRAPH
type: Feature
title: Moteur d'Ingestion & Indexation Dual-Space (Passages Denses, Entités Métier
  & Hyper-Arêtes)
tags:
- core
- ingest
- wiki
- chunking
- markdown
- backend
status: READY_FOR_QA
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by:
- MLOOP-340-BE
created_at: '2026-09-25'
validated_by: Marco
validated_at: '2026-09-25T16:49:32Z'
dossier_ref: memory/evidence/MLOOP-341-BE_fact_dossier.md
ttl_cycles: 1
---

# Moteur d'Ingestion & Indexation Dual-Space (Passages Denses, Entités Métier & Hyper-Arêtes)

---

## Description
**En tant qu'** Pipeline d'Ingestion mLoop (Phase 1 : Ingest & Explore),  
**je veux** découper les documents Markdown sources en passages sémantiques continus et extraire automatiquement les hyper-arêtes reliant chaque entité métier (`ADR-*`, `RM-*`, `US-*`, symboles AST) à ses contextes textuels d'apparition,  
**afin de** peupler le Wiki Graph dual-layer sans tronquer la continuité des textes, résolvant la faiblesse du chunking naïf identifiée dans WFM (*arXiv:2609.18182*).

---

## Contexte & Périmètre

### Contexte Métier
Dans un RAG classique, les textes sont hachés en blocs aveugles de $N$ tokens (ex. 500 tokens avec 50 d'overlap), brisant la hiérarchie logique des titres et coupant les règles métier en deux. WFM formalise la notion de **Passage Documentaire Continu** : chaque section sous un titre Markdown de niveau 2 ou 3 forme une unité sémantique complète ($d \in \mathcal{D}$). En reliant ces passages aux entités discrètes ($\mathcal{E}_w$), l'agent conserve la profondeur d'explication sans perdre le fil conducteur du domaine.

### In-Scope
- Implémentation du module `src/pipelines/llm_wiki_indexer.py` (strictement $\le 300$L, `RULE-AST-01`, `ADR-0202`).
- Découpage sémantique hiérarchique (*Markdown Section Chunking*) respectant les délimiteurs `#`, `##`, `###` :
  - Découpage aux frontières H2 (`##`) et H3 (`###`) avec fil d'Ariane hiérarchique dans le titre (`Doc > H2 > H3`).
  - Agrégation continue des titres H4+ et des blocs de code (` ``` `) sans rupture dans le passage parent.
- Détecteur déterministe d'entités métier :
  - Expressions régulières pour `ADR-\d+`, `RULE-[A-Z]+-\d+`, `RM-\d+`, `MLOOP-\d+`.
  - Résolution des symboles AST de code qualifiés (`chemin/fichier.py::Classe.methode`).
  - Concepts du lexique métier canonique (`src/utils/lexicon/`).
- Typage structurel déterministe des hyper-arêtes `wiki_cross_links` :
  - `defines` : si l'entité apparaît dans le titre de la section (`section_title`).
  - `justifies` : si la section aborde le contexte décisionnel ou le rationale (mots-clés *Contexte*, *Justification*, *Décision*, *Rationale*).
  - `mentions` : pour toute citation de l'entité dans le corps du texte.
- Ingestion incrémentale par empreinte SHA-256 :
  - Fichiers inchangés ignorés avec le statut `SKIP_UNCHANGED`.
  - Nettoyage atomique en cascade (`delete_document_passages`) avant ré-indexation des fichiers modifiés.

### Out-of-Scope
- Vectorisation par plongements neuronaux GPU (hors périmètre local standard mLoop).
- Exécution de la recherche réflexive (couverte par `MLOOP-342-BE`).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*
#### 1. Découpage et Indexation de Document Markdown
* **Entrée Métier** : Chemin de fichier Markdown (`file_path: Path`), base SQLite cible (`db_path: Optional[Path]`).
* **Règles d'admissibilité & Validation** : Le fichier doit exister, être non vide et au format texte UTF-8.
* **Traitement & Algorithme Métier** :
  1. Calcul de l'empreinte SHA-256 du fichier.
  2. Vérification d'idempotence : si le fichier a déjà été indexé avec la même empreinte, renvoyer `0` avec mention `SKIP_UNCHANGED`.
  3. En cas de modification, purge transactionnelle des anciens passages associés au document via `delete_document_passages`.
  4. Découpage en sections au niveau H2/H3 en maintenant l'état des blocs de code (aucun découpage à l'intérieur d'un bloc ` ``` `).
  5. Détection des entités et qualification des hyper-arêtes (`defines`, `justifies`, `mentions`).
  6. Insertion transactionnelle dans `wiki_passages` et `wiki_cross_links`.
* **Résultat Métier & Mutations** : Nombre de passages indexés et d'hyper-arêtes créées.
* **Cas de Rejet Métier** : Tout fichier vide (0 octet) renvoie immédiatement `0` avec log `EMPTY_DOC_SKIPPED` sans altérer la base de données.

#### 2. Indexation Globale du Projet
* **Entrée Métier** : Répertoire racine du projet (`project_root: Path`), répertoires cibles `docs/` et `standards/`.
* **Traitement** : Parcours itératif, appel d'indexation incrémentale par fichier, et agrégation des métriques.
* **Résultat Métier** : Dictionnaire récapitulatif `{"processed": int, "skipped": int, "passages_created": int, "links_created": int}`.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
- `src.pipelines.llm_wiki_indexer:index_single_document(file_path: Path, db_path: Optional[Path] = None) -> int`
- `src.pipelines.llm_wiki_indexer:index_project_wiki(project_root: Path, db_path: Optional[Path] = None) -> dict`

### Matrice des Contrats API
| Méthode | Route / Point d'Entrée | Finalité | Contrat |
| :--- | :--- | :--- | :--- |
| `index_single_document` | `src.pipelines.llm_wiki_indexer:index_single_document` | Indexation d'un fichier Markdown unitaire | `(file_path: Path, db_path: Optional[Path]) -> int` |
| `index_project_wiki` | `src.pipelines.llm_wiki_indexer:index_project_wiki` | Indexation globale des Markdown du projet | `(project_root: Path, db_path: Optional[Path]) -> dict` |

> OQ-341-1 : Ce récit définit des fonctions Python internes (module `src.pipelines.llm_wiki_indexer`), pas des endpoints HTTP/REST. La "Route / Point d'Entrée" référence le chemin de module Python qualifié (`module:function`), conforme au standard Zéro Fausse Route (ADR-0319) pour les APIs internes. **[API de soumission à définir]** — Aucune route HTTP/REST n'est exposée par ce module.

---

## Règles d'affaires

- **Préservation de l'Intégrité des Paragraphes & Blocs de Code** : Aucun découpage ne peut scinder un bloc de code (` ``` `) ou tronquer une phrase.
- **Dédoublonnage des Hyper-Arêtes** : Une même entité mentionnée plusieurs fois dans le même paragraphe ne génère qu'une seule hyper-arête pondérée par sa fréquence d'occurrence.
- **Typage Déterministe des Relations (Arbitrage Micro-Grill Q2)** : L'attribution des types `defines`, `justifies` et `mentions` suit des règles structurelles objectives (titre, mot-clé décisionnel, corps du texte).
- **Idempotence & Zéro Résidu Fantôme (Arbitrage Micro-Grill Q3)** : Tout document ré-indexé purge au préalable atomiquement ses anciennes données via `delete_document_passages`.
- **Modularité Étroite (ADR-0202)** : Le fichier source `src/pipelines/llm_wiki_indexer.py` doit strictement respecter la limite de $\le 300$ lignes.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-341-BE_fact_dossier.md`](../../memory/evidence/MLOOP-341-BE_fact_dossier.md)
- 📄 **Publication de Référence** : WFM (*arXiv:2609.18182*, Section 3.1 : *Wiki Graph Construction and Dual-Space Initialization*).

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Persistance Relationnelle** : [`src/state/wiki_graph_db.py`](../../src/state/wiki_graph_db.py)
- 📜 **ADR Associé** : [ADR-0395](../../standards/adr-system/0395-wiki-graph-dual-layer-et-fact-search-reflexif-wfm.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Moteur d'Ingestion & Indexation Dual-Space

  # CHEMIN NOMINAL (Happy Path & Persistance)
  Scénario: Découpage sémantique d'un document d'architecture et liaison d'entités
    Étant donné un document Markdown contenant un en-tête H2 "Contexte ADR-0395" et une section citant "RM-012"
    Quand le pipeline d'indexation traite le fichier
    Alors les passages continus sont enregistrés dans "wiki_passages" avec leur fil d'Ariane
    Et une hyper-arête "defines" ou "justifies" est créée pour "ADR-0395"
    Et une hyper-arête "mentions" est créée pour "RM-012"
    Et l'intégrité des blocs de code Markdown est strictement préservée

  # EXCEPTIONS & REJETS MÉTIER (Règles d'affaires)
  Scénario: Traitement sécurisé d'un fichier vide ou sans en-tête Markdown
    Étant donné un fichier Markdown de 0 octet déposé sous "docs/"
    Quand le scanner traite ce fichier
    Alors le fichier est ignoré avec le statut "EMPTY_DOC_SKIPPED"
    Et aucun passage orphelin n'est créé dans la base de données

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Timeouts, Idempotence, Concurrence)
  Scénario: Ré-indexation idempotente suite à modification mineure d'un fichier
    Étant donné un document préalablement indexé
    Quand le fichier est ré-ingéré sans modification de son contenu
    Alors le statut indique "SKIP_UNCHANGED"
    Et aucune duplication de passage ou d'arête n'est introduite dans la base

  # UX, OBSERVABILITÉ & BILAN D'INGESTION
  Scénario: Synthèse structurée des entités et passages moissonnés
    Étant donné l'achèvement de l'indexation d'un ensemble de documents
    Quand le rapport d'exécution est généré
    Alors le journal consigne le total de fichiers traités, sautés, et passages enregistrés
```

---

## Definition of Ready (DoR) Checklist

- [x] **1. Description & Périmètre** : Clairs, contextualisés par WFM et centrés sur le Markdown Section Chunking continu.
- [x] **2. Critères d'Acceptation** : Spécifications fonctionnelles déterministes, typage des hyper-arêtes et idempotence.
- [x] **3. Contrats d'Échange API & Données** : Signatures `index_single_document` et `index_project_wiki` alignées sur `wiki_graph_db.py`.
- [x] **4. Dépendances & Impacts** : Dépend de `MLOOP-340-BE` (opérationnel) et alimente `MLOOP-342-BE`.
- [x] **5. Dossier de Preuves Sourcé** : Preuves factuelles établies dans `memory/evidence/MLOOP-341-BE_fact_dossier.md`.
- [x] **6. Validation Micro-Grill PO** : 3 arbitrages techniques (frontières H2/H3, typage structurel, cache SHA-256) intégrés.
