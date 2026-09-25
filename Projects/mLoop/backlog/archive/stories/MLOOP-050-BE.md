---
id: MLOOP-050-BE
jira_key: '-'
epic_key: EPIC-6-OKF-ENCLAVE
type: Feature
title: Compilateur OKF et Usine de Compétences Typées
tags: [okf, skill-factory, sep-2640, parser]
status: SHIPPED
layer: backend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-6-OKF-ENCLAVE] Compilateur OKF et Usine de Compétences Typées (MLOOP-050-BE)

---

## Description
**En tant qu'** Agent Plan et Orchestrateur du framework mLoop,  
**je veux** disposer d'un compilateur automatisé convertissant la matière brute ingérée en artefacts Open Knowledge Format v0.1 avec extraction d'entités typées,  
**afin de** standardiser la connaissance et permettre son chargement sélectif via les URI de compétences `skill://`.

---

## Contexte & Périmètre

### Contexte Métier
L'ingestion documentaire produit du Markdown hétérogène. Pour éviter d'injecter des pavés documentaires entiers dans le prompt système des agents, le compilateur OKF segmente la documentation en compétences modulaires avec extraction d'entités (Personnes, Organisations, Produits) indexées sous le standard SEP-2640.

### In-Scope
- Moteur de parsing et validation de manifeste OKF v0.1.
- Extraction d'entités typées (*People, Organizations, Places, Products/Features*).
- Génération de paquets de compétences modulaires sous `.agents/skills/<nom>/SKILL.md`.
- Publication du catalogue d'accès pour serveur MCP (`skill://index.json`).

### Out-of-Scope
- Exécution de conteneurs sandboxed distants (confinement local).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Compilation et Validation de Manifeste OKF
* **Entrée Métier** : Fichier Markdown sous `docs/00-ingested/`.
* **Règles d'admissibilité & Validation** : Présence impérative des champs de métadonnées OKF v0.1 (`type`, `title`, `description`, `tags`).
* **Traitement & Algorithme Métier** : Vérification d'intégrité, normalisation des en-têtes et génération du fichier de compétence.
* **Résultat Métier & Mutations** : Création du descripteur `.agents/skills/<skill>/SKILL.md`.
* **Cas de Rejet Métier** : Rejet explicite avec code d'erreur `ERR_OKF_INVALID_MANIFEST` si la structure est incomplète.

---

## Règles d'affaires

- **[Validation Frontmatter OKF]** : Tout document transformé par la Skill Factory doit comporter un bloc frontmatter valide et complet.
- **[Catégorisation d'Entités Typées]** : L'extraction d'entités classe au minimum 4 catégories d'entités sans inventer de métadonnées.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Compilation OKF et Usine de Compétences Typées

  # CHEMIN NOMINAL
  Scénario: Compilation nominale d'un document en compétence modulaire
    Étant donné un document Markdown ingéré valide sous docs/00-ingested/
    Quand le compilateur OKF est invoqué sur le projet
    Alors le fichier est certifié conforme au format OKF
    Et un package de compétence est créé sous .agents/skills/
    Et le catalogue skill://index.json est synchronisé

  # EXCEPTIONS & REJETS MÉTIER
  Scénario: Rejet d'un document au frontmatter incomplet
    Étant donné un fichier Markdown dépourvu du champ obligatoire type
    Quand la compilation OKF est lancée
    Alors le traitement est stoppé avec le rejet ERR_OKF_INVALID_MANIFEST
    Et le catalogue officiel n'est pas corrompu

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ
  Scénario: Traitement idempotent lors de compilations successives
    Étant donné une compétence déjà compilée et non modifiée sur disque
    Quand une nouvelle passe de compilation est demandée
    Alors le compilateur compare l'empreinte SHA-256 et saute la regénération

  # UX, OBSERVABILITÉ & EMPTY STATE
  Scénario: Journalisation de l'économie de tokens obtenue
    Étant donné la résolution d'une compétence via skill://
    Quand la compétence est chargée dans la session
    Alors un journal d'audit trace l'économie d'empreinte obtenue face au document brut
```
