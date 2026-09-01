---
name: thinking-cynefin
description: Classification du domaine de complexité (Simple, Complicated, Complex, Chaotic) pour sélectionner la bonne posture d'ingénierie et déclencher les Spikes techniques (ADR-0336).
disable-model-invocation: true
---

# 🌐 Cynefin Classification (Complexity Domain Mapping)

**Règle d'or :** Classifier la relation de cause à effet avant d'appliquer une méthode de résolution. L'erreur fatale consiste à appliquer des méthodes prédictives (spécification rigide) sur des problèmes complexes émergents (qui exigent des Spikes d'expérimentation).

---

## ⚡ Quand l'utiliser (*When to Use*)
- Triage de backlog ou cadrage d'une fonctionnalité : incertitude sur la démarche (appliquer une recette éprouvée, analyser en profondeur, ou prototyper / spiker).
- Une méthode d'analyse ou de spécification échoue de manière répétée en raison d'inconnues non réductibles.
- Détermination du statut de la story : création directe d'un récit vertical vs création d'un Spike technique (`US-SPIKE-XXX.md` - ADR-0306).

## 🚫 Quand NE PAS l'utiliser (*When NOT to Use*)
- Le domaine et la méthode de résolution sont déjà évidents et partagés.
- La tâche consiste à trouver la cause précise d'un bug identifié (utiliser `thinking-kepner-tregoe` ou `scientific-method`).
- Modifications mécaniques ou cosmétiques sans incertitude méthodologique.

---

## 📋 Procédure de Typage & Postures d'Action

1. **Isoler l'unité de travail** : Définir la fonctionnalité, le module ou le problème cible.
2. **Évaluer la nature du lien Cause ➔ Effet** :
   - **Clair / Simple (*Clear / Simple*)** : Le lien est évident pour tous.
     - *Mécanisme* : **Percevoir ➔ Catégoriser ➔ Répondre** (*Sense ➔ Categorize ➔ Respond*).
     - *Action mLoop* : Appliquer le blueprint standard (`story_template.md`).
   - **Compliqué (*Complicated*)** : Le lien existe mais exige une expertise technique ou une analyse approfondie.
     - *Mécanisme* : **Percevoir ➔ Analyser ➔ Répondre** (*Sense ➔ Analyze ➔ Respond*).
     - *Action mLoop* : Session Grill-with-Docs + Fact-Search FTS5 approfondi.
   - **Complexe (*Complex*)** : Le lien ne peut être compris que rétrospectivement ; comportement émergent avec nombreuses inconnues.
     - *Mécanisme* : **Tester ➔ Percevoir ➔ Répondre** (*Probe ➔ Sense ➔ Respond*).
     - *Action mLoop* : **Déclencher obligatoirement un Spike technique (`US-SPIKE-XXX.md`)** en Priorité #1 avant toute rédaction définitive.
   - **Chaotique (*Chaotic*)** : Aucune relation cause-effet perceptible ; crise ou incident bloquant en cours.
     - *Mécanisme* : **Agir ➔ Percevoir ➔ Répondre** (*Act ➔ Sense ➔ Respond*).
     - *Action mLoop* : Stabilisation d'urgence / pause de sécurité `wait-what`.
3. **Traiter le Désordre (*Disorder*)** : Si un projet comporte un mélange de domaines, le décomposer immédiatement en sous-composants unitaires homogènes.
