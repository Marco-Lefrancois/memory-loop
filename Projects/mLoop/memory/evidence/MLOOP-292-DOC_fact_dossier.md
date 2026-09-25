# 📁 Dossier de Preuves Documentaires — `MLOOP-292-DOC`

- **Récit** : `MLOOP-292-DOC` — Alignement des Blueprints Gates (G6/G7) & Protocole de Cadrage Phase 2 (EPIC-29-GRILL-V2-FRONTIER-SKILLS)
- **Établi le** : 2026-09-24 — Cadrage Macro-Grill VALIDÉ
- **dossier_status**: `VALIDATED`
- **Décisions scellées** : Grill Macro EPIC-29 (Q3-A Tri-État Conditionnel pour Gates G6 et G7) → `ADR-013_epic-29_grill_v2_frontier_rounds_ungrillable_context.md`

---

## 1. Sources & Notes d'Atelier

- Épopée : `Projects/mLoop/backlog/epics/epic_grill_v2_frontier_rounds_ungrillable_context.md`
- Blueprint de référence : `standards/blueprints/gates_grill_me.template.md`
- Protocole cadre de référence : `docs/01-architecture/framework/grill_with_docs_protocol.md`
- ADR de référence : `standards/adr-system/0389-grill-v2-frontier-rounds-ungrillable-handoff-context-budget.md`
- ADR de cadrage local : `Projects/mLoop/docs/01-architecture/ADR-013_epic-29_grill_v2_frontier_rounds_ungrillable_context.md`
- Maquettes : Aucune (récit purement documentaire et normatif)

---

## 2. Matrice de Résolution des Conflits

| Conflit | Résolution |
| :--- | :--- |
| Blocage binaire vs Sémantique tri-état | **Tri-état conditionnel (Q3-A)** : G6 supporte `PASS` (artefact présent), `SKIPPED` (backend pur), `FAIL` (zone d'ombre IHM) ; G7 supporte `PASS` (<80k), `WARNING` (80k-120k avec checkpoint), `FAIL` (>120k). |
| Mythe de la purge de contexte post-grill | **Interdiction constitutionnelle de purge** : Mise à jour du protocole de phase 2 pour proscrire le vidage du contexte avant la rédaction des récits. |
| Parité globale / projet des blueprints | **Synchronisation bidirectionnelle** : Le blueprint de base est enrichi de G6/G7 et répercuté lors des initialisations de projet. |

---

## 3. Extraits Verbatim Sourcés

**Extrait 1 — `standards/adr-system/0389-grill-v2-frontier-rounds-ungrillable-handoff-context-budget.md` :**
```text
"Porte G6 (Handoff Ungrillables) : PASS si toute décision d'interface est matérialisée par un artefact visuel ; SKIPPED si le récit est layer: backend."
```
➔ **Fait établi (F-01)** : Les récits sans composant IHM ne doivent pas être pénalisés par la porte G6.

**Extrait 2 — `standards/blueprints/gates_grill_me.template.md` (Version antérieure Lignes 1-15) :**
```text
Portes existantes : G1 (Arbre Décisionnel), G2 (DoD Complète), G3 (Contrats API), G4 (Tests & BDD), G5 (Alignement Stratégique).
```
➔ **Fait établi (F-02)** : Les portes G6 et G7 étaient absentes du blueprint officiel et nécessitent leur intégration canonique.
