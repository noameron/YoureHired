---
description: Run full code review pipeline on all changes in current branch
allowed-tools: Task, Read, Write, Edit, Bash, Glob, Grep
disable-model-invocation: true
---

# Full Code Review Pipeline

Execute a two-phase review on all branch changes.

**⚠️ CRITICAL: SEQUENTIAL EXECUTION REQUIRED ⚠️**
- Phase 1 (code-simplifier) MUST complete fully before Phase 2 starts
- Phase 2 (pr-review) depends on Phase 1's fixes being applied first
- **NEVER run these phases in parallel** - pr-review reviews the simplified code

---

## Step 0: Get Changed Files

```bash
BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
CURRENT_BRANCH=$(git branch --show-current)
MERGE_BASE=$(git merge-base origin/$BASE_BRANCH HEAD)
CHANGED_FILES=$(git diff --name-only --diff-filter=d $MERGE_BASE HEAD)
```

If no files changed, inform user and stop.

Display the branch info and file list, then proceed.

---

## Phase 1: Code Simplifier (RUN FIRST)

**DO NOT proceed to Phase 2 until this phase completes and returns results.**

Run the `code-simplifier` agent using **Task** tool with prompt:

```
Review these files on branch "$CURRENT_BRANCH" (base: $BASE_BRANCH):

$CHANGED_FILES

Use `git diff $MERGE_BASE HEAD -- <file>` for change context.

FIX all critical/high issues. Document medium/low for later.

Return JSON:
{
  "fixed_issues": [{"severity", "file", "line", "description", "fix_applied"}],
  "deferred_issues": [{"severity", "file", "line", "description", "suggested_fix"}]
}
```

Wait for completion. Save output as `SIMPLIFIER_REPORT`.

---

## Phase 2: PR Review (RUN AFTER PHASE 1 COMPLETES)

**WAIT for Phase 1 to complete. Only start this phase after saving SIMPLIFIER_REPORT.**

Run the `pr-review` agent using **Task** tool with prompt:

```
Review these files on branch "$CURRENT_BRANCH" (already processed by code-simplifier):

$CHANGED_FILES

Review current file state. Use `git diff $MERGE_BASE HEAD -- <file>` for original change context.

FIX all critical/high issues. Document medium/low for later.

Return JSON:
{
  "fixed_issues": [{"severity", "category", "file", "line", "description", "fix_applied"}],
  "deferred_issues": [{"severity", "category", "file", "line", "description", "suggested_fix"}]
}
```

Wait for completion. Save output as `REVIEW_REPORT`.

---

## Phase 3: Final Report

Display combined results:

```
═══════════════════════════════════════════════════════════════
              FULL REVIEW COMPLETE - $CURRENT_BRANCH
═══════════════════════════════════════════════════════════════

## 🔧 CODE SIMPLIFIER
### ✅ Fixed
[SIMPLIFIER_REPORT.fixed_issues]

### 📋 Deferred
[SIMPLIFIER_REPORT.deferred_issues]

## 🔍 PR REVIEW  
### ✅ Fixed
[REVIEW_REPORT.fixed_issues]

### 📋 Deferred
[REVIEW_REPORT.deferred_issues]

═══════════════════════════════════════════════════════════════
```

---

## Phase 4: User Prompt

Ask: **"Fix the deferred medium/low issues?"**

Options:
1. Fix ALL
2. Fix MEDIUM only
3. Pick specific
4. Done

Act on user choice.