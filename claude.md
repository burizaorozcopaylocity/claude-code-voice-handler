# Claude Code Voice Handler - System Documentation

## Project Overview
Voice notifications system for Claude Code that provides audio feedback using OpenAI TTS with async queue processing and retry logic.

## Architecture

### Core Components
1. **Hook Entry** (`hook_entry.py`) - Main entry point called by Claude Code hooks
2. **Queue System** (`src/voice_handler/queue/`)
   - `broker.py` - SQLite-backed persistent message queue
   - `consumer.py` - Background consumer with retry logic
   - `daemon.py` - Daemon process manager
   - `producer.py` - Message enqueueing interface
3. **TTS Provider** (`src/voice_handler/tts/provider.py`) - OpenAI TTS integration
4. **Configuration** - `.env` + `config.json`

### Message Flow
```
Hook → Producer → SQLite Queue → Consumer (daemon) → TTS → Audio Output
```

## Critical Issues Fixed

### 1. Infinite Retry Loop Bug (Fixed Dec 20, 2025)
**Problem**: Messages were retrying infinitely without limit, causing runaway CPU and endless audio loops.

**Root Cause**:
- `consumer.py` line 132: `nack(message)` without retry limit
- Commit e4f9a40 fixed ack/nack, exposing the bug

**Solution**:
- Added retry metadata tracking (`retry_count`, `last_retry_time`)
- Implemented exponential backoff (0.5s → 1s → 2s → 5s)
- Max 3 retries, then drop message
- Messages with `no_callback` reason are acked (dropped) instead of retried

**Files Modified**:
- `src/voice_handler/queue/consumer.py` - Added retry logic
- `src/voice_handler/queue/broker.py` - Metadata initialization and preservation
- `config.json` - Added `queue_settings` section
- `src/voice_handler/queue/daemon.py` - Pass retry config to consumer

### 2. Missing TTS Dependencies (Fixed Dec 20, 2025)
**Problem**: OpenAI TTS not working - fell back to system TTS silently.

**Root Cause**: Dependencies not installed (`openai`, `sounddevice`, `soundfile`)

**Solution**: Run `uv sync` to install dependencies from `pyproject.toml`

## Configuration

### Environment Variables (.env)
```bash
OPENAI_API_KEY=sk-proj-...
TTS_PROVIDER=openai
OPENAI_VOICE=nova
USE_ASYNC_QUEUE=true
```

### Queue Settings (config.json)
```json
{
  "queue_settings": {
    "max_retries": 3,
    "retry_backoff_base": 0.5
  }
}
```

## Common Issues & Solutions

### Issue: No audio output
**Diagnosis**:
```bash
cd ~/.claude/hooks/voice_notifications
uv run python -c "import openai, sounddevice, soundfile; print('✓ Deps OK')"
```

**Fix**: Run `uv sync` to install dependencies

### Issue: Runaway daemon consuming CPU
**Diagnosis**: Check CPU usage: `ps aux | grep voice_handler`

**Fix**:
1. Stop daemon: `pkill -f voice_handler.queue.daemon`
2. Clear queue: `uv run python -c "from voice_handler.queue.broker import get_broker; get_broker().clear()"`
3. Restart: `uv run python -m voice_handler.queue.daemon --start`

### Issue: Messages not being processed
**Check queue size**:
```bash
cd ~/.claude/hooks/voice_notifications
uv run python -c "from voice_handler.queue.broker import get_broker; print(f'Queue: {get_broker().size()}')"
```

**Check daemon running**:
```bash
ps aux | grep voice_handler.queue.daemon | grep -v grep
```

## Logs

### Log Locations
- `/tmp/claude_voice.log` - **MAIN DAEMON LOG** - All TTS events, queue operations, errors (macOS/Linux)
- `logs/hook_errors.log` - Hook entry point errors only

### Checking Logs
```bash
# Main daemon log (most important)
tail -50 /tmp/claude_voice.log

# Hook errors
cat ~/.claude/hooks/voice_notifications/logs/hook_errors.log

# Watch daemon log in real-time
tail -f /tmp/claude_voice.log
```

### Log Rotation
- Max size: 10MB (auto-rotates to `.log.old`)
- Format: `YYYY-MM-DD HH:MM:SS | LEVEL | function | message`

## Development

### Dependencies
Install with: `uv sync`

Required:
- openai>=1.0.0
- sounddevice>=0.4.6
- soundfile>=0.12.1
- persist-queue[extra]>=1.0.0

### Testing TTS
```bash
cd ~/.claude/hooks/voice_notifications
uv run python -c "
from voice_handler.queue.producer import quick_speak
quick_speak('Test message')
"
```

### Running Daemon
```bash
cd ~/.claude/hooks/voice_notifications
uv run python -m voice_handler.queue.daemon --start
uv run python -m voice_handler.queue.daemon --stop
```

## Queue Retry Behavior

### Retry Logic
- **Max retries**: 3 (configurable)
- **Backoff schedule**:
  - Retry 1: 0.5s delay
  - Retry 2: 1.0s delay
  - Retry 3: 2.0s delay
  - After max: Message dropped and logged

### Failure Reasons
- `no_callback` - Permanent failure, ack immediately (no retry)
- `exception` - Transient failure, retry with backoff

### Monitoring Retries
Check daemon logs for retry warnings:
```
Message failed (retry #1/3): Testing...
Message failed (retry #2/3): Testing...
Message exceeded max retries (3), dropping: Testing...
```

## Troubleshooting Checklist

1. ✅ Dependencies installed? `uv sync`
2. ✅ Daemon running? `ps aux | grep voice_handler`
3. ✅ Queue size normal? Should be 0 or small number
4. ✅ CPU usage low? Should be <1%
5. ✅ OpenAI API key set? Check `.env`
6. ✅ Logs clean? Check `logs/hook_errors.log`

## Key Files

- `hook_entry.py` - Main hook entry point
- `src/voice_handler/queue/consumer.py` - **CRITICAL** - Retry logic here
- `src/voice_handler/queue/broker.py` - Queue and message model
- `src/voice_handler/tts/provider.py` - TTS implementation
- `config.json` - Configuration including queue settings
- `.env` - Secrets and environment config

## Recent Changes

### Dec 20, 2025
- Fixed infinite retry loop in consumer
- Added exponential backoff with max retries
- Fixed missing TTS dependencies issue
- Updated config with queue_settings
- Created this documentation file
