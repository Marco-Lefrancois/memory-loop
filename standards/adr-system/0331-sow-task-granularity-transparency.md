# ADR-0331 : Granularité des Tâches SOW & Transparence

**Statut** : ACCEPTÉ  
**Date d'effet** : 18 août 2026  
**Auteurs** : Équipe d'Architecture mLoop & Direction Produit  
**Domaine** : Statement of Work (SOW), Cadrage Macro, Matrice d'Effort Multi-Disciplinaire, Grille Kevin Chamberland  

---

## 1. Contexte & Problématique

Lors de la Phase 1 du cycle de vie projet (`STAGE_SOW` - ADR-0329), la génération d'Énoncés des Travaux (SOW) et d'évaluations budgétaires macro (T-Shirt Sizing) pouvait occasionnellement générer des tableaux de chiffrage contenant des libellés trop génériques (ex: *« Modules Fonctionnels Principaux »*, *« Codebase 1 »*) ou des descriptions sommaires ne reflétant pas la complexité réelle des fonctionnalités.

Cette opacité présentait deux risques majeurs :
1. **Friction Commerciale & Défiance Client** : Difficulté pour le porteur de projet ou le client (ex: Leadco / Metro) de comprendre la justification précise d'une enveloppe de développement de 75 SP (600 heures).
2. **Ambiguïté pour l'Équipe Dev Aval** : Manque de directives sur les briques d'infrastructure critiques (ex: intégration Stripe, cache hors-ligne, mécanismes anti-fraude, gestion des formats).

---

## 2. Décisions d'Architecture & Règles Normatives

### 2.1 Format Épuré en 5 Sections Obligatoires
Tout SOW généré dans l'écosystème mLoop se conforme obligatoirement à la structure épurée en 5 sections validée au standard SSOT :
1. **Objectif Principal** *(Contexte d'Affaires & Bénéfices Attendus)*
2. **Portée du Projet (*Scope*)** *(Fonctionnalités Incluses par Composant + Exclusions Explicites)*
3. **Hypothèses du Projet** *(Déduites mathématiquement des exclusions et contraintes)*
4. **Découpage des Récits Macro** *(Tableau INVEST des User Stories)*
5. **Évaluation Budgétaire** *(Tableau de Chiffrage Détaillé par Tâche & Réconciliation Mathématique)*

---

### 2.2 Règle d'Or de Granularité des Tâches de Développement (Section 3)
Dans le tableau de chiffrage détaillé (Section 5 du SOW), la discipline **3. Développement Logiciel** (tâches `3.1` à `3.N`) est soumise aux règles de rédaction strictes suivantes :

1. ✅ **Exhaustivité Fonctionnelle Obligatoire** : Chaque sous-tâche de développement DOIT obligatoirement énumérer de façon concise les fonctionnalités et composants concrets qui y sont développés (écrans, flux, protocoles, stockage, sécurité).
2. ✅ **Traçabilité des Angles Morts Techniques** : Toute adaptation technique issue de l'analyse d'angles morts (ex: *import direct `.ics`*, *cache local Offline-First*, *modal de validation anti-screenshot*, *passerelle Stripe Checkout*, *gestion des rôles de comités*) doit être explicitement mentionnée dans la colonne commentaires avec son allocation d'effort (*ex: `+2 SP inclus`*).
3. ❌ **Interdiction Formelle des Libellés Génériques** : Les mentions vagues telles que *« [Détail des récits] »*, *« Composant générique »* ou *« Développement divers »* sont formellement proscrites et rejetées par les linters de conformité.

---

## 3. Exemple de Conformité (Gold Standard)

```markdown
| # | Discipline & Tâche | SP | Heures | Commentaires & Hypothèses de Calcul (Fonctionnalités Incluses) |
| :---: | :--- | :---: | :---: | :--- |
| **3** | **Développement Logiciel (Mobile & Backend)** | **75 SP** | **600 h** | |
| 3.1 | Application Mobile : Profil, Authentification & Tâches | 12 SP | 96 h | Inscription sécurisée, onboarding déclaratif (choix établissement/programme), consentement natif (Loi 25), stockage local chiffré, gestionnaire de tâches et bloc-notes avec rappels. |
| 3.2 | Application Mobile : Calendrier & Synchronisation | 12 SP | 96 h | Connexion Google Calendar et Office 365 (Microsoft Graph), affichage des dates officielles, **support de l'import direct de fichiers `.ics` (Omnivox)** et **cache local déterministe *Offline-First* pour les sous-sols de campus** (+2 SP inclus). |
| 3.3 | Application Mobile : Modules Coupons & Recrutement | 14 SP | 112 h | Catalogue géolocalisé de coupons-rabais avec **écran de validation à compte à rebours dynamique de 2 min (sécurité anti-capture d'écran)** (+1 SP inclus), et tableau d'offres d'emploi/stages avec filtres par programme et suivi des clics (`job_click`). |
| 3.4 | Backend API & Moteur Régie Publicitaire IAB | 22 SP | 176 h | Serveur d'inventaire publicitaire IAB (bannières mobiles, CPM, formats fixes), endpoints de télémétrie certifiée (`ad_impression`, `ad_click`, `coupon_redeem`), file d'attente hors-ligne (`OfflineQueue`) et calcul automatisé de la ristourne de 15 % par campus. |
| 3.5 | Consoles Web Frontend (Associations & Annonceurs) | 15 SP | 120 h | • **Console Association** : diffusion push, dates clés, modération des publicités et **gestion des rôles de comités avec passation d'exécutif annuel** (+1 SP inclus).<br>• **Console Annonceur** : espace libre-service, rapports de métriques et **intégration Stripe Checkout pour le paiement automatisé des campagnes par carte de crédit** (+3 SP inclus). |
```

---

## 4. Conséquences & Bénéfices

* **Justification Incontestable de l'Investissement** : Le client perçoit immédiatement la rentabilité et le contenu exact de son enveloppe budgétaire (Taille `M`, `l`, etc.).
* **Continuité Parfaite avec les Stories de Phase 2** : Les spécifications fines de chaque User Story dans le backlog découlent directement des composants décrits dans le chiffrage SOW, sans risque de dérive de périmètre (*Scope Creep*).
* **Alignement Universel (Universal Dev Handoff - ADR-0319)** : Tout développeur humain ou assistant IA reçoit un contrat de développement limpide.

---

*Enregistré au registre d'architecture SSOT mLoop sous `docs/01-architecture/ADR-0331_sow_task_granularity_and_functional_transparency.md`.*
