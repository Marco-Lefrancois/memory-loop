# Plan d'Extraction Modulaire — critic.py

> **Protocole** : `standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md`  
> **Story** : MLOOP-172-BE (EPIC-17-MODULAR-REFACTORING)  
> **Date** : 2026-09-23  
> **Statut** : DONE

---

## §1 Module Source & Callers

| Champ | Valeur |
|:------|:-------|
| Chemin source | `src/engine/rubber_duck/critic.py` |
| Lignes avant extraction | 392 L |
| Ko avant extraction | 16.3 Ko |
| Blast Radius (callers) | 3 fichiers |
| Méthode BR | ast_import_count |
| Lot EPIC-17 | Lot 2 (#11) |

**Callers identifiés** :
- `src/engine/rubber_duck/__init__.py` : `from src.engine.rubber_duck.critic import DevilAdvocateCritic, DevilAdvocateCritique`
- `src/pipelines/multi_draft.py` : `from src.engine.rubber_duck.critic import DevilAdvocateCritic, DevilAdvocateCritique`
- `src/pipelines/rubber_duck.py` : `from src.engine.rubber_duck.critic import DevilAdvocateCritic`

---

## §2 Familles de Responsabilités

| Famille | Symboles | Sous-module cible | Lignes estimées |
|:--------|:---------|:------------------|:----------------|
| Modèles de données | `DevilAdvocateCritique` | `_critic_models.py` | ~55 L |
| Analyse contradictoire (axes 1-4) | méthodes `evaluate_story`, axes 1-4 | `_critic_analysis.py` | ~185 L |
| Checks API (F/G) + persistance | `_run_api_traceability_checks`, helpers `_extract_*`, `_has_*`, `_persist_critique_to_evidence` | `_critic_api.py` | ~120 L |
| Orchestrateur | `DevilAdvocateCritic` (façade) | `__init__.py` | ~50 L |

---

## §3 Cas Spécial Applicable

- [ ] Registre déclaratif
- [ ] Singleton d'état
- [ ] Effets de bord à l'import
- [x] **Aucun cas spécial** — découpe standard §2

**Note** : `critic.py` n'a pas d'effets de bord à l'import, pas de singleton, pas de registre. Découpe par familles de responsabilités pure.

---

## §4 Livrables Physiques

| Artefact | Action | Lignes | Statut |
|:---------|:-------|-------:|:-------|
| `src/engine/rubber_duck/critic.py` | SHIM (ré-export) | 5 L | ✅ DONE |
| `src/engine/rubber_duck/critic/__init__.py` | NEW | ~50 L | ✅ DONE |
| `src/engine/rubber_duck/critic/_critic_models.py` | NEW | ~55 L | ✅ DONE |
| `src/engine/rubber_duck/critic/_critic_analysis.py` | NEW | ~185 L | ✅ DONE |
| `src/engine/rubber_duck/critic/_critic_api.py` | NEW | ~120 L | ✅ DONE |

---

## §5 Checklist Non-Régression

```
PRÉ-EXTRACTION
[x] code-check --file src/engine/rubber_duck/critic.py : 1 violation RULE-AST-01 (392L baseline)
[x] callers identifiés : 3 fichiers (rubber_duck/__init__.py, multi_draft.py, rubber_duck.py)

EXTRACTION
[x] Sous-modules créés, chacun ≤300 L / ≤15 Ko
[x] Shim de ré-export créé (critic.py → from package import *)
[x] __init__.py expose DevilAdvocateCritic et DevilAdvocateCritique
[x] Aucun import circulaire (python -c "import src.engine.rubber_duck.critic" → no error)

POST-EXTRACTION
[x] check fumée : python -m src.pipelines.import_smoke_check --module src/engine/rubber_duck/critic.py → VERT
[x] code-check --file sur chaque sous-module : PASS
[x] pytest tests/ -q --tb=no : zéro régression
[x] _registry non modifié → guide --sync non requis
[x] MLOOP_SKIP_HOOKS non utilisé
```

---

## §6 Résultats Post-Extraction

| Métrique | Avant | Après |
|:---------|------:|------:|
| Lignes module source (shim) | 392 L | 5 L |
| Lignes max sous-module | — | ~185 L (_critic_analysis.py) |
| Violations RULE-AST-01 | 1 | 0 |
| Fumée imports | — | ✅ VERT |

**Statut final** : DONE
