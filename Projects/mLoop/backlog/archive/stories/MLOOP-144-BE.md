---
id: MLOOP-144-BE
jira_key: ""
epic_key: EPIC-14-OBSERVABILITY-INSTRUMENTATION
type: Feature
title: "Instrumentation Logging Jira Sync (sync_engine, jira_item_sync, jira_reader, jira_report)"
tags: [core, observability, logging, jira, sync]
origin: SPEC_SLICING
source_ref: MLOOP-110-BE_gap_analysis
macro_size: S
status: SHIPPED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by: ["MLOOP-140-BE"]
created_at: "2026-09-21"
---

# 📖 MLOOP-144-BE : Instrumentation Logging Jira Sync

## 1. Intention Métier (User Story)
**En tant qu'**Architecte mLoop,  
**je veux** que la synchronisation Jira Cloud (création, mise à jour, lecture, rapport) logue toutes ses erreurs HTTP, d'authentification et de mapping avec contexte complet,  
**afin de** permettre au flow RHO de corréler échecs sync → cause (rate-limit, auth, mapping ADF, champs requis) → fix ciblé.

---

## 2. Origine & Cadrage Avant-Projet
- **Document Source** : Analyse de gap MLOOP-110-BE — 4 modules Jira, ~8 `except Exception`, 5 `ZeroFluffConsole.error`
- **Hypothèse de Chiffrage Retenue** : Fail-Closed protocol exige traçabilité complète des échecs écriture
- **Enveloppe Macro Estimée** : S (fourchette de 0.5-1 jour)

---

## 3. Périmètre Sommaire
### In-Scope (Macro)
- `src/pipelines/jira/sync_engine.py` (3 `except`) : `sync_targeted_to_jira`, `build_sync_preview`, `sync_backlog_to_jira`
- `src/pipelines/jira/jira_item_sync.py` (2 `except`) : `sync_single_item`, création/MAJ stories + sous-tâches
- `src/pipelines/jira/jira_reader.py` (2 `except`, 3 `ZeroFluffConsole.error`) : Lecture stories existantes, mapping champs
- `src/pipelines/jira/jira_report.py` (1 `except`, 2 `ZeroFluffConsole.error`) : Rapport d'audit Markdown, manifeste SHA-256

### Out-of-Scope (Macro)
- `jira_helpers.py`, `jira_story_creator.py`, `jira_story_resolver.py`, `jira_subtasks.py`, `md_cleaner.py`, `adf_converter.py`, `adf_inline.py` — instrumentation optionnelle si erreurs observées
- CLI handler `export_story.py` (jira_sync ciblé) — MLOOP-142-BE

---

## 4. Critères de Succès Préliminaires
- [ ] Erreurs HTTP (4xx, 5xx) → `logger.error(..., extra={"status_code":..., "endpoint":..., "payload_hash":...}, exc_info=True)`
- [ ] Erreurs auth/rate-limit → `logger.error(..., extra={"retry_after":..., "rate_limit_remaining":...})`
- [ ] Échecs mapping ADF / champs requis → `logger.error(..., extra={"field":..., "expected_type":..., "actual_value":...})`
- [ ] Dry-run vs Apply — log distinct avec `mode=dry_run|apply`
- [ ] Tests : Mock HTTP 401/429/500 → validation capture structurée

---

## 5. Zones d'Ombre & Questions pour la Session Grill-Me 1:1
> [!IMPORTANT]
> *Ces questions constituent l'ordre du jour obligatoire de la session contradictoire Grill-Me 1:1.*

- ❓ Payload Jira dans logs : Hash SHA-256 seulement (sécurité) ou champs non-sensibles (debug) ?
- ❓ Rate-limit 429 : Logger comme WARNING (attendu) ou ERROR (échec) ?
- ❓ `sync_engine.py` : Manifeste SHA-256 déjà écrit — logger la divergence comme ERROR ou WARNING ?
- ❓ Contexte `story_id` vs `jira_key` : Les deux ou `jira_key` suffit (clé primaire Jira) ?