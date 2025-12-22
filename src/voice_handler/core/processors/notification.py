#!/usr/bin/env python3
"""
Notification Processor - Permission Request Handler.

Handles the Notification hook, which is triggered when Claude Code
requests permission to use a tool. Parses the permission message and
generates an appropriate approval request via Qwen.
"""

from typing import Optional, Dict, Any
from voice_handler.core.processors.base import HookProcessor


class NotificationProcessor(HookProcessor):
    """
    Processes permission request notifications.

    When Claude Code asks "May I have permission to use Read?",
    this processor extracts the tool name and generates a personalized
    approval request message via Qwen.

    Responsibilities:
    - Extract tool name from permission messages
    - Generate approval request via Qwen AI
    """

    def process(self, stdin_data: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Process notification hook and generate approval request.

        Args:
            stdin_data: Data from stdin containing 'message' field

        Returns:
            Approval request message from Qwen
        """
        if not stdin_data or not isinstance(stdin_data, dict):
            return None

        message = stdin_data.get('message', '')
        if not message:
            return None

        # Extract tool name if this is a permission request
        tool_name = None
        context = message  # Use full message as context

        if "permission to use" in message.lower():
            # Parse: "May I have permission to use Read?"
            parts = message.split("permission to use")
            if len(parts) > 1:
                # Extract tool name (first word after "permission to use")
                tool_name = parts[1].strip().split()[0] if parts[1].strip() else None

        # Generate approval request via Qwen
        return self.qwen.generate_approval_request(
            tool_name=tool_name,
            context=context
        )
