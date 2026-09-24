# Browser Testing with DevTools Recipes & Reference

This reference document accompanies `.agents/skills/browser-testing-with-devtools/SKILL.md`.

## 1. Structured Test Plan Template

```markdown
## Test Plan: Task completion animation bug

### Setup
1. Navigate to http://localhost:3000/tasks
2. Ensure at least 3 tasks exist

### Steps
1. Click the checkbox on the first task
   - Expected: Task shows strikethrough animation, moves to "completed" section
   - Check: Console should have no errors
   - Check: Network should show PATCH /api/tasks/:id with { status: "completed" }

2. Click undo within 3 seconds
   - Expected: Task returns to active list with reverse animation
   - Check: Console should have no errors
   - Check: Network should show PATCH /api/tasks/:id with { status: "pending" }

3. Rapidly toggle the same task 5 times
   - Expected: No visual glitches, final state is consistent
   - Check: No console errors, no duplicate network requests
   - Check: DOM should show exactly one instance of the task

### Verification
- [ ] All steps completed without console errors
- [ ] Network requests are correct and not duplicated
- [ ] Visual state matches expected behavior
- [ ] Accessibility: task status changes are announced to screen readers
```

---

## 2. DevTools Diagnostics Matrix

| Diagnostic | Tool | Threshold / Expectation |
|------------|------|-------------------------|
| Console Errors | Console Monitor | 0 uncaught exceptions or error-level logs |
| Layout Shifts | Performance Trace | CLS < 0.1 |
| Load Latency | Network Monitor | LCP < 2.5s, no duplicate API calls |
| Accessibility | A11y Tree | WCAG 2.1 AA compliant, valid aria-labels |
