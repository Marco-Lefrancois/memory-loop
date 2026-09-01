# Registre des Tâches - Intégration Graph Engineering mLoop

Ce document consigne la grille des sous-tâches validées lors de l'intégration du Graph Engineering dans le framework mLoop.

---

- [x] **Phase 1: Module d'Évidence Structurée (`src/pipelines/evidence.py`)**
  - [x] Créer les classes `EvidenceItem`, `EvidencePack` et `EvidenceReducer`.
  - [x] Implémenter les méthodes de déduplication et de sérialisation JSON.

- [x] **Phase 2: Évolution de `GraphRouter` (`src/pipelines/graph_router.py`)**
  - [x] Ajouter les énumérations `NodeCategory` et `RiskLevel`.
  - [x] Implémenter le support du Fan-Out dynamique et des nœuds déterministes.
  - [x] Implémenter la barrière de synchronisation et l'agrégateur `ReducerNode`.

- [x] **Phase 3: Évolution de `EvaluatorNode` (`src/pipelines/evaluator_node.py`)**
  - [x] Implémenter le routage par le risque (Fast Track vs Deep Review).
  - [x] Produire un `EvidencePack` structuré d'évaluation.

- [x] **Phase 4: Connexion Wayfinder & CLI `swarm.py`**
  - [x] Ajouter la méthode `to_dag()` dans `WayfinderEngine`.
  - [x] Mettre à jour `swarm.py graph-run` pour l'exécution dynamique et la sauvegarde des logs.

- [x] **Phase 5: Validation & Tests**
  - [x] Valider l'exécution synchrone et synchro SQLite (`python src/swarm.py audit-loop`).
