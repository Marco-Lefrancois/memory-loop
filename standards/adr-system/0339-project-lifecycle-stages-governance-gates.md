# ADR-0339 : Portes de Gouvernance & Cycle de Vie Projet

**Statut** : Accepté  
**Date** : 18 août 2026  
**Auteurs** : Équipe mLoop & Co-Architecte Agentique  
**Domaine** : Gouvernance de Projet, Portes d'Étape (Quality Gates), Prévention de la Dérive de Phase, Alignement Commercial & Technique  

---

## 1. Contexte et Problématique

Dans les environnements agentiques multi-rôles, une ambiguïté fréquente survient entre :
1. **L'Avant-Projet / Cadrage Commercial** : Où le client a besoin d'une évaluation macroscopique rapide de type **T-Shirt Size** pour arbitrer son budget, sans payer pour la rédaction exhaustive de 50 User Stories.
2. **L'Engagement Contractuel (SOW)** : Où les hypothèses, jalons et contraintes (Loi 25, architecture) doivent être contractualisés avant tout développement.
3. **L'Ingénierie & la Rédaction Détaillée (Plan / Grill-Me ➔ Build)** : Où les récits sont rédigés au Gold Standard avec les 4 Piliers Gherkin et développés.

Sans frontières explicites, les agents IA ont tendance à basculer immédiatement en rédaction de récits de bas niveau ou en pseudo-code dès qu'on leur mentionne un projet, brûlant les étapes de cadrage macro et de validation du SOW.

---

## 2. Décisions Architecturales

Nous actons la structure séquentielle formelle en **6 Phases et 6 Portes d'Étape (*Quality Gates*)** :

### A. Phase 0 : `T-SHIRT-SIZE` (Cadrage Macro)
* Évaluation de la portée globale et des briques fonctionnelles à l'aide de la grille officielle client (Grille Kevin Chamberland : `xs` à `xl`, ratio 1 000 $/jour).
* Identification explicite des exclusions de périmètre (`-`).
* **Porte 0** : Validation de l'enveloppe globale par la direction / le client.

### B. Phase 1 : `SOW` (Statement of Work / Énoncé des Travaux)
* Rédaction du document d'engagement contractuel (`docs/01-architecture/SOW_<PROJET>.md`).
* **Porte 1** : Signature / Approbation formelle du SOW.

### C. Phase 2 : `PLAN / GRILL-ME` (Analyse & Récits Détaillés)
* Entrevue interactive ciblée *Grill-with-Docs* (1 question par tour, élimination des zones d'ombre).
* Rédaction des User Stories au gabarit Gold Standard `story_template.md` avec les **4 Piliers Gherkin** et génération des EvidencePacks.
* **Porte 2** : Definition of Ready (DoR) validée par WikiFix / Sentinel.

### D. Phase 3 : `BUILD` (Développement)
* Implémentation physique du code et des tests unitaires par les développeurs ou les workers Herdr.
* **Porte 3** : Definition of Done (DoD) — Suite de tests unitaires 100% au vert.

### E. Phase 4 : `VALIDATE` (QA & Evals)
* Audit contradictoire, tests Evals et contrôle de non-régression.
* **Porte 4** : Validation finale QA.

### F. Phase 5 : `SHIP & SYNC` (Déploiement & Synchronisation)
* Synchronisation Jira Cloud, publication Git et archivage mémoire.

---

## 3. Règle d'Injonction Comportementale pour les Agents

* **Interdiction de Saut de Phase** : Un agent opérant dans un projet sous statut `T-SHIRT-SIZE` ou `SOW` (Phase 0 / Phase 1) a l'interdiction formelle de rédiger des récits détaillés sous `backlog/stories/` ou du code avant le passage franchi de la Porte 1 (`SOW`). Le découpage associé à la demande de SOW doit résider exclusivement au niveau macroscopique dans `backlog/sprint_backlog.md` et dans la Section 4 du SOW.
* **Traçabilité du Statut** : L'en-tête de `backlog/sprint_backlog.md` doit obligatoirement déclarer la phase active du projet.

---

## 4. Conséquences

### Positives
* **Zéro Travail Perdu** : L'effort d'ingénierie détaillée n'est engagé que sur des projets contractuellement validés par SOW.
* **Alignement Parfait Vente - Architecture - Delivery** : Le client et l'équipe partagent exactement le même niveau d'attente à chaque jalon.
* **Intégrité Multi-Agents** : Tous les agents (OpenCode, Cursor, Orchestrateur mLoop) respectent les mêmes limites de phase.

---

## 5. Références

* **Protocole SSOT** : [`standards/protocols/PROJECT_LIFECYCLE_STAGES.md`](file:///C:/Memory%20Loop/standards/protocols/PROJECT_LIFECYCLE_STAGES.md)
* **Grille Client** : [`docs/02-business-rules/RM-000_grille_tshirt_sizing_metro.md`](file:///C:/Memory%20Loop/Projects/Metro_Sante_AccesDossier/docs/02-business-rules/RM-000_grille_tshirt_sizing_metro.md)
* **ADR Associés** :
  - `ADR-0301` : 4 Piliers Gherkin et Titres Purs
  - `ADR-0307` : Archivage Systématique des Plans d'Implémentation
  - `ADR-0310` : Vibe Code Common Sense & Guardrails Pré-Vol
  - `ADR-0319` : Universal Dev Handoff & Boundary Code vs Architecture
