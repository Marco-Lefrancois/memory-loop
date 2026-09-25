---
id: MLOOP-174-BE
jira_key: ''
epic_key: EPIC-17-MODULAR-REFACTORING
type: refactor
title: Extraction Modulaire de src/core/lifecycle.py — Gates & Transitions d'État
  (BR=8)
origin: SPEC_SLICING
source_ref: 'EPIC-17 · epic17_prioritization_matrix.md · Rang #4 BR'
macro_size: M
status: DONE_TESTED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by:
- MLOOP-172-BE
created_at: '2026-09-23'
grilled_at: '2026-09-23'
grill_decisions_ref: micro-grill 174 Q1-Q5 (Q2 micro B, Q1/Q3/Q4 pré-résolus Search-Before-Ask,
  Q5 reprise macro Q2)
approved_at: '2026-09-23'
approved_by: humain (go explicite batch APPROVE 173/174/175/176/178/179)
ttl_cycles: 4
---

# Extraction Modulaire de src/core/lifecycle.py — Gates & Transitions d'État (BR=8)

## 1. Intention Métier (User Story)

**En tant qu'** ingénieur du framework mLoop,
**je veux** découper `src/core/lifecycle.py` (852 L, BR=8) en sous-modules cohérents inférieurs à 300 L chacun, en suivant le cas général §2 du protocole d'extraction modulaire,
**afin de** résorber la violation RULE-AST-01 sur le module de gouvernance du cycle de vie sans altérer les 10 callers ni les gates de transition d'état qui en dépendent.

---

## 2. Origine & Cadrage Avant-Projet

- **Document Source** : `memory/evidence/epic17_prioritization_matrix.md` (Réf : Rang #4, BR=8, Lot 1, 38.6 Ko)
- **Protocole SSOT** : `standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md` — **Cas général §2 (découpe par famille de responsabilités)**
- **Hypothèse de Chiffrage Retenue** : Découpe en 3 familles (transitions d'état, gates bloquants, reporting lifecycle) + shim de ré-export ; BR=8 callers, risque modéré mais module critique car pilote du cycle de vie.
- **Enveloppe Macro Estimée** : M (fourchette de 1 à 2 jours)

---

## 3. Périmètre Sommaire

### In-Scope (Macro)
- Lecture et cartographie de `src/core/lifecycle.py` (852 L, 38.6 Ko) : identification des familles (machine à états, gates bloquants C1-C12, reporting & archivage).
- Création du package `src/core/lifecycle/` avec sous-modules thématiques, chacun ≤ 300 L / 15 Ko.
- Shim de ré-export `src/core/lifecycle.py` garantissant la rétrocompatibilité des 10 callers.
- Application du pattern §2 (cas général) : étapes 0 à 8 du protocole (diagnostic, cartographie, création package, déplacement familles, shim, fumée, tests, archivage).
- Check fumée imports + suite tests verte post-extraction.
- Mise à jour de `epic17_prioritization_matrix.md`.

### Out-of-Scope (Macro)
- Modification des 10 callers (shim transparent).
- Enrichissement fonctionnel des gates ou ajout de nouvelles transitions d'état.
- Autres fichiers Lot 1 (`state.py`, `_registry.py`) — traités dans MLOOP-173-BE et MLOOP-175-BE.

---

## 4. Critères de Succès Préliminaires

- [ ] Chaque sous-module du package `src/core/lifecycle/` passe `code-check --file` : ≤ 300 L, ≤ 15 Ko.
- [ ] Shim `src/core/lifecycle.py` opérationnel : `python -c "from src.core.lifecycle import *"` sans erreur.
- [ ] Check fumée vert : zéro symbole non résolu détecté.
- [ ] Suite tests inchangée : `pytest tests/ -x -q` — N_après ≥ N_avant PASS, 0 FAIL.
- [ ] Plan archivé sous `memory/plan/implementation_plan_MLOOP-174-BE.md` avec checklist §4 complétée.

---

## 5. Décisions Grill-Me 1:1 (Frontière Épuisée 2026-09-23)

> [!DONE]
> *Session contradictoire 1:1 clôturée — 5/5 questions tranchées (Q2 micro ici ; Q1/Q3/Q4 pré-résolus Search-Before-Ask ; Q5 reprise macro Q2).*
> *Récit éligible conversion Palier 2 après validation wikifix/rubber-duck et approbation humaine.*

- ✅ **Q1 — Dépendance sur state.py → pré-résolu Search-Before-Ask (F1)** : **`lifecycle.py` n'importe PAS `state.py`** (zéro `from src.state` / `LoopState`). Seuls imports top-level : stdlib + pydantic + `get_logger` ; 2 lazy imports (`gate4_validator` L592, `herdr_adapter` L599). `blocked_by` 173 retiré du frontmatter — indépendance technique confirmée.
- ✅ **Q2 — Frontière gates vs transitions + volume Manager → Option B (4 modules + mixins)** : vrai problème = `ProjectLifecycleManager` **633L** (85% du fichier). Découpe : `_lc_models.py` (`ProjectLifecycleStage` + `GateApprovalRecord` + `ProjectLifecycleState` + `STAGE_NAMES` + `GATE_DEFINITIONS` ~60L) · `_lc_transitions.py` (`TransitionsMixin` : load/save/init/can_execute ~200L) · `_lc_gates.py` (`GatesMixin` : approve_gate/reporting ~250L) · `_lc_manager.py` (`class ProjectLifecycleManager(TransitionsMixin, GatesMixin)` thin ~80L) + shim. Pattern **identique à 173**, API `manager.<méthode>()` intacte pour les 10 callers. Options A (3 modules, `_lc_gates` frôle 300L) et C (2 familles plates, >300L) rejetées.
- ✅ **Q3 — Effets de bord à l'import → pré-résolu Search-Before-Ask (F3)** : **pas de `_lifecycle_init_effects.py`** (sur-ingénierie) — zéro `re.compile`/`basicConfig`/`open()` top-level ; tous les `open()` sont dans des méthodes `with` (ADR-0369 OK).
- ✅ **Q4 — Couverture tests → pré-résolu Search-Before-Ask** : **8/10 méthodes du Manager couvertes par nom** (80% ≥ seuil) + 44 tests dédiés répartis sur 8 fichiers (`test_project_lifecycle`, `test_lifecycle_persistence`, `test_lifecycle_gate4`, `test_lifecycle_logging`, `test_lifecycle_zombie_reap`, `test_phase_1_ingest_gate`, `test_premature_cleanup_safety`, `test_vibe_check_lifecycle`, `test_worker_spawn_lifecycle_gating`). 2 méthodes privées non couvertes (`_compute_file_sha256`, `_find_qa_certification_report`) — non bloquant pour l'extraction structurelle.
- ✅ **Q5 — Séquençage Lot 1 → reprise macro Q2 Option A** : position **4/5** dans la séquence Beachhead `state(78) → db(20) → sync(10) → lifecycle(8) → _registry(3)`, un worker à la fois, smoke check vert entre chaque ; Lot 3 (176/177) gelé. F1 confirme l'indépendance technique de state — le séquençage est une discipline de process, pas un blocage de code.

---

## Règles d'affaires

- **Plafond modulaire absolu** : chaque sous-module de `src/core/lifecycle/` doit rester sous 300 lignes et 15 Ko (ADR-0202 / RULE-AST-01).
- **Rétrocompatibilité stricte des callers** : les 10 fichiers appelants ne sont jamais modifiés — le shim `src/core/lifecycle.py` rend tout import historique (`ProjectLifecycleManager`, `GATE_DEFINITIONS`, `STAGE_NAMES`, `ProjectLifecycleStage`) résoluble sans `ImportError`.
- **Pattern mixins (décision Q2-B)** : `TransitionsMixin` + `GatesMixin` attachées à `ProjectLifecycleManager` — même pattern éprouvé sur MLOOP-173-BE, zéro modification d'API publique.
- **Séquençage Beachhead** : extraction de `lifecycle` uniquement à la position 4/5 après clôture de `state`, `db` et `sync` (macro Q2) — indépendance technique de state prouvée par F1.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Extraction Modulaire Mixins (Q2-B)
- [ ] Package `src/core/lifecycle/` créé : `_lc_models.py`, `_lc_transitions.py`, `_lc_gates.py`, `_lc_manager.py` — chacun ≤ 300 L / 15 Ko
- [ ] Mixins `TransitionsMixin` + `GatesMixin` attachées à `ProjectLifecycleManager` — API `manager.<méthode>()` intacte pour les 10 callers
- [ ] Symboles publics résolus via shim : `ProjectLifecycleManager`, `GATE_DEFINITIONS`, `STAGE_NAMES`, `ProjectLifecycleStage`

#### 2. Rétrocompatibilité & Non-Régression
- [ ] Shim `src/core/lifecycle.py` résout les imports historiques sans `ImportError` (10 callers inchangés)
- [ ] Check fumée vert + `pytest tests/ -x -q` : N_après PASS ≥ N_avant PASS, 0 FAIL
- [ ] Séquençage Beachhead position 4/5 — extraction uniquement après clôture de `state`, `db`, `sync` (macro Q2)

### Admission of Limits
- Avertissements rubber-duck génériques (timeout réseau, expiration de session, anti-rebond) hors domaine : module de gouvernance interne headless — transitions et gates couverts par les piliers Gherkin.

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API
> **Exemption déclarée (ADR-0319)** : refactoring modulaire interne de `src/core/lifecycle.py` — **aucune route HTTP n'est consommée ni exposée**. Toute route découverte en cours d'implémentation fera l'objet d'une question ouverte `OQ-174` avec la mention `[API de soumission à définir]` — jamais inventée (Zéro Fausse Route, AGENTS.md).

| Contrat | Engagement |
|:---|:---|
| `from src.core.lifecycle import *` (shim) | Rétrocompatibilité 10 callers, zéro modification caller |
| `ProjectLifecycleManager` (mixins) | Transitions + gates inchangés (API publique gelée) |
| `code-check --file` sous-modules | ≤ 300 L / 15 Ko each (RULE-AST-01 PASS) |

---

## Scénarios de test

### Pilier 1 — Nominal (Happy path)
```gherkin
Scénario : Découpage modulaire transparent du cycle de vie projet
  Étant donné le package "src/core/lifecycle/" subdivisé en 4 modules avec mixins <= 300 lignes
  Quand un appelant importe "from src.core.lifecycle import ProjectLifecycleManager, GATE_DEFINITIONS, STAGE_NAMES"
  Alors tous les symboles publics sont résolus sans régression ni avertissement
```

### Pilier 2 — Exceptions (Cas d'erreur)
```gherkin
Scénario : Détection d'une transition de gate illicite après extraction
  Étant donné un projet dont un gate est refusé
  Quand "approve_gate" tente une avance de stage non autorisée
  Alors l'exception typée est levée avec message contextuel identique à l'avant-extraction
```

### Pilier 3 — Résilience (Réseau / Timeout / Mode dégradé)
```gherkin
Scénario : Persistance d'état lifecycle résistante à la corruption
  Étant donné un fichier "lifecycle_state.json" corrompu
  Quand "get_state" le charge via le mixin transitions
  Alors l'erreur est logguée avec exc_info et un backup ".corrupt.*" est émis sans crash
```

### Pilier 4 — UX / Accessibilité / État vide
```gherkin
Scénario : Initialisation sur un projet vierge
  Étant donné un chemin de projet sans "memory/lifecycle_state.json"
  Quand "init_lifecycle" est appelé pour la première fois
  Alors l'état par défaut STAGE_1_INGEST est créé sans message parasite ni effet de bord d'import
```
