# Brief de Mission — P7 : Résidus AST ADR-0369 (hors RULE-AST-01)

**Date** : 2026-09-23  
**Projet** : mLoop  
**Task-type** : build  
**Priorité** : P7 (ordre validé P4→P7→P5→P6→P3→P8)  
**Base légale** : ADR-0369 (7 standards Python), ADR-0202 (modularité), ADR-0381 (harnais Phase 3)  
**Périmètre EXCLUS** : toute violation RULE-AST-01 (dette modulaire → P5/P6/EPIC-17) · toute modification de `src/core/ast_checker.py` (ADR-0376 — hors mission) · commits Git

---

## 0. Commandes de vérification (à exécuter avant/après)

```bash
python src/swarm.py code-check --file <chemin>   # par fichier touché
python src/swarm.py code-check --all --project mLoop  # bilan final (compter 0 sur les règles 02/03/04)
python -m pytest <tests pertinents> -q
```

**Critère de succès** : sur les 9 fichiers ci-dessous, **zéro** violation RULE-AST-02/03/04. Les violations RULE-AST-01 restantes sont HORS scope (ne pas tenter de découper ces modules).

---

## 1. Inventaire frais `code-check --all` (2026-09-23) — 13 violations / 9 fichiers

### A. RULE-AST-03 — `subprocess` sans timeout (4 sites / 3 fichiers)

| Fichier | Ligne | Appel | Classification | Action attendue |
|:---|:---:|:---|:---|:---|
| `src/bridges/mcp_crawler.py` | 38 | `subprocess.Popen(cmd, stdin/stdout/stderr=...)` puis `process.wait()` | **Cas MCP stdio** : le process vit tant que le client MCP — `wait()` sans bornes est intentionnel | `process.wait(timeout=<N>)` avec N grand mais fini (ex. `86400` = 24h) **ou** `# noqa: RULE-AST-03 (processus MCP stdio — durée de vie = session client)` sur la ligne du `Popen` si un timeout de wait est jugé incorrect. Préférer un `wait(timeout=...)` explicite si le pattern l'accepte. |
| `src/core/herdr_daemon.py` | 56 | `subprocess.Popen([self.herdr_bin, "server"], ...)` + `proc.wait(timeout=10)` déjà présent L64 | **Faux positif partiel** : `Popen` n'accepte pas `timeout=` ; l'attente bornée est via `wait(timeout=10)` L64. Le linter pointe le `Popen`. | Ajouter `# noqa: RULE-AST-03 (attente bornée via proc.wait(timeout=10) L64)` sur la ligne du `Popen` L56. **Ne pas** ajouter `timeout=` au `Popen` (TypeError). |
| `src/dashboard/routers/drawdb.py` | 154 | `subprocess.Popen(cmd, ...)` + boucle deadline `SPAWN_TIMEOUT_S` + `proc.poll()` | **Faux positif** : bornes via boucle `time.monotonic() < deadline` L162-164 | `# noqa: RULE-AST-03 (bornes via boucle deadline SPAWN_TIMEOUT_S + proc.poll())` sur L154. |
| `src/commands/handlers/plannotator.py` | 69 | `subprocess.run(cmd, cwd=cwd)` | **Vrai positif** | Ajouter `timeout=3600` (revue interactive longue). |
| `src/commands/handlers/plannotator.py` | 156 | `subprocess.run(cmd)` | **Vrai positif** | Ajouter `timeout=3600` (annotate interactif). |

> Note : le visiteur AST vérifie `kw.arg == "timeout"` sur l'appel lui-même. Pour `subprocess.run`, ajouter `timeout=<secondes>`. Pour `subprocess.Popen`, ne JAMAIS ajouter `timeout=` au constructeur (invalide) — utiliser `noqa` + trace de l'attente bornée existante.

### B. RULE-AST-02 — ressources nues (7 sites / 6 fichiers)

| Fichier | Ligne | Appel | Classification | Action attendue |
|:---|:---:|:---|:---|:---|
| `src/core/semantic_cache.py` | 40 | `sqlite3.connect` dans `@contextmanager _connection` | **Faux positif** : lifecycle = contextmanager + `finally: conn.close()` | `# noqa: RULE-AST-02 (géré via @contextmanager _connection)` sur L40. |
| `src/core/standards_graph.py` | 120 | `sqlite3.connect` dans `@contextmanager _get_connection` | **Faux positif** idem | `# noqa: RULE-AST-02 (géré via @contextmanager _get_connection)` sur L120. |
| `src/loop_mem/db.py` | 158 | `sqlite3.connect` dans `@contextmanager get_observation_db_session` | **Faux positif** idem | `# noqa: RULE-AST-02 (géré via @contextmanager get_observation_db_session)` sur L158. |
| `src/loop_mem/db.py` | 195 | `sqlite3.connect` dans `_get_observation_conn()` helper **legacy déprécié** (DeprecationWarning déjà émis) | **Vrai positif technique** mais helper déprécié ADR-0369 | `# noqa: RULE-AST-02 (helper legacy déprécié ADR-0369 — migrer les callers vers get_observation_db_session)` sur L195. **Ne pas** supprimer la fonction (rétrocompat). |
| `src/engine/agent_graph.py` | 47 | `sqlite3.connect` dans `_get_connection()` qui **retourne** la connexion (callers en try/finally) | **Vrai positif** — pattern retour brut | Refactorer `_get_connection` en `@contextmanager` (style `semantic_cache._connection`) et ajuster les callers dans ce fichier (`_init_db` L64, et tout autre usage de `_get_connection()`). Si le refactor est trop large pour le temps alloué : `# noqa: RULE-AST-02 (connexion managée par callers try/finally close)` + laisser une note dans le rapport. **Préférer le vrai refactor contextmanager.** |
| `src/loop_mem/rho_hybrid_search.py` | 243 | `sqlite3.connect` dans `_get_db_connection()` qui retourne la connexion | **Vrai positif** — idem agent_graph | Idem : refactor `@contextmanager` si callers contenus dans le fichier ; sinon `noqa` documenté. |
| `src/pipelines/crawler.py` | 857, 861 | `httpx.AsyncClient(...)` passé à `stack.enter_async_context(...)` dans `async with AsyncExitStack()` | **Faux positif** : lifecycle = `AsyncExitStack` | `# noqa: RULE-AST-02 (lifecycle géré via AsyncExitStack.enter_async_context)` sur L857 et L861. |

### C. RULE-AST-04 — `except` silencieux (2 sites / 1 fichier)

| Fichier | Ligne | Contexte | Action attendue |
|:---|:---:|:---|:---|
| `src/pipelines/struct_checker.py` | 886 | `except Exception:` + comment « Dégradation gracieuse » + `pass` (check C11 ADR malformé) | Remplacer `pass` par `logger.debug("...", exc_info=True, extra={"component": "pipelines.struct_checker", "operation": "_check_c11..."})`. Vérifier qu'un `logger` existe dans le module (sinon `get_logger` depuis `src.utils.logger`). |
| `src/pipelines/struct_checker.py` | 922 | `except Exception:` + comment « Dégradation gracieuse » + `pass` (check C12 DomainInvariant) | Idem : `logger.debug(..., exc_info=True, extra={...})`. |

---

## 2. Contraintes inviolables

1. **Ne pas** modifier `src/core/ast_checker.py` (ADR-0376 — audit 7 couches requis, hors mission P7).
2. **Ne pas** toucher aux fichiers dont la seule violation est RULE-AST-01 (dette modulaire → P5/P6).
3. **Ne pas** exécuter `git commit` / `git push`.
4. **Ne pas** introduire de `except Exception: pass` nu (ironie du sort).
5. **Timeout explicite** sur tout nouvel appel réseau/subprocess (ADR-0369 Std 3).
6. **Context managers** pour toute nouvelle ressource SQLite/HTTP si vous refactorisez (Std 2).
7. **`logger.debug(..., exc_info=True, extra={...})`** pour tout except traité (Std 4).
8. Préserver les signatures publiques et la rétrocompatibilité des imports.
9. Après chaque fichier : `python src/swarm.py code-check --file <path>` doit passer **sans RULE-AST-02/03/04** (RULE-AST-01 autorisé s'il préexistait).

---

## 3. Tests à lancer (au minimum)

```bash
python -m pytest tests/test_ast_checker.py -q
python -m pytest tests/ -k "semantic_cache or standards_graph or agent_graph or rho or struct_checker or plannotator or crawler or herdr" -q
python src/swarm.py code-check --all --project mLoop
```

Bilan attendu : les 9 fichiers cibles ne doivent plus apparaître en FAIL pour 02/03/04. Les autres FAIL (RULE-AST-01 monolithes) restent inchangés.

---

## 4. Livrable de fin de mission

Écrire `Projects/mLoop/memory/evidence/p7_ast_residuals_report.md` avec :
- Tableau fichier × violations avant/après (02/03/04).
- Liste des `# noqa` ajoutés + justification 1 ligne chacun.
- Liste des vrais refactors (contextmanager, timeout, logger).
- Sortie du `code-check --all` bilan (nombre de fichiers conformes).
- Sortie pytest pertinente.
- Anomalies éventuelles / hors scope rencontrées.

Puis répondre au canal principal : **P7 DONE** + résumé 5 lignes + chemin du rapport.
