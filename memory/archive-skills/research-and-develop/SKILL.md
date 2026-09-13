---
name: research-and-develop
description: Session de R&D automatisée mLoop. Ingestion de liens/documentation via crawler, analyse d'impact sur l'écosystème mLoop, création d'ADR et implémentation du code.
---

# 🧪 research-and-develop (Skill R&D & Analyse de Spécification mLoop)

> **Status:** Active | **Standard:** mLoop Core R&D Protocol

## 🧠 Introduction
Ce skill régit la conduite d'une **Session de Recherche & Développement (R&D)** pour l'écosystème **mLoop**. Il permet de capturer automatiquement toute spécification externe, article, repository ou documentation (via une URL), d'analyser son contenu par rapport aux 8 piliers mLoop, de rédiger l'ADR d'architecture correspondant et de réaliser les évolutions du framework mLoop.

---

## ⚡ Déclencheurs Automatiques
Ce skill se déclenche lorsque l'utilisateur exprime une demande telle que :
- *"J'aimerais lancer une session de recherche et développement pour mloop sur cette spec : [URL]"*
- *"Peux-tu analyser cette documentation/spécification et voir si on peut l'intégrer à mLoop : [URL]"*
- *"R&D mLoop sur [URL]"*
- Invoqué via la CLI mLoop : `python src/swarm.py research --url <URL>`

---

## 🚀 Le Workflow R&D en 5 Étapes (Standard ADR-0335)

### Étape 1 : Ingestion Automatique & Source Manifest Canonique
1. Exécuter la commande mLoop Crawler :
   `python src/swarm.py crawl --project mLoop --url <URL>`
2. Inspecter le fichier Markdown généré sous `memory/crawler/cache/crawl_<domain>_<hash>.md`.
3. Si la documentation référence un index global (ex: `/llms.txt`, arbre GitHub API ou manifeste de source), utiliser `read_url_content` pour extraire les sous-pages et fichiers bruts pertinents.
4. **Contrat de Source Canonique** : L'analyse doit s'appuyer sur la matière première brute complète (code source, sections textuelles intégrales, tables de données) et non sur un simple survol d'abstract (*Raw-Source Authority*).

### Étape 2 : Analyse d'Impact & Audit Épistémique des Preuves
1. Inspecter le contenu ingéré par rapport à la grille d'architecture mLoop :
   - **Moteur CLI & Swarm Pipelines** (`src/swarm.py`, `src/pipelines/`)
   - **Ponts et Serveurs MCP** (`src/bridges/mcp_*.py`, `opencode.json`)
   - **Graphify & VectorStore RAG** (`graphify-out/`, `Open Notebook`)
   - **Directives & Guardrails** (`AGENTS.md`, `GEMINI.md`, `WikiFix`, `AOEP`)
2. **Découpage Épistémique Strict (Diptyque de Grounding)** :
   - **`what_it_actually_proves`** : Ce que les données chiffrées, benchmarks, règles ou implémentations démontrent formellement.
   - **`what_it_does_not_prove`** : Ce que la source ne démontre pas (angles morts, hypothèses non testées, limites d'échelle, contraintes de production).
   - **`claim_boundaries`** : Périmètre de validité de chaque assertion pour éviter toute sur-interprétation (*Claim Inflation*).
3. Identifier les ruptures de conception, opportunités d'optimisation (Prompt Cache, Caching déterministe, Observabilité OpenTelemetry, Stateless, Glossaire atomique) et gains de performance.

### Étape 3 : Plan-First & Grounding Gate
1. Rédiger le rapport d'analyse R&D et le plan d'évolution sous forme d'artefact `implementation_plan.md` via `write_to_file`.
2. **Grounding Gate** : Vérifier que chaque proposition technique découle directement d'une preuve documentée dans le manifest de source avant toute écriture de code.
3. Présenter le plan à l'utilisateur avec `request_feedback: true` pour validation explicite.

### Étape 4 : Formalisation SSOT & ADR (`docs/01-architecture/`)
1. Rédiger la décision d'architecture officielle dans `docs/01-architecture/ADR-XXX_<titre>.md`.
2. Inclure le contexte, les 6 piliers d'impact, les conséquences, le découpage épistémique et le statut d'alignement.

### Étape 5 : Implémentation Physique & Multi-Gates ("Lint is a Floor")
1. Effectuer les modifications de code nécessaires sous `src/` (dans le respect de l'exception de développement mLoop).
2. Valider selon la séquence en entonnoir Multi-Gates :
   - *Gate Déterministe* : Linter, tests unitaires et vérification de conformité.
   - *Gate Analytique Qualitative* : Revue de fond Sentinel / Rubber-Duck (zéro score de linter mécanique).
3. Exécuter la commande d'auto-calibration :
   `python src/swarm.py calibrate --project mLoop`
4. Mettre à jour `task.md` et `walkthrough.md`.

