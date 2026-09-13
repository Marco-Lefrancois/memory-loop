---
name: thinking-kepner-tregoe
description: Diagnostic d'anomalies par matrice différentielle IS / IS-NOT et comparaison pondérée d'options (Problem Analysis & Decision Analysis) (ADR-0336).
disable-model-invocation: true
---

# 🎯 Kepner-Tregoe Analysis (IS / IS-NOT Differential)

**Règle d'or :** Diagnostiquer les anomalies en testant les causes candidates à la fois contre ce qui **EST** (*IS*) et ce qui **N'EST PAS** (*IS-NOT*). Pour les choix d'options à fort impact, filtrer d'abord les prérequis stricts (*MUSTs*), pondérer les critères souhaitables (*WANTs*) et expliciter les conséquences indésirables avant sélection.

---

## ⚡ Quand l'utiliser (*When to Use*)
- Une anomalie ou régression affecte certains objets, composants, endpoints ou environnements, mais pas d'autres apparemment similaires.
- Plusieurs causes plausibles subsistent et la délimitation de la frontière de contraste permet de discriminer la vraie cause racine.
- Un choix d'architecture ou de conception présente des critères non négociables, des compromis concurrents et des risques opérationnels à comparer objectivement.
- Cadrage d'une User Story mLoop pour délimiter strictement le périmètre dans les Piliers Gherkin 2 (Exceptions) et 3 (Résilience).

## 🚫 Quand NE PAS l'utiliser (*When NOT to Use*)
- Une panne uniforme et globale sans contraste significatif *IS-NOT*, ou cause racine déjà confirmée par une trace univoque.
- Une observation immédiate et triviale suffit à clore l'investigation.
- Les critères ne peuvent être formulés de manière opérationnelle ou mesurable.
- Phase purement exploratoire de découverte amont (utiliser `pre-mortem` ou `scientific-method`).

---

## 📋 Procédure Opérationnelle

### Mode 1 : Analyse de Problème (Problem Analysis)
1. **Définir la cible précise** : Formuler l'objet, le comportement déviant et l'environnement.
2. **Construire la Matrice IS / IS-NOT** :
   - **QUOI (*WHAT*)** : Quel est le défaut exact ? vs Quel défaut similaire aurait pu survenir mais n'apparaît pas ?
   - **OÙ (*WHERE*)** : Sur quel module/écran/endpoint se produit-il ? vs Où aurait-il pu se produire sans s'y manifester ?
   - **QUAND (*WHEN*)** : À quel moment exact / après quelle action survient-il ? vs Quand aurait-il pu survenir mais ne se produit pas ?
   - **MAGNITUDE (*EXTENT*)** : Combien d'occurrences / quelle volumétrie ? vs Combien auraient pu être touchées ?
3. **Identifier les distinctions & changements récents** : Qu'est-ce qui est unique ou a changé récemment entre le côté *IS* et le côté *IS-NOT* ?
4. **Tester les causes candidates** : La cause candidate explique-t-elle à la fois le *IS* ET le *IS-NOT* ? Éliminer toute cause qui contredit l'un des deux volets.

### Mode 2 : Analyse de Décision (Decision Analysis)
1. **Énoncer la décision & les alternatives** : Lister les 2 à 4 options crédibles.
2. **Filtrer les MUSTs (Conditions éliminatoires)** : Rejeter immédiatement toute option qui ne satisfait pas 100% des exigences non négociables.
3. **Pondérer les WANTs (Critères d'optimisation)** : Évaluer les options restantes sur les critères souhaitables (poids de 1 à 10).
4. **Expliciter les conséquences indésirables** : Lister les risques collatéraux pour chaque option avant conclusion.
