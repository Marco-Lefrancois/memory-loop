# Plan d'implémentation — Règle globale de traçabilité des routes API connues

*Statut*: **Approuvé**
*Date*: 20 août 2026

## 1. Objectif
Formaliser dans le framework mLoop l’obligation de documenter les routes API connues et confirmées dans les récits. Les contrats déclaratifs (routes, paramètres, méthodes HTTP) font partie de l'isolation ADR-0319 et garantissent la symétrie FE ↔ BE sans pour autant polluer le récit avec du code.

## 2. AGENTS.md et story_template.md
- **Règle** : Lorsqu’une méthode HTTP et une route sont connues et confirmées par le modèle ou les ADRs, tout récit `layer: backend` ou `layer: fullstack` DOIT les documenter dans la section `## Contrats UI & API Backend`.
- **Symétrie** : Tout récit `layer: frontend` qui consomme cette action DOIT référencer la même méthode/route connue dans sa Matrice CTA.
- **Anti-Hallucination** : Si la route n'est pas encore confirmée (contrat ouvert), il est STRICTEMENT INTERDIT d'inventer une route (ex. `/api/dummy`). Le récit doit consigner ce manque sous forme de question ouverte (`OQ-XXX`) et utiliser une description déclarative (ex. `[API de soumission à définir]`).

## 3. Mise à jour des Skills
- Modifier `.agents/skills/plan/SKILL.md` :
  - Renforcer le *cross-check FE/BE* lors du découpage vertical : les routes connues doivent correspondre exactement. Une absence non documentée est un écart de symétrie.
- Modifier `.agents/skills/sentinel/SKILL.md` et `.agents/skills/rubber-duck/SKILL.md` (Agent d'audit) :
  - L'audit contradictoire doit signaler (WARNING/BLOCKING) toute route identifiée dans un FE mais absente du BE homologue (ou inversement).
  - Ne déclencher l'alerte de contrat manquant QUE si l'absence n'est pas justifiée par une question ouverte ou une mention de contrat à définir.

## 4. Livrables de l'équipe de Build
1. Mise à jour de `AGENTS.md` (Projets clients et framework).
2. Mise à jour de `standards/blueprints/story_template.md`.
3. Mise à jour des skills `plan`, `sentinel` et `rubber-duck`.
4. Mise à jour des règles du linter `rubber_duck.py` pour valider la présence de la matrice des contrats (Méthode, Route, Finalité) dans les récits BE/Fullstack.

## 5. Stratégie de déploiement
Aucune modification rétroactive des récits clients (legacy) n'est requise. Les récits seront corrigés individuellement lors de leur prochaine phase d'analyse ciblée.