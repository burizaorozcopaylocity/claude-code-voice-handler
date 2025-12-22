#!/usr/bin/env python3
"""
TTS Provider Interface - The Contract.

Like a recording contract that defines what every vocalist must deliver,
this interface ensures all TTS providers follow the same protocol.
"""

from abc import ABC, abstractmethod
from typing import Optional


class TTSProviderInterface(ABC):
    """
    Abstract base class for all TTS providers.

    Implementers must provide:
    1. speak() - Generate and play audio
    2. available() - Check if provider is ready to use
    3. provider_name - Identifier for logging
    """

    @abstractmethod
    def speak(self, message: str, voice: Optional[str] = None) -> bool:
        """
        Generate speech from text and play it.

        Args:
            message: Text to speak
            voice: Optional voice selection (provider-specific)

        Returns:
            True if speech was successful, False otherwise
        """
        pass

    @abstractmethod
    def available(self) -> bool:
        """
        Check if this provider is available and ready to use.

        Returns:
            True if provider can be used, False otherwise
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Return the name of this provider for logging.

        Returns:
            Provider name (e.g., "OpenAI", "System")
        """
        pass
