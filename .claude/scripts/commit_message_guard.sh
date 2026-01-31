#!/bin/bash
# .claude/scripts/commit_message_guard.sh
# PreToolUse hook: enforces commit discipline
#   1. Max 5 staged files per commit
#   2. Commit message must follow format: description + bullet per file
#   3. No Co-Authored-By line

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
    REASON+="   <short paragraph describing what changed and why>\n"
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

# ── Check 2: Commit message format ──

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

ERRORS=""

# Check for Co-Authored-By (not allowed)
if echo "$COMMIT_MSG" | grep -qi "Co-Authored-By"; then
    ERRORS+="- Do not include 'Co-Authored-By' in commit messages.\n"
fi

# Read message into an array (bash 3.x compatible — no mapfile)
LINES=()
while IFS= read -r line || [[ -n "$line" ]]; do
    LINES+=("$line")
done <<< "$COMMIT_MSG"

TOTAL_LINES=${#LINES[@]}

# Must have at least: 1 description line + 1 blank + N file bullets
MIN_LINES=$((2 + STAGED_COUNT))

if [[ "$TOTAL_LINES" -lt "$MIN_LINES" ]]; then
    ERRORS+="- Message too short. Need description, blank line, then $STAGED_COUNT file bullet(s).\n"
fi

# Check structure: description (non-empty), blank line, then file bullets
# Line 1: non-empty description
if [[ -z "${LINES[0]// /}" ]]; then
    ERRORS+="- First line must be a non-empty description of what changed and why.\n"
fi

# Find the blank line that separates description from bullets
# Description can be multiple lines, so find the last non-bullet section
BLANK_LINE_IDX=-1
for ((i=1; i<TOTAL_LINES; i++)); do
    if [[ -z "${LINES[$i]// /}" ]]; then
        # Check if next line starts with "* " (bullet)
        NEXT_IDX=$((i + 1))
        if [[ $NEXT_IDX -lt $TOTAL_LINES ]] && [[ "${LINES[$NEXT_IDX]}" == "* "* ]]; then
            BLANK_LINE_IDX=$i
            break
        fi
    fi
done

if [[ $BLANK_LINE_IDX -eq -1 ]]; then
    ERRORS+="- Must have a blank line before file bullets.\n"
else
    # Check file bullets start after blank line
    BULLET_START=$((BLANK_LINE_IDX + 1))
    BULLET_IDX=0
    while IFS= read -r staged_file; do
        LINE_IDX=$((BULLET_START + BULLET_IDX))
        EXPECTED_BULLET="* $staged_file"
        ACTUAL_LINE="${LINES[$LINE_IDX]:-}"
        if [[ "$ACTUAL_LINE" != "$EXPECTED_BULLET" ]]; then
            ERRORS+="- Expected bullet: $EXPECTED_BULLET\n"
        fi
        BULLET_IDX=$((BULLET_IDX + 1))
    done <<< "$STAGED_FILES"
fi

if [[ -n "$ERRORS" ]]; then
    # Build pre-filled template
    TEMPLATE="<short paragraph describing what changed and why>\n\n"
    while IFS= read -r f; do
        TEMPLATE+="* $f\n"
    done <<< "$STAGED_FILES"

    REASON="COMMIT MESSAGE FORMAT ERROR.\n\n"
    REASON+="Issues found:\n$ERRORS\n"
    REASON+="Required format:\n\n"
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
