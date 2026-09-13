# ADR-0367 : Orchestration Asynchrone Structurée — Éradication des Tâches Orphelines, Budgets Hiérarchiques & Gestion Dynamique des Ressources

- **Statut** : Approuvé (Constitutionnel)
- **Date** : 2026-09-13
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Périmètre** : Client LLM (src/core/llm_client.py), Crawler Web (src/pipelines/crawler.py), Débat d'Agents (src/bridges/batch_debate.py), Bus d'Acteurs (src/core/actor_swarm.py)
- **Autorité** : [ADR-0201](0201-orchestration-dag-multi-agents.md), [ADR-0345](0345-smart-crawler-v2-discovery-and-traversal.md), [ADR-0352](0352-harnessdev-autonomous-harness-creation-evolution.md), [ADR-0365](0365-harmonisation-symbiotique-skills-et-standard-agent-skills.md)
- **Références R&D** : KDnuggets (*5 Python Techniques for Efficient Resource Orchestration*, Shittu Olumide, Sep 2026), Python 3.11+ PEP 654 (Exception Groups) & TaskGroup, Python 3.14 PEP 779 (Free-Threaded Concurrency Support)

---

## 1. Contexte & Problématique

Memory Loop est un moteur d'orchestration multi-agents asynchrone fondé sur Python >= 3.12. Dans sa version initiale, plusieurs briques critiques (AsyncLLMClient.batch_complete, WebCrawlerAgent._execute_async, BatchDebateBridge) s'appuyaient sur le pattern classique asyncio.gather(*tasks, return_exceptions=True/False).

L'analyse R&D et le profilage sous charge ont mis en lumière quatre faiblesses majeures en production :
1. **Prolifération de Tâches Orphelines (Le Syndrome gather)** : Si une coroutine au sein de asyncio.gather lève une exception ou expire, les autres coroutines sœurs continuent de s'exécuter de façon invisible en arrière-plan. Cela entraîne une surconsommation de tokens LLM (surfacturation LiteLLM Nmedia Cloud), une rétention abusive de connexions HTTPX et un risque d'écriture d'états incohérents.
2. **Absence de Bounding Global de Capacité** : Les créations ad-hoc de sémaphores par appel empêchent de borner la capacité globale au niveau du processus, exposant les fournisseurs tiers (LiteLLM, APIs cibles du crawler) à des dépassements de quotas (*429 Too Many Requests*).
3. **Imbrication Rigide des Gestionnaires de Contexte** : Lors de sessions hybrides nécessitant simultanément des connexions HTTPX, des instances Playwright et des verrous SQLite, l'imbrication statique de blocs async with devient fragile et sujette aux fuites de ressources si l'un des contextes échoue à l'initialisation.
4. **Délais Non Coopératifs & Blocages Cumulatifs** : L'utilisation de timeouts unitaires par requête réseau (ex: `timeout=12.0`) sans budget temps global parent permet à un crawl multi-pages ou un débat d'agents d'accumuler des retards exponentiels sans point d'arrêt ferme.

---

## 2. Décisions d'Architecture

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                   MÂT CONCURRENCE & ORCHESTRATION STRUCTURÉE (ADR-0367)                │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   1. STRUCTURED CONCURRENCY (Zéro Tâche Orpheline)                                     │
│      async with asyncio.TaskGroup() as tg:                                            │
│          tg.create_task(coro_1)                                                        │
│          tg.create_task(coro_2)                                                        │
│      -> En cas d'exception sur coro_1, coro_2 est annulée immédiatement et proprement  │
│                                                                                        │
│   2. PROPAGATION HIÉRARCHIQUE DES DÉLAIS (Deadlines Coopératives)                      │
│      async with asyncio.timeout(overall_budget):                                       │
│          async with asyncio.TaskGroup() as tg:                                        │
│              tg.create_task(bounded_call(per_task_timeout))                            │
│                                                                                        │
│   3. NETTOYAGE DYNAMIQUE GARANTI (AsyncExitStack)                                      │
│      async with AsyncExitStack() as stack:                                             │
│          conns = [await stack.enter_async_context(res) for res in dynamic_resources]   │
│      -> Fermeture garantie LIFO en cas d'erreur ou d'interruption                      │
│                                                                                        │
│   4. OBSERVABILITÉ & INTROSPECTION EN VOL                                              │
│      Enregistrement des coroutines actives dans TaskRegistry (Nom, Début, Deadline)    │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Règle 1 : Remplacement Systématique de asyncio.gather par asyncio.TaskGroup
Tout traitement parallèle de lots de coroutines au sein du framework mLoop (src/) DOIT être orchestré via asyncio.TaskGroup().
- L'utilisation de asyncio.gather() est formellement bannie pour les traitements de lots batch.
- Toute exception survenant dans une tâche enfant entraîne l'annulation immédiate (cancel()) de toutes les tâches sœurs du groupe avant la sortie du bloc contextuel.

### Règle 2 : Budgétisation Temporelle Hiérarchique avec asyncio.timeout()
Chaque pipeline d'orchestration longue (crawling, batch LLM, débats) DOIT définir :
1. Un **budget temporel global** (overall_timeout) encapsulant l'ensemble du lot.
2. Un **délai unitaire par appel** (per_call_timeout) bornant chaque requête.
3. Le mécanisme standard est asyncio.timeout(), remplaçant les appels disparates à asyncio.wait_for().

### Règle 3 : Gestion Dynamique du Cycle de Vie via AsyncExitStack
Lorsque le nombre de ressources réseau ou contextes asynchrones (clients HTTP, sessions Playwright, contextes d'état) est résolu dynamiquement à l'exécution, ils DOIVENT être inscrits dans un contextlib.AsyncExitStack. Aucun descripteur ne doit subsister en cas de levée d'exception.

### Règle 4 : Registre d'Observabilité des Tâches (TaskRegistry)
Le framework intègre un registre in-memory non-bloquant des coroutines principales, associant chaque tâche à un nommage sémantique (project, action, deadline). Cela permet un diagnostic précis des coroutines bloquées via python src/swarm.py daemon status --tasks.

---

## 3. Conséquences & Invariants

- **Positives** : Éradication totale des tâches zombies et de la consommation fantôme de tokens ; fermeture déterministe et étanche des sockets et contextes ; respect inviolable des délais d'exécution fixés par l'utilisateur.
- **Vérification Obligatoire** : Toute modification du moteur asynchrone doit valider la suite de tests `tests/test_structured_concurrency.py` avec 0 coroutine orpheline mesurée en post-exécution.