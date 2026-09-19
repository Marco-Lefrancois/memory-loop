# 🏛️ Protocole de Rigueur d'Ingénierie & Audit 360° (Zéro Blindspot)

**Statut** : Norme Fondatrice Inviolable (ADR-0376)  
**Date d'effet** : Septembre 2026  
**Autorité** : Architecte en Chef & Équipe Core mLoop  
**Champ d'Application** : Toute modification du moteur, des protocoles, des gabarits ou des directives de Memory Loop (`Projects/mLoop` ou racine `C:\Memory Loop\`).

---

## 🎯 1. Raison d'Être & Contexte

Dans un environnement agentique distribué multi-LLMs (Claude, Gemini, GPT, Antigravity, OpenCode), modifier un système complexe sans cartographie globale provoque inévitablement des régressions insidieuses :
- Des gabarits de stories redondants ou abandonnés.
- Des incohérences entre la machine à états Python et la documentation SSOT.
- Des consignes obsolètes résiduelles dans les personas ou skills des agents.
- Des tests unitaires masquant des hypothèses erronées.

Ce protocole décrète la fin des interventions isolées et impose la **méthode de l'Audit 360° en 7 Couches (Zéro Blindspot)** pour toute évolution de l'écosystème mLoop.

---

## 🧭 2. Les 7 Couches de l'Audit 360° (Matrice Inviolable)

Avant d'écrire ou de modifier la moindre ligne de code ou de directive sur Memory Loop, l'agent ou l'ingénieur DOIT auditer et cartographier l'impact sur l'ensemble des 7 couches ci-dessous :

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                   LES 7 COUCHES DE L'ÉCOSYSTÈME MLOOP                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Blueprints        : Quels gabarits sont créés, modifiés ou rendus caducs ?│
│ 2. Protocoles        : Quels frameworks méthodologiques régissent ce flux ? │
│ 3. Architecture ADR  : Quels ADRs fondateurs sont créés ou amendés ?        │
│ 4. Directives Agents : Quels personas (plan, sentinel, orchestrator) changent?│
│ 5. Skills Portables  : Quelles compétences (.agents/skills/) sont impactées?│
│ 6. Core & CLI Python : Quels modules (core, pipelines, commands) implémentent?│
│ 7. Tests & Parité    : Quels tests garantissent 100% de non-régression ?    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Couche 1 : Gabarits & Blueprints (`standards/blueprints/`)
* **Question clé** : Le changement introduit-il un nouveau format de document ? Rend-il un template existant obsolète ?
* **Règle d'or** : Aucun gabarit ne doit subsister sans être activement utilisé par les pipelines ou les agents. Éliminer immédiatement les doublons.

### Couche 2 : Protocoles & Frameworks Métier (`standards/protocols/`)
* **Question clé** : Les règles de gouvernance, de cycle de vie ou de rédaction sont-elles alignées avec la nouvelle réalité ?
* **Règle d'or** : Tout changement de flux doit être consigné dans `PROJECT_LIFECYCLE_STAGES.md` et `STORY_AUTHORING_FRAMEWORK.md`.

### Couche 3 : Architecture & Système Décisionnel (`standards/adr-system/`)
* **Question clé** : Cette modification relève-t-elle d'une décision irréversible de Type 1 ? Contredit-elle un ADR antérieur ?
* **Règle d'or** : Si un ADR existant est impacté (ex: ADR-0339 amendé par ADR-0375), ne jamais écraser silencieusement l'historique : ajouter une bannière formelle d'amendement et créer un nouvel ADR explicite.

### Couche 4 : Directives, Personas & TOML Agents (`.agents/agents/`, `standards/agents/`)
* **Question clé** : Les agents spécialisés (`plan`, `sentinel`, `orchestrator`) ont-ils les instructions à jour dans leur prompt système et leur fichier TOML ?
* **Règle d'or** : Un agent avec des directives désynchronisées sabotera le nouveau workflow. Mettre à jour `developer_instructions` et personas en continu.

### Couche 5 : Skills & Compétences Portables (`.agents/skills/`)
* **Question clé** : Les compétences des agents (`grill`, `plan`, `vibe-check`) décrivent-elles fidèlement le nouveau comportement opérationnel ?
* **Règle d'or** : Chaque skill impactée doit refléter les nouveaux drapeaux CLI, gabarits et déclencheurs.

### Couche 6 : Moteur Core Python & CLI (`src/core/`, `src/pipelines/`, `src/commands/`)
* **Question clé** : La machine à états FSM, le registre des commandes (`_registry.py`) et les linters respectent-ils le nouveau standard ?
* **Règle d'or** : Maintenir une rétrocompatibilité déterministe pour les projets existants (auto-migration des anciens fichiers d'état).

### Couche 7 : Suite de Tests & Parité de Documentation (`tests/`, `CLI_PIPELINE_GUIDE.md`)
* **Question clé** : Les tests unitaires couvrent-ils les nouvelles transitions ? Le guide CLI est-il strictement synchrone ?
* **Règle d'or** : Exécuter systématiquement `python src/swarm.py guide --sync` et valider 100% de tests verts (`uv run pytest`).

---

## 📋 3. Protocole d'Exécution en 4 Étapes

Pour toute initiative d'évolution sur Memory Loop, l'agent doit impérativement suivre les 4 étapes suivantes :

1. **Étape 1 : Balayage à Froid & Recherche de Dépendances**
   * Exploration par motifs de recherche textuelle (`ripgrep`) pour identifier chaque occurrence de l'ancien concept à travers l'ensemble des 7 couches.
2. **Étape 2 : Rédaction du Plan d'Implémentation Zéro Blindspot**
   * Présentation à l'humain d'un inventaire complet classé par couche avec statut explicite : `[NEW]`, `[MODIFY]`, `[DELETE]`.
   * Interdiction formelle de coder avant approbation explicite.
3. **Étape 3 : Exécution Atomique & Harmonisation Synchrone**
   * Application des modifications couche par couche en préservant l'intégrité référentielle.
4. **Étape 4 : Clôture & Certification par les Tests**
   * Lancement de la suite complète de tests de cycle de vie, persistance, blueprints et parité CLI.
   * Rédaction d'un compte-rendu de conformité (*Walkthrough*).
