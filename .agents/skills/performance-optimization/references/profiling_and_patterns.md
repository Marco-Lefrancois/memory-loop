# Profiling Techniques & Performance Fix Patterns

Detailed code patterns and profiling commands for frontend, backend, and database optimization.

## 1. Database Optimization Patterns
- **Index Missing Foreign Keys** : Create B-tree indexes on columns used in `WHERE`, `JOIN`, and `ORDER BY`.
- **Eliminate N+1 Query Anti-Patterns** :
  - In ORMs (Prisma, Entity Framework, Django, SQLAlchemy), use eager loading (`include`, `select_related`, `prefetch_related`) instead of lazy loops.
- **Cursor-Based Pagination** : For large datasets (> 10k rows), use `WHERE id > last_seen_id ORDER BY id LIMIT 20` instead of `OFFSET`.

## 2. Backend & API Patterns
- **HTTP Caching** : Use `Cache-Control: public, max-age=3600, stale-while-revalidate=60` and `ETag` headers.
- **Connection Pooling** : Reuse pooled database and HTTP client connections.
- **Compression** : Enable Gzip or Brotli compression for JSON and text payloads.

## 3. Frontend & Core Web Vitals
- **LCP Optimization** : Preload hero images (`<link rel="preload">`) and use modern formats (WebP/AVIF).
- **INP Optimization** : Break long tasks (> 50ms) using `requestIdleCallback()` or `scheduler.yield()`.
- **CLS Optimization** : Always define explicit `width` and `height` (or aspect-ratio) on images and media containers.
