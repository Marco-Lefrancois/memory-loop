---
id: REC-XXX
jira_key: PROJECT-XXX
epic_key: EPIC-XXX
type: Feature
title: Titre de la Story
tags: [power-apps, canvas-app, ui, api, core]
status: IN_ANALYZE
layer: frontend            # frontend | backend | fullstack
macrostructure: ""         # Optionnel (FE/Fullstack). Ex: "bento-grid", "workbench", "stat-led" (ADR-0340)
gold_standard_ref: ""      # Optionnel. Ex: "REC-015-FE.md" — référence stylistique du projet pour struct-check
---
# Titre de la Story

## Description
**En tant qu'** [Utilisateur final / Rôle métier / Service backend],  
**je veux** [Action dans l'interface ou endpoint exposé],  
**afin de** [Valeur métier ou objectif utilisateur].

---

## Contexte
[Expliquer le contexte métier de manière concise pour les développeurs. Règle Zero-Bruit : Interdiction absolue d'inclure des mentions de traçabilité, noms de personnes, ou références à des réunions/ateliers.]

---

## Critères d'acceptation

> **Règle conditionnelle par `layer` (ADR-0366)** :
> - **`layer: frontend`** : Renseigner les sections UI et Matrice CTA ci-dessous.
> - **`layer: backend`** : Renseigner les sections Opérations Métier & Logique Backend et Matrice des Réponses HTTP.

### Spécifications de l'Interface *(frontend / fullstack)*

#### 1. [Section UI 1]
* **[Élément]** : [Description]

#### 2. [Section UI 2]
* **[Élément]** : [Description]

#### 3. États d'Interaction (signifiants)
> **Règle de modulation (anti-remplissage)** : la profondeur de cette section s'adapte à la richesse réelle du composant. Ne documenter que les états qui portent une décision UX ou métier ; ne pas énumérer des états natifs génériques sans contenu spécifique.
> - **Composant riche** (formulaire multi-champs, liste alimentée par API, carte cliquable, wizard) : documenter la **Matrice complète des 8 États** (référence) : Default/Nominal, Hover, Focus-Visible, Active, Disabled, Loading/Processing, Error, Success.
> - **Composant simple / écran `minimal-spotlight`** (champ + bouton, saisie unique, action directe) : documenter uniquement les **états signifiants** (ex : champ vide → bouton désactivé ; saisie valide → bouton activé ; validation locale ; succès → transition). Omettre Hover/Active/Focus-Visible lorsqu'ils relèvent du comportement natif par défaut sans règle métier associée.

* **[État 1]** : [Comportement et condition de déclenchement]
* **[État 2]** : [Comportement et condition de déclenchement]
* **[État N]** : [Comportement et condition de déclenchement]

### Liste Call to Actions *(frontend / fullstack)*

| Élément UI | Trigger | Action (Navigation/API) | Feedback & État Final |
| :--- | :--- | :--- | :--- |
| **[Bouton/Lien]** | `onClick` | [Action] | [Feedback] |

### Opérations Métier & Logique Backend *(backend uniquement)*

#### 1. [Nom de l'Opération ou Service Métier]
* **Entrée Métier** : [Paramètres métier obligatoires / optionnels]
* **Règles d'admissibilité & Validation** : [Contrôles d'éligibilité, statuts autorisés, verrous de concurrence]
* **Traitement & Algorithme Métier** : [Calculs métier, tri déterministe, logique de priorité biologique/économique]
* **Résultat Métier & Mutations** : [Structure des données produites, indicateurs calculés et impacts d'inventaire]
* **Cas de Rejet Métier** : [Conditions de rejet exprimées en langage d'affaires pur, sans codes de transport HTTP]

---

## Règles d'affaires
* **[Titre Métier Pur]** : [Description de la règle]

> **Note** : Le titre est le nom métier de la règle uniquement (ex : « Saisie Limitée »). Zéro numérotation type `Règle-01`/`RG-01` imposée par le SSOT — un identifiant technique n'apporte aucune valeur au dev et introduit du bruit rédactionnel.

---

## Maquettes *(frontend uniquement)*
- 🔗 **Lien Figma** : [Nom de l'écran](https://figma.com/file/...)

---

## Navigation / Contrats d'échange API
> **Règle conditionnelle par `layer` (ADR-0366)** :
> - **`layer: frontend`** : le contrat d'échange officiel EST la **Matrice CTA** (section précédente). Cette section se limite alors à `## Navigation` (écran cible, navigation amont/aval). Si l'écran consomme réellement des routes backend, les lister en version allégée (méthode + chemin, sans payload).
> - **`layer: backend` / `layer: fullstack`** : déclarer les endpoints en puces simples sans snippets de code. Tout le détail des payloads et codes HTTP réside dans `specs/api.md`.

### Navigation
- **Écran cible** : [Type d'app Power Apps ou Frontend Web]
- **Navigation Amont** : [Origine]
- **Navigation Aval** : [Destination]

### Contrats d'échange API *(backend/fullstack uniquement, ou FE avec routes réelles consommées)*
- **[Nom Opération]** : `[METHODE] /api/...`

> 📄 **Contrats techniques détaillés** : Consulter les spécifications formelles OpenAPI et schémas JSON exhaustifs dans [specs/api.md](../../handoff/<STORY_ID>/specs/api.md).

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [Portail Web / Azure DevOps Git](https://...) | [Relatif](../../../memory/evidence/<STORY_ID>_fact_dossier.md)

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Modèle de Données SSOT** : [Structure-de-données.md (Portail Web)](https://...) | [Relatif](../../../reference/Structure-de-donn%C3%A9es.md)
- 📋 **Cas d'Utilisation Métier** : [Cas-XX — Titre (Wiki)](https://...)
- 📜 **ADR d'Architecture** : [ADR-XXX — Titre (Wiki)](https://...)

### 3. Paquet OpenSpec (Handoff Développeur)
- 📄 **Proposition Technique (proposal.md)** : [Portail Web / Azure DevOps Git](https://...) | [Relatif](../../handoff/<STORY_ID>/proposal.md)
- 📋 **Spécifications d'Échange (specs/api.md)** : [Portail Web / Azure DevOps Git](https://...) | [Relatif](../../handoff/<STORY_ID>/specs/api.md)
- 🎯 **Plan de Découpage TDD (tasks.md)** : [Portail Web / Azure DevOps Git](https://...) | [Relatif](../../handoff/<STORY_ID>/tasks.md)
- ✅ **Definition of Done** : [DoD Normative](https://...) | [Relatif](../../../reference/definition-of-done.md)


---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: [Nom métier pur de la fonctionnalité]

  # 1. Pilier Nominal (Happy Path)
  Scénario: [Titre explicite nominal]
    Étant donné [Pré-conditions valides]
    Quand [Action principale exécutée]
    Alors [Résultat nominal attendu]

  # 2. Pilier Exceptions & Règles Métier
  Scénario: [Titre explicite exception]
    Étant donné [Pré-conditions avec donnée non conforme ou exclue]
    Quand [Action déclenchée]
    Alors [Erreur ou rejet métier attendu]

  # 3. Pilier Résilience & Erreurs Techniques
  Scénario: [Titre explicite résilience]
    Étant donné [Défaillance de service ou timeout]
    Quand [Tentative d'appel]
    Alors [Comportement gracieux sans crash]

  # 4. Pilier UX / Empty State & État Limite
  Scénario: [Titre explicite cas limite ou résultat vide]
    Étant donné [Aucune donnée disponible correspondant aux critères]
    Quand [Consultation demandée]
    Alors [Retour d'une collection vide et indicateurs à zéro]
```
