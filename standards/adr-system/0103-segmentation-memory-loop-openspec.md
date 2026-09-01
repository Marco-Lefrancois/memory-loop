# ADR-0103 : Segmentation Cognitive entre Memory Loop et OpenSpec
## Statut : Accepté (Série 01xx - Isolation)

---

## 1. Contexte & Problématique

Avec la coexistence de Memory Loop (Machine à états cognitive de haut niveau) et d'OpenSpec (Framework d'implémentation de la phase de Build), il est nécessaire de prévenir toute superposition de responsabilités ou spec-drift.

---

## 2. Décision

Nous officialisons une **frontière hermétique** :

1. **Le Domaine de Memory Loop (Cerveau & Alignement)** :
   - Contient la vision stratégique, l'analyse d'affaires, les règles `RM-XXX`, le backlog (`backlog/`) et la mémoire opérationnelle.
   - Régit les modes `ProjectMode.CLIENT` et `ProjectMode.MLOOP`.
2. **Le Domaine des Outils de Build Physique (OpenSpec, etc.)** :
   - Confiné à la phase d'exécution du code physique.
   - **Interdit dans l'analyse interne en mode `ProjectMode.CLIENT` au sein de mLoop**.
   - **Indépendance d'Outillage (ADR-0319)** : En mode client, les outils et frameworks de build (OpenSpec, Cursor, Copilot, etc.) sont opérés librement par l'équipe de dev aval. mLoop produit des Story Contracts universels ("Agent-Ready" et déclaratifs), agnostiques de tout outil spécifique.

---

## 3. Conséquences

- **Zéro Spec-Drift** : L'IA ne subit aucun conflit d'autorité décisionnelle.
- **Clarté du Dépôt** : Isolation parfaite entre spécifications d'affaires (mLoop) et répertoires de build physique (OpenSpec).
- **Synergie Dual-Agent** : Flux fluide entre l'analyse fonctionnelle amont et le build assisté par IA en aval.
