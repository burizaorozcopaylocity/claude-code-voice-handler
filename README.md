# Claude Code Voice Handler 🎸

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenAI TTS](https://img.shields.io/badge/TTS-OpenAI-00A67E.svg)](https://platform.openai.com/docs/guides/text-to-speech)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> *"Shine on you crazy coder!"* - Cosmic Eddie, your AI roadie

A **psychedelic rock-themed** voice notification system for [Claude Code](https://claude.ai/code) that makes your coding sessions feel like a legendary concert. Each session gets a unique voice, contextual AI commentary via Qwen, and **non-blocking async processing** so Claude never misses a beat.

## ✨ Features

### 🎤 Multi-Voice Sessions
Each Claude Code tab gets a **unique OpenAI TTS voice** - know which instance is speaking without looking!
- 6 voices: `nova`, `alloy`, `echo`, `fable`, `onyx`, `shimmer`
- Automatic assignment, consistent per session
- 4-hour expiry for voice recycling

### 🎸 Qwen AI Rock Personality
**Cosmic Eddie** - your AI roadie from the golden age of psychedelic rock:
- References Pink Floyd, Led Zeppelin, Hendrix, The Doors
- Contextual commentary on your tasks
- Rock metaphors: bugs = feedback, deploy = encore, refactor = new arrangement

### ⚡ Non-Blocking Async Queue
Claude hooks return **instantly** - TTS processing happens in the background:
- SQLite-backed persistent queue (survives crashes)
- Background daemon worker
- Priority-based message ordering
- Auto-start on first voice request

### 🔊 Smart TTS
- **OpenAI TTS** with GPT-4o-mini text compression
- Automatic fallback to system TTS
- Speech deduplication
- Inter-process locking (no overlapping audio)

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/burizaorozcopaylocity/claude-code-voice-handler.git ~/.claude/hooks/voice_notifications
cd ~/.claude/hooks/voice_notifications

# Install in development mode
pip install -e ".[dev]"

# For Qwen AI support (optional)
npm install -g qwen-code
```

### Configuration

1. **Set your OpenAI API key:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

2. **Copy and customize config:**
```bash
cp config.example.json config.json
```

3. **Edit `config.json`:**
```json
{
  "voice_settings": {
    "tts_provider": "openai",
    "openai_voice": "onyx",
    "user_nickname": "YourName",
    "personality": "rockstar"
  }
}
```

### Configure Claude Code Hooks

Add to your Claude Code settings (`~/.claude/settings.json`):

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "type": "command",
        "command": "python -m voice_handler --hook UserPromptSubmit"
      }
    ],
    "Stop": [
      {
        "type": "command",
        "command": "python -m voice_handler --hook Stop"
      }
    ]
  }
}
```

## 📁 Project Structure

```
claude-code-voice-handler/
├── pyproject.toml              # Modern Python packaging (PEP 517)
├── README.md                   # You are here!
├── config.example.json         # Configuration template
│
├── src/voice_handler/          # Main package
│   ├── __init__.py
│   ├── __main__.py             # CLI entry point
│   ├── cli.py                  # Argument parsing
│   │
│   ├── core/                   # Core business logic
│   │   ├── handler.py          # Main orchestrator
│   │   ├── state.py            # State management
│   │   └── session.py          # Session-voice mapping
│   │
│   ├── tts/                    # Text-to-Speech providers
│   │   └── provider.py         # OpenAI + System TTS
│   │
│   ├── ai/                     # AI Integrations
│   │   ├── qwen.py             # Qwen context generator
│   │   └── prompts.py          # Rock personality prompts 🎸
│   │
│   ├── queue/                  # Async Processing
│   │   ├── broker.py           # SQLite message queue
│   │   ├── producer.py         # Fast message enqueueing
│   │   ├── consumer.py         # Background TTS worker
│   │   └── daemon.py           # Daemon process manager
│   │
│   └── utils/                  # Utilities
│       ├── logger.py           # Structured logging
│       ├── dedup.py            # Message deduplication
│       ├── transcript.py       # Claude transcript reader
│       └── lock.py             # Cross-process speech locking
│
├── tests/                      # Test suite
│   ├── test_handler.py
│   ├── test_queue.py
│   └── test_e2e.py
│
└── scripts/                    # Setup and utility scripts
    └── install.py
```

## 🎵 How It Works

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Claude Hook    │────▶│  SQLite Queue    │────▶│  Background     │
│  (returns fast) │     │  (persist-queue) │     │  Daemon         │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
                                               ┌─────────────────┐
                                               │  Qwen AI        │
                                               │  (rock context) │
                                               └────────┬────────┘
                                                         │
                                                         ▼
                                               ┌─────────────────┐
                                               │  OpenAI TTS     │
                                               │  (speaks aloud) │
                                               └─────────────────┘
```

1. **Hook fires** → Producer queues message → Returns instantly (Claude continues!)
2. **Daemon processes** → Qwen generates rock commentary
3. **TTS speaks** → OpenAI generates audio → Plays through speakers

## 🎤 CLI Commands

```bash
# Start the background daemon
voice-daemon --start

# Check daemon status
voice-daemon --status

# Stop the daemon
voice-daemon --stop

# Run handler directly (for testing)
voice-handler --hook UserPromptSubmit --message "Testing, one two three!"

# Quick speak test
python -c "from voice_handler.queue.producer import quick_speak; quick_speak('Hello rock star!')"
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=voice_handler --cov-report=html

# Run specific tests
pytest tests/test_handler.py -v

# Run E2E tests
pytest tests/test_e2e.py -v --slow
```

## 🎸 Rock Personality Examples

**When starting a task:**
> "¡Shine on, Bernard! Claude va a refactorizar ese módulo como Gilmour afinando para Comfortably Numb!"

**When reading code:**
> "Revisando las partituras cósmicas del proyecto..."

**When completing a task:**
> "¡Encore completado! El público enloquece!"

**When debugging:**
> "Un poco de feedback en la señal, pero lo solucionamos. Hasta Hendrix rompía cuerdas a veces."

**When needing approval:**
> "Hey Bernard! El roadie necesita tu visto bueno!"

## 🔧 Configuration Reference

| Option | Description | Default |
|--------|-------------|---------|
| `tts_provider` | TTS engine (`openai` or `system`) | `openai` |
| `openai_voice` | Preferred voice for first session | `nova` |
| `user_nickname` | Your name for personalized messages | `rockstar` |
| `personality` | Qwen personality style | `rockstar` |
| `speech_rate` | Speed for system TTS | `180` |

## 🔗 Resources

Based on research from:
- [persist-queue](https://github.com/peter-wangxu/persist-queue) - SQLite-backed queues
- [Huey](https://github.com/coleifer/huey) - Lightweight task queue patterns
- [PyOpenSci Guide](https://www.pyopensci.org/python-package-guide/package-structure-code/python-package-structure.html) - Python project structure
- [Backstage Culture](https://www.backstageculture.com/roadie-dictionary-a-list-of-touring-terms/) - Roadie terminology

## 🤝 Contributing

Contributions welcome! This is a fork of [markhilton/claude-code-voice-handler](https://github.com/markhilton/claude-code-voice-handler).

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingSolo`)
3. Commit your changes (`git commit -m 'Add some AmazingSolo'`)
4. Push to the branch (`git push origin feature/AmazingSolo`)
5. Open a Pull Request

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **Mark Hilton** - Original creator
- **Bernard Uriza** - Qwen integration, async queue, rock personality, Windows support
- **Pink Floyd, Led Zeppelin, Hendrix, The Doors** - Eternal inspiration
- **OpenAI** - Amazing TTS API
- **Anthropic** - Claude Code

---

<p align="center">
  <i>"The code is strong with this one. May the riffs be with you."</i><br>
  <b>- Cosmic Eddie</b>
</p>

<p align="center">
  🎸 Rock on! 🎸
</p>
