---
story_id: MLOOP-174-BE
dossier_status: VALIDATED
created_at: 2026-09-23T15:08:56Z
updated_at: 2026-09-23T15:08:56Z
sources_hashes:
  source_1: epic17_prioritization_matrix
  source_2: modular_extraction_protocol
---

# Dossier de Preuves Documentaires & Cadrage — `MLOOP-174-BE` (Extraction Modulaire de src/core/lifecycle.py — Gates & Transitions d'État (BR=8))

> **Titre Fonctionnel Pur** : Extraction Modulaire de src/core/lifecycle.py — Gates & Transitions d'État (BR=8)  
> **Epic Jira** : `EPIC-17-MODULAR-REFACTORING` (Extraction Modulaire RULE-AST-01)  
> **Couche** : `backend`  
> **Récit Précédent / Dépendances** : [`MLOOP-172-BE.md`](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-172-BE.md)

---

### 1. Sources Physiques & Maquettes SSOT (Liens Directs Cliquables)

| Source SSOT | Nature du Document | Lien Repo Local |
| :--- | :--- | :--- |
| **Maquette Principale** | — | *N/A - Composant Headless* |
| **Cible d'extraction** | Code source monolithique | [`src/core/lifecycle.py`](file:///C:/Memory%20Loop/src/core/lifecycle.py) |
| **Protocole SSOT** | Règle d'extraction modulaire | [MODULAR_EXTRACTION_PROTOCOL.md](file:///C:/Memory%20Loop/standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md) |
| **Matrice priorisation** | Blast radius & ordre Lot | [epic17_prioritization_matrix.md](file:///C:/Memory%20Loop/Projects/mLoop/memory/evidence/epic17_prioritization_matrix.md) |
| **Gabarit dossier** | Template officiel | [dossier_de_preuves_template.md](file:///C:/Memory%20Loop/standards/blueprints/dossier_de_preuves_template.md) |

> *Note Headless* : Récit de refactoring modulaire 100% headless — aucune interface visuelle, le code source physique `src/core/lifecycle.py` est la source principale.

---

### 1.1 Matrice de Résolution des Conflits de Sources

| Conflit Identifié | Source A | Source B | Décision Retenue |
| :--- | :--- | :--- | :--- |
| *N/A — zéro conflit de sources détecté* | — | — | — |

---

### 2. Extraits Verbatim Sourcés (Passage-Level Grounding)

> NOTE
**Extrait 1 — Monolithe ProjectLifecycleManager**  
**Source** : [`src/core/lifecycle.py`](file:///C:/Memory%20Loop/src/core/lifecycle.py)  
*« Le fichier src/core/lifecycle.py pèse 852 lignes (38.6 Ko) dont 633 lignes (85%) pour la seule classe ProjectLifecycleManager — un blast radius de 8 à 10 callers uniques pilotant les gates de transition du cycle de vie projet mLoop. »*  
➔ **Fait établi** : 852L total, Manager 633L, BR=8-10 callers, 2 lazy imports (gate4_validator, herdr_adapter)..

> NOTE
**Extrait 2 — Indépendance technique vis-à-vis de state.py**  
**Source** : [`src/core/lifecycle.py`](file:///C:/Memory%20Loop/src/core/lifecycle.py)  
*« Vérification par Search-Before-Ask : lifecycle.py n'importe PAS state.py (zéro from src.state / LoopState). Seuls imports top-level : stdlib + pydantic + get_logger ; 2 lazy imports internes uniquement — blocked_by 173 retiré du frontmatter. »*  
➔ **Fait établi** : F1 prouve zéro dépendance sur state.py — indépendance technique confirmée..

> NOTE
**Extrait 3 — Mixins éprouvés pattern 173**  
**Source** : [`MLOOP-173-BE`](file:///C:/Memory%20Loop/MLOOP-173-BE)  
*« Le pattern mixins (TransitionsMixin + GatesMixin) est directement repris de la décision grill Q2 de MLOOP-173-BE, déjà validé et éprouvé — assurant la rétrocompatibilité API manager sans modification des 10 callers existants. »*  
➔ **Fait établi** : Pattern identique à 173, API publique gelée, 10 callers inchangés..

---

### 3. Schéma de Données & Tables Clés

Pas d'entité transactionnelle : récit purement structurel (refactoring modulaire), zéro schéma DB modifié.

---

### 4. Contrats Déclaratifs Cibles

* **Backend** : `N/A - Exemption ADR-0319` — aucune route HTTP n'est consommée ni exposée. Exemption déclarée avec `OQ-174` + `[API de soumission à definir]`.
* **Contrat d'import (shim)** : `from src.core.lifecycle import *` résout tous les symboles publics historiques sans `ImportError`.
* **Plafond** : chaque sous-module ≤ 300 L / 15 Ko (RULE-AST-01 PASS via `code-check --file`).

---

### 5. Evaluation de la Frontiere Active

#### CAS A — Arbitrages tranches en Grill-Me 1:1 : Decisions Consignees

| Question Grill | Decision Arbitree |
| :--- | :--- |
| Q1 — Dépendance state.py | pré-résolu F1 — zéro import state, blocked_by 173 retiré |
| Q2 — Frontière gates vs transitions | Option B (4 modules + mixins) — _lc_models + _lc_transitions + _lc_gates + _lc_manager |
| Q5 — Séquençage Beachhead | position 4/5 — après state → db → sync |

> **Frontiere close** — toutes les questions d'arbitrage ont ete tranchees en session Grill-Me 1:1 contradictoire (frontiere epuisee), puis approuvees par l'humain (batch APPROVE 2026-09-23). Zero question ouverte residuelle.
