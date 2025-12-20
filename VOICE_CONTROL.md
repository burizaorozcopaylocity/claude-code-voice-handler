# Voice Notifications Control

## Quick Commands (from PowerShell or Claude Code)

```bash
# Main command
voice off       # Disable voice + clear message queue
voice on        # Enable voice notifications
voice status    # Show current status
voice           # Default: show status

# Ultra-short aliases
voff            # Disable
von             # Enable
vs              # Status
```

## How it Works

- **VOICE_ENABLED flag** in `.env` controls voice on/off
- **Automatic queue clearing** prevents "ghost voices" when re-enabling
- **Instant effect** - no need to restart daemon

## Manual Control

Edit `.env` file directly:
```bash
# Location
C:\Users\BUrizaorozco\.claude\hooks\voice_notifications\.env

# Change this line:
VOICE_ENABLED=false  # Silence mode
VOICE_ENABLED=true   # Voice active
```

## From Claude Code

Simply ask Claude to run:
```
voff    # Silence
von     # Voice on
vs      # Check status
```

## Current Configuration

- **Personality**: Tech Advisor (professional, corporate)
- **Max words**: 20 words per message
- **TTS Provider**: OpenAI (nova voice)
- **LLM Provider**: Ollama (qwen2.5:0.5b)
- **Nickname**: Bernard
