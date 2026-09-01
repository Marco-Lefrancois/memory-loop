# ADR-0300 : Story Constraint Contract (SCC) & INVEST Score
## Statut : Accepté (Série 03xx - Story Contract)

---

## 1. Contexte

Pour éliminer le risque de divergence entre l'analyse fonctionnelle et la livraison, la rédaction d'un récit ne peut plus reposer sur une description informelle. Elle doit être scellée par des contraintes métier explicites.

---

## 2. Décision

Adoption obligatoire du **Story Constraint Contract (SCC)** :

1. **Frontière d'Analyse Scellée** : Aucune story ne passe en statut `READY_FOR_GROOMING` sans un contrat d'accompagnement définissant les contraintes de réalisation.
2. **Évaluation INVEST Déterministe** : Calcul automatique de l'INVEST Score par la phase QA (`wikifix` / `aoep`). Un score < 80% bloque la transition.

---

## 3. Conséquences

- **Cristallisation du Besoin** : Élimine l'évaporation d'information.
- **Auditabilité Métier** : Évaluation objective de la qualité du récit.
