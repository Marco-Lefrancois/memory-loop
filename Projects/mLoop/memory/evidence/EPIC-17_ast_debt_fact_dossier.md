# Dossier de Preuves — EPIC-17-MODULAR-REFACTORING (RULE-AST-01)

**Statut** : CURRENT
**Date** : 2026-09-22
**Récits couverts** : MLOOP-171-BE (cartographie), MLOOP-170-BE (pilote vibe_check), MLOOP-172-BE (pattern)
**Base légale** : ADR-0381 (Harnais Phase 3 — Linter AST), ADR-0202 (Modularité < 300 lignes), ADR-0369 (Robustesse Python), ADR-0376 (Audit 360° 7 couches)

---

## 1. Sources primaires
| Source | Emplacement | Usage |
|:---|:---|:---|
| Audit AST frais | `memory/evidence/codecheck_audit_epic17.txt` (317 lignes, exit 1 = violations) | Inventaire factuel des 39 fichiers |
| Top 40 priorisé | `memory/evidence/epic17_top40_oversized.txt` | Matrice de priorisation |
| Définition RULE-AST-01 | `src/core/ast_checker.py` L199-208 (`MAX_LINES` = seuil strict) | Référence de la règle |
| Backlog épopée | `Projects/mLoop/backlog/epic_modular_refactoring_ast_debt.md` | Cartographie et décisions ouvertes |

## 2. Extraits verbatim sourcés

**Extrait 1 — ast_checker.py (L199-208)** : « RULE-AST-01 : Modularité ADR-0202 / if line_count > cls.MAX_LINES: violations.append(AstViolation(rule_id="RULE-AST-01", ... corrective_action="Découper le module en composants spécialisés (ADR-0202).")) » ➔ **Fait établi** : le plafond est strict et la règle est codifiée dans le harnais Phase 3.

**Extrait 2 — Audit code-check 2026-09-22** : « Statut : [FAIL] VIOLATIONS | 317 lignes ... [RULE-AST-01] (L317) : Plafond modulaire dépassé : 317 lignes (seuil strict = 300) » ➔ **Fait établi** : l'audit est reproduisible et déterministe (exécution 702 ms, 0 dépendance externe).

**Extrait 3 — vibe_check.py (L10, L129)** : « def detect_project_lifecycle_stage(...) » / « def run_vibe_check(project_name: str, target_file: str = None, stage: str = None) -> dict: » ➔ **Fait établi** : 880 lignes concentrées en 2 définitions top-level ; le corps de `run_vibe_check` est monolithique. Toute extraction doit préserver cette signature (34 callers cités dans l'épopée, 19 fichiers détectés par grep aujourd'hui).

**Extrait 4 — sprint_backlog.md L202-204** : « EPIC-17-MODULAR-REFACTORING ... 318 fichiers, 81 violations, 38 dépassements de plafond modulaire (300 lignes) ... MLOOP_SKIP_HOOKS=1 (dette documentée) » ➔ **Fait établi** : engagement formel de résorption pris lors de la livraison EPIC-15.

## 3. Divergence constatée vs épopée (à arbitr en Grill)
- Épopée créée : 38 dépassements. Audit frais : **39 fichiers uniques** (+ `archify.py` 463L, créé par l'agent EPIC-16 hors plafond ; `server.py` 1632L en hausse).
- **Enseignement clé** : la dette s'aggrave sans garde-fou → la question du contrôle anti-aggravation (vibe-check/gate) devient prioritaire.

## 4. Contrats déclaratifs cibles
- Commande de reproduction : `python src/swarm.py code-check --all --project mLoop` (exit 1 tant que la dette existe)
- Livrable MLOOP-171-BE : inventaire (fichier, lignes, blast radius, criticité) + ordre de traitement
- Livrable MLOOP-170-BE : package `src/pipelines/vibe_check/` avec modules < 300L, signature publique intacte
- Livrable MLOOP-172-BE : `standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md`

## 5. Frontière active & Admission of Limits
- Le blast radius « 34 callers » de l'épopée date de sa rédaction ; la mesure fraîche (grep) donne 19 fichiers — la valeur exacte sera fixée par CodeGraph dans MLOOP-171-BE (l'agent ne présume pas).
- La matrice de priorisation finale dépend des arbitrages Grill (blast radius vs criticité fonctionnelle) — non pré-jugée ici.
- RULE-AST-02/03 sont hors périmètre (déjà conformes/traitées par le passé).
