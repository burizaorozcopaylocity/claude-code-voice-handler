#!/usr/bin/env python3
"""
Voice Daemon - The Tireless Roadie Manager

Like a production manager who ensures the crew is always ready,
this daemon manages the background TTS worker process.

Features:
- Auto-start on first voice request
- Health monitoring with watchdog
- Graceful restart on failures
- PID file management for process tracking
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path
from typing import Optional
import json


class VoiceDaemon:
    """
    Manages the background voice processing daemon.

    The daemon ensures that voice messages are processed
    even when Claude hooks have already returned.
    """

    def __init__(self, logger=None):
        """Initialize the daemon manager."""
        self.logger = logger

        # PID file location
        if sys.platform == 'win32':
            temp_dir = os.environ.get('TEMP', 'C:\\Temp')
            self.pid_file = Path(temp_dir) / 'claude_voice_daemon.pid'
            self.status_file = Path(temp_dir) / 'claude_voice_daemon.status'
        else:
            self.pid_file = Path('/tmp/claude_voice_daemon.pid')
            self.status_file = Path('/tmp/claude_voice_daemon.status')

    def _read_pid(self) -> Optional[int]:
        """Read PID from file."""
        if self.pid_file.exists():
            try:
                return int(self.pid_file.read_text().strip())
            except (ValueError, IOError):
                pass
        return None

    def _write_pid(self, pid: int):
        """Write PID to file."""
        self.pid_file.write_text(str(pid))

    def _remove_pid(self):
        """Remove PID file."""
        if self.pid_file.exists():
            self.pid_file.unlink()

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process is running."""
        if sys.platform == 'win32':
            try:
                # Windows: use tasklist
                result = subprocess.run(
                    ['tasklist', '/FI', f'PID eq {pid}', '/NH'],
                    capture_output=True,
                    text=True,
                )
                return str(pid) in result.stdout
            except Exception:
                return False
        else:
            # Unix: use kill 0
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False

    def is_running(self) -> bool:
        """Check if the daemon is currently running."""
        pid = self._read_pid()
        if pid:
            return self._is_process_running(pid)
        return False

    def get_status(self) -> dict:
        """Get daemon status information."""
        status = {
            "running": False,
            "pid": None,
            "uptime_seconds": 0,
            "messages_processed": 0,
        }

        pid = self._read_pid()
        if pid and self._is_process_running(pid):
            status["running"] = True
            status["pid"] = pid

            # Read status file if available
            if self.status_file.exists():
                try:
                    status_data = json.loads(self.status_file.read_text())
                    status.update(status_data)
                except Exception:
                    pass

        return status

    def start(self) -> bool:
        """
        Start the daemon if not already running.

        Returns:
            bool: True if daemon is running (started or already running)
        """
        if self.is_running():
            if self.logger:
                self.logger.log_debug("Daemon already running")
            return True

        try:
            # Get project directory and daemon script path
            project_dir = Path(__file__).parent.parent.parent.parent
            daemon_script = Path(__file__)  # This file

            # Start the daemon process using uv run with direct script path
            if sys.platform == 'win32':
                # Windows: use CREATE_NEW_CONSOLE with hidden window (mypy approach)
                # This avoids issues with DETACHED_PROCESS causing console popups
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE

                process = subprocess.Popen(
                    ['uv', 'run', '--project', str(project_dir),
                     'python', str(daemon_script), '--worker'],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    startupinfo=startupinfo,
                    cwd=str(project_dir),
                    env=os.environ.copy(),  # Inherit environment (OPENAI_API_KEY)
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                # Unix: fork and daemonize with uv run
                process = subprocess.Popen(
                    ['uv', 'run', '--project', str(project_dir),
                     'python', str(daemon_script), '--worker'],
                    start_new_session=True,
                    cwd=str(project_dir),
                    env=os.environ.copy(),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            # Wait a moment and check if it started
            time.sleep(0.5)
            if self._is_process_running(process.pid):
                self._write_pid(process.pid)
                if self.logger:
                    self.logger.log_info(f"Daemon started with PID {process.pid}")
                return True
            else:
                if self.logger:
                    self.logger.log_error("Daemon failed to start")
                return False

        except Exception as e:
            if self.logger:
                self.logger.log_error("Error starting daemon", exception=e)
            return False

    def stop(self) -> bool:
        """
        Stop the daemon if running.

        Returns:
            bool: True if daemon was stopped
        """
        pid = self._read_pid()
        if not pid:
            return True

        try:
            if sys.platform == 'win32':
                subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True)
            else:
                os.kill(pid, signal.SIGTERM)

            # Wait for process to end
            for _ in range(10):
                if not self._is_process_running(pid):
                    break
                time.sleep(0.5)

            self._remove_pid()
            if self.logger:
                self.logger.log_info("Daemon stopped")
            return True

        except Exception as e:
            if self.logger:
                self.logger.log_error("Error stopping daemon", exception=e)
            return False

    def restart(self) -> bool:
        """Restart the daemon."""
        self.stop()
        time.sleep(1)
        return self.start()

    def ensure_running(self) -> bool:
        """
        Ensure the daemon is running, starting it if necessary.

        This is called by hooks to auto-start the daemon.
        """
        if self.is_running():
            return True
        return self.start()


def run_worker():
    """
    Run the daemon worker process.

    This is the main entry point when running as a daemon.
    """
    # CRITICAL: Load .env FIRST before any imports
    from dotenv import load_dotenv
    from pathlib import Path as EnvPath
    env_path = EnvPath.home() / ".claude" / "hooks" / "voice_notifications" / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=True)

    from voice_handler.queue.consumer import QueueConsumer
    from voice_handler.queue.broker import get_broker
    from voice_handler.tts.provider import TTSProvider
    from voice_handler.utils.logger import VoiceLogger

    # Initialize components
    logger = VoiceLogger()
    logger.log_info("Voice daemon worker starting...")

    # Write PID file
    daemon = VoiceDaemon(logger=logger)
    daemon._write_pid(os.getpid())

    # Load configuration
    config = {}
    config_path = Path(__file__).parent.parent.parent.parent / "config.json"
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding='utf-8'))
            logger.log_info(f"Loaded config from {config_path}")
        except Exception as e:
            logger.log_warning(f"Could not load config: {e}")

    # Initialize TTS provider with config
    tts = TTSProvider(config=config, logger=logger)

    # Get queue settings from config
    queue_config = config.get("queue_settings", {})
    max_retries = queue_config.get("max_retries", 3)
    retry_backoff_base = queue_config.get("retry_backoff_base", 0.5)

    # Create consumer with TTS callback and retry config
    consumer = QueueConsumer(
        logger=logger,
        max_retries=max_retries,
        retry_backoff_base=retry_backoff_base,
    )
    consumer.set_speak_callback(lambda text, voice: tts.speak(text, voice))

    # Set up signal handlers
    def handle_signal(signum, frame):
        logger.log_info(f"Received signal {signum}, shutting down...")
        consumer.stop(wait=False)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    # Start processing
    logger.log_info("Voice daemon worker ready - the show begins!")

    try:
        # Run consumer in main thread (blocking)
        consumer._running = True
        consumer._consumer_loop()
    except KeyboardInterrupt:
        logger.log_info("Keyboard interrupt received")
    finally:
        daemon._remove_pid()
        logger.log_info("Voice daemon worker stopped - B.O.!")


def main():
    """CLI entry point for the daemon."""
    import argparse

    parser = argparse.ArgumentParser(description="Voice Handler Daemon")
    parser.add_argument('--worker', action='store_true', help='Run as worker process')
    parser.add_argument('--start', action='store_true', help='Start the daemon')
    parser.add_argument('--stop', action='store_true', help='Stop the daemon')
    parser.add_argument('--restart', action='store_true', help='Restart the daemon')
    parser.add_argument('--status', action='store_true', help='Show daemon status')

    args = parser.parse_args()

    daemon = VoiceDaemon()

    if args.worker:
        run_worker()
    elif args.start:
        if daemon.start():
            print("Daemon started successfully")
        else:
            print("Failed to start daemon")
            sys.exit(1)
    elif args.stop:
        if daemon.stop():
            print("Daemon stopped")
        else:
            print("Failed to stop daemon")
            sys.exit(1)
    elif args.restart:
        if daemon.restart():
            print("Daemon restarted")
        else:
            print("Failed to restart daemon")
            sys.exit(1)
    elif args.status:
        status = daemon.get_status()
        print(f"Running: {status['running']}")
        print(f"PID: {status['pid']}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
