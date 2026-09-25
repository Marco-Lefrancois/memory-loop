# Plan d'Implémentation : Intégration des Patterns Azure Content Understanding 2.0 dans mLoop

Ce plan d'implémentation formalise l'adoption et l'adaptation des innovations architecturales issues d'**Azure Content Understanding 2.0** (Semantic Chunking, Mode Agentique multi-passes, Ingestion Synchrone et Contrôle de Confiance) pour renforcer le pipeline d'ingestion et d'analyse de **mLoop**.

---

## 🎯 Objectifs & Bénéfices Métier

1. **Semantic Chunking Préservant la Structure** : Remplacer les découpages naïfs par un découpeur sémantique qui conserve l'intégrité des tableaux Markdown, sections H2/H3, listes et blocs d'admonition (`[!NOTE]`, `[!WARNING]`).
2. **Mode Agentique Itératif (Proposer/Critic/Verifier)** : Formaliser un pipeline multi-passes pour l'extraction de règles d'affaires complexes depuis les documents bruts volumineux.
3. **Réduction Drastique des Tokens (Advanced Contextualization)** : Minimiser l'injection de contexte redondant dans les prompts agents en ciblant uniquement les sous-arbres sémantiques pertinents.
4. **Gouvernance & Traçabilité (ADR-0324)** : Consigner officiellement la décision d'architecture dans le SSOT de mLoop.

---

## ⚠️ User Review Required

> [!IMPORTANT]
> - L'implémentation cible **exclusivement le framework mLoop** (`src/`, `docs/01-architecture/`) sans impacter les projets clients isolés (`Projects/Metro_*`, `Projects/BoireFrere_*`).
> - Le découpage sémantique deviendra le standard par défaut pour l'indexation Graphify et les EvidencePacks.

---

## 📂 Modifications Proposées

### 1. Module de Découpage Sémantique (Semantic Chunking)

#### [NEW] [`src/utils/semantic_chunker.py`](file:///C:/Memory%20Loop/src/utils/semantic_chunker.py)
* Détecte et respecte les frontières naturelles des documents :
  - Blocs d'en-tête Markdown (`#`, `##`, `###`)
  - Tableaux intègres (ne jamais scinder une ligne ou un tableau au milieu)
  - Blocs de code et admonitions GitHub (`[!NOTE]`, `[!WARNING]`)
  - Préservation des métadonnées de section (chemin hiérarchique : `Doc > H2 > H3`)
* Génère des chunks enrichis de leur contexte parent pour maximiser la précision de recherche sémantique.

---

### 2. Pipeline d'Extraction Agentique Itérative (Agentic Mode)

#### [NEW] [`src/pipelines/agentic_doc_extractor.py`](file:///C:/Memory%20Loop/src/pipelines/agentic_doc_extractor.py)
* Implémente le pattern itératif inspiré de CU 2.0 pour les documents volumineux :
  - **Passe 1 (Scan Structurel)** : Cartographie des sections et extraction des fragments candidats.
  - **Passe 2 (Validation Croisée & Contradiction)** : Confrontation des faits extraits avec les sections adjacentes (Sentinel).
  - **Passe 3 (Consolidation SSOT)** : Génération du contrat fonctionnel / EvidencePack sans hallucination.

---

### 3. Intégration CLI Swarm

#### [MODIFY] [`src/swarm.py`](file:///C:/Memory%20Loop/src/swarm.py)
* Ajout de la commande CLI mLoop :
  - `python src/swarm.py chunk --file <chemin>` : Découpage sémantique d'un fichier Markdown.
  - Intégration transparente dans le pipeline `ingest` et `sync`.

---

### 4. Décision d'Architecture Officielle (ADR-0324)

#### [NEW] [`docs/01-architecture/ADR-0324_semantic_chunking_and_agentic_reasoning.md`](file:///C:/Memory%20Loop/docs/01-architecture/ADR-0324_semantic_chunking_and_agentic_reasoning.md)
* Formalisation des principes directeurs :
  - Invariant : Aucun chunk ne doit briser un tableau ou séparer un titre de son premier paragraphe.
  - Règle de sélection : Fast-Path synchrone vs Mode Agentique itératif selon la complexité documentaire.

---

## 🧪 Plan de Validation & Vérification

### Tests Automatisés
- **Test Unitaire Chunking Sémantique** :
  ```bash
  python -m unittest discover -s tests -p "test_semantic_chunker.py"
  ```
  Validation que les tableaux Markdown et les sections hiérarchiques restent 100% intègres.
- **Validation CLI Swarm** :
  ```bash
  python src/swarm.py chunk --file memory/crawler/cache/crawl_devblogs_microsoft_com_15a8fda6da08.md
  ```

### Auto-Étalonnage & Synchronisation
- Exécution de l'auto-étalonnage mLoop :
  ```bash
  python src/swarm.py calibrate --project mLoop
  python src/swarm.py sync --project mLoop
  ```
