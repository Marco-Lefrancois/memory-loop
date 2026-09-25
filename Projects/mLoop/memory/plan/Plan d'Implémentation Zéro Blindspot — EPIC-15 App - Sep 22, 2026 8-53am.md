---
created: 2026-09-22T12:53:07.949Z
source: plannotator
tags: [plannotator, memory-loop, impl, mentation, blindspot]
---

[[Plannotator Plans]]

# Plan d'Implémentation Zéro Blindspot — EPIC-15 : Application du Chargement des Directives Projet & Ancrage SSOT

**Autorité** : ADR-0376 (Audit 360° en 7 Couches) · Plan-First ADR-0305 Niveau 3 (Critique — cœur framework)
**Archivé** : `Projects/mLoop/memory/plan/implementation_plan_EPIC-15-DIRECTIVES-SSOT.md`
**Portée** : 6 récits `MLOOP-160` à `MLOOP-165-BE`, validés struct-check (6/6) + rubber-duck (0 rejet, Trust 83.2).

---

## ✅ Prérequis FRAMEWORK_STATE (ADR-0352) — tous cochés
Status source vérifié (IN_ANALYZE) · pas de certificat NLI à régénérer · struct-check en §5A · verification_harness défini · transition d'état valide.

---

## 🚨 Points nécessitant TON approbation explicite

1. **Changement de sémantique du verdict Vibe-Check pour TOUS les projets** (D1) : `is_valid` passe de binaire (`passed == total`) à tri-état (PASS/WARNING/FAIL). Scores recalculés au fil de l'eau. Impact transverse assumé.
2. **Modification de la charte racine `AGENTS.md`** (+ miroirs GEMINI/CLAUDE auto-sync) : nouvelle clause §4.1.
3. **Correction de `Projects/BoireFrere_Segment2/AGENTS.md`** : un fichier de projet client est touché — uniquement sa charte de gouvernance, jamais son code. À valider vs herméticité (OQ-03).
4. **Deux nouveaux contrôles** dans le guardrail (directives + ancrage visuel), tous deux WARNING non bloquants.

---

## 📦 Modifications par couche (ADR-0376)

| Couche | Récit | Fichier | Action |
| :--- | :--- | :--- | :--- |
| 1 Blueprints | — | — | `[NO-OP]` confirmé |
| 2 Protocoles | 160 | `standards/protocols/PROJECT_DIRECTIVES_SSOT_PROTOCOL.md` | `[NEW]` ~40L |
| 3 ADR | 161 | `standards/adr-system/0384-*.md` + `README.md` | `[NEW]` + `[MODIFY]` index |
| 4 Chartes | 161 | `AGENTS.md` (+miroirs) + `Projects/BoireFrere_Segment2/AGENTS.md` | `[MODIFY]` |
| 5 Skills | 162 | `.agents/skills/grill/SKILL.md` | `[MODIFY]` Étape 0 |
| 6 Core | 163 | `src/pipelines/vibe_check.py` | `[MODIFY]` Check directives + correctif tri-état |
| 6 Core | 165 | `src/pipelines/vibe_check.py` | `[MODIFY]` Check ancrage visuel (étend Check 10) |
| 7 Tests | 164 | `tests/test_vibe_check_directives_ssot.py` (NEW) + réalignement 10 tests | `[NEW]` + `[MODIFY]` |

**Blast radius core** : `run_vibe_check` = 34 callers + 10 fichiers de tests. Signature de sortie `dict` inchangée.

---

## 🛡️ Risques principaux & parades
- Correctif `is_valid` casse des tests → réalignement volontaire (récit 164), `uv run pytest` vert obligatoire.
- Check directives bloque un projet sans `directives/` → conditionnalité stricte (absent = PASS), test dédié verrouille.
- Herméticité Boire → seule la charte de gouvernance touchée, jamais le code. Signalé OQ-03.

---

## ✅ Recette Triple Gate
```
uv run pytest tests/ -q
struct-check --project mLoop
vibe-check --project BoireFrere_Segment2   # nouveau check PASS
vibe-check --project Metro_FOOD            # non-régression : inchangé
code-check --all                           # AST ADR-0369
```
DoD : pytest 100% vert · code-check sans nouvelle violation · ADR indexé + parité miroirs · walkthrough rédigé.

---

## 🔢 Séquence d'exécution
160 → 161 → 162 ∥ 163 → 165 → 164 → certification.

**Aucune ligne de code ne sera écrite avant ton approbation explicite (ADR-0376).**

---

## Questions ouvertes
- **OQ-01** : ADR 0384 — reconfirmer le slot libre au build, re-numéroter si collision.
- **OQ-02** : vérifier qu'aucun test n'assertait un FAIL global sur un WARNING Check 17.
- **OQ-03** : la correction de la charte Boire reste-t-elle dans cette epic framework, ou bascule dans la reprise Boire distincte (D6) ?