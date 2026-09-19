---
name: herdr-orchestration
description: Gouvernance d'orchestration PTY multi-agents via Herdr, isolation de contexte Fork & Harvest, et politique stricte Anti-Zombies. Use when delegating long-running, multi-file, or context-polluting background tasks to ephemeral worker agents.
---

# 🤖 Skill : Gouvernance d'Orchestration Herdr & Workers PTY (`/herdr-orchestration`)

## Aperçu & Rôle Souverain
Ce skill régit la délégation de travail vers des agents workers éphémères dans des sessions multiplexées PTY Herdr ([ADR-0310](../../standards/adr-system/README.md), [ADR-0345](../../standards/adr-system/README.md), [ADR-0360](../../standards/adr-system/README.md)). Il garantit l'isolation stricte de la mémoire de l'agent maître et prévient l'apparition de processus fantômes (*Zero Zombie Policy*).

## Déclencheurs & Exclusions
- **Quand l'utiliser** : Tâche satisfaisant au moins un des 4 critères de la matrice de déclenchement ([`.agents/references/herdr-worker-checklist.md`](../references/herdr-worker-checklist.md)) :
  1. *Volume* : Modification ou lecture de ≥ 3 fichiers distincts.
  2. *Durée* : Exécution estimée > 5 minutes (tests longs, compilations, crawl lourd).
  3. *Sécurité / Red Team* : Audit contradictoire, simulation d'attaques ou spike jetable.
  4. *Pollution* : Risque élevé de saturer la fenêtre de contexte par des logs verbeux.
- **Quand NE PAS l'utiliser** : Pour les tâches unitaires et rapides (< 1 minute, 1 fichier) ➔ exécuter directement dans la session principale.

---

## Le Protocole Fork & Harvest en 4 Phases

```
1. PREPARE (Scratch)  ──→ 2. SPAWN (PTY)        ──→ 3. HARVEST (Synthèse) ──→ 4. TEARDOWN GATE
   Écrire prompt auto-   Déléguer au worker       Moissonner résultats      Tuer le processus
   suffisant dans file    avec timeout borné       dans EvidencePack         et purger zombies
```

### 1. Préparation du Prompt Éphémère (Clean Slate)
- Tout worker démarre dans une session vierge.
- S'assurer au préalable que le runtime est opérationnel via `python src/swarm.py doctor --agents` ou `agent-probe` (ADR-0377).
- Écrire le prompt complet dans un fichier scratch (`memory/scratch/worker_<ID>_prompt.md`).
- Le prompt DOIT être auto-suffisant (chemin du fichier, séquence d'actions, commande de synchronisation). Ne jamais passer de prompt brut volumineux dans la ligne de commande.

### 2. Délégation (Spawn)
- Utiliser la commande CLI haut niveau :
  ```bash
  python src/swarm.py worker-spawn --project <PROJET> --story <ID> --task-type validation
  ```

### 3. Moisson & Réconciliation (Harvest)
- Récupérer uniquement les faits tangibles et le statut d'achèvement (PASS/FAIL) :
  ```bash
  python src/swarm.py worker-harvest --project <PROJET> --story <ID>
  ```
- Enrichir le sidecar `*_evidence.json` et fermer le volet worker :
  ```bash
  python src/swarm.py worker-close --project <PROJET> --story <ID>
  ```

### 4. Teardown Gate (Anti-Zombies Inviolable)
- Tout processus worker doit être formellement arrêté à la clôture de la tâche ou en cas de timeout.
- En cas de doute ou de crash, déclencher le moissonneur de zombies :
  ```bash
  herdr plugin action invoke reap_zombies --plugin org.mloop.orchestrator
  ```

---

## Table Anti-Rationalisation (Inviolable)

| Excuse de l'Agent (Paresse) | Réalité & Règle Inviolable |
| :--- | :--- |
| *"C'est plus simple de lancer le gros crawl de 100 pages directement dans mon terminal."* | Sature irrémédiablement la fenêtre de contexte de l'agent maître et provoque un Context Rot immédiat. Délégation obligatoire. |
| *"La tâche est finie, je laisse le worker ouvert au cas où j'en aurais encore besoin."* | Violation de la Zero Zombie Policy. Un worker inactif consomme des ressources système et des descripteurs PTY. Fermeture immédiate obligatoire. |
| *"Je vais injecter tout le contexte de 50k tokens dans les arguments du worker."* | Risque de dépassement de tampon OS (Windows/POSIX) et de fuite de tokens. Le prompt doit toujours être écrit dans un fichier scratch. |

---

## Signaux d'Alerte (Red Flags)
- Spawner un worker pour éditer un seul fichier ou corriger une faute de frappe.
- Oublier la commande `worker-close` après la récolte des résultats.
- Présence de processus orphelins dans `worker-status`.

## Vérification de Sortie
- [ ] Checklist `herdr-worker-checklist.md` validée.
- [ ] Résultats moissonnés dans l'EvidencePack.
- [ ] Zero processus zombie subsistant.
