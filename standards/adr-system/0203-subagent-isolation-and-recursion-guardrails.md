# ADR-0203 : Isolation des Sous-Agents, Guardrails Anti-Récursion & Écosystème Herdr
## Statut : Accepté (Série 02xx - Architecture Multi-Agents & Loop Graph)
## Date : 2026-08-26
## Références : Claude Code Subagents Standard, Herdr v0.8+ PTY Multiplexer, ADR-0200, ADR-0201

---

## 1. Contexte

Face à la prolifération des architectures multi-agents complexes (*recursive agents*), les systèmes monolithiques souffrent de dérives systémiques majeures :
- **Pourriture de contexte (*Context Rot*)** : pollution de la conversation principale par des logs et explorations secondaires brutes.
- **Biais de complaisance & collusion (*Validator Collusion*)** : un LLM validant passivement ses propres omissions sans audit contradictoire neutre.
- **Boucles infinies & blocages (*Deadlocks & Recursive Ping-Pong*)** : échanges bilatéraux asymétriques sans mécanisme d'arbitrage déterministe.
- **Dérive de concurrence (*Concurrency Drift*)** : incompatibilités sémantiques entre agents parallèles Frontend et Backend.

---

## 2. Décision

Nous adoptons le standard unifié **mLoop Sub-Agents & Guardrails** articulé autour de 4 piliers normatifs :

### 1. Isolation Stricte de Contexte (*Context Preservation & Clean Slate*)
- Chaque sous-agent de recherche ou de validation opère dans un sous-processus éphémère PTY indépendant (piloté via Herdr `worker-spawn`).
- Seuls les **EvidencePacks JSON structurés** et typés (`src/pipelines/evidence.py`) transitent entre les nœuds et vers la session orchestratrice principale.
- Zéro fuite de texte brut intermédiaire ou d'historique polluant dans le prompt principal.

### 2. Scoping Granulaire des Outils & Permissions Asymétriques
- **Orchestrator** : Raisonnement de synthèse, planification, délégation. Permissions bash contrôlées.
- **Plan / Research** : Exploration en lecture seule (`tools: [Read, Grep, Glob]`, `edit: "ask"`).
- **Build / Worker** : Exécution TDD dans un workspace isolé (`isolated_workspace`, `edit: "allow"`).
- **Sentinel (Audit Contradictoire)** : Verrouillage strict en lecture seule (`edit: "deny"`). Les validateurs ne peuvent en aucun cas auto-corriger silencieusement le document qu'ils évaluent.

### 3. Circuit-Breaker Déterministe & Miroir de Contrats (0 ms LLM)
- **CircuitBreakerGovernor** : Plafond strict de récursion ($Max=2$ passes de correction). Détection automatique des cycles de dépendances (`detect_deadlock`) et gèle immédiat avec alerte humaine (`HITL`) en cas de blocage.
- **DeterministicContractMirror** : Vérification AST pure Python de l'isomorphisme des contrats d'API (routes, méthodes, structures de payloads) avant fusion des branches parallèles dans `EvidenceReducer`.

### 4. Manifeste Herdr Plugin & Visualisation Live DAG (`herdr-dagr` pattern)
- Exposition native du fichier racine `herdr-plugin.toml` pour brancher mLoop sur le multiplexeur Herdr.
- Émission d'événements temps réel sur `memory/herdr_events.jsonl` pour piloter le panneau TUI DAG d'avancement des sous-agents.
- Collecte périodique d'hygiène mémoire (`dream_collector`) pour déprécier en `TOMBSTONE` les règles RHO obsolètes.

---

## 3. Conséquences

- **Robustesse & Déterminisme** : Élimination mathématique des boucles infinies et des hallucinations récursives.
- **Économie de Tokens & Modèle Économique** : Routage sélectif sur modèles gratuits (`opencode/nemotron-3-ultra-free`, `deepseek-v4-flash`) sans saturation de quotas.
- **Expérience Utilisateur Transparente** : Visualisation claire de l'essaim d'agents dans la console et dans Herdr.
