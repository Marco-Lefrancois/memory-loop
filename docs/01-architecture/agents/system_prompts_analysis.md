# Rapport d'Analyse Comparative : System Prompts d'Agents IA & Alignment mLoop

## 1. Contexte & Objectif de l'Étude

Ce rapport d'analyse évalue l'architecture des consignes système (*system prompts*) issues des principaux assistants agentiques du marché (Anthropic Claude Code, Google Antigravity, Cursor, GitHub Copilot) et met en perspective leurs patterns de conception avec le framework de gouvernance d'état **mLoop (Memory Loop)**.

L'objectif est d'adopter une **démarche prudente et basée sur des données** pour déterminer si les consignes actuelles de mLoop (`AGENTS.md`, `GEMINI.md`, `docs/agents/`) nécessitent des ajustements ou si elles constituent déjà un standard robuste.

---

## 2. Analyse Comparative des Design Patterns

| Pattern de System Prompt | Fonctionnement dans les Agents Majeurs (Claude Code, Antigravity, Cursor) | Implémentation & Pertinence dans mLoop | Évaluation & Recommandation |
| :--- | :--- | :--- | :--- |
| **1. Enclavement & Frontières (`Boundary Enforcing`)** | Restriction stricte des répertoires accessibles en écriture et interdiction de modifier certains fichiers système ou de configuration sans confirmation. | **La Loi des 3 Piliers** (`reference/`, `docs/`, `backlog/`) et le terrain de jeu restreint sous `Projects/<p>/backlog/` ou `src/`. | **Excellente** : mLoop applique un découpage encore plus strict que la plupart des assistants généralistes en isolant la matière première, la SSOT et le backlog. |
| **2. Raisonnement Explicite (`Scratchpad / <thinking>`)** | Bloc de pensée explicite non présenté directement comme réponse finale pour décomposer la logique avant l'action. | Utilisé systématiquement via le bloc `<thinking>` pour l'analyse d'architecture et les arbitrages métiers. | **Conforme** : Permet de prévenir l'hallucination et de séparer les *faits* établis des *décisions* à trancher avec l'utilisateur. |
| **3. Planification Explicite (`Plan-First & Task Tracking`)** | Génération préalable d'un plan de modifications (`implementation_plan.md`) et suivi dynamique par tâches (`task.md`). | Protocole **Plan-First** obligatoire (périmètre, fichiers ciblés, règles mobilisées, questions ouvertes) + confirmation gate utilisateur. | **Très Haute Valeur** : Prévient les modifications intempestives de code ou de spécifications avant validation explicite. |
| **4. Interrogation Structurée (`Grill with Docs & D-A-F-E`)** | Questionnement de l'utilisateur pour clarifier les zones d'ombre plutôt que d'émettre des hypothèses non vérifiées. | Protocole **Grill with Docs** (Faits vs Décisions) + Contrat d'Interaction D-A-F-E pour le Frontend + Registre des `OQ-XXX`. | **Supérieur au Standard** : La plupart des agents généralistes ont tendance à combler l'ambiguïté par des hypothèses. mLoop interdit l'assomption (*Zero-Assumption*). |
| **5. Boucle d'Auto-Correction (*Self-Healing & Exit Code 0*)** | Exécution silencieuse de tests ou de linters en arrière-plan avant d'annoncer l'achèvement d'une tâche. | Règle d'**Auto-Audit (WikiFix, audit-loop, aoep)** exécutée automatiquement après toute modification de récit. | **Crucial** : Garantit que tout récit produit respecte immédiatement le blindage Gherkin 4 Piliers et les règles d'isolation sémantique. |
| **6. Matrice d'Outillage par Phase (`Phase Scoped Tools`)** | Restriction des outils utilisables selon la phase courante pour éviter la confusion d'outils (*Tool Confusion*). | Matrice explicite sur 5 phases (SPEC $\rightarrow$ PLAN $\rightarrow$ BUILD $\rightarrow$ VALIDATE $\rightarrow$ SHIP) avec guardrails par phase. | **Excellente** : Empêche l'utilisation d'outils inappropriés (ex: lecture brute de fichiers texte dans `reference/` au lieu d'interroger Open Notebook). |

---

## 3. Analyse d'Impact & Évaluation de Pertinence

### 3.1. Les consignes racines mLoop sont-elles déjà optimales ?
**Oui.** L'analyse démontre que `AGENTS.md` et `GEMINI.md` intègrent déjà l'ensemble des meilleures pratiques découvertes dans les prompts d'agents les plus avancés de l'industrie :
- **Absence de Fluff** (*Zero-Fluff*) et communication concise.
- **Séparation stricte des responsabilités** (mLoop comme Backend d'État et de Validation, le code physique cliente restant externe sous le contrôle de l'utilisateur via son IDE ou Aider).
- **Harnais déterministe** (commandes CLI `swarm.py`, `wikifix`, `wayfinder`, `to-spec`, `to-tickets`, `audit-loop`).

### 3.2. Prudence et Recommandation d'Action
Par mesure de prudence et pour éviter toute régression ou churn d'instructions :
1. **Pas de modification à chaud des fichiers racines (`AGENTS.md` / `GEMINI.md`)** : Les règles actuelles sont parfaitement équilibrées et éprouvées.
2. **Usage selon l'IDE** :
   - **Sous Antigravity** : Conserver 100% de la matrice d'outillage, du protocole Plan-First, des artefacts et de la gouvernance MCP.
   - **Sous OpenCode** : Si un relais de dev physique est requis dans un IDE tiers léger, la documentation présente dans `docs/agents/` servira de guide sans surcharger la configuration système d'Antigravity.

---

## 4. Conclusion

Les principes d'ingénierie de prompts et d'architecture d'agents extraits des systèmes industriels confirment la validité et la maturité du framework mLoop. Aucune modification précipitée des règles système n'est nécessaire. Ce rapport reste consigné dans `docs/agents/system_prompts_analysis.md` comme référence d'audit et de comparaison.
