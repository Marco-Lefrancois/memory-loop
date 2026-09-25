---
story_id: MLOOP-178-BE
dossier_status: VALIDATED
created_at: 2026-09-23T15:08:56Z
updated_at: 2026-09-23T15:08:56Z
sources_hashes:
  source_1: epic17_prioritization_matrix
  source_2: modular_extraction_protocol
---

# Dossier de Preuves Documentaires & Cadrage — `MLOOP-178-BE` (Extraction Modulaire de src/loop_mem/db.py — Couche SQLite (BR=20))

> **Titre Fonctionnel Pur** : Extraction Modulaire de src/loop_mem/db.py — Couche SQLite (BR=20)  
> **Epic Jira** : `EPIC-17-MODULAR-REFACTORING` (Extraction Modulaire RULE-AST-01)  
> **Couche** : `backend`  
> **Récit Précédent / Dépendances** : [`MLOOP-172-BE.md`](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-172-BE.md)

---

### 1. Sources Physiques & Maquettes SSOT (Liens Directs Cliquables)

| Source SSOT | Nature du Document | Lien Repo Local |
| :--- | :--- | :--- |
| **Maquette Principale** | — | *N/A - Composant Headless* |
| **Cible d'extraction** | Code source monolithique | [`src/loop_mem/db.py`](file:///C:/Memory%20Loop/src/loop_mem/db.py) |
| **Protocole SSOT** | Règle d'extraction modulaire | [MODULAR_EXTRACTION_PROTOCOL.md](file:///C:/Memory%20Loop/standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md) |
| **Matrice priorisation** | Blast radius & ordre Lot | [epic17_prioritization_matrix.md](file:///C:/Memory%20Loop/Projects/mLoop/memory/evidence/epic17_prioritization_matrix.md) |
| **Gabarit dossier** | Template officiel | [dossier_de_preuves_template.md](file:///C:/Memory%20Loop/standards/blueprints/dossier_de_preuves_template.md) |

> *Note Headless* : Récit de refactoring modulaire 100% headless — aucune interface visuelle, le code source physique `src/loop_mem/db.py` est la source principale.

---

### 1.1 Matrice de Résolution des Conflits de Sources

| Conflit Identifié | Source A | Source B | Décision Retenue |
| :--- | :--- | :--- | :--- |
| *N/A — zéro conflit de sources détecté* | — | — | — |

---

### 2. Extraits Verbatim Sourcés (Passage-Level Grounding)

> NOTE
**Extrait 1 — Monolithe couche SQLite 956 lignes**  
**Source** : [`src/loop_mem/db.py`](file:///C:/Memory%20Loop/src/loop_mem/db.py)  
*« Le fichier src/loop_mem/db.py pèse 956 lignes (36.6 Ko) avec un blast radius de 20 callers uniques — violation RULE-AST-01 sur le module de persistance SQLite central de mLoop (schéma, CRUD observations, lexicon, FTS search). »*  
➔ **Fait établi** : 956L, 36.6 Ko, BR=20 callers, 4 familles identifiées (connection, observations, lexicon, search)..

> NOTE
**Extrait 2 — Contrainte ADR-0369 context managers**  
**Source** : [`standards/adr-system/0369`](file:///C:/Memory%20Loop/standards/adr-system/0369)  
*« L'ADR-0369 interdit formellement de retourner une connexion SQLite nue à l'appelant (L46-47) : 100% des accès doivent être encapsulés dans des blocs with sqlite3.connect / with get_observation_db_session — toute connexion ouverte hors context manager est une violation bloquante. »*  
➔ **Fait établi** : 100% accès SQLite via context manager, zéro connexion nue retournée (ADR-0369 L46-47)..

> NOTE
**Extrait 3 — Legacy _get_observation_conn à supprimer**  
**Source** : [`src/loop_mem/db.py`](file:///C:/Memory%20Loop/src/loop_mem/db.py)  
*« La fonction legacy _get_observation_conn a 0 caller en production (seul usage = test de dépréciation test_python_senior_standards.py:L178) — décision Q5-A : supprimer à l'extraction et migrer le test vers un assert symbole absent du shim. »*  
➔ **Fait établi** : 0 caller production, suppression à l'extraction, test migré en assert symbole absent..

---

### 3. Schéma de Données & Tables Clés

Pas d'entité transactionnelle : récit purement structurel (refactoring modulaire), zéro schéma DB modifié.

---

### 4. Contrats Déclaratifs Cibles

* **Backend** : `N/A - Exemption ADR-0319` — aucune route HTTP n'est consommée ni exposée. Exemption déclarée avec `OQ-178` + `[API de soumission à definir]`.
* **Contrat d'import (shim)** : `from src.loop_mem.db import *` résout tous les symboles publics historiques sans `ImportError`.
* **Plafond** : chaque sous-module ≤ 300 L / 15 Ko (RULE-AST-01 PASS via `code-check --file`).

---

### 5. Evaluation de la Frontiere Active

#### CAS A — Arbitrages tranches en Grill-Me 1:1 : Decisions Consignees

| Question Grill | Decision Arbitree |
| :--- | :--- |
| Q1 — Frontière connection vs queries | Option A (4 modules) — _db_connection + _db_observations + _db_lexicon + _db_search |
| Q3 — Rollback BR=20 | reprise macro Q3 — BR=20 ≥ 20, arbitrage humain obligatoire |
| Q5 — Legacy _get_observation_conn | Option A (supprimer) — 0 caller production, ADR-0369 interdit le pattern |

> **Frontiere close** — toutes les questions d'arbitrage ont ete tranchees en session Grill-Me 1:1 contradictoire (frontiere epuisee), puis approuvees par l'humain (batch APPROVE 2026-09-23). Zero question ouverte residuelle.
