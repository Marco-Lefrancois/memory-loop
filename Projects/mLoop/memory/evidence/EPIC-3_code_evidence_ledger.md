# 📜 Code Evidence Ledger (CEL) — Épopée EPIC-3-SAFETY-GOVERNANCE (Complémentaire)

**Projet** : `mLoop`  
**Phase** : `STAGE_3_BUILD`  
**Porte Active** : `Gate 3 (DoD)`  
**Auteurs** : Marco (Architecte Propriétaire), Lead Architect (Antigravity)  
**Date de Scellement** : 2026-09-19T20:43:00+00:00  
**Statut Épistémique** : `VERIFIED_DETERMINISTIC`  

---

## 1. Cartographie des Empreintes Cryptographiques (SHA-256)

| Fichier Source / Test | Empreinte SHA-256 | Lignes | Violations AST |
| :--- | :--- | :---: | :---: |
| `src/bridges/story_guard.py` | `81c16290aa70dbed7ae27fc4d33dc1f4aab4010821f36ac0040cdecf6d4fbca6` | 64 | 0 (Conforme ADR-0202) |
| `src/pipelines/rho_optimizer.py` | `203175ef7a960db87dca990dd560fa95b8db8dc4adf5b31b058178baf1cb97a7` | 252 | 0 (Conforme ADR-0202) |
| `src/pipelines/rho_registry.py` | `3729551eedfdcc62af587fc41402157f5dffb052500a2832e2bf349b7134e11b` | 82 | 0 (Conforme ADR-0202) |
| `tests/test_story_guard.py` | `01864b06159f2261070f68f1bc51f68427623e6dd86b15e34f64a8667b53a37d` | 98 | - (Pytest Vert) |
| `tests/test_rho_optimizer.py` | `aee4bb1297d03e018e2c5030057fcb5ca4ef4995ccba7da4383d0c94321c65d6` | 85 | - (Pytest Vert) |

---

## 2. Triangulation des 4 Piliers Gherkin

### Pilier 1 — Chemin Nominal
- **Bloc CEL-020-001** (`src/bridges/story_guard.py` : `validate_story_state`)  
  *Preuve* : `tests/test_story_guard.py::test_story_guard_nominal_authorized_file` (PASS).  
  *Règle* : Autorisation garantie des écritures de fichiers déclarés dans le Story Constraint Contract (SCC).
- **Bloc CEL-023-001** (`src/pipelines/rho_registry.py` : `record_rejected_hypothesis`)  
  *Preuve* : `tests/test_rho_optimizer.py::test_record_and_get_rejected_hypothesis` (PASS).  
  *Règle* : Enregistrement immuable des hypothèses architecturales rejetées dans `rho_impact.yaml`.

### Pilier 2 — Exceptions & Rejets Métier
- **Bloc CEL-020-002** (`src/bridges/story_guard.py` : `validate_story_state`)  
  *Preuve* : `tests/test_story_guard.py::test_story_guard_rejects_unauthorized_file` (PASS).  
  *Règle* : Interception immédiate avec sortie d'erreur (`sys.exit(1)`) de toute tentative de modification hors périmètre SCC.
- **Bloc CEL-023-002** (`src/pipelines/rho_optimizer.py` : `optimize_rho`)  
  *Preuve* : `tests/test_rho_optimizer.py::test_optimize_rho_creates_rule` (PASS).  
  *Règle* : Détection des doublons et prévention de la dérive de règles redondantes.

### Pilier 3 — Résilience & Mode Dégradé
- **Bloc CEL-020-003** (`src/bridges/story_guard.py` : `validate_story_state`)  
  *Preuve* : `tests/test_story_guard.py::test_story_guard_bypass_when_no_components_declared` (PASS).  
  *Règle* : Tolérance opérationnelle et avertissement si la story active n'impose aucune contrainte SCC.
- **Bloc CEL-023-003** (`src/pipelines/deterministic_checks.py` : `classify_anomaly`)  
  *Preuve* : `tests/test_rho_optimizer.py::test_optimize_rho_compact_strings_bifurcation` (PASS).  
  *Règle* : Bifurcation déterministe automatique des anomalies mécaniques (placeholders, compaction de commentaires) vers `standards/linters/deterministic_rules.json` pour préserver le budget de tokens LLM.

### Pilier 4 — UX & Observabilité
- **Bloc CEL-023-004** (`src/pipelines/rho_optimizer.py` : `dream_collector`)  
  *Preuve* : Traçabilité des statuts `TOMBSTONE` dans `rho_rules.yaml` lors de l'exécution nocturne.
  *Règle* : Observabilité continue et hygiène anti-amnésie sans corruption d'état.
