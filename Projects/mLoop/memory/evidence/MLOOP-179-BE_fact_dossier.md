---
story_id: MLOOP-179-BE
dossier_status: VALIDATED
created_at: 2026-09-23T15:08:56Z
updated_at: 2026-09-23T15:08:56Z
sources_hashes:
  source_1: epic17_prioritization_matrix
  source_2: modular_extraction_protocol
---

# Dossier de Preuves Documentaires & Cadrage — `MLOOP-179-BE` (Extraction Modulaire de src/pipelines/sync.py — Pipeline Sync (BR=10))

> **Titre Fonctionnel Pur** : Extraction Modulaire de src/pipelines/sync.py — Pipeline Sync (BR=10)  
> **Epic Jira** : `EPIC-17-MODULAR-REFACTORING` (Extraction Modulaire RULE-AST-01)  
> **Couche** : `backend`  
> **Récit Précédent / Dépendances** : [`MLOOP-172-BE.md`](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-172-BE.md)

---

### 1. Sources Physiques & Maquettes SSOT (Liens Directs Cliquables)

| Source SSOT | Nature du Document | Lien Repo Local |
| :--- | :--- | :--- |
| **Maquette Principale** | — | *N/A - Composant Headless* |
| **Cible d'extraction** | Code source monolithique | [`src/pipelines/sync.py`](file:///C:/Memory%20Loop/src/pipelines/sync.py) |
| **Protocole SSOT** | Règle d'extraction modulaire | [MODULAR_EXTRACTION_PROTOCOL.md](file:///C:/Memory%20Loop/standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md) |
| **Matrice priorisation** | Blast radius & ordre Lot | [epic17_prioritization_matrix.md](file:///C:/Memory%20Loop/Projects/mLoop/memory/evidence/epic17_prioritization_matrix.md) |
| **Gabarit dossier** | Template officiel | [dossier_de_preuves_template.md](file:///C:/Memory%20Loop/standards/blueprints/dossier_de_preuves_template.md) |

> *Note Headless* : Récit de refactoring modulaire 100% headless — aucune interface visuelle, le code source physique `src/pipelines/sync.py` est la source principale.

---

### 1.1 Matrice de Résolution des Conflits de Sources

| Conflit Identifié | Source A | Source B | Décision Retenue |
| :--- | :--- | :--- | :--- |
| *N/A — zéro conflit de sources détecté* | — | — | — |

---

### 2. Extraits Verbatim Sourcés (Passage-Level Grounding)

> NOTE
**Extrait 1 — Monolithe pipeline sync 542 lignes**  
**Source** : [`src/pipelines/sync.py`](file:///C:/Memory%20Loop/src/pipelines/sync.py)  
*« Le fichier src/pipelines/sync.py pèse 542 lignes (22.7 Ko) avec un blast radius de 10 callers — violation RULE-AST-01 sur le pipeline de synchronisation (docs, git wikis, hypergraphe, orchestration run_sync). »*  
➔ **Fait établi** : 542L, 22.7 Ko, BR=10 callers, 3 familles identifiées (docs, graph, run)..

> NOTE
**Extrait 2 — Hypothèse API Jira réfutée**  
**Source** : [`src/pipelines/jira/`](file:///C:/Memory%20Loop/src/pipelines/jira/)  
*« Recherche Search-Before-Ask : zéro API Jira dans sync.py — le client Jira vit dans src/pipelines/jira/ séparé avec httpx timeout=30.0. L'hypothèse de l'ébauche (_sync_jira) est réfutée ; découpe réelle = _sync_docs + _sync_graph + _sync_run. »*  
➔ **Fait établi** : F1 réfute hypothèse Jira — Jira = src/pipelines/jira/ httpx timeout=30.0, pas dans sync.py..

> NOTE
**Extrait 3 — Timeout réseau ADR-0369 déjà conforme**  
**Source** : [`src/pipelines/sync.py`](file:///C:/Memory%20Loop/src/pipelines/sync.py)  
*« Unique appel réseau de sync.py = subprocess.run(git pull, timeout=8) aux lignes 282-287 — déjà conforme ADR-0369 (timeout explicite). L'extraction doit conserver ce timeout tel quel, sans inventer de constantes JIRA_TIMEOUT_S/GIT_TIMEOUT_S (F1 : pas de Jira ici). »*  
➔ **Fait établi** : git pull timeout=8 L282-287 déjà ADR-0369, conservation inchangée à l'extraction..

---

### 3. Schéma de Données & Tables Clés

Pas d'entité transactionnelle : récit purement structurel (refactoring modulaire), zéro schéma DB modifié.

---

### 4. Contrats Déclaratifs Cibles

* **Backend** : `N/A - Exemption ADR-0319` — aucune route HTTP n'est consommée ni exposée. Exemption déclarée avec `OQ-179` + `[API de soumission à definir]`.
* **Contrat d'import (shim)** : `from src.pipelines.sync import *` résout tous les symboles publics historiques sans `ImportError`.
* **Plafond** : chaque sous-module ≤ 300 L / 15 Ko (RULE-AST-01 PASS via `code-check --file`).

---

### 5. Evaluation de la Frontiere Active

#### CAS A — Arbitrages tranches en Grill-Me 1:1 : Decisions Consignees

| Question Grill | Decision Arbitree |
| :--- | :--- |
| Q1 — Famille Git vs Jira vs hypergraphe | Option B (3 modules) — hypothèse Jira réfutée F1, _sync_docs + _sync_graph + _sync_run |
| Q3 — Rollback BR=10 | reprise macro Q3 — BR=10 < 20, autonomie worker |
| Q5 — Dépendances state/lifecycle | pré-résolu F4 — state top-level L6 (via 173), zéro import lifecycle |

> **Frontiere close** — toutes les questions d'arbitrage ont ete tranchees en session Grill-Me 1:1 contradictoire (frontiere epuisee), puis approuvees par l'humain (batch APPROVE 2026-09-23). Zero question ouverte residuelle.
