#!/usr/bin/env python3
"""
TTS Provider Factory - The Talent Agency.

Like a talent agency that books the right vocalist for each gig,
this factory creates and configures TTS providers based on availability
and configuration.
"""

from typing import List, Optional

from voice_handler.tts.base import TTSProviderInterface
from voice_handler.tts.openai_provider import OpenAITTSProvider
from voice_handler.tts.system_provider import SystemTTSProvider


class TTSProviderFactory:
    """
    Factory for creating TTS provider instances.

    Provides:
    - Provider creation based on configuration
    - Automatic fallback chain construction
    - Availability checking
    """

    @staticmethod
    def create_provider_chain(
        config: Optional[dict] = None,
        logger=None
    ) -> List[TTSProviderInterface]:
        """
        Create a chain of TTS providers with automatic fallback.

        The chain is ordered by preference from config, with system TTS
        as the final fallback (always available).

        Args:
            config: Voice configuration
            logger: Logger instance

        Returns:
            List of providers in priority order
        """
        config = config or {}
        voice_settings = config.get("voice_settings", {})
        tts_provider = voice_settings.get("tts_provider", "openai")
        use_steerable = voice_settings.get("use_steerable_tts", True)

        providers: List[TTSProviderInterface] = []

        # Add primary provider based on config
        if tts_provider == "openai":
            openai_provider = OpenAITTSProvider(
                config=config,
                logger=logger,
                use_steerable=use_steerable
            )
            if openai_provider.available():
                providers.append(openai_provider)
                if logger:
                    logger.log_debug("Added OpenAI TTS to provider chain")
            else:
                if logger:
                    logger.log_debug("OpenAI TTS not available, skipping")

        # Always add system TTS as fallback
        system_provider = SystemTTSProvider(config=config, logger=logger)
        if system_provider.available():
            providers.append(system_provider)
            if logger:
                logger.log_debug(f"Added {system_provider.provider_name} TTS to provider chain")

        if not providers:
            if logger:
                logger.log_error("No TTS providers available!")

        return providers

    @staticmethod
    def create_openai_provider(
        config: Optional[dict] = None,
        logger=None,
        use_steerable: bool = True
    ) -> OpenAITTSProvider:
        """
        Create an OpenAI TTS provider.

        Args:
            config: Voice configuration
            logger: Logger instance
            use_steerable: Whether to use steerable TTS with accent

        Returns:
            OpenAI TTS provider instance
        """
        return OpenAITTSProvider(
            config=config,
            logger=logger,
            use_steerable=use_steerable
        )

    @staticmethod
    def create_system_provider(
        config: Optional[dict] = None,
        logger=None
    ) -> SystemTTSProvider:
        """
        Create a system TTS provider.

        Args:
            config: Voice configuration
            logger: Logger instance

        Returns:
            System TTS provider instance
        """
        return SystemTTSProvider(config=config, logger=logger)
