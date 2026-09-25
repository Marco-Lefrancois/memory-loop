---
id: MLOOP-242-BE
jira_key: ''
epic_key: EPIC-24-SKILLS-EVAL-HARNESS
type: Feature
title: "Boucle d'Amélioration Fermée (Eval Flywheel) : Couplage Auto-Tuner, Harvester & Anti-Amnésie"
tags:
- skills
- flywheel
- auto-tuner
- skill-impact
- backend
origin: SPEC_SLICING
source_ref: EPIC-24-§4.3
macro_size: M
status: SHIPPED
grill_me: DONE
invest_score: 6/6
validated_by: Marco (PO)
validated_at: '2026-09-24'
layer: backend
blocked_by:
- MLOOP-240-BE
created_at: '2026-09-24'
updated_at: '2026-09-24'
ttl_cycles: 4
---

# 📖 MLOOP-242-BE : Boucle d'Amélioration Fermée (Eval Flywheel) : Couplage Auto-Tuner, Harvester & Anti-Amnésie

## Description
**En tant que** Concepteur de Système Multi-Agents,
**je veux** un module `src/pipelines/skill_flywheel.py` qui orchestre les modules existants `SkillAutoTuner` et `SkillImpactTracker` en les branchant sur les résultats du `SkillEvalEngine` (MLOOP-240-BE),
**afin de** créer une boucle d'amélioration continue où chaque régression est capturée, les contraintes négatives injectées, et les propositions de modification de `SKILL.md` soumises à l'approbation humaine (HITL) avant application.

---

## Contexte & Périmètre

### Contexte Métier
L'ADR-0348 identifie deux pathologies récurrentes : l'**Amnésie d'Optimisation** (reproposition de mutations déjà invalidées) et la **Pollution Contextuelle** (injection de logs bruts dans le prompt). Ce récit crée le `SkillFlywheel` — un orchestrateur léger qui relie les briques existantes sans les réécrire.

**Décisions Grill (2026-09-24) :**
- **Évolution des modules existants** — pas de remplacement. `skill_auto_tuner.py` et `skill_impact_tracker.py` sont préservés tels quels.
- **HITL obligatoire** : Le Flywheel *propose* des mutations de `SKILL.md`. L'humain *valide* via `mloop skill-eval --apply-patch <skill_name>` avant toute écriture.
- **Max 3 itérations** d'auto-tuning par skill par cycle. Rollback automatique si Δscore ≤ 0 dès la 1ère itération.
- Module dédié `src/pipelines/skill_flywheel.py` ≤ 300 lignes (ADR-0202).

### In-Scope
- Création de `src/pipelines/skill_flywheel.py` orchestrant le cycle : EvalEngine → ImpactTracker → AutoTuner → Proposition HITL.
- Lecture des résultats de `SkillEvalEngine` (JSON) et identification des skills en régression (verdict `FAIL` ou `WARNING`).
- Injection des contraintes négatives (anti-patterns passés) dans le prompt du `SkillAutoTuner` avant génération de proposition.
- Écriture dans `memory/skill_impact.jsonl` (append) avec traçabilité radicale : diff, motif, delta de score.
- Génération d'un fichier `memory/evals/pending_patches/<skill_name>_patch.md` (proposition HITL, jamais appliquée automatiquement).
- Rollback auto : si Δscore ≤ 0 à la 1ère itération → patch annulé, contrainte négative enregistrée.
- Limite 3 itérations par skill par cycle : au-delà, skill marquée `NEEDS_HUMAN_REVIEW` dans le rapport.

### Out-of-Scope
- Réécriture ou modification de `skill_auto_tuner.py` et `skill_impact_tracker.py`.
- Application automatique de patches sans validation humaine.
- Modification du code Python des skills (limité aux manifestes `SKILL.md`).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Orchestration du Cycle Flywheel
* **Entrée Métier** : Rapport JSON produit par `SkillEvalEngine.evaluate_all()`.
* **Règles d'admissibilité** : Seules les skills avec verdict `FAIL` ou `WARNING` entrent dans le cycle Flywheel. Les skills `PASS` sont ignorées.
* **Traitement** : Pour chaque skill dégradée — (1) charger contraintes négatives depuis `skill_impact.jsonl`, (2) appeler `SkillAutoTuner.propose_patch(skill_name, negative_constraints)`, (3) évaluer le patch avec `SkillEvalEngine`, (4) si Δscore > 0 → écrire `pending_patches/<skill_name>_patch.md`, sinon rollback + ajouter contrainte négative.
* **Résultat** : Journal `memory/skill_impact.jsonl` mis à jour + dossier `pending_patches/` peuplé des propositions validables.
* **Cas de Rejet** : 3 itérations sans amélioration → `NEEDS_HUMAN_REVIEW`, cycle arrêté pour cette skill.

#### 2. Traçabilité dans skill_impact.jsonl
```json
{
  "timestamp": "2026-09-24T20:00:00Z",
  "skill_name": "grill",
  "action": "patch_proposed",
  "score_before": 72.5,
  "score_after": 81.0,
  "delta_score": 8.5,
  "iteration": 1,
  "status": "PENDING_HITL",
  "patch_file": "memory/evals/pending_patches/grill_patch.md"
}
```

#### 3. Contrôle de la limite d'itérations
* **Règle** : `max_iterations = 3` par skill par cycle. Configurable via paramètre CLI `--max-iterations`.
* **Dépassement** : Skill marquée `NEEDS_HUMAN_REVIEW` dans le rapport final + entrée dans `skill_impact.jsonl` avec `"action": "max_iterations_reached"`.

### Contrats d'Échange API
- Module Python pur. Invoqué par `mloop skill-eval --flywheel`.

---

## Règles d'affaires

- **HITL inviolable** : Aucune écriture sur `SKILL.md` en production sans commande humaine explicite `--apply-patch`. Violation = faute grave (ADR-0375).
- **Anti-Amnésie** : Les contraintes négatives dans `skill_impact.jsonl` sont injectées dans chaque appel au `SkillAutoTuner`. Un pattern rejeté une fois ne peut jamais être reproposé.
- **Rollback automatique** : Si Δscore ≤ 0 à n'importe quelle itération → annulation immédiate + enregistrement de la contrainte négative.
- **Plafond AST** : `skill_flywheel.py` ≤ 300 lignes (ADR-0202). Orchestrateur léger uniquement — toute logique complexe dans les modules existants.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Modules existants** : [`src/pipelines/skill_auto_tuner.py`](../../../src/pipelines/skill_auto_tuner.py) · [`src/core/skill_impact_tracker.py`](../../../src/core/skill_impact_tracker.py)
- 🏛️ **ADR** : [ADR-0348](../../../standards/adr-system/0348-wikiskill-tri-layer-evolution.md) · [ADR-0375](../../../standards/adr-system/0375-standard-preuve-epistemique-et-tracabilite-radicale.md) · [ADR-0202](../../../standards/adr-system/0202-modularite-interne-agents.md)
- 📋 **Epic** : [`epics/epic_skills_eval_harness.md`](../epics/epic_skills_eval_harness.md)
- 📄 **Dépendance amont** : MLOOP-240-BE (résultats d'évaluation)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Eval Flywheel — Boucle d'Amélioration Fermée avec HITL

  Scénario: Pilier 1 - Nominal (Happy path) : Cycle nominal avec amélioration et proposition HITL
    Étant donné la skill "wait-what" avec un score de 72.5 (verdict WARNING)
    Et des contraintes négatives existantes dans skill_impact.jsonl
    Quand j'exécute le Flywheel via "mloop skill-eval --flywheel"
    Alors une proposition de patch est générée sous memory/evals/pending_patches/wait-what_patch.md
    Et skill_impact.jsonl contient une entrée avec "status": "PENDING_HITL" et delta_score > 0
    Et aucune modification de SKILL.md n'a eu lieu sans commande --apply-patch

  Scénario: Pilier 2 - Exceptions (Cas d'erreur) : Rollback automatique lors d'une régression
    Étant donné la skill "triage" avec un score de 68.0
    Quand le Flywheel propose un patch qui abaisse le score à 65.0 (Δscore = -3.0)
    Alors le patch est annulé automatiquement
    Et une contrainte négative est ajoutée dans skill_impact.jsonl avec "action": "rollback"
    Et aucun fichier pending_patch n'est créé

  Scénario: Pilier 3 - Résilience (Mode dégradé) : Plafond d'itérations et arrêt sécurisé
    Étant donné la skill "svg-ocr" avec un score de 61.0
    Et 3 itérations de tuning sans amélioration (tous Δscore ≤ 0)
    Quand la 3ème itération échoue
    Alors la skill est marquée "NEEDS_HUMAN_REVIEW" dans le rapport
    Et l'entrée skill_impact.jsonl contient "action": "max_iterations_reached"
    Et le Flywheel s'arrête de façon sécurisée pour cette skill

  Scénario: Pilier 4 - UX (Accessibilité & Transparence) : Contraintes négatives explicites
    Étant donné une contrainte négative "ajouter trigger 'optimise'" dans skill_impact.jsonl
    Quand le Flywheel génère un nouveau patch pour cette skill
    Alors le prompt du SkillAutoTuner contient la contrainte négative
    Et aucune proposition contenant "optimise" n'est générée
```
