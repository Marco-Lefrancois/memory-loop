---
id: PLAN-MLOOP-101-BE
story_id: MLOOP-101-BE
status: APPROVED
harness: claude-code
created_at: 2026-09-20
---

# Plan d'Implémentation — Rénovation Modulaire du Résolveur Lexical et Grand Livre de Jetons

> **Objectif** : Ramener 100% de la couche `src/utils/` en conformité ADR-0202 (plafonds 300L / 15 Ko) et ADR-0369 (zéro exception silencieuse, zéro ressource hors context manager), via le découpage de `lexicon_resolver.py` (411L) et `token_ledger.py` (350L) en packages à façades intangibles, la purge de 11 blocs `except: pass` et 1 `sqlite3.connect` nu sur 6 modules d'audit, sans aucune régression fonctionnelle (16 sites d'import) ni dérive de performance (< 5 ms).
> **Source** : Grill-Me 1:1 du 2026-09-20 (5 arbitrages Option A) — dossier `memory/evidence/MLOOP-101-BE_fact_dossier.md` ; FRAMEWORK_STATE.md lu (baseline 257 violations, initialisation 2026-09-20).

---

## 1. User Review Required (Arbitrages & Points Clés)

> [!IMPORTANT]
> **Décisions structurantes nécessitant la confirmation humaine avant BUILD :**
> - **Conversion module → package** : `src/utils/token_ledger.py` (350L) est transformé en package `src/utils/token_ledger/` (suppression du module remplacée par `__init__.py` ré-exportant `TokenLedger`). L'import `from src.utils.token_ledger import TokenLedger` demeure inchangé pour les 7 consommateurs.
> - **Façades intangibles** : `SemanticLexiconResolver` (16 sites) et `TokenLedger` (7 sites) — signatures publiques gelées, aucune rupture d'API autorisée.
> - **Périmètre gelé** : handlers CLI (MLOOP-106-BE) et pipelines (MLOOP-107-BE) exclus — interdiction d'injecter des modifications hors `src/utils/` + tests.
> - **Promotion `READY_FOR_DEV`** : subordonnée à l'approbation de ce plan (Interdiction d'Auto-Approbation).

---

## 2. Questions Ouvertes (Open Questions)

> [!NOTE]
> **OQ-101 (résolue — exemption de traçabilité)** : Matrice des Contrats API non applicable — composant headless sans route REST/CTA `[API de soumission à définir]`, consignée dans la story (validation rubber-duck 2026-09-20, 0 bloquant).
> **Aucune OQ bloquante restante** : les 5 arbitrages de cadrage sont tranchés (§6 du dossier de preuves).

---

## 3. Modifications Proposées (Proposed Changes)

### A. Package Lexicon (découpage lexicon_resolver.py — 411L)

- #### `[NEW]` [`src/utils/lexicon/__init__.py`](file:///c:/Memory%20Loop/src/utils/lexicon/__init__.py)
  - **Intention** : Ré-exporter la façade `SemanticLexiconResolver` pour transparence totale des imports.
- #### `[NEW]` [`src/utils/lexicon/entity_matcher.py`](file:///c:/Memory%20Loop/src/utils/lexicon/entity_matcher.py)
  - **Intention** : Algorithmes de matching flou et détection des préfixes de tickets (~180L).
- #### `[NEW]` [`src/utils/lexicon/project_resolver.py`](file:///c:/Memory%20Loop/src/utils/lexicon/project_resolver.py)
  - **Intention** : Résolution contextuelle et tie-break managérial (~170L).
- #### `[MODIFY]` [`src/utils/lexicon_resolver.py`](file:///c:/Memory%20Loop/src/utils/lexicon_resolver.py)
  - **Intention** : Réduit en façade déléguante (< 300L, idéalement < 80L) — classe `SemanticLexiconResolver` conservée avec les 2 méthodes publiques, délégation interne aux sous-modules.

### B. Package Token Ledger (conversion token_ledger.py — 350L)

- #### `[NEW]` [`src/utils/token_ledger/__init__.py`](file:///c:/Memory%20Loop/src/utils/token_ledger/__init__.py)
  - **Intention** : Façade `TokenLedger` (conservant `calculate_cost`, `record_interaction`, `load_entries` ~145L) ré-exportée pour les 7 consommateurs.
- #### `[NEW]` [`src/utils/token_ledger/reporting.py`](file:///c:/Memory%20Loop/src/utils/token_ledger/reporting.py)
  - **Intention** : Report budgétaire `generate_report` (~100L, ex-L250-349).
- #### `[NEW]` [`src/utils/token_ledger/key_info.py`](file:///c:/Memory%20Loop/src/utils/token_ledger/key_info.py)
  - **Intention** : Sélection de clé LiteLLM `resolve_active_key_info` (~70L, ex-L62-130).
- #### `[DELETE]` [`src/utils/token_ledger.py`](file:///c:/Memory%20Loop/src/utils/token_ledger.py)
  - **Intention** : Le module est remplacé atomiquement par le package éponyme (l'import public reste stable).

### C. Audit Conformité ADR-0369 (6 modules, 11 sites)

- #### `[MODIFY]` 6 fichiers sous `src/utils/`
  - **Intention** : Remplacement de chaque `except: pass` par `logger.debug(..., exc_info=True, extra={...})` contextualisé — sites : `file_lock.py` (L72, L78, L154, L166), `context_guard.py` (L138), `opencode_meter.py` (L49, L117), `context_monitor.py` (L96), `lexical_guard.py` (L136, L142), `antigravity_meter.py` (L45).
  - **Correctif RULE-AST-02** : `opencode_meter.py` L143 — `sqlite3.connect` encapsulé dans un bloc `with` (Zero-Leak).
  - **Impact** : ligne par ligne, aucun changement de flux (zéro altération du format JSONL ni des seuils — Out-of-Scope respecté).

### D. Harnais de Vérification

- #### `[NEW]` [`tests/performance/test_utils_latency.py`](file:///c:/Memory%20Loop/tests/performance/test_utils_latency.py)
  - **Intention** : Arbitrage #4 — moyenne `time.perf_counter()` < 5 ms sur `resolve_project_alias` + `resolve_story_query`, et garde déterministe des plafonds 300L / 15 Ko sur les modules du périmètre.

## 4. Gestion des Risques & Rollback

| Risque Identifié | Impact Potentiel | Stratégie d'Atténuation / Rollback |
| :--- | :--- | :--- |
| **Rupture d'import lors de la conversion module → package** (`token_ledger`) | Élevé | Conversion atomique dans une seule passe ; rejouer la suite non-régression (4 fichiers) immédiatement après ; `git checkout -- src/utils/token_ledger.py` en rollback. |
| **Perte d'ordre d'initialisation** (imports au niveau module dans les sous-modules) | Moyen | Sous-modules sans état global : paramètres passés en arguments ; `import` de la façade testé par `python -c "from src.utils.token_ledger import TokenLedger"`. |
| **Régression de performance** sur le chemin chaud focus | Moyen | Harnais `tests/performance/test_utils_latency.py` (< 5 ms) en §5A ; échec = BUILD non clôturable. |
| **Fix `sqlite3.connect` modifiant par effet de bord la persistance** | Faible | Comportement inchangé (le contexte ne fait qu'assurer la fermeture) ; test token_ledger rejoué ; observation avant/après sur un run réel. |
| **Conflit parallèle sur MLOOP-100-BE** (sync_engine.py, 914L) | Faible | Fichiers disjoints ; le focus unique reste MLOOP-101-BE. |

---

## 5. Plan de Vérification & Recette (Triple Gate)

### A. Tests Automatisés
- [ ] Suite de non-régression :
  ```powershell
  python -m pytest tests/test_token_ledger.py tests/test_lexicon_project_resolver.py tests/test_lexicon_resolver_tiebreak.py tests/test_lexicon_resolve_story_prefix.py -v
  ```
- [ ] Harnais performance (Arbitrage #4) :
  ```powershell
  python -m pytest tests/performance/test_utils_latency.py -v
  ```
- [ ] Conformité déterministe (zéro violation attendue sur le périmètre) :
  ```powershell
  python src/swarm.py code-check --file src/utils/lexicon_resolver.py; python src/swarm.py code-check --file src/utils/token_ledger/__init__.py; python src/swarm.py code-check --file src/utils/file_lock.py; python src/swarm.py code-check --file src/utils/context_guard.py; python src/swarm.py code-check --file src/utils/opencode_meter.py; python src/swarm.py code-check --file src/utils/context_monitor.py; python src/swarm.py code-check --file src/utils/lexical_guard.py; python src/swarm.py code-check --file src/utils/antigravity_meter.py
  ```
- [ ] Gate structurelle (Gate C12 — Domain Sanity, exigence FRAMEWORK_STATE) :
  ```powershell
  python src/swarm.py struct-check --project mLoop --file MLOOP-101-BE.md
  ```
- [ ] Validité JSON de l'EvidencePack :
  ```powershell
  python -c "import json; json.load(open(r'Projects/mLoop/memory/evidence/MLOOP-101-BE_evidence.json', encoding='utf-8')); print('OK')"
  ```

### B. Vérifications Manuelles & Scénarios Clés
- [ ] **Scénario Nominal** : `python src/swarm.py focus --project mLoop --story MLOOP-105-BE.md` (à rejouer avec la vraie story cible en BUILD) — la résolution lexicale identifie le projet et le statut IN_ANALYZE persiste.
- [ ] **Scénario d'Exception / Résilience** : simulation d'un fichier de verrou corrompu → exception typée/journalisation explicite (Pilier 2), jamais de silence.
- [ ] **Scénario Performance** : moyenne < 5 ms confirmée par le harnais pytest (Arbitrage #4).

### C. Definition of Done (DoD)
- [ ] Tous les fichiers modifiés respectent ADR-0202 (≤ 300L / ≤ 15 Ko) et ADR-0369 (zéro `except: pass`, zéro ressource hors `with`).
- [ ] `code-check --file` PASS sur les 8 modules du périmètre.
- [ ] Façades `SemanticLexiconResolver` et `TokenLedger` : imports publics inchangés (vérifiés par la suite non-régression).
- [ ] Suite non-régression + harnais performance au vert.
- [ ] Archivage du plan dans `Projects/mLoop/memory/plan/implementation_plan_MLOOP-101-BE.md` (fait — ce fichier).
