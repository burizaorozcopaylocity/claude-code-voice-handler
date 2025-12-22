#!/usr/bin/env python3
"""
Centralized path management for voice handler.

Single source of truth for all file paths - prevents duplicated
platform-specific logic across the codebase.
"""

import sys
import os
from pathlib import Path


class VoiceHandlerPaths:
    """Centralized path management for voice handler."""

    @staticmethod
    def _get_temp_dir() -> Path:
        """Get platform-specific temp directory."""
        if sys.platform == 'win32':
            temp = os.environ.get('TEMP', r'C:\Temp')
        else:
            temp = '/tmp'
        return Path(temp)

    @property
    def queue_db(self) -> Path:
        """Queue database path."""
        return self._get_temp_dir() / 'claude_voice_queue'

    @property
    def daemon_pid(self) -> Path:
        """Daemon PID file path."""
        return self._get_temp_dir() / 'claude_voice_daemon.pid'

    @property
    def daemon_lock(self) -> Path:
        """Daemon lock file path."""
        return self._get_temp_dir() / 'claude_voice_daemon.lock'

    @property
    def daemon_log(self) -> Path:
        """Daemon log file path."""
        return self._get_temp_dir() / 'claude_voice.log'

    @property
    def daemon_status(self) -> Path:
        """Daemon status file path."""
        return self._get_temp_dir() / 'claude_voice_daemon.status'

    @property
    def session_storage(self) -> Path:
        """Session storage file path."""
        return self._get_temp_dir() / 'claude_voice_sessions.json'

    @property
    def state_storage(self) -> Path:
        """State storage file path."""
        return self._get_temp_dir() / 'claude_voice_state.json'

    @property
    def chat_history(self) -> Path:
        """LLM chat history file path."""
        return self._get_temp_dir() / 'claude_voice_chat_history.json'

    @property
    def speech_lock(self) -> Path:
        """Speech lock file path."""
        return self._get_temp_dir() / 'claude_voice_speech.lock'

    @property
    def last_speech_time(self) -> Path:
        """Last speech timestamp file path."""
        return self._get_temp_dir() / 'claude_voice_last_speech.time'


# Singleton instance
_paths_instance = None


def get_paths() -> VoiceHandlerPaths:
    """Get the global paths instance."""
    global _paths_instance
    if _paths_instance is None:
        _paths_instance = VoiceHandlerPaths()
    return _paths_instance
