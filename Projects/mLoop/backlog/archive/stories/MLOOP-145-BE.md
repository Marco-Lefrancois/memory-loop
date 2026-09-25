---
id: MLOOP-145-BE
jira_key: ''
epic_key: EPIC-14-OBSERVABILITY-INSTRUMENTATION
type: Feature
title: Instrumentation Logging Modules Internes & Handlers Secondaires (Ingest, Crawler,
  Dashboard, Calibrate, Graphify, Wikifix, Rho, Converters, LLM, Lexicon, Bridges,
  Fact-Search, Evidence, Rubber-Duck)
tags:
- core
- observability
- logging
- internal
- pipelines
origin: SPEC_SLICING
source_ref: MLOOP-110-BE_gap_analysis
macro_size: L
status: SHIPPED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by:
- MLOOP-140-BE
- MLOOP-141-BE
created_at: '2026-09-21'
ttl_cycles: 1
---

# 📖 MLOOP-145-BE : Instrumentation Logging Modules Internes & Handlers Secondaires

## 1. Intention Métier (User Story)
**En tant qu'**Architecte mLoop,  
**je veux** que l'ensemble des modules internes (ingestion, crawling, dashboard, calibrate, graphify, wikifix, rho, converters, LLM client, lexicon, bridges, fact-search, evidence, rubber-duck) et handlers secondaires loguent leurs erreurs,  
**afin d'**obtenir une couverture 100% du codebase mLoop pour le flow RHO — zéro exception silencieuse, zéro zone d'ombre.

---

## 2. Origine & Cadrage Avant-Projet
- **Document Source** : Analyse de gap MLOOP-110-BE — 30+ modules, ~180 `except Exception`, ~20 `ZeroFluffConsole.error`
- **Hypothèse de Chiffrage Retenue** : Travail systématique par lots, priorité aux modules déjà partiellement instrumentés
- **Enveloppe Macro Estimée** : L (fourchette de 3-5 jours)

---

## 3. Périmètre Sommaire
### In-Scope (Macro) — Groupes par criticité

**Groupe A — Partiellement instrumentés (étendre `get_logger` existant) :**
- `src/pipelines/crawler.py` (21 `except`, ✅ logger) — Étendre couverture
- `src/state.py` (10 `except`, ✅ logger) — Étendre couverture
- `src/pipelines/rubber_duck.py` (5 `except`, ✅ logger) — Étendre couverture
- `src/utils/lexicon/project_resolver.py` (6 `except`, ✅ logger) — Étendre couverture
- `src/engine/fact_search/indexer.py` (6 `except`, ✅ logger) — Étendre couverture
- `src/pipelines/wikifix_auditors.py` (8 `except`) — Ajouter logger

**Groupe B — Non instrumentés (criticité métier) :**
- `src/pipelines/ingest_agent.py` (25 `except`) — Ingestion critique
- `src/dashboard/server.py` (20 `except`) — API Cockpit
- `src/engine/hooks/compaction.py` (13 `except`) — Compaction mémoire
- `src/pipelines/calibrate.py` (12 `except`) — Auto-étalonnage
- `src/pipelines/graphify/agent.py` (10 `except`) — Agent Graphify
- `src/pipelines/wikifix_core.py` (10 `except`, 5 `ZeroFluffConsole.error`) — WikiFix cœur
- `src/loop_mem/db.py` (10 `except`) — SQLite FTS5
- `src/core/llm_client.py` (7 `except`) — Client LLM unifié
- `src/pipelines/rho_optimizer.py` (8 `except`, 3 `ZeroFluffConsole.error`) — RHO
- `src/converters/markpdfdown_converter.py` (8 `except`) — PDF conversion
- `src/bridges/antigravity_hook.py` (6 `except`) — Hook Antigravity
- `src/converters/markitdown_converter.py` (5 `except`) — MarkItDown
- `src/converters/svg_to_md.py` (5 `except`) — SVG OCR
- `src/loop_mem/hybrid_search.py` (5 `except`) — Recherche hybride
- `src/pipelines/evidence_pack.py` (5 `except`) — EvidencePacks
- `src/pipelines/graphify/extractor.py` (5 `except`) — Extractor Graphify
- `src/bridges/mcp_resources.py` (5 `except`) — MCP Resources
- `src/loop_mem/rho_hybrid_search.py` (5 `except`) — RHO hybride
- `src/pipelines/skill_doctor.py` (6 `except`) — Skill Doctor
- `src/utils/lexicon_resolver.py` (1 `except`, ✅ logger) — Étendre
- `src/utils/blueprints.py` (1 `except`, ✅ logger) — Étendre
- `src/utils/antigravity_meter.py` (1 `except`, ✅ logger) — Étendre
- `src/engine/artifacts/boundary_wrapper.py` (✅ logger) — Étendre
- `src/agents/circuit_breaker.py` (1 `except`, ✅ logger) — Étendre
- `src/engine/fact_search/structural_extractor.py` (1 `except`, ✅ logger) — Étendre
- `src/engine/fact_search/retriever.py` (1 `except`, ✅ logger) — Étendre
- `src/engine/fact_search/coverage.py` (1 `except`, ✅ logger) — Étendre
- `src/engine/fact_check/nli_verifier.py` (1 `except`, ✅ logger) — Étendre
- `src/engine/fact_check/certificate.py` (1 `except`, ✅ logger) — Étendre
- `src/utils/opencode_meter.py` (1 `except`, ✅ logger) — Étendre

### Out-of-Scope (Macro)
- Point d'entrée CLI (MLOOP-140-BE)
- Pipelines cœur QA (MLOOP-141-BE)
- Handlers CLI principaux (MLOOP-142-BE)
- Workers Herdr (MLOOP-143-BE)
- Jira Sync (MLOOP-144-BE)

---

## 4. Critères de Succès Préliminaires
- [ ] 100% des `except Exception` → `logger.error(..., exc_info=True)` avec contexte métier minimal
- [ ] 100% des `ZeroFluffConsole.error` → `logger.error(..., extra={...}, exc_info=True)`
- [ ] Modules avec logger existant : étendre à tous les points de capture
- [ ] Contexte standardisé : `module`, `operation`, `input_hash`, `duration_ms`
- [ ] Tests : Échantillonnage — 1 test par groupe (A/B) validant capture erreur injectée

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Couverture 100% Exceptions
- [ ] 100% des `except Exception` → `logger.error(..., exc_info=True)` avec contexte métier minimal
- [ ] 100% des `ZeroFluffConsole.error` → `logger.error(..., extra={...}, exc_info=True)`
- [ ] Modules avec logger existant : étendre à tous les points de capture

#### 2. Contexte Standardisé
- [ ] Contexte standardisé : `module`, `operation`, `input_hash`, `duration_ms`
- [ ] Niveau log codifié : ERROR (exceptions), WARNING (fallbacks), INFO (lifecycle) — mapping 1:1 sans ambiguïté

#### 3. Tests de Validation
- [ ] Tests : Échantillonnage — 1 test par groupe (A/B) validant capture erreur injectée
- [ ] Non-régression : Suite complète tests existants passe

### Scénarios de test (Gherkin 4 Piliers)

#### Pilier 1 — Chemin Nominal
```gherkin
Scénario : Instrumentation complète d'un module non instrumenté
  Étant donné un module du Groupe B (ex: ingest_agent.py) sans logger
  Quand l'instrumentation est appliquée
  Alors 100% des `except Exception` sont remplacés par `logger.error(..., exc_info=True)`
  Et 100% des `ZeroFluffConsole.error` sont remplacés par `logger.error(..., extra={...}, exc_info=True)`
  Et le contexte `module`, `operation`, `input_hash`, `duration_ms` est présent
```

#### Pilier 2 — Exceptions & Rejets
```gherkin
Scénario : Module avec logger existant (Groupe A)
  Étant donné un module du Groupe A (ex: crawler.py) avec logger partiel
  Quand l'instrumentation est étendue
  Alors tous les points de capture `except Exception` loguent avec `exc_info=True`
  Et aucun `except Exception` silencieux ne subsiste
```

#### Pilier 3 — Résilience & Mode Dégradé
```gherkin
Scénario : Échec d'instrumentation sur un module
  Étant donné un module avec syntaxe invalide ou import circulaire
  Quand l'instrumentation est tentée
  Alors l'erreur est consignée
  Et les autres modules continuent d'être instrumentés
  Et le rapport final liste les modules en échec
```

#### Pilier 4 — UX & Observabilité
```gherkin
Scénario : Validation de la couverture 100%
  Étant donné l'instrumentation terminée sur les 30+ modules
  Quand le script de validation est exécuté
  Alors 0 `except Exception` silencieux détectés
  Et 0 `ZeroFluffConsole.error` non instrumentés détectés
  Et le rapport de couverture affiche 100%
```

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API

> **Contexte** : Ce récit instrumente 30+ modules internes avec logging structuré. Aucune API HTTP n'est exposée. Conformément à ADR-0319, l'absence de routes HTTP est consignée via la question ouverte **OQ-145-01**.

| Méthode | Route | Finalité |
|:---|:---|:---|
| `get_logger(name)` | `src.utils.logger:get_logger` | Factory retournant logger configuré (console + fichier rotatif) |
| `logger.error(msg, extra, exc_info)` | `logging.Logger:error` | Log ERROR avec contexte structuré + stack trace |
| `MLoopLoggerAdapter.error()` | `src.utils.logger:MLoopLoggerAdapter.error` | Wrapper imposant `extra={module, operation, input_hash, duration_ms}` |

**Question Ouverte (Exemption ADR-0319)** :
- **OQ-145-01** : Ce récit instrumente 30+ modules internes avec logging structuré. Aucune API HTTP n'est exposée. Les interfaces sont des appels de fonction Python internes (stdlib logging). **[API de soumission à définir]**

---

## 5. Zones d'Ombre & Questions pour la Session Grill-Me 1:1
> [!IMPORTANT]
> *Ces questions constituent l'ordre du jour obligatoire de la session contradictoire Grill-Me 1:1.*

- ❓ Ordre d'exécution : Par groupe (A puis B) ou par criticité métier transversale ?
- ❓ `ingest_agent.py` (25 `except`) : Découper en sous-modules (ADR-0202) avant instrumentation ?
- ❓ `dashboard/server.py` (20 `except`) : FastAPI a son propre logging — fusionner ou séparer ?
- ❓ `compaction.py` (13 `except`) : Hook pre-compact critique — niveau ERROR ou CRITICAL ?
- ❓ `llm_client.py` (7 `except`) : Erreurs LLM (timeout, rate-limit, context window) — taxonomie d'erreurs partagée ?
- ❓ Converters (markitdown, svg, pdf) : Échecs conversion — logger `input_path`, `file_size`, `mime_type` ?
- ❓ Fact-search modules : Erreurs indexation vs recherche — même logger ou séparés ?