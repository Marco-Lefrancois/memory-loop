---
id: REC-XXX
jira_key: PROJECT-XXX
epic_key: EPIC-XXX
type: Feature
title: Titre de la Story
tags: [power-apps, canvas-app, ui, api, core]
status: IN_ANALYZE
layer: frontend
macrostructure: ""         # Optionnel (FE/Fullstack). Ex: "bento-grid", "workbench", "stat-led" (ADR-0340)
gold_standard_ref: ""      # Optionnel. Ex: "REC-015-FE.md" — référence stylistique du projet pour struct-check
---
# Titre de la Story

## Description
**En tant qu'** [Utilisateur final / Rôle métier],  
**je veux** [Action dans l'interface ou intégration],  
**afin de** [Valeur métier ou objectif utilisateur].

---

## Contexte
[Expliquer le contexte métier de manière concise pour les développeurs. Règle Zero-Bruit : Interdiction absolue d'inclure des mentions de traçabilité, noms de personnes, ou références à des réunions/ateliers.]

---

## Critères d'acceptation

### Spécifications de l'Interface

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

### Liste Call to Actions

| Élément UI | Trigger | Action (Navigation/API) | Feedback & État Final |
| :--- | :--- | :--- | :--- |
| **[Bouton/Lien]** | `onClick` | [Action] | [Feedback] |

---

## Règles d'affaires
* **[Titre Métier Pur]** : [Description de la règle]

> **Note** : Le titre est le nom métier de la règle uniquement (ex : « Saisie Limitée »). Zéro numérotation type `Règle-01`/`RG-01` imposée par le SSOT — un identifiant technique n'apporte aucune valeur au dev et introduit du bruit rédactionnel.

---

## Maquettes
- 🔗 **Lien Figma** : [Nom de l'écran](https://figma.com/file/...)

---

## Navigation / Contrats d'échange API
> **Règle conditionnelle par `layer`** :
> - **`layer: frontend`** : le contrat d'échange officiel EST la **Matrice CTA** (section précédente). Cette section se limite alors à `## Navigation` (écran cible, navigation amont/aval). Si l'écran consomme réellement des routes backend, les lister en version allégée (méthode + chemin, sans payload) ; ne jamais inclure une sous-section « Contrats d'échange API » vide ou renvoyant uniquement vers « à définir ».
> - **`layer: backend` / `layer: fullstack`** : documenter le contrat complet ci-dessous (Profil A/B, payload, idempotence).

### Navigation
- **Écran cible** : [Type d'app Power Apps]
- **Navigation Amont** : [Origine]
- **Navigation Aval** : [Destination]

### Contrats d'échange API *(backend/fullstack uniquement, ou FE avec routes réelles consommées)*
- **[Nom Opération]** : `[METHODE] /api/...`
```json
{
  "request": {
    "champ": "valeur"
  }
}
```
> Note : [Précisions sur l'idempotence/Auth/Log]

---

## Références
- 📂 **Dossier de Preuves & Cadrage SSOT** : [<STORY_ID>_fact_dossier.md](../../memory/evidence/<STORY_ID>_fact_dossier.md)
- [Nom Référence Métier / Wiki] : [Lien HTTPS Officiel](https://...)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: [Nom métier pur de la fonctionnalité]

  Scénario: [Titre explicite]
    Étant donné [Pré-conditions]
    Quand [Action utilisateur]
    Alors [Résultat attendu]
```
```

---

