# Archive des Compétences Dépréciées (`memory/archive-skills/`)

Ce répertoire contient les compétences historiques retirées du catalogue actif [`.agents/skills/`](../../.agents/skills/) dans le cadre de la rationalisation constitutionnelle **[ADR-0365](../../standards/adr-system/0365-harmonisation-symbiotique-skills-et-standard-agent-skills.md)**.

## Contexte & Justification (ADR-0362 & ADR-0365)
L'audit de santé des compétences (`python src/swarm.py doctor --skills`) a mis en évidence un risque critique de **Context Rot** avec 35 compétences totalisant ~39 464 jetons au démarrage du modèle.
Afin d'abaisser l'empreinte sous le seuil constitutionnel des 15 000 jetons et d'éviter les collisions sémantiques entre compétences doublons, ces 14 compétences ont été archivées ici. Leurs contenus demeurent intégralement consultables pour l'historique et la recherche.

## Table de Correspondance & Remplacements

| Compétence Archivée | Raison de l'Archivage | Remplacement Actif / Équivalent |
| :--- | :--- | :--- |
| `tdd` | Remplacé par le standard supérieur d'ingénierie | `.agents/skills/test-driven-development/` (Addy) |
| `thinking-cynefin` | Découpage théorique non sollicité en production | Modèle cognitif natif d'alignement & ADR-0103 |
| `thinking-kepner-tregoe` | Sur-spécification théorique de décision | Matrice de décision dans `.agents/skills/plan/` |
| `thinking-reversibility` | Redondant avec la classification ADR | Filtrage Type 1 / Type 2 dans `adr-decision-checklist.md` |
| `thinking-theory-of-constraints` | Sur-spécification de diagnostic | `.agents/skills/performance-optimization/` |
| `thinking-triz` | Trop abstrait pour la planification agile | `.agents/skills/code-simplification/` |
| `thinking-via-negativa` | Redondant avec la posture Sentinel | `.agents/skills/sentinel/` & `doubt-driven-development` |
| `teach` | Obèse (2 224 jetons) et hors scope handoff | Standards normatifs dans `standards/` et NotebookLM |
| `office` | Obsolète et lourd | `.agents/skills/markitdown/` (ingestion universelle) |
| `analyze` | Redondant avec le moteur hybride | `fact_search` FTS5 SQLite & `.agents/skills/blindspot-scan/` |
| `research` | Vague et générateur d'hallucinations | `.agents/skills/source-driven-development/` |
| `research-and-develop` | Doublon conceptuel de cadrage | `.agents/skills/spec-driven-development/` |
| `validate` | Rôle confus entre linter et audit | `.agents/skills/sentinel/` & `doubt-driven-development` |
| `sop` | Doublon avec les protocoles normatifs | `standards/protocols/` |
