# Guidelines de Développement & Core Capabilities

## Zero-Bloat Swarm Autonomous Guidelines

### 1. Zero-Fluff Standard
- **Low Noise / High Signal**: All console logs, reports, and system notifications must be purely textual, concise, and focused on operational indicators. Avoid animations, progress bars, or ASCII decoration.
- **Kernel-Pipeline Awareness**: Agents must recognize that logic is decoupled from `src/swarm.py`. If a behavior needs changing, look into `src/pipelines/` or `.agents/skills/`.
- **French Technical Language**: Use professional, clear, and concise technical French for user-facing terminal logs, comments, and project documents.
- **Windows CP1252 Compliance**: Ensure all console logs emitted via `src/cli.py` use CP1252-compatible terminal symbols to prevent `UnicodeEncodeError` exceptions on Windows environments.

### 2. Permissions & Safe Invocations
- **Windows CLI Execution**: When running JavaScript or Python scripts, always prefix with the explicit executor (e.g. `node relative/path/to/file.js` or `python relative/path/to/file.py`) to prevent OS-level dialog interruptions.
- **Frictionless AFK Tasks**: Leverage the background execution of tasks to proceed with long-running tests or RAG compilation without blocking the user interface.

### 3. Standards de Documentation (Gherkin)
- **Couverture par Piliers** : Toute Story doit impérativement respecter le Manifeste Qualité Gherkin (`standards/GHERKIN_GUIDELINES.md`).
- **Audit de Scénarios** : Lors de la phase d'analyse, l'agent doit systématiquement vérifier qu'il a couvert le chemin nominal, les exceptions métier, les cas limites techniques et le comportement UX.
- **Liaison RM** : Les scénarios d'exception métier doivent explicitement mentionner l'identifiant de la règle métier (ex: RM-REC-008) qu'ils valident.

## Core Capabilities Leveraged in mLoop

### Native Thinking Process (System 2 Cognitive Power)
When executing Cloud Architect System 2 tasks (DDD, Tree of Thoughts, MCTS convergence):
- **Thinking Budget Allocation**: Always utilize the thinking budget to explore parallel design decisions and evaluate trade-offs before saving structural decisions to the codebase.
- **Non-Speculative Convergence**: Calculate feasibility scores based on empirical scout reports instead of guessing the filesystem state.

### Asymmetric Dual-Path (System 1 execution)
When executing local physical tasks via the System 1 Scout & Dev Engine:
- **Tool-First Grounding**: Always run a static verify or directory listing tool before proposing code changes to prevent missing import exceptions.
- **Strict Interface Alignment**: Every code block written in `src/` must be mapped to a specific story (e.g. `// [US-XXX]`) and validated against Pydantic schema contracts.
