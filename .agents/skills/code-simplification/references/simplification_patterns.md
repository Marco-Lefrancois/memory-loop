# Code Simplification Patterns & Language Guides

This reference document accompanies `.agents/skills/code-simplification/SKILL.md`.

## 1. TypeScript & JavaScript Patterns

```typescript
// Replace dense ternaries with explicit early returns or lookup tables
// Before:
const label = isNew ? 'New' : isUpdated ? 'Updated' : isArchived ? 'Archived' : 'Active';

// After:
function getStatusLabel(item: Item): string {
  if (item.isNew) return 'New';
  if (item.isUpdated) return 'Updated';
  if (item.isArchived) return 'Archived';
  return 'Active';
}

// Unnecessary async wrapper
// Before: async function getUser(id: string) { return await userService.findById(id); }
// After: function getUser(id: string) { return userService.findById(id); }
```

---

## 2. Python Patterns

```python
# List and Dict comprehensions over manual loops
# Before:
result = {}
for item in items:
    result[item.id] = item.name

# After:
result = {item.id: item.name for item in items}

# Guard clauses instead of nested conditions
# Before:
def process(data):
    if data is not None:
        if data.is_valid():
            return do_work(data)
# After:
def process(data):
    if data is None or not data.is_valid():
        raise ValueError("Invalid data")
    return do_work(data)
```
