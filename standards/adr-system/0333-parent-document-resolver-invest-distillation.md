# ADR-0333 : Parent Document Resolver & Distillation INVEST

**Statut** : Accepté  
**Date** : 18 août 2026  
**Auteurs** : Équipe mLoop & Co-Architecte Agentique  
**Domaine** : RAG Contextuel, Distillation LLM, Audit INVEST, Optimisation de Tokens, Fine-Tuning Local  

---

## 1. Contexte et Problématique

Dans les systèmes agentiques et de RAG documentaire (ex: mLoop, Graphify, Sentinel) :

1. **L'Aveuglement du RAG Naïf (*Fragment Isolation*)** :
   Lorsqu'une recherche vectorielle ou textuelle isole une règle atomique (ex: *"Le délai de garde est fixé à 500ms"*), l'agent perd la section englobante, le contexte d'écran et les règles sœurs associées, risquant des interprétations partielles.
2. **Le Coût Élevé des Audits Contradictoires Cloud** :
   Soumettre systématiquement l'intégralité d'un backlog aux grands modèles propriétaires (GPT-4o, Claude 3.5 Sonnet) pour de simples contrôles de forme, critères INVEST et 4 Piliers Gherkin engendre une latence et une facture de tokens disproportionnées.

---

## 2. Décisions Architecturales

Inspiré des schémas d'ingénierie de **Decoding AI (Second Brain Course - Août 2026)**, mLoop intègre deux composants fondamentaux :

### A. Parent Document Resolver (`src/utils/parent_doc_resolver.py`)
* Tout extrait, règle ou observation extrait par recherche sémantique peut être automatiquement rattaché à son bloc parent :
  - **Chemin Hiérarchique** : `Doc > H1 > H2 > H3`
  - **Bloc Parent Englobant** : Titre H2/H3, paragraphe d'introduction et règles soeurs.
* Permet d'alimenter les EvidencePacks JSON avec un contexte à 360° sans blindspot.

### B. Distillation de Dataset INVEST / Gherkin (`src/pipelines/invest_dataset_distiller.py`)
* Génération automatisée de jeux de données d'instructions synthétiques (*Instruct Dataset*) au format JSONL (ChatML / ShareGPT) combinant :
  - **Exemples Compliants** : Récits respectant le Gold Standard `standards/blueprints/story_template.md`.
  - **Exemples Contradictoires Dégradés** : Récits injectés avec des anomalies ciblées (fuites de code physique `ADR-0319`, piliers Gherkin manquants, titres avec identifiants parasites).
* Permet le fine-tuning (Unsloth / QLoRA) de petits modèles locaux (Llama 3.1 8B, Qwen 7B) dédiés au rôle Sentinel ultra-rapide.

---

## 3. Commandes CLI Associées

* `python src/swarm.py parent-resolve --project <nom> --file <fichier> --query "<extrait>"` : Résout et affiche la section parente et les règles sœurs.
* `python src/swarm.py distill-invest --project <nom>` : Exporte le jeu de données d'entraînement sous `Projects/<nom>/memory/datasets/invest_gherkin_distilled.jsonl`.

---

## 4. Conséquences

### Positives
* **Zéro Perte de Contexte RAG** : Les agents de rédaction et d'audit ont accès immédiat à la règle parente et aux conditions adjacentes.
* **Autonomie de Fine-Tuning** : Disponibilité d'un pipeline de génération de données de haute qualité pour entraîner des agents locaux spécialisés.
* **Économie de Tokens** : Réduction substantielle des requêtes vers les modèles cloud lourds pour les tâches d'audit répétitives.

---

## 5. Références

* **Référence Externe** : Decoding AI — *« Building Your Second Brain AI Assistant Using Agents, LLMs and RAG »* (Août 2026)
* **ADR Associés** :
  - `ADR-0301` : 4 Piliers Gherkin et Titres Purs
  - `ADR-0319` : Universal Dev Handoff & Boundary Code vs Architecture
  - `ADR-0325` : Semantic Chunking et Extraction Documentaire Agentique
  - `ADR-0326` : Auto Eval Harvester et Moniteur de Contexte
  - `ADR-0327` : Guardrail d'Intégrité Lexicale et Signature de Vocabulaire
