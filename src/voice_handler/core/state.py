#!/usr/bin/env python3
"""
State Management - The Tour Manager's Notebook.

Like the tour manager who tracks every venue, every setlist, and every rider,
this module handles persistent state and context tracking across sessions.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class StateManager:
    """
    Manages persistent state and task context across multiple hook invocations.

    The road manager who remembers everything about the tour.
    """

    def __init__(self, state_file_path: Optional[str] = None):
        """
        Initialize state manager with file path.

        Args:
            state_file_path: Path to state file (auto-detected based on OS)
        """
        if state_file_path is None:
            if sys.platform == 'win32':
                temp_dir = os.environ.get('TEMP', 'C:\\Temp')
                state_file_path = os.path.join(temp_dir, 'claude_voice_state.json')
            else:
                state_file_path = '/tmp/claude_voice_state.json'

        self.state_file = Path(state_file_path)
        self.state = self._load_state()
        loaded_context = self.state.get('task_context', {})
        self.task_context = self._validate_and_merge_task_context(loaded_context)
        self.last_speech_time = self.state.get('last_speech_time', 0)
        self.last_todos = self.state.get('last_todos', [])
        self.initial_summary_announced = self.state.get('initial_summary_announced', False)
        self.current_session_id = self.state.get('current_session_id', None)

    def _get_default_task_context(self) -> Dict[str, Any]:
        """
        Initialize a fresh task context for tracking operations.

        Returns:
            Empty task context with tracking arrays
        """
        return {
            "files_created": [],
            "files_modified": [],
            "files_deleted": [],
            "commands_run": [],
            "searches_performed": [],
            "start_time": datetime.now().isoformat(),
            "operations_count": 0
        }

    def _validate_and_merge_task_context(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate task_context has all required keys, merge with defaults if incomplete.

        Handles corrupted state files where task_context exists but is empty or missing keys.

        Args:
            task_context: Task context from state file (may be incomplete)

        Returns:
            Valid task_context with all required keys
        """
        defaults = self._get_default_task_context()

        if not task_context:
            return defaults

        validated = defaults.copy()
        validated.update(task_context)

        return validated

    def _load_state(self) -> Dict[str, Any]:
        """
        Load persistent state from temporary storage.

        Returns:
            Saved state or default state if none exists
        """
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    # Clean up old transcript positions
                    if 'transcript_positions' in state:
                        state['transcript_positions'] = self._clean_old_positions(
                            state['transcript_positions']
                        )
                    return state
            except (json.JSONDecodeError, IOError):
                pass
        return {
            'transcript_positions': {},
            'task_context': self._get_default_task_context()
        }

    def _clean_old_positions(self, positions: Dict[str, int]) -> Dict[str, int]:
        """
        Clean up transcript position tracking.

        Args:
            positions: Current transcript positions

        Returns:
            Cleaned positions dictionary
        """
        cleaned = {}
        for path, pos in positions.items():
            if Path(path).exists():
                cleaned[path] = pos
        return cleaned

    def save_state(self):
        """Persist current state to temporary storage."""
        self.state['task_context'] = self.task_context
        self.state['last_speech_time'] = self.last_speech_time
        self.state['last_todos'] = self.last_todos
        self.state['initial_summary_announced'] = self.initial_summary_announced
        self.state['current_session_id'] = self.current_session_id
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except IOError:
            pass  # Silent failure - the show must go on!

    def update_context(
        self,
        hook_type: str,
        tool_name: Optional[str] = None,
        file_path: Optional[str] = None,
        **kwargs
    ):
        """
        Track Claude's operations for context-aware announcements.

        Like marking songs off the setlist as they're played.

        Args:
            hook_type: Type of hook event
            tool_name: Name of tool being used
            file_path: Path to file being operated on
            **kwargs: Additional context
        """
        self.task_context["operations_count"] += 1

        if tool_name == "Write" and file_path:
            self.task_context["files_created"].append(file_path)
        elif tool_name in ["Edit", "MultiEdit"] and file_path:
            self.task_context["files_modified"].append(file_path)
        elif tool_name == "Bash" and kwargs.get("command"):
            self.task_context["commands_run"].append(kwargs["command"])
        elif tool_name in ["Grep", "Glob", "WebSearch"] and kwargs.get("query"):
            self.task_context["searches_performed"].append(kwargs["query"])

        self.save_state()

    def reset_task_context(self):
        """Reset task context for new session - new tour, new setlist!"""
        self.task_context = self._get_default_task_context()
        self.initial_summary_announced = False
        self.last_todos = []
        if 'transcript_positions' in self.state:
            self.state['transcript_positions'] = {}
        self.save_state()

    def detect_completed_todos(self, new_todos: List[Dict]) -> List[str]:
        """
        Detect which todos were marked as completed.

        Like checking off songs as encore material!

        Args:
            new_todos: New todo list from stdin data

        Returns:
            List of completed todo descriptions
        """
        completed = []

        # Create lookup of old todos by id
        old_todos_by_id = {todo.get('id'): todo for todo in self.last_todos}

        # Check for status changes
        for todo in new_todos:
            todo_id = todo.get('id')
            old_todo = old_todos_by_id.get(todo_id)

            if old_todo:
                old_status = old_todo.get('status', 'pending')
                new_status = todo.get('status', 'pending')

                if old_status != 'completed' and new_status == 'completed':
                    completed.append(todo.get('content', 'task'))

        # Update stored todos
        self.last_todos = new_todos
        self.save_state()

        return completed

    def get_task_summary(self) -> Optional[str]:
        """
        Create a summary of operations performed during the current session.

        Returns:
            Human-readable task summary or None if no operations
        """
        if self.task_context.get("operations_count", 0) == 0:
            return None

        summary_parts = []

        created = len(set(self.task_context.get("files_created", [])))
        modified = len(set(self.task_context.get("files_modified", [])))
        commands = len(self.task_context.get("commands_run", []))
        searches = len(self.task_context.get("searches_performed", []))

        if created > 0:
            summary_parts.append(f"Created {created} files")
        if modified > 0:
            summary_parts.append(f"Modified {modified} files")
        if commands > 0:
            summary_parts.append(f"Ran {commands} commands")
        if searches > 0:
            summary_parts.append(f"Performed {searches} searches")

        if summary_parts:
            return ". ".join(summary_parts)

        return None


# Singleton instance
_state_manager_instance = None


def get_state_manager() -> StateManager:
    """Get or create the state manager singleton."""
    global _state_manager_instance
    if _state_manager_instance is None:
        _state_manager_instance = StateManager()
    return _state_manager_instance
