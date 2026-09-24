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
