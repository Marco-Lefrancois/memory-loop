---
id: REC-XXX
jira_key: PROJECT-XXX
epic_key: EPIC-XXX
type: Feature
title: Titre Fonctionnel Pur du Récit
tags: [core, ui, api]
status: IN_ANALYZE
layer: fullstack            # frontend | backend | fullstack (ADR-0366)
invest_score: 6/6           # Auto-audité par WikiFix / Sentinel
macrostructure: "workbench" # Optionnel FE/Fullstack : bento-grid | workbench | stat-led (ADR-0340)
---
# Titre Fonctionnel Pur du Récit

---

## Description
**En tant qu'** [Persona ou Rôle métier],  
**je veux** [effectuer une action fonctionnelle précise],  
**afin de** [bénéficier d'une valeur métier concrète et mesurable].

---

## Contexte & Périmètre

### Contexte Métier
[Description concise en langage naturel de la place du besoin dans le parcours global. Règle Zero-Bruit & No-Code : Exprimer le besoin en langage d'affaires pur. Interdiction absolue d'inclure des noms physiques de tables de données, de colonnes, des prédicats techniques (ex: IS NULL, = true), des mentions de traçabilité, ou des références à des réunions/ateliers.]

### In-Scope
- [Périmètre fonctionnel inclus dans ce récit : ce que la story accomplit de bout en bout]
- [Comportements et entités manipulées couverts par ce développement]

### Out-of-Scope
- [Exclusions explicites pour éliminer tout glissement de périmètre (Scope Creep)]
- [Actions, cas limites ou fonctionnalités différées. Règle anti-couplage : Décrire la frontière fonctionnelle en langage pur sans citer de clés de tickets internes (ex: proscrire les mentions du type « couvert par REC-002 »)]

---

## Critères d'acceptation

> **Règle conditionnelle par `layer` (ADR-0366)** :
> - **`layer: frontend`** : Renseigner les Spécifications de l'Interface & UX, Maquettes SSOT et Parcours Interactif.
> - **`layer: backend`** : Renseigner les Opérations Métier & Logique Backend (avec les 5 sous-titres normés) et Contrats d'échange API.
> - **`layer: fullstack`** : Renseigner l'ensemble des sections avec symétrie stricte UI/API (ADR-0319).

### Spécifications de l'Interface & UX *(frontend / fullstack)*
- **Macrostructure & États de surface** : L'écran respecte les 4 états de surface : Initial/Vide, Chargement, Erreur et Succès.
- **États d'Interaction (signifiants)** : [Comportement des composants sur les états d'interaction signifiants : Default, Hover, Focus-Visible, Active, Disabled, Loading, Error, Success. Omettre les états natifs sans règle métier].
- **Feedback Utilisateur** : [Indicateurs visuels clairs : toasts contextuels, modales, bannières informatives ou désactivation préventive des boutons pendant les requêtes].

### Opérations Métier & Logique Backend *(backend / fullstack)*
#### 1. [Nom de l'Opération ou Service Métier]
* **Entrée Métier** : [Paramètres métier d'entrée, filtres, identifiants d'entité ciblée, motif managérial]
* **Règles d'admissibilité & Validation** : [Conditions métier d'acceptation, vérification de statut, conformité des plages]
* **Traitement & Algorithme Métier** : [Logique d'exécution, mutations d'état, calculs déterministes, atomicité transactionnelle tout-ou-rien]
* **Résultat Métier & Mutations** : [Structure des données produites, réconciliation de stock/inventaire, indicateurs calculés]
* **Cas de Rejet Métier** : [Conditions de rejet exprimées en langage d'affaires pur, sans codes de transport HTTP]

### Maquettes SSOT *(frontend / fullstack)*
- 🔗 **Maquette Validée (SSOT)** : [Nom de l'écran Figma](https://figma.com/file/...) *(ou N/A - Composant Headless)*
- 📂 **Actif Local Ingéré** : [`docs/05-assets/maquettes/ecran_principal.svg`](../../docs/05-assets/maquettes/ecran_principal.svg)
- 📌 **Ajustements Visuels Validés** : [Résumé des ajustements de cadrage issus des revues UI, sans contradiction des maquettes SSOT].

---

## Parcours Interactif & API

### Parcours Interactif (Frontend / Déclencheurs UI)
> *Cartographie exhaustive des composants interactifs de l'écran et de leurs transitions d'état.*

| Élément UI | Déclencheur | Action Déclarative (Navigation / API) | Feedback & Changement d'État |
| :--- | :--- | :--- | :--- |
| `[Bouton Soumettre]` | Clic / Tap | Appel `POST /api/v1/ressource` | Bouton désactivé + spinner, puis toast de confirmation |
| `[Lien Annuler]` | Clic / Tap | Navigation vers l'écran d'accueil | Réinitialisation des saisies et redirection |

### Contrats d'Échange API (Backend / Services)
> *Définition déclarative des contrats réseau. Règle anti-invention : interdiction d'inventer des routes non documentées.*

- **[Nom de l'Opération 1]** : `GET /api/v1/ressource`
- **[Nom de l'Opération 2]** : `POST /api/v1/ressource`

> 📄 **Spécifications formelles détaillées** : Consulter les schémas JSON exhaustifs et routes OpenAPI dans [`specs/api.md`](../../backlog/handoff/<STORY_ID>/specs/api.md) *(ou portail Git distant : `https://<DOMAINE_GIT>/<PROJET>/_git/<REPO>?path=/backlog/handoff/<STORY_ID>/specs/api.md`)*.

---

## Règles d'affaires

- **[Nom de la Règle Métier Pure]** : [Formulation explicite de la contrainte, du calcul, du seuil ou de la condition d'éligibilité métier. Règle absolue : proscrire tout préfixe artificiel du type RM-XXX ou RG-XXX (ADR-0301 Rule #7 / Directive #11)].
- **[Gestion des Données Invalides]** : [Comportement attendu et rejet en cas de dépassement de quota, doublon ou format non conforme].

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/<STORY_ID>_fact_dossier.md`](../../memory/evidence/<STORY_ID>_fact_dossier.md) *(Portail Git distant : `https://<DOMAINE_GIT>/<PROJET>/_git/<REPO>?path=/memory/evidence/<STORY_ID>_fact_dossier.md`)*

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Modèle de Données SSOT** : [Structure-de-données](../../reference/modeles/<FICHIER_MODELE>.md) *(Wiki distant : `https://<WIKI_URL>/...`)*
- 📋 **Cas d'Utilisation Métier** : [Cas XX — Titre](../../docs/00-ingested/<CAS_UTILISATION>.md)
- 📜 **ADR d'Architecture** : [ADR-XXXX — Titre Architecture](../../standards/adr-system/<ADR_ID>-<SLUG>.md)

### 3. Paquet OpenSpec (Handoff Développeur)
- 📄 **Proposition Technique (proposal.md)** : [`backlog/handoff/<STORY_ID>/proposal.md`](../../backlog/handoff/<STORY_ID>/proposal.md) *(Portail Git distant : `https://<DOMAINE_GIT>/<PROJET>/_git/<REPO>?path=/backlog/handoff/<STORY_ID>/proposal.md`)*
- 📋 **Spécifications d'Échange (specs/api.md)** : [`backlog/handoff/<STORY_ID>/specs/api.md`](../../backlog/handoff/<STORY_ID>/specs/api.md) *(Portail Git distant : `https://<DOMAINE_GIT>/<PROJET>/_git/<REPO>?path=/backlog/handoff/<STORY_ID>/specs/api.md`)*
- 🎯 **Plan de Découpage TDD (tasks.md)** : [`backlog/handoff/<STORY_ID>/tasks.md`](../../backlog/handoff/<STORY_ID>/tasks.md) *(Portail Git distant : `https://<DOMAINE_GIT>/<PROJET>/_git/<REPO>?path=/backlog/handoff/<STORY_ID>/tasks.md`)*
- ✅ **Definition of Done** : [DoD Normative](../../reference/definition-of-done.md) *(Portail Git distant : `https://<DOMAINE_GIT>/<PROJET>/_git/<REPO>?path=/reference/definition-of-done.md`)*

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Titre Fonctionnel Pur du Récit

  # CHEMIN NOMINAL (Happy Path & Persistance)
  Scénario: Exécution nominale avec persistance des données
    Étant donné un utilisateur authentifié disposant des droits requis
    Et que les paramètres du formulaire sont valides et complets
    Quand l'utilisateur confirme la soumission
    Alors le statut de l'entité passe à "Confirmé"
    Et un message de succès s'affiche
    Et les données sont persistées dans le système

  # EXCEPTIONS & REJETS MÉTIER (Règles d'affaires)
  Scénario: Rejet pour non-respect de la règle d'éligibilité
    Étant donné un utilisateur initiant une soumission
    Mais que les paramètres enfreignent la règle d'éligibilité
    Quand l'utilisateur tente de valider l'action
    Alors la soumission est bloquée avec un message d'erreur explicite
    Et le système n'enregistre aucune modification
    Et le champ en faute est mis en évidence visuelle

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Timeouts, Idempotence, Concurrence)
  Scénario: Rupture réseau ou indisponibilité du service de traitement
    Étant donné une requête de validation transmise au serveur
    Mais que le service distant subit un timeout ou une coupure réseau
    Quand la temporisation maximale est atteinte
    Alors l'action est interrompue sans altérer l'état local
    Et l'utilisateur est invité à réessayer ultérieurement
    Et un jeton d'idempotence prévient tout double traitement lors du rejeu

  # UX, OBSERVABILITÉ & EMPTY STATE (Spinners, Retours Écran, Logs)
  Scénario: Indicateurs de progression, désactivation temporaire et état vide
    Étant donné le déclenchement d'un traitement asynchrone ou l'absence de données
    Quand l'opération est en cours d'exécution
    Alors le bouton de confirmation affiche un indicateur de chargement et devient inactif
    Et l'interface empêche toute navigation conflictuelle
    Et un journal d'audit trace l'amorce de la transaction
```
