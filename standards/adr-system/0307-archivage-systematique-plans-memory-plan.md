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

## 3. Conséquences Initiales

- **Traçabilité totale** : Conservation de l'historique des cadrages d'implémentation par récit.
- **Zéro-Pollution** : Propreté stricte de la racine des répertoires projets et centralisation sous `memory/plan/`.
- **Rétro-compatibilité Plannotator & Antigravity** : Les outils d'annotation visuelle (Plannotator) et les artefacts IDE continuent d'intercepter les plans tout en garantissant leur archivage sécurisé.

---

## 4. Amendement 2026-09-10 : Cycle de Vie Réel & Découplage de la Preuve

Suite au retour d'expérience et à l'audit du système :
1. **Consommation par les agents (Vérité terrain)** :
   - Les agents mLoop n'ont **pas** vocation à relire perpétuellement les anciens plans de stories déjà livrées.
   - La source de vérité immuable d'un travail terminé est l'**EvidencePack** ([`memory/evidence/<STORY>_evidence.json`](file:///c:/Memory%20Loop/CLAUDE.md), ADR-0341), les tests d'acceptation et les commits Git.
2. **Pertinence recentrée sur la Session Active & l'Anti-Amnésie** :
   - Le plan d'implémentation est hautement pertinent **pendant** la conception (alignement HITL via Plannotator/Antigravity) et **pendant** l'exécution de la story pour permettre la reprise de session déterministe (`python src/swarm.py resume`).
   - Une fois la story livrée (`DONE`), le plan devient une trace historique passive.
3. **Hygiène Stricte & Zéro Stub Vide** :
   - Tout fichier de plan à 0 octet est interdit.
   - Les plans de stories terminées ne doivent pas gonfler inutilement les index contextuels ou le graphe de connaissances.
