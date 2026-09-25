# Mission Worker — Validation E2E « Runtimes Workers Multi-CLI » (Cline / glm-5.3-flash)

**Projet** : mLoop
**Récit de rattachement** : MLOOP-109-BE (dette enregistrée) — validation du chantier amont
**Type de mission** : VALIDATION (lecture seule, **aucune modification de code**)
**Répertoire de travail** : `C:\Memory Loop`
**Date** : 2026-09-20

---

## 1. Contexte (faits, pas d'interprétation)

Le framework mLoop vient d'acquérir la capacité de faire tourner des workers Herdr sur **plusieurs CLI**
(avant : OpenCode uniquement). Deux commits locaux portent ce chantier :
- `b2830bd` — registre SSOT `src/core/worker_runtimes.py` + `src/core/cline_adapter.py` + entrée sonde Cline + tests
- `aba3d7a` — routage déclaratif de `src/core/herdr_adapter.py` + `src/commands/_registry.py`

Modèle par défaut attendu pour Cline : `nmedia_cloud/glm-5.3-flash`.

---

## 2. Mission (3 vérifications opposables)

1. **Non-régression des tests** — exécuter et rapporter la sortie brute :
   ```
   python -m pytest tests/test_worker_runtimes.py tests/test_cline_adapter.py tests/test_herdr_adapter.py tests/test_ast_checker.py -q
   ```
2. **Conformité AST déterministe** — exécuter et rapporter la sortie brute :
   ```
   python src/swarm.py code-check --file src/core/worker_runtimes.py
   python src/swarm.py code-check --file src/core/cline_adapter.py
   python src/swarm.py code-check --file src/core/agent_probe.py
   ```
3. **Contrat de flags par runtime** — vérifier par lecture (commandes read-only proposées) :
   ```
   python -c "from src.core.worker_runtimes import WORKER_RUNTIMES as W; [print(k, '| one_shot=', v.one_shot_flags, '| model=', v.default_model) for k, v in sorted(W.items())]"
   python -c "from src.core.worker_runtimes import get_worker_runtime as g; print(g('cline').build_flags(model=g('cline').default_model)); print(g('opencode').build_flags(model='nmedia_cloud/claude-opus-4.8'))"
   ```
   Attendu : `cline` → `['--model', 'nmedia_cloud/glm-5.3-flash']` ; `opencode` → `['--yolo', '--model', 'nmedia_cloud/claude-opus-4.8']` (sémantique historique préservée).

---

## 3. Livrable obligatoire

Créer **un seul** fichier : `Projects/mLoop/memory/worker_MLOOP-109-BE_validation.md` contenant :
- `VERDICT:` (PASS / FAIL / PASS_WITH_RESERVES)
- `EVIDENCE:` commandes exactes exécutées + extraits de sortie **verbatim** (pas de paraphrase)
- `ANOMALIES:` tout écart constaté, ou `Aucune`
- `RECOMMANDATIONS:` actions concrètes
- Dernière ligne du fichier : `STATUS: COMPLETED`

---

## 4. Contraintes strictes

- **Interdiction absolue de modifier, créer ou supprimer du code** (`src/`, `tests/`, `standards/`) : mission read-only.
- **Interdiction de committer** (aucun `git commit`/`git push`).
- Si une commande échoue, **la rapporter telle quelle** (sortie brute) — aucune complaisance, aucune invention de résultat.
- Ne pas inventer de faits : tout constat doit provenir d'une commande réellement exécutée.
