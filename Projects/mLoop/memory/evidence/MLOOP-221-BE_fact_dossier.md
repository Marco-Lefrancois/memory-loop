# 📁 Dossier de Preuves Documentaires — `MLOOP-221-BE`

- **Récit** : `MLOOP-221-BE` — Harnais Automatisé Plannotator (Génération, Validation Visuelle HITL & Archivage Canonique) (EPIC-22-TOOLING-ECOSYSTEM-HARNESS)
- **Établi le** : 2026-09-24 — Cadrage Macro-Grill VALIDÉ
- **dossier_status**: VALIDATED
- **Décisions scellées** : Grill Macro EPIC-22 (Q2-A Topologie Projet Stricte & Mode Headless) → `ADR-014_epic-22_integration_operationnelle_ecosysteme_tooling.md`

---

## 1. Sources & Notes d'Atelier

- Épopée : `Projects/mLoop/backlog/epics/epic_tooling_ecosystem_harness.md`
- Fiche de Savoir SSOT : `docs/06-knowledge/06-tooling-ecosystem/KN-051_plannotator_workflow.md`
- Protocole SSOT : `standards/protocols/PHASE_FILES_AND_TEST_PLAN.md`
- ADR de référence : `standards/adr-system/0202-modularite-interne-agents.md` (≤ 300L)
- ADR de cadrage local : `Projects/mLoop/docs/01-architecture/ADR-014_epic-22_integration_operationnelle_ecosysteme_tooling.md`
- Code source existant : `src/commands/handlers/plannotator.py`

---

## 2. Matrice de Résolution des Conflits

| Conflit | Résolution |
| :--- | :--- |
| Dossier racine `plannotator/` vs Confinement projet | **Éradication Zéro-Orphelin (Q2-A)** : Suppression du dossier racine `plannotator/`. Confinement strict sous `Projects/<project>/memory/plan/`. |
| Emplacement du binaire | **Sanctuarisation Système** : Exécution depuis `%LOCALAPPDATA%\plannotator\plannotator.exe` avec fallback explicite. |
| Exécution CI/CD sans écran graphique | **Mode Headless `--approve`** : Possibilité de valider le plan sans blocage d'interface utilisateur en environnement automatisé. |

---

## 3. Extraits Verbatim Sourcés

**Extrait 1 — `docs/06-knowledge/06-tooling-ecosystem/KN-051_plannotator_workflow.md` :**
```text
"Plannotator doit opérer sur les plans de phase situés dans memory/plan/. Aucun fichier temporaire ou déchet ne doit résider à la racine du dépôt Memory Loop."
```
➔ **Fait établi (F-01)** : Le chemin de sauvegarde des plans annotés est canoniquement `Projects/<project>/memory/plan/<story_id>_phase_plan.annotated.md`.

**Extrait 2 — `standards/protocols/PHASE_FILES_AND_TEST_PLAN.md` :**
```text
"Le cycle Phase Plan -> Test Plan impose une validation explicite avant tout commencement d'écriture de code de production."
```
➔ **Fait établi (F-02)** : L'approbation Plannotator valide la transition vers le plan de test unitaire.
