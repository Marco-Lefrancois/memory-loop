---
created: 2026-09-21T20:53:35.825Z
source: plannotator
tags: [plannotator, memory-loop, impl, mentation, mloop-143-be]
---

[[Plannotator Plans]]

# Plan d'Implémentation — MLOOP-143-BE : Instrumentation Logging Workers Herdr

## Contexte & Constat de Réalité (Fact-Search sur le code)

L'exploration verbatim des 6 modules révèle que **la majorité de l'instrumentation est déjà en place** (travaux prérequis MLOOP-140-BE + découpage worker déjà livrés). Le delta réel est plus étroit que l'enveloppe macro M :

| Module | État vérifié (n° lignes) | Action |
|---|---|---|
| `src/core/herdr_adapter.py` (44L) | Façade pure, aucun `except` | **Aucune** (délègue aux mixins) |
| `src/core/herdr_daemon.py` | 2 `except` L77/L84 : `logger.error(exc_info=True, extra=...)` ✅ + Popen `wait(timeout=10)` ✅ | **Aucune** (déjà conforme) |
| `src/core/herdr_agents.py` | 1 `except` L79 : `logger.debug(exc_info=True, extra=...)` ✅ | **Aucune** (déjà conforme) |
| `src/core/herdr_core.py` | L56/L72 `logger.debug` ✅ ; **L116 `logger.error` SANS `exc_info`/`extra`** ⚠️ | **Corriger L116** |
| `src/core/herdr_worker_core.py` | **L103 `except Exception:` nu silencieux** ; **L176 `except Exception:` nu silencieux** ; spawn/harvest/reap sans logs lifecycle/erreur structurés ⚠️ | **Instrumenter** |
| `src/pipelines/worker_pipeline.py` | 4 `ZeroFluffConsole.error` (L72, L193, L215, L260) sans `logger.error` jumeau ; L212 `except` avec ZFC.warning mais sans `logger` ⚠️ | **Ajouter logger.error(exc_info) parallèle** |

> **Cap ADR-0202** : `herdr_worker_core.py` est déjà à **307L (> 300L)**. L'ajout de logs risque d'aggraver le dépassement — je resterai au plus près, sans refactor structurel (hors périmètre), et signalerai la dette si le seuil grimpe.

---

## Objectif (rappel récit)
Instrumenter les erreurs workers (PTY, spawn, timeout, zombie, leak) avec contexte `extra={worker_id, pane_id, agent_kind, task_type, timeout_ms, exit_code}` + zombie reap `{worker_id, age_seconds, status}`, niveaux : lifecycle INFO / zombie WARNING (+ERROR si reap échoue) / PTY hang-timeout ERROR. Conformité ADR-0369 (Zero-Silent-Pass, Zero-Leak, Zero-Unbounded-Wait).

---

## Fichiers à MODIFIER

### 1. `[MODIFY]` src/core/herdr_core.py
- **L116** `except Exception as e:` → passer `logger.error(...)` en `logger.error(..., exc_info=True, extra={"herdr_bin": self.herdr_bin, "cmd": ' '.join(cmd)})`. Aligne la façade `_exec` sur le standard (couvre l'`except` compté pour l'adapter, puisque l'adapter délègue à ce mixin).

### 2. `[MODIFY]` src/core/herdr_worker_core.py
- **L103** (`spawn_story_worker_impl`, `wait_agent` timeout) : remplacer `except Exception:` nu + `logger.debug(f"wait_agent timeout...")` par `except Exception as exc:` avec `logger.warning("wait_agent timeout au spawn worker", exc_info=True, extra={"worker_id": worker_name, "pane_id": pane_id, "agent_kind": kind, "task_type": task_type})` (PTY/spawn hang = signal diagnostique, WARNING car le prompt part quand même).
- **spawn** : ajouter `logger.info("Worker lifecycle: spawn", extra={worker_id, pane_id, agent_kind, task_type, model})` à la création (transition spawn→working) juste avant le `return`.
- **L176** (`harvest_story_evidence_impl`, lecture EvidencePack JSON existant) : remplacer `except Exception:` nu par `except (OSError, json.JSONDecodeError) as exc:` avec `logger.warning("EvidencePack existant illisible — réinitialisation", exc_info=True, extra={"worker_id": worker_name, "evidence_file": str(evidence_file)})`.
- **harvest** : `logger.info("Worker lifecycle: harvest", extra={worker_id, harvest_status, cleaned_lines, worker_active})` avant le `return`.
- **`audit_and_reap_zombies_impl`** : la boucle logue déjà `logger.info("Reaping zombie...")` ; l'enrichir → `logger.warning("Zombie reap", extra={"worker_id": name, "pane_id": pane_id, "status": status, "age_seconds": ag.get("age_seconds")})` (niveau WARNING = standard récit) ; **si `cr.get("success")` est False → `logger.error("Échec reap zombie", extra={worker_id, pane_id, status, close_error})`** (ERROR si reap échoue, per spec).
- **`reap_zombie_workers_impl`** : sur chaque entrée `errors` (close échoué) → `logger.error("Échec fermeture worker orphelin", extra={"worker_id": ag.get('name'), "pane_id": pid, "reason": ag.get('reason'), "close_error": cr.get('error')})` ; sur reap réussi → `logger.warning("Worker orphelin reapé", extra={worker_id, pane_id, reason})`.
- **`cleanup_worker_impl`** : `logger.info("Worker lifecycle: close", extra={"worker_id": story_id_or_pane, "pane_id": pane_id})` avant le `return`.

### 3. `[MODIFY]` src/pipelines/worker_pipeline.py
- Ajouter `import logging` + `logger = logging.getLogger("mloop.worker_pipeline")` en tête.
- **L72-74** (spawn échoué) : ajouter `logger.error("Échec spawn worker Herdr", extra={"worker_id": story_id, "agent_kind": kind, "task_type": task_type, "error": res.get('error')})` en parallèle du `ZeroFluffConsole.error`.
- **spawn réussi** : `logger.info("Worker lifecycle: spawn OK", extra={worker_id, pane_id, agent_kind, model, task_type})`.
- **L193** (Gate évidence FAIL) : `logger.error("Gate d'évidence FAIL", extra={"worker_id": story_id, "reasons": evidence_res.reasons})`.
- **L212** (`except Exception as exc:` re-vérif gates) : ajouter `logger.warning("Re-vérification gates échouée", exc_info=True, extra={"worker_id": story_id})` (garder le ZFC.warning existant).
- **L215** (harvest échoué) : `logger.error("Échec moisson évidences", extra={"worker_id": story_id, "error": res.get('error')})`.
- **L260** (reap : erreur close volet) : `logger.error("Échec fermeture volet au reap", extra={"pane_id": err.get('pane_id'), "error": err.get('error')})`.
- **harvest/close réussis** : `logger.info("Worker lifecycle: harvest/close", extra={...})`.

> **Note** : `herdr_worker.py` (façade mixin) et `herdr_adapter.py` restent inchangés (délégation pure — l'instrumentation vit dans `_core` et le mixin `_exec`).

---

## Fichiers à MODIFIER (Tests — TDD)

### 4. `[MODIFY]` tests/test_herdr_adapter.py
Ajouter (via `caplog` pytest, niveau logger `mloop.*`) les cas de rupture couvrant les 3 scénarios du critère de succès #5 :
- **`test_spawn_worker_logs_pty_wait_timeout`** : `wait_agent` lève `Exception` → assert `caplog` contient un record WARNING `mloop.herdr_worker_core` avec `worker_id`/`pane_id` dans `extra`, et que le spawn retourne quand même `success=True` (résilience).
- **`test_harvest_corrupt_evidence_logs_warning`** : EvidencePack existant JSON corrompu → assert WARNING loggé avec `evidence_file` en `extra`, harvest réussit (repli `{}`).
- **`test_zombie_reap_logs_warning_and_error_on_close_fail`** : `close_pane` retourne `success=False` pour un zombie → assert un record WARNING (reap) **et** un record ERROR (échec close) avec `worker_id`/`pane_id`/`status` en `extra`.
- **`test_worker_pipeline_spawn_failure_logs_error`** : `spawn_story_worker` renvoie `success=False` → assert `logger.error` `mloop.worker_pipeline` émis avec `worker_id` en `extra`.

Ces tests utilisent le pattern `caplog.set_level(logging.WARNING)` + inspection de `record.__dict__` pour les clés `extra`, conformément au Failure Contract ADR-0369 (#5 `parametrize`/`raises`).

---

## Audit 360° / 7 Couches (ADR-0376)
1. **Blueprints** : aucun gabarit touché. ✅
2. **Protocoles** : aucun SSOT normatif modifié. ✅
3. **ADR** : aucune décision nouvelle (application ADR-0369 existant, pas de Type 1). ✅
4. **Directives agents** : inchangées. ✅
5. **Skills** : inchangés. ✅
6. **Core Python** : `herdr_core.py`, `herdr_worker_core.py`, `worker_pipeline.py` (rétrocompat stricte : signatures et valeurs de retour identiques, ajout de logs uniquement). ✅
7. **Tests & Parité** : +4 tests unitaires ; `guide --sync` **non requis** (aucun ajout/modif dans `src/commands/_registry.py`). ✅

---

## Séquence de Vérification (clôture)
1. `python -m pytest tests/test_herdr_adapter.py -q` → 15 passed attendus (11 existants + 4 nouveaux, zéro régression).
2. `python -m pytest tests/test_worker_harvest_partial.py tests/test_sortie_resilience_patterns.py -q` → non-régression des consommateurs voisins.
3. `python src/swarm.py vibe-check --project mLoop` → 20/20 maintenu (dont contrôle ADR-0369 Robustesse Python).
4. `python src/swarm.py sync --project mLoop` → réindexation FTS5 + hypergraphe.

---

## Hors Périmètre (explicite)
- Refactor structurel de `herdr_worker_core.py` sous 300L (dette ADR-0202 signalée, hors récit).
- Modification des mixins `herdr_panes.py` (aucun `except` détecté).
- CLI handlers (MLOOP-142-BE).
- Capture `stdout`/`stderr` tail PTY dans un fichier séparé (question ouverte grill non tranchée vers cette option ; le contexte `extra` suffit au critère #1).