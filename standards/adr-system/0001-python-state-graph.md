# ADR-0001 : Choix de Python 3.12+ et d'un Graphe d'États Déterministe
## Statut : Accepté (Série 00xx - Fondations)

---

## 1. Contexte

Le système de planification et de validation **Memory Loop** requiert une orchestration multi-agents déterministe et fortement typée. Les agents doivent partager un état complexe de manière sûre, sans dérive ni boucles infinies.

---

## 2. Décision

Nous imposons **Python (3.12+)** comme runtime principal unique, associé à une architecture par **Graphe d'États (State Graph)** et au moteur de validation **Pydantic v2** (`src/state.py`).

Principes clés :
1. **Shared State Typé (`LoopState`)** : Schéma d'état unique, immuable et typé pour toutes les lectures et écritures.
2. **Circuit Breakers & Robustesse** : Contrôle financier (`TokenBudget`) et limite de révisions (`MaxRevisionsReached`).
3. **CLI Unifié (`src/swarm.py`)** : Entrée unique pour toutes les commandes de la suite mLoop avec Rich Console Zero-Fluff.

---

## 3. Conséquences

- **Déterminisme Total** : Réponses LLM contraintes par schémas Pydantic stricts.
- **Fiabilité Opérationnelle** : Éradication des erreurs d'état grâce aux types statiques.
