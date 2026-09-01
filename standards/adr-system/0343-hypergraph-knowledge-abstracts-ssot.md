# ADR-0343 : Hypergraph Knowledge Abstracts & Relations N-aires SSOT

## 🏛️ Statut
**Accepté** — Standard Normatif mLoop Core Architecture (29 août 2026)

---

## 🎯 Contexte & Problématique
Dans l'architecture mLoop précédente (ADR-0200, ADR-0204), les graphes de connaissances (Graphify & CodeGraph) reposaient sur des modèles binaires standardisés ($u \leftrightarrow v$).

Dans un contexte de spécification logicielle et de backlog agile :
* Une User Story ne constitue pas un nœud isolé relié par des paires simples. Elle lie de manière indissociable un ensemble de dimensions hétérogènes :
$$\text{Hyper-Edge } e = \{\text{Story}, \text{Persona}, \text{Route API}, \text{Règle Métier}, \text{Modèle de Données}, \text{ADR}, \text{Critères Gherkin 4 Piliers}\}$$
* L'éclatement binaire classique oblige l'agent à naviguer sur plusieurs sauts de graphe (*Multi-hop graph traversal*), augmentant le risque d'omission de contraintes transverses et la consommation d'attention/tokens.

---

## 💡 Décision Architecturale

### 1. Adoption du Modèle Hypergraphe (Hyper-Story Units)
Nous adoptons le concept de **Knowledge Abstract (KA)** et de structure sur **Hypergraphe** inspiré de *Hyper-Extract* :
* Une **Hyper-Edge** (Hyper-Arête) représente une unité sémantique cohérente reliant simultanément $N$ entités typées.
* Chaque User Story du backlog est représentée en mémoire comme une **Hyper-Story Unit**.

### 2. Le Moteur d'Hypergraphes (`src/core/hypergraph_engine.py`)
Le moteur fournit les primitives d'abstraction :
* `create_hyper_edge(edge_id, node_ids, edge_type, metadata)`
* `get_hyper_story_unit(story_id)` -> retourne instantanément la projection compacte de toutes les entités liées sans traversée récursive.
* `query_hypergraph(filter_predicate)` -> permet le filtrage multidimensionnel par version, statut, acteur ou couche technique.
* `merge_hypergraphs(ka_a, ka_b)` -> fusionne de manière incrémentale deux abstracts avec alignement sémantique et résolution de conflits.

### 3. Traçabilité Spatio-Temporelle & Cycles de Vie
Chaque hyper-arête capture :
* La version de validité (`valid_from_version`, `deprecated_in_version`).
* L'historique d'évolution des statuts (`DRAFT` $\rightarrow$ `GRILL_IN_PROGRESS` $\rightarrow$ `READY_FOR_DEV` $\rightarrow$ `DONE`).
* L'impact immédiat en cas de dépréciation d'une règle métier ou d'un ADR.

### 4. Exposition MCP (`loop_hypergraph_query`)
Le serveur MCP de mLoop expose la fonction native `loop_hypergraph_query` pour permettre à tout agent ou sous-session Herdr d'obtenir en un seul appel l'intégralité du contexte architectural et fonctionnel d'un récit.

---

## ⚖️ Conséquences & Impacts
* **Positif** : Zéro angle mort lors de la rédaction et de l'audit de récits (Sentinel / Rubber-Duck).
* **Positif** : Réduction substantielle du budget de contexte grâce au packaging compact des Knowledge Abstracts.
* **Positif** : Alignement complet avec le paradigme Universal Dev Handoff (ADR-0319).
