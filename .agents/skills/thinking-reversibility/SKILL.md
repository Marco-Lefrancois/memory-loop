---
name: thinking-reversibility
description: Classification des décisions d'ingénierie et d'architecture en Type 1 (irréversible / porte à sens unique) vs Type 2 (réversible / porte à double sens) (ADR-0336).
disable-model-invocation: true
---

# 🚪 Reversibility (Type 1 vs Type 2 Decision Governance)

**Règle d'or :** Aligner la profondeur d'analyse sur le coût de réversion (*Undo Cost*). La plupart des décisions sont bien plus simples à inverser qu'il n'y paraît (décider vite) ; les rares décisions irréversibles méritent une délibération approfondie, un ADR formel et un engagement par étapes.

---

## ⚡ Quand l'utiliser (*When to Use*)
- Incertitude sur le niveau de délibération à accorder à un choix technique, architectural, d'outillage ou d'organisation.
- Risque de créer des comités d'analyse excessifs pour des choix à faible rayon d'impact (*Type 2*), ou inversement d'acter précipitamment un choix à fort verrouillage (*Lock-in / Type 1*).
- Possibilité de restructurer le choix (feature flag, abstraction, timebox, spike de faisabilité) pour en réduire le coût de réversion.
- Préparation d'une session Grill-with-Docs ou arbitrage de création d'ADR (ADR-0320 / ADR-0336).

## 🚫 Quand NE PAS l'utiliser (*When NOT to Use*)
- Décision déjà classifiée au cours de la session mLoop (agir à la profondeur requise sans re-classifier indéfiniment).
- Choix triviaux de Type 2 (noms de variables, refactoring local) où classifier coûte plus cher que d'exécuter directement.
- Contraintes externes imposées sans optionalité (date butoir réglementaire, contrat non négociable).
- Garde-fous de sécurité ou d'intégrité des données qui exigent la solution exacte et non une vitesse de parade.

---

## 📋 Procédure Opérationnelle

1. **Nommer la décision et le chemin de retour (*Undo Path*)** :
   - Énoncer l'engagement proposé et la manœuvre concrète de retour en arrière (rollback, migration inverse, abandon de SDK, refonte de contrat).
2. **Évaluer le profil de réversibilité** :
   - Mesurer : effort technique, temps, rupture de données, dépendants externes et coût d'apprentissage perdu.
   - **Type 2 (Porte à double sens)** : Réversible en quelques jours à faible coût ➔ **Décision rapide et locale**. Pas d'ADR lourd requis.
   - **Type 1.5 (Porte semi-ouverte)** : Réversible en quelques semaines à coût modéré ➔ **Structure légère + monitoring d'impact**.
   - **Type 1 (Porte à sens unique)** : Réversion en mois ou quasi impossible sans rupture majeure (schéma DB de prod, protocole d'échange, modèle d'authentification) ➔ **ADR officiel obligatoire (`docs/01-architecture/`) + revue contradictoire Sentinel**.
3. **Appliquer le réducteur de réversibilité si Type 1** :
   - Peut-on scinder la décision en sous-étapes réversibles (Pattern Strangler, interface d'abstraction, Feature Toggle, Spike isolé) ?
