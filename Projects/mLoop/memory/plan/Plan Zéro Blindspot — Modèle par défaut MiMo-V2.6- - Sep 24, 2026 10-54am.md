---
created: 2026-09-24T14:54:22.399Z
source: plannotator
tags: [plannotator, memory-loop, blindspot, mod, par]
---

[[Plannotator Plans]]

# Plan Zéro Blindspot — Modèle par défaut MiMo-V2.6-Flash Free pour le développement & worker-spawn

## 0. Contexte & Demande

**Demande utilisateur** : faciliter le développement et le `worker-spawn` en positionnant par défaut (ou en changeant la consigne de modèle) le modèle **MiMo-V2.6-Flash Free**.

**Identifiant modèle confirmé** (Niveau 1 — `opencode models`) : `opencode/mimo-v2.6-flash-free`

**Boot Sequence** : ✅ resume / vibe-check (22 PASS / 1 WARNING) / lifecycle-status — projet `mLoop` (STAGE_5_SHIP).

---

## 1. Faits Établis (Dossier de Preuves)

### Extrait 1 — Chaîne de sélection du modèle worker (`src/core/herdr_worker_core.py`, L60-78)
> `target_model = model or (TASK_MODEL_MAP.get(task_type.lower()) if task_type else None)` … `if runtime_spec is not None and runtime_spec.default_model and not model: target_model = runtime_spec.default_model`

➡️ Fait établi : priorité = `--model` explicite > `runtime_spec.default_model` (si non nul) > `TASK_MODEL_MAP[task_type]`.

### Extrait 2 — TASK_MODEL_MAP actuel (SSOT doublon, L18-24 core + L24-30 mixin)
> `"build": "nmedia_cloud/claude-sonnet-4.6"` (idem dans `herdr_worker.py`)

➡️ Fait établi : la mission `build` coûte actuellement du LiteLLM payant.

### Extrait 3 — Runtime opencode sans default_model (`src/core/worker_runtimes.py`, L110-117 + test L62-64)
> `"opencode": WorkerRuntimeSpec(...)` — pas de `default_model` ; test `test_opencode_has_no_default_model` enforce `None` (« la sélection reste TASK_MODEL_MAP »).

➡️ Fait établi : fixer `default_model` sur le runtime opencode **écraserait** TOUTES les valeurs `TASK_MODEL_MAP` (validation/deepening incluses) via L77-78 → **solution rejetée** (break governance ADR-0346).

### Extrait 4 — Consignes agent amont
- `opencode.json` → `agent.worker.model = "nmedia_cloud/claude-sonnet-4.6"`
- `.agents/agents/worker.md` → `model: claude-sonnet-4.6`
- `.agents/com.nmedia.opencode/agents.json` → `build` / `sentinel` = `nmedia_cloud/claude-sonnet-4.6`

➡️ Fait établi : 3 couches de consigne doivent rester en parité.

### Extrait 5 — Modèle gratuit disponible (preuve d'appel)
> `opencode models` liste `opencode/mimo-v2.6-flash-free`.

➡️ Fait établi : le modèle est résolvable sans configuration provider additionnelle.

### Extrait 6 — Frontière LiteLLM vs modèles natifs gratuits
- AGENTS.md : « Passer exclusivement par le proxy LiteLLM (`nmedia_cloud/<modele>`) » pour les **binaires externes non configurés**.
- Précedent SSOT : `DEFAULT_CLINE_MODEL = "cline-free/deepseek-v4.1-flash"` (natif gratuit hors nmedia_cloud, `worker_runtimes.py` L30-37).

➡️ Fait établi : un modèle natif gratuit hors LiteLLM est déjà constitutionnel pour un runtime worker (pattern Cline).

---

## 2. Matrice de Résolution des Conflits

| Conflit | Résolution |
| :--- | :--- |
| Free model vs ADR-0338 (Trio d'Or LiteLLM) | ADR-0338 reste SSOT pour l'**orchestrateur/plan/sentinel** ; le bascuile ne touche que la voie `build`/`worker` (ganterie de coût). Légitimé par le pattern Cline free. |
| Free model vs ADR-0346 (build → claude-sonnet-4.6) | ADR-0346 §L47 : mise à jour documentaire obligatoire (amendement ou ADR successeur). |
| `runtime.default_model` vs `TASK_MODEL_MAP` | Ne PAS fixer `default_model` sur le runtime opencode (cf. Extrait 3) — casserait validation/deepening. |
| `deepening`/`validation`/`deepsearch`/`compaction` | **Conservés sur LiteLLM** (portes qualité : Opus 4.8, Terra-Thinking, Sonnet-5, Gemini-3.8-Flash). Seul `build` bascule. |
| ID modèle `opencode/…` vs `nmedia_cloud/…` | Utiliser l'ID complet `opencode/mimo-v2.6-flash-free` (conforme output `opencode models` et flag `--model`). |

---

## 3. Périmètre des Modifications (Matrice [NEW]/[MODIFY]/[DELETE])

### 🔵 Couche Core Python
1. **[MODIFY] `src/core/herdr_worker_core.py`** — `TASK_MODEL_MAP["build"]` → `"opencode/mimo-v2.6-flash-free"`
2. **[MODIFY] `src/core/herdr_worker.py`** — miroir `HerdrWorkerMixin.TASK_MODEL_MAP["build"]` → idem (parité stricte du doublon existant)
3. **[NO-CHANGE] `src/core/worker_runtimes.py`** — aucun changement (default_model opencode reste `None` par design)
4. **[NO-CHANGE] `src/commands/_registry/_reg_workers.py`** — aucun arg ajouté → **pas de `guide --sync` requis** (ADR-0370)

### 🟢 Consignes Agent (parité 3 couches)
5. **[MODIFY] `opencode.json`** — `agent.worker.model` → `"opencode/mimo-v2.6-flash-free"`
6. **[MODIFY] `opencode.json`** — `agent.build.model` → `"opencode/mimo-v2.6-flash-free"` (faciliter le dev comme demandé)
7. **[MODIFY] `.agents/agents/worker.md`** — frontmatter `model: mimo-v2.6-flash-free`
8. **[MODIFY] `.agents/com.nmedia.opencode/agents.json`** — `build.model` → `"opencode/mimo-v2.6-flash-free"` ; `sentinel.model` **inchangé** (revue contradictoire = porte qualité)

### 🟡 Tests
9. **[MODIFY] `tests/test_worker_runtimes.py`** — aucune altération du test `test_opencode_has_no_default_model` (invariant préservé)
10. **[NEW] assertion parité** — test unitaire validant `TASK_MODEL_MAP["build"] == "opencode/mimo-v2.6-flash-free"` et parité mixin/core (dans un fichier test existant ou extension de `test_herdr_adapter.py`)
11. **[VERIFY] `tests/test_worker_spawn_lifecycle_gating.py`**, **`tests/test_specialized_workers.py`** — relecture pour détecter tout assert sur l'ancien modèle build

### 🟠 Architecture & Documentation (7 couches ADR-0376)
12. **[NEW] ADR** — `standards/adr-system/0388-worker-build-default-free-model.md` : décision Type 1 (bascule build/worker → MiMo free, préservation des portes qualité, pattern Cline étendu à OpenCode)
13. **[MODIFY] `standards/adr-system/README.md`** — indexation ADR-0388
14. **[MODIFY] `standards/adr-system/0346-specialized-agent-delegation-gates.md`** — L47 : note d'amendement `claude-sonnet-4.6` → `mimo-v2.6-flash-free` (build)
15. **[MODIFY] `standards/adr-system/0338-nmedia-cloud-litellm-pricing-forensics.md`** — note de portée : Trio d'Or inchangé pour orchestrator/plan/sentinel ; voie build/worker déléguée au free tier
16. **[MODIFY] `docs/06-knowledge/04-model-governance/KN-030_litellm_model_routing_pricing.md`** — matrice de sélection : ligne build/worker → free tier

### 🔴 Intentionnellement Hors Périmètre (Admission of Limits)
- `agent.orchestrator` / `agent.plan` / `agent.sentinel` dans `opencode.json` : **inchangés** (portes de gouvernance ADR-0338/0346).
- Top-level `model` / `small_model` : **inchangés** (sécurité de l'orchestration principale).
- `TASK_MODEL_MAP` hors `build` : **inchangé**.
- Aucun push Git / Jira / sync externe sans instruction explicite.

---

## 4. Plan d'Exécution (séquence)

1. Éditer les 2 miroirs `TASK_MODEL_MAP` (core + mixin) — atomique.
2. Éditer les 3 consignes agent (`opencode.json` ×2 clés, `worker.md`, `agents.json`) — atomique.
3. Rédiger ADR-0388 + index README + amendments ADR-0346/0338 + KN-030.
4. Ajouter test de parité build→free.
5. **Vérification** :
   - `pytest tests/test_worker_runtimes.py tests/test_herdr_adapter.py tests/test_worker_spawn_lifecycle_gating.py tests/test_specialized_workers.py -q`
   - Suite complète `pytest -q` (Gate C parité).
   - `python src/swarm.py vibe-check --project mLoop`
   - Appel d'épreuve : `python src/swarm.py worker-spawn --project mLoop --story <ID_test> --task-type build` (dry inspection du modèle rapporté) si un récit test est disponible, sinon vérification unitaire du dict.
6. `graphify update .` (AST-only) pour fraîcheur du graphe.

---

## 5. Stratégie de Délégation (DELEGATION GATE)

- **Volume ≥ 3 fichiers → OUI** → après approbation du plan, exécution via `worker-spawn --task-type build` (modèle free justement) **ou** exécution directe thread principal si l'humain le préfère (justification : édition config atomique multi-couche sensible à la répartition — à trancher à l'approbation).
- Teardown : `worker-harvest` → `worker-close` → `worker-status` avant fin de tour si délégué.

---

## 6. Critères d'Acceptation

- [ ] `TASK_MODEL_MAP["build"]` (core + mixin) = `opencode/mimo-v2.6-flash-free`
- [ ] `opencode.json` agent.worker + agent.build = free model
- [ ] `.agents/agents/worker.md` + `agents.json` build = free model (parité)
- [ ] Portes qualité intactes : validation/deepening/deepsearch/compaction/sentinel inchangés
- [ ] `runtime opencode.default_model` toujours `None`
- [ ] ADR-0388 créé + README indexé + amendments ADR-0346/0338/KN-030
- [ ] Tests verts (ciblés + suite complète)
- [ ] Vibe-Check ≥ 22 PASS, 0 FAIL

---

## 7. Frontière Active & Risques

- **Risque** : un test non détecté assert l'ancien modèle → mitigation : grep assert `claude-sonnet-4.6` dans `tests/` avant édition.
- **Risque** : `agent.build` free tier moins robuste pour code complexe → rollback documenté : 1 ligne dans `opencode.json` + 2 dans `TASK_MODEL_MAP`.
- **Non couvert** : pas de benchmark qualité MiMo vs Sonnet dans ce plan (hors scope ; option spike séparé si souhaité).
