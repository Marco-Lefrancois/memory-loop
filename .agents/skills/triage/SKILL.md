---
name: triage
description: Triage du backlog et découpage en récits verticaux actionnables au gabarit story_template.md. Use when prioritizing backlog items, triaging incoming feature requests, or splitting messy user stories.
---

# 🧹 Skill `/triage` (Triage du Backlog & Vertical Slicing)

> **Standard :** mLoop Triage & Story Slicing Protocol  

## 🧠 Description
Le skill `/triage` prend en entrée un ensemble d'exigences floues, un document de spécification brute ou des notes de réunions, et les transforme en un ensemble structuré de **Stories verticales indépendantes** conformes au gabarit officiel `standards/blueprints/story_template.md`.

## ⚡ Exécution
1. **Inspection Documentaire** : Inspecter le fichier d'entrée sous `docs/00-ingested/` ou `reference/`.
2. **Typage de Complexité Cynefin (`thinking-cynefin` / ADR-0336)** :
   - Si la fonctionnalité relève du domaine *Simple* ou *Complicated* ➔ Poursuivre le découpage vertical standard.
   - Si la fonctionnalité relève du domaine *Complex* (inconnues techniques majeures, comportement émergent non documenté) ➔ Créer obligatoirement un Spike d'expérimentation préalable `US-SPIKE-XXX.md` (ADR-0306) en Priorité #1 avant de figer la story verticale.
3. **Vérification d'Étanchéité Backlog** : Consulter `backlog/STORY_MAPPING.md` et `backlog/sprint_backlog.md` pour éviter les doublons avec les récits existants.
4. **Découpage Vertical Pur (Vertical Slicing) & Macrostructures UI (ADR-0340)** :
   - Découper chaque épopée en récits verticaux minces (UI + API Backend + Modèle de données), centrés sur la valeur métier et l'expérience utilisateur, en laissant le découpage technique de bas niveau à l'équipe de dev aval.
   - Pour chaque récit `layer: frontend` ou `layer: fullstack`, sélectionner une **macrostructure UI dédiée** parmi les 21 formes du catalogue ([`standards/blueprints/ui_macrostructures.md`](file:///c:/Memory%20Loop/standards/blueprints/ui_macrostructures.md)) et appliquer la **règle de diversification** (zéro répétition de structure entre écrans consécutifs).
5. **Régulation par la Théorie des Contraintes (`thinking-theory-of-constraints` / ADR-0336)** : Identifier les dépendances bloquantes dans le DAG et ordonnancer les récits pour alimenter le goulet d'étranglement sans engorger l'encours (*WIP*).
6. **Rédaction Standardisée** : Rédiger chaque récit sous `backlog/stories/<ID>.md` avec les 4 piliers Gherkin (Nominal, Exceptions, Résilience, UX), la matrice CTA, la matrice des 8 états d'interaction pour les composants, les contrats déclaratifs et les références documentaires SDK (ADR-0319, Zéro Snippet de Code).
7. **Génération EvidencePack** : Invoquer `EvidencePackEngine` pour générer automatiquement `memory/evidence/<STORY_ID>_evidence.json` avec empreintes SHA-256 et diptyque épistémique.
8. **Enregistrement Backlog** : Enregistrer les récits dans `backlog/sprint_backlog.md`.
