---
name: thinking-triz
description: Résolution de contradictions d'ingénierie et d'architecture sans compromis destructeur par séparation spatiale, temporelle, conditionnelle ou d'échelle (ADR-0336).
disable-model-invocation: true
---

# ⚙️ TRIZ (Théorie de Résolution des Contradictions d'Ingénierie)

**Règle d'or :** Résoudre les contradictions techniques d'architecture sans compromis médiocre au milieu. Nommer le conflit sous forme formelle, séparer les états opposés et transformer la conception pour obtenir les deux bénéfices simultanément.

---

## ⚡ Quand l'utiliser (*When to Use*)
- Deux exigences architecturales ou paramètres système tirent dans des directions opposées (ex: stabilité vs évolutivité, fraîcheur des données vs latence de cache, rigueur de validation vs fluidité UX).
- Vous êtes sur le point d'accepter un compromis dégradant parce que "on ne peut pas avoir le beurre et l'argent du beurre".
- Toutes les solutions candidates partagent la même faiblesse structurelle : le blocage réside dans la contradiction des exigences.

## 🚫 Quand NE PAS l'utiliser (*When NOT to Use*)
- Une option est manifestement supérieure sous les contraintes actuelles.
- Une mesure peu coûteuse (profiling/benchmark) suffit à départager l'arbitrage.
- Un pattern architectural standard résout déjà élégamment la situation (ex: CQRS, Outbox pattern, cache-aside, feature flags).

---

## 📋 Procédure de Résolution des Contradictions

1. **Formuler la contradiction sous forme canonique** :
   > *"Nous avons besoin que le [PARAMÈTRE] soit dans l'[ÉTAT 1] pour [BÉNÉFICE 1], MAIS dans l'[ÉTAT 2] pour [BÉNÉFICE 2]."*
   - *Exemple* : "Nous avons besoin que le contexte du prompt soit ultra-complet pour la justesse de raisonnement, MAIS minimal pour économiser le budget de tokens."
2. **Définir le Résultat Idéal Final (*Ideal Final Result - IFR*)** :
   - Décrire l'état où les deux bénéfices sont préservés avec un minimum de nouvelle mécanique.
3. **Tester les 4 Principes de Séparation (dans cet ordre)** :
   - **Séparation dans le Temps (*Time*)** : L'état 1 à un instant $T_1$, l'état 2 à un instant $T_2$ (ex: indexation asynchrone hors ligne vs lecture rapide en ligne).
   - **Séparation dans l'Espace (*Space*)** : L'état 1 dans un composant/couche A, l'état 2 dans un composant/couche B (ex: graphe global en base SQLite locale vs injection chirurgicale de sous-graphe dans le prompt via progressive disclosure).
   - **Séparation sous Condition (*Condition*)** : L'état 1 en mode nominal, l'état 2 en mode dégradé ou haute criticité (ex: exécution directe pour les tâches simples, passage en sous-agent pour les tâches lourdes).
   - **Séparation d'Échelle (*Scale*)** : L'état 1 au niveau macro/interface, l'état 2 au niveau micro/implémentation.
4. **Formuler la solution no-compromise** et documenter l'arbitrage dans un ADR.
