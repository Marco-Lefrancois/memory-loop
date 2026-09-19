# Gabarit Officiel d'Énoncé des Travaux (Statement of Work - SOW)

**Statut** : SSOT Normatif mLoop (ADR-0375)  
**Date d'effet** : Septembre 2026  
**Domaine** : Statement of Work (SOW), Périmètre Contractuel, Jalons de Livraison, Gouvernance & Loi 25  

---

<!-- 
INSTRUCTIONS DE RÉDACTION POUR L'AGENT (ADR-0375) :
1. Le SOW formalise l'ENGAGEMENT CONTRACTUEL et le PÉRIMÈTRE JURIDIQUE/MÉTIER.
2. Le dimensionnement macroscopique détaillé est géré séparément dans docs/01-architecture/TSHIRT_SIZE_<PROJET>.md.
3. Remplacer les placeholders [ENTRE_CROCHETS] par les données réelles du mandat.
4. Conserver obligatoirement la section 5 (Conformité Légale & Loi 25) et la section 7 (Signatures).
-->

# [TITRE DU PROJET] — Énoncé des Travaux (SOW)

**Client** : [Nom du Client / Organisation]  
**Partenaire Technologique** : Nmédia Solutions Inc.  
**Projet** : [Nom Officiel du Projet]  
**Date d'Émission** : [Date de Rédaction] | **Version** : 1.0  
**Enveloppe Retenue** : **[T-SHIRT_SIZE]** ([N] jours / [N] h / [N] $ CAD) — *Réf. [TSHIRT_SIZE_[PROJET].md](TSHIRT_SIZE_[PROJET].md)*  
**Dépôt de Référence** : [[Nom_Depot](https://dev.azure.com/...)]  

---

## 1. Contexte d'Affaires & Objectifs Stratégiques

[Décrire en 1 à 2 paragraphes synthétiques la raison d'être du projet, le problème utilisateur résolu, la valeur ajoutée pour le client et la finalité d'affaires].

---

## 2. Portée Contractuelle & Livrables Officiels

### 2.1 Périmètre Inclus (In-Scope)
* **Lot 1 : [Nom du Lot ou Domaine 1]**
  - [Livrable / Fonctionnalité contractuelle 1.1]
  - [Livrable / Fonctionnalité contractuelle 1.2]
* **Lot 2 : [Nom du Lot ou Domaine 2]**
  - [Livrable / Fonctionnalité contractuelle 2.1]
  - [Livrable / Fonctionnalité contractuelle 2.2]
* **Lot Transverse : Architecture, CI/CD & Documentation**
  - Architecture décision-complete (ADR) et schémas d'intégration.
  - Spécifications des interfaces et contrats d'API.

### 2.2 Exclusions Fermes (Out-of-Scope)
> *Tout élément non expressément stipulé dans la section 2.1 est considéré hors périmètre.*
- ❌ **[EXCL-01]** : [Exclusion explicite 1].
- ❌ **[EXCL-02]** : [Exclusion explicite 2].
- ❌ **[EXCL-03]** : [Exclusion explicite 3].

---

## 3. Jalons de Livraison & Calendrier Cible

| Jalon | Intitulé du Jalon | Livrables Attendus | Date Cible / Sprint |
| :---: | :--- | :--- | :---: |
| **M1** | Cadrage & Architecture Validée | Dossier d'architecture (ADR), Backlog DRAFT initialisé | Sprint 0 |
| **M2** | Premier Incrément Fonctionnel | Stories Lot 1 livrées en environnement de staging | Sprint 2 |
| **M3** | Feature Complete & Recette QA | 100% des stories livrées, audits Sentinel verts | Sprint 4 |
| **M4** | Mise en Production & Clôture | Déploiement production, synchro Jira scellée, handoff | Sprint 5 |

---

## 4. Matrice de Responsabilités (RACI)

| Activité / Domaine | Client | Nmédia (mLoop) | Tiers / Fournisseurs |
| :--- | :---: | :---: | :---: |
| Arbitrage fonctionnel & Approbation des User Stories (DoR) | **A / R** | C | I |
| Rédaction des User Stories & Spécifications Gherkin | C | **A / R** | I |
| Fourniture des accès, environnements et APIs tierces | **A / R** | C | C |
| Développement logiciel, tests unitaires et intégration | I | **A / R** | I |
| Recette utilisateur finale (UAT) | **A / R** | C | I |
| Autorisation de déploiement en production | **A** | R | I |

*Légende : R = Réalise (Responsible), A = Approuve (Accountable), C = Consulté (Consulted), I = Informé (Informed).*

---

## 5. Conformité Légale, Loi 25 & Protection des Renseignements Personnels

1. **Gouvernance des Données (Loi 25 - Québec)** :  
   Les parties s'engagent à respecter les dispositions de la Loi 25 sur la protection des renseignements personnels dans le secteur privé. Aucun renseignement personnel direct (PII) ne doit être stocké en clair sans chiffrement conforme aux standards de l'industrie.
2. **Confidentialité & Propriété Intellectuelle** :  
   L'ensemble des livrables logiciels, configurations et documentations produits dans le cadre de ce mandat deviennent la propriété exclusive du Client dès acquittement des factures afférentes.

---

## 6. Budget, Tarification & Conditions de Facturation

- **Type d'Engagement** : [Forfaitaire / Régie Plafonnée / Agile aux Sprints]
- **Enveloppe Globale Prévue** : **[TOTAL_BUDGET] $ CAD** (hors taxes)
- **Modalités de Facturation** :
  - Facturation mensuelle à l'avancement basée sur les jalons M1 à M4 validés.
  - Tout changement de périmètre fera l'objet d'un avenant formalisé (*Change Request*) chiffré selon la grille T-Shirt mLoop.

---

## 7. Approbation & Signatures Formelles

En signant le présent Énoncé des Travaux, les parties confirment leur accord mutuel sur les objectifs, la portée, les jalons, les responsabilités et les conditions budgétaires décrits ci-dessus.

| Pour le Client : [Nom du Client] | Pour Nmédia Solutions Inc. |
| :--- | :--- |
| **Nom** : ___________________________ | **Nom** : ___________________________ |
| **Titre** : ___________________________ | **Titre** : ___________________________ |
| **Date** : ___________________________ | **Date** : ___________________________ |
| **Signature** : _______________________ | **Signature** : _______________________ |
