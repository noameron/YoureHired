---
name: commit-discipline
description: Enforces commit discipline rules. Max 5 staged files per commit, strict message template, git identity verification. Use when making git commits.
user-invocable: false
allowed-tools: Bash
---

# Commit Discipline Rules

This skill enforces commit discipline through a pre-tool-use hook. Understand these rules before committing.

## Rule 1: Max 5 Staged Files Per Commit

If more than 5 files are staged:
1. Run `git reset HEAD` to unstage all files
2. Group files by related module/feature (max 5 per group)
3. For each group, stage and commit separately

## Rule 2: Commit Message Template

**Required format:**
```
<description: what changed and why>

* path/to/file1
* path/to/file2
```

**Structure:**
- **Line 1**: Description of what changed and why. Must be descriptive enough to understand the change without looking at the code. Avoid vague phrases like "Fix bug" or "Update code". Instead, explain the specific change: "Fix null pointer exception when user submits empty form" or "Add validation for email format in registration endpoint".
- **Line 2**: Blank separator line
- **Lines 3+**: Each staged file listed as `* <path>`

**Good examples:**
```
Add JWT token refresh endpoint to prevent session expiration during long tasks

* backend/app/api/auth.py
* backend/app/schemas/auth.py
* backend/tests/test_auth.py
```

```
Fix race condition in concurrent file uploads by adding mutex lock

* backend/app/services/upload.py
* backend/tests/test_upload.py
```

**Bad examples (too vague):**
- "Fix bug"
- "Update tests"
- "Refactor code"
- "Add feature"

**Using heredoc (recommended for multi-line):**
```bash
git commit -m "$(cat <<'EOF'
Add JWT token refresh endpoint to prevent session expiration during long tasks

* backend/app/api/auth.py
* backend/app/schemas/auth.py
* backend/tests/test_auth.py
EOF
)"
```

## Workflow Summary

1. Check staged file count (`git diff --cached --name-only | wc -l`)
2. If > 5, reset and split into logical groups
3. Stage files for current commit (max 5)
4. Write commit message following the template
5. Commit and repeat for remaining groups

## Quick Reference

```bash
# Check what's staged
git diff --cached --name-only

# Unstage all
git reset HEAD

# Stage specific files
git add path/to/file1 path/to/file2

# Commit with template
git commit -m "$(cat <<'EOF'
Description here

* file1
* file2
EOF
)"
```
