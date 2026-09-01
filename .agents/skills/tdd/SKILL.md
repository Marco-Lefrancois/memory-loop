---
name: tdd
description: Skill d'implémentation physique guidée par les tests unitaires (Test-Driven Development Red-Green-Refactor) pour l'auto-évolution du framework mLoop.
---

# 🧪 Skill `/tdd` (Test-Driven Development Loop)

> **Standard :** mLoop TDD & Tracer Bullet Protocol  

## 🧠 Description
Le skill `/tdd` régit les modifications de code physique dans le framework mLoop (`src/`). Il impose l'écriture préalable d'assertions ou de tests unitaires (Red) avant toute modification de la logique applicative (Green) puis le nettoyage (Refactor).

## ⚡ Le Cycle TDD en 3 Étapes
1. **Étape RED (Test d'abord)** : Écrire le test unitaire dans `tests/` ou le script de reproduction minimal dans `memory/` qui échoue.
2. **Étape GREEN (Code minimal)** : Écrire le code le plus simple possible dans `src/` pour faire passer le test.
3. **Étape REFACTOR (Optimisation & Calibrate)** : Nettoyer le code, exécuter `python src/swarm.py --project mLoop calibrate` et s'assurer qu'aucun régressivité n'est introduite.
