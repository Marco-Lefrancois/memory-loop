# 📁 Dossier de Preuves Documentaires — `MLOOP-293-FULL`

- **Récit** : `MLOOP-293-FULL` — Validation E2E sur Cas Réel (Metro FOOD) & Certification Vibe-Check (EPIC-29-GRILL-V2-FRONTIER-SKILLS)
- **Établi le** : 2026-09-24 — Cadrage Macro-Grill VALIDÉ
- **dossier_status**: `VALIDATED`
- **Décisions scellées** : Grill Macro EPIC-29 (Q4-A Cas Réel Pilote Metro FOOD & Certification Vibe-Check 0 FAIL) → `ADR-013_epic-29_grill_v2_frontier_rounds_ungrillable_context.md`

---

## 1. Sources & Notes d'Atelier

- Épopée : `Projects/mLoop/backlog/epics/epic_grill_v2_frontier_rounds_ungrillable_context.md`
- Projet pilote : `Projects/Metro_FOOD/`
- ADR de référence : `standards/adr-system/0389-grill-v2-frontier-rounds-ungrillable-handoff-context-budget.md`
- ADR de cadrage local : `Projects/mLoop/docs/01-architecture/ADR-013_epic-29_grill_v2_frontier_rounds_ungrillable_context.md`
- Outil souverain d'audit : `src/commands/handlers/vibe_check.py`
- Maquettes : Maquette pilote Handoff issue du cadrage Metro FOOD

---

## 2. Matrice de Résolution des Conflits

| Conflit | Résolution |
| :--- | :--- |
| Validation par tests unitaires isolés vs Cas Réel | **Pilote réel en conditions opérationnelles (Q4-A)** : Exécution de bout en bout sur une initiative complexe du projet Metro FOOD pour valider empiriquement le gain de vélocité. |
| Métrique subjective vs Preuve quantitative | **Mesure d'efficacité chiffrée** : Suivi rigoureux du nombre de tours d'échange (réduction $\ge 50\%$) et respect des seuils de tokens. |
| Clôture d'épopée sans vérification globale | **Gate Vibe-Check 0 FAIL obligatoire** : Aucun récit de l'épopée ne peut être finalisé sans le passage au vert du Vibe-Check souverain. |

---

## 3. Extraits Verbatim Sourcés

**Extrait 1 — `standards/adr-system/0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md` :**
```text
"Toute nouvelle capacité de cadrage ou d'orchestration doit être validée sur un cas métier concret avant d'être déclarée prête pour l'ensemble du portefeuille."
```
➔ **Fait établi (F-01)** : La validation E2E sur Metro FOOD répond directement aux impératifs constitutionnels de l'ADR-0376.

**Extrait 2 — `standards/adr-system/0389-grill-v2-frontier-rounds-ungrillable-handoff-context-budget.md` :**
```text
"Le succès d'un cadrage v2 se mesure par la capacité à produire des récits de qualité 6/6 sans réinitialisation de contexte en moins de la moitié du temps habituel."
```
➔ **Fait établi (F-02)** : L'objectif de réduction de 50% des interactions est la cible formelle de validation du pilote.
