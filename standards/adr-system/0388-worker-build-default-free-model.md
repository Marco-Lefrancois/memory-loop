# 🏛️ ADR-0388 : Bascule du Modèle par Défaut de la Mission `build` vers le Free Tier Natif OpenCode (MiMo-V2.6-Flash Free)

## Statut
**Accepté** — 24 septembre 2026

## Contexte & Problématique

La mission `build` (développement de code applicatif mLoop et exécution `worker-spawn` sans `--task-type` explicite) était routée par défaut vers `nmedia_cloud/claude-sonnet-4.6`, un modèle payant via le proxy LiteLLM NMedia Cloud (ADR-0338).

Or, un précédent architectural existe déjà dans `src/core/worker_runtimes.py` : le runtime **Cline** utilise nativement `cline-free/deepseek-v4.1-flash` (`DEFAULT_CLINE_MODEL`), un modèle **gratuit hors LiteLLM**, sans que cela ne viole la règle « Zéro Binaire Externe Non Configuré » d'AGENTS.md — car ce modèle n'est pas un binaire externe non configuré, mais un tiers gratuit **natif** au runtime CLI lui-même.

OpenCode expose de façon similaire un catalogue de modèles gratuits natifs (`opencode models`), incluant `opencode/mimo-v2.6-flash-free`, résolvable sans configuration de provider additionnelle (aucune clé API requise, contrairement à `nmedia_cloud`).

**Demande opérationnelle** : faciliter le développement quotidien et les sessions `worker-spawn` en réduisant le coût et la friction budgétaire, sans dégrader les portes de qualité contradictoires (`validation`, `deepening`) qui exigent un raisonnement de pointe.

## Décision d'Architecture

### 1. Bascule Ciblée de `TASK_MODEL_MAP["build"]`
Dans les deux miroirs SSOT (`src/core/herdr_worker_core.py` et la classe `HerdrWorkerMixin` de `src/core/herdr_worker.py`) :

```python
TASK_MODEL_MAP = {
    "deepening": "nmedia_cloud/claude-opus-4.8",       # INCHANGÉ — porte qualité
    "validation": "nmedia_cloud/gpt-5.6-terra-thinking", # INCHANGÉ — porte qualité
    "deepsearch": "nmedia_cloud/claude-sonnet-5",        # INCHANGÉ — porte qualité
    "build": "opencode/mimo-v2.6-flash-free",            # ⬅ MODIFIÉ (ADR-0388)
    "compaction": "nmedia_cloud/gemini-3.8-flash",       # INCHANGÉ — porte qualité
}
```

### 2. Parité des Consignes Agent (3 couches)
- `opencode.json` : `agent.worker.model` et `agent.build.model` → `opencode/mimo-v2.6-flash-free`.
- `.agents/agents/worker.md` : frontmatter `model: mimo-v2.6-flash-free`.
- `.agents/com.nmedia.opencode/agents.json` : `build.model` → `opencode/mimo-v2.6-flash-free`.

### 3. Invariant Préservé — `runtime_spec.default_model` du runtime `opencode` reste `None`
La logique de précédence dans `spawn_story_worker_impl` (`src/core/herdr_worker_core.py`) applique :

```python
target_model = model or (TASK_MODEL_MAP.get(task_type.lower()) if task_type else None)
if runtime_spec is not None and runtime_spec.default_model and not model:
    target_model = runtime_spec.default_model
```

Fixer un `default_model` sur `WORKER_RUNTIMES["opencode"]` **écraserait** systématiquement la sélection `TASK_MODEL_MAP` pour **tous** les task-types dès lors qu'aucun `--model` explicite n'est fourni — y compris `validation` et `deepening`, qui exigent des modèles de raisonnement de pointe. Cette option a été **explicitement rejetée** (cf. `tests/test_worker_runtimes.py::test_opencode_has_no_default_model`, invariant préservé).

### 4. Portes Qualité Non Affectées
`agent.orchestrator`, `agent.plan`, `agent.sentinel` dans `opencode.json`, ainsi que `TASK_MODEL_MAP["deepening"|"validation"|"deepsearch"|"compaction"]`, demeurent strictement sur leurs modèles LiteLLM nmedia_cloud (Trio d'Or ADR-0338).

## Statut d'Alignement & Fichiers Modifiés
- `src/core/herdr_worker_core.py` (SSOT `TASK_MODEL_MAP`)
- `src/core/herdr_worker.py` (miroir `HerdrWorkerMixin.TASK_MODEL_MAP`)
- `opencode.json` (`agent.worker.model`, `agent.build.model`)
- `.agents/agents/worker.md` (frontmatter `model`)
- `.agents/com.nmedia.opencode/agents.json` (`build.model`)
- `tests/test_worker_runtimes.py` (tests de parité `test_task_model_map_build_uses_free_opencode_model`, `test_task_model_map_core_mixin_parity`)
- Amendements documentaires : `standards/adr-system/0346-specialized-agent-delegation-gates.md` (§L47), `standards/adr-system/0338-nmedia-cloud-litellm-pricing-forensics.md` (note de portée), `docs/06-knowledge/04-model-governance/KN-030_litellm_model_routing_pricing.md`.

## Conséquences

### Positives
- **Coût nul** pour le développement quotidien (`build`) et les `worker-spawn` sans `--task-type`.
- **Zéro régression de gouvernance** : les 4 autres task-types et les agents primaires (orchestrator/plan/sentinel) restent sur les modèles LiteLLM certifiés (ADR-0338).
- **Cohérence architecturale** : extension du pattern déjà validé pour Cline (`DEFAULT_CLINE_MODEL`) au runtime OpenCode, sans nouvelle branche conditionnelle.

### Risques & Mitigation
- **Risque qualité** : un modèle free tier peut sous-performer sur du code complexe. Mitigation : rollback documenté à 1 ligne par fichier (revert direct de ce diff) ; `--model` explicite reste toujours disponible en override ponctuel (`worker-spawn --model nmedia_cloud/claude-sonnet-5`).
- **Non couvert par cet ADR** : aucun benchmark qualitatif MiMo-V2.6-Flash vs Claude Sonnet 4.6 n'a été mené (hors périmètre ; un spike dédié pourrait être engagé séparément si une régression est constatée en usage réel).

## Références
- ADR-0338 (Gouvernance Modèles LiteLLM & Pricing Forensics) — Trio d'Or préservé pour orchestrator/plan/sentinel.
- ADR-0346 (Suite des 5 Workers Stratégiques Spécialisés) — §L47 amendé.
- ADR-0369 (Standards de Robustesse Python Senior) — aucune violation introduite.
- `src/core/worker_runtimes.py` — pattern `DEFAULT_CLINE_MODEL` étendu par précédent.
