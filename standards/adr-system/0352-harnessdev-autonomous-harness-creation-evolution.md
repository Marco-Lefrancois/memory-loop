# ADR-0352 : Enseignements HarnessDev, Abstraction H=<E,T,C,S,L,V> & Souveraineté du Harnais d'Agent mLoop

- **Statut** : Approuvé (Constitutionnel)
- **Date** : 2026-09-07
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Périmètre** : Framework Backend mLoop, Protocole de Harnais (docs/01-architecture/framework/architecture_harness_mloop.md), Pipeline Research (src/pipelines/research_pipeline.py), Crawler mLoop (src/pipelines/crawler.py), Moteur d'Auto-Évolution (src/swarm.py self-dev), Gouvernance d'État AOEP & EvidencePacks (memory/evidence/)

---

## 1. Contexte & Problématique

Le 1er septembre 2026, la publication du benchmark de référence **HarnessDev** (arXiv:2609.01437, ByteDance Seed, SUTD, Georgia Tech, M-A-P, TokenWave.AI) a introduit un tournant paradigmatique dans l'ingénierie des agents autonomes :
1. **L'impasse des benchmarks centrés sur les réponses (*Answer-Centric*)** : Les benchmarks historiques (SWE-bench, GAIA, Terminal-Bench, tau-bench) évaluent la réponse ponctuelle d'un modèle au sein d'un harnais figé conçu par des humains. Cette approche masque le fait que la performance en production dépend massivement du logiciel d'exécution qui entoure le modèle (le *harnais*). À poids identiques, GPT-5 résout 35.2% de Terminal-Bench dans Terminus 2, mais atteint 49.6% dans Codex CLI.
2. **Le défi de la création et de l'évolution autonome d'infrastructure** : HarnessDev évalue pour la première fois la capacité de 6 modèles de pointe (Opus 4.8, GPT-5.5, Gemini 3.1 Pro, DeepSeek V4 Pro, Qwen 3.7 Max, Seed 2.0 Pro) à :
   - **Créer (RQ1)** un système d'exécution exécutable et scorable  = \langle E, T, C, S, L, V \rangle$ à partir d'une graine minimale non-agissante (*weak seed*).
   - **Faire évoluer (RQ2)** ce harnais de manière itérative à l'aide de traces d'échecs en boucle fermée sur des jeux de données réels.
3. **Alignement avec la philosophie mLoop** : mLoop a postulé dès sa fondation le principe de la **Suprématie du Harnais** (*Harness Supremacy Protocol*) : l'intelligence et la fiabilité d'un système agentique ne résident pas uniquement dans les poids neuronaux, mais s'accumulent dans l'échafaudage logiciel déterministe (boucle, état persistant, outillage typé, guardrails).

Cette ADR consigne les enseignements formels de HarnessDev et acte les renforcements requis dans l'écosystème mLoop.

---

## 2. Diptyque de Grounding & Audit Épistémique (ADR-0335)

Conformément à la norme [ADR-0335](0335-deep-paper-note-ingestion-epistemic-grounding.md), l'audit s'appuie sur le découpage épistémique strict des données brutes ingérées (memory/crawler/cache/crawl_www_alphaxiv_org_4feab621bdfe.md) :

`
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        DIPTYQUE DE GROUNDING — HARNESSDEV (2609.01437)                 │
├──────────────────────────────────────────┬─────────────────────────────────────────────┤
│ WHAT IT ACTUALLY PROVES                  │ WHAT IT DOES NOT PROVE                      │
│ • Les LLMs peuvent créer des harnais     │ • Les LLMs ne remplacent pas les ingénieurs │
│   fonctionnels en Writing et MLE (égaux  │   humains sur les dépôts de code complexes  │
│   ou supérieurs aux références humaines).│   (écart de 10.7 à 51.1 pts sur SWE-Pro).   │
│ • La persistance d'état et de mémoire    │ • L'évolution par feedback n'est pas        │
│   est défaillante chez tous les créateurs│   monotone : 37.5% des révisions régressent │
│   (0% de checkpointing sur 26 679 runs). │   et les gains sur-apprennent sur le dev.   │
│ • Le volume de code ajouté ne corrèle    │ • Pas de preuve de boucle d'auto-           │
│   pas avec le score (Gemini: 1 006 LOC,  │   amélioration infinie (saturation rapide). │
│   meilleur score Terminal-Bench 68.8%).  │ • Ne couvre pas les topologies multi-agents │
│ • Forte co-adaptation créateur/exécuteur │   asynchrones (DAG, consensus distribué).   │
│   (Opus passe de 69.3% à 33.0% sous      │                                             │
│   Gemini ; requêtes de recherche x8.7).  │                                             │
│ • "Lint is a floor" validé : les tests   │                                             │
│   mécaniques ne corrèlent pas (r=0.13),  │                                             │
│   seul le diagnostic d'échec aide (r=0.57│                                             │
├──────────────────────────────────────────┴─────────────────────────────────────────────┤
│ CLAIM BOUNDARIES                                                                       │
│ Valide pour les boucles d'agents mono-agent ReAct sur conteneurs isolés et les tâches   │
│ standards de programmation/recherche. Ne préjuge pas des architectures swarm à états.  │
└────────────────────────────────────────────────────────────────────────────────────────┘
`

---

## 3. Matrice de Confrontation  = \langle E, T, C, S, L, V \rangle$

HarnessDev formalise le harnais comme un sextuplet de modules fonctionnels. L'analyse des résultats démontre que l'architecture mLoop compense structurellement les faiblesses révélées par le benchmark :

| Module Formel | Rôle Normalisé | Constat & Pathologie HarnessDev | Réponse Architecturale mLoop |
| :--- | :--- | :--- | :--- |
| **$ (Execution)** | Boucle de décision, séquencement, arrêts | Arrêts prématurés non détectés (441 runs dégénérés). Limites codées en dur (120 pas). | **CLI Déterministe & Phases 0 à 5** : Machine à états finis src/state.py et orchestration pilotée par objectifs. |
| **$ (Tools)** | Registre d'outils, validation I/O | Plantages de syntaxe bash, collisions d'arguments non typés. | **MCP Proxy Router & Plugins AP 1.0** (src/bridges/mcp_proxy_router.py). Interfaces typées strictes. |
| **$ (Context)** | Formatage d'invite, compaction, historique | Compaction naïve rompant la correspondance call/result des modèles stricts (Gemini). | **AST CodeGraph & Chunking Sémantique** (ADR-0323). Injection ciblée sans altération de l'historique conversationnel. |
| **$ (State)** | **Persistance, mémoire, hypothèses, reprise** | **ÉCHEC TOTAL : 0% de checkpointing déclenché sur 26 679 trajectoires**. Amnésie de session. | **AOEP-v0, LoopState & EvidencePacks** : Sérialisation JSON/Markdown sur disque à chaque fin de phase (memory/evidence/). |
| **$ (Lifecycle)** | Hooks avant/après action, reprise sur incident | Crash silencieux lors des ruptures de conteneur, aucun rollback de commit défectueux. | **Dynamic Hooks & Boot Sequence** (ADR-0322). Handlers isolés avec restauration d'état automatique (esume). |
| **$ (Verification)** | Lint, tests unitaires, validation de patch | Validation purement syntaxique ; fausse sécurité des auto-tests (=0.13$). | **Multi-Gates "Lint is a floor"** (ADR-0335). Triptyque : Lint déterministe -> Review Sentinel -> Preuve d'intégration. |

---

## 4. Décisions Normatives pour le Framework mLoop

### 4.1 Préservation Absolue de la Couche d'État Déterministe ($)
L'échec universel documenté dans HarnessDev (où 11 créateurs sur 18 déclarent du code de mémoire sans jamais l'exécuter) confirme le danger de déléguer la persistance au bon vouloir de l'agent.
- **Règle** : La sérialisation d'état (LoopState, EvidencePacks, caches de crawler, registres SHA256) doit demeurer **entièrement gérée par le code Python du framework** (src/state.py, src/pipelines/), hors des mains du LLM. L'agent ne décide pas *s'il doit* sauvegarder : le framework persiste automatiquement après chaque phase.

### 4.2 Standardisation Neutre des Outils & Prévention de la Co-Adaptation
Le benchmark démontre qu'un harnais optimisé pour un modèle précis (ex: Opus 4.8) s'effondre lorsqu'il est exécuté par un autre modèle (Gemini 3.1 Pro : chute de 69.3% à 33.0% sur SWE-Pro).
- **Règle** : Les descriptions de fonctions, schémas d'outils et prompts système mLoop (	ools.yaml, .agents/skills/, .agents/mcp.json) doivent respecter une neutralité absolue vis-à-vis des fournisseurs. Interdiction d'intégrer des idiomes spécifiques à un seul modèle dans le cœur du framework.

### 4.3 Règle "Diagnostic First" pour l'Auto-Évolution (self-dev)
HarnessDev prouve que les créateurs LLM qui lisent superficiellement les scores globaux régressent dans 37.5% des cas, alors que ceux qui dissèquent les traces détaillées (	rajectory.jsonl) réalisent des gains pérennes.
- **Règle** : Toute session d'auto-développement (python src/swarm.py self-dev) doit impérativement débuter par l'inspection des échecs récents (memory/wikifix_report.md, logs de calibration) avant de modifier la moindre ligne de code.

### 4.4 Optimisation du Crawler & Recherche Anti-Bouclage (ADR-0345)
La recherche et navigation longue distance est le domaine où l'écart avec l'humain est le plus grand (-39.8% sur BrowseComp, 88.2% de requêtes dupliquées).
- **Règle** : Le composant src/pipelines/crawler.py consolide ses gardes-fous : détection automatique des clones Markdown (.md), normalisation d'URL avec retrait des paramètres de tracking, et cache déterministe TTL (max_age) pour interdire tout gaspillage de contexte.

---

## 5. Statut & Alignement

- **Conformité ADR-0335** : Validée (Diptyque de Grounding complet consigné dans eference/research/harnessdev_paper_2609.01437.md).
- **Gouvernance mLoop** : Intégration immédiate dans le corpus des standards SSOT (standards/adr-system/).
