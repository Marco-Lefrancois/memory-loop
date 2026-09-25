---
created: 2026-09-16T14:46:34.817Z
source: plannotator
tags: [plannotator, memory-loop, correction, des, lacunes]
---

[[Plannotator Plans]]

# Plan — Correction des lacunes d'outillage Herdr (L-01, L-02)

## Contexte
Le test de délégation sur SHOP-303 a révélé 2 frictions d'orchestration rendant la supervision « à l'aveugle ». Correction dans le code framework `src/` (exception d'herméticité auto-développement). TDD + ADR-0369.

## Diagnostic racine (vérifié dans le code)

**L-02 (harvest contradictoire) — LE VRAI BUG :**
- `harvest_story_evidence` (`herdr_adapter.py:805`) lit le PTY via `read_agent_output`.
- Si le worker est encore actif, la lecture `recent-unwrapped` échoue (`agent_not_idle`), l'adapter fait un **fallback silencieux sur `visible`** (l.407-425) qui réussit.
- Résultat : `harvest` retourne **toujours** `success: True` (l.858) SANS signaler que la moisson est **partielle/prématurée**. D'où le message contradictoire (`agent_not_idle` loggé + « Moisson réussie »).

**L-01 (`worker-wait` timeout) :**
- L'adapter `wait_for_agent` (l.373-380) gère **déjà** proprement le timeout (retourne `working`/`timed_out`). Le problème n'est PAS là.
- Le `worker-wait` que j'ai appelé passe par le **MCP Herdr direct** (`cli:agent:wait`), pas par cet adapter Python. => hors du code mLoop, c'est le binaire Herdr. **Non corrigeable côté mLoop** ; on documente le contournement.

## Modifications (2 fichiers `src/` + 1 fichier de test)

### A. `src/core/herdr_adapter.py` — `read_agent_output` (l.383-426)
Exposer explicitement quand le worker était actif pendant la lecture :
- Quand le fallback `visible` est déclenché par `agent_not_idle`, ajouter au résultat : `res["worker_was_active"] = True` (en plus du `source_fallback` déjà présent).
- Log DEBUG contextualisé conservé (ADR-0369, pas de `except: pass`).

### B. `src/core/herdr_adapter.py` — `harvest_story_evidence` (l.805-865)
- Récupérer `worker_was_active` / `source_fallback` depuis `read_res`.
- Ajouter au dict de retour : `"partial_harvest": bool`, `"worker_active_during_harvest": bool`.
- Écrire ces marqueurs dans l'EvidencePack (`harvest_status = "PARTIAL"` si actif, sinon `"COMPLETED"`).
- **Ne PAS** transformer en échec (le fallback visible reste un résultat exploitable) — juste signaler la nature partielle.

### C. `src/pipelines/worker_pipeline.py` — `run_worker_harvest` (l.122-126)
- Si `res.get("partial_harvest")` : afficher un **avertissement clair** au lieu du « Moisson réussie » trompeur :
  `ZeroFluffConsole.warning("Moisson PARTIELLE : le worker était encore actif (capture 'visible'). Relancer harvest après fin d'exécution pour une moisson complète.")`
- Sinon, message de succès normal inchangé.

### D. `tests/test_specialized_workers.py` — nouveaux tests (TDD, ADR-0369 Failure Contract)
- `test_harvest_flags_partial_when_worker_active` : mocke `read_agent_output` renvoyant `worker_was_active=True` → assert `res["partial_harvest"] is True` et `harvest_status == "PARTIAL"`.
- `test_harvest_complete_when_worker_idle` : lecture normale → `partial_harvest is False`, `harvest_status == "COMPLETED"`.
- `@pytest.mark.parametrize` sur les 2 cas.

## Ce que je NE fais PAS
- Aucune modification du binaire Herdr (hors périmètre mLoop).
- Aucun changement de signature CLI (pas de `guide --sync` requis, `_registry.py` intouché).
- Aucune régression sur le chemin nominal (worker idle => comportement identique).

## Validation post-correction
1. `python -m pytest tests/test_specialized_workers.py -v` (nouveaux tests + non-régression).
2. `python src/swarm.py vibe-check --project Shopify_AI_Item_Creator` (17/17).
3. Mise à jour du journal `memory/herdr_delegation_validation.md` : L-02 → corrigé, L-01 → documenté (hors mLoop), L-03/L-04 (conventions) traités séparément.

## Note sur L-03 (nommage) & L-04 (format liens)
Ce sont des conventions de **prompt de délégation**, pas des bugs de code. Je propose de les traiter en ajustant le prompt worker (harmoniser nommage par `id` + format de citation standard) plutôt que par du code — à valider séparément.

## Question pour toi
Après cette correction de code, je reprends la **délégation Herdr** pour la suite de la Phase 1 (SHOP-401, 402, 501, 502, 601, 602, 603) en appliquant les contournements — confirmes-tu cet enchaînement ?