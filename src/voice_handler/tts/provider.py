#!/usr/bin/env python3
"""
TTS Provider - The Sound Engineer.

Like the sound engineer who ensures every note reaches the audience crystal clear,
this module handles text-to-speech output with multiple provider support.
"""

import os
import subprocess
import platform
import tempfile
from pathlib import Path
from typing import Optional

# Optional imports for OpenAI TTS
try:
    from openai import OpenAI
    import sounddevice as sd
    import soundfile as sf
    import numpy as np
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class TTSProvider:
    """
    Manages text-to-speech output with multiple provider support.

    The sound engineer who makes sure the voice hits every speaker in the arena!
    """

    def __init__(self, config: Optional[dict] = None, logger=None):
        """
        Initialize TTS provider with configuration.

        Args:
            config: Voice configuration
            logger: Logger instance
        """
        self.config = config or {}
        self.logger = logger
        self.openai_client = None

        # Initialize OpenAI client if available and configured
        if OPENAI_AVAILABLE and os.environ.get("OPENAI_API_KEY"):
            try:
                self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
                if self.logger:
                    self.logger.log_info("OpenAI client initialized - sound check complete!")
            except Exception as e:
                if self.logger:
                    self.logger.log_error("Failed to initialize OpenAI client", exception=e)
                self.openai_client = None

    def compress_text_for_speech(self, text: str) -> str:
        """
        Use GPT-4o-mini to compress verbose text for natural speech.

        Args:
            text: Original text to compress

        Returns:
            Compressed, speech-optimized text
        """
        if not self.openai_client:
            return text

        # Skip compression for short messages
        if len(text) < 50:
            if self.logger:
                self.logger.log_debug(f"Skipping compression for short message ({len(text)} chars)")
            return text

        try:
            prompt = f"""You are an assistant that makes long technical responses more concise for voice output.
Your task is to rephrase the following text to be shorter and more conversational,
while preserving all key information. Focus only on the most important details.
Be brief but clear, as this will be spoken aloud.

IMPORTANT HANDLING FOR CODE BLOCKS:
- Do not include full code blocks in your response
- Instead, briefly mention "I've created code for X" or "Here's a script that does Y"
- For large code blocks, just say something like "I've written a Python function that handles user authentication"
- DO NOT attempt to read out the actual code syntax
- Only describe what the code does in 1 sentence maximum

Original text:
{text}

Return only the compressed text, without any explanation or introduction."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1024,
            )

            compressed = response.choices[0].message.content

            if self.logger:
                self.logger.log_debug(f"Compressed text from {len(text)} to {len(compressed)} chars")

            return compressed

        except Exception as e:
            if self.logger:
                self.logger.log_error("Error compressing text", exception=e)
            return text

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

    def speak_with_openai_steerable(self, message: str, voice: str = "nova") -> bool:
        """
        Generate speech using gpt-4o-mini-tts with Mexican accent steering.

        The premium experience - full control over accent and emotion!

        Args:
            message: Text to speak
            voice: OpenAI voice selection

        Returns:
            True if successful, False if failed
        """
        if not self.openai_client:
            return False

        if len(message.strip()) < 3:
            return True

        try:
            # Get accent config
            accent = self.config.get("voice_settings", {}).get("accent", "mexicano")

            # System prompt for Mexican accent
            accent_prompt = f"""Eres un locutor de radio mexicano.
Habla con acento {accent} natural y auténtico.
Usa entonación mexicana, con las inflexiones características del español de México.
Habla de forma clara pero con el ritmo y musicalidad del habla mexicana.
NO traduzcas el texto, solo léelo con acento mexicano."""

            if self.logger:
                self.logger.log_debug(f"Using gpt-4o-mini-audio-preview with {accent} accent, voice: {voice}")

            # Use chat completions with audio modality
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini-audio-preview",
                modalities=["text", "audio"],
                audio={"voice": voice, "format": "wav"},
                messages=[
                    {"role": "system", "content": accent_prompt},
                    {"role": "user", "content": message}
                ]
            )

            # Extract audio data
            audio_data = response.choices[0].message.audio.data

            # Decode base64 audio and save to temp file
            import base64
            audio_bytes = base64.b64decode(audio_data)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_filename = temp_file.name
                temp_file.write(audio_bytes)

            # Play audio - use afplay on macOS for better background compatibility
            if platform.system() == 'Darwin':
                # macOS: use native afplay (works in daemon background)
                if self.logger:
                    self.logger.log_debug(f"Playing audio with afplay: {temp_filename}")
                # Run afplay in foreground and wait for completion
                result = subprocess.run(['afplay', temp_filename], check=False, capture_output=True, text=True)
                if self.logger:
                    if result.returncode != 0:
                        self.logger.log_error(f"afplay failed with code {result.returncode}: {result.stderr}")
                    else:
                        self.logger.log_debug(f"afplay completed successfully (took {result.returncode} seconds)")
                # Wait a bit before cleanup to ensure audio finished
                import time
                time.sleep(0.5)
                os.unlink(temp_filename)
            else:
                # Other platforms: use sounddevice
                data, samplerate = sf.read(temp_filename)
                sd.play(data, samplerate)
                sd.wait()
                os.unlink(temp_filename)

            if self.logger:
                self.logger.log_tts_event("OpenAI-Steerable", True, voice=voice, text=message)

            return True

        except Exception as e:
            if self.logger:
                self.logger.log_warning(f"Steerable TTS failed: {e}, falling back to basic TTS")
            return False

    def speak_with_openai(self, message: str, voice: str = "nova") -> bool:
        """
        Generate and play speech using OpenAI's TTS API.

        The headliner performance - crystal clear audio from the cloud!

        Args:
            message: Text to speak
            voice: OpenAI voice selection

        Returns:
            True if successful, False if failed
        """
        if not self.openai_client:
            if self.logger:
                self.logger.log_debug("OpenAI client not available, falling back to system TTS")
            return False

        # Skip very short messages
        if len(message.strip()) < 3:
            if self.logger:
                self.logger.log_debug(f"Skipping very short message: '{message}'")
            return True

        try:
            if self.logger:
                self.logger.log_info(f"OpenAI TTS Original text: '{message}'")

            # Compress the message for better speech
            compressed_message = self.compress_text_for_speech(message)

            if self.logger:
                if compressed_message != message:
                    self.logger.log_info(f"OpenAI TTS Compressed text: '{compressed_message}'")
                self.logger.log_debug(f"Using OpenAI TTS with voice: {voice}")

            # Generate speech
            response = self.openai_client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=compressed_message,
                speed=0.95,  # Slightly slower for clarity
            )

            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_filename = temp_file.name
                for chunk in response.iter_bytes():
                    temp_file.write(chunk)

            # Play audio - use afplay on macOS for better background compatibility
            if platform.system() == 'Darwin':
                # macOS: use native afplay (works in daemon background)
                if self.logger:
                    self.logger.log_debug(f"Playing audio with afplay: {temp_filename}")
                # Run afplay in foreground and wait for completion
                result = subprocess.run(['afplay', temp_filename], check=False, capture_output=True, text=True)
                if self.logger:
                    if result.returncode != 0:
                        self.logger.log_error(f"afplay failed with code {result.returncode}: {result.stderr}")
                    else:
                        self.logger.log_debug(f"afplay completed successfully (took {result.returncode} seconds)")
                # Wait a bit before cleanup to ensure audio finished
                import time
                time.sleep(0.5)
                os.unlink(temp_filename)
            else:
                # Other platforms: use sounddevice
                data, samplerate = sf.read(temp_filename)
                sd.play(data, samplerate)
                sd.wait()
                os.unlink(temp_filename)

            if self.logger:
                self.logger.log_tts_event("OpenAI", True, voice=voice, text=compressed_message)

            return True

        except Exception as e:
            if self.logger:
                self.logger.log_tts_event("OpenAI", False, voice=voice, error=str(e))
            return False

    def speak_with_system(self, message: str, voice: Optional[str] = None):
        """
        Use system TTS (macOS say, Linux espeak, Windows SAPI).

        The backup PA system - always reliable!

        Args:
            message: Text to speak
            voice: System voice selection
        """
        system = platform.system()

        if not voice:
            voice = self.config.get("voice_settings", {}).get("default_voice", "Samantha")

        try:
            if system == "Darwin":  # macOS
                cmd = ["say", "-v", voice]
                rate = self.config.get("voice_settings", {}).get("speech_rate")
                if rate:
                    cmd.extend(["-r", str(rate)])
                cmd.append(message)
                subprocess.run(cmd, check=True)

            elif system == "Linux":
                subprocess.run(["espeak", message], check=True)

            elif system == "Windows":
                ps_command = (
                    f'Add-Type -AssemblyName System.speech; '
                    f'$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
                    f'$speak.Speak("{message}")'
                )
                subprocess.run(["powershell", "-Command", ps_command], check=True)

            if self.logger:
                self.logger.log_tts_event("System", True, voice=voice, text=message)

        except subprocess.CalledProcessError as e:
            if self.logger:
                self.logger.log_tts_event("System", False, voice=voice, error=str(e))
            raise

    def speak(self, message: str, voice: Optional[str] = None):
        """
        Main speech output method with automatic provider selection.

        The main show - pick the best mic and let it rip!
        Priority: Steerable TTS (accent) → Basic TTS → System TTS

        Args:
            message: Message to speak
            voice: Override voice selection
        """
        if self.logger:
            self.logger.log_debug(f"TTS Input (before formatting): '{message}'")

        message = self.format_message_for_speech(message)

        # Apply message prefix if configured (e.g., "Consola VHouse dice:")
        message_prefix = self.config.get("voice_settings", {}).get("message_prefix", "")
        if message_prefix:
            message = f"{message_prefix} {message}"

        if self.logger:
            self.logger.log_debug(f"TTS Input (after formatting): '{message}'")

        tts_provider = self.config.get("voice_settings", {}).get("tts_provider", "openai")
        use_steerable = self.config.get("voice_settings", {}).get("use_steerable_tts", True)

        if self.openai_client and (tts_provider == "openai" or tts_provider == "auto"):
            openai_voice = voice or self.config.get("voice_settings", {}).get("openai_voice", "nova")

            # Try steerable TTS first (with Mexican accent)
            if use_steerable:
                if self.speak_with_openai_steerable(message, openai_voice):
                    return
                if self.logger:
                    self.logger.log_debug("Steerable TTS failed, trying basic OpenAI TTS")

            # Fallback to basic OpenAI TTS
            if self.speak_with_openai(message, openai_voice):
                return
            if self.logger:
                self.logger.log_info("Falling back to system TTS")

        # Use system TTS as last resort
        self.speak_with_system(message, voice)
