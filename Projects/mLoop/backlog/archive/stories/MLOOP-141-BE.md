---
id: MLOOP-141-BE
jira_key: ""
epic_key: EPIC-14-OBSERVABILITY-INSTRUMENTATION
type: Feature
title: "Instrumentation Logging Pipelines Cœur QA (qa_certifier, vibe_check, sync, focus, lifecycle)"
tags: [core, observability, logging, qa, pipelines]
origin: SPEC_SLICING
source_ref: MLOOP-110-BE_gap_analysis
macro_size: M
status: SHIPPED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by: ["MLOOP-140-BE"]
created_at: "2026-09-21"
---

# 📖 MLOOP-141-BE : Instrumentation Logging Pipelines Cœur QA

## 1. Intention Métier (User Story)
**En tant qu'**Architecte mLoop,  
**je veux** que les pipelines de certification QA, vibe-check, synchronisation, focus et lifecycle loguent toutes leurs erreurs avec stack trace et contexte métier,  
**afin de** permettre au flow RHO de détecter les patterns d'échec récurrents et proposer des fixes ciblés.

---

## 2. Origine & Cadrage Avant-Projet
- **Document Source** : Analyse de gap MLOOP-110-BE — 5 pipelines critiques, ~40 `except Exception`, 0 instrumentation
- **Hypothèse de Chiffrage Retenue** : 5 modules, ~8 `except Exception` chacun → instrumentation systématique
- **Enveloppe Macro Estimée** : M (fourchette de 1-2 jours)

---

## 3. Périmètre Sommaire
### In-Scope (Macro)
- `src/pipelines/qa_certifier.py` (4 `except Exception`) : Certification Gate 3/4, triangulation CEL, NLI, leakage
- `src/pipelines/vibe_check.py` (8 `except Exception`) : 15 contrôles pré-vol, violations AST, warnings Phase 4
- `src/pipelines/sync.py` (10 `except Exception`) : WikiFix, Graphify, FTS5 indexation, hypergraphe
- `src/pipelines/focus.py` (2 `except Exception`) : Verrou attention, persistance frontmatter
- `src/core/lifecycle.py` (6 `except Exception`) : Gates, transitions d'état, `approve_gate()`, zombie reap

### Out-of-Scope (Macro)
- Handlers CLI (MLOOP-142-BE)
- Workers Herdr (MLOOP-143-BE)
- Jira sync (MLOOP-144-BE)

---

## 4. Critères de Succès Préliminaires
- [ ] Chaque `except Exception` remplacé par `logger.error(..., extra={...}, exc_info=True)`
- [ ] Contexte métier : `story_id`, `gate`, `phase`, `check_name`, `file_path`, `violation_type`
- [ ] `mloop.log` trace : début/fin chaque pipeline, durée, statut, métriques clés
- [ ] Tests : 5 nouveaux tests `test_*_logging.py` valident la capture d'erreurs injectées

---

## 5. Zones d'Ombre & Questions pour la Session Grill-Me 1:1
> [!IMPORTANT]
> *Ces questions constituent l'ordre du jour obligatoire de la session contradictoire Grill-Me 1:1.*

- ❓ `qa_certifier.py` : Faut-il logger chaque niveau de triangulation (L1-L6) séparément ou agrégé ?
- ❓ `vibe_check.py` : Les 15 contrôles — un log par contrôle ou un log agrégé en fin de run ?
- ❓ `sync.py` : WikiFix vs Graphify vs FTS5 — log unifié ou par sous-système ?
- ❓ `lifecycle.py` : Transitions d'état — log à chaque transition ou seulement sur échec ?
- ❓ Niveau de log pour les succès : DEBUG (détail) ou INFO (synthèse) ?