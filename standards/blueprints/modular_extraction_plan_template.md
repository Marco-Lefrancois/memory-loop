# Plan d'Extraction Modulaire — <MODULE>

> **Protocole** : `standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md`  
> **Story** : MLOOP-172-BE (EPIC-17-MODULAR-REFACTORING)  
> **Date** : <YYYY-MM-DD>  
> **Statut** : DRAFT | IN_PROGRESS | DONE

---

## §1 Module Source & Callers

| Champ | Valeur |
|:------|:-------|
| Chemin source | `src/<chemin>/<module>.py` |
| Lignes avant extraction | <N> L |
| Ko avant extraction | <N> Ko |
| Blast Radius (callers) | <N> fichiers |
| Méthode BR | ast_import_count |
| Lot EPIC-17 | Lot 1 / 2 / 3 |

**Callers identifiés** :
- `src/.../<caller1>.py`
- `src/.../<caller2>.py`

---

## §2 Familles de Responsabilités

| Famille | Symboles | Sous-module cible | Lignes estimées |
|:--------|:---------|:------------------|:----------------|
| <Famille 1> | `Foo`, `bar()` | `_<module>_<famille1>.py` | ~<N> L |
| <Famille 2> | `Baz`, `qux()` | `_<module>_<famille2>.py` | ~<N> L |

---

## §3 Cas Spécial Applicable

- [ ] Registre déclaratif → voir §3.1 du protocole
- [ ] Singleton d'état → voir §3.2 du protocole
- [ ] Effets de bord à l'import → voir §3.3 du protocole
- [x] Aucun cas spécial (découpe standard §2)

---

## §4 Livrables Physiques

| Artefact | Action | Lignes | Statut |
|:---------|:-------|-------:|:-------|
| `src/<chemin>/<module>.py` | SHIM (ré-export) | ≤5 L | ☐ |
| `src/<chemin>/<module>/__init__.py` | NEW | <N> L | ☐ |
| `src/<chemin>/<module>/_<famille1>.py` | NEW | <N> L | ☐ |
| `src/<chemin>/<module>/_<famille2>.py` | NEW | <N> L | ☐ |

---

## §5 Checklist Non-Régression

```
PRÉ-EXTRACTION
[ ] code-check --file <module> : <N_violations> violations (baseline)
[ ] pytest tests/ -q --tb=no : <N_avant> PASS, 0 FAIL (baseline)

EXTRACTION
[ ] Sous-modules créés, chacun ≤300 L / ≤15 Ko
[ ] Shim de ré-export créé
[ ] __init__.py expose tous les symboles publics
[ ] Aucun import circulaire

POST-EXTRACTION
[ ] check fumée : python -m src.pipelines.import_smoke_check --module src/<chemin>/<module>.py → VERT
[ ] code-check --file sur chaque sous-module : PASS
[ ] pytest tests/ -q --tb=no : <N_après> PASS = <N_avant> (zéro régression)
[ ] Si _registry modifié : guide --sync exécuté
[ ] Plan archivé mis à jour
[ ] MLOOP_SKIP_HOOKS non utilisé (ou audit log justifié)
```

---

## §6 Résultats Post-Extraction

| Métrique | Avant | Après |
|:---------|------:|------:|
| Lignes module source | <N> L | ≤5 L (shim) |
| Lignes max sous-module | — | <N> L |
| Tests PASS | <N> | <N> |
| Violations RULE-AST-01 | 1 | 0 |
| Fumée imports | — | ✅ VERT |

**Statut final** : DONE / BLOCKED — <raison>
