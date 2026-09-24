# Shipping and Launch Checklists & References

This reference document accompanies `.agents/skills/shipping-and-launch/SKILL.md`.

## 1. Complete Pre-Launch Verification Matrix

| Category | Checks | Gate Condition |
|----------|--------|----------------|
| Quality | Unit/Integration tests, build, lint | 100% PASS, zero warnings |
| Security | `npm audit` / `pip-audit`, gitleaks, CSP | Zero HIGH or CRITICAL findings |
| Performance | Lighthouse Core Web Vitals, N+1 queries | LCP <= 2.5s, CLS <= 0.1 |
| Accessibility | axe-core, keyboard navigation | WCAG 2.1 AA compliant |
| Infra | Migrations, env vars, health check | `/healthz` responds 200 OK |

---

## 2. Canary Rollout Thresholds

| Metric | Advance (Green) | Hold (Yellow) | Roll Back (Red) |
|--------|-----------------|---------------|-----------------|
| Error rate | Within 10% baseline | 10-50% increase | >2x baseline |
| P95 latency | Within 20% baseline | 20-50% increase | >50% increase |
| Crash rate | Zero new exceptions | Trace investigated | Any crash loop |
