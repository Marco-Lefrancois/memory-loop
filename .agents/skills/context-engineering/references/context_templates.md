# Context Engineering Templates & Best Practices

This reference document accompanies `.agents/skills/context-engineering/SKILL.md`.

## 1. Project Rules File Template (CLAUDE.md / AGENTS.md)

```markdown
# Project Rules & Technical Profile

## Tech Stack
- Python 3.11+, pytest, Pydantic v2, SQLite FTS5

## Core Commands
- Sync: `python src/swarm.py sync --project mLoop`
- Test: `pytest tests/`
- Vibe-check: `python src/swarm.py vibe-check --project mLoop`

## Behavioral Boundaries
- Zero local hardcoded absolute paths (`file:///C:`).
- Maximum 300 physical lines per SKILL.md (ADR-0202).
- Palier 1 stories locked in DRAFT with `grill_me: PENDING`.
```

---

## 2. Context Packing Ratios

| Layer | Priority | Retention Strategy |
|-------|----------|--------------------|
| Rules & Constraints | P0 (Highest) | Pinned throughout session |
| Relevant Spec Slice | P1 | Scoped to active task only |
| Source Files Under Edit | P2 | Read fresh from disk before edit |
| Execution Output | P3 | Truncated to relevant error stack |
| Chat History | P4 (Lowest) | Compacted at task boundaries |
