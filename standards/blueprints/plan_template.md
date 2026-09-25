---
id: PLAN-XXX
story_id: STORY-OR-TASK-ID
status: DRAFT # DRAFT | APPROVED | EXECUTING | COMPLETED
harness: antigravity # antigravity | opencode | pi | claude-code
created_at: YYYY-MM-DD
---

# [Titre Concis & Métier de l'Implémentation]

> **Objectif** : [Description concise du problème, du contexte fonctionnel/technique et de la valeur apportée par l'intervention.]

---

## 1. User Review Required (Arbitrages & Points Clés)

> [!IMPORTANT]
> **Décisions structurantes ou impacts majeurs nécessitant une confirmation explicite de l'utilisateur :**
> - [Point d'attention 1 : ex. rupture de contrat d'API, refonte d'un schéma]
> - [Point d'attention 2 : ex. ajout d'une dépendance ou changement de comportement UX]

---

## 2. Questions Ouvertes (Open Questions)

> [!NOTE]
> **Questions de clarification ou arbitrages restants :**
> - **OQ-01** : [Description de l'interrogation] $\rightarrow$ *Recommandation : [Option A]*

---

## 3. Modifications Proposées (Proposed Changes)

Groupement par composant / domaine fonctionnel, ordonné par dépendance logique.

### [Composant A / Couche]
*Résumé de l'intervention sur ce composant.*

- #### `[MODIFY]` [`chemin/vers/fichier.ext`](file:///c:/Memory%20Loop/chemin/vers/fichier.ext)
  - **Intention** : [Description concise de l'ajustement]
  - **Impact** : [Fonctions / sections ciblées]

- #### `[NEW]` [`chemin/vers/nouveau_fichier.ext`](file:///c:/Memory%20Loop/chemin/vers/nouveau_fichier.ext)
  - **Intention** : [Rôle du nouveau fichier créé]

- #### `[DELETE]` [`chemin/vers/ancien_fichier.ext`](file:///c:/Memory%20Loop/chemin/vers/ancien_fichier.ext)
  - **Intention** : [Raison de la suppression / obsolescence]

### Matrice de Traçabilité Code ↔ Exigences (Code Evidence — ADR-0394)
> *Obligation de lier chaque symbole physique créé ou modifié à la règle métier ou au scénario Gherkin qui justifie son implémentation.*

| Symbole AST Qualifié (`chemin/fichier.py::symbole`) | Règle Métier Cible (`RM-XXX`) | Scénario Gherkin (Pilier 1-4) | Justification de l'Implémentation & Rationale | Test Unitaire Associé |
| :--- | :---: | :--- | :--- | :--- |
| `[chemin/fichier.ext::Symbole]` | `[RM-XXX ou N/A]` | `[Nom du Scénario]` | [Pourquoi ce code précis est requis, compromis ou garde-fou] | `[chemin/test_fichier.py::test_nom]` |

---

## 4. Gestion des Risques & Rollback

| Risque Identifié | Impact Potentiel | Stratégie d'Atténuation / Rollback |
| :--- | :--- | :--- |
| **[Effet de bord potentiel]** | [Moyen / Élevé] | [Procédure de rollback ou contournement] |

---

## 5. Plan de Vérification & Recette (Triple Gate)

### A. Tests Automatisés
- [ ] Commande(s) de test / linting à exécuter :
  ```powershell
  python -m pytest tests/...
  # ou npm test / python src/swarm.py vibe-check
  ```

### B. Vérifications Manuelles & Scénarios Clés
- [ ] **Scénario Nominal** : [Description du flux validé]
- [ ] **Scénario d'Exception / Résilience** : [Validation de la gestion d'erreur]

### C. Definition of Done (DoD)
- [ ] Tous les fichiers modifiés respectent les standards du projet (Zéro lint error).
- [ ] Rapport `walkthrough.md` généré (pour Antigravity) ou plan validé archivé.
- [ ] Archivage automatique du plan dans `Projects/<projet>/memory/plan/implementation_plan_<STORY_ID>.md`.
