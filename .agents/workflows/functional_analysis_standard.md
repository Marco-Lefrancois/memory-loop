# Standard Functional Analysis Workflow

Standard Spec-Driven lifecycle for functional analysis (Analyze-Plan-QA).

## Workflow Steps

1. **Phase 1: Ingestion & Modeling (Analyze)**
   - Execute ingestion and knowledge graph update via `python src/swarm.py ingest`.
   - Update semantic graph with `python src/swarm.py sync`.

2. **Phase 2: Planning & Clarification (Plan)**
   - Run interactive interrogation session using `python src/swarm.py grill`.
   - Draft `implementation_plan.md` following the Plan-First protocol.
   - Resolve decisions and document ADR entries in `docs/01-architecture/`.

3. **Phase 3: Backlog & Specification (Build/Spec)**
   - Create or update user stories in `backlog/stories/` using standard blueprints (`story_template_FE.md` / `story_template_BE.md`).
   - Formulate 4 Gherkin pillars (Nominal, Exceptions, Resilience, UX/Observability).

4. **Phase 4: QA Audit & INVEST Scoring (Validate)**
   - Audit semantic integrity and Gherkin rules using `python src/swarm.py wikifix`.
   - Validate persistent state governance with `python src/swarm.py aoep`.
