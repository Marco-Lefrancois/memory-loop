---
name: doubt-driven-development
description: Subjects every non-trivial decision to fresh-context adversarial review. Use when stress-testing architectural decisions, high-stakes code, or plans for hidden failure modes before finalizing.
---

# Doubt-Driven Development

A confident answer is not a correct one. Doubt-driven development subjects non-trivial decisions to an adversarial reviewer biased to disprove assumptions while course correction is cheap.

## 1. Ground Truth & Repository Anchoring (SSOT & Evidence)

All doubts and claims must be reconciled against verifiable repository artifacts (SSOT & evidence factuelle) :
- Architectural decisions and blueprints: consult [standards/blueprints/](standards/blueprints/) and [Projects/](Projects/).
- Automated test suites and regression logs: verify directly in [tests/](tests/) and execution traces.
- Adversarial prompt templates and escalation recipes: see [references/doubt_protocols.md](references/doubt_protocols.md).

---

## 2. Core Execution Protocol

Follow these ordered steps sequentially:

### Étape 1 : Formulate the Claim (CLAIM)
State the decision, assumption, or invariant explicitly in 2-3 lines:
- Name what is claimed and why failure would be catastrophic or hard to detect in QA.
- If the claim cannot be articulated compactly, clarify the decision before proceeding.

### Étape 2 : Extract Isolated Artifact & Contract (EXTRACT)
Isolate the exact subject under review without your reasoning history:
- Pass only the specific diff, function, or proposal alongside the target contract.
- Strip conversational rationalizations so the reviewer evaluates the artifact objectively.

### Étape 3 : Invoke Adversarial Fresh-Context Review (DOUBT)
Prompt a reviewer agent whose sole instruction is to find failure modes, unstated assumptions, or contract violations:
- Instruct the reviewer to disprove, never to validate or flatter.
- In interactive sessions, offer cross-model second opinions where stakes warrant.

### Étape 4 : Reconcile Findings (RECONCILE)
Classify each finding strictly against the artifact text:
- Refactor code or update specs to eliminate verified failure modes.
- Dismiss false positives only with explicit physical counter-evidence.

### Étape 5 : Termination & Convergence (STOP)
- Stop the cycle when all valid findings are addressed or a maximum of 3 iterations is reached.
- Run complete regression suites in `tests/` before marking the decision final.

---

## 3. Prescriptive Rules & Garde-fous

### Rules & Garde-fous (DO NOT / NEVER)
- **Règle 1** : DO NOT pass your own justification or conclusion to the adversarial reviewer.
- **Règle 2** : DO NOT run doubt cycles on trivial mechanical edits (renaming, formatting).
- **Règle 3** : NEVER allow personas to spawn recursive subagent trees; doubt cycles must be orchestrator-driven.
- **Règle 4** : DO NOT dismiss adversarial findings without verifiable physical evidence in code or tests.

---

## 4. Gestion des erreurs, résilience et fallback

- **Comportement en cas d'erreur ou d'échec du reviewer** : Si l'agent reviewer subit un timeout ou échoue, ré-émettre la requête avec un contexte encore plus réduit (diff focalisé).
- **Fallback en environnement imbriqué (sans subagents)** : Si l'environnement interdit le spawn de sous-agents, appliquer un fallback par auto-questionnement adversarial explicite avec un prompt hermétique sans masquer la dégradation.
- **Gestion des exceptions d'exécution** : Toute exception levée lors de l'appel d'outils d'évaluation externes doit interrompre le cycle et alerter l'utilisateur.
