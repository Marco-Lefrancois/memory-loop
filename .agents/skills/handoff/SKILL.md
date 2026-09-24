---
name: handoff
description: "Protocole de clôture de session et compression sémantique de contexte. Use when concluding a work session, approaching token limits, or passing clean state to a subsequent agent session."
disable-model-invocation: true
---

# 🧠 handoff

> **Status:** Active | **Standard:** Zero-Bloat v1.0

## 🎯 Purpose
Ce skill remplace l'ancienne compétence "synapse". Il est responsable de lutter contre la pathologie de la "Pourriture du contexte" (Context Rot / Dumb Zone) en permettant à un agent de clore proprement sa session de travail.
Il agit comme un mécanisme de compression sémantique pour passer le relais (handoff) à une nouvelle session de l'agent sans surcharger sa fenêtre de contexte.

## 🧱 Core Principles
- **Smart Zone vs Dumb Zone** : Un agent est beaucoup plus performant au début de sa session (Smart Zone). Ce skill permet de conserver la continuité du travail tout en redémarrant avec une conscience fraîche.
- **Zero-Bloat** : Le document généré ne doit contenir que du signal, pas de bruit. Ne dupliquez pas le code existant, pointez vers les artefacts.

## 🛠️ Workflow en 4 Étapes
1. **Détection** : Invoquez cette compétence lorsque la session de travail s'éternise, lorsque la tâche actuelle est terminée, ou que vous sentez que votre contexte est surchargé. Ou si l'utilisateur demande "close session".
2. **Génération du Handoff** : Créez ou remplacez le fichier `memory/sessions/handoff.md`. (Créez le dossier `sessions` si nécessaire).
3. **Contenu Requis** :
   - **Objectif de la prochaine session** : Ce qui reste à accomplir.
   - **Contexte pertinent** : Les décisions récentes, l'état d'avancement.
   - **Skills Suggérés** : Une liste des skills que l'agent de la prochaine session devra potentiellement utiliser.
   - **Pointeurs** : Liens Markdown vers les fichiers pertinents et les artefacts créés (ex: `standards/adr-system/`, `task.md`, etc.).
4. **Graphify Sync** : Recommandez toujours d'exécuter `python src/swarm.py sync --project <nom_du_projet>` pour s'assurer que l'index de connaissances intègre le nouveau savoir avant de clore.

## 🤝 Universal Dev Handoff vers l'Équipe de Dev (ADR-0319)
Lorsque l'analyse d'une story est achevée (`READY_FOR_DEV`) et prête à être transmise au développement :
- **Transmettre le Story Contract pur** : Fournir le chemin vers la story `backlog/stories/<ID>.md` et les documents de référence `docs/00-ingested/...`.
- **Zéro Code Prescrit** : Ne jamais envoyer de snippets de code d'implémentation ; laisser l'entière autonomie à l'équipe de dev pour concevoir son plan technique avec sa connaissance du codebase.

## 🛡️ Résilience & Dégradation Gracieuse
Si le répertoire `memory/sessions/` ne peut être écrit, écrire en fallback sous `memory/HANDOFF.md` et consigner l'anomalie dans `memory/logs/`.
