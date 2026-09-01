# Gabarit Officiel de SOW & Évaluation Budgétaire (SOW & T-Shirt Sizing Template)

**Statut** : SSOT Normatif mLoop  
**Date d'effet** : 18 août 2026  
**Domaine** : Statement of Work (SOW), Cadrage Macro, Matrice d'Effort Multi-Disciplinaire, Grille T-Shirt Sizing Metro  

---

<!-- 
INSTRUCTIONS DE RÉDACTION POUR L'AGENT (ADR-0331) :
1. Conserver l'ensemble des 5 sections numérotées et les séparateurs '---'.
2. Remplacer les placeholders [ENTRE_CROCHETS] par les données réelles du projet (zéro placeholder résiduel).
3. Respecter la ventilation obligatoire des 7 disciplines (UX/UI, Analyse, Dev, Doc, QA, PM/Scrum, Hypercare).
4. RÈGLE D'OR DE GRANULARITÉ (ADR-0331) : Dans la section 3 (Développement Logiciel), chaque tâche 3.1 à 3.N DOIT obligatoirement comporter une description explicite des fonctionnalités concrètes développées et mentionner les briques déduites des angles morts (Stripe, cache hors-ligne, formats, anti-fraude) avec leur allocation d'effort (+N SP inclus).
5. Utiliser la règle de conversion : 1 SP = 8 heures, 1 jour = 1 000 $ CAD.
6. Associer l'enveloppe finale à la Grille T-Shirt Sizing Metro (RM-000 : xs à xl).
-->

# [TITRE DU PROJET] — Énoncé des Travaux (SOW)

**Client** : [Metro Inc. / Nom du Client]  
**Projet** : [Nom Officiel du Projet]  
**Partenaire Technologique** : Nmédia Solutions Inc.  
**Date** : [Date de Rédaction] | **Version** : 1.0  
**Taille T-Shirt Sizing** : **`[T-SHIRT_SIZE]`** ([N] jours / [N] h / [N] $ CAD)  
**Dépôt Azure DevOps** : [[Nom_Depot_Doc](https://dev.azure.com/NmediaInc/Nms.Mobile/_git/[Nom_Depot])]  

---

## 1. Objectif Principal (Contexte d'Affaires & Bénéfices)

[Décrire en 1 à 2 paragraphes clairs et synthétiques la raison d'être du projet, le problème utilisateur résolu, la valeur ajoutée pour le client et la conformité légale/stratégique visée].

---

## 2. Portée du Projet (*Scope*)

### 2.1 Fonctionnalités Incluses par Composant

* **Composant 1 : [Nom du Composant]**
  - [Fonctionnalité 1.1]
  - [Fonctionnalité 1.2]
* **Composant 2 : [Nom du Composant]**
  - [Fonctionnalité 2.1]
  - [Fonctionnalité 2.2]
* **Composant 3 : [Nom du Composant]**
  - [Fonctionnalité 3.1]
  - [Fonctionnalité 3.2]

### 2.2 Exclusions

- ❌ **[EXCL-01]** [Exclusion explicite 1].
- ❌ **[EXCL-02]** [Exclusion explicite 2].
- ❌ **[EXCL-03]** [Exclusion explicite 3].

---

## 3. Hypothèses du Projet

1. **[Hypothèse 1]** : [Description de l'hypothèse technique ou organisationnelle].
2. **[Hypothèse 2]** : [Description de l'hypothèse d'intégration ou de backend].
3. **[Hypothèse 3]** : [Description de l'hypothèse de validation légale ou client].
4. **[Hypothèse 4]** : [Description de l'hypothèse d'environnements ou de données de test].

---

## 4. Découpage des Récits Macro (Backlog)

| ID | Parcours / Composant | SP | Titre & Description Sommaire (*INVEST*) |
| :--- | :--- | :---: | :--- |
| `US-01` | [Composant 1] | 3 | **[Titre US 1]** : [Description sommaire En tant que... je veux... afin de...]. |
| `US-02` | [Composant 2] | 5 | **[Titre US 2]** : [Description sommaire]. |
| `US-03` | [Composant 3] | 3 | **[Titre US 3]** : [Description sommaire]. |
| `US-TECH-01` | [Socle Technique] | 5 | **[Titre US Tech]** : [Description technique]. |

---

## 5. Évaluation Budgétaire (Tableau de Chiffrage Détaillé)

| # | Discipline & Tâche | SP | Heures | Commentaires & Hypothèses de Calcul |
| :---: | :--- | :---: | :---: | :--- |
| **1** | **Conception UX/UI** | **[N] SP** | **[N] h** | |
| 1.1 | Conception UX & Flux Utilisateur | [N] SP | [N] h | Wireframes, états vides et gestion d'erreurs. |
| 1.2 | Déclinaison UI Design System | [N] SP | [N] h | Maquettes graphiques maîtresse (Figma) et thèmes. |
| **2** | **Analyse & Spécifications** | **[N] SP** | **[N] h** | |
| 2.1 | Rédaction des récits | [N] SP | [N] h | Découpage fin et critères INVEST. |
| 2.2 | Atelier | [N] SP | [N] h | Arbitrages et validation DoR. |
| 2.3 | Rencontre interne (Grooming, Sync) | [N] SP | [N] h | Alignement continu et préparation des sprints. |
| **3** | **Développement Logiciel (Mobile / Backend)** | **[N] SP** | **[N] h** | *(Règle ADR-0331 : Décrire explicitement les fonctionnalités réelles pour chaque sous-tâche 3.1 à 3.N)* |
| 3.1 | [Nom du Sous-Composant / Écran 1] | [N] SP | [N] h | [Description précise des flux, formulaires, écrans et intégration backend]. |
| 3.2 | [Nom du Sous-Composant / Écran 2] | [N] SP | [N] h | [Description précise + mention des ajouts d'angles morts ex: cache local, formats spécifiques avec +N SP inclus]. |
| 3.3 | [Nom du Sous-Composant / Backend API] | [N] SP | [N] h | [Description précise des endpoints, règles de sécurité, gestion des tokens ou tiers]. |
| **4** | **Documentation Technique** | **[N] SP** | **[N] h** | |
| 4.1 | Guide d'architecture & Contrats d'API OpenAPI | [N] SP | [N] h | Schémas de séquences et spécifications techniques. |
| **5** | **Assurance Qualité (QA) & Tests Multi-OS** | **[N] SP** | **[N] h** | |
| 5.1 | Rédaction des scénarios de test Zephyr Scales | [N] SP | [N] h | Couverture des 4 Piliers Gherkin. |
| 5.2 | Exécution des tests fonctionnels & non-régression | [N] SP | [N] h | Validation sur appareils cibles iOS et Android. |
| **6** | **Gestion de Projet (PM / Scrum)** | **[N] SP** | **[N] h** | |
| 6.1 | Coordination des livraisons & animation Scrum | [N] SP | [N] h | Suivi de vélocité et gestion des dépendances. |
| 6.2 | Préparation des builds & soumission Stores | [N] SP | [N] h | Releases et fiches de déploiement. |
| **7** | **Hypercare & Support Post-MEP** | **[N] SP** | **[N] h** | |
| 7.1 | Monitoring télémétrie & Logs consoles | [N] SP | [N] h | Surveillance en temps réel et support immédiat. |
| 🏁 | **TOTAL GLOBAL DU MANDAT** | **[N] SP** | **[N] h** | **[N] Jours Ouvrés ([N] $ CAD — Taille `[T-SHIRT_SIZE]`)** |

---

### Grille de Référence Kevin Chamberland (Metro)

| Taille | Effort (Jours) | Valeur ($ CAD) | Portée Typique & Équivalence |
| :---: | :---: | :---: | :--- |
| **`-`** | 0 j | 0 $ | Exclusions explicites de périmètre |
| **`xs`** | 15 j | 15 000 $ | Micro-ajustement / Écran unique simple |
| **`XS`** | 28,5 j | 28 500 $ | Petite fonctionnalité isolée |
| **`s`** | 35 j | 35 000 $ | Module fonctionnel standard |
| **`S`** | 50 j | 50 000 $ | Module complet avec tests |
| **`m`** | 75 j | 75 000 $ | Projet moyen multi-codebases |
| **`M`** | **95 j** | **95 000 $** | **Projet multi-codebases avec contraintes légales (ex: Santé / OneTrust)** |
| **`l`** | 175 j | 175 000 $ | Initiative majeure multi-systèmes |
| **`L`** | 235 j | 235 000 $ | Refonte d'envergure multi-applications |
| **`xl`** | 250 j | 250 000 $ | Projet stratégique entreprise multi-annuel |
