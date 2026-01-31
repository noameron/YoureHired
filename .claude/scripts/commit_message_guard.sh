#!/bin/bash
# .claude/scripts/commit_message_guard.sh
# PreToolUse hook: enforces commit discipline
#   1. Max 5 staged files per commit
#   2. Commit message must follow a strict template

INPUT=$(cat)

TOOL=$(echo "$INPUT" | jq -r '.tool_name')
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

ALLOW='{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'

# Only check actual git commit commands (not strings that merely contain "git commit")
if [[ "$TOOL" != "Bash" ]] || ! echo "$CMD" | grep -qE '(^|&&|\|\||;)[[:space:]]*git[[:space:]]+commit'; then
    echo "$ALLOW"
    exit 0
fi

# Get staged files
STAGED_FILES=$(git diff --cached --name-only)

if [[ -z "$STAGED_FILES" ]]; then
    echo "$ALLOW"
    exit 0
fi

STAGED_COUNT=$(echo "$STAGED_FILES" | wc -l | tr -d ' ')

# ── Check 1: Max 5 staged files ──
if [[ "$STAGED_COUNT" -gt 5 ]]; then
    FILE_LIST=$(echo "$STAGED_FILES" | sed 's/^/  - /')
    REASON="TOO MANY FILES STAGED ($STAGED_COUNT > 5 max).\n\n"
    REASON+="Currently staged:\n$FILE_LIST\n\n"
    REASON+="ACTION REQUIRED — do this autonomously, do NOT ask the user:\n"
    REASON+="1. Run: git reset HEAD\n"
    REASON+="2. Group the files by related module/feature (max 5 per group)\n"
    REASON+="3. For each group, stage the files and commit using this template:\n\n"
    REASON+="   <short description: what changed and why>\n"
    REASON+="   \n"
    REASON+="   * path/to/file1\n"
    REASON+="   * path/to/file2"

    jq -n --arg reason "$REASON" '{
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: $reason
      }
    }'
    exit 0
fi

# ── Check 2: Commit message template ──

# Extract commit message from the command.
# Try heredoc first (<<'EOF'...EOF), then -m "..." / -m '...'
COMMIT_MSG=""

if echo "$CMD" | grep -q "<<'EOF'"; then
    COMMIT_MSG=$(echo "$CMD" | sed -n "/<<'EOF'/,/^[[:space:]]*EOF/p" | sed '1d;$d')
elif echo "$CMD" | grep -q '<<"EOF"'; then
    COMMIT_MSG=$(echo "$CMD" | sed -n '/<<"EOF"/,/^[[:space:]]*EOF/p' | sed '1d;$d')
elif echo "$CMD" | grep -q '<<EOF'; then
    COMMIT_MSG=$(echo "$CMD" | sed -n '/<<EOF/,/^[[:space:]]*EOF/p' | sed '1d;$d')
fi

# Fall back to -m "..." or -m '...'
if [[ -z "$COMMIT_MSG" ]]; then
    COMMIT_MSG=$(echo "$CMD" | sed -n 's/.*git commit.*-m "\(.*\)"/\1/p')
fi
if [[ -z "$COMMIT_MSG" ]]; then
    COMMIT_MSG=$(echo "$CMD" | sed -n "s/.*git commit.*-m '\(.*\)'/\1/p")
fi

# If we can't extract a message, allow (git will handle it)
if [[ -z "$COMMIT_MSG" ]]; then
    echo "$ALLOW"
    exit 0
fi

# Trim trailing whitespace/blank lines
COMMIT_MSG=$(echo "$COMMIT_MSG" | awk 'NF{p=1} p{b=b $0 ORS; if(NF){printf "%s",b; b=""}}')

# Build expected values
ERRORS=""

# Read message into an array (bash 3.x compatible — no mapfile)
LINES=()
while IFS= read -r line || [[ -n "$line" ]]; do
    LINES+=("$line")
done <<< "$COMMIT_MSG"

# Line 1: non-empty description
if [[ -z "${LINES[0]// /}" ]]; then
    ERRORS+="- Line 1 must be a non-empty description of what changed and why.\n"
fi

# Line 2: blank separator
if [[ -n "${LINES[1]// /}" ]]; then
    ERRORS+="- Line 2 must be a blank separator line.\n"
fi

# Lines 3+: each staged file as "* <path>"
LINE_NUM=2
while IFS= read -r staged_file; do
    EXPECTED_LINE="* $staged_file"
    ACTUAL_LINE="${LINES[$LINE_NUM]:-}"
    if [[ "$ACTUAL_LINE" != "$EXPECTED_LINE" ]]; then
        ERRORS+="- Line $((LINE_NUM + 1)) must be: $EXPECTED_LINE\n"
    fi
    LINE_NUM=$((LINE_NUM + 1))
done <<< "$STAGED_FILES"

if [[ -n "$ERRORS" ]]; then
    # Build pre-filled template
    TEMPLATE="<short description: what changed and why>\n\n"
    while IFS= read -r f; do
        TEMPLATE+="* $f\n"
    done <<< "$STAGED_FILES"

    REASON="COMMIT MESSAGE FORMAT ERROR.\n\n"
    REASON+="Issues found:\n$ERRORS\n"
    REASON+="Required template (use this, replacing the first line):\n\n"
    REASON+="$TEMPLATE"

    jq -n --arg reason "$REASON" '{
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: $reason
      }
    }'
    exit 0
fi

echo "$ALLOW"
is