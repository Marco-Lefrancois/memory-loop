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
