---
id: MLOOP-140-BE
jira_key: ''
epic_key: EPIC-14-OBSERVABILITY-INSTRUMENTATION
type: Feature
title: Instrumentation Logging Point d'Entrée CLI (swarm.py, router.py, cli.py)
tags:
- core
- observability
- logging
- cli
origin: SPEC_SLICING
source_ref: MLOOP-110-BE_gap_analysis
macro_size: S
status: SHIPPED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by: []
created_at: '2026-09-21'
---

# 📖 MLOOP-140-BE : Instrumentation Logging Point d'Entrée CLI

## 1. Intention Métier (User Story)
**En tant qu'**Architecte mLoop,  
**je veux** que toutes les erreurs du point d'entrée CLI (`swarm.py`, `router.py`, `cli.py`) soient loguées dans `errors.log` et `mloop.log` avec contexte structuré,  
**afin de** permettre au flow RHO de corréler, diagnostiquer et proposer des corrections automatiques.

---

## 2. Origine & Cadrage Avant-Projet
- **Document Source** : Analyse de gap MLOOP-110-BE (RotatingFileHandler posé mais non utilisé au point d'entrée)
- **Hypothèse de Chiffrage Retenue** : 3 fichiers critiques, ~5 `except Exception`, 0 `ZeroFluffConsole.error` → instrumentation directe
- **Enveloppe Macro Estimée** : S (fourchette de 0.5-1 jour)

---

## 3. Périmètre Sommaire
### In-Scope (Macro)
- `src/swarm.py` : Ajouter `get_logger("cli")` + logger.error dans `main()` + `resolve_project_name()` + `get_project_context()`
- `src/commands/router.py` : Ajouter `get_logger("cli.router")` + logger.error dans `execute_cli()` + `_resolve_handler()` + `_build_parser()`
- `src/cli.py` : Étendre `get_logger("cli")` existant pour couvrir `ZeroFluffConsole` wrapper

### Out-of-Scope (Macro)
- Handlers CLI individuels (couvert par MLOOP-142-BE)
- Pipelines internes (couvert par MLOOP-141-BE, MLOOP-143-BE)

---

## 4. Critères de Succès Préliminaires
- [ ] Toute exception non gérée dans `swarm.py`/`router.py`/`cli.py` écrit dans `errors.log` avec `exc_info=True`
- [ ] Contexte structuré : `command`, `project`, `phase`, `story_id` via `extra={...}`
- [ ] `mloop.log` trace l'exécution complète (INFO) : commande, projet, durée, exit_code
- [ ] Tests : `python -m pytest tests/test_cli_logging.py` valide la capture

---

## 5. Zones d'Ombre & Questions pour la Session Grill-Me 1:1
> [!IMPORTANT]
> *Ces questions constituent l'ordre du jour obligatoire de la session contradictoire Grill-Me 1:1.*

- ❓ Faut-il logger aussi les `KeyboardInterrupt` (Ctrl-C) ou les laisser silencieux ?
- ❓ Le `exit_code` final doit-il être loggé au niveau INFO ou WARNING selon succès/échec ?
- ❓ `cli.py` wrap `ZeroFluffConsole` : faut-il patcher la classe ou créer un adapter `LoggingConsole` ?
- ❓ Niveau de log par défaut pour `mloop.log` : INFO (verbeux) ou WARNING (bruit réduit) ?