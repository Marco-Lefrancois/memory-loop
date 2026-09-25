---
id: MLOOP-244-FULL
jira_key: ''
epic_key: EPIC-24-SKILLS-EVAL-HARNESS
type: Feature
title: "Commande CLI mloop skill-eval --all & Contrôle de Vol Pré-Vol Vibe-Check (Check 23)"
tags:
- skills
- cli
- vibe-check
- fullstack
- check-23
origin: SPEC_SLICING
source_ref: EPIC-24-§4.5
macro_size: L
status: SHIPPED
grill_me: DONE
invest_score: 6/6
validated_by: Marco (PO)
validated_at: '2026-09-24'
layer: fullstack
blocked_by:
- MLOOP-242-BE
- MLOOP-243-FE
created_at: '2026-09-24'
updated_at: '2026-09-24'
ttl_cycles: 4
---

# 📖 MLOOP-244-FULL : Commande CLI mloop skill-eval --all & Contrôle de Vol Pré-Vol Vibe-Check (Check 23)

## Description
**En tant qu'** Ingénieur DevOps / Développeur mLoop,
**je veux** une commande CLI `python src/swarm.py skill-eval --all` (et `--skill <nom>`, `--flywheel`, `--fast`) ainsi qu'un nouveau **Check 23** dans le guardrail Vibe-Check pré-vol contrôlant la santé des skills,
**afin de** détecter toute régression de qualité d'une compétence avant tout déploiement, en CI ou sur demande manuelle, sans bloquer le flux de développement quotidien par un hook pre-push automatique.

---

## Contexte & Périmètre

### Contexte Métier
Le guardrail Vibe-Check compte actuellement 24 checks déclarés (Checks 1–24), mais les Checks 18 et 23 sont **absents** de l'orchestrateur `__init__.py`. Ce récit comble ce trou en ajoutant le Check 23 "Intégrité & Santé des Compétences Agentiques", qui invoque le `SkillEvalEngine` en mode rapide (`--fast`) lors du Vibe-Check.

**Décisions Grill (2026-09-24) :**
- **CI uniquement** — pas de hook Git pre-push automatique (trop lent pour 39 skills). Lancement manuel ou en CI pipeline.
- **Mode `--fast`** : assertions statiques uniquement (Système 1, sans Flywheel), rapide < 10s pour 39 skills.
- **Check 23 additionnel** : comble le trou existant entre Check 22 (extraction) et Check 24 (storage hygiene). Pas de remplacement.
- **Seuil Check 23** : WARNING si 1+ skill FAIL ou moyenne < 70, PASS sinon. Jamais bloquant (WARNING non bloquant selon ADR-0384).

### In-Scope
- Handler CLI `src/commands/handlers/skill_eval.py` (nouveau fichier ≤ 300L).
- Enregistrement dans `src/commands/_registry/` avec la commande `skill-eval`.
- Options supportées :
  - `--all` : évalue les 39 skills
  - `--skill <nom>` : évalue une skill spécifique
  - `--flywheel` : active le Flywheel (nécessite MLOOP-242-BE)
  - `--fast` : mode rapide Système 1 uniquement (sans Flywheel, sans golden dataset comportemental)
  - `--apply-patch <skill_name>` : applique le patch HITL en attente dans `pending_patches/`
- Check 23 dans `src/pipelines/vibe_check/_vc_agents.py` (ou nouveau `_vc_skills.py` si > 164L après ajout) : invocation `SkillEvalEngine` en mode `--fast`, résultat WARNING si dégradation détectée.
- Rapport exécutif `memory/evals/skills_eval_summary.md` + `skills_eval_summary.json`.
- Mise à jour de `standards/protocols/CLI_PIPELINE_GUIDE.md` avec parité stricte (ADR-0370).
- Code de sortie : exit code 0 si moyenne ≥ 80 et zéro FAIL critique, exit code 1 sinon.

### Out-of-Scope
- Hook Git pre-push automatique.
- Remplacement du `SkillDoctor` existant (fonctionnement en synergie).
- Évaluation des outils tiers non intégrés au dépôt.
- Remplacement des checks 1–22 ou 24 existants.

---

## Critères d'acceptation

### Spécifications de l'Interface & UX
- **Sortie CLI ZeroFluff** : tableau récapitulatif avec verdict PASS/WARN/FAIL par skill, score moyen, résumé en dernière ligne.
- **Mode `--fast`** : affiche uniquement les scores statiques, sortie < 10s pour 39 skills.
- **Exit code strict** : 0 = succès (moyenne ≥ 80, zéro FAIL), 1 = dégradation détectée.
- **`--apply-patch`** : confirmation interactive avant écriture (`Confirmer l'application du patch grill ? [y/N]`).

### Opérations Métier & Logique Backend

#### 1. Commande CLI skill-eval
* **Entrée Métier** : Options CLI (`--all`, `--skill`, `--fast`, `--flywheel`, `--apply-patch`).
* **Règles d'admissibilité** : `--apply-patch` nécessite l'existence du fichier `pending_patches/<skill>_patch.md` et confirmation HITL interactive.
* **Traitement** : Délègue à `SkillEvalEngine.evaluate_all()` (ou `evaluate_one()`) puis optionnellement `SkillFlywheel.run()`.
* **Résultat** : Rapport JSON + Markdown + sortie CLI colorée. Exit code 0 ou 1.
* **Cas de Rejet** : `--apply-patch` sans fichier pending → erreur explicite, aucune modification.

#### 2. Check 23 Vibe-Check — Intégrité & Santé des Compétences Agentiques
* **Nom** : `Check 23 : Intégrité & Santé des Compétences Agentiques (EPIC-24 / ADR-0389)`
* **Invocation** : `SkillEvalEngine(workspace_root).evaluate_all()` en mode `--fast`.
* **Seuil WARNING** : 1+ skill FAIL OU moyenne globale < 70 pts.
* **Seuil PASS** : Toutes skills ≥ 65 pts ET moyenne ≥ 70 pts.
* **Non bloquant** : WARNING uniquement (jamais FAIL bloquant) — conforme ADR-0384.
* **Performance** : Check 23 doit s'exécuter en < 15s pour ne pas ralentir le Vibe-Check global.

### Contrats d'Échange API
- `python src/swarm.py skill-eval [options]` — CLI uniquement, aucun endpoint réseau.

---

## Règles d'affaires

- **CI uniquement** : La commande n'est pas enregistrée comme hook pre-push Git. Elle est invoquée explicitement ou en CI pipeline.
- **Check 23 non bloquant** : Conforme au verdict tri-état ADR-0384 — WARNING signalé, jamais FAIL bloquant. Un parc de skills légèrement dégradé ne doit pas bloquer un déploiement critique.
- **Parité CLI obligatoire** : `CLI_PIPELINE_GUIDE.md` mis à jour avec `skill-eval` avant merge (ADR-0370 / Check 15 Vibe-Check).
- **Exit code strict** : Code 1 si dégradation = bloquant en CI. L'équipe CI peut choisir de le passer en WARNING selon leur politique.
- **Plafond AST** : `skill_eval.py` (handler) ≤ 300L. Si Check 23 dépasse la capacité de `_vc_agents.py` (164L actuellement), créer `_vc_skills.py` dédié.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Orchestrateur Vibe-Check** : [`src/pipelines/vibe_check/__init__.py`](../../../src/pipelines/vibe_check/__init__.py) (Checks 1–24, trous aux numéros 18 et 23)
- 📂 **Module agents** : [`src/pipelines/vibe_check/_vc_agents.py`](../../../src/pipelines/vibe_check/_vc_agents.py) (164L — capacité disponible pour Check 23)
- 🏛️ **ADR** : [ADR-0384](../../../standards/adr-system/) · [ADR-0370](../../../standards/adr-system/) · [ADR-0202](../../../standards/adr-system/0202-modularite-interne-agents.md) · ADR-0389 (à créer)
- 📋 **Epic** : [`epics/epic_skills_eval_harness.md`](../epics/epic_skills_eval_harness.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: CLI skill-eval & Check 23 Vibe-Check

  Scénario: Pilier 1 - Nominal (Happy path) : Exécution nominale --all avec toutes skills PASS
    Étant donné 39 skills avec scores >= 80 pts
    Quand j'exécute "python src/swarm.py skill-eval --all"
    Alors la sortie CLI affiche un tableau récapitulatif avec 39 PASS
    Et le fichier memory/evals/skills_eval_summary.json est mis à jour
    Et l'exit code est 0

  Scénario: Pilier 2 - Exceptions (Cas d'erreur) : Compétence inconnue ou patch inexistant
    Étant donné une requête ciblant une compétence invalide ou un patch absent
    Quand j'exécute "python src/swarm.py skill-eval --skill inconnue" ou "--apply-patch absent"
    Alors une erreur explicite est affichée sur la console
    Et l'exécution s'interrompt avec un exit code 1

  Scénario: Pilier 3 - Résilience (Mode dégradé & Timeout) : Check 23 Vibe-Check WARNING non bloquant
    Étant donné 1 skill avec verdict FAIL lors de l'audit
    Quand j'exécute "python src/swarm.py vibe-check --project mLoop"
    Alors Check 23 retourne "WARNING" avec message de santé dégradé
    Et le verdict global du Vibe-Check reste PASS (WARNING non bloquant ADR-0384)
    Et le mode --fast s'exécute en moins de 10 secondes

  Scénario: Pilier 4 - UX (Accessibilité & État vide) : Sortie ZeroFluff et confirmation HITL
    Étant donné un opérateur exécutant --apply-patch
    Quand la commande est lancée en mode interactif
    Alors une invite de confirmation claire [y/N] est présentée
    Et un état vide affiche un message guidé sans planter
```
