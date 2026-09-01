# ADR-0345 : Smart Crawler v2 — Découverte LLMs.txt, Traversal Avancé et Caching Déterministe

> **Statut :** Accepté  
> **Date :** 2026-08-30  
> **Contexte :** Benchmark Firecrawl v2 & Modernisation du Sous-Système d'Ingestion mLoop  

---

## 1. Contexte & Problématique

L'analyse comparative approfondie avec **Firecrawl v2** a révélé des opportunités d'optimisation majeures pour le sous-système de crawling et de scraping mLoop (Python `src/pipelines/crawler.py` et TypeScript `c:/mloop-crawler`) :
1. **Absence de Fast-Path Index (`llms.txt`)** : Les crawls parcouraient l'arbre HTML alors que les sites modernes exposent des manifestes sémantiques pré-calculés (`/llms-full.txt`, `/llms.txt`).
2. **Absence de TTL de Cache Déterministe (`maxAge`)** : Ré-exécution redondante d'appels réseau sur des URLs déjà scrapées récemment.
3. **Pollution par Paramètres de Tracking** : Duplication de pages et de caches due aux tags `utm_*`, `ref`, `fbclid`, `session_id`.
4. **Manque de Contrôle de Traversal Fin** : Absence de filtrage de chemin par Regex (`includePaths`, `excludePaths`), de contrôle des sous-domaines (`allowSubdomains`), et d'exclusion automatique des homepages externes lors du crawling 1-hop (`allowExternalLinks`).

---

## 2. Décisions d'Architecture

1. **Découverte Proactive LLMs.txt (Fast-Path)** :
   Avant tout crawl lourd, le moteur sonde en priorité `${origin}/llms-full.txt`, `${origin}/llms.txt` et `${origin}/.well-known/llms.txt`. Si un index Markdown est présent, il est sauvegardé immédiatement et priorisé.

2. **Moteur de Caching Déterministe avec TTL (`max_age` / `maxAge`)** :
   Support d'un paramètre TTL (en secondes côté Python, millisecondes côté TypeScript). Si le fichier de cache est plus récent que le TTL, la réponse est servie instantanément depuis le cache local sans appel réseau.

3. **Normalisation et Nettoyage des Paramètres d'URL** :
   Purge systématique des paramètres de tracking (`utm_*`, `ref`, `fbclid`, `gclid`, `session_id`) avant le calcul du hash d'intégrité SHA256 et le dédoublonnage.

4. **Contrôles de Traversal Granulaires** :
   - `include_paths` / `exclude_paths` : Filtrage d'URLs par expressions régulières.
   - `allow_subdomains` : Navigation autorisée sur les sous-domaines documentaires du même domaine racine.
   - `allow_external_links` (1-Hop Safe) : Suivi des liens sortants sur un seul niveau avec exclusion stricte des pages d'accueil externes racines (`https://external.com/`).
   - `max_depth` / `maxDiscoveryDepth` : Gestion de la récursion basée sur les sauts de découverte réels.

5. **Parité Dual-Stack (Python & TypeScript)** :
   Le pipeline Python léger (`httpx` + `MarkItDown`) et le moteur headless TypeScript (`Playwright` + `Cheerio` + Stdio MCP Server) implémentent strictement les mêmes règles sémantiques et options CLI/MCP.

---

## 3. Impact sur les 6 Piliers mLoop

- **Pilier 1 (CLI & Swarm)** : Nouvelles options CLI riches `--max-age`, `--max-depth`, `--include`, `--exclude`, `--allow-subdomains`.
- **Pilier 2 (Bridges & MCP)** : Outils MCP `scrape_url`, `crawl_domain`, `map` enrichis avec support de `maxAge`, `includePaths`, `excludePaths`, `sitemapMode`.
- **Pilier 3 (Skills)** : Le skill `research-and-develop` exploite nativement le fast-path `llms.txt` pour diviser par 10 le temps d'ingestion des documentations techniques.
- **Pilier 4 (Directives & Guardrails)** : Élimination du bruit d'URL et garantie d'isolation locale sans fuite de secrets.
- **Pilier 5 (Performance & Cache)** : Zéro requête réseau superflue grâce au cache déterministe TTL.
- **Pilier 6 (Graphify & RAG)** : Ingestion de documents Markdown ultra-propres et cohérents.

---

## 4. Statut & Suivi

- Implémentation physique dans `src/pipelines/crawler.py`, `src/commands/_registry.py`, `src/commands/handlers/pipeline.py`.
- Implémentation monorepo dans `c:/mloop-crawler/packages/core/`, `packages/cli/`, `packages/mcp-server/`.
- Tests unitaires validés : `pytest tests/test_crawler_v2.py` (6/6 passés) et `npm test` dans `c:/mloop-crawler` (72/72 passés).
