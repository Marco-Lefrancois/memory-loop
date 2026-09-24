# Doubt-Driven Development Protocols & Cross-Model Reference

This reference document accompanies `.agents/skills/doubt-driven-development/SKILL.md`.

## 1. Adversarial Review Prompt Template

```markdown
Adversarial review. Find what is wrong with this artifact.
Assume the author is overconfident. Look for:
- Unstated assumptions
- Edge cases not handled
- Hidden coupling or shared state
- Ways the contract could be violated
- Existing conventions this might break
- Failure modes under unexpected input

Do NOT validate. Do NOT summarize. Find issues, or state
explicitly that you cannot find any after thorough examination.

ARTIFACT: <paste artifact>
CONTRACT: <paste contract>
```

---

## 2. Cross-Model CLI Escalation Shapes

```bash
# Codex CLI read-only review
codex exec --sandbox read-only -C <repo-path> - < /tmp/doubt-prompt.md

# Gemini CLI plan mode review
gemini --approval-mode plan -p "" < /tmp/doubt-prompt.md
```
