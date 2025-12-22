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
from voice_handler.utils.text import truncate_message
from voice_handler.core.state import get_state_manager
from voice_handler.core.session import get_session_voice_manager
from voice_handler.tts.provider import TTSProvider
from voice_handler.queue.producer import get_producer
from voice_handler.queue.daemon import VoiceDaemon
from voice_handler.ai.qwen import get_qwen_generator
from voice_handler.ai.prompts import get_rock_personality
from voice_handler.config import is_voice_enabled


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

        # Message truncation limits (validated config - no .get() needed)
        message_limits = self.config["message_limits"]
        self.max_words = message_limits["max_words"]
        self.max_chars = message_limits["max_chars"]
        self.truncate_suffix = message_limits["truncate_suffix"]

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

        # Initialize processor registry (Strategy Pattern)
        from voice_handler.core.processors import ProcessorRegistry, ProcessorDependencies
        deps = ProcessorDependencies(
            state_manager=self.state_manager,
            session_voice_manager=self.session_voice_manager,
            qwen=self.qwen,
            config=self.config,
            logger=self.logger
        )
        self.registry = ProcessorRegistry(deps)

        # Speech timing control from config (validated - no .get() needed)
        timing_config = self.config["timing"]
        self.min_speech_delay = timing_config["min_speech_delay"]

        # Current session tracking via property (reads from state_manager)
        self.preferred_voice = self.config["voice_settings"]["openai_voice"]

        if self.state_manager.current_session_id:
            self.logger.log_debug(f"Loaded session_id from state: {self.state_manager.current_session_id[:8]}...")

        self.logger.log_info("VoiceNotificationHandler ready - Let's rock!")

    def _load_config(self) -> dict:
        """Load voice configuration from config.json with Pydantic validation."""
        from voice_handler.config import get_voice_config
        from voice_handler.config_schema import VoiceConfig

        try:
            config = get_voice_config()
            return config.model_dump()  # Convert to dict for backward compat
        except Exception as e:
            self.logger.log_error("Config validation failed, using defaults", exception=e)
            return VoiceConfig().model_dump()

    @property
    def current_session_id(self) -> Optional[str]:
        """Get current session ID from state manager (for backward compatibility)."""
        return self.state_manager.current_session_id

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
        # Check if voice is enabled - early exit if disabled
        if not is_voice_enabled():
            self.logger.log_debug("Voice disabled (VOICE_ENABLED=false) - clearing queue and exiting")
            # Clear any pending messages in the queue when voice is disabled
            if self.use_async and hasattr(self, 'producer'):
                try:
                    self.producer.clear_queue()
                except Exception as e:
                    self.logger.log_warning(f"Failed to clear queue: {e}")
            return

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

        # Truncate message if it exceeds limits
        original_length = len(message)
        original_words = len(message.split())
        message = truncate_message(
            message,
            max_words=self.max_words,
            max_chars=self.max_chars,
            suffix=self.truncate_suffix
        )

        if len(message) < original_length:
            self.logger.log_info(
                f"Message truncated: {original_words} words ({original_length} chars) "
                f"-> {len(message.split())} words ({len(message)} chars)"
            )
        else:
            self.logger.log_debug(f"Message within limits: {len(message)} chars, {len(message.split())} words")

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

    def process_hook(self, hook_type: str, stdin_data: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Generic hook processor using Strategy Pattern.

        This is the new unified entry point for all hook processing.
        Instead of having 6 different methods with duplicated logic,
        we delegate to the appropriate processor from the registry.

        Args:
            hook_type: Type of hook (SessionStart, PreToolUse, etc.)
            stdin_data: Data from stdin

        Returns:
            Message to speak, or None
        """
        processor = self.registry.get_processor(hook_type)

        if not processor:
            self.logger.log_warning(f"No processor registered for hook: {hook_type}")
            return None

        # Let processor decide if it should process (rate limiting, filters, etc.)
        if not processor.should_process(stdin_data):
            self.logger.log_debug(f"Processor {hook_type} declined to process")
            return None

        # Process and return message
        return processor.process(stdin_data)

    # ==================== Backward Compatibility Wrappers ====================
    # These methods maintain the existing API for CLI compatibility.
    # They delegate to the new process_hook() method.

    def process_session_start(self, stdin_data: Optional[dict]) -> Optional[str]:
        """Process SessionStart hook (backward compatibility wrapper)."""
        return self.process_hook("SessionStart", stdin_data)

    def process_user_prompt_submit(self, stdin_data: Optional[dict]) -> Optional[str]:
        """Process UserPromptSubmit hook (backward compatibility wrapper)."""
        return self.process_hook("UserPromptSubmit", stdin_data)

    def process_pre_tool_use(
        self,
        stdin_data: Optional[dict],
        tool_name: Optional[str] = None
    ) -> Optional[str]:
        """Process PreToolUse hook (backward compatibility wrapper)."""
        return self.process_hook("PreToolUse", stdin_data)

    def process_post_tool_use(self, stdin_data: Optional[dict]) -> Optional[str]:
        """Process PostToolUse hook (backward compatibility wrapper)."""
        return self.process_hook("PostToolUse", stdin_data)

    def process_stop(self, stdin_data: Optional[dict]) -> Optional[str]:
        """Process Stop hook (backward compatibility wrapper)."""
        return self.process_hook("Stop", stdin_data)

    def process_notification(self, stdin_data: Optional[dict]) -> Optional[str]:
        """Process Notification hook (backward compatibility wrapper)."""
        return self.process_hook("Notification", stdin_data)


# Singleton handler instance
_handler_instance: Optional[VoiceNotificationHandler] = None


def get_handler(config: Optional[dict] = None, use_async: bool = True) -> VoiceNotificationHandler:
    """Get or create the voice handler singleton."""
    global _handler_instance
    if _handler_instance is None:
        _handler_instance = VoiceNotificationHandler(config=config, use_async=use_async)
    return _handler_instance
