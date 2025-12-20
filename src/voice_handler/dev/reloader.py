#!/usr/bin/env python3
"""
Auto-reload module for voice handler daemon - The Soundcheck Engineer.

Like a soundcheck engineer who tweaks equipment on the fly,
this module watches code changes and hot-reloads the daemon.
"""

import time
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class DebouncedEventHandler(FileSystemEventHandler):
    """
    Handles file system events with debouncing.

    Groups rapid file changes (like 'Save All' in editors) into a single
    reload event to avoid restart storms.
    """

    def __init__(self, callback, debounce_seconds=1.5, logger=None):
        """
        Initialize the debounced event handler.

        Args:
            callback: Function to call after debounce period
            debounce_seconds: Seconds to wait after last change
            logger: VoiceLogger instance for logging
        """
        super().__init__()
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self.logger = logger
        self._last_change_time = None
        self._pending_files = set()
        self._timer = None
        self._lock = threading.Lock()

    def on_modified(self, event):
        """Handle file modification events."""
        # Ignore directories
        if event.is_directory:
            return

        # Only watch .py files
        if not event.src_path.endswith('.py'):
            return

        # Ignore __pycache__ and compiled files
        if '__pycache__' in event.src_path or event.src_path.endswith('.pyc'):
            return

        with self._lock:
            # Track changed file
            self._pending_files.add(event.src_path)
            self._last_change_time = time.time()

            # Cancel existing timer and start new one
            if self._timer:
                self._timer.cancel()

            self._timer = threading.Timer(self.debounce_seconds, self._trigger_restart)
            self._timer.start()

    def _trigger_restart(self):
        """Called after debounce period with no new changes."""
        with self._lock:
            if not self._pending_files:
                return

            if self.logger:
                # Show which files changed
                file_names = ', '.join(Path(f).name for f in self._pending_files)
                self.logger.log_info(f"Code changes detected: {file_names}")

            # Clear pending files
            self._pending_files.clear()

        # Call the restart callback
        self.callback()

    def stop(self):
        """Stop any pending timers."""
        with self._lock:
            if self._timer:
                self._timer.cancel()
                self._timer = None


class AutoReloader:
    """
    Manages auto-reload of daemon on file changes.

    Watches the source directory and automatically restarts
    the daemon when Python files are modified.
    """

    def __init__(self, daemon, watch_dirs, logger=None):
        """
        Initialize the auto-reloader.

        Args:
            daemon: VoiceDaemon instance to restart
            watch_dirs: List of directories to watch
            logger: VoiceLogger instance for logging
        """
        self.daemon = daemon
        self.watch_dirs = watch_dirs if isinstance(watch_dirs, list) else [watch_dirs]
        self.logger = logger
        self.observer = None
        self._running = False
        self._worker_process = None  # Track worker subprocess in DEV mode

    def start_background(self):
        """
        Start watching in background mode (non-blocking).

        The observer runs in a daemon thread and the method returns immediately.
        Used when daemon is started via ensure_running() with DEV_MODE=true.
        """
        if self.logger:
            self.logger.log_info("Auto-reload enabled (background mode)")

        # Create event handler
        handler = DebouncedEventHandler(
            callback=self._restart_daemon,
            debounce_seconds=1.5,
            logger=self.logger
        )

        # Set up observer
        self.observer = Observer()
        self.observer.daemon = True  # Daemon thread - will exit when main process exits
        for watch_dir in self.watch_dirs:
            watch_path = str(watch_dir)
            self.observer.schedule(handler, watch_path, recursive=True)

        self.observer.start()
        self._running = True

        # Start initial worker subprocess
        if self.logger:
            self.logger.log_info("Starting initial worker subprocess...")
        self._worker_process = self.daemon.start_worker_subprocess()

        if not self._worker_process:
            if self.logger:
                self.logger.log_error("Failed to start worker subprocess")
            self._running = False
            return

        # Keep process alive (blocks but observer runs in background thread)
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            if self.logger:
                self.logger.log_info("Auto-reload stopped by user (Ctrl+C)")
            self.stop()

    def start(self):
        """
        Start watching and automatically restart daemon on changes.

        This method blocks until interrupted (Ctrl+C).
        """
        if self.logger:
            self.logger.log_info("Auto-reload enabled - watching for code changes")

        # Create event handler
        handler = DebouncedEventHandler(
            callback=self._restart_daemon,
            debounce_seconds=1.5,
            logger=self.logger
        )

        # Set up observer
        self.observer = Observer()
        for watch_dir in self.watch_dirs:
            watch_path = str(watch_dir)
            self.observer.schedule(handler, watch_path, recursive=True)
            if self.logger:
                self.logger.log_info(f"Watching: {watch_path}")

        self.observer.start()
        self._running = True

        # Start initial worker subprocess
        if self.logger:
            self.logger.log_info("Starting initial worker subprocess...")
        self._worker_process = self.daemon.start_worker_subprocess()

        if not self._worker_process:
            if self.logger:
                self.logger.log_error("Failed to start worker subprocess")
            self.stop()
            return

        try:
            # Keep running and watching
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            if self.logger:
                self.logger.log_info("Auto-reload stopped by user (Ctrl+C)")
            self.stop()

    def _restart_daemon(self):
        """Restart the worker subprocess (called by event handler)."""
        if self.logger:
            self.logger.log_info("Restarting worker due to code changes...")

        try:
            # Stop existing worker if running
            if self._worker_process and self._worker_process.poll() is None:
                if self.logger:
                    self.logger.log_info(f"Stopping worker (PID {self._worker_process.pid})...")
                self._worker_process.terminate()
                self._worker_process.wait(timeout=5)

            # Start fresh worker subprocess
            self._worker_process = self.daemon.start_worker_subprocess()

            if self._worker_process:
                if self.logger:
                    self.logger.log_info("Worker reloaded successfully - back to work!")
            else:
                if self.logger:
                    self.logger.log_error("Failed to restart worker subprocess")
        except Exception as e:
            if self.logger:
                self.logger.log_error("Failed to restart worker", exception=e)

    def stop(self):
        """Stop watching and shut down worker subprocess."""
        self._running = False

        if self.observer:
            if self.logger:
                self.logger.log_info("Stopping file watcher...")
            self.observer.stop()
            self.observer.join(timeout=5)

        # Stop worker subprocess (don't call daemon.stop() - that would kill the --dev-background process)
        if self._worker_process and self._worker_process.poll() is None:
            if self.logger:
                self.logger.log_info(f"Stopping worker subprocess (PID {self._worker_process.pid})...")
            self._worker_process.terminate()
            try:
                self._worker_process.wait(timeout=5)
            except:
                self._worker_process.kill()  # Force kill if doesn't respond
