# 🎸 Voice Handler Control Panel

> Your backstage pass to managing Claude Code voice notifications!

## 🚀 Quick Start

### Launch the Control Panel

```bash
cd ~/.claude/hooks/voice_notifications
uv run python launcher.py
```

This will:
1. ✅ Start the voice daemon (if not already running)
2. ✅ Launch the FastAPI server on port 8765
3. ✅ Open your browser to http://localhost:8765

## 📊 Features

### Dashboard Tab
- **Real-time daemon status** - See if the daemon is running, PID, uptime
- **Queue metrics** - View pending messages count
- **Control buttons** - Start, Stop, Restart the daemon

### Queue Tab
- **View pending messages** - See how many messages are in the queue
- **Clear queue** - Remove all pending messages if they've backed up

### Hooks Tab
- **Manage hooks** - Enable/disable individual hooks (SessionStart, UserPromptSubmit, etc.)
- **Recommendations** - Visual indicators for recommended hooks
- **Live toggle** - Switch hooks on/off instantly

### Config Tab
- **TTS Provider** - Choose between OpenAI TTS and System TTS
- **Voice selection** - Pick from 6 OpenAI voices (nova, alloy, echo, fable, onyx, shimmer)
- **Language** - Switch between English and Spanish
- **Personality** - Choose between rockstar, professional, or minimal styles

### Test TTS Tab
- **Voice tester** - Test any voice with custom text
- **Quick phrases** - Pre-loaded test phrases to try out
- **Instant feedback** - Hear your test immediately

## 🎛️ API Endpoints

The control panel exposes a REST API at `http://localhost:8765/api/`:

### Daemon
- `GET /api/daemon/status` - Get daemon status
- `POST /api/daemon/start` - Start daemon
- `POST /api/daemon/stop` - Stop daemon
- `POST /api/daemon/restart` - Restart daemon

### Queue
- `GET /api/queue/status` - Get queue status
- `POST /api/queue/clear` - Clear all messages

### Config
- `GET /api/config` - Get current config
- `PUT /api/config` - Update config

### Hooks
- `GET /api/hooks` - Get all hooks status
- `POST /api/hooks/toggle` - Enable/disable a hook

### TTS
- `POST /api/tts/test` - Test TTS with custom message

### API Documentation
Visit `http://localhost:8765/docs` for interactive Swagger UI documentation.

## 🛠️ Development Mode

For frontend development with hot-reload:

```bash
# Terminal 1: Start backend
cd ~/.claude/hooks/voice_notifications
uv run python src/voice_handler/api/server.py

# Terminal 2: Start frontend dev server
cd ~/.claude/hooks/voice_notifications/web
npm run dev
```

Then visit http://localhost:5173 for hot-reload development.

## 📦 Building

To rebuild the frontend after making changes:

```bash
cd ~/.claude/hooks/voice_notifications/web
npm run build
```

## 🔧 Troubleshooting

### Port 8765 already in use
```bash
# Find and kill the process using port 8765
lsof -ti:8765 | xargs kill -9
```

### Frontend not loading
Make sure you've built the frontend:
```bash
cd ~/.claude/hooks/voice_notifications/web
npm install
npm run build
```

### API not responding
Check if FastAPI dependencies are installed:
```bash
cd ~/.claude/hooks/voice_notifications
uv sync
```

### Daemon not starting
Check daemon status:
```bash
cd ~/.claude/hooks/voice_notifications
uv run python src/voice_handler/queue/daemon.py --status
```

## 🎨 Customization

The control panel uses:
- **React** for the frontend
- **Tailwind CSS** for styling (purple/rock theme)
- **FastAPI** for the backend
- **React Query** for state management
- **Vite** for building

You can customize the theme by editing `web/tailwind.config.js`.

## 📝 Notes

- The control panel automatically refreshes data every 2 seconds
- All config changes are saved to `config.json`
- Hook changes modify `~/.claude/settings.json`
- The daemon continues running in the background even after closing the control panel

---

**Rock on!** 🎸
