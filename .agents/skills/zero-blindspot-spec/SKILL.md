---
name: zero-blindspot-spec
description: Protocole déterministe d'analyse 360° Zéro Blindspot, ancrage ADR, cadrage d'épopée et découpage en récits Palier 1 (Draft + Questions Grill-Me). Orchestrateur haut niveau exécuté sur demande explicite. Use when analyzing an external specification, RFC, framework evolution, or complex feature to turn it into an official ADR, an Epic document under backlog/epics/, and sliced story drafts.
disable-model-invocation: true
---

# 🏛️ Skill : Zero-Blindspot Spec-to-Backlog Pipeline

## 🎯 Overview

Cette compétence formalise et automatise le protocole d'ingénierie senior permettant de transformer une spécification externe, une documentation officielle, une RFC ou une demande d'évolution complexe en un ensemble complet et cohérent d'artefacts mLoop :
1. **Vérité Terrain & Épistémique** (Cache crawler / extraits verbatim / diptyque *what it proves vs what it does not prove*).
2. **ADR Architectural** scellé sous `standards/adr-system/`.
3. **Cadrage d'Épopée** sous `Projects/<projet>/backlog/epics/epic_<slug>.md` selon `standards/blueprints/epic_template.md`.
4. **Découpage en Récits Palier 1** sous `Projects/<projet>/backlog/stories/` selon `standards/blueprints/story_draft_template.md`.
5. **Enregistrement SSOT & Indexation Mémoire** dans `Projects/<projet>/backlog/sprint_backlog.md` puis synchronisation via `swarm.py sync`.
6. **Contrôle de Vol** via `python src/swarm.py vibe-check`.

---

## 🧭 Le Pipeline Déterministe en 7 Étapes

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│               LE PIPELINE ZERO-BLINDSPOT SPEC-TO-BACKLOG                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. INGESTION       : Crawler ou extraire la spec officielle (vérité terrain)│
│ 2. AUDIT 360°      : Passer la matrice des 7 couches (ECOSYSTEM_RIGOR)      │
│ 3. ANCRAGE ADR     : Rédiger l'ADR de référence dans standards/adr-system/  │
│ 4. CADRAGE ÉPOPÉE  : Instancier epic_template.md dans backlog/epics/        │
│ 5. DÉCOUPAGE       : Générer les stories drafts Palier 1 (INVEST + Grill-Me)│
│ 6. SSOT & SYNCHRO  : Enregistrer dans sprint_backlog & swarm.py sync        │
│ 7. VIBE-CHECK      : Certifier l'intégrité (22+ PASS / 0 FAIL)              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Étape 1 : Ingestion & Extraction de Vérité Terrain (ADR-0375)
* Si une URL est fournie, vérifier d'abord si elle est présente dans le cache du crawler (`memory/crawler/cache/`).
* Si absente, crawler la cible ou lire les sources normatives avec un outil de lecture de contenu.
* Extraire les **faits techniques vérifiables**, les versions exactes, les endpoints, et les extraits verbatim nécessaires.
* **Validation Épistémique Obligatoire (Diptyque de Vérité)** :
  * 🟢 **Ce que la source prouve formellement** : Capacités avérées, signatures d'API exactes, contraintes matérielles ou logicielles explicites.
  * 🔴 **Ce que la source ne prouve pas** : Extrapolations du modèle, fonctionnalités non documentées, angles morts architecturaux. Ces points DOIVENT être consignés sous forme de questions ouvertes pour le Grill-Me.
* ⚠️ **Garde-fou** : Ne jamais concevoir sur des suppositions ou des souvenirs vagues de LLM. L'ancrage doit être physique.

---

### Étape 2 : Audit 360° en 7 Couches (ADR-0376)
Analyser systématiquement l'impact du changement sur l'ensemble des 7 couches du framework définies dans `standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md` :
1. **Couche 1 : Gabarits & Blueprints** (`standards/blueprints/`) — de nouveaux formats sont-ils nécessaires ?
2. **Couche 2 : Protocoles & Cycle de Vie** (`standards/protocols/`) — les flux ou règles de gestion changent-ils ?
3. **Couche 3 : Architecture & Décisionnel** (`standards/adr-system/`) — quel arbitrage de Type 1 est scellé ?
4. **Couche 4 : Directives Agents** (`.agents/agents/`, `standards/agents/`) — des personas doivent-ils être mis à jour ?
5. **Couche 5 : Skills Portables** (`.agents/skills/`) — de nouvelles compétences doivent-elles être créées ?
6. **Couche 6 : Cœur & CLI Python** (`src/core/`, `src/pipelines/`, `src/commands/`) — quels modules impactés ?
   * 📏 **Plafond Modulaire Strict (ADR-0202)** : Concision ≤ 300 lignes par fichier. Si un module risque de dépasser ce seuil, anticiper d'emblée la modularisation (ex: découpage en `*_core.py`, sous-modules ou adaptateurs).
7. **Couche 7 : Tests & Parité Documentaire** (`tests/`, `CLI_PIPELINE_GUIDE.md`) — comment garantir 100% de non-régression ?

---

### Étape 3 : Rédaction de l'ADR Normatif
* Trouver le prochain numéro d'ADR libre sous `standards/adr-system/` (ex: `0389-titre-en-kebab-case.md`).
* Rédiger l'ADR selon le standard établi :
  * Contexte & Problématique.
  * Décision d'Architecture & Alternatives considérées.
  * Conséquences Positives & Négatives.
  * Matrice d'Alignement sur les 7 Couches.
* Mettre à jour l'index dans `standards/adr-system/README.md`.

---

### Étape 4 : Cadrage de l'Épopée (`backlog/epics/`)
* Copier le gabarit `standards/blueprints/epic_template.md` vers `Projects/<projet>/backlog/epics/epic_<slug>.md`.
* Compléter :
  * Les références ADR, composants, origine et décideurs.
  * L'intention stratégique et les métriques de succès.
  * La cartographie mermaid montrant le graphe de dépendance entre les récits.
  * Le tableau récapitulatif des récits composant l'épopée.
  * La matrice d'impacts des 7 couches.

---

### Étape 5 : Découpage en Récits Palier 1 (`backlog/stories/`)
* Créer un fichier de récit pour chaque étape sous `Projects/<projet>/backlog/stories/<ID>.md` (ex: `MLOOP-210-BE.md`).
* Utiliser rigoureusement le gabarit Palier 1 `standards/blueprints/story_draft_template.md` :
  * **Frontmatter complet** : `id`, `jira_key: ""`, `epic_key`, `type: Feature`, `status: DRAFT`, `grill_me: PENDING`, `invest_score: 0/6`, `layer: frontend|backend|fullstack`.
  * **Section 1 : Intention Métier** (`En tant que... je veux... afin de...`).
  * **Section 2 : Origine & Cadrage Avant-Projet** (liens relatifs vers l'ADR et vers `backlog/epics/epic_<slug>.md`).
  * **Section 3 : Périmètre Sommaire** (`In-Scope` et `Out-of-Scope` macro).
  * **Section 4 : Critères de Succès Préliminaires** (jalons mesurables de haut niveau).
  * **Section 5 : Zones d'Ombre & Questions pour la Session Grill-Me 1:1** (questions contradictoires obligatoires issues de l'Étape 1).
* ⚠️ **Règle absolue Palier 1 (ADR-0366)** :
  * Tout récit créé lors du découpage initial est STRICTEMENT au statut `DRAFT` avec `grill_me: PENDING`. Aucune auto-promotion en `READY_FOR_DEV` n'est tolérée avant la session 1:1 Grill-Me avec le PO humain.
  * **Pas de Gherkin prématuré** : La rédaction exhaustive des scénarios Gherkin sur les 4 piliers (`story_template.md`) est réservée au Palier 2 (`READY_FOR_DEV`), après arbitrage contradictoire des zones d'ombre lors du Grill-Me.

---

### Étape 6 : Enregistrement SSOT & Synchronisation Mémoire
* Insérer la nouvelle épopée dans `Projects/<projet>/backlog/sprint_backlog.md`.
* Inclure le paragraphe d'origine avec lien relatif vers `epics/epic_<slug>.md`.
* Insérer la table Markdown des récits avec leur statut initial (`DRAFT` / `grill_me: PENDING`).
* **Synchronisation Obligatoire du Moteur Mémoire & FTS5** :
  ```powershell
  python src/swarm.py sync --project <NomProjet>
  ```
  Cette commande enregistre immédiatement les nouveaux récits et l'épopée dans `memory/loop_mem.db` (FTS5 / graphe de connaissances local) pour permettre le recoupement sémantique et la détection d'angles morts.

---

### Étape 7 : Contrôle de Vol Pré-Vol & Non-Régression
* Exécuter la commande souveraine :
  ```powershell
  python src/swarm.py vibe-check --project <NomProjet>
  ```
* Vérifier :
  * `Intégrité SSOT & Absence de Références Fantômes : PASS`
  * Total : `0 FAIL`.
* Si des tests unitaires ou des modules Python sont impactés, exécuter `pytest tests/`.

---

## ⚡ Exemple d'Invocation pour l'Agent

```text
Exécute la compétence zero-blindspot-spec sur la spécification officielle :
- Source : https://modelcontextprotocol.io/docs/2026-07-28/getting-started/intro
- Projet Cible : mLoop
- Thématique : Support des extensions Tasks, MCP Apps ui:// et Elicitation
```
