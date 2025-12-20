#!/bin/bash
# Setup voice-panel alias
# This script is run automatically on SessionStart to ensure the alias exists

ALIAS_NAME="voice-panel"
ALIAS_COMMAND="cd ~/.claude/hooks/voice_notifications && uv run python launcher.py"
SHELL_CONFIG=""

# Detect shell config file
if [ -f "$HOME/.zshrc" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
elif [ -f "$HOME/.bash_profile" ]; then
    SHELL_CONFIG="$HOME/.bash_profile"
else
    # Create .zshrc if no config exists (macOS default)
    SHELL_CONFIG="$HOME/.zshrc"
    touch "$SHELL_CONFIG"
fi

# Check if alias already exists
if grep -q "alias $ALIAS_NAME=" "$SHELL_CONFIG" 2>/dev/null; then
    # Alias already exists, exit silently
    exit 0
fi

# Add alias to shell config
echo "" >> "$SHELL_CONFIG"
echo "# Voice Handler Control Panel alias (added automatically)" >> "$SHELL_CONFIG"
echo "alias $ALIAS_NAME='$ALIAS_COMMAND'" >> "$SHELL_CONFIG"
echo "" >> "$SHELL_CONFIG"

# Notify user (this will appear in Claude Code output)
echo "✅ Created alias '$ALIAS_NAME' in $SHELL_CONFIG"
echo "   Use '$ALIAS_NAME' to launch the control panel"
echo "   Restart your terminal or run: source $SHELL_CONFIG"
