# Checklist de Déclenchement & Gouvernance des Workers Herdr

Cette checklist normative régit le cycle de vie de tout worker éphémère exécuté via Herdr PTY (`herdr-orchestration`, [`ADR-0310`](../../standards/adr-system/README.md), [`ADR-0360`](../../standards/adr-system/README.md)).
Elle garantit l'absence totale de processus fantômes (*zombies*) et l'intégrité de la mémoire de travail.

---

## 1. Matrice des 4 Critères de Déclenchement Herdr

Un fork de worker Herdr est justifié SI ET SEULEMENT SI au moins l'un des 4 critères est satisfait :

- [ ] **Critère 1 : Volume de Fichiers Importants (≥ 3 fichiers)** : La tâche implique la lecture ou modification concurrente de 3 fichiers ou plus dans des sous-systèmes distincts.
- [ ] **Critère 2 : Durée d'Exécution Estimée (> 5 minutes)** : Exécution de suites de tests longues, crawl massif, ingestion multi-documents ou compilation lourde.
- [ ] **Critère 3 : Tâche Critique de Sécurité / Red Team / Spike** : Audit contradictoire, simulation d'attaques ou prototypage jetable isolé.
- [ ] **Critère 4 : Risque Élevé de Pollution de Contexte** : Génération de logs verbeux ou manipulation de formats bruts risquant de saturer la fenêtre de contexte de l'agent maître.

---

## 2. Préparation du Prompt Éphémère & Isolation

- [ ] **Prompt Déporté dans Scratch** : Le prompt d'instructions du worker est écrit dans un fichier scratch dédié (`memory/scratch/worker_<ID>_prompt.md`) et passé par référence, jamais injecté en bloc dans la commande CLI.
- [ ] **Périmètre Délimité** : Le worker a une mission unitaire et bornée. Il ne doit pas ré-invoquer d'autres sous-agents de façon récursive non supervisée.
- [ ] **Flags de Monitoring Actifs** : Session lancée avec timeout explicite et logging redirectif vers `memory/scratch/worker_<ID>.log`.

---

## 3. Teardown Gate & Anti-Zombies (Non Négociable)

- [ ] **Arrêt Confirmé du Processus** : Dès la fin de la tâche ou en cas d'erreur/timeout, le PID ou la session tmux/PTY associée est formellement arrêtée (`manage_task: kill` ou signal `SIGTERM`).
- [ ] **Vérification d'Orphelins** : Aucun processus résiduel ne tourne en arrière-plan après la phase de récolte.

---

## 4. Récolte & Réconciliation (*Harvest*)

- [ ] **Extraction des Faits Clés** : Seuls les résultats synthétiques et le statut de sortie (PASS/FAIL) sont réinjectés dans la conversation principale.
- [ ] **Nettoyage des Artefacts Temporaires** : Les fichiers intermédiaires sont purgés ou archivés proprement sous `memory/scratch/`.
