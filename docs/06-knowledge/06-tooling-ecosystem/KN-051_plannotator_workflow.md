---
id: KN-051
title: Plannotator — Annotation et Validation Visuelle de Plans
domain: tooling-ecosystem
status: VALIDATED
confidence_score: 0.98
tags: [plannotator, hitl, plan-validation, test-plan, phase-files, ui]
related_adrs: [ADR-0040, ADR-0100, ADR-0201]
---

# 📋 Plannotator — Annotation et Validation Visuelle de Plans

> [!ABSTRACT]
> Outil visuel interactif (HITL - Human In The Loop) dédié à la revue, l'annotation et l'approbation formelle des plans d'implémentation et de test générés par les agents avant toute modification de code.

## 1. Principes Fondamentaux & Mécanique
- **Localisation de l'Exécutable** : Binaire installé de manière standardisée au niveau utilisateur sous `%LOCALAPPDATA%\plannotator\plannotator.exe`.
- **Topologie de Stockage Canonique** :
  - Les fichiers de plans appartiennent exclusivement aux projets respectifs sous `Projects/<project>/memory/plan/`.
  - Aucun fichier d'état ou plan orphelin ne doit résider à la racine globale de Memory Loop.
- **Workflow Phase -> Test Plan** :
  - Défini rigoureusement dans `standards/protocols/PHASE_FILES_AND_TEST_PLAN.md`.
  - Étape 1 : Génération du plan de phase préliminaire par l'agent Plan.
  - Étape 2 : Lancement de l'UI Plannotator pour inspection visuelle et annotations humaines.
  - Étape 3 : Export et archivage du plan validé servant de contrat d'exécution pour l'agent Build.

## 2. Découpage Épistémique
- **what_it_actually_proves** : Élimine les dérives d'implémentation prématurées en forçant un point d'arrêt humain vérifiable sur la spécification.
- **what_it_does_not_prove** : Ne garantit pas l'absence de bugs lors de l'exécution du code ; la validation du code reste dévolue à la suite de tests unitaires et aux linters.
