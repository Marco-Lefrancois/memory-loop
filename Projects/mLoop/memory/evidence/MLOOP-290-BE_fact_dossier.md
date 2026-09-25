# 📁 Dossier de Preuves Documentaires — `MLOOP-290-BE`

- **Récit** : `MLOOP-290-BE` — Câblage CLI Swarm (Options `--mode round/atomic` & Alertes Health) (EPIC-29-GRILL-V2-FRONTIER-SKILLS)
- **Établi le** : 2026-09-24 — Cadrage Macro-Grill VALIDÉ
- **dossier_status**: `VALIDATED`
- **Décisions scellées** : Grill Macro EPIC-29 (Q1-A Asymétrie CLI, Mode Round par défaut en Macro vs 1:1 Atomic en Micro & Alertes Health) → `ADR-013_epic-29_grill_v2_frontier_rounds_ungrillable_context.md`

---

## 1. Sources & Notes d'Atelier

- Épopée : `Projects/mLoop/backlog/epics/epic_grill_v2_frontier_rounds_ungrillable_context.md`
- Source de référence état de l'art : `docs/00-ingested/grill-me/12_things_people_get_wrong_with_grill_me_and_grill_with_docs.md`
- ADR de référence : `standards/adr-system/0389-grill-v2-frontier-rounds-ungrillable-handoff-context-budget.md`
- ADR de cadrage local : `Projects/mLoop/docs/01-architecture/ADR-013_epic-29_grill_v2_frontier_rounds_ungrillable_context.md`
- Code source ciblé : `src/commands/handlers/architecture.py`, `src/swarm.py`
- Maquettes : Aucune (récit backend pur, outillage CLI et monitoring in-process)

---

## 2. Matrice de Résolution des Conflits

| Conflit | Résolution |
| :--- | :--- |
| Mode 1:1 systématique vs Traitement par lots | **Asymétrie contextuelle (Q1-A)** : `grill-project` adopte `--mode round` par défaut (lots de 2-4 questions) tandis que `grill-me --story` conserve `--mode atomic` (1:1 strict). |
| Purge de contexte post-grill vs Rétention continue | **Rétention continue absolue** : Aucune commande ni hook ne doit purger la session. Le modèle enchaîne directement avec le contexte chaud. |
| Détection Dumb Zone en production | **Surveillance passive locale** : Estimation déterministe basée sur la taille des transcripts (len // 4) sans dépendance API externe. |

---

## 3. Extraits Verbatim Sourcés

**Extrait 1 — `docs/00-ingested/grill-me/12_things_people_get_wrong_with_grill_me_and_grill_with_docs.md` :**
```text
"When grilling at a macro level, asking 15 individual questions one-by-one destroys user momentum. Group independent orthogonal questions into frontier rounds."
```
➔ **Fait établi (F-01)** : Le groupement de questions orthogonales en rounds divise le délai de cadrage sans dégrader la qualité des arbitrages.

**Extrait 2 — `standards/adr-system/0389-grill-v2-frontier-rounds-ungrillable-handoff-context-budget.md` (Lignes 45-52) :**
```text
"Dumb Zone : Au-delà de 120k tokens, l'attention se dégrade. Interdiction de purge de contexte : basculer immédiatement en rédaction plutôt que d'effacer la mémoire."
```
➔ **Fait établi (F-02)** : La surveillance du budget de contexte est une exigence de sécurité cognitive pour prévenir les hallucinations et l'amnésie post-grill.
