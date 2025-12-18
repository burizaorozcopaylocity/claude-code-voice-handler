#!/usr/bin/env python3
"""
Voice Notification Handler - The Maestro.

Like the conductor who orchestrates every instrument in the symphony,
this module coordinates all voice handler components for the ultimate
rock concert experience!
"""

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any

from voice_handler.utils.logger import get_logger
from voice_handler.utils.dedup import get_deduplicator
from voice_handler.utils.lock import get_speech_lock
from voice_handler.utils.transcript import TranscriptReader
from voice_handler.core.state import get_state_manager
from voice_handler.core.session import get_session_voice_manager
from voice_handler.tts.provider import TTSProvider
from voice_handler.queue.producer import get_producer
from voice_handler.queue.daemon import VoiceDaemon
from voice_handler.ai.qwen import get_qwen_generator
from voice_handler.ai.prompts import get_rock_personality


class VoiceNotificationHandler:
    """
    Main handler class for voice notifications.

    The maestro who conducts the entire show - from the opening act
    to the encore, every voice notification goes through here!
    """

    def __init__(self, config: Optional[dict] = None, use_async: bool = True):
        """
        Initialize the handler with all necessary components.

        Args:
            config: Configuration dictionary
            use_async: Whether to use async queue system (recommended)
        """
        self.logger = get_logger()
        self.logger.log_info("Initializing VoiceNotificationHandler - Soundcheck!")

        # Load configurations
        self.script_dir = Path(__file__).parent.parent
        self.config = config or self._load_config()

        # Initialize components
        self.state_manager = get_state_manager()
        self.deduplicator = get_deduplicator()
        self.speech_lock = get_speech_lock()
        self.session_voice_manager = get_session_voice_manager(logger=self.logger)
        self.rock_personality = get_rock_personality()

        # Async queue system
        self.use_async = use_async
        if use_async:
            self.producer = get_producer(logger=self.logger)
            self.daemon = VoiceDaemon(logger=self.logger)
            # Ensure daemon is running
            self.daemon.ensure_running()
        else:
            # Direct TTS for synchronous mode
            self.tts_provider = TTSProvider(config=self.config, logger=self.logger)

        # Qwen AI integration
        self.qwen = get_qwen_generator(config=self.config, logger=self.logger)

        # Speech timing control
        self.min_speech_delay = 1.0

        # Current session tracking - load from state if available
        self.current_session_id: Optional[str] = self.state_manager.current_session_id
        self.preferred_voice = self.config.get("voice_settings", {}).get("openai_voice", "nova")

        if self.current_session_id:
            self.logger.log_debug(f"Loaded session_id from state: {self.current_session_id[:8]}...")

        # Active voice hooks
        self.active_voice_hooks = {
            "UserPromptSubmit",
            "PreToolUse",
            "PostToolUse",
            "Stop",
            "Notification"
        }

        # Tool announcement rate limiting
        self.last_tool_announcement: Dict[str, float] = {}
        self.min_tool_announcement_interval = 3.0

        self.logger.log_info("VoiceNotificationHandler ready - Let's rock!")

    def _load_config(self) -> dict:
        """Load voice configuration from config.json."""
        config_file = self.script_dir / "config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def get_session_voice(self) -> str:
        """
        Get the voice assigned to the current session.

        Returns:
            Voice name for this session
        """
        if self.current_session_id:
            return self.session_voice_manager.get_voice_for_session(
                self.current_session_id,
                preferred_voice=self.preferred_voice
            )
        return self.preferred_voice

    def speak(self, message: str, voice: Optional[str] = None, priority: int = 5):
        """
        Main speech output method.

        Args:
            message: Message to speak
            voice: Override voice selection
            priority: Message priority (1-10, higher = more urgent)
        """
        if isinstance(message, dict):
            message = (
                message.get('message') or
                message.get('content') or
                message.get('text') or
                str(message)
            )

        message = str(message)

        # Check for duplicate announcements
        if self.deduplicator.is_duplicate(message):
            self.logger.log_debug(f"Skipping duplicate announcement: {message[:50]}...")
            return

        # Use session-specific voice if no override provided
        if voice is None:
            voice = self.get_session_voice()
            self.logger.log_debug(
                f"Using session voice: {voice} for session "
                f"{self.current_session_id[:8] if self.current_session_id else 'None'}..."
            )

        # Use async queue system or direct TTS
        if self.use_async:
            self.producer.speak(
                text=message,
                voice=voice,
                session_id=self.current_session_id,
                priority=priority
            )
        else:
            # Synchronous mode with locking
            try:
                with self.speech_lock.acquire(min_spacing=self.min_speech_delay):
                    self.tts_provider.speak(message, voice)
                    self.state_manager.last_speech_time = time.time()
                    self.state_manager.save_state()
            except TimeoutError as e:
                self.logger.log_warning(f"Could not acquire speech lock: {e}")

    def should_announce(self, hook_type: str, tool_name: Optional[str] = None) -> bool:
        """
        Determine if this hook should trigger voice announcements.

        Args:
            hook_type: Hook type
            tool_name: Tool name for PreToolUse

        Returns:
            True if should announce
        """
        if hook_type not in self.active_voice_hooks:
            return False

        if hook_type == "PreToolUse" and tool_name:
            current_time = time.time()
            last_time = self.last_tool_announcement.get(tool_name, 0)
            if current_time - last_time < self.min_tool_announcement_interval:
                return False
            if tool_name == "TodoWrite":
                return True

        return True

    def process_user_prompt_submit(self, stdin_data: Optional[dict]) -> Optional[str]:
        """
        Process UserPromptSubmit hook.

        The opening act - acknowledge the user's request!

        Args:
            stdin_data: Data from stdin

        Returns:
            Acknowledgment message
        """
        if not stdin_data or not isinstance(stdin_data, dict):
            return None

        session_id = stdin_data.get('session_id')
        transcript_path = stdin_data.get('transcript_path')
        user_prompt = (
            stdin_data.get('prompt') or
            stdin_data.get('message') or
            stdin_data.get('content')
        )

        self.logger.log_debug(f"UserPromptSubmit stdin_data keys: {list(stdin_data.keys())}")

        # Set session ID if provided
        if session_id:
            self.current_session_id = session_id
            self.state_manager.current_session_id = session_id

        # Get session voice
        session_voice = self.get_session_voice()
        self.logger.log_info(
            f"Session {session_id[:8] if session_id else 'None'}... "
            f"will use voice: {session_voice}"
        )

        # Reset task context and chat history for new prompt
        self.state_manager.reset_task_context()
        self.state_manager.initial_summary_announced = False
        self.state_manager.save_state()
        self.qwen.clear_history()  # Clear LLM chat history for fresh context

        # Generate personalized acknowledgment with AI
        # Works with or without transcript_path
        return self.qwen.generate_acknowledgment(task_description=user_prompt)

    def process_pre_tool_use(
        self,
        stdin_data: Optional[dict],
        tool_name: Optional[str]
    ) -> Optional[str]:
        """
        Process PreToolUse hook.

        Announce what tool is about to be used!

        Args:
            stdin_data: Data from stdin
            tool_name: Name of the tool

        Returns:
            Tool announcement message
        """
        if tool_name == "TodoWrite":
            if stdin_data and isinstance(stdin_data, dict):
                tool_input = stdin_data.get('tool_input', {})
                if tool_input and 'todos' in tool_input:
                    new_todos = tool_input['todos']
                    completed_todos = self.state_manager.detect_completed_todos(new_todos)
                    if completed_todos:
                        task = completed_todos[-1]
                        return self._format_todo_completion(task)
            return None

        # Update rate limiting timestamp
        if tool_name:
            self.last_tool_announcement[tool_name] = time.time()

        # Generate tool announcement with Qwen
        if stdin_data and isinstance(stdin_data, dict):
            tool_input = stdin_data.get('tool_input', {})
            file_path = tool_input.get('file_path')
            return self.qwen.generate_tool_announcement(tool_name, file_path)

        return None

    def process_post_tool_use(self, stdin_data: Optional[dict]) -> Optional[str]:
        """
        Process PostToolUse hook.

        Report on what just happened!

        Args:
            stdin_data: Data from stdin

        Returns:
            Status message
        """
        if not stdin_data or not isinstance(stdin_data, dict):
            return None

        tool_name = stdin_data.get('tool_name')
        session_id = stdin_data.get('session_id')
        transcript_path = stdin_data.get('transcript_path')

        if not transcript_path:
            return None

        try:
            reader = TranscriptReader(transcript_path, session_id=session_id)
            new_messages = reader.get_messages_since_last_check()

            if new_messages:
                combined_message = " ".join(new_messages)

                if not self.state_manager.initial_summary_announced:
                    if len(combined_message) > 600:
                        combined_message = reader.extract_meaningful_summary(
                            combined_message, 600, 150
                        )
                    self.state_manager.initial_summary_announced = True
                    self.state_manager.save_state()
                    return combined_message

                # Check for approval requests
                for msg in new_messages:
                    if reader.detect_approval_request(msg):
                        return self.qwen.generate_approval_request()

                # Regular message handling
                meaningful_messages = [msg for msg in new_messages if len(msg) > 20]
                if meaningful_messages:
                    claude_message = meaningful_messages[-1]
                    if len(claude_message) > 400:
                        claude_message = reader.extract_meaningful_summary(
                            claude_message, 400, 100
                        )
                    return claude_message

        except Exception as e:
            self.logger.log_error("Error processing transcript", exception=e)

        return None

    def process_stop(self, stdin_data: Optional[dict]) -> Optional[str]:
        """
        Process Stop hook.

        The encore - summarize what was accomplished!

        Args:
            stdin_data: Data from stdin

        Returns:
            Completion message
        """
        if stdin_data and isinstance(stdin_data, dict):
            transcript_path = stdin_data.get('transcript_path')
            if transcript_path:
                try:
                    reader = TranscriptReader(transcript_path)
                    last_message = reader.get_last_message(max_length=500)

                    if last_message:
                        files_modified = len(set(
                            self.state_manager.task_context.get("files_modified", [])
                        ))
                        commands_run = len(
                            self.state_manager.task_context.get("commands_run", [])
                        )
                        return self.qwen.generate_completion(
                            summary=last_message,
                            files_modified=files_modified,
                            commands_run=commands_run
                        )
                except Exception as e:
                    self.logger.log_error("Error reading transcript", exception=e)

        # Fallback completion message
        return self.qwen.generate_completion()

    def process_notification(self, stdin_data: Optional[dict]) -> Optional[str]:
        """
        Process Notification hook for permission requests.

        The roadie asking for permission!

        Args:
            stdin_data: Data from stdin

        Returns:
            Approval request message
        """
        self.logger.log_info("Processing Notification hook", stdin_data=stdin_data)

        message = ""
        if stdin_data and isinstance(stdin_data, dict):
            message = stdin_data.get('message', '')

        if "permission to use" in message:
            parts = message.split("permission to use")
            if len(parts) > 1:
                tool_name = parts[1].strip()
                return self.qwen.generate_approval_request(tool_name=tool_name)

        return self.qwen.generate_approval_request()

    def _format_todo_completion(self, task: str) -> str:
        """
        Format a todo task completion for announcement.

        Args:
            task: Task description

        Returns:
            Formatted completion message
        """
        task_lower = task.lower()

        if task_lower.startswith('add '):
            return f"Added {task[4:]}"
        elif task_lower.startswith('modify '):
            return f"Modified {task[7:]}"
        elif task_lower.startswith('update '):
            return f"Updated {task[7:]}"
        elif task_lower.startswith('create '):
            return f"Created {task[7:]}"
        elif task_lower.startswith('fix '):
            return f"Fixed {task[4:]}"
        elif task_lower.startswith('test '):
            return f"Tested {task[5:]}"
        else:
            return f"Completed: {task}"


# Singleton handler instance
_handler_instance: Optional[VoiceNotificationHandler] = None


def get_handler(config: Optional[dict] = None, use_async: bool = True) -> VoiceNotificationHandler:
    """Get or create the voice handler singleton."""
    global _handler_instance
    if _handler_instance is None:
        _handler_instance = VoiceNotificationHandler(config=config, use_async=use_async)
    return _handler_instance
