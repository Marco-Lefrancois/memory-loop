# ADR-0389 : Harnais d'Évaluation des Compétences Agentiques (Skill Eval Harness Framework)

> **Statut :** Accepté — Session Grill EPIC-24 (2026-09-24)
> **Date :** 2026-09-24
> **Auteurs :** Équipe mLoop & Architecte Agentique (Co-décision PO Marco)
> **Périmètre :** `src/pipelines/skill_eval.py`, `src/pipelines/skill_flywheel.py`, `src/pipelines/vibe_check/_vc_skills.py`, `memory/evals/`, `.agents/skills/*/SKILL.md`
> **Références :** ADR-0308 (Evals Continue) · ADR-0348 (WikiSkill Tri-Couches) · ADR-0202 (Modularité ≤ 300L) · ADR-0375 (Traçabilité Radicale) · ADR-0384 (Verdict tri-état Vibe-Check)

---

## 1. Contexte & Problématique

L'écosystème mLoop compte **39 compétences déclarées** sous `.agents/skills/*/SKILL.md`. L'audit de leur qualité reposait sur deux approches partielles :

1. **`SkillDoctor`** : hygiène budgétaire statique (token count, longueur description) — *"Lint is a floor, not the goal."*
2. **`SkillEvalEngine`** (existant dans `skill_eval.py`) : rubrique 4 axes × 25 pts = 100 pts, assertions déterministes sur le contenu du manifeste.

Ces outils mesurent le **manifeste**, pas le **comportement**. Il manquait :
- Un référentiel de **Golden Datasets** (cas nominaux, limites, adversariaux) pour chaque skill.
- Une **boucle de rétroaction** (Flywheel) couplant les résultats d'évaluation à l'auto-tuning de manifeste avec protection HITL.
- Un **guardrail Vibe-Check** (Check 23) signalant les dégradations lors du contrôle pré-vol.
- Une **vue Dashboard** consolidée pour la surveillance opérationnelle.

---

## 2. Décisions d'Architecture

### A. Scope Système 1 Uniquement (v1)

**Décision :** L'évaluation reste **statique déterministe (Système 1)** pour cette épopée. L'évaluation comportementale LLM-as-a-judge (Système 2, tester le déclenchement réel de la skill) est différée à EPIC-24-v2.

**Motivation :** L'évaluation Système 2 requiert une infrastructure LLM-as-a-judge dédiée avec budget de tokens maîtrisé. L'apport du Système 1 seul est déjà substantiel pour les 39 skills (assertions sur mots-clés, déclencheurs, ancrage, résilience).

### B. Extension de l'Existant — Pas de Remplacement

**Décision :** `SkillEvalEngine` dans `skill_eval.py` est **étendu** (méthode `evaluate_with_golden_dataset`). `skill_auto_tuner.py` et `skill_impact_tracker.py` sont **préservés tels quels**. Un nouvel orchestrateur `skill_flywheel.py` les couple sans les réécrire.

### C. Seuil Officiel à 80 pts

**Décision :** Le seuil de passage reste à **80 pts** (PASS_THRESHOLD actuel du code). Le seuil dashboard alerting (vert ≥ 80, orange 65–79, rouge < 65) est aligné. La montée à 85 pts est différée après un premier run baseline sur les 39 skills.

### D. Format Golden Dataset Uniforme

**Décision :** Format JSON **uniforme** pour les 39 skills avec champ optionnel `category` (`TRIGGER_ONLY`, `EXECUTION_FLOW`, `META_ORCHESTRATION`). **Minimum 3 cas par skill** : 1 nominal + 1 limite + 1 adversarial = 117 cas minimum.

### E. HEAVY_META_SKILLS — Couverture Statique Seule

**Décision :** Les 8 `HEAVY_META_SKILLS` déjà identifiées dans le code (`zero-blindspot-spec`, `handoff`, `router`, `sentinel`, `rubber-duck`, `calibrate`, `obsidian-canvas`, `visual-excalidraw`, `visual-mermaid`) bénéficient de couverture **statique uniquement**. Leurs `cases.json` ont `"behavioral": false`.

**Motivation :** Ces skills sont des orchestrateurs lourds dont l'évaluation comportementale imposerait des chaînes d'invocation récursives coûteuses et non maîtrisables en Système 1.

### F. HITL Obligatoire pour les Mutations de SKILL.md

**Décision :** Le `SkillFlywheel` **propose** des mutations (fichier `pending_patches/<skill>_patch.md`), jamais les applique automatiquement. L'application requiert la commande humaine explicite `mloop skill-eval --apply-patch <skill_name>` avec confirmation interactive.

**Motivation :** Cohérence avec la gouvernance mLoop (ADR-0375) — aucune modification de document de gouvernance sans feu vert humain tracé.

### G. Max 3 Itérations par Cycle + Rollback Automatique

**Décision :** 3 itérations d'auto-tuning maximum par skill par cycle. Rollback automatique si Δscore ≤ 0. Au-delà de 3 itérations sans amélioration → `NEEDS_HUMAN_REVIEW`.

**Motivation :** Prévention de l'oscillation documentée dans ADR-0348 (reproposition cyclique de mutations invalidées).

### H. Dashboard HTML Statique Auto-Contenu

**Décision :** Vue `/skills-health` en **HTML statique auto-contenu**, zéro CDN externe, générée depuis `skills_eval_summary.json`. Lecture seule v1.

**Motivation :** Cohérence avec l'approche MCP Apps (MLOOP-212-FE) et la politique de confinement sandbox (ADR-0379). Pas de bouton de relancement dans l'interface — le CLI reste la surface de commande souveraine.

### I. Check 23 Vibe-Check — Additionnel Non Bloquant

**Décision :** Ajout du **Check 23** "Intégrité & Santé des Compétences Agentiques" comblant le trou existant entre Check 22 et Check 24. Verdict **WARNING uniquement** (jamais FAIL bloquant) — conforme ADR-0384.

**Décision :** CLI `skill-eval` en **CI uniquement**, pas de hook pre-push Git automatique (latence inacceptable). Mode `--fast` (Système 1 pur, < 10s) disponible pour intégrations rapides.

---

## 3. Conséquences & Engagements

| Aspect | Impact |
| :--- | :--- |
| **Modularité** | `skill_flywheel.py` nouveau (≤ 300L). Si `skill_eval.py` dépasse 300L après extension → scission obligatoire. |
| **Données** | Nouveau dossier `memory/evals/skills/<skill_name>/cases.json` pour les 39 skills. |
| **Vibe-Check** | Check 23 ajouté dans l'orchestrateur `__init__.py` (trou comblé). |
| **CLI** | Nouvelle commande `skill-eval` avec 5 options. `CLI_PIPELINE_GUIDE.md` mis à jour (parité ADR-0370). |
| **Tests** | Suite `tests/test_skill_eval_harness.py` à créer (couverture des 5 récits). |
| **Dashboard** | `src/dashboard/skills_health.html` généré. Handler CLI étendu. |

---

## 4. Alternatives Rejetées

| Alternative | Motif du Rejet |
| :--- | :--- |
| Évaluation Système 2 LLM-as-a-judge v1 | Budget tokens inconnu, infrastructure LLM-judge non cadrée. Différé EPIC-24-v2. |
| Formats Golden Datasets spécialisés par catégorie | Maintenance de 3 formats parallèles non justifiée pour 39 skills. |
| Seuil 85 pts | Causerait des FAIL immédiats sans baseline historique. Montée progressive. |
| Auto-application de patches SKILL.md | Violation ADR-0375 (traçabilité radicale + feu vert humain). |
| Hook pre-push Git pour skill-eval | Latence ≥ 10s inacceptable en flux de développement quotidien. |
