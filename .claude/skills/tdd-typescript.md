---
name: tdd-typescript
description: Test-Driven Development workflow for TypeScript projects using Vitest. Use when writing new features, fixing bugs, or refactoring TypeScript code. Enforces tests-first development with 80%+ coverage. Triggers on requests to add features, fix bugs, create components, add API endpoints, or refactor code in TypeScript/Vue/Node projects.
---

# TDD Workflow for TypeScript/Vitest

## Core Principle

**Write tests FIRST, then implement code to make tests pass.**

## TDD Cycle

### 1. Red: Write Failing Test

```typescript
// src/utils/calculator.test.ts
import { describe, it, expect } from 'vitest'
import { add } from './calculator'

describe('add', () => {
  it('adds two positive numbers', () => {
    expect(add(2, 3)).toBe(5)
  })

  it('handles negative numbers', () => {
    expect(add(-1, 5)).toBe(4)
  })
})
```

Run: `npm run test:run` - tests should fail.

### 2. Green: Minimal Implementation

```typescript
// src/utils/calculator.ts
export function add(a: number, b: number): number {
  return a + b
}
```

Run: `npm run test:run` - tests should pass.

### 3. Refactor

Improve code while keeping tests green.

### 4. Verify Coverage

```bash
npm run test:run -- --coverage
```

## Test Patterns

### Unit Test

```typescript
import { describe, it, expect, vi } from 'vitest'
import { formatDate } from './date-utils'

describe('formatDate', () => {
  it('formats ISO date to readable string', () => {
    expect(formatDate('2024-01-15')).toBe('January 15, 2024')
  })

  it('returns empty string for invalid date', () => {
    expect(formatDate('invalid')).toBe('')
  })
})
```

### Vue Component Test

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Button from './Button.vue'

describe('Button', () => {
  it('renders slot content', () => {
    const wrapper = mount(Button, {
      slots: { default: 'Click me' }
    })
    expect(wrapper.text()).toBe('Click me')
  })

  it('emits click event', async () => {
    const wrapper = mount(Button)
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toHaveLength(1)
  })

  it('is disabled when prop is set', () => {
    const wrapper = mount(Button, { props: { disabled: true } })
    expect(wrapper.attributes('disabled')).toBeDefined()
  })
})
```

### Async/API Test

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fetchUser } from './api'

describe('fetchUser', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('returns user data on success', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ id: 1, name: 'John' })
    })

    const user = await fetchUser(1)
    expect(user).toEqual({ id: 1, name: 'John' })
  })

  it('throws on network error', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'))
    await expect(fetchUser(1)).rejects.toThrow('Network error')
  })
})
```

### Pinia Store Test

```typescript
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from './user'

describe('useUserStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('starts with no user', () => {
    const store = useUserStore()
    expect(store.user).toBeNull()
  })

  it('sets user on login', async () => {
    const store = useUserStore()
    await store.login('test@example.com', 'password')
    expect(store.user).toBeDefined()
    expect(store.isAuthenticated).toBe(true)
  })
})
```

## Parameterized Tests

**NEVER use for loops inside tests.** Use `it.each()` for multiple test cases.

### Wrong: For Loop in Test

```typescript
// DON'T DO THIS
it('validates inputs', () => {
  const cases = [1, 2, 3, 4, 5]
  for (const num of cases) {
    expect(isPositive(num)).toBe(true)
  }
})
```

### Correct: Use it.each()

```typescript
it.each([
  [1, true],
  [0, false],
  [-1, false],
  [100, true],
])('isPositive(%i) returns %s', (input, expected) => {
  expect(isPositive(input)).toBe(expected)
})
```

### With Named Parameters

```typescript
it.each([
  { input: 'hello', expected: 'HELLO' },
  { input: 'World', expected: 'WORLD' },
  { input: '', expected: '' },
])('toUpperCase($input) returns $expected', ({ input, expected }) => {
  expect(toUpperCase(input)).toBe(expected)
})
```

### describe.each for Test Suites

```typescript
describe.each([
  { role: 'admin', canDelete: true },
  { role: 'user', canDelete: false },
  { role: 'guest', canDelete: false },
])('$role permissions', ({ role, canDelete }) => {
  it(`${role} canDelete is ${canDelete}`, () => {
    expect(getPermissions(role).canDelete).toBe(canDelete)
  })
})
```

## Mocking

### Mock Module

```typescript
vi.mock('./api', () => ({
  fetchData: vi.fn(() => Promise.resolve({ data: 'mocked' }))
}))
```

### Mock Function

```typescript
const mockFn = vi.fn()
mockFn.mockReturnValue(42)
mockFn.mockResolvedValue({ success: true })
mockFn.mockImplementation((x) => x * 2)
```

### Spy on Method

```typescript
const spy = vi.spyOn(console, 'log')
// ... code that logs
expect(spy).toHaveBeenCalledWith('expected message')
```

## Coverage Requirements

- Minimum 80% coverage (lines, branches, functions)
- All edge cases: null, undefined, empty, boundary values
- Error paths tested, not just happy paths

## Vitest Config

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      thresholds: {
        lines: 80,
        branches: 80,
        functions: 80,
        statements: 80
      }
    }
  }
})
```

## File Organization

```
src/
├── components/
│   ├── Button.vue
│   └── Button.test.ts
├── composables/
│   ├── useAuth.ts
│   └── useAuth.test.ts
├── stores/
│   ├── user.ts
│   └── user.test.ts
└── utils/
    ├── helpers.ts
    └── helpers.test.ts
```

## Checklist Before Implementation

1. Write user story: "As a [role], I want [action], so that [benefit]"
2. List test cases covering happy path, edge cases, errors
3. Write failing tests
4. Implement minimal code
5. Refactor
6. Verify 80%+ coverage
