#!/bin/bash
# ~/.claude/hooks/git-identity-guard.sh

# 1. Capture stdin (the JSON payload from Claude Code)
INPUT=$(cat)

# 2. Extract tool name and the specific command
TOOL=$(echo "$INPUT" | jq -r '.tool_name')
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

# 3. Only run logic if it's a git commit
if [[ "$TOOL" == "Bash" && "$CMD" == *"git commit"* ]]; then
    
    # 4. Fetch current identity
    CURRENT_NAME=$(git config user.name)
    CURRENT_EMAIL=$(git config user.email)
    
    REQUIRED_NAME="noameron"
    REQUIRED_EMAIL="noameron3@gmail.com"

    # 5. Validation Logic
    if [[ "$CURRENT_NAME" != "$REQUIRED_NAME" || "$CURRENT_EMAIL" != "$REQUIRED_EMAIL" ]]; then
        # Block and provide the specific fix
        echo "{
          \"hookSpecificOutput\": {
            \"hookEventName\": \"PreToolUse\",
            \"permissionDecision\": \"block\",
            \"reason\": \"❌ IDENTITY MISMATCH: Current is '$CURRENT_NAME' <$CURRENT_EMAIL>. Please run:\\n\\ngit config user.name '$REQUIRED_NAME'\\ngit config user.email '$REQUIRED_EMAIL'\"
          }
        }"
        exit 0
    fi
fi

# 6. Default: Allow (or pass to user prompt)
echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask"}}'