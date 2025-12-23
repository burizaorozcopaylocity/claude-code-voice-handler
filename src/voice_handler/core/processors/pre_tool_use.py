#!/usr/bin/env python3
"""
PreToolUse Processor - Tool Announcement Handler.

Handles the PreToolUse hook, which fires before Claude Code uses a tool.
Implements rate limiting, TodoWrite completion detection, and generates
tool announcements.
"""

import time
from typing import Optional, Dict, Any
from voice_handler.core.processors.base import HookProcessor


class PreToolUseProcessor(HookProcessor):
    """
    Processes pre-tool-use events with rate limiting.

    Announce what tool is about to be used!

    PreToolUse is called before tool execution with data like:
    {
        "tool_name": "Read",
        "tool_input": {"file_path": "..."},
        ...
    }

    Responsibilities:
    - Rate limit tool announcements (avoid spam)
    - Special handling for TodoWrite (detect completions)
    - Generate tool announcement via Qwen
    """

    def __init__(self, deps):
        """
        Initialize with rate limiting state.

        Args:
            deps: Shared dependencies
        """
        super().__init__(deps)

        # Per-tool rate limiting state
        self.last_tool_announcement: Dict[str, float] = {}

        # Rate limiting config from validated config
        self.min_interval = self.config["timing"]["min_tool_announcement_interval"]

    def should_process(self, stdin_data: Optional[Dict[str, Any]]) -> bool:
        """
        Determine if tool announcement should happen.

        Implements rate limiting: Don't announce the same tool
        too frequently unless it's TodoWrite (always process for
        completion detection).

        Args:
            stdin_data: Data from stdin

        Returns:
            True if should announce, False to skip
        """
        if not stdin_data or not isinstance(stdin_data, dict):
            return False

        tool_name = stdin_data.get('tool_name')
        if not tool_name:
            return False

        # TodoWrite always processes (for completion detection)
        if tool_name == "TodoWrite":
            return True

        # Rate limiting for other tools
        current_time = time.time()
        last_time = self.last_tool_announcement.get(tool_name, 0)

        # Skip if announced too recently
        if current_time - last_time < self.min_interval:
            return False

        return True

    def process(self, stdin_data: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Process pre-tool-use and return announcement.

        Args:
            stdin_data: Data from stdin containing tool_name and tool_input

        Returns:
            Tool announcement message or todo completion message
        """
        if not stdin_data or not isinstance(stdin_data, dict):
            return None

        tool_name = stdin_data.get('tool_name')
        if not tool_name:
            return None

        # TodoWrite special case: detect completed todos
        if tool_name == "TodoWrite":
            return self._process_todo_write(stdin_data)

        # Update rate limiting timestamp
        self.last_tool_announcement[tool_name] = time.time()

        # Extract file path for context
        tool_input = stdin_data.get('tool_input', {})
        file_path = tool_input.get('file_path')

        # Generate tool announcement with project context
        session_id = self.extract_session_id(stdin_data)
        project_name = self.get_project_name(session_id)
        return self.qwen.generate_tool_announcement(
            tool_name,
            file_path,
            context=None,
            project_name=project_name
        )

    def _process_todo_write(self, stdin_data: Dict[str, Any]) -> Optional[str]:
        """
        Process TodoWrite to detect task completions.

        TodoWrite is special: we want to announce when tasks are completed,
        not when the tool is used. This requires inspecting the new todo list
        and comparing it with the previous state.

        Args:
            stdin_data: Data from stdin with tool_input containing todos

        Returns:
            Completion message if todos were completed, None otherwise
        """
        tool_input = stdin_data.get('tool_input', {})
        if not tool_input or 'todos' not in tool_input:
            return None

        new_todos = tool_input['todos']

        # Detect completed todos
        completed_todos = self.state_manager.detect_completed_todos(new_todos)

        if completed_todos:
            # Announce most recent completion
            task = completed_todos[-1]
            return self._format_todo_completion(task)

        return None

    def _format_todo_completion(self, task: str) -> str:
        """
        Format a todo task completion for announcement.

        Converts task descriptions into natural completion messages:
        "Add user authentication" → "Added user authentication"

        Args:
            task: Task description

        Returns:
            Formatted completion message
        """
        task_lower = task.lower()

        # Map action verbs to past tense
        verb_map = {
            'add ': 'Added ',
            'modify ': 'Modified ',
            'update ': 'Updated ',
            'create ': 'Created ',
            'fix ': 'Fixed ',
            'test ': 'Tested ',
            'implement ': 'Implemented ',
            'refactor ': 'Refactored ',
        }

        for present, past in verb_map.items():
            if task_lower.startswith(present):
                return past + task[len(present):]

        # Default format
        return f"Completed: {task}"
