---
id: MLOOP-143-BE
jira_key: ''
epic_key: EPIC-14-OBSERVABILITY-INSTRUMENTATION
type: Feature
title: Instrumentation Logging Workers Herdr (herdr_adapter, herdr_core, herdr_daemon,
  herdr_worker, worker_pipeline)
tags:
- core
- observability
- logging
- herdr
- workers
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

# 📖 MLOOP-143-BE : Instrumentation Logging Workers Herdr

## 1. Intention Métier (User Story)
**En tant qu'**Architecte mLoop,  
**je veux** que l'orchestration Herdr (spawn, PTY, pannes, zombie reap, workers) logue toutes ses erreurs avec contexte d'exécution,  
**afin de** permettre au flow RHO de diagnostiquer les pannes workers (timeout, crash PTY, leak ressources) et proposer des corrections d'infrastructure.

---

## 2. Origine & Cadrage Avant-Projet
- **Document Source** : Analyse de gap MLOOP-110-BE — 5 modules Herdr + worker_pipeline, ~10 `except Exception`, 4 `ZeroFluffConsole.error`
- **Hypothèse de Chiffrage Retenue** : Instrumentation critique pour l'anti-zombie policy et la fiabilité PTY
- **Enveloppe Macro Estimée** : M (fourchette de 1-2 jours)

---

## 3. Périmètre Sommaire
### In-Scope (Macro)
- `src/core/herdr_adapter.py` (1 `except`) : Façade 44L, délégation aux mixins
- `src/core/herdr_core.py` (2 `except`) : Layout BSP, panes, workspace
- `src/core/herdr_daemon.py` (1 `except`) : Daemon PTY, santé processus
- `src/core/herdr_worker.py` (3 `except`) : Worker lifecycle, spawn/harvest/close
- `src/pipelines/worker_pipeline.py` (2 `except`, 4 `ZeroFluffConsole.error`) : Orchestration workers, delegation gates

### Out-of-Scope (Macro)
- Mixins Herdr internes (herdr_agents, herdr_panes) — couverts si utilisés via façade
- CLI handlers (MLOOP-142-BE)

---

## 4. Critères de Succès Préliminaires
- [ ] Toute panne PTY, timeout spawn, zombie détecté → `logger.error(..., exc_info=True)`
- [ ] Contexte : `worker_id`, `pane_id`, `agent_kind`, `task_type`, `timeout_ms`, `exit_code`
- [ ] `mloop.log` trace : spawn → working → harvest → close (durée, statut)
- [ ] Zombie reap : log WARNING systématique avec `worker_id` et `age_seconds`
- [ ] Tests : Simulation panne PTY / timeout / zombie → validation capture

---

## 5. Zones d'Ombre & Questions pour la Session Grill-Me 1:1
> [!IMPORTANT]
> *Ces questions constituent l'ordre du jour obligatoire de la session contradictoire Grill-Me 1:1.*

- ❓ `herdr_adapter.py` façade vs mixins : logger au niveau façade seulement ou propager aux mixins ?
- ❓ `worker_pipeline.py` : Délégation gates (validation, build, deepsearch, compaction) — log par gate ou agrégé ?
- ❓ Zombie reap : Niveau WARNING (standard) ou ERROR (critique) ?
- ❓ Contexte PTY : Capturer `stdout`/`stderr` tail dans `extra` ou fichier séparé ?