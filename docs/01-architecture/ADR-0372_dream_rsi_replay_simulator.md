# ADR-0372 : Replay Simulator Hors-Ligne & Auto-Amélioration Récursive du Harnais (Synthèse Dream RSI & Modular RSI)

- **Statut** : Approuvé (Constitutionnel)
- **Date** : 2026-09-16
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Périmètre** : Pipeline de rêverie et consolidation (src/pipelines/dream_rsi/), Gestion de l'historique d'exécution (memory/events.jsonl, xecution_traces.json), Moteur d'optimisation de harnais, Commande CLI dream-rsi
- **Autorité** : [ADR-0001](0001-python-state-graph.md), [ADR-0201](0201-orchestration-dag-multi-agents.md), [ADR-0202](0202-modularite-interne-agents.md), [ADR-0310](0310-vibe-code-session-resume.md), [ADR-0335](0335-deep-paper-note-ingestion-epistemic-grounding.md), [ADR-0347](0347-agentic-memory-evals-write-path-fidelity-unprompted-recall.md), [ADR-0369](0369-python-senior-robustness-and-resource-governance.md), [ADR-0370](0370-cli-pipeline-ssot-generator-and-anti-drift-governance.md), [ADR-0371](0371-paradigme-dual-harnais-preventif-et-point-in-time-recovery-agentique.md)
- **Références R&D** : Tong Zheng et al. (Google DeepMind, UMD, UVA), *Dream-RSI: Recursive Self-Improvement through Evolving Worlds*, arXiv:2609.14858v1, Sep 2026 ; *Modular RSI: Harness Optimization*; Noam Brown (OpenAI, Sep 2026).

---

## 1. Contexte & Problématique

L'auto-amélioration récursive (RSI - *Recursive Self-Improvement*) est l'un des défis majeurs de l'intelligence artificielle agentique. Dans un écosystème de méta-orchestration comme mLoop, les agents explorent continuellement des arbres de décisions complexes : découverte de règles métier, synthèse d'architectures, génération de tests et audit de conformité.

Traditionnellement, les systèmes d'exploration agentique souffrent d'un dilemme insoluble :
1. **Stratégies d'Exploration Statiques** : Des heuristiques codées en dur (patience fixe, nombre de branches arbitraire, seuils de retry immuables) qui ne s'adaptent pas à l'expérience accumulée et gaspillent du calcul dans des impasses.
2. **Optimisation en Ligne Prohibitive** : Ajuster une politique d'exploration en temps réel pendant l'exécution requiert des milliers d'appels LLM payants, avec un feedback extrêmement différé (nécessité de dérouler de longs horizons d'inférence avant de juger de la pertinence d'une stratégie).

Les recherches récentes de **Google DeepMind, UMD et UVA (Dream-RSI)** et l'analyse de **Modular RSI** démontrent que :
- Les historiques d'exploration passés d'un agent constituent déjà un **Simulateur de Rejeu (*Replay Simulator / Evolving Worlds*)**.
- Toutes les transitions, réussites, échecs et métriques réelles étant consignées dans les traces, le système peut « rêver » hors-ligne (*dreaming*) en simulant et comparant des milliers d'alternatives à coût zéro.
- **Constat contre-intuitif majeur** : Tenter d'injecter des résumés rédigés en langage naturel dans les invites dégrade les performances cognitives. En revanche, optimiser la **méta-stratégie structurelle d'exploration** (graphe, branchement, arrêt précoce) et le **harnais modulaire** produit des gains spectaculaires et transférables entre modèles LLM.

---

## 2. Décisions d'Architecture

`	ext
┌────────────────────────────────────────────────────────────────────────────────────────┐
│             DREAM-RSI : REPLAY SIMULATOR HORS-LIGNE & MODULAR RSI (ADR-0372)           │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   [PHASE ÉVEILLÉE (Online Execution)]                                                  │
│   Tâches réelles ──> Trajectoires d'exécution ──> memory/events.jsonl                   │
│                                                                                        │
│   [CONSTRUCTION DU SIMULATEUR DE REJEU (Offline Replay Simulator)]                     │
│   events.jsonl + execution_traces.json ──> ReplaySimulator (Arbre d'états réels)       │
│                                                                                        │
│   [PHASE DE RÊVE : DREAMING-BASED POLICY OPTIMIZATION]                                 │
│   DreamExplorer ──> Rejeu de N politiques candidates (largeur, patience, cutoff)       │
│   └──> Évaluation à coût zéro (zéro appel API LLM externe)                             │
│   └──> Sélection Pareto (Performance max, Coût/Tokens min)                             │
│   └──> Garantie de Non-Régression : la politique active pi_0 est toujours candidate    │
│                                                                                        │
│   [MODULAR RSI : ISOLATION DU HARNAIS]                                                 │
│   ModularHarnessIsolator ──> Décomposition des échecs (Memory, Tool, Gate, Prompt)     │
│   └──> Ajustement chirurgical de la brique défaillante sans toucher au modèle          │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
`

### 1. Le Simulateur de Rejeu Hors-Ligne (ReplaySimulator)
mLoop exploite désormais les traces historiques (memory/events.jsonl, memory/execution_traces.json, memory/sessions/) comme un monde simulé déterministe. Chaque nœud de l'arbre stocke les actions tentées, les outils appelés et les scores de sortie constatés.

### 2. L'Optimiseur de Méta-Stratégie d'Exploration (DreamExplorer)
Lors du cycle nocturne ou de maintenance (python src/swarm.py dream-rsi --simulate), DreamExplorer fait varier les hyper-paramètres de parcours :
- **Facteur de branchement** ( \in [1, 5]$) : nombre d'hypothèses explorées en parallèle.
- **Seuil de patience** ( \in [1, 4]$) : nombre d'échecs tolérés avant abandon d'une branche.
- **Early-stopping déterministe** : coupure immédiate dès que l'évaluation d'une porte stagne sous 5%.
- **Garantie Monotone de Survie** : La politique actuelle $\pi_0$ fait obligatoirement partie de l'échantillon. Une nouvelle politique n'est adoptée que si son score simulé surpasse $\pi_0$ ou égale ses performances avec un coût d'exploration réduit.

### 3. Modular RSI : Isolation Chirurgicale du Harnais (ModularHarnessIsolator)
Conformément à la thèse fondamentale « Harnais > Modèle », le système isole les causes racines des échecs sans jamais blâmer aveuglément les poids du LLM :
- *Composante Mémoire* : dépassement de fenêtre de contexte, amnésie ou poison contextuel.
- *Composante Tooling* : indisponibilité ou paramètres d'outils non conformes.
- *Composante Gate* : non-conformité aux critères d'acceptation Gherkin ou seuils de couverture.
- *Composante Prompt* : directives ambiguës nécessitant un renforcement déterministe.

### 4. Règle Constitutionnelle : Interdiction des Résumés Flous
Conformément aux résultats empiriques de Dream-RSI, il est formellement interdit de substituer des résumés textuels d'expériences passées aux politiques de contrôle d'arbres. Le système s'améliore par des méta-paramètres de structure, non par de la prose cumulative.

---

## 3. Conséquences & Invariants

- **Zéro Dépense Inutile de Tokens** : L'évaluation de centaines de méta-stratégies s'exécute localement en mémoire en moins d'une seconde, sans requêter LiteLLM.
- **Transfert Inter-Modèles** : Les harnais optimisés via Dream RSI bénéficient instantanément à tout nouveau modèle de fondation branché sur mLoop.
- **Architecture Modulaire Stricte (ADR-0202)** : L'ensemble du sous-système est fractionné en 4 modules autonomes de moins de 200 lignes sous src/pipelines/dream_rsi/.
