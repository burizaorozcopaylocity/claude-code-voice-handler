#!/usr/bin/env python3
"""
Session Voice Manager - The Voice Casting Director.

Like assigning different voices to different characters in an epic concept album,
this module gives each Claude Code session a unique voice identity.
"""

import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Any


class SessionVoiceManager:
    """
    Manages unique voice assignments per Claude Code session.

    Each session gets a unique OpenAI TTS voice so users can audibly
    distinguish between multiple Claude Code instances running in parallel.

    Think of it like having different vocalists for each track on the album!
    """

    # Available OpenAI TTS voices - our band of vocalists
    VOICES: List[str] = ["nova", "alloy", "echo", "fable", "onyx", "shimmer"]

    def __init__(self, storage_path: Optional[str] = None, logger=None, config: Optional[Dict] = None):
        """
        Initialize the session voice manager.

        Args:
            storage_path: Path to store session-voice mappings
            logger: Logger instance for debugging
            config: Optional config dict (loaded from config.json if not provided)
        """
        self.logger = logger

        # Load validated config to get session expiry time
        if config is None:
            from voice_handler.config import get_voice_config
            voice_config = get_voice_config()
            config = voice_config.model_dump()

        # Get session expiry from validated config (hours → seconds)
        session_expiry_hours = config["timing"]["session_expiry_hours"]
        self.SESSION_EXPIRY_SECONDS = session_expiry_hours * 60 * 60

        if storage_path is None:
            from voice_handler.utils.paths import get_paths
            storage_path = get_paths().session_storage

        self.storage_path = Path(storage_path)
        self.sessions: Dict[str, Dict[str, Any]] = self._load_sessions()

        if self.logger:
            self.logger.log_debug(
                f"SessionVoiceManager initialized with {len(self.sessions)} sessions"
            )

    def _load_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Load existing session mappings from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    return data.get('sessions', {})
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def _save_sessions(self):
        """Save session mappings to storage."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump({
                    'sessions': self.sessions,
                    'updated_at': datetime.now().isoformat()
                }, f, indent=2)
        except IOError as e:
            if self.logger:
                self.logger.log_error("Failed to save session mappings", exception=e)

    def _cleanup_expired_sessions(self):
        """Remove expired sessions to free up voices - clearing the old guest list."""
        current_time = time.time()
        expired_sessions = []

        for session_id, data in self.sessions.items():
            last_used = data.get('last_used', 0)
            if current_time - last_used > self.SESSION_EXPIRY_SECONDS:
                expired_sessions.append(session_id)

        if expired_sessions:
            for session_id in expired_sessions:
                del self.sessions[session_id]
            self._save_sessions()

            if self.logger:
                self.logger.log_debug(
                    f"Cleaned up {len(expired_sessions)} expired sessions"
                )

    def _get_used_voices(self) -> List[str]:
        """Get list of voices currently in use by active sessions."""
        self._cleanup_expired_sessions()
        return [data['voice'] for data in self.sessions.values()]

    def _get_next_available_voice(self, preferred_voice: Optional[str] = None) -> str:
        """
        Get the next available voice that's not in use.

        Like finding the lead singer who isn't already booked!

        Args:
            preferred_voice: User's preferred voice from config

        Returns:
            Voice name to use
        """
        used_voices = self._get_used_voices()

        # If preferred voice is available, use it
        if preferred_voice and preferred_voice not in used_voices:
            return preferred_voice

        # Find first unused voice
        for voice in self.VOICES:
            if voice not in used_voices:
                return voice

        # All voices in use - find least recently used session's voice
        if self.sessions:
            oldest_session = min(
                self.sessions.items(),
                key=lambda x: x[1].get('last_used', 0)
            )
            return oldest_session[1]['voice']

        # Default fallback
        return preferred_voice or self.VOICES[0]

    def get_voice_for_session(
        self,
        session_id: str,
        preferred_voice: Optional[str] = None
    ) -> str:
        """
        Get the assigned voice for a session, creating assignment if needed.

        Args:
            session_id: Claude Code session identifier
            preferred_voice: User's preferred voice from config

        Returns:
            Voice name for this session
        """
        if not session_id:
            return preferred_voice or self.VOICES[0]

        # Check if session already has a voice
        if session_id in self.sessions:
            # Update last used time
            self.sessions[session_id]['last_used'] = time.time()
            self._save_sessions()

            voice = self.sessions[session_id]['voice']
            if self.logger:
                self.logger.log_debug(
                    f"Session {session_id[:8]}... using existing voice: {voice}"
                )
            return voice

        # Assign new voice to this session
        voice = self._get_next_available_voice(preferred_voice)
        self.sessions[session_id] = {
            'voice': voice,
            'created_at': time.time(),
            'last_used': time.time()
        }
        self._save_sessions()

        if self.logger:
            self.logger.log_info(
                f"Session {session_id[:8]}... assigned NEW voice: {voice}"
            )

        return voice

    def get_active_sessions_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get info about all active sessions and their voices.

        Returns:
            Session info for debugging/display
        """
        self._cleanup_expired_sessions()

        info = {}
        for session_id, data in self.sessions.items():
            info[session_id[:8] + '...'] = {
                'voice': data['voice'],
                'age_minutes': int((time.time() - data.get('created_at', 0)) / 60)
            }
        return info

    def clear_session(self, session_id: str):
        """
        Clear a specific session's voice assignment.

        Args:
            session_id: Session to clear
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            self._save_sessions()

            if self.logger:
                self.logger.log_debug(f"Cleared session {session_id[:8]}...")

    def clear_all_sessions(self):
        """Clear all session mappings - new tour, all voices available!"""
        self.sessions = {}
        self._save_sessions()

        if self.logger:
            self.logger.log_info("Cleared all session voice mappings")


# Singleton instance
_session_voice_manager: Optional[SessionVoiceManager] = None


def get_session_voice_manager(logger=None) -> SessionVoiceManager:
    """Get or create the session voice manager singleton."""
    global _session_voice_manager
    if _session_voice_manager is None:
        _session_voice_manager = SessionVoiceManager(logger=logger)
    return _session_voice_manager
