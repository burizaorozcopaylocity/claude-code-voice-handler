#!/usr/bin/env python3
"""
Voice Handler Control Panel - FastAPI Server.

The backstage control center where roadies manage the show.
Provides REST API and WebSocket endpoints for the SPA control panel.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from voice_handler.queue.daemon import VoiceDaemon
from voice_handler.queue.broker import get_broker
from voice_handler.utils.logger import get_logger


# Initialize FastAPI app
app = FastAPI(
    title="Voice Handler Control Panel",
    description="🎸 Rock'n'Roll control center for Claude Code voice notifications",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8765"],  # Vite dev + production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
logger = get_logger()
daemon = VoiceDaemon(logger=logger)
broker = get_broker(logger=logger)

# Get project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.json"
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"


# ==================== Models ====================

class DaemonStatusResponse(BaseModel):
    running: bool
    pid: Optional[int]
    uptime_seconds: int = 0
    messages_processed: int = 0


class QueueStatusResponse(BaseModel):
    size: int
    pending_messages: int


class ConfigUpdateRequest(BaseModel):
    voice_settings: Optional[Dict[str, Any]] = None


class HookToggleRequest(BaseModel):
    hook_name: str
    enabled: bool


class TTSTestRequest(BaseModel):
    text: str
    voice: str = "nova"


# ==================== Routes ====================

@app.get("/")
async def root():
    """Serve the SPA index.html."""
    web_dir = PROJECT_ROOT / "web" / "dist"
    index_file = web_dir / "index.html"

    if index_file.exists():
        return FileResponse(index_file)
    else:
        return {"message": "Voice Handler Control Panel API", "status": "ready"}


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "voice-handler-api"}


@app.get("/api/daemon/status", response_model=DaemonStatusResponse)
async def get_daemon_status():
    """Get current daemon status."""
    status = daemon.get_status()
    return DaemonStatusResponse(
        running=status["running"],
        pid=status["pid"],
        uptime_seconds=status.get("uptime_seconds", 0),
        messages_processed=status.get("messages_processed", 0)
    )


@app.post("/api/daemon/start")
async def start_daemon():
    """Start the voice daemon."""
    if daemon.start():
        return {"status": "started", "message": "Daemon started successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to start daemon")


@app.post("/api/daemon/stop")
async def stop_daemon():
    """Stop the voice daemon."""
    if daemon.stop():
        return {"status": "stopped", "message": "Daemon stopped successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to stop daemon")


@app.post("/api/daemon/restart")
async def restart_daemon():
    """Restart the voice daemon."""
    if daemon.restart():
        return {"status": "restarted", "message": "Daemon restarted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to restart daemon")


@app.get("/api/queue/status", response_model=QueueStatusResponse)
async def get_queue_status():
    """Get current queue status."""
    size = broker.size()
    return QueueStatusResponse(size=size, pending_messages=size)


@app.post("/api/queue/clear")
async def clear_queue():
    """Clear all pending messages in the queue."""
    size_before = broker.size()
    broker.clear()
    return {
        "status": "cleared",
        "messages_cleared": size_before,
        "message": f"Cleared {size_before} pending messages"
    }


@app.get("/api/config")
async def get_config():
    """Get current configuration."""
    if CONFIG_PATH.exists():
        try:
            config = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
            return config
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read config: {str(e)}")
    else:
        return {"voice_settings": {}}


@app.put("/api/config")
async def update_config(request: ConfigUpdateRequest):
    """Update configuration."""
    try:
        # Load current config
        config = {}
        if CONFIG_PATH.exists():
            config = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))

        # Update voice settings
        if request.voice_settings:
            if "voice_settings" not in config:
                config["voice_settings"] = {}
            config["voice_settings"].update(request.voice_settings)

        # Save config
        CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding='utf-8')

        return {"status": "updated", "config": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")


@app.get("/api/hooks")
async def get_hooks():
    """Get current hooks configuration from settings.json."""
    if SETTINGS_PATH.exists():
        try:
            settings = json.loads(SETTINGS_PATH.read_text(encoding='utf-8'))
            hooks = settings.get("hooks", {})

            # Return simplified hook status
            hook_status = {}
            for hook_name in ["SessionStart", "UserPromptSubmit", "PreToolUse",
                             "PostToolUse", "Stop", "Notification", "SubagentStop"]:
                hook_status[hook_name] = {
                    "enabled": hook_name in hooks and len(hooks[hook_name]) > 0,
                    "config": hooks.get(hook_name, [])
                }

            return hook_status
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read hooks: {str(e)}")
    else:
        raise HTTPException(status_code=404, detail="Settings file not found")


@app.post("/api/hooks/toggle")
async def toggle_hook(request: HookToggleRequest):
    """Enable or disable a specific hook."""
    try:
        if not SETTINGS_PATH.exists():
            raise HTTPException(status_code=404, detail="Settings file not found")

        settings = json.loads(SETTINGS_PATH.read_text(encoding='utf-8'))
        hooks = settings.get("hooks", {})

        hook_name = request.hook_name

        if request.enabled:
            # Hook should be enabled - ensure it exists
            if hook_name not in hooks or len(hooks[hook_name]) == 0:
                return {
                    "status": "warning",
                    "message": f"Hook {hook_name} has no configuration to enable. Please configure it in settings.json first."
                }
        else:
            # Disable by removing the hook
            if hook_name in hooks:
                hooks[hook_name] = []

        settings["hooks"] = hooks
        SETTINGS_PATH.write_text(json.dumps(settings, indent=2), encoding='utf-8')

        return {
            "status": "updated",
            "hook": hook_name,
            "enabled": request.enabled,
            "message": f"Hook {hook_name} {'enabled' if request.enabled else 'disabled'}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle hook: {str(e)}")


@app.post("/api/tts/test")
async def test_tts(request: TTSTestRequest):
    """Test TTS with a custom message."""
    try:
        from voice_handler.queue.producer import quick_speak
        quick_speak(request.text, voice=request.voice)
        return {
            "status": "queued",
            "text": request.text,
            "voice": request.voice,
            "message": "TTS message queued successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue TTS: {str(e)}")


# WebSocket for real-time log streaming
active_websockets = []

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for streaming logs in real-time."""
    await websocket.accept()
    active_websockets.append(websocket)

    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connection",
            "message": "Connected to log stream"
        })

        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            # Echo back for ping/pong
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        active_websockets.remove(websocket)


# Mount static files (after building the React app)
web_dist = PROJECT_ROOT / "web" / "dist"
if web_dist.exists():
    app.mount("/", StaticFiles(directory=str(web_dist), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")
