# ADR-0323 : Semantic Chunking & Raisonnement Documentaire

**Statut** : Accepté  
**Date** : 18 août 2026  
**Auteurs** : Équipe mLoop & Co-Architecte Agentique  
**Domaine** : Ingestion documentaire, RAG Graphify, Extraction de Spécifications, Azure Content Understanding 2.0  

---

## 1. Contexte et Problématique

L'ingestion documentaire et l'extraction de contrats fonctionnels dans les architectures d'agents rencontrent deux écueils majeurs :

1. **La Rupture Sémantique du Chunking Naïf (Fixed-Window Drift)** :
   Le découpage linéaire standard basé sur le nombre de caractères ou de lignes scinde arbitrairement les tableaux Markdown au milieu d'une ligne, sépare les titres de leurs paragraphes explicatifs ou tronque les blocs d'admonition (`[!NOTE]`, `[!WARNING]`), produisant des fragments incompréhensibles pour les moteurs de recherche sémantique (RAG / Graphify).

2. **L'Insuffisance de l'Extraction en Simple Passe (Single-Pass Blindspot)** :
   Face à des spécifications d'architecture complexes et volumineuses, une analyse en une seule passe omet les dépendances réparties sur plusieurs sections distantes et ne dispose d'aucun mécanisme contradictoire pour réconcilier les contradictions.

3. **L'Inspiration d'Azure Content Understanding 2.0 (Août 2026)** :
   L'annonce de Microsoft Foundry concernant **Azure Content Understanding 2.0** valide deux piliers fondamentaux :
   - Le **Semantic Chunking** basé sur la hiérarchie structurelle des documents.
   - Le **Mode Agentique (Agentic Document Reasoning)** appliquant une boucle de raisonnement itérative multi-passes (Proposer / Critic / Verifier).

---

## 2. Décisions Architecturales

Nous actons l'intégration et le renforcement des composants suivants au sein du framework mLoop :

### A. Moteur de Découpage Sémantique (`src/utils/semantic_chunker.py`)
* **Atomicité Absolue des Blocs** : Les tableaux Markdown (`|---|---|`), blocs de code clôturés (```` ``` ````) et admonitions GitHub (`> [!NOTE]`) sont traités comme des blocs atomiques insécables.
* **Fil d'Ariane Hiérarchique (Header Breadcrumb Path)** : Chaque fragment sémantique (`SemanticChunk`) conserve son chemin hiérarchique complet (`Document > H1 > H2 > H3`), garantissant que le modèle connaît toujours le contexte englobant lors d'un appel RAG.
* **Seuils Adaptatifs** : Découpage ciblé avec `max_chunk_chars: 1500` et `min_chunk_chars: 150`, préservant la cohésion des paragraphes frères.

### B. Pipeline d'Extraction Agentique Multi-Passes (`src/pipelines/agentic_doc_extractor.py`)
Le pipeline d'extraction de spécifications s'articule en 4 passes séquentielles :
1. **Passe 1 (Scan Structurel & Semantic Chunking)** : Cartographie complète des sections sans rupture.
2. **Passe 2 (Proposer - Extraction Candidate)** : Détection déclarative des règles métier, schémas, contraintes et endpoints.
3. **Passe 3 (Critic - Validation Croisée & Sentinel)** : Détection des contradictions entre fragments distants et ajustement du score de confiance.
4. **Passe 4 (Verifier - Consolidation SSOT)** : Génération du contrat fonctionnel consolidé et alimentation synchrone des EvidencePacks (`memory/evidence/`).

### C. Primitives CLI mLoop
mLoop enrichit sa suite d'outils CLI :
* `python src/swarm.py chunk --project <nom> --file <chemin>` : Découpage sémantique d'un document Markdown avec estimation de tokens et traçabilité hiérarchique.
* `python src/swarm.py agentic-extract --project <nom> --file <chemin>` : Extraction agentique multi-passes produisant le rapport de faits et de règles consolidé.

---

## 3. Conséquences

### Positives
* **Zéro Tableau Brisé** : Intégrité totale des structures tabulaires et des blocs d'alertes lors de l'ingestion dans Graphify et SQLite.
* **Haute Précision RAG** : Grâce au Header Breadcrumb Path, les fragments récupérés par recherche sémantique conservent leur sens exact sans ambiguïté de portée.
* **Économie de Tokens (Advanced Contextualization)** : Les sous-agents ne reçoivent que les chunks pertinents avec leur métadonnée d'en-tête, réduisant la consommation de tokens de prompt.
* **Détection Précoce des Incohérences** : La validation croisée de la Passe 3 intercepte les contradictions avant toute phase de rédaction de code BUILD.

### Négatives / Vigilances
* Légère augmentation du temps de pré-traitement lors de l'analyse initiale par rapport à un découpage brut par lignes.

---

## 4. Références & Alignement

* **Standard mLoop R&D** : `.agents/skills/research-and-develop/SKILL.md`
* **Article de Référence** : Microsoft Foundry Blog — *« Azure Content Understanding: Agentic workflow, Sync APIs, GPT-5 model series »* (Août 2026)
* **Code Source Associé** :
  - `src/utils/semantic_chunker.py`
  - `src/pipelines/agentic_doc_extractor.py`
  - `tests/test_semantic_chunker.py`
  - `tests/test_agentic_doc_extractor.py`
