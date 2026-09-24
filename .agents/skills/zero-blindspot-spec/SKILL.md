---
name: zero-blindspot-spec
description: Protocole déterministe d'analyse 360° Zéro Blindspot, ancrage ADR, cadrage d'épopée et découpage en récits Palier 1. Use when analyzing an external specification, RFC, framework evolution, or complex feature to turn it into an official ADR, an Epic document under backlog/epics/, and sliced story drafts.
---

# 🏛️ Skill : Zero-Blindspot Spec-to-Backlog Pipeline

## 🎯 Overview

Cette compétence formalise et automatise le protocole d'ingénierie senior permettant de transformer une spécification externe, une documentation officielle, une RFC ou une demande d'évolution complexe en un ensemble complet et cohérent d'artefacts mLoop :
1. **Vérité Terrain** (Cache crawler / extraits verbatim / fact-checking).
2. **ADR Architectural** scellé sous [`standards/adr-system/`](file:///C:/Memory%20Loop/standards/adr-system/).
3. **Cadrage d'Épopée** sous [`Projects/<projet>/backlog/epics/epic_<slug>.md`](file:///C:/Memory%20Loop/Projects/mLoop/backlog/epics/) selon [`standards/blueprints/epic_template.md`](file:///C:/Memory%20Loop/standards/blueprints/epic_template.md).
4. **Découpage en Récits Palier 1** sous [`Projects/<projet>/backlog/stories/`](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/) selon [`standards/blueprints/story_draft_template.md`](file:///C:/Memory%20Loop/standards/blueprints/story_draft_template.md).
5. **Enregistrement SSOT** dans [`sprint_backlog.md`](file:///C:/Memory%20Loop/Projects/mLoop/backlog/sprint_backlog.md).
6. **Contrôle de Vol** via `python src/swarm.py vibe-check`.

---

## 🧭 Le Pipeline Déterministe en 7 Étapes

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│               LE PIPELINE ZERO-BLINDSPOT SPEC-TO-BACKLOG                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. INGESTION       : Crawler ou extraire la spec officielle (verbatim SSOT) │
│ 2. AUDIT 360°      : Passer la matrice des 7 couches (ECOSYSTEM_RIGOR)      │
│ 3. ANCRAGE ADR     : Rédiger l'ADR de référence dans standards/adr-system/  │
│ 4. CADRAGE ÉPOPÉE  : Instancier epic_template.md dans backlog/epics/        │
│ 5. DÉCOUPAGE       : Générer les stories drafts Palier 1 (INVEST + Gherkin) │
│ 6. SSOT BACKLOG    : Enregistrer l'épopée et les récits dans sprint_backlog │
│ 7. VIBE-CHECK      : Certifier l'intégrité (22+ PASS / 0 FAIL)              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Étape 1 : Ingestion & Extraction de Vérité Terrain (ADR-0375)
* Si une URL est fournie, vérifier d'abord si elle est présente dans le cache du crawler (`memory/crawler/cache/`).
* Si absente, crawler la cible ou lire les sources normatives avec un outil de lecture de contenu.
* Extraire les **faits techniques vérifiables**, les versions exactes, les endpoints, et les extraits verbatim nécessaires.
* ⚠️ **Garde-fou** : Ne jamais concevoir sur des suppositions ou des souvenirs vagues de LLM. L'ancrage doit être physique.

---

### Étape 2 : Audit 360° en 7 Couches (ADR-0376)
Analyser systématiquement l'impact du changement sur l'ensemble des 7 couches du framework définies dans [`standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md`](file:///C:/Memory%20Loop/standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md) :
1. **Couche 1 : Gabarits & Blueprints** (`standards/blueprints/`) — de nouveaux formats sont-ils nécessaires ?
2. **Couche 2 : Protocoles & Cycle de Vie** (`standards/protocols/`) — les flux ou règles de gestion changent-ils ?
3. **Couche 3 : Architecture & Décisionnel** (`standards/adr-system/`) — quel arbitrage de Type 1 est scellé ?
4. **Couche 4 : Directives Agents** (`.agents/agents/`, `standards/agents/`) — des personas doivent-ils être mis à jour ?
5. **Couche 5 : Skills Portables** (`.agents/skills/`) — de nouvelles compétences doivent-elles être créées ?
6. **Couche 6 : Cœur & CLI Python** (`src/core/`, `src/pipelines/`, `src/commands/`) — quels modules impactés (respect strict ADR-0202 ≤ 300L) ?
7. **Couche 7 : Tests & Parité Documentaire** (`tests/`, `CLI_PIPELINE_GUIDE.md`) — comment garantir 100% de non-régression ?

---

### Étape 3 : Rédaction de l'ADR Normatif
* Trouver le prochain numéro d'ADR libre sous `standards/adr-system/` (ex: `0388-titre-en-kebab-case.md`).
* Rédiger l'ADR selon le standard établi :
  * Contexte & Problématique.
  * Décision d'Architecture & Alternatives considérées.
  * Conséquences Positives & Négatives.
  * Matrice d'Alignement sur les 7 Couches.
* Mettre à jour l'index dans [`standards/adr-system/README.md`](file:///C:/Memory%20Loop/standards/adr-system/README.md).

---

### Étape 4 : Cadrage de l'Épopée (`backlog/epics/`)
* Copier le gabarit [`standards/blueprints/epic_template.md`](file:///C:/Memory%20Loop/standards/blueprints/epic_template.md) vers `Projects/<projet>/backlog/epics/epic_<slug>.md`.
* Compléter :
  * Les références ADR, composants, origine et décideurs.
  * L'intention stratégique et les métriques de succès.
  * La cartographie mermaid montrant le graphe de dépendance entre les récits.
  * Le tableau récapitulatif des récits composant l'épopée.
  * La matrice d'impacts des 7 couches.

---

### Étape 5 : Découpage en Récits Palier 1 (`backlog/stories/`)
* Créer un fichier de récit pour chaque étape sous `Projects/<projet>/backlog/stories/<ID>.md` (ex: `MLOOP-210-BE.md`).
* Utiliser rigoureusement [`standards/blueprints/story_draft_template.md`](file:///C:/Memory%20Loop/standards/blueprints/story_draft_template.md) :
  * Frontmatter complet : `id`, `jira_key: ""`, `epic_key`, `type: Feature`, `status: DRAFT`, `grill_me: PENDING`, `invest_score: 0/6`.
  * Section 1 : Intention Métier (`En tant que... je veux... afin de...`).
  * Section 2 : Origine & Cadrage Avant-Projet (liens relatifs vers l'ADR et vers `backlog/epics/epic_<slug>.md`).
  * Section 3 : Périmètre Sommaire (`In-Scope` et `Out-of-Scope`).
  * Section 4 : Scénarios de Test Gherkin 4 piliers (Nominal, Aux Limites, Résilience/Cyber, Non-Régression).
* ⚠️ **Règle absolue Palier 1 (ADR-0366)** : Tout récit créé lors du découpage initial est STRICTEMENT au statut `DRAFT` avec `grill_me: PENDING`. Aucune auto-promotion en `READY_FOR_DEV` n'est tolérée avant la session 1:1 Grill-Me avec le PO humain.

---

### Étape 6 : Enregistrement SSOT dans `sprint_backlog.md`
* Insérer la nouvelle épopée dans [`Projects/<projet>/backlog/sprint_backlog.md`](file:///C:/Memory%20Loop/Projects/mLoop/backlog/sprint_backlog.md).
* Inclure le paragraphe d'origine avec lien relatif vers `epics/epic_<slug>.md`.
* Insérer la table Markdown des récits avec leur statut initial (`DRAFT` / `grill_me: PENDING`).

---

### Étape 7 : Contrôle de Vol Pré-Vol & Non-Régression
* Exécuter la commande souveraine :
  ```powershell
  python src/swarm.py vibe-check --project <NomProjet>
  ```
* Vérifier :
  * `Intégrité SSOT & Absence de Références Fantômes : PASS`
  * Total : `0 FAIL`.
* Si des tests unitaires sont impactés, exécuter `pytest tests/`.

---

## ⚡ Exemple d'Invocation pour l'Agent

```text
Exécute la compétence zero-blindspot-spec sur la spécification officielle :
- Source : https://modelcontextprotocol.io/docs/2026-07-28/getting-started/intro
- Projet Cible : mLoop
- Thématique : Support des extensions Tasks, MCP Apps ui:// et Elicitation
```
