# Test-Driven Development Patterns & Reference

This reference document accompanies `.agents/skills/test-driven-development/SKILL.md`.

## 1. The Red-Green-Refactor Loop

```
    RED                GREEN              REFACTOR
 Write a test    Write minimal code    Clean up the
 that fails  ──→  to make it pass  ──→  implementation  ──→  (repeat)
      │                  │                    │
      ▼                  ▼                    ▼
   Test FAILS        Test PASSES         Tests still PASS
```

---

## 2. Bug Reproduction: The Prove-It Pattern

```typescript
// Step 1: Write a reproduction test that asserts the desired fix
it('sets completedAt when task is marked complete', async () => {
  const task = await taskService.createTask({ title: 'Test' });
  const completed = await taskService.completeTask(task.id);
  expect(completed.status).toBe('completed');
  expect(completed.completedAt).toBeInstanceOf(Date); // Fails initially
});

// Step 2: Implement minimal fix in application code
// Step 3: Verify test passes and re-run entire test suite
```

---

## 3. Testing Pyramid Ratios

- **Unit Tests (~70%)**: Fast, isolated, test pure domain logic and edge cases.
- **Integration Tests (~20%)**: Test module boundaries, database interactions, and API routes.
- **E2E / Browser Tests (~10%)**: Test critical end-to-end user journeys.
