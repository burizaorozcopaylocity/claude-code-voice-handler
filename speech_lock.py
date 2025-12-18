#!/usr/bin/env python3
"""
Speech lock manager to prevent overlapping announcements across processes.
Cross-platform version (Windows + Unix/macOS)
"""

import time
import os
import sys
from pathlib import Path
from contextlib import contextmanager

# Cross-platform file locking
if sys.platform == 'win32':
    import msvcrt

    def lock_file(fd):
        """Lock file on Windows"""
        msvcrt.locking(fd.fileno(), msvcrt.LK_NBLCK, 1)

    def unlock_file(fd):
        """Unlock file on Windows"""
        try:
            fd.seek(0)
            msvcrt.locking(fd.fileno(), msvcrt.LK_UNLCK, 1)
        except:
            pass
else:
    import fcntl

    def lock_file(fd):
        """Lock file on Unix/macOS"""
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def unlock_file(fd):
        """Unlock file on Unix/macOS"""
        fcntl.flock(fd, fcntl.LOCK_UN)


class SpeechLock:
    """
    File-based lock to prevent multiple processes from speaking simultaneously.
    Cross-platform: uses msvcrt on Windows, fcntl on Unix/macOS.
    """

    def __init__(self, lock_file=None, timeout=10.0):
        """
        Initialize speech lock.

        Args:
            lock_file (str): Path to lock file
            timeout (float): Maximum time to wait for lock
        """
        # Use temp directory appropriate for OS
        if lock_file is None:
            if sys.platform == 'win32':
                temp_dir = os.environ.get('TEMP', 'C:\\Temp')
                lock_file = os.path.join(temp_dir, 'claude_voice_speech.lock')
            else:
                lock_file = '/tmp/claude_voice_speech.lock'

        self.lock_file = Path(lock_file)
        self.timeout = timeout
        self.lock_fd = None

        # Ensure lock file directory exists
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        # Ensure lock file exists
        self.lock_file.touch()

    def _get_time_file(self):
        """Get path to last speech time file"""
        if sys.platform == 'win32':
            temp_dir = os.environ.get('TEMP', 'C:\\Temp')
            return Path(temp_dir) / 'claude_voice_last_speech.time'
        else:
            return Path('/tmp/claude_voice_last_speech.time')

    @contextmanager
    def acquire(self, min_spacing=1.0):
        """
        Acquire speech lock with context manager.

        Args:
            min_spacing (float): Minimum seconds between speech events

        Yields:
            None when lock is acquired
        """
        start_time = time.time()

        # Open lock file
        self.lock_fd = open(self.lock_file, 'w')

        try:
            # Try to acquire exclusive lock with timeout
            while True:
                try:
                    lock_file(self.lock_fd)
                    break  # Lock acquired
                except (IOError, OSError):
                    # Lock is held by another process
                    if time.time() - start_time > self.timeout:
                        raise TimeoutError(f"Could not acquire speech lock within {self.timeout}s")
                    time.sleep(0.1)  # Wait a bit before retrying

            # Check last speech time from lock file
            last_speech_file = self._get_time_file()
            if last_speech_file.exists():
                try:
                    with open(last_speech_file, 'r') as f:
                        last_speech_time = float(f.read().strip())

                    # Enforce minimum spacing
                    time_since_last = time.time() - last_speech_time
                    if time_since_last < min_spacing:
                        wait_time = min_spacing - time_since_last
                        time.sleep(wait_time)
                except (ValueError, IOError):
                    pass  # Ignore errors reading time file

            # Yield control back to caller with lock held
            yield

            # Update last speech time
            with open(last_speech_file, 'w') as f:
                f.write(str(time.time()))

        finally:
            # Release lock
            if self.lock_fd:
                unlock_file(self.lock_fd)
                self.lock_fd.close()
                self.lock_fd = None
