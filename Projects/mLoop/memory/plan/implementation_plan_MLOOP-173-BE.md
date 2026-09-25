# Plan d'Implémentation — MLOOP-173-BE
# Extraction Modulaire de src/state.py (BR=78)
# Date : 2026-09-23 | Statut : DONE

## §1. Callers identifiés
- BR=78 (78 fichiers importent src/state.py — identifiés via epic17_prioritization_matrix.md)
- Aucun caller modifié — rétrocompatibilité via package src/state/__init__.py

## §2. Familles et bornes de lignes (src/state.py original 770L)

| Famille | Sous-module | Lignes source |
|:--------|:------------|:--------------|
| Exceptions + Enums + Pydantic models + SavepointManager | `_state_core.py` | L1-L336 + import L79 remonté |
| Méthodes FSM LoopState (StateAccessorsMixin) | `_state_accessors.py` | L384-L524 |
| Méthodes I/O LoopState (StateSerializerMixin) | `_state_serializer.py` | L389-L770 |
| Assemblage LoopState + singleton + re-exports | `__init__.py` | — |

## §3. Architecture Package (Q2 Mixin Option A)
```
src/state/
├── __init__.py          # LoopState(StateAccessorsMixin, StateSerializerMixin, BaseModel) + re-exports
├── _state_core.py       # Exceptions, Enums, Pydantic models, SavepointManager
├── _state_accessors.py  # StateAccessorsMixin : FSM, query_graph, search_nodes
└── _state_serializer.py # StateSerializerMixin : checkpoint, save/load_to/from_graph, audit, journal, discover_backlog
```
- Singleton §3.2 : LoopState instanciée UNIQUEMENT par les callers (jamais dans les sous-modules)
- src/state.py (fichier original) : SUPPRIMÉ — le package src/state/ est l'entrée canonique

## §4. Checklist Non-Régression

### PRÉ-EXTRACTION
- [x] code-check --file src/state.py : violation RULE-AST-01 (770L > 300L) — baseline documentée
- [x] pytest baseline : import OK (python -c "from src.state import *" → OK)
- [x] Callers identifiés : BR=78

### EXTRACTION
- [x] Sous-modules créés : _state_core.py (298L/9.7Ko), _state_accessors.py (176L/7.4Ko), _state_serializer.py (264L/11.6Ko), __init__.py (136L/4.8Ko)
- [x] Package src/state/ est l'entrée canonique (src/state.py original supprimé)
- [x] __init__.py expose tous les symboles publics via __all__
- [x] Aucun import circulaire

### POST-EXTRACTION
- [x] CHECK 1 — from src.state import * : PASS
- [x] CHECK 2 — code-check --file sur chaque module : 4/4 PASS
- [x] CHECK 3 — Audit AST singleton : ZÉRO instanciation LoopState/ProjectState dans sous-modules
- [x] CHECK 4 — code-check swarm : 4/4 conformes, 0 violation
- [x] CHECK 5 — import_smoke_check : ✅ Aucun symbole non résolu détecté
- [x] pytest tests/ -x -q : 1380 PASSED, 0 FAILED (baseline ≥1306 — SURPASSÉE)
- [x] MLOOP_SKIP_HOOKS non utilisé

## §5. Résultats Finaux

| Check | Résultat |
|:------|:---------|
| from src.state import * | ✅ PASS |
| code-check 4 modules | ✅ 4/4 PASS (≤300L, ≤15Ko) |
| Audit AST singleton | ✅ PASS (0 instanciation hors __init__) |
| pytest 1380 tests | ✅ 1380 PASSED, 0 FAILED |
| import_smoke_check | ✅ PASS |

**STATUT : DONE — Prêt pour merge.**
