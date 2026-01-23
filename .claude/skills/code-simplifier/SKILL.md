---
name: code-simplifier-skill
description: Core skill for analyzing code complexity and dead code. Identifies unused imports, variables, overly complex functions, and suggests simplifications. Used by code-simplifier agent and pr-review.
user-invocable: false
allowed-tools: Bash, Read, Grep, Glob
---

# Code Simplifier Skill

Analyzes recent git changes for dead code and complexity issues, returning structured suggestions for simplification.

## Analysis Workflow

### Step 1: Identify Changed Files

```bash
# Get all changed files (staged + unstaged)
git diff --name-only HEAD
git diff --cached --name-only
```

### Step 2: Categorize by Language

- **Python files**: `*.py` in `backend/`
- **TypeScript/Vue files**: `*.ts`, `*.tsx`, `*.vue` in `frontend/`

### Step 3: Run Static Analysis

#### Python Analysis

```bash
# Dead imports (F401)
cd backend && uv run ruff check --select=F401 --output-format=json .

# Unused variables (F841)
cd backend && uv run ruff check --select=F841 --output-format=json .

# High complexity - cyclomatic > 10 (C901)
cd backend && uv run ruff check --select=C901 --output-format=json .
```

#### TypeScript/Vue Analysis

```bash
# Run ESLint for unused variables
cd frontend && npm run lint -- --format json 2>/dev/null
```

Look for rules: `no-unused-vars`, `@typescript-eslint/no-unused-vars`

### Step 4: Heuristic Analysis

For each changed file, also check:

1. **Long Functions** (> 30 lines)
   - Read file, identify function boundaries
   - Count lines between `def`/`function` and next definition or end
   - Flag functions exceeding 30 lines

2. **Deep Nesting** (> 3 levels)
   - Count indentation levels in conditionals/loops
   - Flag blocks with nesting > 3 levels

3. **Dead Functions**
   - Identify function definitions
   - Grep codebase to see if function is called anywhere
   - Flag functions defined but never referenced

---

## Issue Categories

### HIGH Priority (Safe to auto-fix)

| Code | Issue | Detection | Auto-fix |
|------|-------|-----------|----------|
| F401 | Unused import | ruff | Remove import line |
| F841 | Unused variable | ruff | Remove variable assignment |
| TS-unused | Unused TS var | ESLint | Remove declaration |

### MEDIUM Priority (Suggest, needs review)

| Issue | Detection | Suggestion |
|-------|-----------|------------|
| Long function (>30 lines) | Line count | Extract helper functions |
| Deep nesting (>3 levels) | Indentation | Use guard clauses / early returns |
| High cyclomatic complexity | ruff C901 | Simplify conditionals |

### LOW Priority (Informational)

| Issue | Detection | Note |
|-------|-----------|------|
| Redundant else after return | Pattern | Remove else, dedent code |
| Multiple return statements | Pattern | Consider single exit point |

---

## Output Format

Return a structured list for the agent to present interactively:

```markdown
## Simplification Analysis Results

**Files Analyzed:** X (Y Python, Z TypeScript)
**Issues Found:** N total

### Issues

#### Issue 1
- **File:** `backend/app/services/user.py`
- **Line:** 3
- **Type:** Dead Import (F401)
- **Priority:** HIGH
- **Current:**
  ```python
  from typing import Optional, Union, List
  ```
- **Proposed:**
  ```python
  from typing import Optional, List
  ```
- **Reason:** `Union` is imported but never used in this file.

#### Issue 2
- **File:** `backend/app/api/routes.py`
- **Line:** 42-108
- **Type:** Long Function
- **Priority:** MEDIUM
- **Current:** Function `process_request` is 67 lines
- **Proposed:** Extract validation logic to `_validate_request()` helper
- **Reason:** Functions over 30 lines are harder to test and maintain.
```

---

## Integration Notes

When invoked by an agent:

1. Run all detection commands
2. Parse JSON output from linters
3. Apply heuristics for non-linter checks
4. Return structured issue list
5. Agent handles interactive approval and applies changes

The agent calling this skill is responsible for:
- Presenting issues one by one
- Getting user approval
- Applying changes via Edit tool
- Tracking applied vs skipped
