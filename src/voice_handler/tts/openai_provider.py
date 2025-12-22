#!/usr/bin/env python3
"""
OpenAI TTS Provider - The Cloud Studio.

Premium audio quality from OpenAI's text-to-speech API with optional
accent steering using GPT-4o-mini-audio-preview.
"""

import os
import base64
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from voice_handler.tts.base import TTSProviderInterface

# Optional imports for OpenAI TTS
try:
    from openai import OpenAI
    import sounddevice as sd
    import soundfile as sf
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAITTSProvider(TTSProviderInterface):
    """
    OpenAI TTS provider with support for both basic TTS and steerable TTS.

    Steerable TTS uses gpt-4o-mini-audio-preview for accent control.
    Basic TTS uses tts-1 with speed control and GPT-4o-mini compression.
    """

    def __init__(
        self,
        config: Optional[dict] = None,
        logger=None,
        use_steerable: bool = True
    ):
        """
        Initialize OpenAI TTS provider.

        Args:
            config: Voice configuration
            logger: Logger instance
            use_steerable: Whether to use steerable TTS with accent
        """
        self.config = config or {}
        self.logger = logger
        self.use_steerable = use_steerable
        self.client: Optional[OpenAI] = None

        # Load config values
        message_limits = self.config.get("message_limits", {})
        self.min_chars_for_tts = message_limits.get("min_chars_for_tts", 3)
        self.min_chars_for_compression = message_limits.get("min_chars_for_compression", 50)

        tts_settings = self.config.get("tts_settings", {})
        self.openai_speed = tts_settings.get("openai_speed", 0.95)

        # Initialize OpenAI client if API key available
        if OPENAI_AVAILABLE and os.environ.get("OPENAI_API_KEY"):
            try:
                self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
                if self.logger:
                    self.logger.log_info("OpenAI TTS provider initialized")
            except Exception as e:
                if self.logger:
                    self.logger.log_error("Failed to initialize OpenAI client", exception=e)
                self.client = None

    @property
    def provider_name(self) -> str:
        return "OpenAI"

    def available(self) -> bool:
        """Check if OpenAI client is available."""
        return self.client is not None and OPENAI_AVAILABLE

    def speak(self, message: str, voice: Optional[str] = None) -> bool:
        """
        Generate speech using OpenAI TTS.

        Priority: Steerable TTS (accent) → Basic TTS

        Args:
            message: Text to speak
            voice: OpenAI voice selection (nova, alloy, echo, fable, onyx, shimmer)

        Returns:
            True if successful, False otherwise
        """
        if not self.available():
            return False

        # Skip very short messages
        if len(message.strip()) < self.min_chars_for_tts:
            if self.logger:
                self.logger.log_debug(f"Skipping very short message: '{message}'")
            return True

        # Use steerable TTS if enabled
        if self.use_steerable:
            if self._speak_steerable(message, voice):
                return True
            if self.logger:
                self.logger.log_debug("Steerable TTS failed, trying basic TTS")

        # Fallback to basic TTS
        return self._speak_basic(message, voice)

    def _speak_steerable(self, message: str, voice: Optional[str] = None) -> bool:
        """
        Generate speech using gpt-4o-mini-audio-preview with accent steering.

        Args:
            message: Text to speak
            voice: OpenAI voice selection

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get accent config
            voice_settings = self.config.get("voice_settings", {})
            accent = voice_settings.get("accent", "mexicano")
            voice = voice or voice_settings.get("openai_voice", "nova")

            # System prompt for accent - VERBATIM reading
            accent_prompt = f"""Your only task is to read the user's text EXACTLY as written with a {accent} accent.

CRITICAL INSTRUCTIONS:
- Read ONLY the exact text provided, word-for-word, character-for-character
- Apply {accent} accent and intonation to your speech
- Do NOT interpret, paraphrase, summarize, or change any words
- Do NOT add commentary, explanations, or your own words
- Do NOT answer questions in the text - just read them aloud
- Do NOT correct grammar or spelling - read it exactly as written
- Preserve all punctuation, capitalization, and formatting in your speech rhythm

You are a voice reader, not a conversational assistant. Read the text verbatim with {accent} pronunciation."""

            if self.logger:
                self.logger.log_debug(f"Using gpt-4o-mini-audio-preview with {accent} accent, voice: {voice}")

            # Use chat completions with audio modality
            response = self.client.chat.completions.create(
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
            audio_bytes = base64.b64decode(audio_data)

            # Play audio with cleanup
            self._play_audio(audio_bytes)

            if self.logger:
                self.logger.log_tts_event("OpenAI-Steerable", True, voice=voice, text=message)

            return True

        except Exception as e:
            if self.logger:
                self.logger.log_warning(f"Steerable TTS failed: {e}")
            return False

    def _speak_basic(self, message: str, voice: Optional[str] = None) -> bool:
        """
        Generate speech using OpenAI tts-1 with compression.

        Args:
            message: Text to speak
            voice: OpenAI voice selection

        Returns:
            True if successful, False otherwise
        """
        try:
            voice_settings = self.config.get("voice_settings", {})
            voice = voice or voice_settings.get("openai_voice", "nova")

            if self.logger:
                self.logger.log_info(f"OpenAI TTS Original text: '{message}'")

            # Compress the message for better speech
            compressed_message = self._compress_text(message)

            if self.logger:
                if compressed_message != message:
                    self.logger.log_info(f"OpenAI TTS Compressed text: '{compressed_message}'")
                self.logger.log_debug(f"Using OpenAI TTS with voice: {voice}")

            # Generate speech
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=compressed_message,
                speed=self.openai_speed,
            )

            # Play audio with cleanup
            audio_bytes = b''.join(response.iter_bytes())
            self._play_audio(audio_bytes)

            if self.logger:
                self.logger.log_tts_event("OpenAI", True, voice=voice, text=compressed_message)

            return True

        except Exception as e:
            if self.logger:
                self.logger.log_tts_event("OpenAI", False, voice=voice, error=str(e))
            return False

    def _compress_text(self, text: str) -> str:
        """
        Use GPT-4o-mini to compress verbose text for natural speech.

        Args:
            text: Original text to compress

        Returns:
            Compressed, speech-optimized text
        """
        # Skip compression for short messages
        if len(text) < self.min_chars_for_compression:
            if self.logger:
                self.logger.log_debug(f"Skipping compression for short message ({len(text)} chars)")
            return text

        try:
            prompt = f"""Eres un asistente que hace respuestas técnicas largas más concisas para salida de voz.
Tu tarea es reformular el siguiente texto para que sea más corto y conversacional,
preservando toda la información clave. Enfócate solo en los detalles más importantes.
Sé breve pero claro, ya que esto será hablado en voz alta.

IMPORTANTE - MANEJO DE BLOQUES DE CÓDIGO:
- No incluyas bloques de código completos en tu respuesta
- En su lugar, menciona brevemente "Creé código para X" o "Aquí hay un script que hace Y"
- Para bloques grandes de código, solo di algo como "Escribí una función Python que maneja autenticación de usuarios"
- NO intentes leer la sintaxis del código
- Solo describe qué hace el código en máximo 1 oración

CRÍTICO - IDIOMA:
- SIEMPRE responde en ESPAÑOL
- Mantén el mismo idioma del texto original
- NO traduzcas a inglés

Texto original:
{text}

Devuelve solo el texto comprimido en ESPAÑOL, sin explicación ni introducción."""

            response = self.client.chat.completions.create(
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

    def _play_audio(self, audio_bytes: bytes):
        """
        Play audio bytes with guaranteed cleanup.

        Args:
            audio_bytes: WAV audio data
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_filename = Path(temp_dir) / "speech.wav"

            with open(temp_filename, 'wb') as f:
                f.write(audio_bytes)

            # Play audio - use afplay on macOS for better background compatibility
            if platform.system() == 'Darwin':
                # macOS: use native afplay (works in daemon background)
                if self.logger:
                    self.logger.log_debug(f"Playing audio with afplay: {temp_filename}")
                # Run afplay in foreground and wait for completion
                result = subprocess.run(
                    ['afplay', str(temp_filename)],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if self.logger:
                    if result.returncode != 0:
                        self.logger.log_error(f"afplay failed with code {result.returncode}: {result.stderr}")
                    else:
                        self.logger.log_debug("afplay completed successfully")
            else:
                # Other platforms: use sounddevice
                data, samplerate = sf.read(temp_filename)
                sd.play(data, samplerate)
                sd.wait()
            # TemporaryDirectory auto-cleans on exit
