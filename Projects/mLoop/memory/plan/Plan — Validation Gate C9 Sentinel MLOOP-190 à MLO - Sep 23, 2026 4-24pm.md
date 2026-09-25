---
created: 2026-09-23T20:24:38.681Z
source: plannotator
tags: [plannotator, memory-loop, validation, gate, sentinel]
---

[[Plannotator Plans]]

# Plan — Validation Gate C9 / Sentinel MLOOP-190 à MLOOP-194

## Gouvernance et périmètre
- Exécuter la validation en worker Herdr isolé : la mission est une validation multi-récits et crée 15 artefacts (critères Volume, Durée et Type de la Delegation Gate satisfaits).
- Ne modifier ni les cinq récits ni leur frontmatter, ni `src/core/ast_checker.py`, ni l’état de cycle de vie ; ne réaliser aucun commit ni push.
- Mettre à jour `Projects/mLoop/memory/worker_MLOOP-190-BE.status` pour refléter les phases du worker et son résultat.

## Exécution séquentielle dans le worker
1. Pour chacun des récits `MLOOP-190-BE`, `MLOOP-191-BE`, `MLOOP-192-BE`, `MLOOP-193-BE`, `MLOOP-194-BE`, lancer `rubber-duck`, vérifier le rapport substantif correspondant sous `backlog/reviews/` et traiter immédiatement toute erreur CLI.
2. Lire chaque récit, l’épopée Click CLI, les ADR-0202, ADR-0339, ADR-0369 et ADR-0370, ainsi que le protocole de dossier de preuves ; produire le fact dossier avec les six sections prescrites, citations verbatim liées par `file:///` et bornes de lignes, exemptions backend correctement justifiées.
3. Créer l’EvidencePack JSON de chaque récit avec le statut existant, le résultat Gate C9, les preuves sourcées, la référence Sentinel et un horodatage ISO 8601.
4. Vérifier que les 5 rapports, 5 dossiers et 5 JSON existent et sont cohérents sans modifier les statuts des récits.
5. Exécuter `python src/swarm.py sync --project mLoop`, confirmer que le blocage WikiFix de MLOOP-190 est levé, puis fermer proprement le worker (harvest + close).

## Vérification et restitution
- Produire le récapitulatif exact demandé : statut global, comptes et chemins des rapports Sentinel, comptes des dossiers/JSON, résultat WikiFix, blockers éventuels et durée.
- En cas d’échec non corrigeable, conserver les artefacts valides, inscrire le détail dans la sidecar de statut et signaler le blocker sans masquer l’erreur.