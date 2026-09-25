---
id: MLOOP-341-BE
jira_key: ''
epic_key: EPIC-34-WFM-COGNITIVE-WIKI-GRAPH
type: Feature
title: Moteur d'Ingestion & Indexation Dual-Space (Passages Denses, Entités Métier & Hyper-Arêtes)
tags:
- core
- ingest
- wiki
- chunking
- markdown
- backend
status: DRAFT
grill_me: PENDING
invest_score: 6/6
layer: backend
blocked_by:
- MLOOP-340-BE
created_at: '2026-09-25'
ttl_cycles: 3
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
- Implémentation du module `src/pipelines/llm_wiki_indexer.py` (strictement $\le 300$L, `RULE-AST-01`).
- Découpage sémantique hiérarchique (*Markdown Section Chunking*) respectant les délimiteurs `#`, `##`, `###`.
- Détecteur d'entités métier calibré :
  - Expressions régulières pour `ADR-\d+`, `RM-\d+`, `US-\d+`, `MLOOP-\d+`.
  - Résolution des symboles AST de code qualifiés (`chemin/fichier.py::Classe.methode`).
  - Concepts du lexique métier canonique (`src/utils/lexicon/`).
- Création automatique des hyper-arêtes `wiki_cross_links` :
  - `defines` : si l'entité est le sujet principal ou le titre de la section.
  - `mentions` : si l'entité apparaît dans le corps du paragraphe.
  - `justifies` : si la section contient une clause de justification ou un contexte d'ADR.
- Injection ou consolidation des liens bidirectionnels `[[WikiLinks]]`.

### Out-of-Scope
- Vectorisation par plongements neuronaux GPU (hors périmètre local standard mLoop).
- Exécution de la recherche réflexive (couverte par MLOOP-342-BE).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*
#### 1. Découpage et Indexation de Document Markdown (`index_markdown_document_passages`)
* **Entrée Métier** : Chemin de fichier Markdown (`file_path: Path`), contenu brut UTF-8.
* **Règles d'admissibilité & Validation** : Le fichier doit exister sous `docs/` ou `memory/`, être non vide et au format texte valide.
* **Traitement & Algorithme Métier** :
  1. Découpage du document par blocs hiérarchiques basés sur les en-têtes Markdown.
  2. Conservation du titre de section, du niveau d'en-tête et du texte intégral associé.
  3. Scan lexical des entités présentes dans chaque section.
  4. Insertion transactionnelle des sections dans `wiki_passages` et des liaisons dans `wiki_cross_links`.
* **Résultat Métier & Mutations** : Nombre de passages indexés et nombre d'hyper-arêtes créées.
* **Cas de Rejet Métier** : Échec propre avec journal d'avertissement si fichier non décodable en UTF-8 sans faire échouer le pipeline global (`Zero Crash Policy`).

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
- `src.pipelines.llm_wiki_indexer:index_project_wiki(project_root: Path) -> dict`
- `src.pipelines.llm_wiki_indexer:index_single_document(file_path: Path) -> int`

#### Matrice des Contrats API
| Méthode | Route / Point d'Entrée | Finalité | Contrat |
| :--- | :--- | :--- | :--- |
| `index_project_wiki` | `src.pipelines.llm_wiki_indexer:index_project_wiki` | Indexation globale de tous les Markdown du projet | `(project_root: Path) -> dict` |
| `index_single_document` | `src.pipelines.llm_wiki_indexer:index_single_document` | Indexation d'un fichier Markdown unitaire | `(file_path: Path) -> int` |

- **Admission of Limits & Résilience Système** :
  - **Fichiers Volumineux** : Découpage par flux sans chargement monolithique de documents > 10 Mo.
  - **Documents Vides** : Tout fichier Markdown de 0 octet est ignoré avec statut `EMPTY_DOC_SKIPPED` sans générer de nœud fantôme.

---

## Règles d'affaires

- **Préservation de l'Intégrité des Paragraphes** : Aucun découpage ne peut couper une phrase ou un bloc de code (` ``` `) au milieu.
- **Dédoublonnage des Hyper-Arêtes** : Une même entité mentionnée plusieurs fois dans le même paragraphe ne génère qu'une seule hyper-arête pondérée par sa fréquence d'occurrence.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves** : [`memory/evidence/EPIC-34_wfm_fact_dossier.md`](../../memory/evidence/EPIC-34_wfm_fact_dossier.md)
- 📄 **Publication de Référence** : WFM (*arXiv:2609.18182*, Section 3.1 : *Wiki Graph Construction and Dual-Space Initialization*).

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Structure de Données** : [`docs/01-architecture/SCHEMAS_BD_ET_GRAPHES.md`](../../docs/01-architecture/SCHEMAS_BD_ET_GRAPHES.md)
- 📜 **ADR Associé** : [ADR-0395](../../standards/adr-system/0395-wiki-graph-dual-layer-et-fact-search-reflexif-wfm.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Moteur d'Ingestion & Indexation Dual-Space

  # CHEMIN NOMINAL (Happy Path & Persistance)
  Scénario: Découpage sémantique d'un document d'architecture et liaison d'entités
    Étant donné un document Markdown contenant 3 sections et citant "ADR-0392" et "RM-012"
    Quand le pipeline d'indexation traite le fichier
    Alors 3 passages distincts sont enregistrés dans "wiki_passages"
    Et 2 hyper-arêtes "mentions" sont créées dans "wiki_cross_links"
    Et l'intégrité des blocs de code Markdown est strictement préservée

  # EXCEPTIONS & REJETS MÉTIER (Règles d'affaires)
  Scénario: Traitement sécurisé d'un fichier vide ou sans en-tête Markdown
    Étant donné un fichier Markdown de 0 octet déposé sous "docs/00-ingested/"
    Quand le scanner traite ce fichier
    Alors le fichier est ignoré avec le statut "EMPTY_DOC_SKIPPED"
    Et aucun passage orphelin n'est créé dans la base de données

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Timeouts, Idempotence, Concurrence)
  Scénario: Ré-indexation idempotente suite à modification mineure d'un fichier
    Étant donné un document préalablement indexé
    Quand le fichier est ré-ingéré sans modification de son contenu
    Alors les identifiants de hash SHA-256 restent inchangés
    Et aucune duplication de passage ou d'arête n'est introduite

  # UX, OBSERVABILITÉ & EMPTY STATE (Spinners, Retours Écran, Logs)
  Scénario: Synthèse structurée des entités et passages moissonnés
    Étant donné l'achèvement de l'indexation de l'ensemble du répertoire "docs/"
    Quand le rapport d'exécution est généré
    Alors le log consigne le total de passages et d'hyper-arêtes enregistrés
```
