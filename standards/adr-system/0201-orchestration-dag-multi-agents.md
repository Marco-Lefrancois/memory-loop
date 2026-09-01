# ADR-0201 : Orchestration DAG Multi-Agents & Evidence Packs
## Statut : Accepté (Série 02xx - Orchestration DAG)

---

## 1. Contexte

Pour le traitement d'initiatives complexes multi-modules, l'exécution mono-agent devient un goulot d'étranglement. Il est nécessaire d'exécuter des topologies d'agents parallèles tout en garantissant un contrôle qualité neutre et déterministe.

---

## 2. Décision

Nous adoptons le moteur d'**Orchestration DAG Multi-Agents (`python src/swarm.py graph-run`)** :

1. **Pattern Diamant & Fan-Out** : Portée définie $\rightarrow$ Exécution parallèle par spécialités $\rightarrow$ Barrier $\rightarrow$ Reducer Python déterministe $\rightarrow$ Node Évaluateur neutre (`evaluator_node.py`).
2. **EvidencePacks JSON Typés** : Transport d'informations strictement typé et validé entre les arêtes du DAG (`src/pipelines/evidence.py`).
3. **Risk-Based Routing (Routage par le Risque)** :
   - Risque `LOW` : Fast-track déterministe automatique via `WikiFix`.
   - Risque `HIGH/CRITICAL` : Revue contradictoire approfondie par l'Évaluateur (`WikiFix` + INVEST + 4 Piliers Gherkin).

---

## 3. Conséquences

- **Performance & Scalabilité** : Exécution parallèle sécurisée.
- **Traçabilité Totale** : Consignation de l'exécution dans `backlog/graph_execution_log.json`.
