---
type: prd
status: draft
---
# PRD — [Nom du Produit / Projet]

## 1. Problem Statement
* Description du problème du point de vue de l'utilisateur final.

## 2. Solution & Architecture
* Vue d'ensemble de la solution technique et des choix structurants.
* **Important**: Cette section ne doit contenir aucun jargon interne d'IA (pas de référence aux agents, au budget cognitif, etc.).

## 3. Deep Modules & Testing Seams
* Liste des "Boîtes Grises" (modules profonds) identifiés.
* **Frontières d'isolation**: Ce que le module cache du reste de l'application.
* **Contrats**: Interfaces d'entrées/sorties stables.
* **Coutures de test (Testing Seams)**: Les points d'entrée au plus haut niveau pour cibler les futurs tests fonctionnels.

## 4. Business Rules & User Stories
* Liste numérotée des stories.
* Critères d'acceptation sous forme de scénarios **Gherkin**.

## 5. Out-of-Scope (Hors-périmètre)
* Limites strictes définies pour éviter la dispersion du périmètre.
