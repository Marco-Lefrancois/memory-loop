# API and Interface Design Patterns & Deep References

This reference document accompanies `.agents/skills/api-and-interface-design/SKILL.md`.

## 1. Idempotency Deep Dive

### Core Principles
Accepting an `Idempotency-Key` is the contract; honouring it is the implementation.
- **Derive key from intent, not attempt**: Must be stable across retries of one intent and different across distinct intents.
  - Good: `req.headers['idempotency-key']`, `charge:v1:${orderId}`.
  - Bad: `crypto.randomUUID()` (per attempt), timestamp (per attempt).
- **Atomic Claim**: Use unique database constraints to avoid TOCTOU race conditions.
- **Guard Payload**: Reject different payloads under the same key with 422 Unprocessable Entity.
- **Duplicate Handling**: Choose between `409 Conflict`, bounded wait, or `202 Accepted` with status URL.
- **Key Retention**: Key TTL must exceed longest retry chain (e.g. 7-day DLQ requires >= 7-day retention).

```typescript
// Atomic claim with unique constraint
try {
  await db.insert({ key, state: 'in_progress', requestHash: hash(req.body) });
} catch (e) {
  if (isUniqueViolation(e)) return replayOrReject(key);
  throw e;
}
const result = await chargeCard(amount);
await db.update({ key, state: 'succeeded', response: result });
```

---

## 2. REST API Specification

### Resource Conventions
```
GET    /api/tasks              → List tasks (query params for filtering/pagination)
POST   /api/tasks              → Create task
GET    /api/tasks/:id          → Get single task
PATCH  /api/tasks/:id          → Update partial task
DELETE /api/tasks/:id          → Idempotent delete
```

### Pagination Schema
```typescript
interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    pageSize: number;
    totalItems: number;
    totalPages: number;
  };
}
```

---

## 3. TypeScript Interface Patterns

### Discriminated Unions for State
```typescript
type TaskStatus =
  | { type: 'pending' }
  | { type: 'in_progress'; assignee: string; startedAt: Date }
  | { type: 'completed'; completedAt: Date; completedBy: string }
  | { type: 'cancelled'; reason: string; cancelledAt: Date };
```

### Branded Types for Entity Identifiers
```typescript
type TaskId = string & { readonly __brand: 'TaskId' };
type UserId = string & { readonly __brand: 'UserId' };

function getTask(id: TaskId): Promise<Task> { /* ... */ }
```
