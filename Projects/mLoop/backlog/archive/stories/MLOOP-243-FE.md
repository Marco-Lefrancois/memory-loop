---
id: MLOOP-243-FE
jira_key: ''
epic_key: EPIC-24-SKILLS-EVAL-HARNESS
type: Feature
title: "Matrice Visuelle & Radar de Santé des Compétences dans le Dashboard mLoop"
tags:
- skills
- dashboard
- frontend
- radar
- html-static
origin: SPEC_SLICING
source_ref: EPIC-24-§4.4
macro_size: M
status: SHIPPED
grill_me: DONE
invest_score: 6/6
validated_by: Marco (PO)
validated_at: '2026-09-24'
layer: frontend
blocked_by:
- MLOOP-241-BE
created_at: '2026-09-24'
updated_at: '2026-09-24'
ttl_cycles: 4
---

# 📖 MLOOP-243-FE : Matrice Visuelle & Radar de Santé des Compétences dans le Dashboard mLoop

## Description
**En tant que** Responsable de Plateforme mLoop,
**je veux** un nouvel onglet `/skills-health` dans le Dashboard mLoop affichant la matrice d'évaluation des 39 compétences (score global, 4 axes radar) sous forme de page HTML statique auto-contenue,
**afin d'** identifier en un coup d'œil les compétences fragiles, sous-utilisées ou sujettes au context rot, sans avoir à lire des rapports JSON bruts.

---

## Contexte & Périmètre

### Contexte Métier
Le Dashboard mLoop expose aujourd'hui des vues opérationnelles via handler CLI. Ce récit ajoute une vue dédiée à la santé des 39 skills, cohérente avec l'approche HTML statique auto-contenu validée dans MLOOP-212-FE (MCP Apps, zéro CDN externe).

**Décisions Grill (2026-09-24) :**
- **Nouvel onglet `/skills-health`** — le dashboard existant garde sa cohérence, la vue skills est isolée.
- **HTML statique auto-contenu** — zéro CDN, zéro dépendance réseau. Généré depuis `skills_eval_summary.json` et servi depuis `src/dashboard/skills_health.html`.
- **Lecture seule v1** — pas de bouton "Relancer l'évaluation" depuis l'interface. Le relancement reste CLI (`mloop skill-eval --all`).
- Seuils visuels : Vert ≥ 80, Orange 65–79, Rouge < 65 (alignés sur les seuils du moteur MLOOP-240-BE).

### In-Scope
- Fichier `src/dashboard/skills_health.html` auto-contenu (Chart.js embarqué inline ou via bundle local, zéro CDN).
- Génération du fichier depuis `scripts/generate_skills_dashboard.py` lisant `memory/evals/skills_eval_summary.json`.
- Vue tableau : 39 lignes, colonnes Skill / Score Global / Trigger Clarity / Rule Determinism / Ground Truth / Resilience / Verdict (PASS/WARN/FAIL).
- Vue radar : graphique radar des 4 axes pour la skill sélectionnée (clic sur ligne du tableau).
- Filtres : par verdict (PASS / WARNING / FAIL) et par score croissant/décroissant.
- Historique : affichage des 3 dernières évolutions de score depuis `memory/skill_impact.jsonl`.
- Chargement < 300 ms en local (données statiques, pas d'appel réseau).
- Handler CLI `src/commands/handlers/dashboard.py` étendu pour servir `/skills-health`.

### Out-of-Scope
- Bouton "Relancer l'évaluation" (CLI uniquement — v1 Read-Only).
- Édition des manifestes `SKILL.md` depuis l'interface.
- Déploiement cloud (localhost uniquement).
- Mise à jour temps-réel (page regénérée à chaque `mloop skill-eval --all`).

---

## Critères d'acceptation

### Spécifications de l'Interface & UX

- **Macrostructure & États de surface** :
  - **Initial/Vide** : Message explicite "Aucun rapport d'évaluation trouvé — lancez `mloop skill-eval --all`" avec lien CLI.
  - **Chargement** : Spinner inline pendant le rendu du tableau (< 300 ms, pratiquement invisible).
  - **Erreur** : Bandeau rouge si `skills_eval_summary.json` est corrompu ou absent.
  - **Succès** : Tableau complet des 39 skills avec radar interactif.

- **États d'interaction** :
  - Ligne de tableau : hover → surbrillance, clic → mise à jour du radar latéral.
  - Filtres : Default (aucun filtre), sélectionné → badge actif, reset → retour à la vue complète.
  - Verdict badges : PASS (vert), WARNING (orange), FAIL (rouge) avec états Default et Hover.

- **Feedback Utilisateur** :
  - Seuils visuels couleur : Vert ≥ 80, Orange 65–79, Rouge < 65.
  - Bandeau informatif si ≥ 1 skill FAIL : "X compétence(s) nécessitent une attention immédiate."
  - Colonne "Δ Score" affichant la tendance depuis le dernier run (↑ / ↓ / =).

### Maquettes SSOT
- 🔗 **Maquette Validée** : N/A — Dashboard HTML statique, pas de Figma.
- 📂 **Actif Local** : `src/dashboard/skills_health.html` (généré).
- 📌 **Ajustements** : Palette de couleurs alignée sur le Dashboard existant (noir/blanc/vert mLoop).

---

## Parcours Interactif & API

### Parcours Interactif

| Élément UI | Déclencheur | Action | Feedback |
| :--- | :--- | :--- | :--- |
| Ligne tableau skill | Clic | Mise à jour du radar (JS inline) | Radar animé, ligne sélectionnée surlignée |
| Filtre Verdict | Clic badge | Masque/affiche les lignes filtrées | Badge actif + compteur mis à jour |
| Tri colonne Score | Clic en-tête | Tri croissant/décroissant | Icône de tri visible, données réordonnées |

### Contrats d'Échange API
- Pas d'API réseau. Données lues depuis `memory/evals/skills_eval_summary.json` à la génération du HTML.

---

## Règles d'affaires

- **Seuils couleur alignés sur le moteur** : Vert ≥ 80 (PASS), Orange 65–79 (WARNING), Rouge < 65 (FAIL) — identiques aux seuils de `SkillEvalEngine`.
- **Lecture seule v1** : Aucun bouton d'action vers le backend. Le HTML est un rapport consultatif, pas une interface de commande.
- **Zéro CDN** : Toutes les dépendances JS (Chart.js) sont embarquées inline ou en bundle local dans `src/dashboard/assets/`. Cohérence avec ADR-0379 (confinement sandbox).
- **Regénération sur chaque run** : Le fichier `skills_health.html` est écrasé à chaque `mloop skill-eval --all`. Pas d'historique dans le HTML — l'historique est dans `skill_impact.jsonl`.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Données source** : `memory/evals/skills_eval_summary.json` (produit par MLOOP-240-BE)
- 📂 **Historique** : `memory/skill_impact.jsonl` (produit par MLOOP-242-BE)
- 🏛️ **ADR** : [ADR-0202](../../../standards/adr-system/0202-modularite-interne-agents.md) · [ADR-0379](../../../standards/adr-system/0379-sandbox-confinement.md)
- 📋 **Epic** : [`epics/epic_skills_eval_harness.md`](../epics/epic_skills_eval_harness.md)
- 📄 **Référence UI** : MLOOP-212-FE (HTML statique auto-contenu, zéro CDN)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Dashboard Skills Health — Vue Matrice & Radar

  Scénario: Affichage nominal — 39 skills avec rapport valide
    Étant donné un fichier skills_eval_summary.json valide avec 39 skills
    Quand j'ouvre skills_health.html dans un navigateur local
    Alors le tableau affiche 39 lignes avec scores et verdicts
    Et le chargement initial est inférieur à 300 ms
    Et aucun appel réseau externe n'est effectué (zéro CDN)

  Scénario: État vide — rapport absent
    Étant donné l'absence de memory/evals/skills_eval_summary.json
    Quand j'ouvre skills_health.html
    Alors le message "Aucun rapport d'évaluation trouvé — lancez mloop skill-eval --all" est affiché
    Et aucune erreur JavaScript n'est levée dans la console

  Scénario: Clic sur une skill — radar mis à jour
    Étant donné le dashboard chargé avec 39 skills
    Quand je clique sur la ligne "grill"
    Alors le graphique radar affiche les 4 axes de "grill" (trigger_clarity, rule_determinism, ground_truth_anchoring, resilience)
    Et la ligne "grill" est visuellement surlignée dans le tableau

  Scénario: Filtre par verdict FAIL
    Étant donné 3 skills avec verdict FAIL dans le rapport
    Quand j'active le filtre "FAIL"
    Alors seules les 3 skills FAIL sont visibles dans le tableau
    Et le compteur affiche "3 compétences"
    Et le bandeau d'alerte reste visible
```
