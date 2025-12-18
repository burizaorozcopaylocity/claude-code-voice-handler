"""
Claude Code Voice Handler - Rock your code with voice notifications!

A voice notification system for Claude Code hooks that provides natural text-to-speech
notifications using OpenAI's TTS API with Qwen AI context generation.

Like a legendary roadie, this handler works behind the scenes to keep the show running.
"""

__version__ = "2.0.0"
__author__ = "Mark Hilton, Bernard Uriza"

from voice_handler.core.handler import VoiceNotificationHandler
from voice_handler.core.session import SessionVoiceManager
from voice_handler.tts.provider import TTSProvider
from voice_handler.ai.qwen import QwenContextGenerator

__all__ = [
    "VoiceNotificationHandler",
    "SessionVoiceManager",
    "TTSProvider",
    "QwenContextGenerator",
    "__version__",
]
