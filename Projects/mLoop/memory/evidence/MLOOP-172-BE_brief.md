# Brief Worker — MLOOP-172-BE (P5-2)

> **Story** : `Projects/mLoop/backlog/stories/MLOOP-172-BE.md`  
> **Statut cible** : passer en `IN_DEV` uniquement après harvest MLOOP-171-BE (orchestrateur). INVEST **6/6** (réévalué 2026-09-23). `grill_me: DONE` · `blocked_by: MLOOP-170-BE` = **levé** (DONE_TESTED).  
> **Fact dossier** : `Projects/mLoop/memory/evidence/MLOOP-172-BE_fact_dossier.md`  
> **Prérequis** : rapport MLOOP-171-BE + matrice Beachhead disponibles sous `memory/evidence/` (lire si présents).

---

## 1. Mission

Établir le **protocole d’extraction modulaire réutilisable** issu du pilote MLOOP-170-BE, l’**armer** (check fumée + contrôle Vibe-Check Phase 3), et le **valider** sur un second module indépendant.

---

## 2. Livrables (critères d’acceptation)

### A. Protocole v1 exhaustif (OQ-172-01)
Créer **`standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md`** couvrant :

1. **Cas général** (issu du pilote `vibe_check.py` 880L → package `src/pipelines/vibe_check/` <300L) :
   - Étapes : diagnostic `code-check --all` → découpage par famille de responsabilités → shim de ré-export si nécessaire → suite tests verte → signature publique inchangée → `code-check` du module extrait <300L.
   - Garanties : rétrocompatibilité imports, signature publique, non-régression tests.
   - Checklist non-régression intégrée (exigible à chaque lot).
2. **3 cas spéciaux avec contre-exemples** (chacun : description, risque, pattern sûr, **contre-exemple explicite**) :
   - **Registres déclaratifs** (ex : `src/commands/_registry.py` 2028L — registres partiels par domaine sans perdre la découverte).
   - **Singletons d’état** (ex : modules d’état partagée / cache process-global).
   - **Effets de bord à l’import** (side effects au import : logging config, regex compile globales, ouverture de fichiers).
3. **Lien vers le garde-fou anti-aggravation** MLOOP-171-BE (delta size + audit `MLOOP_SKIP_HOOKS`) — le protocole s’appuie dessus pour empêcher la ré-aggravation pendant les lots.

Éventuel gabarit : `standards/blueprints/modular_extraction_plan_template.md` (plan d’extraction par lot).

### B. Check de fumée imports (OQ-172-02)
- Script/module **exécutable** (idéalement sous `src/` avec commande CLI **ou** module testable `python -m ...` — si nouvelle commande CLI → **`python src/swarm.py guide --sync`** obligatoire ADR-0370).
- Comportement : pour un module extrait `X`, résoudre les imports des callers connus (grep/AST) et signaler tout symbole non résolu **avec le fichier caller exact**.
- Léger : **pas** de comparaison exhaustive de surface AST.
- Exigé à chaque lot (documenté dans le protocole + automatisable).

### C. Contrôle Vibe-Check Phase 3 (OQ-172-03)
- Nouveau check dans le package `src/pipelines/vibe_check/` (préférer `_vc_build.py` ou module satellite **<300L** ADR-0202) — **ne pas dépasser 300L** sur les modules existants.
- Nom suggestion : `check_22_extraction_protocol` (ou équivalent non conflitant avec 01→21 existants).
- Règle Phase 3 BUILD : si working tree modifie un fichier **déjà** en dépassement RULE-AST-01 **ou** un package d’extraction en cours :
  - **FAIL** si un plan d’extraction absent (`memory/plan/implementation_plan_*extraction*` ou convention documentée dans le protocole) **et** fumée non exécutable/rouge ;
  - **PASS/WARNING** selon la combinaison documentée (détailler la matrice dans le protocole).
- S’inscrire dans `run_vibe_check` (`src/pipelines/vibe_check/__init__.py`) sans faire exploser ce fichier (271L actuellement — marge max 29L ; si trop juste → check dans un sous-module importé 1 ligne).
- Tests miroirs style `tests/vibe_check/*_test.py` (nouveau fichier `extraction_test.py` ou équivalent) — **verts**.

### D. Validation sur un second module (garantie d’extraction)
- Choisir un module **en dépassement** de la matrice Beachhead MLOOP-171-BE (lot 1 prioritaire, pas `_registry.py` 2028L d’emblée — préférer un module ~300-500L raisonnable, ex. un sous-candidat du top 5 si taille gérable, sinon le plus petit des 39 déjà >300L avec BR élevé).
- Appliquer le protocole **en conditions réelles** :
  - Module source < **300L** après extraction (chaque fichier).
  - **Zéro import cassé** (check fumée vert + suite tests ciblée + full si faisable).
  - Plan d’extraction archivé : `Projects/mLoop/memory/plan/implementation_plan_<MODULE>_extraction.md` (ou convention MLOOP-172 dans le protocole).
- **Ne pas** refactorer un monolithe >900L dans ce récit (reste en lots EPIC-17 ultérieurs).

### E. Mise à jour SSOT
- `Projects/mLoop/backlog/sprint_backlog.md` : **ne pas** toucher le statut (orchestrateur).
- `Projects/mLoop/backlog/epic_modular_refactoring_ast_debt.md` : marquer MLOOP-172 fait quand DONE (orchestrateur au harvest — worker peut proposer le diff dans le rapport).
- Épingle protocole dans le fact dossier / hypergraph via `python src/swarm.py sync --project mLoop` en fin de mission si commande dispo.

---

## 3. Contraintes strictes

| Contrainte | Détail |
|:---|:---|
| ADR-0369 | `timeout=` explicite partout ; `with` sur ressources ; zéro `except: pass` nu ; `logger.debug(exc_info=True, extra={...})`. |
| ADR-0202 | Tout nouveau fichier Python ≤300L / 15 Ko. |
| ADR-0370 | Si ajout commande `_registry.py` → `guide --sync` immédiat. |
| ADR-0376 | Éviter de modifier `src/core/ast_checker.py` ; si indispensable, documenter audit 7 couches dans le rapport. |
| Git | **Aucun commit/push**. |
| Story | Ne pas modifier le frontmatter `status:` de MLOOP-172-BE (orchestrateur). |
| API | Exemption ADR-0319 : protocole documentaire, **zéro route inventée**. |
| Working dir | `C:\Memory Loop` |

---

## 4. Méthode de fin (DONE)

1. Rapport : `Projects/mLoop/memory/evidence/MLOOP-172-BE_report.md`  
   sections : Protocole (chemin, sections couvertes 3 cas spéciaux) · Fumée (usage) · Vibe-Check (nom check, tests) · Module validé (avant/après, tests, fumée) · Écarts/risques.
2. Dernière ligne : `STATUS: DONE` ou `STATUS: BLOCKED — <raison>`.
3. Tests ciblés verts ; aucun CODE FAIL introduit sur RULE-AST-02/03/04.
4. Ne pas fermer le worker (orchestrateur harvest).
