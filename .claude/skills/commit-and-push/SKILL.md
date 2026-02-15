---
name: commit-and-push
description: >
  Commit staged/unstaged changes and push to remote. Use when the user says
  "commit", "commit and push", "push changes", "ship it", "save and push",
  "/commit-and-push", or any similar request to commit and/or push code.
  Enforces: max 5 files per commit (unless all changes are minor),
  paragraph-style commit messages explaining WHAT and WHY, bullet list of
  changed files, and never includes a Co-Authored-By line.
---

# Commit and Push

## Workflow

1. **Gather context** (run in parallel):
   - `git status -u` (never use `-uall`)
   - `git diff --stat` and `git diff --cached --stat` for change summary
   - `git log --oneline -5` for recent commit style reference

2. **File count gate**:
   - Count files that will be committed (staged + unstaged modified/new).
   - If **<= 5 files**: proceed normally.
   - If **> 5 files**: inspect each diff. Only proceed if ALL changes are
     minor (formatting, lint fixes, import reordering, renaming, config
     tweaks, version bumps). If any file has substantive logic changes,
     **stop and ask the user** to split the commit into smaller batches.

3. **Stage files**:
   - Add files by explicit name — never use `git add -A` or `git add .`.
   - Never stage files that may contain secrets (`.env`, credentials, tokens).

4. **Compose commit message** using this exact format:

   ```
   <One paragraph: what changed and why. Be specific. Mention the feature,
   bug, or motivation. Do not start with "This commit…".>

   * path/to/file1.ts
   * path/to/file2.vue
   ```

   Rules:
   - First line is the summary paragraph (can wrap, no length limit).
   - Blank line, then bullet list of changed files using `* ` prefix (asterisk + space).
   - **Files must be listed in alphabetical order** (a commit hook enforces this).
   - **No header** before the file list — just the `* file` lines directly.
   - **NEVER** use `- ` (dash) bullets — always use `* ` (asterisk).
   - **NEVER** append a `Co-Authored-By` line or any trailer.

5. **Commit** using a HEREDOC for the message:

   ```bash
   git commit -m "$(cat <<'EOF'
   <paragraph>

   * file1
   * file2
   EOF
   )"
   ```

6. **Push**:
   - If the branch has an upstream, run `git push`.
   - If no upstream, run `git push -u origin <branch>`.
   - **Never** force-push unless the user explicitly asks.

7. **Confirm**: Show the commit hash, branch, and remote URL after push.
