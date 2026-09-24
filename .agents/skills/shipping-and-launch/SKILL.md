---
name: shipping-and-launch
description: Prepares production launches. Use when preparing to deploy to production, setting up rollout strategies, or validating pre-flight release gates to ensure zero-downtime and safe rollbacks.
---

# Shipping and Launch

Ship software with confidence. Every deployment must be observable, incremental, and backed by a documented rollback mechanism.

## 1. Ground Truth & Repository Anchoring (SSOT & Evidence)

All release decisions must anchor directly to verifiable repository evidence (SSOT & evidence factuelle) :
- Release governance and deployment blueprints: consult [standards/blueprints/](standards/blueprints/) and [Projects/](Projects/).
- Automated test suites and release verification: verify passes in [tests/](tests/) and deployment traces.
- Detailed launch matrices and rollout thresholds: see [references/launch_checklists.md](references/launch_checklists.md).

---

## 2. Core Execution Protocol

Follow these ordered steps sequentially:

### Étape 1 : Pre-Flight Verification Gate
Confirm that all quality, security, and build checks pass unconditionally:
- Execute all test suites in `tests/` and confirm clean exit codes.
- Validate that dependencies contain zero critical vulnerabilities via audit scans.
- Confirm all migrations are idempotent and backward-compatible with the previous release.

### Étape 2 : Feature Flag & Environment Isolation
Decouple deployment from release:
- Deploy new functionality behind disabled feature flags.
- Verify environment configurations, secrets management, and health check endpoints.

### Étape 3 : Canary Rollout & Telemetry Monitoring
Promote traffic incrementally while continuously observing telemetry:
- Roll out to internal users first, then 5% canary, then gradual increments (25%, 50%, 100%).
- Monitor error rates, P95 latency, and crash telemetry against baseline metrics.

### Étape 4 : Post-Launch Verification & Flag Retirement
- Confirm system stability under full traffic load.
- Schedule feature flag retirement and remove dead code branches within 2 weeks of full launch.

---

## 3. Prescriptive Rules & Garde-fous

### Rules & Garde-fous (DO NOT / NEVER)
- **Règle 1** : DO NOT deploy to production without an executable and tested rollback strategy.
- **Règle 2** : DO NOT release state-changing schema migrations that break backward compatibility with running instances.
- **Règle 3** : NEVER deploy on Fridays or before holidays without explicit organizational sign-off.
- **Règle 4** : DO NOT ignore canary error rate spikes — immediately halt rollout or execute rollback.

---

## 4. Gestion des erreurs, résilience et fallback

- **Comportement en cas d'erreur ou d'anomalie canary** : Si le taux d'erreur dépasse le double de la référence (`baseline`), déclencher un rollback immédiat sans attendre l'intervention humaine.
- **Fallback en l'absence de système de feature flags** : En cas de déploiement direct sans flags, procéder par versionnage parallèle (blue/green deploy) avec bascule DNS réversible en cas de dégradation.
- **Gestion des exceptions de migration** : Si une migration de base de données échoue, le script doit lever une exception bloquante et restaurer l'état transactionnel sans corrompre les données existantes.
