---
trigger: "Toute session d'amorçage, initialisation de projet (init), ingestion (ingest) ou travail en Phase 1 (STAGE_1_INGEST)"
authority: "ADR-0378 / INGESTION_AND_EXPLORATION_PROTOCOL.md"
---

# Règle Inviolable : Guardrails de Phase 1 (INGEST & EXPLORE)

En Phase 1 (`STAGE_1_INGEST`), l'ensemble des agents de l'écosystème Memory Loop (mLoop) doivent respecter scrupuleusement les 5 règles d'or suivantes :

## 1. Interdiction Absolue de Créer des Stories (Check 13 / Anti-Ghost-Bias)
- Il est **formellement interdit** de créer, déplacer ou modifier le moindre fichier sous `backlog/stories/` avant l'approbation formelle de la **Porte 1 (*Gate 1*)**.
- Il est interdit de positionner des récits en statut engagé (`IN_ANALYZE`, `READY_FOR_DEV`) dans `backlog/sprint_backlog.md`.
- En cas de découverte de stories prématurées, exécuter immédiatement :
  ```bash
  python src/swarm.py lifecycle-clean --confirm
  ```

## 2. Respect de la Pause Humaine & Zéro Sous-Readme dans `reference/`
- Le répertoire `reference/` est une zone de staging local non versionnée réservée au dépôt manuel par l'humain.
- Conformément à l'ADR-0100 (`forbidden_subreadmes: true`), **aucun fichier sous-readme interne** ne doit être créé dans `reference/`.
- L'agent ne doit jamais inventer ou simuler de la matière : si `reference/` est vide, avertir l'humain et attendre le dépôt.

## 3. Découplage Strict des Actifs Visuels (ADR-0332)
- Toutes les maquettes vectorielles (`.svg`) et illustrations doivent être placées sous `docs/05-assets/maquettes/` ou `docs/05-assets/diagrams/`.
- Les maquettes SVG doivent être nettoyées de toute métadonnée d'éditeur via :
  ```bash
  python src/swarm.py svg-optimize --input docs/05-assets
  ```

## 4. Grounding Épistémique & Manifeste de Source (ADR-0335)
- Tout document ingéré doit être référencé dans `docs/00-ingested/source_manifest.json` avec son empreinte SHA-256 et ses sections canoniques.
- Maintenir la distinction épistémique :
  - `what_it_actually_proves` : faits et données démontrés.
  - `what_it_does_not_prove` : limites, hypothèses et zones non couvertes.
- Les entités et concepts alimentent `docs/04-transverse/lexique_domaine.md`.

## 5. Synchronisation Obligatoire Post-Ingestion
- Toute séquence d'ingestion doit être clôturée par :
  ```bash
  python src/swarm.py sync --project <nom_projet>
  ```
  afin de garantir la fraîcheur de l'index de recherche SQLite FTS5 et de l'hypergraphe Graphify.
