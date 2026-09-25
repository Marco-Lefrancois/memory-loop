---
story_id: MLOOP-173-BE
dossier_status: VALIDATED
created_at: 2026-09-23T15:08:56Z
updated_at: 2026-09-23T15:08:56Z
sources_hashes:
  source_1: epic17_prioritization_matrix
  source_2: modular_extraction_protocol
---

# Dossier de Preuves Documentaires & Cadrage — `MLOOP-173-BE` (Extraction Modulaire de src/state.py — Singleton d'État Partagé (BR=78))

> **Titre Fonctionnel Pur** : Extraction Modulaire de src/state.py — Singleton d'État Partagé (BR=78)  
> **Epic Jira** : `EPIC-17-MODULAR-REFACTORING` (Extraction Modulaire RULE-AST-01)  
> **Couche** : `backend`  
> **Récit Précédent / Dépendances** : [`MLOOP-172-BE.md`](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-172-BE.md)

---

### 1. Sources Physiques & Maquettes SSOT (Liens Directs Cliquables)

| Source SSOT | Nature du Document | Lien Repo Local |
| :--- | :--- | :--- |
| **Maquette Principale** | — | *N/A - Composant Headless* |
| **Cible d'extraction** | Code source monolithique | [`src/state.py`](file:///C:/Memory%20Loop/src/state.py) |
| **Protocole SSOT** | Règle d'extraction modulaire | [MODULAR_EXTRACTION_PROTOCOL.md](file:///C:/Memory%20Loop/standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md) |
| **Matrice priorisation** | Blast radius & ordre Lot | [epic17_prioritization_matrix.md](file:///C:/Memory%20Loop/Projects/mLoop/memory/evidence/epic17_prioritization_matrix.md) |
| **Gabarit dossier** | Template officiel | [dossier_de_preuves_template.md](file:///C:/Memory%20Loop/standards/blueprints/dossier_de_preuves_template.md) |

> *Note Headless* : Récit de refactoring modulaire 100% headless — aucune interface visuelle, le code source physique `src/state.py` est la source principale.

---

### 1.1 Matrice de Résolution des Conflits de Sources

| Conflit Identifié | Source A | Source B | Décision Retenue |
| :--- | :--- | :--- | :--- |
| *N/A — zéro conflit de sources détecté* | — | — | — |

---

### 2. Extraits Verbatim Sourcés (Passage-Level Grounding)

> NOTE
**Extrait 1 — État monolithique de state.py**  
**Source** : [`src/state.py`](file:///C:/Memory%20Loop/src/state.py)  
*« Le fichier src/state.py est un monolithe de 770 lignes physiques (31.1 Ko) contenant les exceptions, enums, modèles Pydantic, la classe LoopState avec ses méthodes d'accès et de sérialisation, ainsi que le SavepointManager — totalisant un blast radius de 78 callers uniques dans le codebase. »*  
➔ **Fait établi** : 770 lignes, BR=78, 3 familles de responsabilités identifiées (noyau, accesseurs, sérialisation)..

> NOTE
**Extrait 2 — Pattern Singleton obligatoire**  
**Source** : [`standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md`](file:///C:/Memory%20Loop/standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md)  
*« Le cas spécial §3.2 du protocole d'extraction modulaire impose que l'instance singleton d'état soit créée exactement une seule fois dans le module __init__.py du package, et que toute instanciation locale dans un sous-module soit formellement interdite pour éviter la désynchronisation d'instance partagée. »*  
➔ **Fait établi** : Singleton unique dans __init__.py, zéro instanciation locale autorisée (protocole §3.2)..

> NOTE
**Extrait 3 — Plafond modulaire RULE-AST-01**  
**Source** : [`standards/adr-system/0202`](file:///C:/Memory%20Loop/standards/adr-system/0202)  
*« L'ADR-0202 fixe un plafond strict de 300 lignes physiques et 15 kilo-octets par fichier module Python, sous peine de violation RULE-AST-01 détectée par code-check — applicable à chaque sous-module produit par l'extraction. »*  
➔ **Fait établi** : ≤300L / ≤15 Ko par sous-module, audit code-check --file obligatoire..

---

### 3. Schéma de Données & Tables Clés

Pas d'entité transactionnelle : récit purement structurel (refactoring modulaire), zéro schéma DB modifié.

---

### 4. Contrats Déclaratifs Cibles

* **Backend** : `N/A - Exemption ADR-0319` — aucune route HTTP n'est consommée ni exposée. Exemption déclarée avec `OQ-173` + `[API de soumission à definir]`.
* **Contrat d'import (shim)** : `from src.state import *` résout tous les symboles publics historiques sans `ImportError`.
* **Plafond** : chaque sous-module ≤ 300 L / 15 Ko (RULE-AST-01 PASS via `code-check --file`).

---

### 5. Evaluation de la Frontiere Active

#### CAS A — Arbitrages tranches en Grill-Me 1:1 : Decisions Consignees

| Question Grill | Decision Arbitree |
| :--- | :--- |
| Q1 — Frontière noyau vs accesseurs | Option A (3 modules) — _state_core + _state_accessors + _state_serializer |
| Q2 — Pattern d'attachement serializer | Option A (Mixin) — StateAccessorsMixin + StateSerializerMixin |
| Q3 — Effets de bord à l'import | Option A (pas de module dédié) — zéro side effect top-level |

> **Frontiere close** — toutes les questions d'arbitrage ont ete tranchees en session Grill-Me 1:1 contradictoire (frontiere epuisee), puis approuvees par l'humain (batch APPROVE 2026-09-23). Zero question ouverte residuelle.
