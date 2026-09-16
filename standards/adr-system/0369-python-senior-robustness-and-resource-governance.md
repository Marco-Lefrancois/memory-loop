# ADR-0369 : Gouvernance des Ressources & Robustesse Python Senior — Les 7 Standards d'Ingénierie mLoop

- **Statut** : Approuvé (Constitutionnel)
- **Date** : 2026-09-15
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Périmètre** : Ensemble du framework mLoop (`src/`), Suites de tests (`tests/`), Spécification du paquet (`pyproject.toml`)
- **Autorité** : [ADR-0001](0001-python-state-graph.md), [ADR-0341](0341-runnable-gates-depth-tree-orchestration.md), [ADR-0352](0352-harnessdev-autonomous-harness-creation-evolution.md), [ADR-0367](0367-structured-concurrency-resource-orchestration.md)
- **Références R&D** : Nahla Davies, *7 Python Best Practices Senior Developers Follow (That Beginners Often Miss)*, KDnuggets, Sep 2026 ; PEP 544 (Protocols) ; PEP 621 (pyproject.toml metadata).

---

## 1. Contexte & Problématique

Memory Loop est un framework de méta-orchestration multi-agents écrit en Python >= 3.12. Le pipeline manipule des ressources hétérogènes : bases SQLite locales en mode WAL (`loop_mem`, `agent_graph`, `semantic_cache`), connexions HTTP/2 persistantes vers LiteLLM et Jira Cloud, exécutions de sous-processus d'outils externes (CodeGraph, Graphify, Git, Playwright) et systèmes de cache.

Un audit architectural approfondi du runtime Python (`src/`) à la lumière des pratiques avancées de l'industrie (synthétisées par Nahla Davies sur KDnuggets) a révélé plusieurs failles de robustesse latentes :
1. **Fuites de Connexions SQLite** : Des fonctions utilitaires (notamment `record_rho_solution` et `search_rho_solution` dans `src/loop_mem/db.py`) appelaient une méthode legacy `_get_observation_conn()` ouvrant une connexion sans jamais appeler `conn.close()`, remettant la libération des verrous WAL au bon vouloir du ramasse-miettes (*garbage collector*).
2. **Attentes Externe Sans Limite (*Unbounded External Waits*)** : Plusieurs gestionnaires CLI exécutaient `subprocess.run` (ex. `_run_codegraph_command` dans `src/commands/handlers/code_intelligence.py`) sans argument `timeout`, créant un risque de freeze infini du pipeline si l'outil externe attend un input ou subit un blocage.
3. **Pauvreté Contextuelle des Logs & Silences d'Exceptions** : L'utilisation de `except Exception: pass` silencieux (notamment dans l'enregistrement de métrologie) combinée à un formateur `MLoopFormatter` ignorant les métadonnées `extra={...}` privait les opérateurs de contexte d'audit post-mortem.
4. **Biais de Complaisance dans les Suites de Tests** : Sur 100 fichiers de tests, seuls 3 utilisaient `@pytest.mark.parametrize` et 9 utilisaient `pytest.raises`, laissant les contrats de rupture aux frontières non validés.

---

## 2. Décisions d'Architecture

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               GOUVERNANCE DES RESSOURCES & ROBUSTESSE PYTHON SENIOR (ADR-0369)          │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   1. TYPAGE STRUCTUREL (Protocols)      -> Injection explicite des collaborateurs      │
│   2. GESTION DES RESSOURCES (with)      -> Zéro connexion/socket hors Context Manager  │
│   3. DEADLINES D'EXÉCUTION (timeout)    -> Timeout obligatoire sur tout subprocess/net │
│   4. OBSERVABILITÉ CONTEXTUELLE (extra) -> Sérialisation automatique des paires clé/val│
│   5. TESTS AUX FRONTIÈRES (parametrize) -> Validation systématique du Failure Contract  │
│   6. SSOT DU PAQUET (pyproject.toml)    -> Déclaration unifiée PEP 621 et dev tools    │
│   7. DÉPRÉCIATION EXPLICITE (stacklevel)-> warnings.warn sur toute API legacy          │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Règle 1 : Typage Structurel via `typing.Protocol`
Les composants consommant des services externes (LLM, HTTP, Cache) doivent privilégier des protocoles d'interface (`typing.Protocol`) plutôt que de forcer une instanciation interne ou un couplage fort à une classe concrète. Les collaborateurs sont injectés au constructeur ou en argument de méthode.

### Règle 2 : Gouvernance Stricte des Ressources par Context Managers
- L'ensemble des accès aux bases SQLite doit obligatoirement utiliser un context manager (`with get_observation_db_session() as conn:` ou `@contextmanager def _connection(self):`).
- L'utilisation de fonctions renvoyant des connexions nues sans gestion de cycle de vie (comme `_get_observation_conn()`) est formellement interdite.
- Tout client asynchrone possédant un pool persistant (ex. `AsyncLLMClient`) doit exposer un protocole contextuel `async with` et une méthode de fermeture explicite `aclose()`.

### Règle 3 : Obligation Constitutionnelle de Timeout sur Tout Appel Externe
- Tout appel à `subprocess.run`, `subprocess.Popen` ou client HTTP synchrone au sein de `src/` DOIT comporter un argument `timeout` explicite (valeur par défaut recommandée : `30.0` secondes).
- Tout dépassement de délai doit être capturé (`subprocess.TimeoutExpired`, `TimeoutError`) et transformé en exception typée et diagnostiquable.

### Règle 4 : Journalisation Structurée & Interdiction du `except Exception: pass` Nu
- Le formateur `MLoopFormatter` est bonifié pour injecter automatiquement dans la sortie de log toute clé transmise via `extra={...}` sous la forme `cle=valeur`.
- Tout bloc `except Exception: pass` avalant silencieusement une erreur est requalifié en `logger.debug("...", exc_info=True, extra={...})` afin de préserver l'auditabilité sans bloquer l'exécution.

### Règle 5 : Exigence de Couverture du Contrat d'Échec (*Failure Contract*)
Les suites de tests (`tests/`) ne doivent plus se limiter au scénario nominal (*happy path*). Les tests d'intégration et de validation d'API doivent tester systématiquement les codes d'erreur (400, 401, 403, 429, 500, 504), les payloads tronqués et les timeouts via `@pytest.mark.parametrize` et `pytest.raises`.

### Règle 6 : Centralisation du Contrat de Dépendances dans `pyproject.toml`
Les dépendances de développement, de test et de validation de code sont formalisées dans la section `[project.optional-dependencies]` de `pyproject.toml`, aux côtés des tables d'outillage `[tool.pytest.ini_options]`, `[tool.ruff]` et `[tool.mypy]`.

### Règle 7 : Protocole de Dépréciation Standardisée
Toute fonction interne ou interface publique mLoop appelée à être remplacée doit émettre un `warnings.warn(message, DeprecationWarning, stacklevel=2)` spécifiant la fonction de substitution, avant toute suppression physique dans une version ultérieure.

---

## 3. Conséquences & Invariants

- **Positives** : Éradication définitive des fuites de verrous SQLite WAL et des blocages de subprocess en production ; observabilité limpide des incidents via les logs contextuels ; tests unitaires résilients aux pannes réseau ; maintenance facilitée pour les développeurs et agents IA.
- **Invariants de Contrôle** :
  1. Le guide d'ingénierie opérationnel associé est consigné sous [`standards/protocols/PYTHON_SENIOR_CODING_STANDARDS.md`](../protocols/PYTHON_SENIOR_CODING_STANDARDS.md).
  2. La documentation source ingérée est conservée sous [`docs/00-ingested/kdnuggets_7_python_best_practices.md`](../../docs/00-ingested/kdnuggets_7_python_best_practices.md).
  3. Tout code de `src/` violant la Règle 2 (connexion SQLite sans context manager) ou la Règle 3 (subprocess sans timeout) est considéré comme non conforme lors du Vibe-Check.
