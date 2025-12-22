#!/usr/bin/env python3
"""
System TTS Provider - The Backup PA System.

Uses platform-native text-to-speech engines:
- macOS: say command
- Linux: espeak
- Windows: SAPI via PowerShell

Always reliable, always available!
"""

import platform
import subprocess
from typing import Optional

from voice_handler.tts.base import TTSProviderInterface


class SystemTTSProvider(TTSProviderInterface):
    """
    System TTS provider using native OS speech engines.

    Platform support:
    - macOS: `say` command with voice and rate control
    - Linux: `espeak` command
    - Windows: SAPI via PowerShell
    """

    def __init__(self, config: Optional[dict] = None, logger=None):
        """
        Initialize system TTS provider.

        Args:
            config: Voice configuration
            logger: Logger instance
        """
        self.config = config or {}
        self.logger = logger
        self.system = platform.system()

        # Load config values for message formatting
        message_limits = self.config.get("message_limits", {})
        self.min_chars_for_tts = message_limits.get("min_chars_for_tts", 3)

    @property
    def provider_name(self) -> str:
        return f"System ({self.system})"

    def available(self) -> bool:
        """System TTS is always available on supported platforms."""
        return self.system in ("Darwin", "Linux", "Windows")

    def speak(self, message: str, voice: Optional[str] = None) -> bool:
        """
        Generate speech using system TTS.

        Args:
            message: Text to speak
            voice: System voice selection (platform-specific)

        Returns:
            True if successful, False otherwise
        """
        # Skip very short messages
        if len(message.strip()) < self.min_chars_for_tts:
            if self.logger:
                self.logger.log_debug(f"Skipping very short message: '{message}'")
            return True

        # Format message for speech
        message = self._format_message(message)

        # Get default voice if not specified
        if not voice:
            voice_settings = self.config.get("voice_settings", {})
            voice = voice_settings.get("fallback_voice", "Samantha")

        try:
            if self.system == "Darwin":  # macOS
                self._speak_macos(message, voice)
            elif self.system == "Linux":
                self._speak_linux(message, voice)
            elif self.system == "Windows":
                self._speak_windows(message, voice)
            else:
                if self.logger:
                    self.logger.log_error(f"Unsupported platform: {self.system}")
                return False

            if self.logger:
                self.logger.log_tts_event("System", True, voice=voice, text=message)

            return True

        except subprocess.CalledProcessError as e:
            if self.logger:
                self.logger.log_tts_event("System", False, voice=voice, error=str(e))
            return False
        except Exception as e:
            if self.logger:
                self.logger.log_error("System TTS failed", exception=e)
            return False

    def _format_message(self, message: str) -> str:
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

    def _speak_macos(self, message: str, voice: str):
        """
        Speak using macOS say command.

        Args:
            message: Text to speak
            voice: macOS voice name
        """
        cmd = ["say", "-v", voice]

        # Add speech rate if configured
        voice_settings = self.config.get("voice_settings", {})
        rate = voice_settings.get("fallback_speech_rate")
        if rate:
            cmd.extend(["-r", str(rate)])

        cmd.append(message)
        subprocess.run(cmd, check=True)

    def _speak_linux(self, message: str, voice: str):
        """
        Speak using Linux espeak command.

        Args:
            message: Text to speak
            voice: espeak voice (ignored for now)
        """
        subprocess.run(["espeak", message], check=True)

    def _speak_windows(self, message: str, voice: str):
        """
        Speak using Windows SAPI via PowerShell.

        Args:
            message: Text to speak
            voice: SAPI voice name (ignored for now)
        """
        ps_command = (
            f'Add-Type -AssemblyName System.speech; '
            f'$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
            f'$speak.Speak("{message}")'
        )
        subprocess.run(["powershell", "-Command", ps_command], check=True)
