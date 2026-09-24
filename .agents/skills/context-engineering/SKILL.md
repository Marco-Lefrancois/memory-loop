---
name: context-engineering
description: Optimizes agent context setup. Use when configuring LLM context, managing token budgets, or structuring project rules to maximize reasoning accuracy and eliminate hallucinations.
---

# Context Engineering

Curate and structure context deliberately to maximize agent reasoning accuracy, maintain token economy, and eliminate hallucinations across sessions.

## 1. Ground Truth & Repository Anchoring (SSOT & Evidence)

All injected context must be grounded in physical repository artifacts (SSOT & evidence factuelle) :
- Project rules and blueprints: consult [standards/blueprints/](standards/blueprints/) and [Projects/](Projects/).
- Verifiable test results and logs: inspect [tests/](tests/) and execution traces.
- Context templates and packing ratios: see [references/context_templates.md](references/context_templates.md).

---

## 2. Core Execution Protocol

Follow these ordered steps sequentially:

### Étape 1 : Persistent Rules & Constraints Curation
Pin immutable project conventions and repository guardrails at the highest priority:
- Ensure project instructions (`AGENTS.md`, `CLAUDE.md`, `CONSTRAINTS.md`) are concise and unambiguous.
- Never duplicate knowledge that can be read on demand from the filesystem.

### Étape 2 : Task-Scoped Spec Slicing
Inject only the minimal relevant specification for the immediate task:
- Extract the specific user story or task acceptance criteria rather than dumping entire epics.
- Reference canonical paths rather than embedding massive redundant code blocks.

### Étape 3 : Fresh Code & Evidence Inspection
Read actual source files directly from disk immediately prior to making edits:
- Never rely on conversational memory or stale context for existing code signatures.
- Inspect neighboring implementations to match exact project patterns and typing styles.

### Étape 4 : Error Isolation & Token Compaction
- Feed targeted error lines rather than multi-thousand-line terminal outputs.
- Compact or restart conversation sessions cleanly at completed task boundaries to prevent attention degradation.

---

## 3. Prescriptive Rules & Garde-fous

### Rules & Garde-fous (DO NOT / NEVER)
- **Règle 1** : DO NOT dump full repositories or entire multi-thousand-line files into context when a focused slice suffices.
- **Règle 2** : DO NOT trust unverified assumptions — always read target files from disk first.
- **Règle 3** : NEVER allow conversational context to override explicit repository rules files.
- **Règle 4** : DO NOT carry forward stale conversation traces across unrelated work streams.

---

## 4. Gestion des erreurs, résilience et fallback

- **Comportement en cas d'erreur ou d'échec de lecture** : Si un fichier source requis est introuvable ou illisible, l'agent doit lever une exception explicite et interroger l'arborescence plutôt qu'halluciner son contenu.
- **Fallback en cas de dépassement de fenêtre de contexte** : Si le budget de jetons est saturé, appliquer une dégradation ordonnée en éliminant les traces historiques secondaires tout en préservant les règles (`CONSTRAINTS.md`) et la spécification active.
- **Gestion des outils absents** : Si un outil de recherche ou d'indexation échoue, basculer immédiatement en fallback sur la recherche textuelle native (`grep` ou parcours de fichiers).
