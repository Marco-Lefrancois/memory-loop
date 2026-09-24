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
