#!/usr/bin/env python3
"""
Speech Lock - The Stage Manager.

Like the stage manager who ensures only one band plays at a time,
this module prevents overlapping announcements across processes.

Cross-platform version (Windows + Unix/macOS)
"""

import os
import sys
import time
from pathlib import Path
from contextlib import contextmanager
from typing import Optional

# Cross-platform file locking
if sys.platform == 'win32':
    import msvcrt

    def _lock_file(fd):
        """Lock file on Windows."""
        msvcrt.locking(fd.fileno(), msvcrt.LK_NBLCK, 1)

    def _unlock_file(fd):
        """Unlock file on Windows."""
        try:
            fd.seek(0)
            msvcrt.locking(fd.fileno(), msvcrt.LK_UNLCK, 1)
        except (IOError, OSError):
            pass
else:
    import fcntl

    def _lock_file(fd):
        """Lock file on Unix/macOS."""
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _unlock_file(fd):
        """Unlock file on Unix/macOS."""
        fcntl.flock(fd, fcntl.LOCK_UN)


class SpeechLock:
    """
    File-based lock to prevent multiple processes from speaking simultaneously.

    The bouncer at the backstage door - only one performer at a time!
    Cross-platform: uses msvcrt on Windows, fcntl on Unix/macOS.
    """

    def __init__(self, lock_file: Optional[str] = None, timeout: float = 10.0):
        """
        Initialize speech lock.

        Args:
            lock_file: Path to lock file
            timeout: Maximum time to wait for lock
        """
        if lock_file is None:
            from voice_handler.utils.paths import get_paths
            lock_file = get_paths().speech_lock

        self.lock_file = Path(lock_file)
        self.timeout = timeout
        self.lock_fd = None

        # Ensure lock file directory exists
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        self.lock_file.touch()

    def _get_time_file(self) -> Path:
        """Get path to last speech time file."""
        from voice_handler.utils.paths import get_paths
        return get_paths().last_speech_time

    @contextmanager
    def acquire(self, min_spacing: float = 1.0):
        """
        Acquire speech lock with context manager.

        Like getting the all-clear from the sound engineer before your set.

        Args:
            min_spacing: Minimum seconds between speech events

        Yields:
            None when lock is acquired

        Raises:
            TimeoutError: If lock cannot be acquired within timeout
        """
        start_time = time.time()

        # Open lock file
        self.lock_fd = open(self.lock_file, 'w')

        try:
            # Try to acquire exclusive lock with timeout
            while True:
                try:
                    _lock_file(self.lock_fd)
                    break  # Lock acquired - showtime!
                except (IOError, OSError):
                    # Lock is held by another process
                    if time.time() - start_time > self.timeout:
                        raise TimeoutError(
                            f"Could not acquire speech lock within {self.timeout}s - "
                            "another process is hogging the mic!"
                        )
                    time.sleep(0.1)

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
            # Release lock - next act, please!
            if self.lock_fd:
                _unlock_file(self.lock_fd)
                self.lock_fd.close()
                self.lock_fd = None


# Singleton instance
_speech_lock_instance = None


def get_speech_lock(timeout: float = 10.0) -> SpeechLock:
    """Get or create the speech lock singleton."""
    global _speech_lock_instance
    if _speech_lock_instance is None:
        _speech_lock_instance = SpeechLock(timeout=timeout)
    return _speech_lock_instance
