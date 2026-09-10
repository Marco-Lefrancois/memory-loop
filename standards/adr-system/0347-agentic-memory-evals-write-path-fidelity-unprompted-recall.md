# ADR-0347 : Métrologie de Mémoire Agentique, Fidélité du Write-Path & Rappel Proactif Non Sollicité

- **Statut** : Approuvé (Constitutionnel)
- **Date** : 2026-09-02
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Périmètre** : Framework Backend mLoop, Pipelines Mémoire (src/pipelines/), Indexation Graphify/FTS5, EvidencePacks, Session Memory Health

---

## 1. Contexte & Problématique

L'évaluation des systèmes de mémoire pour agents IA souffre historiquement de trois biais majeurs identifiés par la recherche empirique (garrytan/gbrain-evals, HaluMem arXiv 2511.03506, Dey & Viradecha arXiv 2604.21284) :
1. **L'illusion du QA End-to-End** : Les benchmarks déclaratifs mélangent la performance du système de mémoire avec les capacités de raisonnement du grand modèle de langage lecteur (jusqu'à 18 points de variation pour une mémoire identique).
2. **L'angle mort du Write-Path** : La quasi-totalité des solutions évalue la lecture (Read-Path), alors que plus de 50% de la perte d'information critique et des distorsions surviennent lors de la phase de capture/distillation des sessions de travail.
3. **Le piège de la métrique any-hit vs recall_all@k** : Les scores de recall any-hit masquent l'incapacité à rassembler l'intégralité des preuves nécessaires sur les requêtes multi-sessions et temporelles.

Cette ADR formalise l'intégration dans **mLoop** des principes de métrologie de mémoire à long terme, de distillation mesurée en écriture et de rappel contextuel spontané.

---

## 2. Décisions d'Architecture

### 2.1 Les 4 Piliers de Métrologie de Mémoire mLoop

`
                                  ┌────────────────────────────────────────────────────────┐
                                  │             ARCHITECTURE MÉMOIRE MLOOP                 │
                                  └───────────────────────────┬────────────────────────────┘
                                                              │
                        ┌─────────────────────────────────────┼─────────────────────────────────────┐
                        │                                     │                                     │
                        ▼                                     ▼                                     ▼
        ┌───────────────────────────────┐     ┌───────────────────────────────┐     ┌───────────────────────────────┐
        │ 1. RETRIEVAL HYBRIDE NO-LLM   │     │  2. WRITE-PATH DISTILLATION   │     │   3. PROACTIVE UNPROMPTED     │
        │ • SQLite FTS5 (BM25 exact)    │     │ • Gating de Survie (>85%)     │     │ • Trigger Reflex Non-Ask      │
        │ • Dense Embeddings + RRF      │     │ • Rejet Distracteurs (<2%)    │     │ • Zéro Fuite Cross-Source     │
        │ • Graphify Traversal (+30 pts)│     │ • Distillation Triple-Couche  │     │ • Push Precision 1.0          │
        └───────────────────────────────┘     └───────────────────────────────┘     └───────────────────────────────┘
                                                              │
                                                              ▼
                                              ┌───────────────────────────────┐
                                              │ 4. AUDIT ÉPISTÉMIQUE & GROUND │
                                              │ • Passage-Level EvidencePacks │
                                              │ • Métrique Stricte Recall-All │
                                              │ • Errata & Logs Falsifiables  │
                                              └───────────────────────────────┘
`

#### 1. Retrieval Hybride RRF Déterministe (Zéro Coût LLM par Requête)
- **Principe** : Le moteur de recherche interne mLoop (loop_mem_search, vectorstore local, Graphify) s'appuie sur une fusion déterministe **FTS5 (BM25) + Dense Embeddings + Traversée de Graphe** via Reciprocal Rank Fusion (RRF).
- **Justification** : Le RAG vectoriel pur échoue sur les termes précis, identifiants de tickets, dates et hashes. Le graphe relationnel apporte un gain prouvé de ~30 points de précision sur les requêtes multi-sauts, à coût nul d'inférence LLM au runtime.

#### 2. Protocole de Distillation en Écriture (Write-Path Audit)
- **Principe** : Lors de la synthèse de session, du compactage d'état (SESSION_MEMORY_HEALTH.md) ou de l'extraction de connaissances OKF (docs/06-knowledge/), mLoop applique une architecture en 3 couches :
  - **Verbatim Capture** : Préservation intacte des extraits sources originaux.
  - **Facts Distillation** : Extraction des faits et décisions d'architecture irrévocables.
  - **Synthesis / Dream Layer** : Établissement des liens sémantiques globaux et mise à jour de la mémoire de travail.
- **Seuils de tolérance** : Taux de survie des éléments saillants >= 85%, fuite de distracteurs <= 2%.

#### 3. Rappel Contextuel Proactif Non Sollicité (Unprompted Reflex)
- **Principe** : Le Cerveau mLoop doit faire émerger les contraintes critiques, règles d'affaires et précédents d'architecture au moment opportun *sans que le développeur ou le sous-agent n'ait à poser la question* (Zéro know-to-ask failure).
- **Mise en œuvre** : Vérifications pré-vol au démarrage de tour (vibe-check), verrouillage d'attention sur récit cible (focus), et audit de conformité Sentinel passif.

#### 4. Audit Épistémique & Rigueur des Métriques
- **Découpage Strict** : Toute évaluation R&D mLoop applique le diptyque de grounding (what_it_actually_proves, what_it_does_not_prove, claim_boundaries).
- **Standard Recall-All** : Interdiction de promouvoir des chiffres any-hit sans publier en vis-à-vis le score recall_all@k officiel sur les requêtes multi-sources.

---

## 3. Conséquences & Bénéfices
- **Robustesse du Crawl & Ingestion** : Résolution du bug de collision des llms.txt racines sur les forges de code (github.com, gitlab.com, huggingface.co).
- **Précision Maximale sans Latence** : Maintien de l'approche no-LLM pour la recherche documentaire locale, garantissant des réponses sub-seconde et un budget d'inférence préservé.
- **Pérennité de la Mémoire de Projet** : Intégrité garantie des EvidencePacks et des fiches de santé de session au fil des itérations.

---

## 4. Fichiers Liés & Implémentation
- **Crawler Web mLoop** : src/pipelines/crawler.py (Correction de sonde fast-path llms.txt).
- **Pipeline R&D** : src/pipelines/research_pipeline.py.
- **Skill de Référence** : .agents/skills/research-and-develop/SKILL.md.
- **Dépôt de Référence Ingéré** : Projects/mLoop/reference/research/gbrain-evals/.