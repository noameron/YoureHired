---
name: frontend-code-review-skill
description: Conducts thorough code review on Vue 3 + TypeScript frontend changes. Checks TypeScript strictness (no 'any'), Vue Composition API patterns, SOLID principles, clean code, security, performance, and enforces max 5 files per PR. Used exclusively by pr-review-agent for frontend/ directory changes.
user-invocable: false
allowed-tools: Bash, Read, Grep, Glob
allowed-prompts:
  - tool: Bash
    prompt: run git diff commands
  - tool: Bash
    prompt: run npm run build
  - tool: Bash
    prompt: run npm run lint
  - tool: Bash
    prompt: run npm run test
---

# Frontend Code Review Skill

Strict code reviewer for Vue 3 + TypeScript frontend in the `frontend/` directory.

## Review Workflow

1. **Count Changed Files**
   ```bash
   git diff --name-only HEAD -- frontend/ | wc -l
   ```
   If > 5 files, flag as blocking (unless changes are trivial 1-3 lines each).

2. **Run Verification**
   ```bash
   cd frontend && npm run build && npm run lint && npm run test:run
   ```
   Stop and report immediately if any fail.

3. **Scan for 'any' Type**
   ```bash
   git diff HEAD -- frontend/ | grep -E ":\s*any|as\s+any|<any>"
   ```
   Flag all as CRITICAL.

4. **Read and Analyze Each Changed File**

5. **Generate Report**

---

## Review Criteria

### BLOCKING (Stop Review)
- `npm run build` fails
- `npm run lint` has errors
- `npm run test:run` fails
- PR exceeds 5 files (alert but continue if changes are trivial)

### CRITICAL (Must Fix)

**TypeScript Strictness - NO 'any'**
- `: any`, `as any`, `<any>`, `type X = any`
- Use `unknown` or specific types instead

**Test Compliance**
- New features/functions require test coverage
- Tests follow `// GIVEN // WHEN // THEN` structure

**Security**
- Hardcoded credentials (API keys, tokens)
- XSS vulnerabilities (unescaped user input, `v-html` with user data)
- Missing input validation
- Sensitive data in localStorage/sessionStorage

### HIGH (Should Fix)

**Over-Abstraction**
- Unnecessary wrappers for single-use code
- Premature abstractions
- Deep inheritance when composition works
- 3 similar lines > premature abstraction

**Code Quality**
- Functions > 50 lines
- Files > 800 lines
- Nesting > 4 levels
- Missing error handling
- `console.log` left in code
- Mutation patterns (prefer immutability)

**Clean Code Naming**
- Variables: descriptive, intent-revealing (not `x`, `temp`, `data`)
- Functions: verb phrases (`calculateTotal`, not `calc`)
- Booleans: read as questions (`isValid`, `hasPermission`)
- No abbreviations except universally understood (`url`, `id`)

**SOLID Principles**
- Single Responsibility: one reason to change
- Open/Closed: extend, don't modify
- Dependency Inversion: depend on abstractions

### MEDIUM (Consider Fixing)

**Performance**
- Unnecessary re-renders
- Missing `computed` for derived state
- Memory leaks (unremoved event listeners, subscriptions)
- Missing `v-once` for static content
- Large arrays without virtual scrolling

**Best Practices**
- TODO/FIXME without tickets
- Magic numbers without explanation
- Emoji in code/comments

---

## Project-Specific Rules

- Use Composition API with `<script setup lang="ts">`
- Use `type` over `interface` for type definitions
- Use `@/` alias for src imports
- Use Pinia for state management
- Prefer `computed` over methods for derived state
- Clean up watchers and event listeners in `onUnmounted`

---

## Output Format

```
## Frontend Code Review Report

### Build Status
| Check | Status |
|-------|--------|
| Build | ✅/❌ |
| Lint | ✅/❌ |
| Tests | ✅/❌ |
| Files Changed | X/5 |

### Critical Issues (Must Fix)
- [ ] `file.ts:123` - Description

### High Issues (Should Fix)
- [ ] `file.vue:45` - Description

### Medium Issues (Consider Fixing)
- [ ] `utils.ts:30` - Description

### What's Good
- [Positive observations]

### Summary
X critical | Y high | Z medium issues found
**Verdict:** ✅ APPROVE | ⚠️ WARNING | ❌ BLOCK
```
