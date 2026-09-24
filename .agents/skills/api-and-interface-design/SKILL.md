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
