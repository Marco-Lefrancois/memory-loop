---
id: MLOOP-108-BE
jira_key: '-'
epic_key: EPIC-10-SOVEREIGN-EXCELLENCE
type: Bug
title: Fiabilisation du Harnais E2E Boot-Sequence et Alignement de la Clé LiteLLM Metro
layer: backend
status: SHIPPED
grill_me: PENDING
invest_score: 0/6
dependencies: []
complexity: XS
assignee: IA
---

# Fiabilisation du Harnais E2E Boot-Sequence et Alignement de la Clé LiteLLM Metro

> **Référence croisée** : Dette détectée pendant la recette QA (Gate 4) de `MLOOP-101-BE` (2026-09-20).

## Contexte et problème
1. Trois tests e2e échouent de façon pré-existante (artefact exit-code du harnais `subprocess.run` sans timeout face au canary ConfinementShield ADR-0379 qui journalise `[CONFINEMENT 403]` sur stderr, alors que le shell direct retourne EXIT 0) : `tests/test_e2e_agent_workflow.py::test_boot_sequence_step2_vibe_check`, `::test_full_agent_boot_sequence_end_to_end`, `tests/test_e2e_user_prompt_simulation.py::test_vibe_check_guardrail_simulation`.
2. `vibe-check --project Metro_COMMERCE` échoue au contrôle 19/19 « Alignement Projet ↔ Clé LiteLLM » (18/19) : clé active `Perso (Générale)` au lieu de la clé attendue `Metro` (dette de configuration LiteLLM).


---

## Périmètre
- Fiabiliser `run_swarm_cmd` (timeout explicite ADR-0369, gestion du canal stderr du canary, assertion exit-code alignée sur le comportement réel).
- Réaligner la clé LiteLLM du projet Metro_COMMERCE (via `python tools/budget/switch_key.py` — interdiction de modification manuelle d'une clé uniq
---

## Hors périmètreimètre
- Tout module de `src/utils/` (livré par `MLOOP-101-BE`), les pipelines, le moteur de co
---

## Ouvertures (OQ)ertures (OQ)
- OQ-108-1 : le canary CONFINEMENT 403 doit-il passer sur stdout (silencieux en stderr) pour compatibilité harnais ?
- OQ-108-2 : quelle est la politique de rotation attendue des clés (fréquence, seuils de budg
---

## Prochaines étapes Prochaines étapes
- Session Grill-Me dédiée (`python src/swarm.py grill-me --story MLOOP-108-BE`) avant toute promotion Palier 2.
