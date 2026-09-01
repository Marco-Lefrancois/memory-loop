# Matrice de Maturité Agentique : Framework MLOOP

Ce document d'architecture interne mappe les concepts d'ingénierie avancés à travers nos 3 niveaux d'architectures agentiques. Il sert de guide pour les équipes de développement et de **grille d'évaluation** pour auditer les projets au sein du framework Memory Loop (mLoop v2.0.0).

---

## Niveau 1 : Le Pipeline Procédural (Stateless DAG & Task Workers)
**Objectif :** Exécution prédictible de tâches isolées (ETL, Batch, Routage).

### ⚖️ Forces & Faiblesses
*   🟢 **Forces :** Ultra-rapide, très peu coûteux, prédictible à 100 %, extrêmement facile à déboguer (on sait exactement quelle étape a planté).
*   🔴 **Faiblesses :** Rigide. Si le format de la donnée d'entrée change ne serait-ce qu'un peu, le script casse. Aucune capacité d'adaptation face à l'imprévu.

### 1. Les 3 Layers (Context, Harness, Model)
*   **Model :** Modèles rapides et peu coûteux (ex: Gemini Flash, GPT-4o-mini).
*   **Harness :** Très minimaliste. Souvent une simple API REST ou un orchestrateur statique (LangChain, n8n).
*   **Context :** Injecté au moment de l'appel. Aucun contexte dynamique persistant.

### 2. Les 5 Piliers
*   **Memory & Session Recall :** Amnésie cognitive totale. Peut posséder un état opérationnel temporaire (logs), mais aucune mémoire persistante.
*   **Skills :** Hardcodées. Appels de fonctions figés dans le code.
*   **Soul :** Utilitaire. Ton et valeurs limités à un formatage strict.
*   **Self-healing :** Limité aux mécanismes techniques (retries, fallback). Sans raisonnement autonome. Un système d'alerte strict (Dead-letter queue / Notifications avec format standardisé) est obligatoire.

### 3. Agent Conception & Développement
*   **Développement :** Itération manuelle. Aucune boucle d'évaluation autonome.

### 4. Boîte à Outils (Harness Tools)
*   *Non applicables ici.* 

---

## Niveau 2 : Le Copilote Contextuel (Stateful Workspace & HITL Boundary)
**Objectif :** Partenaire de travail interactif nécessitant une compréhension fine du contexte local, bridé par une validation humaine.

### ⚖️ Forces & Faiblesses
*   🟢 **Forces :** Rend l'humain "super-puissant" tout en gardant 100% du contrôle. Très forte adaptabilité face aux problèmes complexes grâce au raisonnement du LLM. Excellent ROI à court terme.
*   🔴 **Faiblesses :** Goulot d'étranglement manuel (inopérant sans l'humain). Amnésie inter-sessions (dépendance stricte à la qualité des fichiers de contexte locaux).

### 1. Les 3 Layers
*   **Harness (Le Cerveau Local) :** Le cœur du Niveau 2 (ex: Antigravity, Claude Code, Cursor). Gère l'UI, le workspace et maintient la session interactive.
*   **Context :** Fortement ancré dans le Workspace local (fichiers ouverts, arborescence, `AGENTS.md`).
*   **Model :** Modèles puissants (Gemini 3 Flash/Pro, Claude Sonnet, DeepSeek R1).

### 2. Les 5 Piliers
*   **Memory & Session Recall :** Persistance de session (chat) et mémoire par fichiers (lecture de `AGENTS.md`).
*   **Skills :** Manifestes portables au standard **Agent Plugins 1.0** (`.agents/skills/` avec `SKILL.md`). Un *Skill* est un "paquet de connaissances et d'instructions spécialisées activé à la demande" pour préserver le budget d'instructions.
*   **Soul :** Forte identité d'équipe (ton Senior Tech Lead, rules Zero-Fluff).
*   **Self-healing :** Assisté (Human-in-the-Loop). Le développeur doit initier et valider la relance en cas d'erreur. Tout mécanisme modifiant de façon autonome le code source d'une application client sans validation humaine est formellement interdit.

### 3. Agent Conception & Développement
*   La *Soul* et les *Skills* sont configurées au standard Agent Plugins 1.0 (`.agents/plugin.json`, `.agents/mcp.json`).
*   **Évaluation (Evals) :** Se fait de manière itérative via le feedback direct du développeur et le linter `wikifix`.

### 4. Boîte à Outils (Harness Tools)
*   **AGENTS.md**, **LSP** (précision du symbole), **MCP Bridges** (`mcp_loop_mem.py`), **Plugins AP 1.0**.

---

## Niveau 3 : L'Écosystème Cognitif (State-Machine Swarm, Graph DAG & Contract-Driven AI)
**Objectif :** Opérations autonomes de longue durée, décisions architecturales, exécution de topologies DAG Multi-Agents et maintien rigoureux de l'état global.

### ⚖️ Forces & Faiblesses
*   🟢 **Forces :** Autonomie totale sur des jours ou des semaines. Capacité unique à maintenir une architecture complexe à long terme grâce au Graphe de Connaissances (SSOT) et à s'auto-corriger via `calibrate`.
*   🔴 **Faiblesses :** Coût de développement et d'API explosif si non régulé. Ingénierie complexe. Risque majeur de "boucle infinie" si mal gouverné (prévenu par le *Circuit Breaker* et le *Token Budget Guard*).

### 1. Les 3 Layers
*   **Context :** Domine le système. La Machine à États sémantique orchestre dynamiquement le flux DAG (Pattern Diamant, Scoper, Reducer, Risk Router).
*   **Harness (Execution Runner) :** Supervisé par le Swarm central avec points de contrôle idempotents (`.mloop_tmp/checkpoints/`).
*   **Model :** Architecture Asymétrique (System 2 pour la stratégie, le Grill et la validation des SCC, System 1 pour l'exécution physique déterministe).

### 2. Les 5 Piliers
*   **Memory & Session Recall :** Absolue. Stockée dans le Graphe de Connaissances (`knowledge_graph.json` & `graphify-out/`). Protocole *Search-First Protocol* obligatoire (`graphify query`) avant toute planification.
*   **Mission Layer (Anti-Goal Drift) :** Couche d'objectifs persistants verrouillée par `python src/swarm.py focus`.
*   **Self-healing & Auto-Repair :** Autonome en boucle fermée via le linter `wikifix`, la rétroaction `RHO` (`rho_rules.yaml`) et le moteur `calibrate`. Limité par un **Coupe-circuit** (budget de tokens maximal + TTL max).
*   **Skills Portables (AP 1.0) :** Artefacts versionnés et portables (`plugin-export`) déployables sur tous les IDEs compatibles.
*   **Validation & EvidencePacks :** Intransigeante. Validation systématique des **4 Piliers Gherkin** et génération autonome d'un artefact JSON d'audit `memory/evidence/<STORY_ID>_evidence.json` via `EvidencePackEngine`.

### 3. Agent Conception & Développement
*   **Harness -> Evals -> Calibrate Engine -> Better agent :** Auto-étalonnage continu des 8 composants de l'écosystème mLoop (`python src/swarm.py calibrate`).

### 4. Boîte à Outils (Harness Tools)
*   **Graph Engineering DAG (`graph-run`)**, **Ponts MCP**, **EvidencePackEngine**, **Agent Plugins 1.0 (`plugin-export`)**.

---

## 📋 Grille d'Évaluation MLOOP (Audit de Projets)

Utilisez cet arbre de décision pour auditer un projet existant ou concevoir une architecture.

### Question 1 : Le cycle de décision est-il autonome et fermé ? (N2 vs N3)
*   *Le système possède-t-il une boucle décisionnelle fermée capable de modifier son plan d'action de manière irréversible et sans validation humaine ?*
    *   **NON (Délégation Hybride) :** L'humain pilote le cycle ou valide les étapes $\rightarrow$ **Niveau 2**.
    *   **OUI (Autonomie Totale) :** Le système pilote son propre cycle de vie $\rightarrow$ **Niveau 3**.

### Question 2 : Tolérance au risque & Contrôle
*   *Si le système est autonome (Question 1 = OUI), quel est le risque métier ?*
    *   **Faible risque (Jetables) :** Données temporaires ou batch routinier $\rightarrow$ **Niveau 1**.
    *   **Risque critique (Altération Prod/Architecture) :** $\rightarrow$ **Niveau 3** (Exigence de SCC + EvidencePack).

### Question 3 : Horizon temporel et Mémoire (Prévention du Goal Drift)
*   *Sur quelle durée l'agent doit-il conserver la compréhension de son objectif ?*
    *   **Le temps d'un appel API :** $\rightarrow$ **Niveau 1**.
    *   **La session de travail de l'utilisateur :** $\rightarrow$ **Niveau 2**.
    *   **Des semaines/mois (Processus Daemonisé) :** $\rightarrow$ **Niveau 3** (Exigence de Mission Layer, Checkpoints et SSOT).

### Question 4 : Complexité de la logique et Traçabilité (Audit Trail)
*   *Le système doit-il justifier et tracer ses décisions (Audit, Conformité, Post-mortem) dans un graphe de dépendances ?*
    *   **NON (Opérations triviales) :** $\rightarrow$ **Niveau 1** ou **Niveau 2**.
    *   **OUI (Explicabilité obligatoire) :** $\rightarrow$ **Niveau 3** (Exigence d'un EvidencePack JSON et de SCC validés).

---

## 🚨 Signaux d'Alarme Architecturaux (Red Flags) lors d'un Audit

1. **L'Usine à Gaz Niveau 1 :** Un script procédural rempli de centaines de conditions `if/else` pour tenter de mimer un raisonnement. *(Correction : Migrer vers un N2).*
2. **Le N2 Fantôme :** Un Copilote déployé sans fichier `AGENTS.md` ni `Soul` explicite. Il échouera en production dès la perte de son contexte de session locale.
3. **Le Faux Niveau 3 (YOLO Agent) :** Une boucle réflexive autonome mais *SANS* contrat formel (SCC) et sans pack d'évidence. Résultat : dérive fonctionnelle certaine. *(Correction : SCC & EvidencePack obligatoires).*
4. **Le Knowledge Graph Décoratif :** Un système qui écrit dans une base (Write-first) mais que l'agent ne consulte jamais pour prendre ses décisions (Search-never).
5. **Le Zombie Agent (Boucle Infinie) :** Un Niveau 3 sans Coupe-circuit ni Token Budget Guard. *(Correction : Circuit Breaker & Calibrate).*

---

## 📘 Annexe Technique & Lexique (Standards MLOOP)

*   **SCC (Story Constraint Contract) :** Représentation testable d'une contrainte métier ou architecturale (modèles Pydantic/TypeScript, 4 Piliers Gherkin).
*   **EvidencePack :** Artefact JSON structuré (`memory/evidence/<STORY_ID>_evidence.json`) consolidant les preuves d'audit, alertes (`[!NOTE]`, `[!WARNING]`, etc.) et questions ouvertes (`Q-`, `QD-`).
*   **Soul (Behavioral Contract Layer) :** Couche de gouvernance comportementale qui contraint les décisions du modèle (valeurs, règles Zero-Fluff) indépendamment de la mission en cours.
*   **Coupe-Circuit (Circuit Breaker) :** Mécanisme de sécurité déterministe imposé aux agents de Niveau 3 (Max loops, Token Budget, TTL).
