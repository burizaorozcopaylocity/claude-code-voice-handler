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
import fcntl
import errno
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

    def _acquire_pid_lock(self) -> bool:
        """
        Adquiere lock exclusivo en PID file, retorna True si exitoso.

        Usa fcntl para garantizar que solo un proceso puede iniciar el daemon
        a la vez, previniendo race conditions.

        Returns:
            bool: True si se adquirió el lock, False si otro proceso lo tiene
        """
        if sys.platform == 'win32':
            # Windows no tiene fcntl, usar lógica básica
            # (En Windows es menos probable tener race conditions por cómo funciona subprocess)
            return True

        lock_path = str(self.pid_file) + '.lock'

        try:
            # Abrir archivo de lock (crear si no existe)
            self.lock_fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)

            # Intentar lock exclusivo no-bloqueante
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

            if self.logger:
                self.logger.log_debug(f"Acquired PID lock: {lock_path}")

            return True

        except (OSError, IOError) as e:
            if e.errno in (errno.EACCES, errno.EAGAIN):
                # Otro proceso tiene el lock
                if self.logger:
                    self.logger.log_debug("Another process holds the PID lock")
                return False
            # Otro tipo de error, propagar
            raise

    def _release_pid_lock(self):
        """Libera lock del PID file."""
        if sys.platform == 'win32':
            return  # No hay lock en Windows

        if hasattr(self, 'lock_fd'):
            try:
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                os.close(self.lock_fd)
                delattr(self, 'lock_fd')

                if self.logger:
                    self.logger.log_debug("Released PID lock")

            except Exception as e:
                if self.logger:
                    self.logger.log_warning(f"Error releasing lock: {e}")

    def _cleanup_stale_pid(self) -> bool:
        """
        Limpia PID file si proceso ya no existe.

        Returns:
            bool: True si se limpió un PID obsoleto, False si no había nada que limpiar
        """
        pid = self._read_pid()
        if pid and not self._is_process_running(pid):
            if self.logger:
                self.logger.log_warning(f"Removing stale PID file for non-running process {pid}")
            self.pid_file.unlink(missing_ok=True)
            return True
        return False

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
        # CRITICAL: Acquire lock BEFORE any checks to prevent race conditions
        if not self._acquire_pid_lock():
            if self.logger:
                self.logger.log_info("Daemon already starting/running (lock held by another process)")
            # Check if actually running (another process may have started it)
            return self.is_running()

        try:
            # Now that we have the lock, check if daemon is running
            if self.is_running():
                if self.logger:
                    self.logger.log_debug("Daemon already running")
                return True

            if self.logger:
                self.logger.log_info("Attempting to start daemon...")

        except Exception as e:
            if self.logger:
                self.logger.log_error("Error in start() pre-checks", exception=e)
            self._release_pid_lock()
            return False

        try:
            # Get project directory and daemon script path
            project_dir = Path(__file__).parent.parent.parent.parent
            daemon_script = Path(__file__)  # This file

            # Prepare environment with PYTHONPATH
            env = os.environ.copy()
            src_path = str(project_dir / 'src')
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{src_path}:{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = src_path

            # Start the daemon process using native Python (no virtual env)
            if sys.platform == 'win32':
                # Windows: use CREATE_NEW_CONSOLE with hidden window
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE

                process = subprocess.Popen(
                    ['python3.14', str(daemon_script), '--worker'],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    startupinfo=startupinfo,
                    cwd=str(project_dir),
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                # Unix: fork and daemonize with native Python
                process = subprocess.Popen(
                    ['python3.14', str(daemon_script), '--worker'],
                    start_new_session=True,
                    cwd=str(project_dir),
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            # Wait a moment and check if it started
            time.sleep(0.5)
            if self._is_process_running(process.pid):
                self._write_pid(process.pid)
                if self.logger:
                    self.logger.log_info(f"Daemon started successfully with PID {process.pid}")
                return True
            else:
                if self.logger:
                    self.logger.log_error("Daemon process spawned but failed to stay running")
                return False

        except Exception as e:
            if self.logger:
                self.logger.log_error("Error starting daemon", exception=e)
            return False

        finally:
            # ALWAYS release the lock when exiting start()
            self._release_pid_lock()

    def start_dev(self) -> bool:
        """
        Start the daemon in development mode with auto-reload (background).

        Similar to start() but launches with --dev flag for auto-reload.
        The process runs in background with watchdog monitoring code changes.

        Returns:
            bool: True if daemon is running (started or already running)
        """
        # CRITICAL: Acquire lock BEFORE any checks to prevent race conditions
        if not self._acquire_pid_lock():
            if self.logger:
                self.logger.log_info("Daemon already starting/running (lock held by another process)")
            return self.is_running()

        try:
            # Now that we have the lock, check if daemon is running
            if self.is_running():
                if self.logger:
                    self.logger.log_debug("Daemon already running")
                return True

            if self.logger:
                self.logger.log_info("Starting daemon in DEV MODE with auto-reload...")

        except Exception as e:
            if self.logger:
                self.logger.log_error("Error in start_dev() pre-checks", exception=e)
            self._release_pid_lock()
            return False

        try:
            # Get project directory and daemon script path
            project_dir = Path(__file__).parent.parent.parent.parent
            daemon_script = Path(__file__)  # This file

            # Prepare environment with PYTHONPATH
            env = os.environ.copy()
            src_path = str(project_dir / 'src')
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{src_path}:{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = src_path

            # Start the daemon process in DEV MODE using native Python
            if sys.platform == 'win32':
                # Windows: use CREATE_NEW_CONSOLE with hidden window
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE

                process = subprocess.Popen(
                    ['python3.14', str(daemon_script), '--dev-background'],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    startupinfo=startupinfo,
                    cwd=str(project_dir),
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                # Unix: fork and daemonize with native Python in dev mode
                process = subprocess.Popen(
                    ['python3.14', str(daemon_script), '--dev-background'],
                    start_new_session=True,
                    cwd=str(project_dir),
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            # Wait a moment and check if it started
            time.sleep(0.5)
            if self._is_process_running(process.pid):
                self._write_pid(process.pid)
                if self.logger:
                    self.logger.log_info(f"Daemon started in DEV MODE with PID {process.pid}")
                return True
            else:
                if self.logger:
                    self.logger.log_error("Daemon DEV process spawned but failed to stay running")
                return False

        except Exception as e:
            if self.logger:
                self.logger.log_error("Error starting daemon in dev mode", exception=e)
            return False

        finally:
            # ALWAYS release the lock when exiting start_dev()
            self._release_pid_lock()

    def stop(self) -> bool:
        """
        Stop the daemon if running.

        Returns:
            bool: True if daemon was stopped
        """
        pid = self._read_pid()
        if not pid:
            if self.logger:
                self.logger.log_debug("No PID file found, daemon not running")
            return True

        if self.logger:
            self.logger.log_info(f"Stopping daemon (PID {pid})...")

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
                self.logger.log_info("Daemon stopped successfully")
            return True

        except Exception as e:
            if self.logger:
                self.logger.log_error(f"Error stopping daemon (PID {pid})", exception=e)
            return False

    def restart(self) -> bool:
        """Restart the daemon."""
        self.stop()
        time.sleep(1)
        return self.start()

    def start_worker_subprocess(self):
        """
        Start a worker subprocess without managing PID file.

        This is used by AutoReloader in DEV mode where the main --dev-background
        process owns the PID file, and we just need to spawn/respawn worker subprocesses.

        Returns:
            subprocess.Popen: The worker process object
        """
        # Get project directory and daemon script path
        project_dir = Path(__file__).parent.parent.parent.parent
        daemon_script = Path(__file__)

        # Prepare environment with PYTHONPATH
        env = os.environ.copy()
        src_path = str(project_dir / 'src')
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{src_path}:{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = src_path

        # Start worker subprocess
        if self.logger:
            self.logger.log_info("Starting worker subprocess...")

        process = subprocess.Popen(
            ['python3.14', str(daemon_script), '--worker'],
            cwd=str(project_dir),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Give it a moment to start
        time.sleep(0.3)

        if self._is_process_running(process.pid):
            if self.logger:
                self.logger.log_info(f"Worker subprocess started with PID {process.pid}")
            return process
        else:
            if self.logger:
                self.logger.log_error("Worker subprocess failed to start")
            return None

    def ensure_running(self) -> bool:
        """
        Ensure the daemon is running, starting it if necessary.

        This is called by hooks to auto-start the daemon.
        Automatically uses dev mode if DEV_MODE=true in environment.

        Uses locking to prevent multiple daemons from starting simultaneously.
        """
        # CRITICAL: Acquire lock FIRST to prevent race conditions
        # Multiple hooks may call this simultaneously
        if not self._acquire_pid_lock():
            # Another process is starting the daemon or it's already running
            if self.logger:
                self.logger.log_debug("Another process holds lock, assuming daemon is starting/running")
            # Wait a moment and check if daemon is running
            import time
            time.sleep(0.5)
            running = self.is_running()
            return running

        try:
            # Now that we have the lock, clean up stale PID files
            self._cleanup_stale_pid()

            # Double-check if daemon is running (after acquiring lock)
            if self.is_running():
                if self.logger:
                    self.logger.log_debug("Daemon already running")
                return True

            # Check if DEV_MODE is enabled
            dev_mode = os.environ.get('DEV_MODE', 'false').lower() == 'true'

            # Start daemon (start() or start_dev() will handle the lock)
            # We need to release OUR lock first since start methods acquire their own
            self._release_pid_lock()

            if dev_mode:
                return self.start_dev()
            else:
                return self.start()

        except Exception as e:
            if self.logger:
                self.logger.log_error("Error in ensure_running()", exception=e)
            self._release_pid_lock()
            return False


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

    # NOTE: We do NOT write PID file here anymore because:
    # - In normal mode, the parent daemon.start() writes the PID
    # - In DEV mode, the --dev-background process owns the PID file
    # Writing here would overwrite the parent's PID, causing issues

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


def run_with_auto_reload(background=False):
    """
    Run daemon with auto-reload on code changes (dev mode).

    This is a development mode that watches for Python file changes
    and automatically restarts the daemon with fresh code.

    Args:
        background: If True, run as daemon in background (used by --dev-background)
    """
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        print("ERROR: watchdog not installed. Run: uv sync --extra dev")
        sys.exit(1)

    from voice_handler.utils.logger import VoiceLogger
    from voice_handler.dev.reloader import AutoReloader

    # Initialize logger
    logger = VoiceLogger()
    logger.log_info("🎸 Starting daemon in DEV MODE with auto-reload")

    # Determine watch directory
    project_root = Path(__file__).parent.parent.parent.parent
    watch_dir = project_root / "src" / "voice_handler"

    if not watch_dir.exists():
        logger.log_error(f"Watch directory not found: {watch_dir}")
        sys.exit(1)

    logger.log_info(f"Watching: {watch_dir}")

    # Create daemon and reloader
    daemon = VoiceDaemon(logger=logger)
    reloader = AutoReloader(
        daemon=daemon,
        watch_dirs=[watch_dir],
        logger=logger
    )

    # Start auto-reload loop
    if background:
        # Background mode: start observer and daemon, then return
        # The observer runs in a background thread
        reloader.start_background()
    else:
        # Foreground mode: blocks until Ctrl+C
        reloader.start()


def main():
    """CLI entry point for the daemon."""
    import argparse

    parser = argparse.ArgumentParser(description="Voice Handler Daemon")
    parser.add_argument('--worker', action='store_true', help='Run as worker process')
    parser.add_argument('--start', action='store_true', help='Start the daemon')
    parser.add_argument('--stop', action='store_true', help='Stop the daemon')
    parser.add_argument('--restart', action='store_true', help='Restart the daemon')
    parser.add_argument('--status', action='store_true', help='Show daemon status')
    parser.add_argument('--dev', action='store_true', help='Start with auto-reload (development mode)')
    parser.add_argument('--dev-background', action='store_true', help='Start with auto-reload in background (internal use)')

    args = parser.parse_args()

    daemon = VoiceDaemon()

    if args.worker:
        run_worker()
    elif args.dev_background:
        run_with_auto_reload(background=True)
    elif args.dev:
        run_with_auto_reload(background=False)
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
