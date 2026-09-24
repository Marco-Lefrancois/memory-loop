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
