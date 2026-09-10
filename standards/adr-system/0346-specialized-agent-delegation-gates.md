# ADR-0346 : Suite des 5 Workers Stratégiques Spécialisés mLoop, Isolation Cognitive & Matrice Zero-Blindspot

- **Statut** : Approuvé (Constitutionnel)
- **Date** : 2026-09-02
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Périmètre** : Framework Backend mLoop, Pipelines de Délégation, Simulation Black-Box, Mining Legacy, Shadow Estimation, Dissection Visuelle, Watcher Mémoire

---

## 1. Contexte & Problématique

L'orchestrateur mLoop (System 2 & 1) opère comme le cerveau d'architecture de l'IDE. Si certaines opérations légères sont résolues *in-process* par le chargement de compétences méthodologiques (Skills), certaines tâches critiques nécessitent une **isolation stricte** afin d'éliminer le biais de complaisance (*Self-Validation Sycophancy*), d'éviter la saturation cognitive et de garantir l'impartialité des décisions.

Cette ADR standardise la suite des **5 Workers Stratégiques Spécialisés** de mLoop propulsés par le runtime **Herdr v0.8.2+**.

---

## 2. Décisions d'Architecture

### 2.1 Les 5 Workers Stratégiques & leurs Protocoles d'Exécution

```
                                  ┌────────────────────────────────────────────────────────┐
                                  │           ORCHESTRATEUR PRINCIPAL (mLoop p1)           │
                                  └───────────────────────────┬────────────────────────────┘
                                                              │
                       ┌──────────────────────────────────────┼──────────────────────────────────────┐
                       │                                      │                                      │
                       ▼                                      ▼                                      ▼
       ┌───────────────────────────────┐      ┌───────────────────────────────┐      ┌───────────────────────────────┐
       │   1. ZERO-ASK HANDOFF TEST    │      │    2. LEGACY LOGIC MINER      │      │     3. SHADOW ESTIMATOR       │
       │  • Black-Box Enclave isolée   │      │  • CodeGraph AST Filter       │      │  • Red-Team Thinking Model    │
       │  • Modèle : Sonnet 4.6        │      │  • Modèle : Sonnet 5          │      │  • Modèle : GPT-5.6 Thinking  │
       │  • Mission : Test d'autonomie │      │  • Mission : Extraction BRs   │      │  • Mission : Contre-chiffrage │
       └───────────────────────────────┘      └───────────────────────────────┘      └───────────────────────────────┘
                       │                                      │
                       ▼                                      ▼
       ┌───────────────────────────────┐      ┌───────────────────────────────┐
       │    4. VISUAL DISSECTOR        │      │     5. SEMANTIC JANITOR       │
       │  • Headless OCR Chromium      │      │  • SHA256 Anti-Loop Debounce  │
       │  • Modèle : Gemini Flash-Lite │      │  • Single-Pass / Watcher      │
       │  • Mission : Matrice 8 États  │      │  • Mission : Intégrité Mémoire│
       └───────────────────────────────┘      └───────────────────────────────┘
```

1. **Simulateur de Handoff "Zero-Ask" (`worker-handoff-test`)** :
   - *Modèle LiteLLM* : `claude-sonnet-4.6` (`build`).
   - *Protocole* : Test à l'aveugle dans une enclave temporaire ne contenant **que** le fichier `US-XXX.md`. Si l'agent hésite ou invente un contrat ➔ Statut `HANDOFF_REJECTED`. Si autonome ➔ `HANDOFF_APPROVED`.
2. **Mineur de Logique Métier Legacy (`worker-legacy-mine`)** :
   - *Modèle LiteLLM* : `claude-sonnet-5` (`deepsearch`).
   - *Protocole* : Exploration ciblée par CodeGraph d'un dossier de code existant et génération de règles d'affaires atomiques sous `docs/02-business-rules/BR-LEGACY-*.md`.
3. **Shadow Estimator & Challengeur de Risques (`worker-shadow-estimate`)** :
   - *Modèle LiteLLM* : `gpt-5.6-terra-thinking` (`validation`).
   - *Protocole* : Chiffrage contradictoire pessimiste fondé sur les dépendances techniques externes, générant `memory/plan/shadow_estimation_*.json`.
4. **Dissecteur de Contrat Visuel (`worker-visual-dissect`)** :
   - *Modèle LiteLLM* : `gemini-3.5-flash-lite` (`compaction`).
   - *Protocole* : Extraction des libellés et cartographie exhaustive des 8 états d'interface (ADR-0340) dans `docs/05-assets/*_ui_matrix.json`.
5. **Janitor Sémantique Continu (`worker-janitor-watch`)** :
   - *Protocole* : Watcher d'arrière-plan avec empreinte SHA256 et debounce pour prévenir les boucles infinies. Émission de toasts Herdr non-bloquants.

### 2.2 Distillation Dual-Track : Skill vs Worker
- **In-Process (Skill)** : Directives légères chargées dans la mémoire de travail de l'orchestrateur (`view_file` sur `SKILL.md`). Zéro création de sous-processus.
- **Out-of-Process (Worker)** : Tâches franchissant la `DELEGATION GATE` nécessitant un nouveau volet Herdr, un modèle dédié et un cycle de vie autonome.

---

## 3. Statut d'Alignement & Fichiers Cibles
- **Module Pipelines** : `src/pipelines/delegation/` (`handoff_simulator.py`, `legacy_miner.py`, `shadow_estimator.py`, `visual_dissector.py`, `semantic_janitor.py`)
- **CLI Commands** : `src/commands/_registry.py` & `src/commands/handlers/worker.py`
- **MCP Bridge** : `src/bridges/mcp_herdr.py`
- **Plugin Manifest** : `plugins/mloop-herdr-plugin/herdr-plugin.toml`
