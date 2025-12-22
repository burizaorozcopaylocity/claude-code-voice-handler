#!/usr/bin/env python3
"""
Stop Processor - Task Completion Handler.

Handles the Stop hook, which fires when Claude Code completes a task.
Reads the transcript, collects task statistics, and generates completion
summaries.
"""

from typing import Optional, Dict, Any
from voice_handler.core.processors.base import HookProcessor
from voice_handler.utils.transcript import TranscriptReader


class StopProcessor(HookProcessor):
    """
    Processes task completion events.

    The encore - summarize what was accomplished!

    Stop is called when a task completes with data like:
    {
        "session_id": "...",
        "transcript_path": "...",
        ...
    }

    Responsibilities:
    - Read final message from transcript
    - Collect task statistics (files modified, commands run)
    - Generate completion summary via Qwen
    """

    def process(self, stdin_data: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Process task stop and return completion message.

        Args:
            stdin_data: Data from stdin containing transcript path

        Returns:
            Task completion summary from Qwen
        """
        if not stdin_data or not isinstance(stdin_data, dict):
            # Fallback completion without transcript
            return self.qwen.generate_completion()

        transcript_path = stdin_data.get('transcript_path')
        if not transcript_path:
            # No transcript available, use fallback
            return self.qwen.generate_completion()

        try:
            # Read last message from transcript
            reader = TranscriptReader(transcript_path)
            last_message = reader.get_last_message(max_length=500)

            if last_message:
                # Collect task statistics from state
                files_modified = len(set(
                    self.state_manager.task_context.get("files_modified", [])
                ))
                commands_run = len(
                    self.state_manager.task_context.get("commands_run", [])
                )

                # Generate completion with stats
                return self.qwen.generate_completion(
                    summary=last_message,
                    files_modified=files_modified,
                    commands_run=commands_run
                )

        except Exception as e:
            self.logger.log_error("Error reading transcript", exception=e)

        # Fallback completion message
        return self.qwen.generate_completion()
