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

#### 3. Matrice des États d'Interaction & Résilience (8 États UI - ADR-0340)
* **[Default / Nominal State]** : [Comportement visuel au repos]
* **[Hover State]** : [Transition subtile au survol]
* **[Focus-Visible State]** : [Contour d'accessibilité clavier]
* **[Active State]** : [Rétroaction lors du clic/toucher]
* **[Disabled State]** : [Indicateur grisé ou inerte non bloquant]
* **[Loading / Processing State]** : [Spinner ou indicateur de progression pendant la soumission]
* **[Error State]** : [Message d'anomalie en ligne et mise en évidence]
* **[Success State]** : [Notification de confirmation ou redirection]

### Liste Call to Actions

| Élément UI | Trigger | Action (Navigation/API) | Feedback & État Final |
| :--- | :--- | :--- | :--- |
| **[Bouton/Lien]** | `onClick` | [Action] | [Feedback] |

---

## Règles d'affaires
* **[Titre Métier Pur]** : [Description de la règle]

---

## Maquettes
- 🔗 **Lien Figma** : [Nom de l'écran](https://figma.com/file/...)

---

## Contrats d'échange API

### Spécifications de l'Interface
- **Écran cible** : [Type d'app Power Apps]
- **Navigation Amont** : [Origine]
- **Navigation Aval** : [Destination]

### Contrats d'échange API
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

