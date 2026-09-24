---
name: performance-optimization
description: Optimizes application performance across frontend, backend, queries, and databases. Use when performance requirements exist, when you suspect performance regressions, when Core Web Vitals or load times need improvement, when N+1 query patterns need fixing, or when profiling reveals bottlenecks.
---

# Performance Optimization

## Overview

Measure before optimizing. Performance work without measurement is guessing — and guessing leads to premature optimization that adds complexity without improving what matters. Profile first, identify the actual bottleneck, fix it, measure again. Optimize only what measurements prove matters.

## When to Use

- Performance requirements exist in specifications (load time budgets, response time SLAs)
- Core Web Vitals (CWV) scores fall below acceptable thresholds
- Profiling or APM monitoring detects query bottlenecks or CPU spikes
- Handling large datasets, high traffic, or infinite scroll surfaces

**When NOT to use:** Do not optimize before having measurable evidence of a bottleneck. Premature optimization adds technical debt.

---

## 🧭 Core Web Vitals Targets

| Metric | Good (Target) | Needs Improvement | Poor |
| :--- | :--- | :--- | :--- |
| **LCP** (Largest Contentful Paint) | ≤ 2.5s | 2.5s – 4.0s | > 4.0s |
| **INP** (Interaction to Next Paint) | ≤ 200ms | 200ms – 500ms | > 500ms |
| **CLS** (Cumulative Layout Shift) | ≤ 0.1 | 0.1 – 0.25 | > 0.25 |

---

## 🛠️ The 5-Step Optimization Workflow

```text
1. MEASURE  ──→ Establish baseline with synthetic and RUM profiling
2. IDENTIFY ──→ Isolate the single dominant bottleneck (CPU, I/O, Network)
3. FIX      ──→ Apply the targeted minimal optimization
4. VERIFY   ──→ Measure again under identical conditions (confirm Δspeed)
5. GUARD    ──→ Add automated regression tests and budget gates
```

### 1. Measure (Baseline First)
- **Frontend** : Run Lighthouse in Chrome DevTools or inspect Core Web Vitals via RUM telemetry.
- **Backend** : Profile endpoint latency ($p50, p95, p99$) and measure database query durations using APM traces.
- **Database** : Run `EXPLAIN ANALYZE` on suspect queries; track query count per HTTP request.

### 2. Identify the Dominant Bottleneck
- **N+1 Query Anti-Pattern** : Multiple database round-trips inside application loops.
- **Missing Index** : Sequential full-table scans on foreign keys or search fields.
- **Unbounded Queries** : Missing pagination resulting in huge payloads transferred over the wire.
- **Main-Thread Blocking** : Long JavaScript execution (> 50ms) delaying user interaction feedback.

### 3. Apply Targeted Fixes
- **Database** : Add composite/partial indexes, convert sequential queries to eager joins, implement cursor pagination.
- **Backend** : Add HTTP caching headers (`ETag`, `Cache-Control`), enable payload compression, pool connections.
- **Frontend** : Preload critical resources, defer non-critical scripts, preserve aspect-ratio on layout containers.

### 4. Verify & Confirm Delta
- Measure performance under identical conditions.
- If the improvement is negligible (< 10%) but increases code complexity significantly, **revert the change**.

### 5. Guard Against Regressions
- Add performance assertions to the test suite (e.g. latency assertions, query count assertions).

---

## 🛡️ Verification Checklist

- [ ] Baseline performance measured and recorded before writing optimization code
- [ ] Actual bottleneck confirmed by profiling data (not assumed)
- [ ] Fix addresses the specific bottleneck without adding unnecessary abstractions
- [ ] Performance re-measured showing tangible, verifiable improvement
- [ ] No behavioral regressions introduced (all existing unit and integration tests pass)
- [ ] Performance assertions or budget guards added to prevent regression

---

## 🏛️ References & Deep Guides
- **Profiling Patterns & Code Examples** : `references/profiling_and_patterns.md`
- **mLoop Performance Standards** : `standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md`

## 🛡️ Résilience & Dégradation Gracieuse
En cas d'échec de mesure ou d'indisponibilité des outils de profilage en ligne, s'appuyer sur des benchmarks in-process Python/Node locaux (`time.perf_counter()`), consigner les métriques dans `memory/logs/` et valider les gains par micro-benchmarks reproductibles.
