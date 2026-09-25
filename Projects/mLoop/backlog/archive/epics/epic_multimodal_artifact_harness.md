# 🏛️ Épopée — `EPIC-30-MULTIMODAL-ARTIFACT-HARNESS` : Harnais de Fidélité Visuelle & Intégrité des Artefacts Topologiques

---

> **Référence d'Architecture** : [ADR-016](../../docs/01-architecture/ADR-016_epic-30_harnais_fidelite_visuelle_et_integrite_artefacts_topologiques.md) (Macro-Grill EPIC-30) · [ADR-0392](../../../../standards/adr-system/0392-harnais-fidelite-visuelle-integrite-artefacts-topologiques.md) (Standard Topologique Artefacts) · [ADR-0377](../../../../standards/adr-system/0377-runtimes-agents-aval-et-herdr-operationnels.md) (Runtimes Aval & Herdr) · [ADR-0202](../../../../standards/adr-system/0202-modularite-interne-agents.md) (Modularité ≤ 300L) · [ADR-0375](../../../../standards/adr-system/0375-standard-preuve-epistemique-et-tracabilite-radicale.md) (Traçabilité Radicale) · [ADR-0376](../../../../standards/adr-system/0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md) (Rigueur 360° Zéro Blindspot) · [ADR-0389](../../../../standards/adr-system/0389-grill-v2-frontier-rounds-ungrillable-handoff-context-budget.md) (Grill v2 & Ungrillable Context)  
> **Composant(s)** : `Tools/Archify` · `Pipelines/Ingest` · `Pipelines/Audit` · `Bridges/Crawler` · `QA/VibeCheck`  
> **Origine / Déclencheur** : Étude scientifique de pointe **ReFigBench** (*arXiv:2609.18844*, Septembre 2026) :
> 1. Mise en évidence du phénomène critique de *Connector Collapse* (perte de 100 % des connecteurs relationnels natifs lors d'optimisations visuelles poussées par les agents multimodaux).
> 2. Démonstration de la primauté du Harnais (*Harness Primacy* : écart de plus de 5 points de score à modèle invariant selon le contexte et les outils du harnais).
> 3. Identification des inversions de flux sémantiques masquées sous une apparence visuelle séduisante.
> 4. Algorithme d'extraction guidé par les légendes techniques (*ORBIT Caption Harvesting*).  
> **Statut** : `OPEN` — **Session Macro-Grill VALIDÉE le 25/09/2026 (PO Marco)**. 5 récits en transition Palier 2 (`READY_FOR_GROOMING`).  
> **Décideurs** : Marco (PO) / Architecte Agentique  

---

## 🎯 1. Contexte & Intention Stratégique

Dans le modèle mental de **Memory Loop**, le framework agit en **Fournisseur Universel de Spécifications (*Universal Dev Handoff*)**. Il cadre, valide et formalise les règles métier et les modèles sous forme d'artefacts sans ambiguïté destinés aux développeurs et aux agents d'implémentation avals (Claude Code, OpenCode, Cursor, Codex).

L'étude scientifique **ReFigBench** (*Benchmarking Scientific Figure Reconstruction as Editable PowerPoint Artifacts*) démontre que lorsque des agents autonomes manipulent ou reconstituent des figures et diagrammes complexes :
- **L'illusion cosmétique prime sur l'intégrité structurelle** : les agents remplacent les connecteurs logiques et la topologie par des dessins plats, détruisant l'éditabilité et la maintenabilité future de l'artefact.
- **Le harnais fait le succès ou l'échec** : le même modèle de pointe (ex. GPT-5.5) progresse nettement ou régresse selon l'infrastructure d'outils, la granularité de contexte et les contrats de gating fournis par le harnais.
- **La sémantique peut s'inverser silencieusement** : un diagramme peut obtenir un score de propreté visuelle maximal tout en inversant le sens des dépendances logiques ou des pipelines de traitement.

L'objectif de cette épopée est d'incorporer ces enseignements dans mLoop afin de garantir qu'aucun artefact visuel ou architectural (diagramme Archify, schéma d'ingestion, spécification d'IHM) ne sacrifie sa structure relationnelle à une simple ressemblance de surface.

---

## 🧭 2. Vérité Terrain & Ancrage Normatif

> En application de l'**ADR-0375** (Traçabilité Radicale) et de l'**ADR-0376** (Zéro Blindspot), cette épopée s'ancre sur les sources vérifiées suivantes :

* **Publication Scientifique** : *ReFigBench: Benchmarking Scientific Figure Reconstruction as Editable PowerPoint Artifacts* (arXiv:2609.18844, 2026).
* **Codebase Source Locale mLoop** :
  * Moteur de diagrammes vectoriels : [`tools/archify/`](tools/archify/) et [`src/commands/handlers/archify_core.py`](src/commands/handlers/archify_core.py)
  * Ingestion documentaire : [`src/pipelines/ingest.py`](src/pipelines/ingest.py) et [`src/pipelines/ingest_file_processors.py`](src/pipelines/ingest_file_processors.py)
  * Moteur de crawl local : [`C:\mloop-crawler`](c:/mloop-crawler) et [`src/bridges/mcp_crawler.py`](src/bridges/mcp_crawler.py)
  * Audit d'analyse : [`src/commands/handlers/analysis_audit.py`](src/commands/handlers/analysis_audit.py)

---

## 🗂️ 3. Décomposition des Récits (Backlog Slicing INVEST)

L'épopée est découpée en 5 récits verticaux indépendants de Palier 1 :

| Identifiant | Type | Titre | Scope & Valeur Produite | Macro-Taille |
| :--- | :---: | :--- | :--- | :---: |
| **`MLOOP-300-BE`** | Enabler | **Porte Déterministe d'Artefacts & Anti-Raster Paste (`DeterministicArtifactGate`)** | Porte mécanique $g(P) \in \{0, 1\}$ bloquant les livrables visuels non ouvrables ou usurpés par un collage raster brut (>85%). | **M** |
| **`MLOOP-301-BE`** | Feature | **Validation Topologique Anti-Effondrement des Connecteurs Archify** | Contrôle strict dans `archify validate` interdisant les arêtes orphelines et garantissant l'intégrité relationnelle du graphe. | **M** |
| **`MLOOP-302-BE`** | Feature | **Filtre d'Ingestion Documentaire ORBIT pour Schémas d'Architecture** | Heuristique de repérage et découpage des figures d'architecture directrices via analyse des légendes (*captions*). | **M** |
| **`MLOOP-303-BE`** | Feature | **Grille d'Audit Architectural Découplée (Structure Sémantique vs Rendu)** | Refonte de la notation d'audit surpondérant la topologie des dépendances (30%) et détectant les inversions logiques de flux. | **S** |
| **`MLOOP-304-FULL`** | Feature | **Contrats de Dev Handoff Multi-Harnais & Commande CLI `mloop artifact-check`** | Commande CLI unifiée d'audit d'artefacts, intégration Vibe-Check (Check 24) et formalisation des garde-fous pour runtimes aval. | **L** |

---

## 🛡️ 4. Matrice d'Impact en 7 Couches (ADR-0376)

1. **Blueprints / Standards** : Enrichissement des critères de validation DoR / DoD (6/6) pour les artefacts graphiques et schémas système.
2. **Protocols** : Formalisation du protocole de contrôle d'artefacts déterministe avant toute relecture cognitive LLM.
3. **ADR System** : Référencement croisé avec ADR-0377 (Runtimes avals) et formalisation d'un futur ADR d'intégrité d'artefacts.
4. **Agents** : Fourniture aux agents de directives explicites bannissant l'usage d'éléments décoratifs plats en lieu et place d'arêtes relationnelles.
5. **Skills** : Renforcement du skill `archify` et des compétences d'ingestion multimodale.
6. **Code (`src/` & `tools/`)** : Extension modulaire de `tools/archify/` et de `src/pipelines/ingest.py` (respect strict du plafond modulaire ≤ 300L, `RULE-AST-01`).
7. **Tests & Vibe-Check** : Création d'un test suite dédié `tests/test_artifact_harness.py` et intégration dans la sonde de vol `vibe-check`.