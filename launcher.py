#!/usr/bin/env python3
"""
Voice Handler Control Panel Launcher.

Starts both the voice daemon and the web control panel server.
Opens the browser automatically to http://localhost:8765
"""

import os
import sys
import time
import webbrowser
import subprocess
from pathlib import Path


def main():
    print("🎸 Voice Handler Control Panel Launcher")
    print("=" * 50)

    # Get project root
    project_root = Path(__file__).parent
    os.chdir(project_root)

    print(f"📁 Project root: {project_root}")

    # Check if dependencies are installed
    print("\n1️⃣  Checking Python dependencies...")
    try:
        import uvicorn
        import fastapi
        print("   ✅ Python dependencies OK")
    except ImportError:
        print("   ⚠️  Installing Python dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "fastapi", "uvicorn[standard]", "pydantic"
        ])

    # Check if frontend is built
    web_dist = project_root / "web" / "dist"
    if not web_dist.exists():
        print("\n2️⃣  Building frontend...")
        print("   ⚠️  Frontend not built. Please run:")
        print("      cd web && npm install && npm run build")
        print("\n   For development mode, run:")
        print("      cd web && npm run dev")
        print("\n   Then in another terminal, run:")
        print("      uv run python src/voice_handler/api/server.py")
        sys.exit(1)
    else:
        print("\n2️⃣  Frontend build found ✅")

    # Start the daemon if not running
    print("\n3️⃣  Starting voice daemon...")
    from voice_handler.queue.daemon import VoiceDaemon
    from voice_handler.utils.logger import get_logger

    logger = get_logger()
    daemon = VoiceDaemon(logger=logger)

    if daemon.is_running():
        print("   ✅ Daemon already running")
    else:
        if daemon.start():
            print("   ✅ Daemon started")
        else:
            print("   ⚠️  Failed to start daemon")

    # Start the API server
    print("\n4️⃣  Starting API server...")
    print("   🌐 Server will be available at: http://localhost:8765")
    print("   📊 API docs at: http://localhost:8765/docs")
    print("\n   Press Ctrl+C to stop\n")

    # Open browser
    time.sleep(1)
    webbrowser.open("http://localhost:8765")

    # Start uvicorn server
    try:
        import uvicorn
        uvicorn.run(
            "voice_handler.api.server:app",
            host="127.0.0.1",
            port=8765,
            log_level="info",
            reload=False
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        print("   Daemon will continue running in background")
        print("   To stop daemon: uv run python src/voice_handler/queue/daemon.py --stop")


if __name__ == "__main__":
    main()
