#!/usr/bin/env python3
"""
UserPromptSubmit Processor - User Request Handler.

Handles the UserPromptSubmit hook, which fires when the user submits
a new prompt to Claude Code. Resets context and generates personalized
acknowledgments.
"""

from typing import Optional, Dict, Any
from voice_handler.core.processors.base import HookProcessor


class UserPromptSubmitProcessor(HookProcessor):
    """
    Processes user prompt submissions.

    The opening act - acknowledge the user's request!

    UserPromptSubmit is called when user submits a prompt with data like:
    {
        "session_id": "...",
        "prompt": "...",  # or "message" or "content"
        "transcript_path": "...",
        ...
    }

    Responsibilities:
    - Extract user prompt from stdin (flexible key matching)
    - Update session state with session ID
    - Reset task context for fresh start
    - Clear Qwen chat history
    - Generate personalized acknowledgment
    """

    def process(self, stdin_data: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Process user prompt submission and return acknowledgment.

        Args:
            stdin_data: Data from stdin containing prompt and session info

        Returns:
            Personalized acknowledgment message from Qwen
        """
        if not stdin_data or not isinstance(stdin_data, dict):
            return None

        session_id = self.extract_session_id(stdin_data)

        # Flexible prompt extraction - try multiple keys
        user_prompt = (
            stdin_data.get('prompt') or
            stdin_data.get('message') or
            stdin_data.get('content')
        )

        self.logger.log_debug(f"UserPromptSubmit stdin_data keys: {list(stdin_data.keys())}")

        # Set session ID if provided
        if session_id:
            self.update_session_state(session_id)

            # Log session voice info
            preferred_voice = self.config["voice_settings"]["openai_voice"]
            session_voice = self.session_voice_manager.get_voice_for_session(
                session_id,
                preferred_voice=preferred_voice
            )
            self.logger.log_info(
                f"Session {session_id[:8]}... will use voice: {session_voice}"
            )

        # Reset task context and chat history for new prompt
        self.state_manager.reset_task_context()
        self.state_manager.initial_summary_announced = False
        self.state_manager.save_state()
        self.qwen.clear_history()  # Clear LLM chat history for fresh context

        # Generate personalized acknowledgment with AI
        # Works with or without user_prompt
        return self.qwen.generate_acknowledgment(task_description=user_prompt)
