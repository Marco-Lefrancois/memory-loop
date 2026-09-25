# 📁 Dossier de Preuves Documentaires — `MLOOP-222-BE`

- **Récit** : `MLOOP-222-BE` — Pipeline Décisionnel Wayfinder (Cartographie de Décisions & Sous-Agents Asynchrones AFK) (EPIC-22-TOOLING-ECOSYSTEM-HARNESS)
- **Établi le** : 2026-09-24 — Cadrage Macro-Grill VALIDÉ
- **dossier_status**: VALIDATED
- **Décisions scellées** : Grill Macro EPIC-22 (Q3-A Frontière & Résolution Continue, HITL vs AFK) → `ADR-014_epic-22_integration_operationnelle_ecosysteme_tooling.md`

---

## 1. Sources & Notes d'Atelier

- Épopée : `Projects/mLoop/backlog/epics/epic_tooling_ecosystem_harness.md`
- Fiche de Savoir SSOT : `docs/06-knowledge/06-tooling-ecosystem/KN-052_wayfinder_fog_of_war.md`
- Ingestion technique : `docs/00-ingested/wayfinder/`
- ADR de référence : `standards/adr-system/0202-modularite-interne-agents.md` (≤ 300L)
- ADR de cadrage local : `Projects/mLoop/docs/01-architecture/ADR-014_epic-22_integration_operationnelle_ecosysteme_tooling.md`
- Code source existant : `src/pipelines/wayfinder.py`

---

## 2. Matrice de Résolution des Conflits

| Conflit | Résolution |
| :--- | :--- |
| Arbitrage humain synchrone vs Recherche longue | **Typologie Étanche (Q3-A)** : Distinction stricte entre tickets **HITL** (décision humaine synchrone) et **AFK** (investigation déléguée à sous-agent `/research` asynchrone). |
| Emplacement de la carte | **Confinement Projet** : Carte stockée sous `Projects/<project>/memory/wayfinder/wayfinder_map.md`. |
| Transition vers spécification | **Déblocage déterministe** : Commande `mloop wayfinder resolve` dissipant le brouillard et débloquant les dépendances vers `to-spec`. |

---

## 3. Extraits Verbatim Sourcés

**Extrait 1 — `docs/06-knowledge/06-tooling-ecosystem/KN-052_wayfinder_fog_of_war.md` :**
```text
"Wayfinder modélise le brouillard de guerre sous forme de graphe de décisions. Résoudre un ticket à la frontière débloque les chemins de spécification technique."
```
➔ **Fait établi (F-01)** : La commande `mloop wayfinder frontier` permet d'identifier immédiatement les décisions bloquantes sans navigation manuelle.

**Extrait 2 — `standards/adr-system/0202-modularite-interne-agents.md` :**
```text
"Les composants doivent être découpés en modules de responsabilité unique ne dépassant pas 300 lignes."
```
➔ **Fait établi (F-02)** : L'évolution de `src/pipelines/wayfinder.py` doit respecter la modularité ≤ 300L.
