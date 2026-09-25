# Plan d'Implémentation : Parent Document Resolver & Distillateur de Datasets INVEST/Gherkin

Ce plan formalise l'intégration dans **mLoop** des deux opportunités clés issues du benchmark **Second Brain / Decoding AI** :
1. **Parent Document Resolver pour Graphify & EvidencePacks** : Résolution automatique du paragraphe parent et des règles englobantes dès qu'un fragment sémantique est repéré.
2. **Distillateur de Dataset INVEST & Gherkin (`invest_dataset_distiller`)** : Générateur de jeux de données d'instructions synthétiques (*Instruct Dataset*) prêt pour le fine-tuning QLoRA / Unsloth de modèles locaux dédiés à l'audit rapide.

---

## 🎯 Objectifs & Bénéfices

* **Contexte RAG Enrichi à 100% (Zero Blindspot)** : Les EvidencePacks ne reçoivent plus de fragments isolés mais le bloc parent complet (Section H2, contexte d'écran, règles associées).
* **Autonomie & Économie de Tokens (Fine-Tuning Local)** : Capacité de générer des datasets de distillation formatés (ChatML / Alpaca) pour entraîner des petits modèles (Llama 3.1 8B, Qwen 7B) à l'audit INVEST/Gherkin sans dépendre exclusivement des modèles cloud lourds.
* **Traçabilité & Standardisation (ADR-0328)** : Ancrage officiel dans le SSOT d'architecture de mLoop.

---

## ⚠️ User Review Required

> [!IMPORTANT]
> - L'implémentation est strictement confinée au framework mLoop (`src/utils/`, `src/pipelines/`, `tests/`) sans impacter les données des projets clients.
> - Le distillateur génère des fichiers d'entraînement sous `memory/datasets/` sans lancer d'entraînement GPU lourd localement (génération du dataset uniquement).

---

## 📂 Modifications Proposées

### 1. Parent Document Resolver (`ParentDocumentResolver`)

#### [NEW] [`src/utils/parent_doc_resolver.py`](file:///C:/Memory%20Loop/src/utils/parent_doc_resolver.py)
* À partir d'un chunk ou d'une recherche vectorielle :
  - Identifie le document parent Markdown.
  - Résout le bloc parent englobant (Section H2/H3 complète avec paragraphe d'introduction et règles sœurs).
  - Fournit une méthode d'enrichissement automatique pour les EvidencePacks (`enrich_evidence_with_parents`).

---

### 2. Distillateur de Dataset INVEST & Gherkin (`InvestDatasetDistiller`)

#### [NEW] [`src/pipelines/invest_dataset_distiller.py`](file:///C:/Memory%20Loop/src/pipelines/invest_dataset_distiller.py)
* Analyse les récits Gold Standard (`standards/blueprints/story_template.md` et `backlog/stories/`).
* Génère des paires d'exemples d'entraînement structurés au format JSONL (ChatML / ShareGPT) :
  - **Exemples Positifs (Compliants)** : Récits conformes aux 4 Piliers Gherkin et critères INVEST.
  - **Exemples Négatifs Dégradés (Contradictoires)** : Récits avec anomalies délibérées (fuites techniques, scénarios Gherkin manquants, titres avec bruit d'échafaudage).
* Exporte le dataset synthétique sous `Projects/<project>/memory/datasets/invest_gherkin_distilled.jsonl`.

---

### 3. Intégration CLI Swarm

#### [MODIFY] [`src/commands/_registry.py`](file:///C:/Memory%20Loop/src/commands/_registry.py)
* Ajout des commandes CLI :
  - `distill-invest` : Génération du dataset d'instructions pour fine-tuning.
  - `parent-resolve` : Test et inspection de la résolution de documents parents.

#### [MODIFY] [`src/commands/handlers/analysis.py`](file:///C:/Memory%20Loop/src/commands/handlers/analysis.py)
* Implémentation des handlers CLI associés.

---

### 4. Formalisation SSOT & ADR

#### [NEW] [`docs/01-architecture/ADR-0328_parent_document_resolver_and_invest_dataset_distillation.md`](file:///C:/Memory%20Loop/docs/01-architecture/ADR-0328_parent_document_resolver_and_invest_dataset_distillation.md)
* Consignation de la spécification de résolution parentale et du protocole de distillation de datasets d'audit.

---

## 🧪 Plan de Validation & Vérification

### Tests Automatisés
- **Tests unitaires des 2 moteurs** :
  ```bash
  python -m unittest tests/test_parent_doc_resolver.py
  python -m unittest tests/test_invest_dataset_distiller.py
  ```
- **Validation Globale de la Suite** :
  ```bash
  python -m unittest discover -s tests -p "test_*.py"
  ```

### Vérification CLI & Auto-Étalonnage
- Exécution des commandes CLI :
  ```bash
  python src/swarm.py distill-invest --project mLoop
  python src/swarm.py parent-resolve --project mLoop --file memory/crawler/cache/crawl_towardsdatascience_com_f12c870cabfb.md
  python src/swarm.py calibrate --project mLoop
  ```
