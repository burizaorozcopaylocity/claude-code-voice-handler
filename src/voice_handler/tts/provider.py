#!/usr/bin/env python3
"""
TTS Provider - The Sound Engineer.

Like the sound engineer who ensures every note reaches the audience crystal clear,
this module handles text-to-speech output with automatic provider fallback.
"""

from typing import Optional, List

from voice_handler.tts.base import TTSProviderInterface
from voice_handler.tts.provider_factory import TTSProviderFactory


class TTSProvider:
    """
    Manages text-to-speech output with automatic provider fallback.

    Uses Strategy pattern to try providers in order:
    1. OpenAI TTS (steerable or basic) - if available
    2. System TTS (macOS/Linux/Windows) - always available

    The sound engineer who makes sure the voice hits every speaker in the arena!
    """

    def __init__(self, config: Optional[dict] = None, logger=None, session_voice_manager=None):
        """
        Initialize TTS provider with automatic provider chain.

        Args:
            config: Voice configuration
            logger: Logger instance
            session_voice_manager: Session voice manager for per-session prefixes
        """
        self.config = config or {}
        self.logger = logger
        self.session_voice_manager = session_voice_manager

        # Load config values
        message_limits = self.config.get("message_limits", {})
        self.min_chars_for_tts = message_limits.get("min_chars_for_tts", 3)

        # Create provider chain using factory
        self.providers: List[TTSProviderInterface] = TTSProviderFactory.create_provider_chain(
            config=self.config,
            logger=self.logger
        )

        if self.logger:
            provider_names = [p.provider_name for p in self.providers]
            self.logger.log_info(
                f"TTS provider initialized with chain: {' → '.join(provider_names)}"
            )

    def format_message_for_speech(self, message: str) -> str:
        """
        Format technical text for natural speech output.

        Args:
            message: Technical message text

        Returns:
            Speech-formatted message
        """
        # Replace underscores and hyphens
        message = message.replace('_', ' ').replace('-', ' ')
        # Replace file extensions
        message = message.replace('.py', ' python file')
        message = message.replace('.json', ' JSON file')
        message = message.replace('.js', ' javascript file')
        message = message.replace('.md', ' markdown file')
        return message

    def speak(self, message: str, voice: Optional[str] = None, session_id: Optional[str] = None):
        """
        Main speech output method with automatic provider selection.

        Tries providers in order until one succeeds.
        Priority: OpenAI (steerable → basic) → System TTS

        Args:
            message: Message to speak
            voice: Override voice selection
            session_id: Session ID for per-session prefix (optional)
        """
        # Validate message length
        char_count = len(message)
        word_count = len(message.split())

        if self.logger:
            self.logger.log_info(
                f"TTS receiving message: {word_count} words, {char_count} chars"
            )
            self.logger.log_debug(f"TTS Input (before formatting): '{message}'")

        # Skip very short messages
        if len(message.strip()) < self.min_chars_for_tts:
            if self.logger:
                self.logger.log_debug(f"Skipping very short message: '{message}'")
            return

        # Format message
        message = self.format_message_for_speech(message)

        # Apply per-session prefix if available (takes precedence)
        prefix_applied = False
        if session_id and self.session_voice_manager:
            session_prefix = self.session_voice_manager.get_session_prefix(session_id)
            if session_prefix:
                message = f"{session_prefix} {message}"
                prefix_applied = True
                if self.logger:
                    self.logger.log_debug(f"Applied session prefix: {session_prefix}")

        # Apply global message prefix if no session prefix was applied
        if not prefix_applied:
            voice_settings = self.config.get("voice_settings", {})
            message_prefix = voice_settings.get("message_prefix", "")
            if message_prefix:
                message = f"{message_prefix} {message}"

        if self.logger:
            self.logger.log_debug(f"TTS Input (after formatting): '{message}'")

        # Try each provider in the chain until one succeeds
        for provider in self.providers:
            if not provider.available():
                if self.logger:
                    self.logger.log_debug(
                        f"Provider {provider.provider_name} not available, skipping"
                    )
                continue

            if self.logger:
                self.logger.log_debug(f"Trying provider: {provider.provider_name}")

            if provider.speak(message, voice):
                # Success! No need to try other providers
                return

            if self.logger:
                self.logger.log_debug(
                    f"Provider {provider.provider_name} failed, trying next"
                )

        # All providers failed
        if self.logger:
            self.logger.log_error("All TTS providers failed to speak message")
