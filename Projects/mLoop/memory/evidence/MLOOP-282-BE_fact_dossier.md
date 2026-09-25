# 📁 Dossier de Preuves Documentaires — `MLOOP-282-BE`

- **Récit** : `MLOOP-282-BE` — Scission Modulaire de `grill_engine.py` (Plafond Strict ADR-0202 ≤ 300L)
- **Établi le** : 2026-09-24 — Cadrage Macro-Grill VALIDÉ
- **dossier_status**: `VALIDATED`
- **Décisions scellées** : Grill Macro EPIC-28 (Q4-A Package modulaire `src/pipelines/grill/` + shim) → `ADR-012_epic-28_assainissement_generateur_adr_clean_architecture.md`

---

## 1. Sources & Notes d'Atelier

- Épopée : `file:///C:/Memory%20Loop/Projects/mLoop/backlog/epics/epic_adr_clean_architecture.md`
- Règle constitutionnelle : `RULE-AST-01` (Fichiers ≤ 300 lignes, ≤ 15 Ko)
- Code source existant : `src/pipelines/grill_engine.py` (441 lignes)
- ADR associés : ADR-0202 (Modularité interne), ADR-0320, ADR-0376, ADR-012
- Maquettes : Aucune (récit backend pur)

---

## 2. Matrice de Résolution des Conflits

| Conflit | Résolution |
| :--- | :--- |
| Monolithe unique vs Package sous-modules | **Package modulaire** : `src/pipelines/grill/` pour découpage spécialisé ≤ 300L (Q4-A). |
| Rupture d'imports vs Shim rétrocompatible | **Shim de 15L** : `src/pipelines/grill_engine.py` réexporte `GrillEngine` sans rien casser (Q4-A). |

---

## 3. Extraits Verbatim Sourcés

**Extrait 1 — Bilan `code-check` AST sur `src/pipelines/grill_engine.py` :**
```text
Statut : [FAIL] VIOLATIONS | 440 lignes | 18004 octets
  * [RULE-AST-01] (L440) : Plafond modulaire dépassé : 440 lignes (seuil strict = 300).
  * [RULE-AST-01] (L440) : Taille de fichier excessive : 18004 octets (seuil strict = 15360 octets / 15 Ko).
```
➔ **Fait établi (F-01)** : Dépassement avéré du plafond constitutionnel bloquant les commits pre-commit.
