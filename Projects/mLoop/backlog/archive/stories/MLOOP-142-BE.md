---
id: MLOOP-142-BE
jira_key: ''
epic_key: EPIC-14-OBSERVABILITY-INSTRUMENTATION
type: Feature
title: Instrumentation Logging Handlers CLI Principaux (code_intelligence, build_harness,
  analysis_audit, tooling, export_story)
tags:
- core
- observability
- logging
- cli
- handlers
origin: SPEC_SLICING
source_ref: MLOOP-110-BE_gap_analysis
macro_size: M
status: SHIPPED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by:
- MLOOP-140-BE
created_at: '2026-09-21'
---

# 📖 MLOOP-142-BE : Instrumentation Logging Handlers CLI Principaux

## 1. Intention Métier (User Story)
**En tant qu'**Architecte mLoop,  
**je veux** que les handlers CLI à fort volume d'erreurs utilisateur (`code_intelligence`, `build_harness`, `analysis_audit`, `tooling`, `export_story`) loguent leurs échecs avec contexte complet,  
**afin de** permettre au flow RHO de corréler erreurs utilisateur → cause racine → fix suggéré.

---

## 2. Origine & Cadrage Avant-Projet
- **Document Source** : Analyse de gap MLOOP-110-BE — 5 handlers, ~25 `except Exception`, ~90 `ZeroFluffConsole.error`
- **Hypothèse de Chiffrage Retenue** : Remplacement systématique `ZeroFluffConsole.error` → `logger.error(extra={...}, exc_info=True)`
- **Enveloppe Macro Estimée** : M (fourchette de 1-2 jours)

---

## 3. Périmètre Sommaire
### In-Scope (Macro)
- `src/commands/handlers/code_intelligence.py` (6 `except`, 16 `ZeroFluffConsole.error`) : code-explore, graph-query, graph-explain
- `src/commands/handlers/build_harness.py` (3 `except`, 12 `ZeroFluffConsole.error`) : TDD enforcer, tournoi, AST checker
- `src/commands/handlers/analysis_audit.py` (2 `except`, 9 `ZeroFluffConsole.error`) : Audit Sentinel, Rubber-Duck, Grill
- `src/commands/handlers/tooling.py` (2 `except`, 9 `ZeroFluffConsole.error`) : Install hooks, doctor, calibrate
- `src/commands/handlers/export_story.py` (5 `except`, 6 `ZeroFluffConsole.error`) : Export story, Jira sync ciblé

### Out-of-Scope (Macro)
- Handlers secondaires (MLOOP-145-BE)
- Point d'entrée CLI (MLOOP-140-BE)
- Pipelines cœur (MLOOP-141-BE)

---

## 4. Critères de Succès Préliminaires
- [ ] Chaque `ZeroFluffConsole.error(msg)` → `logger.error(msg, extra={"command":..., "project":..., "story_id":...}, exc_info=True)`
- [ ] Chaque `except Exception` → `logger.error(..., exc_info=True)` avec contexte métier
- [ ] Contexte : `command`, `project`, `story_id`, `target_keys`, `dry_run`, `apply_mode`
- [ ] Tests : Injection d'erreurs simulées dans chaque handler → validation capture dans `errors.log`

---

## 5. Zones d'Ombre & Questions pour la Session Grill-Me 1:1
> [!IMPORTANT]
> *Ces questions constituent l'ordre du jour obligatoire de la session contradictoire Grill-Me 1:1.*

- ❓ `export_story.py` : Le `jira_sync` interne — logger au niveau handler ou déléguer au pipeline Jira (MLOOP-144-BE) ?
- ❓ `code_intelligence.py` : Erreurs `code-explore` vs `graph-query` — même logger ou loggers séparés ?
- ❓ `build_harness.py` : Échecs TDD vs tournoi vs AST — granularité du contexte `extra` ?
- ❓ Remplacer `ZeroFluffConsole.error` partout ou garder pour l'affichage console + ajouter logger en parallèle ?