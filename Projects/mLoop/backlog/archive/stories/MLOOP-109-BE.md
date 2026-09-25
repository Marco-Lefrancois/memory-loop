---
id: MLOOP-109-BE
jira_key: ""
epic_key: EPIC-10-SOVEREIGN-EXCELLENCE
type: Refactoring
title: "Découpage Modulaire de herdr_adapter.py & Alignement RULE-AST-03 (Popen)"
origin: "SPEC_SLICING"
source_ref: "Intégration workers multi-CLI (registre worker_runtimes, 2026-09-20)"
macro_size: "M"
status: SHIPPED
grill_me: PENDING
invest_score: 0/6
layer: backend
blocked_by: []
created_at: "2026-09-20"
---

# 📖 MLOOP-109-BE : Découpage Modulaire de herdr_adapter.py & Alignement RULE-AST-03 (Popen)

## 1. Intention Métier (User Story)
**En tant que** Ingénieur Plateforme / Maintainer mLoop,  
**je veux** scinder `src/core/herdr_adapter.py` (993L / 42 Ko) en modules restreints sous les plafonds ADR-0202 et lever le faux positif `RULE-AST-03` sur `subprocess.Popen`,  
**afin de** rétablir la conformité du cœur d'orchestration Herdr et débloquer le garde-fou pré-commit (MLOOP-105-BE) pour toute évolution future de ce module.

---

## 2. Origine & Cadrage Avant-Projet
- **Document Source** : Chantier « Runtimes Workers Pluggables Multi-CLI » — 4 commits : `b2830bd` (registre SSOT + façade Cline + sonde), `aba3d7a` (routage déclaratif adaptateur), `6ca81d0` (résolution binaire npm dual-topologie `exe`/`cmd`), `9248b11` (court-circuit `pane run` déterministe pour shims npm). Validation indépendante (worker Cline `glm-5.3-flash`, mission read-only) sur **HEAD = `9248b11`** : verdict `PASS_WITH_RESERVES`, 44/44 tests, 3/3 code-check 0 violation, contrat de flags conforme — cf. `memory/worker_MLOOP-109-BE_validation.md`
- **Hypothèse de Chiffrage Retenue** : dette mesurée au 2026-09-20 — `herdr_adapter.py` = 993L / 41 989 o pour un plafond strict de 300L / 15 360 o (ADR-0202) ; baseline HEAD = **4 violations** (2× RULE-AST-01 taille + RULE-AST-03 L162 + RULE-AST-04 L312), version courante = **3 violations** (RULE-AST-04 corrigée, aucune régression introduite)
- **Enveloppe Macro Estimée** : M (fourchette de 2-3 jours)

---

## 3. Périmètre Sommaire
### In-Scope (Macro)
- Découpage de `src/core/herdr_adapter.py` (993L) par responsabilité : primitives de volets (workspace/pane/PTY), cycle de vie des agents, orchestration worker (spawn/harvest/cleanup), assainissement des zombies — en préservant l'API publique `HerdrAdapter` (13 tests `tests/test_herdr_adapter.py` au vert).
- Isolation du bootstrap du daemon (auto-heal, `subprocess.Popen` détaché) dans un module dédié `src/core/herdr_daemon.py` (bloc L122-203, ~82L), avec collaborateur injecté typé `Protocol` (ADR-0369 Standard 1).
- Refinement déterministe de `RULE-AST-03` dans `src/core/ast_checker.py` : reconnaître une attente bornée (`proc.wait(timeout=…)` / `proc.communicate(timeout=…)`) sur le résultat d'un `subprocess.Popen` — TDD Red-Green sur `tests/test_ast_checker.py` (9 tests existants préservés).

### Out-of-Scope (Macro)
- `src/commands/handlers/*` (périmètre de MLOOP-106-BE) et `src/utils/*` (périmètre de MLOOP-101-BE, livré).
- Refactorisation du pipeline worker (`src/pipelines/worker_pipeline.py`).
- Ajout de nouveaux runtimes CLI au registre (extension trivialement couverte par `src/core/worker_runtimes.py`).

---

## 4. Critères de Succès Préliminaires
- [ ] `python src/swarm.py code-check --file` → PASS (0 violation) sur 100% des modules issus du découpage.
- [ ] Garde-fou pré-commit MLOOP-105-BE : un commit touchant `src/core/herdr_adapter.py` passe **sans** `MLOOP_SKIP_HOOKS`.
- [ ] Non-régression : `tests/test_herdr_adapter.py` + `tests/test_ast_checker.py` + `tests/test_worker_runtimes.py` au vert ; `doctor --agents` et `vibe-check` inchangés (19/19).

---

## 5. Zones d'Ombre & Questions pour la Session Grill-Me 1:1
> [!IMPORTANT]
> *Ces questions constituent l'ordre du jour obligatoire de la session contradictoire Grill-Me 1:1.*

- ❓ OQ-1 : La modification de `RULE-AST-03` relève-t-elle de la maintenance corrective (faux positif démontré : l'API `Popen` n'accepte aucun paramètre `timeout`) ou d'un ADR à part entière au titre d'ADR-0376 (modification non auditée du cœur) ?
- ❓ OQ-2 : Granularité et nommage des modules cibles (4 sous-modules par responsabilité vs mixins héritées par `HerdrAdapter`) ?
- ❓ OQ-3 : Faut-il aligner `src/bridges/mcp_crawler.py` (L38, `subprocess.Popen` non borné — second site du même faux positif) dans le même lot ?
- ❓ OQ-4 : Le bypass souverain `MLOOP_SKIP_HOOKS=1` (utilisé le 2026-09-20 pour indexer le routage multi-CLI de ce fichier, dette préexistante prouvée) doit-il être tracé dans un journal d'audit des contournements de garde-fou ?
- ❓ OQ-5 : **Nom fantôme & échec de harvest** (constaté E2E le 2026-09-20) : après un spawn par fallback `pane run`, le renommage Herdr (`agent rename`) ne s'applique pas (échec asynchrone) → `worker-harvest --story <ID>` échoue en `agent_not_found` alors que le worker a réellement produit son livrable. Faut-il (a) ré-essayer le rename avec vérification active, (b) faire résoudre le harvest par `pane_id`, ou (c) consigner la cible (nom + pane) dans le sidecar de statut au spawn ?
- ❓ OQ-6 : **Fail-fast sur `--kind` inconnu** : aujourd'hui un kind non enregistré retombe silencieusement sur le repli hérité (`--dangerously-skip-permissions` + binaire brut). Faut-il échouer explicitement (argparse `choices` dérivé de `WORKER_RUNTIMES`) au risque de casser un usage legacy ?
