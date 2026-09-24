# 📦 Pack de Compétences Agentiques Recommandées (Skills Starter Pack)

> **Document de bootstrapping automatisé pour Développeurs & Agents IA**  
> *Ce fichier contient le code source intégral des 6 compétences méthodologiques fondamentales mLoop.*

---

## 🤖 Instructions de Déploiement pour l'Agent IA (Bootstrap Prompt)

> [!TIP]
> **Développeur : copiez-collez l'instruction suivante à votre agent (OpenCode, Claude Code, Cursor, etc.) pour qu'il déploie ce pack en toute autonomie :**
> 
> ```text
> Lis attentivement le fichier "docs/guides/recommended_skills_pack.md". 
> Pour chaque compétence répertoriée (1 à 6), crée le dossier correspondant sous ".agents/skills/<nom-du-skill>/" ainsi que son fichier "SKILL.md" et son sous-dossier "references/" (le cas échéant) avec le contenu exact fourni dans les blocs de code.
> Ne modifie aucun séparateur YAML frontmatter.
> ```

---

## 🗂️ Sommaire du Pack

1. 🛡️ [**`constraint-driven-development`**](#1-constraint-driven-development) : Verrouille la barre de qualité (`CONSTRAINTS.md`) et empêche l'agent de tricher.
2. 🧪 [**`test-driven-development`**](#2-test-driven-development) : Cycle Red-Green-Refactor et reproduction de bogues par le test (Prove-It Pattern).
3. ✨ [**`code-simplification`**](#3-code-simplification) : Élagage du boilerplate IA sans altération du comportement.
4. 🧱 [**`incremental-implementation`**](#4-incremental-implementation) : Découpage des développements en tranches verticales atomiques et vérifiées.
5. 📐 [**`api-and-interface-design`**](#5-api-and-interface-design) : Conception d'interfaces stables, contrats d'abord et idempotence garantie.
6. 🧐 [**`doubt-driven-development`**](#6-doubt-driven-development) : Revue contradictoire et adversariale avant toute décision architecturale non triviale.

---

## 1. `constraint-driven-development`

Établit le barème de qualité du projet sous forme de contrat écrit (`CONSTRAINTS.md`) et empêche les agents de désactiver discrètement les vérifications (`@ts-ignore`, suppressions de tests, seuils rabaissés).

### Fichier A : `.agents/skills/constraint-driven-development/SKILL.md`
```markdown
---
name: constraint-driven-development
description: Establishes a project's quality bar as a written contract. Use when defining quality gates, coverage thresholds, or constraints in CONSTRAINTS.md to stop agents quietly lowering the shipping bar.
---

# Constraint-Driven Development

Establish an enforceable quality floor for the repository. Ground expectations in written mechanical gates rather than vague prose, preventing agents from quietly degrading standards.

## 1. Ground Truth & Repository Anchoring (SSOT & Evidence)

All quality thresholds must anchor directly to verifiable repository evidence (SSOT & evidence factuelle) :
- Quality architecture and project governance: consult [standards/blueprints/](standards/blueprints/) and [Projects/](Projects/).
- Automated test runs and coverage reports: inspect [tests/](tests/) and test execution metrics.
- Complete constraint schemas and gate definitions: see [references/constraints_templates.md](references/constraints_templates.md).

---

## 2. Core Execution Protocol

Follow these ordered steps sequentially:

### Étape 1 : Baseline Stack Detection
Inspect the repository before interviewing or asserting constraints:
- Detect package managers (`package.json`, `pyproject.toml`, `Cargo.toml`).
- Identify configured linters, type checkers, and test frameworks in `tests/`.
- Measure current baseline coverage and performance before proposing numbers.

### Étape 2 : Define the Universal Floor
Enforce immutable baseline rules that require zero configuration:
- Prohibit new suppression markers (`@ts-ignore`, `eslint-disable`, `# noqa`, `# type: ignore`).
- Prohibit unimplemented stubs (`throw new Error("Not implemented")`, empty `except: pass`).
- Prohibit deleting or skipping existing tests to artificially achieve green builds.

### Étape 3 : Register Enforced Thresholds in CONSTRAINTS.md
Write or update `CONSTRAINTS.md` at the project root with concrete verification commands:
- Every constraint must list the exact CLI command used to evaluate it.
- Include threshold ratchets: existing metrics must never degrade on new commits.

### Étape 4 : Verification & Gate Validation
- Execute all configured gate commands locally.
- Validate that the diff contains no silenced warnings or weakened threshold values.

---

## 3. Prescriptive Rules & Garde-fous

### Rules & Garde-fous (DO NOT / NEVER)
- **Règle 1** : DO NOT weaken numbers in `CONSTRAINTS.md` to make a failing build or PR pass.
- **Règle 2** : DO NOT add suppression comments to bypass type or lint errors without an approved exception entry.
- **Règle 3** : NEVER delete or comment out failing assertions or test files.
- **Règle 4** : DO NOT introduce aspirational constraints without specifying an executable command to verify them.

---

## 4. Gestion des erreurs, résilience et fallback

- **Comportement en cas d'erreur ou d'échec de vérification** : Si une commande de contrainte échoue, l'agent doit corriger le code source sous-jacent et non modifier les seuils de validation.
- **Fallback en l'absence d'outil installé** : Si un outil de mesure (ex: lighthouse ou semgrep) n'est pas installé dans l'environnement local, journaliser une alerte explicite et exécuter les vérifications statiques disponibles dans `tests/` sans masquer la dégradation.
- **Gestion des exceptions d'exécution** : Toute exception inattendue lors de l'exécution des hooks de contrainte doit lever une erreur bloquante et interrompre le pipeline de livraison.
```

### Fichier B : `.agents/skills/constraint-driven-development/references/constraints_templates.md`
```markdown
# Constraint-Driven Development Templates & References

This reference document accompanies `.agents/skills/constraint-driven-development/SKILL.md`.

## 1. Full CONSTRAINTS.md Template

```markdown
# Constraints

Last reviewed: YYYY-MM-DD

## Floor (Always Enforced, Zero Config)
- No new suppression comments: `@ts-ignore`, `eslint-disable`, `# noqa`, `# type: ignore`
- No unimplemented stubs: `throw new Error("Not implemented")`, empty `catch {}`
- No skipped or deleted tests without an explicit reason in commit message
- No plain-text secrets in source code
- This file does not get weakened to make a build pass

## Enforced Quality Gates

| Dimension | Rule | Checker Command | Execution Trigger |
|-----------|------|-----------------|-------------------|
| Types | Zero type errors | `tsc --noEmit` / `mypy .` | every edit |
| Lint | Zero linter errors | `ruff check .` / `biome check` | every edit |
| Secrets | Zero secret leaks | `gitleaks detect` | pre-commit |
| Coverage | Changed lines >= 80% | `pytest --cov` / `vitest` | task end, CI |
| Security | Zero high CVEs | `semgrep scan` / `osv-scanner` | CI |
| Performance | LCP <= 2.5s, CLS <= 0.1 | `lighthouse` | preview deploy |

## Exceptions Table

| ID | Rule Suppressed | Path | Justification | Owner | Expiration |
|----|-----------------|------|---------------|-------|------------|
| E1 | `no-explicit-any` | `src/legacy/` | Legacy migration tracker | @team | 2026-12-31 |
```
```

---

## 2. `test-driven-development`

Pilote le développement par les tests selon la boucle Red-Green-Refactor. Oblige à reproduire tout bogue signalé par un test défaillant avant d'écrire le moindre correctif (*Prove-It Pattern*).

### Fichier A : `.agents/skills/test-driven-development/SKILL.md`
```markdown
---
name: test-driven-development
description: Drives development with tests using the red-green-refactor loop. Use when implementing new logic, fixing bugs, or refactoring behavior to prove correctness with automated tests.
---

# Test-Driven Development

Write a failing test before writing production code. Tests are physical proof of correctness — code without tests is a liability.

## 1. Ground Truth & Repository Anchoring (SSOT & Evidence)

All test assertions must be rooted in verifiable repository standards (SSOT & evidence factuelle) :
- Architecture specifications and acceptance criteria: consult [standards/blueprints/](standards/blueprints/) and [Projects/](Projects/).
- Automated test suites: anchor directly to test files in [tests/](tests/) and test runner configurations.
- In-depth TDD patterns and bug reproduction templates: see [references/tdd_patterns.md](references/tdd_patterns.md).

---

## 2. Core Execution Protocol

Follow these ordered steps sequentially:

### Étape 1 : Stack Discovery & Tooling Check
Detect the repository's test runner and convention before creating files:
- Inspect project config (`pyproject.toml`, `package.json`, `Cargo.toml`).
- Identify the repository test commands (e.g., `pytest tests/`, `npm test`, `./gradlew test`).

### Étape 2 : RED — Write a Failing Test
Write a minimal test that asserts the desired behavior:
- Run the test suite and verify that the test fails for the expected reason.
- For bug reports, write a reproduction test (Prove-It pattern) that fails on the bug.

### Étape 3 : GREEN — Write Minimal Passing Code
Implement the simplest production logic that satisfies the test:
- Focus solely on passing the test without premature optimization.
- Confirm the test passes cleanly.

### Étape 4 : REFACTOR & Regression Verification
Clean up code without altering behavior:
- Eliminate duplication, improve naming, and adhere to typing standards.
- Re-run all existing test suites in `tests/` to guarantee zero regressions.

---

## 3. Prescriptive Rules & Garde-fous

### Rules & Garde-fous (DO NOT / NEVER)
- **Règle 1** : DO NOT write production implementation code before seeing the test fail (RED phase).
- **Règle 2** : DO NOT write tests that pass immediately without exercising new behavior.
- **Règle 3** : NEVER delete or comment out existing tests to make a build pass.
- **Règle 4** : DO NOT ship changes without executing the full regression suite in `tests/`.

---

## 4. Gestion des erreurs, résilience et fallback

- **Comportement en cas d'erreur ou d'échec de test inattendu** : Si un test tiers régresse lors du refactoring, annuler immédiatement la modification et analyser l'impact sur l'interface.
- **Fallback en l'absence de framework de test installé** : Si l'exécuteur de tests est manquant dans l'environnement, exécuter un script d'assertion unitaire autonome via l'interpréteur natif sans masquer la dégradation.
- **Gestion des exceptions d'exécution** : Toute exception inattendue survenue dans le harness de test doit lever une alerte bloquante et interrompre le commit.
```

### Fichier B : `.agents/skills/test-driven-development/references/tdd_patterns.md`
```markdown
# Test-Driven Development Patterns & Reference

This reference document accompanies `.agents/skills/test-driven-development/SKILL.md`.

## 1. The Red-Green-Refactor Loop

```
    RED                GREEN              REFACTOR
 Write a test    Write minimal code    Clean up the
 that fails  ──→  to make it pass  ──→  implementation  ──→  (repeat)
      │                  │                    │
      ▼                  ▼                    ▼
   Test FAILS        Test PASSES         Tests still PASS
```

---

## 2. Bug Reproduction: The Prove-It Pattern

```typescript
// Step 1: Write a reproduction test that asserts the desired fix
it('sets completedAt when task is marked complete', async () => {
  const task = await taskService.createTask({ title: 'Test' });
  const completed = await taskService.completeTask(task.id);
  expect(completed.status).toBe('completed');
  expect(completed.completedAt).toBeInstanceOf(Date); // Fails initially
});

// Step 2: Implement minimal fix in application code
// Step 3: Verify test passes and re-run entire test suite
```

---

## 3. Testing Pyramid Ratios

- **Unit Tests (~70%)**: Fast, isolated, test pure domain logic and edge cases.
- **Integration Tests (~20%)**: Test module boundaries, database interactions, and API routes.
- **E2E / Browser Tests (~10%)**: Test critical end-to-end user journeys.
```

---

## 3. `code-simplification`

Simplifie le code pour en maximiser la lisibilité et la maintenabilité tout en préservant 100% du comportement existant et de la couverture de tests (anti-boilerplate LLM).

### Fichier A : `.agents/skills/code-simplification/SKILL.md`
```markdown
---
name: code-simplification
description: Simplifies code for clarity. Use when refactoring code for clarity without changing behavior to reduce complexity, eliminate duplication, and improve maintainability while ensuring zero behavioral regression.
---

# Code Simplification

Simplify code by reducing structural complexity and mental overhead while preserving 100% of existing behavior and test coverage.

## 1. Ground Truth & Repository Anchoring (SSOT & Evidence)

Every refactoring pass must be grounded in repository facts and verifiable truth (SSOT & evidence factuelle) :
- Architectural conventions and coding standards: consult [standards/blueprints/](standards/blueprints/) and [Projects/](Projects/).
- Automated test suites: run unit and integration assertions in [tests/](tests/) before and after every edit.
- Language-specific recipes and patterns: consult [references/simplification_patterns.md](references/simplification_patterns.md).

---

## 2. Core Execution Protocol

Follow these ordered steps sequentially:

### Étape 1 : Baseline Comprehension & Chesterton's Fence
Understand before modifying:
- Analyze existing callers, side-effects, error branches, and edge cases.
- Confirm all existing tests in `tests/` pass cleanly on the unmodified code.

### Étape 2 : Identify Concrete Simplification Opportunities
Scan for objective signals rather than subjective aesthetics:
- Flatten deep nesting (> 2 levels) using guard clauses and early returns.
- Replace dense inline ternary chains with readable lookup maps or clear conditionals.
- Eliminate dead branches, unused local variables, and speculative abstractions.

### Étape 3 : Apply Atomic Incremental Edits
Apply changes one focused transformation at a time:
- Keep refactoring changes strictly isolated from new feature additions or bug fixes.
- If a refactoring touches more than 500 lines, use automated AST scripts instead of manual edits.

### Étape 4 : Verification & Regression Validation
- Re-run full test suites in `tests/` to guarantee identical behavioral outputs.
- Verify that linter and type-checker pass with zero warnings or errors.

---

## 3. Prescriptive Rules & Garde-fous

### Rules & Garde-fous (DO NOT / NEVER)
- **Règle 1** : DO NOT change runtime behavior, return values, or side effects during simplification.
- **Règle 2** : DO NOT remove or weaken error handling or boundary validation logic.
- **Règle 3** : NEVER batch multiple large refactoring steps into a single unverified commit.
- **Règle 4** : DO NOT modify existing tests to make a "simplification" pass — if tests break, the refactor failed.

---

## 4. Gestion des erreurs, résilience et fallback

- **Comportement en cas d'erreur ou d'échec de test** : Si un test régresse suite à une simplification, effectuer un rollback immédiat vers la version précédente avant d'analyser l'écart.
- **Fallback en l'absence de tests unitaires** : Si le module ciblé manque de couverture dans `tests/`, écrire d'abord un test de caractérisation figé (snapshot test) avant d'appliquer la moindre modification de code.
- **Gestion des exceptions inattendues** : En cas de runtime exception introduite lors du typage ou du déballage de données, préserver les gardes défensives natives sans dégradation du service.
```

### Fichier B : `.agents/skills/code-simplification/references/simplification_patterns.md`
```markdown
# Code Simplification Patterns & Language Guides

This reference document accompanies `.agents/skills/code-simplification/SKILL.md`.

## 1. TypeScript & JavaScript Patterns

```typescript
// Replace dense ternaries with explicit early returns or lookup tables
// Before:
const label = isNew ? 'New' : isUpdated ? 'Updated' : isArchived ? 'Archived' : 'Active';

// After:
function getStatusLabel(item: Item): string {
  if (item.isNew) return 'New';
  if (item.isUpdated) return 'Updated';
  if (item.isArchived) return 'Archived';
  return 'Active';
}

// Unnecessary async wrapper
// Before: async function getUser(id: string) { return await userService.findById(id); }
// After: function getUser(id: string) { return userService.findById(id); }
```

---

## 2. Python Patterns

```python
# List and Dict comprehensions over manual loops
# Before:
result = {}
for item in items:
    result[item.id] = item.name

# After:
result = {item.id: item.name for item in items}

# Guard clauses instead of nested conditions
# Before:
def process(data):
    if data is not None:
        if data.is_valid():
            return do_work(data)
# After:
def process(data):
    if data is None or not data.is_valid():
        raise ValueError("Invalid data")
    return do_work(data)
```
```

---

## 4. `incremental-implementation`

Construit et livre le code par tranches verticales minces et vérifiables (une pièce $\rightarrow$ un test $\rightarrow$ une vérification $\rightarrow$ un checkpoint).

### Fichier Unique : `.agents/skills/incremental-implementation/SKILL.md`
```markdown
---
name: incremental-implementation
description: Delivers changes incrementally in thin, verifiable slices. Use when implementing multi-file changes or features to build one piece, test it, verify it, and save progress safely.
---

# Incremental Implementation

Build in thin vertical slices — implement one piece, test it, verify it, then expand. Avoid implementing an entire feature in one pass. Each increment must leave the system in a working, testable state.

## 1. Ground Truth & Repository Anchoring (SSOT & Evidence)

All slices must be rooted in verifiable repository standards (SSOT & evidence factuelle) :
- Architectural blueprints and feature specifications: consult [standards/blueprints/](standards/blueprints/) and [Projects/](Projects/).
- Automated test suites: verify progress in [tests/](tests/) after every increment.

---

## 2. Core Execution Protocol

Follow these ordered steps sequentially:

### Étape 1 : Slice Decomposition
Break the task down before writing code:
- Identify the smallest end-to-end vertical slice (DB + API + contract).
- Prefer vertical slices (one functional path through the stack) over horizontal layers.

### Étape 2 : Implement Focused Slice
Write only the code strictly required for the active slice:
- Never exceed ~100 lines before running tests.
- Keep abstractions to the absolute minimum necessary for current requirements.

### Étape 3 : Verification & Automated Check
Validate the slice immediately:
- Execute the focused test suite for this slice.
- Confirm type-checks and lint pass with zero regressions.

### Étape 4 : Checkpoint & Next Slice
- Save working progress before moving to the next slice.
- Never abandon a broken slice to start another.

---

## 3. Prescriptive Rules & Garde-fous

### Rules & Garde-fous (DO NOT / NEVER)
- **Règle 1** : DO NOT implement an entire multi-file feature in a single unverified step.
- **Règle 2** : DO NOT move to the next slice if the current slice fails any test in `tests/`.
- **Règle 3** : NEVER leave the codebase in an uncompilable state between slices.
- **Règle 4** : DO NOT build speculative hooks or abstractions for future hypothetical slices.

---

## 4. Gestion des erreurs, résilience et fallback

- **Comportement en cas d'erreur ou de régression** : Si un incrément casse un test existant, annuler immédiatement les modifications de la tranche courante avant d'analyser l'écart.
- **Fallback en l'absence de tests automatisés** : Si le projet n'a pas de harnais de test, effectuer une vérification manuelle par script d'assertion avant de valider la tranche.
- **Gestion des pannes d'environnement** : En cas d'échec du runner de test, journaliser la dégradation et isoler le code non testé sous une garde explicite.
```

---

## 5. `api-and-interface-design`

Guide la conception d'APIs et de frontières de modules stables, typées, rétrocompatibles et résilientes face aux pannes.

### Fichier A : `.agents/skills/api-and-interface-design/SKILL.md`
```markdown
---
name: api-and-interface-design
description: Guides stable API and interface design. Use when designing APIs, module boundaries, or public type contracts to build predictable, resilient, and backwards-compatible system boundaries.
---

# API and Interface Design

Design stable, strictly-typed interfaces that are intuitive to adopt and impossible to misuse. Every public contract represents an unalterable commitment once consumed.

## 1. Ground Truth & Repository Anchoring (SSOT & Evidence)

All contracts must reflect real repository constraints and anchor to verifiable standards (SSOT & evidence factuelle) :
- Schemas & DTO contracts: inspect `src/models/`, `src/api/`, or target framework endpoints.
- Blueprints & architectural rules: consult [standards/blueprints/](standards/blueprints/) and [Projects/](Projects/).
- Automated contract suites: integrate tests directly in [tests/](tests/).
- Deep patterns & idempotency mechanisms: see [references/api_design_patterns.md](references/api_design_patterns.md).

---

## 2. Core Execution Protocol

Follow these ordered steps sequentially:

### Étape 1 : Contract-First Specification
Define the interface and data transfer shapes prior to writing any implementation logic.
- Specify precise input and output schemas with strict typing (Pydantic / TypeScript).
- Adopt additive-only modifications (One-Version Rule). Do not mutate or delete existing fields without formal deprecation.

### Étape 2 : Boundary Validation & Sanitization
Enforce zero-trust validation exclusively at system ingress boundaries:
- Validate untrusted input at HTTP handlers, message queues, and environment loaders.
- Internal functions sharing trusted type contracts must NOT re-validate.
- External third-party responses must always be parsed defensively with schema guards.

### Étape 3 : Unified Error Semantics & Idempotency
Provide uniform error reporting across all endpoints:
- Use consistent error response envelopes: `{ error: { code: string, message: string, details?: unknown } }`.
- Map domain failures to standardized status codes (400, 401, 403, 404, 409, 422, 500).
- State-changing mutations (POST/PUT/PATCH) must honour `Idempotency-Key` headers via atomic database uniqueness guards.

### Étape 4 : Verification & Automated Contract Tests
- Write end-to-end contract assertions in `tests/` covering happy paths, malformed payloads, and duplicate retry attempts.
- Ensure pagination is enforced on all list endpoints (`page`, `pageSize`, `totalItems`).

---

## 3. Prescriptive Rules & Garde-fous

### Rules & Garde-fous (DO NOT / NEVER)
- **Règle 1** : Définir les schémas avant d'implémenter la logique métier.
- **Règle 2** : DO NOT modifier ou supprimer des champs existants sans migration documentée.
- **Règle 3** : NEVER exposer les traces de pile ou détails internes dans les réponses d'erreur.
- **Règle 4** : DO NOT dériver les clés d'idempotence d'un timestamp ou d'un UUID regénéré à chaque essai.

---

## 4. Gestion des erreurs, résilience et fallback

- **Comportement en cas d'erreur ou d'outil absent** : En l'absence de validateur tiers (Pydantic/Zod), activer le fallback sur les dataclasses natives avec assertions de types strictes.
- **Gestion des requêtes concurrentes en vol** : Si une clé d'idempotence est déjà en traitement, lever une exception ou renvoyer un code `409 Conflict`. Dégradation contrôlée sans duplication.
- **Échec de validation de payload** : Si le hash du corps de requête ne correspond pas à la clé existante, lever une exception `422 Unprocessable Entity`.
```

### Fichier B : `.agents/skills/api-and-interface-design/references/api_design_patterns.md`
```markdown
# API and Interface Design Patterns & Deep References

This reference document accompanies `.agents/skills/api-and-interface-design/SKILL.md`.

## 1. Idempotency Deep Dive

### Core Principles
Accepting an `Idempotency-Key` is the contract; honouring it is the implementation.
- **Derive key from intent, not attempt**: Must be stable across retries of one intent and different across distinct intents.
  - Good: `req.headers['idempotency-key']`, `charge:v1:${orderId}`.
  - Bad: `crypto.randomUUID()` (per attempt), timestamp (per attempt).
- **Atomic Claim**: Use unique database constraints to avoid TOCTOU race conditions.
- **Guard Payload**: Reject different payloads under the same key with 422 Unprocessable Entity.
- **Duplicate Handling**: Choose between `409 Conflict`, bounded wait, or `202 Accepted` with status URL.
- **Key Retention**: Key TTL must exceed longest retry chain (e.g. 7-day DLQ requires >= 7-day retention).

```typescript
// Atomic claim with unique constraint
try {
  await db.insert({ key, state: 'in_progress', requestHash: hash(req.body) });
} catch (e) {
  if (isUniqueViolation(e)) return replayOrReject(key);
  throw e;
}
const result = await chargeCard(amount);
await db.update({ key, state: 'succeeded', response: result });
```

---

## 2. REST API Specification

### Resource Conventions
```
GET    /api/tasks              → List tasks (query params for filtering/pagination)
POST   /api/tasks              → Create task
GET    /api/tasks/:id          → Get single task
PATCH  /api/tasks/:id          → Update partial task
DELETE /api/tasks/:id          → Idempotent delete
```

### Pagination Schema
```typescript
interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    pageSize: number;
    totalItems: number;
    totalPages: number;
  };
}
```
```

---

## 6. `doubt-driven-development`

Soumet chaque décision architecturale non triviale à un relecteur contradictoire isolé en contexte frais (*fresh context*) afin de dissiper l'excès de confiance avant la mise en production.

### Fichier A : `.agents/skills/doubt-driven-development/SKILL.md`
```markdown
---
name: doubt-driven-development
description: Subjects every non-trivial decision to fresh-context adversarial review. Use when stress-testing architectural decisions, high-stakes code, or plans for hidden failure modes before finalizing.
---

# Doubt-Driven Development

A confident answer is not a correct one. Doubt-driven development subjects non-trivial decisions to an adversarial reviewer biased to disprove assumptions while course correction is cheap.

## 1. Ground Truth & Repository Anchoring (SSOT & Evidence)

All doubts and claims must be reconciled against verifiable repository artifacts (SSOT & evidence factuelle) :
- Architectural decisions and blueprints: consult [standards/blueprints/](standards/blueprints/) and [Projects/](Projects/).
- Automated test suites and regression logs: verify directly in [tests/](tests/) and execution traces.
- Adversarial prompt templates and escalation recipes: see [references/doubt_protocols.md](references/doubt_protocols.md).

---

## 2. Core Execution Protocol

Follow these ordered steps sequentially:

### Étape 1 : Formulate the Claim (CLAIM)
State the decision, assumption, or invariant explicitly in 2-3 lines:
- Name what is claimed and why failure would be catastrophic or hard to detect in QA.
- If the claim cannot be articulated compactly, clarify the decision before proceeding.

### Étape 2 : Extract Isolated Artifact & Contract (EXTRACT)
Isolate the exact subject under review without your reasoning history:
- Pass only the specific diff, function, or proposal alongside the target contract.
- Strip conversational rationalizations so the reviewer evaluates the artifact objectively.

### Étape 3 : Invoke Adversarial Fresh-Context Review (DOUBT)
Prompt a reviewer agent whose sole instruction is to find failure modes, unstated assumptions, or contract violations:
- Instruct the reviewer to disprove, never to validate or flatter.
- In interactive sessions, offer cross-model second opinions where stakes warrant.

### Étape 4 : Reconcile Findings (RECONCILE)
Classify each finding strictly against the artifact text:
- Refactor code or update specs to eliminate verified failure modes.
- Dismiss false positives only with explicit physical counter-evidence.

### Étape 5 : Termination & Convergence (STOP)
- Stop the cycle when all valid findings are addressed or a maximum of 3 iterations is reached.
- Run complete regression suites in `tests/` before marking the decision final.

---

## 3. Prescriptive Rules & Garde-fous

### Rules & Garde-fous (DO NOT / NEVER)
- **Règle 1** : DO NOT pass your own justification or conclusion to the adversarial reviewer.
- **Règle 2** : DO NOT run doubt cycles on trivial mechanical edits (renaming, formatting).
- **Règle 3** : NEVER allow personas to spawn recursive subagent trees; doubt cycles must be orchestrator-driven.
- **Règle 4** : DO NOT dismiss adversarial findings without verifiable physical evidence in code or tests.

---

## 4. Gestion des erreurs, résilience et fallback

- **Comportement en cas d'erreur ou d'échec du reviewer** : Si l'agent reviewer subit un timeout ou échoue, ré-émettre la requête avec un contexte encore plus réduit (diff focalisé).
- **Fallback en environnement imbriqué (sans subagents)** : Si l'environnement interdit le spawn de sous-agents, appliquer un fallback par auto-questionnement adversarial explicite avec un prompt hermétique sans masquer la dégradation.
- **Gestion des exceptions d'exécution** : Toute exception levée lors de l'appel d'outils d'évaluation externes doit interrompre le cycle et alerter l'utilisateur.
```

### Fichier B : `.agents/skills/doubt-driven-development/references/doubt_protocols.md`
```markdown
# Doubt-Driven Development Protocols & Cross-Model Reference

This reference document accompanies `.agents/skills/doubt-driven-development/SKILL.md`.

## 1. Adversarial Review Prompt Template

```markdown
Adversarial review. Find what is wrong with this artifact.
Assume the author is overconfident. Look for:
- Unstated assumptions
- Edge cases not handled
- Hidden coupling or shared state
- Ways the contract could be violated
- Existing conventions this might break
- Failure modes under unexpected input

Do NOT validate. Do NOT summarize. Find issues, or state
explicitly that you cannot find any after thorough examination.

ARTIFACT: <paste artifact>
CONTRACT: <paste contract>
```

---

## 2. Cross-Model CLI Escalation Shapes

```bash
# Codex CLI read-only review
codex exec --sandbox read-only -C <repo-path> - < /tmp/doubt-prompt.md

# Gemini CLI plan mode review
gemini --approval-mode plan -p "" < /tmp/doubt-prompt.md
```
```

---

## 🚀 7. Comment Activer ces Compétences dans `AGENTS.md`

Une fois les compétences créées sous `.agents/skills/`, ajoutez simplement ce bloc dans le fichier `AGENTS.md` à la racine de votre dépôt :

```markdown
## 🧰 Compétences Méthodologiques Activées

Les compétences suivantes sont disponibles sous `.agents/skills/` et doivent être consultées selon le contexte :
- `constraint-driven-development` : Consulte `CONSTRAINTS.md` avant toute tâche d'implémentation.
- `test-driven-development` : Écris le test avant le code (cycle RED -> GREEN -> REFACTOR).
- `code-simplification` : Applique une passe de simplification après avoir validé les tests.
- `incremental-implementation` : Découpe toute tâche multi-fichiers en tranches atomiques.
- `api-and-interface-design` : Définit les types et contrats DTO avant la logique métier.
- `doubt-driven-development` : Soumets les décisions critiques à une relecture contradictoire.
```
