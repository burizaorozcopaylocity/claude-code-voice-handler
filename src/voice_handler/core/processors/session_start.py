#!/usr/bin/env python3
"""
SessionStart Processor - Session Initialization Handler.

Handles the SessionStart hook, which fires when a Claude Code session begins.
Manages voice assignment, session state, and generates contextual greetings.
"""

from typing import Optional, Dict, Any
from voice_handler.core.processors.base import HookProcessor


class SessionStartProcessor(HookProcessor):
    """
    Processes session start events.

    The opening curtain - welcome the audience to the show!

    SessionStart is called when a session begins with data like:
    {
        "source": "startup|resume|clear|compact",
        "session_id": "...",
        "transcript_path": "...",
        ...
    }

    Responsibilities:
    - Extract session ID and source
    - Update state manager with session ID
    - Assign unique voice to session (via session_voice_manager)
    - Reset context for fresh sessions (startup/clear)
    - Generate contextual greeting based on source
    """

    def process(self, stdin_data: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Process session start and return greeting.

        Args:
            stdin_data: Data from stdin containing source and session_id

        Returns:
            Contextual greeting message from Qwen
        """
        if not stdin_data or not isinstance(stdin_data, dict):
            return None

        session_id = self.extract_session_id(stdin_data)
        source = stdin_data.get('source', 'startup')

        self.logger.log_debug(
            f"SessionStart - source: {source}, session_id: {session_id[:8] if session_id else 'None'}..."
        )

        # Set session ID for voice assignment
        if session_id:
            self.update_session_state(session_id, stdin_data)

            # Get session voice (will assign new voice if first time)
            preferred_voice = self.config["voice_settings"]["openai_voice"]
            session_voice = self.session_voice_manager.get_voice_for_session(
                session_id,
                preferred_voice=preferred_voice
            )

            self.logger.log_info(
                f"SessionStart: Session {session_id[:8]}... "
                f"assigned voice: {session_voice} (source: {source})"
            )

        # Reset task context for fresh session
        if source in ['startup', 'clear']:
            self.state_manager.reset_task_context()
            self.qwen.clear_history()

        # Generate contextual greeting based on source with project context
        project_name = self.get_project_name(session_id)
        return self.qwen.generate_session_greeting(source=source, project_name=project_name)
