# Plan d'implémentation — Clarifier et outiller les récits Frontend / Backend mLoop

*Statut*: **Approuvé**
*Date*: 20 août 2026
*Auteur*: mLoop Sentinel

Ce document consigne la stratégie approuvée pour séparer formellement les exigences documentaires et de validation (linters) entre les profils Frontend et Backend.

---

## 1. Principes de gouvernance (Rappel)

- Le **gabarit unique** est conservé mais rendu conditionnel au champ frontmatter `layer` (`frontend`, `backend`, `fullstack`).
- Un récit Backend ne doit **plus contenir de composants UI** (CTA, toasts, spinners).
- L'audit `rubber-duck` et les outils Gherkin doivent **adapter leurs contrôles** à ce champ `layer`.
- L'isolation technique **ADR-0319 s'applique à tous** (zéro code, pureté déclarative).

---

## 2. Modifications documentaires (Déjà réalisées)

Les modifications suivantes ont été rédigées dans le cadre de ce mode Planning :

1. `standards/blueprints/story_template.md` : ajout de la section `Opérations API & Logique Backend (Profil Backend)` et conditionnement de la section `Interface et UX` (Profil UI).
2. `standards/GHERKIN_GUIDELINES.md` : redéfinition du Pilier 4 en `Comportement UX & Observabilité (UX pour FE, Traces pour BE)`.

---

## 3. Travaux requis sur le Framework (À exécuter lors d'une session Build)

L'équipe mLoop (agent de Build) devra implémenter la logique suivante dans le code source du linter (`src/pipelines/rubber_duck.py` ou module équivalent responsable de la validation QA) :

### A. Détection du profil
- Analyser l'en-tête YAML pour extraire la propriété `layer` (valeurs tolérées : `frontend`, `backend`, `fullstack`, ou absent).
- Si `layer` est absent, produire un avertissement non bloquant recommandant la migration.

### B. Règles conditionnelles

**Si `layer == 'frontend'` ou `layer == 'fullstack'` ou `layer` absent :**
- Maintenir l'exigence `BLOCKING` : "Matrice Call to Actions (CTA) manquante".
- Maintenir l'exigence `WARNING` : "Contrôles UI décrits de manière générique sans typage explicite".

**Si `layer == 'backend'` :**
- Désactiver l'exigence de la matrice CTA.
- Désactiver l'avertissement sur le typage explicite des contrôles UI.
- Ajouter une exigence `BLOCKING` : "Matrice des Opérations Backend manquante" (vérifier la présence de "Opérations API & Logique Backend" ou "Matrice des opérations API").

### C. Préservation de la sécurité
- Tous les récits continuent d'être soumis au linter ADR-0319 (détection de pseudo-code `==`, etc.).
- Tous les récits doivent comporter les 4 scénarios Gherkin.

---

## 4. Stratégie de Migration

- Les récits existants (legacy) sans champ `layer` ne seront pas modifiés en masse par un script aveugle.
- Le linter `wikifix`/`rubber-duck` émettra un avertissement les invitant à spécifier leur profil.
- La migration se fera *story par story* lors de leur prochaine phase `IN_ANALYZE`.

*(Fin du plan)*