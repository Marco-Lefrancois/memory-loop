# ADR-0307 : Archivage Systématique et Sécurisé des Plans dans `memory/plan/`

- **Statut** : DECIDED
- **Date** : 2026-08-13
- **Portée** : Système Global Memory Loop (mLoop), Tous Projets et Agents (Plannotator, OpenCode, Antigravity)
- **Décideurs** : Équipe Architecture mLoop, Utilisateur & Agent Orchestrateur

---

## 1. Contexte & Problème

Lors des sessions de cadrage (*Planning Mode*) et des interactions avec le plugin Plannotator (`@plannotator/opencode`), les agents rédigent des plans d'implémentation (`implementation_plan.md`). 

Auparavant, la création de ce fichier à la racine du projet entraînait :
1. La pollution de la racine du projet avec des artefacts éphémères.
2. L'écrasement incontrôlé des plans des récits précédents lors des nouvelles planifications.

---

## 2. Décision Retenue

**Archivage Systématique Obligatoire dans `Projects/<project_id>/memory/plan/`** :

1. **Emplacement Canonique Systémique** :
   Chaque plan rédigé ou généré par l'IA (via Plannotator ou Antigravity selon le gabarit [`standards/blueprints/plan_template.md`](file:///c:/Memory%20Loop/standards/blueprints/plan_template.md)) doit être obligatoirement sauvegardé et conservé sous :
   `Projects/<project_id>/memory/plan/implementation_plan_<STORY_ID>.md` (ex: `memory/plan/implementation_plan_US-14-FOOD.md`).

2. **Gouvernance des Brouillons Éphémères & Plannotator** :
   Si des fichiers temporaires `implementation_plan.md` ou `plannotator/*.md` sont utilisés pendant la session active, une copie d'archivage DOIT être immédiatement écrite sous `memory/plan/` dès la validation finale du plan. La commande `python src/swarm.py sync` assure l'indexation de ces plans.

3. **Inclusion dans la Constitution Système (`AGENTS.md`)** :
   Cette règle est inscrite dans `AGENTS.md` (section *Boundaries / Always do*) et appliquée par tous les agents et sous-processus d'automatisation mLoop.

---

## 3. Conséquences

- **Traçabilité totale** : Conservation permanente de l'historique de tous les cadrages d'implémentation par récit.
- **Zéro-Pollution** : Propreté stricte de la racine des répertoires projets et centralisation sous `memory/plan/`.
- **Rétro-compatibilité Plannotator & Antigravity** : Les outils d'annotation visuelle (Plannotator) et les artefacts IDE continuent d'intercepter les plans tout en garantissant leur archivage sécurisé.
