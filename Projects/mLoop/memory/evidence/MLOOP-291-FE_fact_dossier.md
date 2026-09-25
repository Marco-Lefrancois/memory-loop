# 📁 Dossier de Preuves Documentaires — `MLOOP-291-FE`

- **Récit** : `MLOOP-291-FE` — Protocole Handoff & Staging des Prototypes Jetables (`scratch/prototypes/`) (EPIC-29-GRILL-V2-FRONTIER-SKILLS)
- **Établi le** : 2026-09-24 — Cadrage Macro-Grill VALIDÉ
- **dossier_status**: `VALIDATED`
- **Décisions scellées** : Grill Macro EPIC-29 (Q2-A Zéro-Build Sandbox & Promotion Conditionnelle vers `docs/05-assets/mockups/`) → `ADR-013_epic-29_grill_v2_frontier_rounds_ungrillable_context.md`

---

## 1. Sources & Notes d'Atelier

- Épopée : `Projects/mLoop/backlog/epics/epic_grill_v2_frontier_rounds_ungrillable_context.md`
- Source de référence : `docs/00-ingested/grill-me/12_things_people_get_wrong_with_grill_me_and_grill_with_docs.md`
- ADR de référence : `standards/adr-system/0389-grill-v2-frontier-rounds-ungrillable-handoff-context-budget.md`
- ADR de cadrage local : `Projects/mLoop/docs/01-architecture/ADR-013_epic-29_grill_v2_frontier_rounds_ungrillable_context.md`
- Arborescence ciblée : `Projects/<p>/scratch/prototypes/` et `docs/05-assets/mockups/`
- Maquettes : Prototypes HTML5 autonomes avec CDN Tailwind ou SVG vectoriel direct

---

## 2. Matrice de Résolution des Conflits

| Conflit | Résolution |
| :--- | :--- |
| Débat textuel IHM vs Prototype interactif | **Prototype Handoff obligatoire (Q2-A)** : Toute question touchant à l'ergonomie visuelle est matérialisée en code statique exécutable immédiatement. |
| Serveur Node / npm lourd vs Zéro-Build | **Zéro-Build absolu** : Fichiers HTML5 avec CDN Tailwind ou SVG visualisables directement via `file:///` sans build ni dépendance. |
| Pollution de la documentation vs Nettoyage | **Staging en `scratch/` et promotion conditionnelle** : Les prototypes jetables restent en scratch ignoré par git, seuls les prototypes validés sont copiés dans `docs/05-assets/mockups/`. |

---

## 3. Extraits Verbatim Sourcés

**Extrait 1 — `docs/00-ingested/grill-me/12_things_people_get_wrong_with_grill_me_and_grill_with_docs.md` :**
```text
"When you hit an ungrillable question, use the handoff pattern: grill -> prototype -> grill again. Don't debate layout in text."
```
➔ **Fait établi (F-01)** : Les questions de layout et d'interaction ne doivent jamais faire l'objet de longues argumentations textuelles ; elles exigent un artefact visuel immédiat.

**Extrait 2 — `standards/adr-system/0389-grill-v2-frontier-rounds-ungrillable-handoff-context-budget.md` :**
```text
"Le prototype doit être généré en moins de 60 secondes et s'ouvrir directement dans le navigateur de l'utilisateur via le protocole file:///."
```
➔ **Fait établi (F-02)** : L'expérience utilisateur mLoop impose une fluidité totale sans latence de configuration d'environnement.
