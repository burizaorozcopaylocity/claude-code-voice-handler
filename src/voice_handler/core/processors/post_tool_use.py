#!/usr/bin/env python3
"""
PostToolUse Processor - Tool Result Handler.

Handles the PostToolUse hook, which fires after Claude Code uses a tool.
Reads transcripts, extracts meaningful updates, and generates summaries.
"""

from typing import Optional, Dict, Any
from voice_handler.core.processors.base import HookProcessor
from voice_handler.utils.transcript import TranscriptReader


class PostToolUseProcessor(HookProcessor):
    """
    Processes post-tool-use events with transcript reading.

    Report on what just happened!

    PostToolUse is called after tool execution with data like:
    {
        "tool_name": "Read",
        "session_id": "...",
        "transcript_path": "...",
        ...
    }

    Responsibilities:
    - Read transcript for new messages
    - Handle initial summary (truncate if too long)
    - Detect approval requests
    - Extract meaningful messages from Claude's responses
    """

    def process(self, stdin_data: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Process post-tool-use and return status message.

        Args:
            stdin_data: Data from stdin containing transcript path

        Returns:
            Status message or summary from transcript
        """
        if not stdin_data or not isinstance(stdin_data, dict):
            return None

        tool_name = stdin_data.get('tool_name')
        session_id = stdin_data.get('session_id')
        transcript_path = stdin_data.get('transcript_path')

        if not transcript_path:
            return None

        try:
            # Read transcript
            reader = TranscriptReader(transcript_path, session_id=session_id)
            new_messages = reader.get_messages_since_last_check()

            if not new_messages:
                return None

            # Combine all new messages
            combined_message = " ".join(new_messages)

            # Handle initial summary (first message after task start)
            if not self.state_manager.initial_summary_announced:
                return self._handle_initial_summary(reader, combined_message)

            # Check for approval requests in messages
            for msg in new_messages:
                if reader.detect_approval_request(msg):
                    project_name = self.get_project_name(session_id)
                    return self.qwen.generate_approval_request(project_name=project_name)

            # Extract meaningful messages (filter out very short ones)
            meaningful_messages = [msg for msg in new_messages if len(msg) > 20]

            if meaningful_messages:
                # Use the last meaningful message
                claude_message = meaningful_messages[-1]

                # Truncate if too long
                if len(claude_message) > 400:
                    claude_message = reader.extract_meaningful_summary(
                        claude_message,
                        max_chars=400,
                        min_chars=100
                    )

                return claude_message

        except Exception as e:
            self.logger.log_error("Error processing transcript", exception=e)

        return None

    def _handle_initial_summary(
        self,
        reader: TranscriptReader,
        combined_message: str
    ) -> Optional[str]:
        """
        Handle the initial summary message.

        The first message after a user prompt is often the most important -
        it's Claude's initial response outlining what it will do. We want
        to announce this, but truncate it if it's too long.

        Args:
            reader: TranscriptReader instance
            combined_message: Combined message text

        Returns:
            Initial summary message (possibly truncated)
        """
        # Truncate if too long (>600 chars)
        if len(combined_message) > 600:
            combined_message = reader.extract_meaningful_summary(
                combined_message,
                max_chars=600,
                min_chars=150
            )

        # Mark that we've announced the initial summary
        self.state_manager.initial_summary_announced = True
        self.state_manager.save_state()

        return combined_message
